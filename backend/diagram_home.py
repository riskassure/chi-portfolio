"""Bring generated math diagram SVGs home: compare rows by content, download missing files additively."""
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import sqlite3
import subprocess

from diagram_sync import SVG_LIMIT, URL_PREFIX, check_svg

NAME_RE = re.compile(r'[0-9a-f]{16}\.svg')
TOTAL_LIMIT = 200 * 1024 * 1024
MANIFEST_SCRIPT = r'''
import hashlib, json, re, sys
from pathlib import Path
config = json.load(sys.stdin)
folder = Path('/home/' + config['username'] + '/chi-portfolio/backend/data/math/diagrams')
result = {}
for name in config['names']:
    assert re.fullmatch(r'[0-9a-f]{16}\.svg', name)
    target = folder / name
    if target.is_symlink() or not target.is_file():
        result[name] = None
        continue
    data = target.read_bytes()
    result[name] = {'sha256': hashlib.sha256(data).hexdigest(), 'size': len(data)}
print('DIAGRAM_MANIFEST=' + json.dumps(result))
'''


def rows(db):
    """Return diagram rows as (canonical, hash, source, svg path), ignoring ids, order and timestamps."""
    try:
        return [tuple(row) for row in db.execute(
            'SELECT c.canonical_name, d.source_hash, d.source_tex, d.svg_path FROM math_concept_diagrams d '
            'JOIN math_concepts c ON c.id=d.concept_id')]
    except sqlite3.OperationalError:
        return []  # A database without diagram tables has nothing to bring home.


def referenced(db):
    """Return the hash-named SVG files the database's diagram rows point at."""
    names = {row[3][len(URL_PREFIX):] for row in rows(db) if isinstance(row[3], str) and row[3].startswith(URL_PREFIX)}
    return sorted(name for name in names if NAME_RE.fullmatch(name))


def remote_manifest(username, names):
    if not re.fullmatch(r'[A-Za-z0-9_]+', username):
        raise ValueError('Invalid account username.')
    result = subprocess.run(
        ['ssh', username + '@ssh.pythonanywhere.com', 'python3.13 -I -B -c ' + shlex.quote(MANIFEST_SCRIPT)],
        input=json.dumps(dict(username=username, names=names)), text=True,
        stdout=subprocess.PIPE, check=True)
    lines = [line for line in result.stdout.splitlines() if line.startswith('DIAGRAM_MANIFEST=')]
    if len(lines) != 1:
        raise ValueError('Server did not return a diagram manifest.')
    return json.loads(lines[0].split('=', 1)[1])


def check_file(path, entry):
    data = path.read_bytes() if path.is_file() and not path.is_symlink() else b''
    if len(data) != entry['size'] or hashlib.sha256(data).hexdigest() != entry['sha256']:
        raise ValueError('Missing or different diagram file: ' + str(path))
    check_svg(data)


def stage_media(username, names, diagrams, folder):
    """Download the live SVGs this computer lacks into folder; never touch an existing local file.

    Returns (manifest, staged, report). A local file with different bytes is
    kept when it is a valid SVG (it renders the same diagram source) and
    stops the refresh when it is not. A file the server itself lacks is
    reported, since nothing here can supply it.
    """
    manifest = remote_manifest(username, names)
    if not isinstance(manifest, dict) or set(manifest) != set(names):
        raise ValueError('Diagram manifest does not match the snapshot rows.')
    total = 0
    for name, entry in manifest.items():
        if entry is None:
            continue
        if (not isinstance(entry, dict) or type(entry.get('size')) is not int or not 0 < entry['size'] <= SVG_LIMIT
                or not isinstance(entry.get('sha256'), str) or not re.fullmatch('[a-f0-9]{64}', entry['sha256'])):
            raise ValueError('Invalid diagram manifest entry.')
        total += entry['size']
        if total > TOTAL_LIMIT:
            raise ValueError('Diagrams exceed the 200 MB synchronization limit; review required.')
    report = dict(verified=[], kept_local=[], missing_on_server=[])
    staged = []
    for index, name in enumerate(names):
        entry, target = manifest[name], Path(diagrams) / name
        if entry is None:
            report['missing_on_server'].append(name)
        elif target.exists() or target.is_symlink():
            data = target.read_bytes() if target.is_file() and not target.is_symlink() else b''
            if hashlib.sha256(data).hexdigest() == entry['sha256']:
                report['verified'].append(name)
            else:
                try:
                    check_svg(data)
                except ValueError:
                    raise ValueError(f'Local diagram {target} differs from live and is not a usable SVG. '
                                     'Remove it, then refresh again.') from None
                report['kept_local'].append(name)
        else:
            temporary = Path(folder) / ('diagram-' + str(index) + '.partial')
            remote = f'{username}@ssh.pythonanywhere.com:/home/{username}/chi-portfolio/backend/data/math/diagrams/{name}'
            subprocess.run(['scp', remote, str(temporary)], check=True)
            check_file(temporary, entry)
            staged.append((name, temporary))
    (Path(folder) / 'diagram-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    return manifest, staged, report


def install_media(diagrams, manifest, staged):
    diagrams = Path(diagrams)
    diagrams.mkdir(parents=True, exist_ok=True)
    for name, temporary in staged:
        check_file(temporary, manifest[name])
        try:
            os.link(temporary, diagrams / name)  # Atomic creation; never replaces a file.
        except FileExistsError:
            check_svg((diagrams / name).read_bytes())
        temporary.unlink()
