"""Read and preview a staged math package without extracting or executing it."""
import argparse
from contextlib import closing
import difflib
import hashlib
import io
import json
from pathlib import Path
import re
import sqlite3
from urllib.error import URLError
from urllib.request import Request, build_opener
import zipfile

from pythonanywhere_api import HOST, SETTINGS, NoRedirects, validate
from stage_pythonanywhere_package import MAX_BYTES, read_package, validate_package
from publish_math_entry import validate as validate_entry, check_target
from preview_math_sync import read_snapshot
from apply_math_text_patch import patch_intended
import profile_sync
import photo_sync
import photo_metadata_sync
import photo_removal_sync
import frontend_sync
import diagram_sync


def fetch_verified(settings, remote, local):
    validate(settings)
    prefix = f"/home/{settings['username']}/chi-portfolio-staging/"
    if not remote.startswith(prefix) or not re.fullmatch(r'[0-9a-f]{32}/package\.zip', remote[len(prefix):]):
        raise ValueError('Use the exact private staging path printed by the uploader.')
    expected = read_package(local)
    request = Request(f"{HOST}/api/v0/user/{settings['username']}/files/path{remote}",
                      headers={'Authorization': 'Token ' + settings['token']}, method='GET')
    try:
        with build_opener(NoRedirects()).open(request, timeout=120) as response:
            data = response.read(MAX_BYTES + 1)
    except (URLError, TimeoutError, OSError):
        raise RuntimeError('Could not read the staged package. Check the path, connection and API settings.') from None
    if hashlib.sha256(data).digest() != hashlib.sha256(expected).digest():
        raise ValueError('Staged package differs from the local reviewed ZIP. Stop and review it again.')
    return validate_package(data)


def preview(data, snapshot=None, *, live=False):
    validate_package(data)
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names = archive.namelist()
        report = ['Verified package SHA-256: ' + hashlib.sha256(data).hexdigest(),
                  'Files (none executed):'] + ['  ' + json.dumps(n) for n in names]
        payloads = [n for n in names if n.endswith('.json')]
        if len(payloads) != 1:
            raise ValueError('Preview supports exactly one math JSON payload per package.')
        payload = json.loads(archive.read(payloads[0]))
    if not isinstance(payload, dict):
        raise ValueError('Invalid math payload.')
    if payload.get('kind') in ('frontend-files', 'website-code'):
        frontend_sync.unpack(data, payload)
        report += [frontend_sync.review(payload)]
        if snapshot:
            frontend = Path(snapshot).resolve().parent.parent/'frontend' if live else Path(__file__).resolve().parents[1]/'frontend'
            if payload['kind'] == 'website-code':
                frontend = frontend.parent
            status = frontend_sync.status(payload, frontend)
    elif payload.get('kind') == 'photo-remove':
        photo_removal_sync.unpack(data, payload)
        report += ['Proposed operation: REMOVE one gallery entry', 'Photo: '+payload['file_path'],
                   json.dumps(payload['expected'], ensure_ascii=False, indent=2),
                   'Image SHA-256: '+payload['sha256'],
                   'The image file is retained and remains accessible at its direct URL.',
                   'The entry stays in your local gallery until option 8 refreshes it after publication.']
        if snapshot:
            frontend = Path(snapshot).resolve().parent.parent/'frontend' if live else Path(__file__).resolve().parents[1]/'frontend'
            status = photo_removal_sync.status(snapshot, payload, frontend)
    elif payload.get('kind') == 'photo-edit':
        photo_metadata_sync.unpack(data, payload)
        report += ['Proposed operation: update existing photo details', 'Photo: '+payload['file_path']]
        for key in photo_metadata_sync.FIELDS:
            if payload['expected'][key] != payload['replacement'][key]:
                report += ['Field: '+key, 'Before: '+json.dumps(payload['expected'][key], ensure_ascii=False),
                           'After: '+json.dumps(payload['replacement'][key], ensure_ascii=False)]
        report += ['Image SHA-256 (image unchanged): '+payload['sha256']]
        if snapshot:
            frontend = Path(snapshot).resolve().parent.parent/'frontend' if live else Path(__file__).resolve().parents[1]/'frontend'
            status = photo_metadata_sync.status(snapshot, payload, frontend)
    elif payload.get('kind') == 'photo-add':
        image = photo_sync.unpack(data, payload)
        report += ['Proposed operation: add one gallery photo', json.dumps(payload['photo'],ensure_ascii=False,indent=2),
                   'Image SHA-256: ' + payload['sha256']]
        if snapshot:
            frontend = Path(snapshot).resolve().parent.parent/'frontend' if live else Path(__file__).resolve().parents[1]/'frontend'
            status = photo_sync.status(snapshot,payload,image,frontend)
    elif payload.get('kind') == 'profile':
        profile_sync.validate_payload(payload)
        report += ['Proposed operation: update profile page ' + payload['page']]
        for key, value in sorted(payload['replacement'].items()):
            old = payload['expected']['fields'].get(key)
            if old != value:
                report += ['Field: ' + key, 'Before: ' + json.dumps(old, ensure_ascii=False),
                           'After: ' + json.dumps(value, ensure_ascii=False)]
        if snapshot:
            frontend = Path(snapshot).resolve().parent.parent/'frontend' if live else Path(__file__).resolve().parents[1]/'frontend'
            status = profile_sync.status(snapshot, payload, frontend)
    elif payload.get('kind') == diagram_sync.KIND:
        payload, files = diagram_sync.unpack(data)
        source = Path(snapshot).resolve().parent/'src' if live else None
        report += [diagram_sync.review(payload, source)]
        if snapshot:
            # A downloaded snapshot has no diagram files beside it; only the live check reads them.
            diagrams = Path(snapshot).resolve().parent/'data'/'math'/'diagrams' if live else None
            status = diagram_sync.status(snapshot, diagrams, payload, files, source)
    elif 'replacement_tex' in payload:
        intended = patch_intended(payload)
        canonical = payload['canonical_name']
        expected = payload['expected']
        report += ['Proposed operation: change existing entry text and/or synonyms', 'Entry: ' + canonical]
        report += list(difflib.unified_diff(expected['cleaned_tex'].splitlines(),
                      payload['replacement_tex'].splitlines(), fromfile='expected text',
                      tofile='proposed text', lineterm=''))
        if 'replacement_synonyms' in payload:
            report += ['Synonyms added: ' + json.dumps(sorted(set(intended['synonyms']) - set(expected['synonyms']))),
                       'Synonyms removed: ' + json.dumps(sorted(set(expected['synonyms']) - set(intended['synonyms'])))]
        if snapshot:
            current = read_snapshot(snapshot).get(canonical)
            status = ('ALREADY PRESENT — no update needed' if current == intended else
                      'EXPECTED TEXT MATCHES — eligible for further review' if current == expected else
                      'CONFLICT — snapshot differs from expected entry')
    else:
        validate_entry(payload)
        report += ['Proposed operation: add one new entry', json.dumps(payload, ensure_ascii=False, indent=2)]
        if snapshot:
            with closing(sqlite3.connect(Path(snapshot).resolve().as_uri() + '?mode=ro', uri=True)) as db:
                records = read_snapshot(snapshot, connection=db)
                intended = {k: sorted(v) if isinstance(v, list) else v
                            for k, v in payload.items() if k != 'canonical_name'}
                if records.get(payload['canonical_name']) == intended:
                    status = 'ALREADY PRESENT — do not apply again'
                else:
                    try:
                        check_target(db, payload)
                        status = 'NO DUPLICATE FOUND — eligible for further review'
                    except ValueError as error:
                        status = 'BLOCKED — ' + str(error)
    if snapshot:
        report += [('File root: '+str(frontend) if payload.get('kind') in ('frontend-files', 'website-code') else
                    ('Live database: ' if live else 'Comparison snapshot: ') + str(Path(snapshot).resolve())), status,
                   ('Read-only file check; files may change after this check.' if payload.get('kind') in ('frontend-files', 'website-code') else
                    'Checked in a consistent read-only transaction; live content may change after this check.'
                    if live else 'This checks the supplied snapshot, not the current live database.')]
    else:
        report += [('Live eligibility NOT CHECKED: run a separate live preflight after staging.'
                    if payload.get('kind') in ('frontend-files', 'website-code') else
                    'Live eligibility NOT CHECKED: no database snapshot supplied.')]
    report += ['Nothing extracted, executed, applied or reloaded. Publication requires separate live checks.']
    return '\n'.join(report)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('remote', help='Exact staged package path')
    parser.add_argument('--local', type=Path, required=True, help='Original reviewed ZIP')
    parser.add_argument('--snapshot', type=Path, help='Optional fresh downloaded live snapshot')
    parser.add_argument('--output', type=Path, required=True, help='New local review report filename')
    args = parser.parse_args()
    try:
        if args.output.exists():
            raise ValueError('Report already exists. Choose a new output filename.')
        settings = validate(json.loads(SETTINGS.read_text(encoding='utf-8')))
        report = preview(fetch_verified(settings, args.remote, args.local), args.snapshot)
        with args.output.open('x', encoding='utf-8') as stream:
            stream.write(report + '\n')
        print('Inspection complete. Read the review report:', args.output.resolve())
        print('No files were extracted or executed. The website and database are unchanged.')
    except (ValueError, RuntimeError) as error:
        raise SystemExit(str(error))
    except (OSError, sqlite3.Error, KeyError, TypeError):
        raise SystemExit('Could not inspect the package. Check input files, payload format and output directory.')
