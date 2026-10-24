"""Guided website publishing and database refresh with remembered local paths."""
from contextlib import closing
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import uuid
import zipfile
import sqlite3

from preview_math_sync import read_snapshot
from prepare_math_patch import local_missing_svgs, prepare
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
import upload_esri_key
import diagram_sync

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / 'dist' / 'math-workflow.json'
DIAGRAMS = ROOT / 'backend' / 'data' / 'math' / 'diagrams'


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


def explain_rejection(entry, message):
    """Turn a publisher validation message into a reason a person can act on."""
    if message.startswith('Media/diagrams'):
        return 'contains diagrams or images (for example \\includegraphics, figure, pspicture or \\pstree)'
    if message.startswith('Diagram or image changed'):
        return ('adds, removes or changes a diagram, image or embed; PSTricks diagrams can change once their SVGs '
                'are rendered (option 19), but other images and embeds must stay exactly as they are')
    if message.startswith('Missing text field: cleaned_tex'):
        return 'has empty content'
    if message.startswith('Include classification'):
        missing = [label for key, label in (('classifications', 'MSC classification'), ('types', 'document type'))
                   if not entry.get(key)]
        return 'has no ' + ' and no '.join(missing or ['classification or document type'])
    if message.startswith('Invalid metadata: '):
        key = message[len('Invalid metadata: '):]
        values = entry.get(key) if isinstance(entry.get(key), list) else []
        problems = sorted({repr(v) for v in values if isinstance(v, str) and values.count(v) > 1})
        problems += sorted(repr(v) for v in values if isinstance(v, str) and v != v.strip())
        return key.replace('_', ' ') + ' ' + ('has duplicate or untrimmed values: ' + ', '.join(problems)
                                              if problems else 'has blank, duplicate or untrimmed values')
    if message.startswith('Use a lowercase'):
        return 'slug ' + repr(entry.get('slug')) + ' is not lowercase words joined by hyphens'
    if message.startswith('Duplicate synonyms ignoring case'):
        return 'synonyms repeat a value that differs only in capitalization'
    return message.rstrip('.')


def diagram_index(database):
    """Return {canonical: set of (hash, source, svg path)} for every entry with stored diagrams."""
    with closing(sqlite3.connect(Path(database).resolve().as_uri() + '?mode=ro', uri=True)) as db:
        try:
            rows = db.execute('SELECT c.canonical_name, d.source_hash, d.source_tex, d.svg_path FROM math_concept_diagrams d '
                              'JOIN math_concepts c ON c.id=d.concept_id').fetchall()
        except sqlite3.DatabaseError:
            return {}  # No diagram table (or not a database): nothing stored to compare.
    index = {}
    for canonical, *row in rows:
        index.setdefault(canonical, set()).add(tuple(row))
    return index


def diagram_blocker(name, state, snapshots):
    """Return why option 2 cannot package this entry's diagram change, or None when it can."""
    try:
        diagram_sync.build_payload(state['base'], state['working'], name, DIAGRAMS, snapshots=snapshots)
    except ValueError as error:
        message = str(error)
        if message.startswith('Diagrams not ready'):
            return ('has diagrams with no rendered SVG in your working copy; choose 19 to render them, then 1 again. '
                    + message[len('Diagrams not ready; run render-missing first. '):])
        entry = dict(snapshots[1].get(name) or {}, canonical_name=name)
        return explain_rejection(entry, message)
    return None


def publish_blocker(name, baseline, working, working_db=None):
    """Return why options 2-5 cannot publish this change, or None when they can.

    This runs the same validation as option 2, so option 1 can report the
    problem before anything is prepared. New entries must meet every new-entry
    rule; existing entries are checked only on what the change touches.
    working_db, when given, is checked for stored diagram SVGs as option 2 does.
    """
    if name not in working:
        return 'deleted locally; deletions are not supported'
    entry = dict(working[name], canonical_name=name)
    if name not in baseline:
        try:
            validate_entry(entry)
        except ValueError as error:
            return 'new entry ' + explain_rejection(entry, str(error))
        return None
    fields = {key for key in working[name] if working[name][key] != baseline[name][key]}
    if fields - {'cleaned_tex', 'synonyms'}:
        return ('changes ' + ', '.join(sorted(fields - {'cleaned_tex', 'synonyms'})) +
                '; only content and synonym changes can be published')
    payload = dict(canonical_name=name, expected=baseline[name], replacement_tex=working[name]['cleaned_tex'])
    if 'synonyms' in fields:
        payload['replacement_synonyms'] = working[name]['synonyms']
    try:
        patch_intended(payload)
    except ValueError as error:
        return 'local version ' + explain_rejection(entry, str(error))
    missing = working_db and local_missing_svgs(working_db, name, working[name]['cleaned_tex'])
    if missing:
        return (f'has {missing} diagram(s) with no stored SVG, so the page would show '
                '"[Diagram unavailable]"; choose 19 to render them, then option 2 publishes the diagrams with the text')
    return None


def changed_entries(state):
    if digest(state['base']) != state['base_sha256']:
        raise ValueError('The saved baseline changed. Select the correct unchanged baseline before continuing.')
    baseline, working = read_snapshot(state['base']), read_snapshot(state['working'])
    base_diagrams, working_diagrams = diagram_index(state['base']), diagram_index(state['working'])
    changes = []
    extract_blocks = diagram_sync.helpers()[0]
    for name in sorted(baseline.keys() | working.keys()):
        diagrams = name in working and base_diagrams.get(name, set()) != working_diagrams.get(name, set())
        if baseline.get(name) == working.get(name) and not diagrams:
            continue
        if name in working and not diagrams:
            # Edited text whose diagrams differ from the stored ones also needs the diagram route.
            planned = {(d['source_hash'], d['source_tex'])
                       for d in diagram_sync.planned_diagrams(working[name]['cleaned_tex'], extract_blocks)}
            stored = {row[:2] for row in working_diagrams.get(name, set())}
            diagrams = planned != stored and (name not in baseline or planned != {
                (d['source_hash'], d['source_tex'])
                for d in diagram_sync.planned_diagrams(baseline[name]['cleaned_tex'], extract_blocks)})
        fields = ([key for key in working[name] if working[name][key] != baseline[name][key]]
                  if name in baseline and name in working else [])
        if diagrams:
            # Stored diagrams changed (an editor rebuild or option 19): SVGs travel with the entry.
            fields.append('diagrams')
            reason = diagram_blocker(name, state, (baseline, working))
        else:
            reason = publish_blocker(name, baseline, working, state['working'])
        changes.append(dict(canonical=name, title=working.get(name, baseline.get(name))['title'],
                            fields=fields, supported=reason is None, reason=reason, new=name not in baseline,
                            diagrams=diagrams))
    return changes


def prepare_selected(state, canonical):
    candidates = {c['canonical']: c for c in changed_entries(state)}
    if canonical not in candidates:
        raise ValueError('No local change found for this entry.')
    package, report, proposed = build_package(state, candidates[canonical], ROOT / 'dist' / 'math-workflow' / uuid.uuid4().hex)
    state['job'] = dict(canonical=canonical, package=str(package), sha256=digest(package),
                        proposed=proposed, remote=None, checked=False)
    save(state)
    return report


def build_package(state, change, folder):
    """Write the review package for one changed entry (an item of changed_entries) into folder, which must be new.

    Return (package path, review text, the entry as the package proposes it).
    """
    canonical = change['canonical']
    if not change['supported']:
        raise ValueError('This change cannot be published through the helper: ' + change['reason'] +
                         '. See "Entries the helper cannot publish" in CONTENT_SYNC.md.')
    folder.mkdir(parents=True)
    package = folder / 'package.zip'
    if change['diagrams']:
        report = diagram_sync.prepare(Path(state['base']), Path(state['working']), canonical, package, DIAGRAMS)
    elif change['new']:
        entry = dict(read_snapshot(state['working'])[canonical], canonical_name=canonical)
        validate_entry(entry)
        with zipfile.ZipFile(package, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('entry.json', json.dumps(entry, ensure_ascii=False, indent=2))
        report = preview(read_package(package))
    else:
        report = prepare(Path(state['base']), Path(state['working']), canonical, package)
    (folder / 'review.txt').write_text(report, encoding='utf-8')
    with zipfile.ZipFile(package) as archive:
        payload = json.loads(archive.read(next(n for n in archive.namelist() if n.endswith('.json'))))
    proposed = (diagram_sync.diagram_intended(payload)[0] if payload.get('kind') == diagram_sync.KIND else
                patch_intended(payload) if 'replacement_tex' in payload else
                {k: sorted(v) if isinstance(v, list) else v for k, v in payload.items() if k != 'canonical_name'})
    return package, report, proposed


def render_missing_diagrams(state, canonical):
    """Render, on this computer, each diagram of one working-copy entry that has no stored SVG."""
    result = diagram_sync.render_missing(state['working'], canonical, DIAGRAMS)
    lines = [f"Rendered: {', '.join(result['rendered']) or 'none'}",
             f"Reused existing SVGs: {', '.join(result['reused']) or 'none'}",
             f"Already stored: {len(result['unchanged'])}; unused rows removed: {result['removed_rows']}",
             'Only your working copy changed. Check the page on the local server, then use 1 and 2 to prepare it.']
    return '\n'.join(lines)


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


def bring_home(state):
    """Option 8: download the live database and refresh the local copies. Return the result, or None if cancelled."""
    print('Stop your local server first (Ctrl+C in its terminal). Old databases and review packages will be preserved.')
    if input('Type STOPPED when the local server is stopped (anything else cancels): ').strip() != 'STOPPED':
        return None
    snapshot = download(Path.home()/'Downloads'/'chi-portfolio'/'database', state['username'])
    result = refresh(state, snapshot, ROOT/'dist'/'home-sync', save, frontend=ROOT/'frontend', diagrams=DIAGRAMS)
    print(result['reason'])
    print('Comparison report:', result['report'])
    if result['safe']:
        print('New working copy:', result['working'])
        print(f"Gallery: {result['photos_verified']} images verified, {result['photos_downloaded']} downloaded; {result['local_drafts_preserved']} local import drafts preserved.")
        print(f"Diagrams: {result['diagrams_verified']} SVGs verified, {result['diagrams_downloaded']} downloaded.")
        if result['diagrams_kept_local']:
            print('Kept your own rendering of the same diagram source:', ', '.join(result['diagrams_kept_local']))
        if result['diagrams_missing_on_server']:
            print('Missing on the server too (those pages show a broken image):', ', '.join(result['diagrams_missing_on_server']))
        print('Choose 6 to restart the local server using this copy. Website program files and other media were not downloaded.')
    else:
        print('Saved paths and existing databases are unchanged. Review the report before proceeding.')
    return result


def main():
    state = json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else None
    while True:
        print('\nWebsite update helper')
        if state:
            print('Working copy:', state['working'])
            print('Selected entry:', (state.get('job') or {}).get('canonical', '(none)'))
        print('1. Show local changes\n2. Prepare an entry for review\n3. Stage reviewed package\n4. Check live\n5. Publish reviewed package\n6. Start local server\n7. Set baseline and working paths\n8. Bring website changes home\n9. Prepare biography or resume update\n10. Open Google Photos import\n11. Prepare a new photo for publication\n12. Prepare changes to existing photo details\n13. Prepare removal from the gallery (keep image)\n14. Prepare frontend files (HTML, CSS, JavaScript)\n15. Prepare Python and matching frontend files\n16. Retry code reload and homepage verification\n17. Upload Esri map key\n18. Prepare saved gallery display settings\n19. Render missing diagrams for an entry\n20. Publish a batch of new entries\n0. Exit')
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
                    if not item['supported']:
                        print('   Why:', item['reason'])
                if any(not item['supported'] for item in changes):
                    print('Entries marked [unsupported] cannot be prepared with option 2. '
                          'See "Entries the helper cannot publish" in CONTENT_SYNC.md.')
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
                bring_home(state)
            elif choice == '20':
                import batch_publish
                batch_publish.run(state)
            elif choice == '9':
                print(prepare_profile(state, input('Page to prepare (bio or resume): ').strip()))
                print('Review the changes above, then choose 3 to stage, 4 to check live, and 5 to publish.')
            elif choice == '10':
                print('Keep the local server running (option 6 in another terminal). Opening the photo review page.')
                webbrowser.open('http://127.0.0.1:5001/api/photography/google/manage')
            elif choice == '19':
                canonical = input('Canonical name of the entry (as option 1 shows it in brackets): ').strip()
                if canonical:
                    print(render_missing_diagrams(state, canonical))
            elif choice == '18':
                print(prepare_frontend(state, ['photography/gallery-settings.js']))
                print('Review the saved photo count, then use 3 (stage), 4 (check live), 5 (publish).')
            elif choice == '17':
                print('Uploading your saved Esri key. SSH may ask for your PythonAnywhere password.')
                print(upload_esri_key.upload(state['username']))
                print('Key setup complete. Publish the map code with option 15 when ready.')
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
