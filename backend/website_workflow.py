"""Guided website publishing and database refresh with remembered local paths."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import uuid
import zipfile
import sqlite3

from preview_math_sync import read_snapshot
from prepare_math_patch import prepare
from publish_math_entry import validate as validate_entry
from inspect_staged_package import preview
from stage_pythonanywhere_package import stage, read_package
from preflight_live_package import preflight
from publish_staged_package import publish_staged
from pythonanywhere_api import SETTINGS, validate
from apply_math_text_patch import patch_intended
from download_live_database import download
from bring_changes_home import refresh
import profile_sync

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / 'dist' / 'math-workflow.json'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(state):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    temporary = STATE.with_suffix('.tmp')
    temporary.write_text(json.dumps(state, indent=2), encoding='utf-8')
    temporary.replace(STATE)


def configure(base, working, username='cwoo'):
    base, working = Path(base).resolve(), Path(working).resolve()
    if base == working or base.samefile(working):
        raise ValueError('Baseline and working copy must be separate files.')
    read_snapshot(base)
    read_snapshot(working)
    state = dict(base=str(base), working=str(working), base_sha256=digest(base),
                 username=username, job=None)
    save(state)
    return state


def changed_entries(state):
    if digest(state['base']) != state['base_sha256']:
        raise ValueError('The saved baseline changed. Select the correct unchanged baseline before continuing.')
    baseline, working = read_snapshot(state['base']), read_snapshot(state['working'])
    changes = []
    for name in sorted(baseline.keys() | working.keys()):
        if baseline.get(name) == working.get(name):
            continue
        fields = ([key for key in working[name] if working[name][key] != baseline[name][key]]
                  if name in baseline and name in working else [])
        supported = name in working and (name not in baseline or set(fields) <= {'cleaned_tex', 'synonyms'})
        changes.append(dict(canonical=name, title=working.get(name, baseline.get(name))['title'],
                            fields=fields, supported=supported, new=name not in baseline))
    return changes


def prepare_selected(state, canonical):
    candidates = {c['canonical']: c for c in changed_entries(state)}
    if canonical not in candidates or not candidates[canonical]['supported']:
        raise ValueError('No supported change selected. Deletions and other metadata changes are not supported yet.')
    folder = ROOT / 'dist' / 'math-workflow' / uuid.uuid4().hex
    folder.mkdir(parents=True)
    package = folder / 'package.zip'
    if candidates[canonical]['new']:
        entry = dict(read_snapshot(state['working'])[canonical], canonical_name=canonical)
        validate_entry(entry)
        with zipfile.ZipFile(package, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('entry.json', json.dumps(entry, ensure_ascii=False, indent=2))
        report = preview(read_package(package))
    else:
        report = prepare(Path(state['base']), Path(state['working']), canonical, package)
    (folder / 'review.txt').write_text(report, encoding='utf-8')
    with zipfile.ZipFile(package) as archive:
        payload = json.loads(archive.read(archive.namelist()[0]))
    proposed = (patch_intended(payload) if 'replacement_tex' in payload else
                {k: sorted(v) if isinstance(v, list) else v for k, v in payload.items() if k != 'canonical_name'})
    state['job'] = dict(canonical=canonical, package=str(package), sha256=digest(package),
                        proposed=proposed, remote=None, checked=False)
    save(state)
    return report


def current_job(state):
    job = state.get('job')
    if not job:
        raise ValueError('Prepare a selected entry first.')
    if digest(state['base']) != state['base_sha256'] or digest(job['package']) != job['sha256']:
        raise ValueError('Baseline or package changed. Prepare a new review package.')
    current = (profile_sync.page_state(state['working'], job['canonical'])['fields']
               if job.get('kind') == 'profile' else read_snapshot(state['working']).get(job['canonical']))
    if job.get('kind') == 'profile' and profile_sync.template_info(ROOT/'frontend', job['canonical'])[0] != job['template_sha256']:
        raise ValueError('Local profile template changed. Prepare again.')
    if current != job['proposed']:
        raise ValueError('Local entry changed since preparation. Prepare it again before continuing.')
    return job


def prepare_profile(state, page):
    if digest(state['base']) != state['base_sha256']:
        raise ValueError('Baseline changed. Select the correct baseline.')
    payload = profile_sync.prepare_payload(state['base'], state['working'], page, ROOT/'frontend')
    folder = ROOT/'dist'/'math-workflow'/uuid.uuid4().hex
    folder.mkdir(parents=True)
    package = folder/'package.zip'
    with zipfile.ZipFile(package, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('profile.json', json.dumps(payload, ensure_ascii=False, indent=2))
    report = preview(read_package(package))
    (folder/'review.txt').write_text(report, encoding='utf-8')
    state['job'] = dict(kind='profile', canonical=page, package=str(package), sha256=digest(package),
                        proposed=payload['replacement'], template_sha256=payload['template_sha256'], remote=None, checked=False)
    save(state)
    return report


def upload(state):
    job = current_job(state)
    if job['remote']:
        print('Already staged:', job['remote'])
        return
    settings = validate(json.loads(SETTINGS.read_text(encoding='utf-8')))
    if settings['username'] != state['username']:
        raise ValueError('API account differs from the selected workflow account.')
    job['remote'], actual = stage(settings, Path(job['package']))
    if actual != job['sha256']:
        raise ValueError('Package changed during staging. Prepare again.')
    save(state)
    print('Staged and verified. Next: check live.')


def check_live(state):
    job = current_job(state)
    if not job['remote']:
        raise ValueError('Stage the package first.')
    job['checked'] = False
    save(state)
    report = Path(job['package']).parent / ('preflight-' + uuid.uuid4().hex + '.txt')
    result = preflight(state['username'], job['remote'], Path(job['package']), report)
    status = result['report'].splitlines()[-3]
    job['checked'] = status.startswith(('EXPECTED TEXT MATCHES', 'NO DUPLICATE FOUND', 'ALREADY PRESENT'))
    job['preflight_status'] = status
    save(state)
    print(result['report'])


def publish_reviewed(state):
    job = current_job(state)
    if not job['remote'] or not job['checked']:
        raise ValueError('Run a successful live check for this package first.')
    print('Selected entry:', job['canonical'])
    print('This applies the reviewed package to the live website, with a backup and repeated conflict checks.')
    if input('Type PUBLISH to proceed (anything else cancels): ').strip() != 'PUBLISH':
        print('Cancelled.')
        return
    # Any failed/uncertain attempt requires another preflight before a retry.
    job['checked'] = False
    save(state)
    receipt = Path(job['package']).parent / ('receipt-' + uuid.uuid4().hex + '.json')
    result = publish_staged(state['username'], job['remote'], Path(job['package']), receipt)
    job['result'] = result['status']
    save(state)
    print('Verify the live page, then download a fresh baseline. Existing local databases were not replaced.')


def main():
    state = json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else None
    while True:
        print('\nWebsite update helper')
        if state:
            print('Working copy:', state['working'])
            print('Selected entry:', (state.get('job') or {}).get('canonical', '(none)'))
        print('1. Show local changes\n2. Prepare an entry for review\n3. Stage reviewed package\n4. Check live\n5. Publish reviewed package\n6. Start local server\n7. Set baseline and working paths\n8. Bring website changes home\n9. Prepare biography or resume update\n0. Exit')
        choice = input('Choose: ').strip()
        try:
            if choice == '0':
                return
            if choice == '7' or state is None:
                if state and state.get('job'):
                    if input('Reset the active workflow? Existing packages will be preserved. Type RESET: ') != 'RESET':
                        continue
                state = configure(input('Unchanged baseline database path: ').strip().strip('"'),
                                  input('Working database path: ').strip().strip('"'))
            elif choice in ('1', '2'):
                changes = changed_entries(state)
                for index, item in enumerate(changes, 1):
                    print(f"{index}. {item['title']} ({item['canonical']}) — " +
                          ('new entry' if item['new'] else ', '.join(item['fields'])) +
                          ('' if item['supported'] else ' [unsupported]'))
                if not changes:
                    print('No math changes compared with your baseline.')
                elif choice == '2':
                    selection = int(input('Entry number: '))
                    if not 1 <= selection <= len(changes):
                        raise ValueError('Invalid entry number.')
                    print(prepare_selected(state, changes[selection-1]['canonical']))
                    print('Review the changes above before choosing Stage.')
            elif choice == '3':
                upload(state)
            elif choice == '4':
                check_live(state)
            elif choice == '5':
                publish_reviewed(state)
            elif choice == '6':
                subprocess.run([sys.executable, str(ROOT / 'backend/start_local.py'), '--database', state['working']], check=True)
            elif choice == '8':
                print('Stop your local server first (Ctrl+C in its terminal). Old databases and review packages will be preserved.')
                if input('Type STOPPED when the local server is stopped (anything else cancels): ').strip() != 'STOPPED':
                    continue
                snapshot = download(Path.home()/'Downloads'/'chi-portfolio'/'database', state['username'])
                result = refresh(state, snapshot, ROOT/'dist'/'home-sync', save)
                print(result['reason'])
                print('Comparison report:', result['report'])
                if result['safe']:
                    print('New working copy:', result['working'])
                    print('Choose 6 to restart the local server using this copy. No website files or media were downloaded.')
                else:
                    print('Saved paths and existing databases are unchanged. Review the report before proceeding.')
            elif choice == '9':
                print(prepare_profile(state, input('Page to prepare (bio or resume): ').strip()))
                print('Review the changes above, then choose 3 to stage, 4 to check live, and 5 to publish.')
            else:
                print('Choose one of the listed numbers.')
        except (ValueError, RuntimeError, OSError, sqlite3.Error, subprocess.CalledProcessError) as error:
            print('Stopped:', str(error))


if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print('\nClosed. Saved workflow files are preserved.')
