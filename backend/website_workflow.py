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
import photo_sync
import photo_metadata_sync
import photo_removal_sync
import frontend_sync
import site_deployment
import webbrowser

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
    if job.get('kind') in ('frontend-files', 'website-code'):
        code = job['kind'] == 'website-code'
        for path, expected_hash in job['proposed'].items():
            if frontend_sync.checksum(frontend_sync.read_text(ROOT if code else ROOT/'frontend', path, code)) != expected_hash:
                raise ValueError('Local frontend file changed since review: '+path)
        return job
    if job.get('kind') in ('photo-edit', 'photo-remove'):
        photo = photo_sync.catalog(state['working']).get(job['canonical'])
        current = photo_metadata_sync.metadata(photo) if photo else None
        if photo_metadata_sync.image_hash(ROOT/'frontend', job['canonical']) != job['image_sha256']:
            raise ValueError('Local photo changed. Prepare it again.')
    elif job.get('kind') == 'photo-add':
        current = photo_sync.catalog(state['working']).get(job['canonical'])
        if digest(ROOT/'frontend'/job['canonical']) != job['image_sha256']:
            raise ValueError('Local photo changed. Prepare it again.')
    else:
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


def prepare_photo(state, file_path):
    if digest(state['base']) != state['base_sha256']:
        raise ValueError('Baseline changed. Select the unchanged baseline.')
    folder = ROOT/'dist'/'math-workflow'/uuid.uuid4().hex
    folder.mkdir(parents=True)
    package = folder/'package.zip'
    payload = photo_sync.prepare(state['base'],state['working'],file_path,ROOT/'frontend',package)
    report = preview(read_package(package))
    (folder/'review.txt').write_text(report,encoding='utf-8')
    state['job'] = dict(kind='photo-add',canonical=file_path,package=str(package),sha256=digest(package),
                        proposed=payload['photo'],image_sha256=payload['sha256'],remote=None,checked=False)
    save(state)
    return report


def prepare_photo_edit(state, file_path):
    if digest(state['base']) != state['base_sha256']:
        raise ValueError('Baseline changed. Select the unchanged baseline.')
    folder = ROOT/'dist'/'math-workflow'/uuid.uuid4().hex
    folder.mkdir(parents=True)
    package = folder/'package.zip'
    payload = photo_metadata_sync.prepare(state['base'], state['working'], file_path, ROOT/'frontend', package)
    report = preview(read_package(package))
    (folder/'review.txt').write_text(report, encoding='utf-8')
    state['job'] = dict(kind='photo-edit', canonical=file_path, package=str(package), sha256=digest(package),
                        proposed=payload['replacement'], image_sha256=payload['sha256'], remote=None, checked=False)
    save(state)
    return report


def prepare_photo_removal(state, file_path):
    if digest(state['base']) != state['base_sha256']:
        raise ValueError('Baseline changed. Select the unchanged baseline.')
    folder = ROOT/'dist'/'math-workflow'/uuid.uuid4().hex
    folder.mkdir(parents=True)
    package = folder/'package.zip'
    payload = photo_removal_sync.prepare(state['base'], state['working'], file_path, ROOT/'frontend', package)
    report = preview(read_package(package))
    (folder/'review.txt').write_text(report, encoding='utf-8')
    state['job'] = dict(kind='photo-remove', canonical=file_path, package=str(package), sha256=digest(package),
                        proposed=payload['expected'], image_sha256=payload['sha256'], remote=None, checked=False)
    save(state)
    return report


def prepare_frontend(state, paths, code=False):
    # Validate local selections before connecting, without changing user files.
    for path in paths:
        if frontend_sync.read_text(ROOT if code else ROOT/'frontend', path, code) is None:
            raise ValueError('Selected local file is missing: '+path)
    print('Reading selected live frontend files for comparison. No live changes.', flush=True)
    domain = None
    if code:
        settings = validate(json.loads(SETTINGS.read_text(encoding='utf-8')))
        if settings['username'] != state['username']:
            raise ValueError('API account differs from selected account.')
        domains = site_deployment.domains(settings)
        if not domains:
            raise ValueError('No website found in the selected account.')
        print('Account websites:', ', '.join(domains))
        domain = domains[0] if len(domains) == 1 else input('Website domain to reload: ').strip()
        if domain not in domains:
            raise ValueError('Choose a website from the account list.')
    live = frontend_sync.capture_live(state['username'], paths, code=code)
    folder = ROOT/'dist'/'math-workflow'/uuid.uuid4().hex
    folder.mkdir(parents=True)
    package = folder/'package.zip'
    payload = frontend_sync.prepare(ROOT if code else ROOT/'frontend', paths, live, package, code=code)
    report = preview(read_package(package))
    (folder/'review.txt').write_text(report, encoding='utf-8')
    state['job'] = dict(kind=payload['kind'], domain=domain, canonical=('Website code: ' if code else 'Frontend files: ')+', '.join(item['path'] for item in payload['files']),
                        package=str(package), sha256=digest(package),
                        proposed={item['path']: frontend_sync.checksum(item['replacement']) for item in payload['files']},
                        remote=None, checked=False)
    save(state)
    return report


def finish_code_deployment(state):
    job = current_job(state)
    if job.get('kind') != 'website-code' or job.get('result') not in ('APPLIED', 'ALREADY_PRESENT'):
        raise ValueError('Publish a reviewed website code package first.')
    # A retry must verify the uploaded code again, not just reload arbitrary
    # files that may have changed since the original upload.
    check_live(state)
    if not job['preflight_status'].startswith('ALREADY PRESENT'):
        raise ValueError('Live files do not match the published package; reload stopped.')
    settings = validate(json.loads(SETTINGS.read_text(encoding='utf-8')))
    if settings['username'] != state['username']:
        raise ValueError('Reload account differs from publication account.')
    deployment_receipt = Path(job['package']).parent/('deployment-'+uuid.uuid4().hex+'.json')
    def record(status):
        job['deployment_status'] = status
        job['deployment_receipt'] = str(deployment_receipt)
        deployment_receipt.write_text(json.dumps(dict(status=status, domain=job['domain'],
            package_sha256=job['sha256'], publication_receipt=job.get('publication_receipt')), indent=2), encoding='utf-8')
        save(state)
    record('RELOAD_PENDING')
    site_deployment.reload_site(settings, job['domain'])
    record('RELOAD_ACKNOWLEDGED')
    site_deployment.verify_site(job['domain'])
    record('HOMEPAGE_VERIFIED')
    print('Deployment receipt:', deployment_receipt)
    print('Reload acknowledged and public homepage returned HTTP 200. Check the changed feature in your browser; this is not a feature test.')


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
    if job.get('kind') == 'photo-remove':
        print('REMOVE this photo from the live gallery. The image file will remain accessible at its direct URL.')
    if job.get('kind') == 'website-code':
        print('This uploads Python and matching files, then reloads https://'+job['domain']+'. No migrations or dependency installation are included.')
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
    job['publication_receipt'] = str(receipt)
    save(state)
    if job.get('kind') == 'website-code':
        print('Code files uploaded. Reload and homepage verification follow; if interrupted, use option 16 after checking the saved status.')
        finish_code_deployment(state)
    elif job.get('kind') == 'frontend-files':
        print('Frontend files verified. Hard-refresh the affected live pages (Ctrl+F5). No reload or database refresh is needed for this file-only update.')
    else:
        print('Verify the live page, then download a fresh baseline. Existing local databases were not replaced.')


def main():
    state = json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else None
    while True:
        print('\nWebsite update helper')
        if state:
            print('Working copy:', state['working'])
            print('Selected entry:', (state.get('job') or {}).get('canonical', '(none)'))
        print('1. Show local changes\n2. Prepare an entry for review\n3. Stage reviewed package\n4. Check live\n5. Publish reviewed package\n6. Start local server\n7. Set baseline and working paths\n8. Bring website changes home\n9. Prepare biography or resume update\n10. Open Google Photos import\n11. Prepare a new photo for publication\n12. Prepare changes to existing photo details\n13. Prepare removal from the gallery (keep image)\n14. Prepare frontend files (HTML, CSS, JavaScript)\n15. Prepare Python and matching frontend files\n16. Retry code reload and homepage verification\n0. Exit')
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
                result = refresh(state, snapshot, ROOT/'dist'/'home-sync', save, frontend=ROOT/'frontend')
                print(result['reason'])
                print('Comparison report:', result['report'])
                if result['safe']:
                    print('New working copy:', result['working'])
                    print(f"Gallery: {result['photos_verified']} images verified, {result['photos_downloaded']} downloaded; {result['local_drafts_preserved']} local import drafts preserved.")
                    print('Choose 6 to restart the local server using this copy. Website program files and other media were not downloaded.')
                else:
                    print('Saved paths and existing databases are unchanged. Review the report before proceeding.')
            elif choice == '9':
                print(prepare_profile(state, input('Page to prepare (bio or resume): ').strip()))
                print('Review the changes above, then choose 3 to stage, 4 to check live, and 5 to publish.')
            elif choice == '10':
                print('Keep the local server running (option 6 in another terminal). Opening the photo review page.')
                webbrowser.open('http://127.0.0.1:5001/api/photography/google/manage')
            elif choice == '16':
                finish_code_deployment(state)
            elif choice == '15':
                print('Enter repository-relative paths, separated by commas. Include backend/src Python and any matching frontend files.')
                selected = input('Code files (blank cancels): ').strip()
                if not selected:
                    continue
                print(prepare_frontend(state, [path.strip() for path in selected.split(',')], code=True))
                print('Review all changes and test locally, then use 3 (stage), 4 (check live), 5 (publish and reload).')
            elif choice == '14':
                print('Enter paths relative to frontend, separated by commas (example: photography/photography.css).')
                selected = input('Files (blank cancels): ').strip()
                if not selected:
                    continue
                paths = [path.strip() for path in selected.split(',')]
                print(prepare_frontend(state, paths))
                print('Review ALL differences against live, then use 3 (stage), 4 (check live), 5 (publish).')
            elif choice == '13':
                baseline = photo_sync.catalog(state['base'])
                local = photo_sync.catalog(state['working'])
                candidates = sorted(baseline.keys() & local.keys())
                for i, path in enumerate(candidates, 1):
                    print(f'{i}. {local[path]["title"]} ({path})')
                if not candidates:
                    print('No existing baseline photos available for removal.')
                else:
                    selected = int(input('Photo number to prepare for removal (0 cancels): '))
                    if selected == 0:
                        continue
                    if not 1 <= selected <= len(candidates):
                        raise ValueError('Invalid photo number.')
                    print(prepare_photo_removal(state, candidates[selected-1]))
                    print('Nothing removed yet. Review, then use 3 (stage), 4 (check live), 5 (publish).')
            elif choice == '12':
                baseline = photo_sync.catalog(state['base'])
                local = photo_sync.catalog(state['working'])
                candidates = sorted(path for path in baseline.keys() & local.keys()
                                    if photo_metadata_sync.metadata(baseline[path]) != photo_metadata_sync.metadata(local[path]))
                for i, path in enumerate(candidates, 1):
                    print(f'{i}. {local[path]["title"]} ({path})')
                if not candidates:
                    print('No changes to existing photo details. Edit and save a title, location or coordinates locally first.')
                else:
                    selected = int(input('Photo number: '))
                    if not 1 <= selected <= len(candidates):
                        raise ValueError('Invalid photo number.')
                    print(prepare_photo_edit(state, candidates[selected-1]))
                    print('Review the changes, then use 3 (stage), 4 (check live), 5 (publish).')
            elif choice == '11':
                baseline = photo_sync.catalog(state['base'])
                local = photo_sync.catalog(state['working'])
                candidates = sorted(set(local)-set(baseline))
                for i,path in enumerate(candidates,1):
                    print(f'{i}. {local[path]["title"]} ({path})')
                if not candidates:
                    print('No new local gallery photos. Import and add a photo locally first.')
                else:
                    selected = int(input('Photo number: '))
                    if not 1 <= selected <= len(candidates):
                        raise ValueError('Invalid photo number.')
                    print(prepare_photo(state,candidates[selected-1]))
                    print('Review your local photo, then use 3 (stage), 4 (check live), 5 (publish).')
            else:
                print('Choose one of the listed numbers.')
        except (ValueError, RuntimeError, OSError, sqlite3.Error, subprocess.CalledProcessError) as error:
            print('Stopped:', str(error))


if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print('\nClosed. Saved workflow files are preserved.')
