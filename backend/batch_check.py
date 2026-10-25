"""Check frozen new-entry packages against the live database over SSH, without applying them.

Two modes, both read-only on the server:
- projected: the whole batch, in publish order, against a private in-memory copy
  of the live database in which each eligible entry is added before the next is
  checked, so an entry may depend on one scheduled earlier in the batch;
- strict (projected=False): each package against the live database as it is, so
  every related concept and explicit link target must really exist there.

Each result carries the same verdict the single-entry live check gives
(NO DUPLICATE FOUND, ALREADY PRESENT, BLOCKED or CONFLICT) and the resolution
of every \\PMlinkname target, with the site's renderer and resolution rules.
"""
import base64
from contextlib import closing
import hashlib
import io
import json
from pathlib import Path
import re
import shlex
import shutil
import sqlite3
import subprocess
import sys
import zipfile

from batch_links import entry_links, name_index

# The single-entry preflight's modules plus these two. Only these local, reviewed modules are sent.
MODULES = ('pythonanywhere_api', 'stage_pythonanywhere_package', 'preview_math_sync', 'publish_math_entry',
           'apply_math_text_patch', 'profile_sync', 'photo_sync', 'photo_metadata_sync', 'photo_removal_sync',
           'frontend_sync', 'diagram_sync', 'math_schema', 'inspect_staged_package', 'batch_links', 'batch_check')
READY = ('NO DUPLICATE FOUND', 'ALREADY PRESENT')
LOADER = '''
import sys, json, types, hashlib, base64
from pathlib import Path
from datetime import datetime, timezone
config = json.load(sys.stdin)
for name, source in config['modules']:
    module = types.ModuleType(name)
    module.__file__ = '<trusted-local-batch-check>/' + name + '.py'
    sys.modules[name] = module
    exec(compile(source, module.__file__, 'exec'), module.__dict__)
'''
# Read-only: the canonical names on the live site now, for planning a batch.
CATALOG_BOOTSTRAP = LOADER + '''
from batch_check import catalog
print('BATCH_CATALOG_RESULT=' + json.dumps(catalog(Path(config['database']))))
'''
BOOTSTRAP = LOADER + '''
from stage_pythonanywhere_package import read_package, validate_package
from batch_check import check_items
packages = []
for item in config['items']:
    data = read_package(Path(item['remote'])) if 'remote' in item else validate_package(base64.b64decode(item['data']))
    if hashlib.sha256(data).hexdigest() != item['sha256']:
        raise SystemExit('A package differs from the reviewed one. Batch check stopped; nothing approved.')
    packages.append(data)
database = Path(config['database'])
results = check_items(packages, database, database.parent / 'src', database.parent / 'data' / 'math' / 'diagrams',
                      config['projected'])
print('BATCH_CHECK_RESULT=' + json.dumps(dict(checked_utc=datetime.now(timezone.utc).isoformat(),
                                              sha256=[item['sha256'] for item in config['items']], results=results)))
'''


def catalog(database):
    """Return the canonical names in database, read-only."""
    with closing(sqlite3.connect(Path(database).resolve().as_uri() + '?mode=ro', uri=True)) as db:
        return sorted(row[0] for row in db.execute('SELECT canonical_name FROM math_concepts WHERE canonical_name IS NOT NULL'))


def catalog_request(username):
    if not re.fullmatch(r'[A-Za-z0-9_]+', username):
        raise ValueError('Invalid username.')
    return dict(database=f'/home/{username}/chi-portfolio/backend/portfolio.db',
                modules=[(name, Path(__file__).with_name(name + '.py').read_text(encoding='utf-8')) for name in MODULES])


def live_catalog(username):
    """Read the live site's canonical names over SSH, without changing anything."""
    request = catalog_request(username)
    if not shutil.which('ssh'):
        raise ValueError('Windows OpenSSH Client is required.')
    result = subprocess.run(['ssh', username + '@ssh.pythonanywhere.com', 'python3.13 -I -B -c ' + shlex.quote(CATALOG_BOOTSTRAP)],
                            input=json.dumps(request), stdout=subprocess.PIPE, text=True, encoding='utf-8', check=True)
    return read_catalog(result.stdout)


def read_catalog(stdout):
    lines = [line[len('BATCH_CATALOG_RESULT='):] for line in stdout.splitlines() if line.startswith('BATCH_CATALOG_RESULT=')]
    if len(lines) != 1:
        raise ValueError('No unambiguous list of live entries received; nothing prepared.')
    names = json.loads(lines[0])
    if not isinstance(names, list) or not all(isinstance(name, str) for name in names):
        raise ValueError('Invalid list of live entries; nothing prepared.')
    return names


def read_item(data):
    """Return (payload, files, entry) for one new-entry package: a text entry or a new entry with diagrams."""
    import diagram_sync
    from publish_math_entry import validate as validate_entry
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names = archive.namelist()
    if 'diagrams.json' in names:
        payload, files = diagram_sync.unpack(data)
        if 'entry' not in payload:
            raise ValueError('Batches publish new entries only; ' + str(payload.get('canonical_name')) + ' is an existing entry.')
        return payload, files, payload['entry']
    if names != ['entry.json']:
        raise ValueError('Batches publish new entries only (one entry.json or one diagram package per entry).')
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        payload = json.loads(archive.read('entry.json'))
    validate_entry(payload)
    return payload, None, payload


def check_items(packages, database, source_dir, diagram_dir, projected):
    """Return one result per package, in order; never writes to database or diagram_dir."""
    source_dir = Path(source_dir)
    # Isolated SSH processes do not inherit the site's import path.
    if str(source_dir.resolve()) not in sys.path:
        sys.path.insert(0, str(source_dir.resolve()))
    import diagram_sync
    from inspect_staged_package import new_entry_status
    from publish_math_entry import insert_entry
    from services.math.render_helper import render_prose_latex_to_html
    with closing(sqlite3.connect(Path(database).resolve().as_uri() + '?mode=ro', uri=True)) as live, \
            closing(sqlite3.connect(':memory:')) as work:
        # A private copy: projected entries are added to it, never to the live file.
        live.backup(work)
        results = []
        for data in packages:
            payload, files, entry = read_item(data)
            canonical = entry['canonical_name']
            status = (diagram_sync.status(database, diagram_dir, payload, files, source_dir, connection=work)
                      if files is not None else new_entry_status(work, payload))
            names = {row[0] for row in work.execute('SELECT canonical_name FROM math_concepts')} | {canonical}
            links = entry_links(canonical, entry['cleaned_tex'], render_prose_latex_to_html, name_index(sorted(names)))
            results.append(dict(canonical=canonical, sha256=hashlib.sha256(data).hexdigest(), status=status, links=links))
            if projected and status.startswith('NO DUPLICATE FOUND'):
                insert_entry(work, entry, '')
        return results


def problems(result, projected=False):
    """Return why one checked entry cannot be published; empty when it can (or is already present)."""
    found = [] if result['status'].startswith(READY) else [result['status']]
    for link in result['links']:
        if link['status'] == 'ambiguous':
            found.append(f"explicit link \"{link['text']}\" → {link['target']} matches more than one canonical name")
        elif link['status'] != 'resolved':
            found.append(f"explicit link \"{link['text']}\" → {link['target']} matches no live entry"
                         + (' or entry scheduled earlier in the batch' if projected else ''))
    return found


def build_request(username, items, projected):
    """items: dicts with package (local path) and, for a staged copy to check, remote."""
    if not re.fullmatch(r'[A-Za-z0-9_]+', username):
        raise ValueError('Invalid username.')
    request_items = []
    for item in items:
        data = Path(item['package']).read_bytes()
        entry = dict(sha256=hashlib.sha256(data).hexdigest())
        if item.get('remote'):
            if not re.fullmatch(re.escape(f'/home/{username}/chi-portfolio-staging/') + r'[0-9a-f]{32}/package\.zip',
                                item['remote']):
                raise ValueError('Use the exact private staging path from the uploader.')
            entry['remote'] = item['remote']
        else:
            entry['data'] = base64.b64encode(data).decode('ascii')
        request_items.append(entry)
    return dict(items=request_items, projected=bool(projected),
                database=f'/home/{username}/chi-portfolio/backend/portfolio.db',
                modules=[(name, Path(__file__).with_name(name + '.py').read_text(encoding='utf-8')) for name in MODULES])


def run(username, items, projected, output):
    """Run the check over SSH; write the report to output (a new file) and return the parsed response."""
    if output.exists() or not output.parent.is_dir():
        raise ValueError('Choose a new report filename in an existing directory.')
    request = build_request(username, items, projected)
    if not shutil.which('ssh'):
        raise ValueError('Windows OpenSSH Client is required.')
    command = 'python3.13 -I -B -c ' + shlex.quote(BOOTSTRAP)
    result = subprocess.run(['ssh', username + '@ssh.pythonanywhere.com', command],
                            input=json.dumps(request), stdout=subprocess.PIPE,
                            text=True, encoding='utf-8', check=True)
    return read_response(result.stdout, request, output)


def read_response(stdout, request, output):
    lines = [line[len('BATCH_CHECK_RESULT='):] for line in stdout.splitlines() if line.startswith('BATCH_CHECK_RESULT=')]
    if len(lines) != 1:
        raise ValueError('No unambiguous batch check result received; nothing approved.')
    response = json.loads(lines[0])
    expected = [item['sha256'] for item in request['items']]
    if response.get('sha256') != expected or [r.get('sha256') for r in response.get('results', [])] != expected:
        raise ValueError('Invalid batch check response; nothing approved.')
    with output.open('x', encoding='utf-8') as stream:
        stream.write(('Projected' if request['projected'] else 'Live') + ' batch check at ' + response['checked_utc'] + '\n')
        for result in response['results']:
            stream.write(result['canonical'] + ': ' + result['status'] + '\n')
            for link in result['links']:
                stream.write(f"  link \"{link['text']}\" → {link['target']}: {link['status']}"
                             + (f" ({link['canonical']})" if link['canonical'] else '') + '\n')
    return response
