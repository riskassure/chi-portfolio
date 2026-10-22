"""Prepare math entries whose PSTricks diagrams changed, with SVGs rendered on this computer.

The server never runs LaTeX for these entries. Each diagram's SVG is rendered
locally, checked, and shipped in the package beside the entry; the package
names every file by its source hash and SHA-256 so the server can verify it.
Images, embeds and any other media must stay exactly as they are (see
publish_math_entry.media_fragments).
"""
import argparse
from contextlib import closing, contextmanager, nullcontext
from datetime import datetime, timezone
import difflib
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import uuid
import zipfile
from xml.etree import ElementTree

from apply_math_text_patch import patch_intended
from preview_math_sync import read_snapshot
from publish_math_entry import check_target, insert_entry, validate as validate_entry

KIND = 'math-diagrams'
SVG_LIMIT = 2 * 1024 * 1024
URL_PREFIX = '/api/math/diagrams/'
HASH_RE = re.compile(r'[0-9a-f]{16}')
SVG_NS = '{http://www.w3.org/2000/svg}'
# Stands in for each PSTricks block when checking the rest of the text. It
# matches nothing in publish_math_entry.MEDIA_RE, so masked text is "plain".
MASK = '@@PSTRICKS-DIAGRAM@@'
ACTIVE_ELEMENTS = {'script', 'foreignobject', 'iframe', 'object', 'embed', 'handler', 'listener'}
# Diagrams are static. Animation can rewrite an attribute (such as href) after
# the checks below have looked at it, so none is allowed.
ANIMATION_ELEMENTS = {'set', 'animate', 'animatemotion', 'animatetransform', 'animatecolor', 'discard', 'mpath'}


def helpers(source_dir=None):
    """Return (extract_blocks, hash_block) from render_helper, the site's own diagram finder."""
    source = str(Path(source_dir) if source_dir else Path(__file__).resolve().parent / 'src')
    if source not in sys.path:
        sys.path.insert(0, source)
    from services.math.render_helper import extract_all_pstricks_diagram_blocks, hash_pstricks_block
    return extract_all_pstricks_diagram_blocks, hash_pstricks_block


def svg_name(source_hash):
    return source_hash + '.svg'


def check_svg(data):
    """Raise ValueError unless data is a small, well-formed SVG with nothing active in it.

    The file is served from the site's own origin, so a script or external
    link in it would run if someone opened the SVG directly.
    """
    if not isinstance(data, bytes) or not data or len(data) > SVG_LIMIT:
        raise ValueError('An SVG of at most 2 MB is required.')
    try:
        text = data.decode('utf-8')
    except UnicodeError:
        raise ValueError('SVG is not UTF-8 text.') from None
    if re.search(r'<!\s*(?:DOCTYPE|ENTITY)', text, re.I):
        raise ValueError('SVG must not declare a DOCTYPE or entities.')
    try:
        root = ElementTree.fromstring(data)
    except ElementTree.ParseError:
        raise ValueError('SVG is not well-formed XML.') from None
    if root.tag != SVG_NS + 'svg':
        raise ValueError('File is not an SVG document.')
    for element in root.iter():
        name = element.tag.rsplit('}', 1)[-1].lower() if isinstance(element.tag, str) else ''
        if name in ACTIVE_ELEMENTS:
            raise ValueError('SVG contains a <' + name + '> element.')
        if name in ANIMATION_ELEMENTS:
            raise ValueError('SVG contains an animation element <' + name + '>; diagrams must be static.')
        styles = [element.text or ''] if name == 'style' else []
        for attribute, value in element.attrib.items():
            local = attribute.rsplit('}', 1)[-1].lower()
            if local.startswith('on'):
                raise ValueError('SVG contains an event handler attribute.')
            if local == 'href' and not value.startswith('#'):
                raise ValueError('SVG links outside itself.')
            styles.append(value)
        for style in styles:
            if '@import' in style.lower() or any(not url.strip(' \'"').startswith(('#', 'data:'))
                                                 for url in re.findall(r'url\(([^)]*)\)', style, re.I)):
                raise ValueError('SVG style refers to an outside resource.')


def planned_diagrams(tex, extract_blocks):
    """Return one record per distinct PSTricks diagram in tex, in source order."""
    planned = {}
    for block in extract_blocks(tex):
        planned.setdefault(block['source_hash'], block['conversion_source'])
    return [dict(source_hash=h, source_tex=s) for h, s in planned.items()]


def masked(tex, extract_blocks):
    """Return tex with every PSTricks diagram replaced by MASK."""
    for block in reversed(extract_blocks(tex)):
        tex = tex[:block['start']] + MASK + tex[block['end']:]
    return tex


def stored_diagrams(db, canonical):
    """Return the diagram rows stored for one entry, sorted by hash."""
    try:
        rows = db.execute('SELECT d.source_hash, d.source_tex, d.svg_path FROM math_concept_diagrams d '
                          'JOIN math_concepts c ON c.id=d.concept_id WHERE c.canonical_name=? '
                          'ORDER BY d.source_hash', (canonical,)).fetchall()
    except sqlite3.OperationalError:
        return []
    return [dict(source_hash=r[0], source_tex=r[1], svg_path=r[2]) for r in rows]


def _check_records(records, keys):
    if not isinstance(records, list):
        raise ValueError('Invalid diagram list.')
    seen = set()
    for record in records:
        if not isinstance(record, dict) or set(record) != keys:
            raise ValueError('Invalid diagram record.')
        if not isinstance(record['source_hash'], str) or not HASH_RE.fullmatch(record['source_hash']):
            raise ValueError('Invalid diagram hash.')
        if not isinstance(record['source_tex'], str) or record['source_hash'] in seen:
            raise ValueError('Invalid or repeated diagram.')
        seen.add(record['source_hash'])


def diagram_intended(payload, source_dir=None):
    """Return (entry, diagram rows) a diagram package produces, or raise ValueError if it is unsafe.

    Existing entries keep the content/synonym rules of a text patch, and new
    entries the full new-entry rules, with every PSTricks block masked out.
    The package's diagrams must be exactly the distinct PSTricks blocks of
    the resulting text, and must differ from the rows it was prepared against.
    """
    extract_blocks, hash_block = helpers(source_dir)
    if not isinstance(payload, dict) or payload.get('kind') != KIND:
        raise ValueError('Invalid diagram package.')
    common = {'kind', 'canonical_name', 'expected_diagrams', 'diagrams'}
    existing = common | {'expected', 'replacement_tex'}
    if set(payload) - {'replacement_synonyms'} == existing:
        patch = {k: payload[k] for k in ('canonical_name', 'expected', 'replacement_tex', 'replacement_synonyms')
                 if k in payload}
        if not isinstance(payload['expected'], dict) or not isinstance(payload['replacement_tex'], str) \
                or not isinstance(payload['expected'].get('cleaned_tex'), str):
            raise ValueError('Invalid existing-entry fields.')
        # Text rules apply with the diagrams masked; other media must stay byte-identical.
        patch_intended(dict(patch, expected=dict(patch['expected'],
                                                 cleaned_tex=masked(patch['expected']['cleaned_tex'], extract_blocks)),
                            replacement_tex=masked(patch['replacement_tex'], extract_blocks)))
        entry = dict(patch_intended(dict(patch, replacement_tex=patch['expected']['cleaned_tex'])),
                     cleaned_tex=patch['replacement_tex'])
    elif set(payload) == common | {'entry'}:
        new = payload['entry']
        if not isinstance(new, dict) or new.get('canonical_name') != payload['canonical_name'] \
                or not isinstance(new.get('cleaned_tex'), str):
            raise ValueError('Invalid new entry.')
        validate_entry(dict(new, cleaned_tex=masked(new['cleaned_tex'], extract_blocks)))
        if payload['expected_diagrams']:
            raise ValueError('A new entry has no stored diagrams.')
        entry = {k: sorted(v) if isinstance(v, list) else v for k, v in new.items() if k != 'canonical_name'}
    else:
        raise ValueError('Invalid diagram package fields.')
    _check_records(payload['expected_diagrams'], {'source_hash', 'source_tex', 'svg_path'})
    _check_records(payload['diagrams'], {'source_hash', 'source_tex', 'sha256', 'bytes'})
    for record in payload['diagrams']:
        if hash_block(record['source_tex']) != record['source_hash']:
            raise ValueError('Diagram hash does not match its source.')
        if not isinstance(record['sha256'], str) or not re.fullmatch(r'[0-9a-f]{64}', record['sha256']) \
                or type(record['bytes']) is not int or not 0 < record['bytes'] <= SVG_LIMIT:
            raise ValueError('Invalid diagram checksum or size.')
    planned = planned_diagrams(entry['cleaned_tex'], extract_blocks)
    if planned != [dict(source_hash=r['source_hash'], source_tex=r['source_tex']) for r in payload['diagrams']]:
        raise ValueError('Package diagrams do not match the PSTricks blocks in the entry.')
    before = {(r['source_hash'], r['source_tex']) for r in payload['expected_diagrams']}
    if before == {(r['source_hash'], r['source_tex']) for r in planned}:
        raise ValueError('No diagram change; publish text edits with the existing-entry patch.')
    rows = [dict(block_index=index, source_hash=r['source_hash'], source_tex=r['source_tex'],
                 svg_path=URL_PREFIX + svg_name(r['source_hash'])) for index, r in enumerate(planned, 1)]
    return entry, rows


def local_files(database, canonical, tex, diagram_dir, source_dir=None):
    """Return (records, files) for each diagram in tex, from the working database and diagrams folder.

    Raise ValueError naming every diagram that has no matching row or no
    valid file, or any row the text no longer uses.
    """
    extract_blocks, _ = helpers(source_dir)
    planned = planned_diagrams(tex, extract_blocks)
    with closing(sqlite3.connect(Path(database).resolve().as_uri() + '?mode=ro', uri=True)) as db:
        rows = {r['source_hash']: r for r in stored_diagrams(db, canonical)}
    problems, records, files = [], [], {}
    for item in planned:
        name = svg_name(item['source_hash'])
        row = rows.get(item['source_hash'])
        if not row or row['source_tex'] != item['source_tex'] or row['svg_path'] != URL_PREFIX + name:
            problems.append(name + ': no matching diagram row')
            continue
        path = Path(diagram_dir) / name
        if path.is_symlink() or not path.is_file():
            problems.append(name + ': SVG file missing')
            continue
        data = path.read_bytes()
        try:
            check_svg(data)
        except ValueError as error:
            problems.append(name + ': ' + str(error))
            continue
        records.append(dict(item, sha256=hashlib.sha256(data).hexdigest(), bytes=len(data)))
        files[item['source_hash']] = data
    problems += [svg_name(h) + ': row no longer used by the text' for h in rows.keys() - {p['source_hash'] for p in planned}]
    if problems:
        raise ValueError('Diagrams not ready; run render-missing first. ' + '; '.join(problems))
    return records, files


def render_svg(source_tex):
    """Render one PSTricks block to SVG bytes with LaTeX and dvisvgm, in a throwaway folder."""
    helpers()
    from database.math.pipeline.step2_build_diagrams import wrap_pstricks_document
    for tool in ('latex', 'dvisvgm'):
        if not shutil.which(tool):
            raise ValueError(tool + ' is not installed on this computer.')
    with tempfile.TemporaryDirectory(prefix='chi-diagram-') as folder:
        Path(folder, 'diagram.tex').write_text(wrap_pstricks_document(source_tex), encoding='utf-8')
        for stage, command in (('latex', ['latex', '-interaction=nonstopmode', 'diagram.tex']),
                               ('dvisvgm', ['dvisvgm', 'diagram.dvi', '-o', 'diagram.svg'])):
            result = subprocess.run(command, cwd=folder, capture_output=True, text=True, timeout=300)
            if result.returncode:
                tail = '\n'.join(((result.stdout or '') + (result.stderr or '')).splitlines()[-15:])
                raise ValueError(f'Diagram failed at {stage}:\n{tail}')
        return Path(folder, 'diagram.svg').read_bytes()


def place_file(diagram_dir, name, data):
    """Create diagram_dir/name with data without ever replacing a file; return True if created.

    The bytes go to a temporary name first and are linked into place, so a
    crash never leaves a partial file under the real name.
    """
    target = Path(diagram_dir) / name
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name('.incoming-' + uuid.uuid4().hex)
    try:
        with temporary.open('xb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, target)
        except FileExistsError:
            return False
    finally:
        temporary.unlink(missing_ok=True)
    if target.read_bytes() != data:
        raise ValueError(name + ' failed verification after writing.')
    return True


def render_missing(database, canonical, diagram_dir, render=None, source_dir=None):
    """Render and store each diagram of one entry that has no row or no valid SVG in the working copy.

    Existing valid files are reused and never replaced. Rows the text no
    longer uses are removed, and the stored page HTML is rebuilt from the
    stored SVGs, as the local editor would after a diagram rebuild.
    """
    render = render or render_svg
    extract_blocks, _ = helpers(source_dir)
    from services.math.concept_render_service import render_tex_reusing_existing_diagrams
    summary = dict(rendered=[], reused=[], unchanged=[], removed_rows=0)
    with closing(sqlite3.connect(Path(database).resolve().as_uri() + '?mode=rw', uri=True, timeout=10)) as db:
        db.execute('BEGIN IMMEDIATE')
        row = db.execute('SELECT id, cleaned_tex FROM math_concepts WHERE canonical_name=?', (canonical,)).fetchone()
        if not row:
            raise ValueError('Entry not found in the working database.')
        ident, tex = row[0], row[1] or ''
        planned = planned_diagrams(tex, extract_blocks)
        rows = {r['source_hash']: r for r in stored_diagrams(db, canonical)}
        stamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for index, item in enumerate(planned, 1):
            name = svg_name(item['source_hash'])
            path = Path(diagram_dir) / name
            current = rows.get(item['source_hash'])
            if path.is_file() and not path.is_symlink():
                try:
                    check_svg(path.read_bytes())
                except ValueError as error:
                    raise ValueError(f'{path} exists but is not usable ({error}). Remove it, then run this again.') from None
                if current and current['source_tex'] == item['source_tex'] and current['svg_path'] == URL_PREFIX + name:
                    summary['unchanged'].append(name)
                    continue
                summary['reused'].append(name)
            elif path.exists() or path.is_symlink():
                raise ValueError(f'{path} is not a regular file. Remove it, then run this again.')
            else:
                data = render(item['source_tex'])
                check_svg(data)
                if not place_file(diagram_dir, name, data):
                    check_svg(path.read_bytes())  # Created meanwhile by another writer; keep it if usable.
                summary['rendered'].append(name)
            db.execute('INSERT INTO math_concept_diagrams(concept_id, block_index, source_hash, source_tex, svg_path, created_at) '
                       'VALUES(?,?,?,?,?,?) ON CONFLICT(concept_id, source_hash) DO UPDATE SET '
                       'block_index=excluded.block_index, source_tex=excluded.source_tex, svg_path=excluded.svg_path',
                       (ident, index, item['source_hash'], item['source_tex'], URL_PREFIX + name, stamp))
        stale = rows.keys() - {p['source_hash'] for p in planned}
        for source_hash in stale:
            db.execute('DELETE FROM math_concept_diagrams WHERE concept_id=? AND source_hash=?', (ident, source_hash))
        summary['removed_rows'] = len(stale)
        db.execute('UPDATE math_concepts SET rendered_tex=? WHERE id=?',
                   (render_tex_reusing_existing_diagrams(ident, tex, db.cursor()), ident))
        db.commit()
    return summary


def build_payload(base, local, canonical, diagram_dir, source_dir=None, snapshots=None):
    """Return (payload, files) for one entry's diagram change between baseline and working copy.

    snapshots, when given, is (baseline, working) as read_snapshot already returned them.
    """
    baseline, working = snapshots or (read_snapshot(base), read_snapshot(local))
    if canonical not in working:
        raise ValueError('Entry not found in the local working database.')
    proposed = working[canonical]
    records, files = local_files(local, canonical, proposed['cleaned_tex'], diagram_dir, source_dir)
    if canonical in baseline:
        expected = baseline[canonical]
        changed = {key for key in expected if expected[key] != proposed[key]}
        if changed - {'cleaned_tex', 'synonyms'}:
            raise ValueError('Only content, synonym and diagram changes can be published for an existing entry.')
        with closing(sqlite3.connect(Path(base).resolve().as_uri() + '?mode=ro', uri=True)) as db:
            before = stored_diagrams(db, canonical)
        payload = dict(kind=KIND, canonical_name=canonical, expected=expected,
                       replacement_tex=proposed['cleaned_tex'], expected_diagrams=before, diagrams=records)
        if 'synonyms' in changed:
            payload['replacement_synonyms'] = proposed['synonyms']
    else:
        payload = dict(kind=KIND, canonical_name=canonical, entry=dict(proposed, canonical_name=canonical),
                       expected_diagrams=[], diagrams=records)
    entry, _ = diagram_intended(payload, source_dir)
    if entry != proposed:
        raise ValueError('Package does not exactly reproduce the selected local entry.')
    return payload, files


def write_package(payload, files, output):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('diagrams.json', json.dumps(payload, ensure_ascii=False, indent=2))
        for record in payload['diagrams']:
            archive.writestr('svg/' + svg_name(record['source_hash']), files[record['source_hash']])
    with Path(output).open('xb') as stream:
        stream.write(buffer.getvalue())
    return buffer.getvalue()


def unpack(data):
    """Return (payload, files) from a diagram package, checking every SVG against its record."""
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        payload = json.loads(archive.read('diagrams.json'))
        if not isinstance(payload, dict) or not isinstance(payload.get('diagrams'), list):
            raise ValueError('Invalid diagram package.')
        expected = {'diagrams.json'} | {'svg/' + svg_name(r.get('source_hash', '')) for r in payload['diagrams']
                                         if isinstance(r, dict)}
        if set(archive.namelist()) != expected or len(archive.namelist()) != len(expected):
            raise ValueError('Diagram packages contain diagrams.json and one svg/<hash>.svg per diagram only.')
        files = {}
        for record in payload['diagrams']:
            data = archive.read('svg/' + svg_name(record['source_hash']))
            if hashlib.sha256(data).hexdigest() != record.get('sha256') or len(data) != record.get('bytes'):
                raise ValueError(svg_name(record['source_hash']) + ' does not match its checksum.')
            check_svg(data)
            files[record['source_hash']] = data
    return payload, files


def review(payload, source_dir=None):
    """Return a plain-text summary of a diagram package for review before staging."""
    entry, rows = diagram_intended(payload, source_dir)
    before = {r['source_hash'] for r in payload['expected_diagrams']}
    after = {r['source_hash'] for r in rows}
    report = ['Proposed operation: ' + ('add one new entry with diagrams' if 'entry' in payload else
                                        'change existing entry diagrams' +
                                        (' and text' if payload['replacement_tex'] != payload['expected']['cleaned_tex'] else '')),
              'Entry: ' + payload['canonical_name']]
    if 'entry' in payload:
        report.append(json.dumps(payload['entry'], ensure_ascii=False, indent=2))
    else:
        report += list(difflib.unified_diff(payload['expected']['cleaned_tex'].splitlines(),
                                            payload['replacement_tex'].splitlines(), fromfile='expected text',
                                            tofile='proposed text', lineterm=''))
        if 'replacement_synonyms' in payload:
            report += ['Synonyms: ' + json.dumps(entry['synonyms'], ensure_ascii=False)]
    sizes = {r['source_hash']: r['bytes'] for r in payload['diagrams']}
    report += [f'Diagram added: {svg_name(h)} ({sizes[h]} bytes)' for h in sorted(after - before)]
    report += [f'Diagram kept: {svg_name(h)}' for h in sorted(after & before)]
    report += [f'Diagram row removed: {svg_name(h)} (the file stays on the server)' for h in sorted(before - after)]
    report += ['SVGs were rendered on this computer; the server will not run LaTeX.']
    return '\n'.join(report)


def prepare(base, local, canonical, output, diagram_dir, source_dir=None):
    payload, files = build_payload(base, local, canonical, diagram_dir, source_dir)
    unpack(write_package(payload, files, output))
    return review(payload, source_dir)


# ---- Server side: verify files, place them, then update rows in one transaction ----

JOURNALS = 'diagram-publish'
INCOMING = 'diagrams-incoming'
LOCK = '.lock'
LOCK_WAIT = 30
ELIGIBLE = ('EXPECTED TEXT MATCHES', 'NO DUPLICATE FOUND')


def _checkpoint(step):
    """Called after each recorded step of apply. Does nothing; tests use it to interrupt a run."""


def _try_lock(stream):
    if os.name == 'nt':
        import msvcrt
        stream.seek(0)
        msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
    else:
        import fcntl
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)


def _unlock(stream):
    if os.name == 'nt':
        import msvcrt
        stream.seek(0)
        msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        import fcntl
        fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


@contextmanager
def publish_lock(journals):
    """Hold the lock that diagram publishing and recovery share.

    A publish holds it from its first check until its rows are committed, and
    recovery holds it while it checks references and deletes, so recovery can
    never remove a file a publish is about to use. The operating system drops
    the lock if the process dies.
    """
    journals = Path(journals)
    journals.mkdir(parents=True, exist_ok=True)
    with open(journals / LOCK, 'a+b') as stream:
        deadline = time.monotonic() + LOCK_WAIT
        while True:
            try:
                _try_lock(stream)
                break
            except OSError:
                if time.monotonic() > deadline:
                    raise ValueError('Another diagram publish or recovery is running. Nothing changed.') from None
                time.sleep(0.2)
        try:
            yield
        finally:
            _unlock(stream)


def _row_set(rows):
    return {(r['source_hash'], r['source_tex'], r['svg_path']) for r in rows}


def file_state(diagram_dir, record):
    """Return 'missing', 'identical', 'kept' (a different but valid SVG) or 'unusable' for one target file.

    File names come from the diagram source, so a different valid file is a
    rendering of the same diagram; it is kept and never overwritten.
    """
    path = Path(diagram_dir) / svg_name(record['source_hash'])
    if path.is_symlink() or (path.exists() and not path.is_file()):
        return 'unusable'
    if not path.exists():
        return 'missing'
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() == record['sha256']:
        return 'identical'
    try:
        check_svg(data)
    except ValueError:
        return 'unusable'
    return 'kept'


def status(database, diagram_dir, payload, files, source_dir=None, connection=None):
    """Return a one-line verdict on applying payload to database; never writes.

    diagram_dir None skips the file checks (for a downloaded snapshot).
    """
    entry, rows = diagram_intended(payload, source_dir)
    canonical = payload['canonical_name']
    states = ({r['source_hash']: file_state(diagram_dir, r) for r in payload['diagrams']}
              if diagram_dir is not None else {})
    unusable = sorted(svg_name(h) for h, state in states.items() if state == 'unusable')
    if unusable:
        return 'CONFLICT — unusable diagram file on the server: ' + ', '.join(unusable) + '; review required'
    with (nullcontext(connection) if connection is not None else
          closing(sqlite3.connect(Path(database).resolve().as_uri() + '?mode=ro', uri=True))) as db:
        current = read_snapshot(database, connection=db).get(canonical)
        stored = stored_diagrams(db, canonical)
        if current == entry and _row_set(stored) == _row_set(rows) and 'missing' not in states.values():
            return 'ALREADY PRESENT — entry, diagram rows and SVG files match'
        if 'entry' in payload:
            if current is not None:
                return 'CONFLICT — an entry with this canonical name already exists'
            try:
                check_target(db, payload['entry'])
            except ValueError as error:
                return 'BLOCKED — ' + str(error)
            verdict = 'NO DUPLICATE FOUND — eligible for further review'
        else:
            if current != payload['expected']:
                return 'CONFLICT — snapshot differs from expected entry'
            if _row_set(stored) != _row_set(payload['expected_diagrams']):
                return 'CONFLICT — stored diagram rows differ from the reviewed ones'
            verdict = 'EXPECTED TEXT MATCHES — eligible for further review'
    kept = sorted(svg_name(h) for h, state in states.items() if state == 'kept')
    if kept:
        verdict += '; the server already has a different valid SVG for ' + ', '.join(kept) + ', which will be kept'
    return verdict


def _write_journal(path, journal):
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(journal, indent=2), encoding='utf-8')
    os.replace(temporary, path)


def _backup(database, backup_dir):
    backup = Path(backup_dir) / ('before-diagram-publish-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
                                 + '-' + uuid.uuid4().hex[:8] + '.db')
    with backup.open('xb'):
        pass
    with closing(sqlite3.connect(Path(database).resolve().as_uri() + '?mode=ro', uri=True)) as source, \
            closing(sqlite3.connect(backup)) as destination:
        source.backup(destination)
        if destination.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise ValueError('Backup failed integrity check.')
    return backup


def apply(database, payload, files, backup_dir, source_dir, diagram_dir, package_sha256):
    """Publish one diagram package: files first, then every row in one transaction.

    A journal in backup_dir/diagram-publish/<package sha256>.json records each
    step. An interrupted run leaves only unused hash-named SVGs (and possibly a
    backup); running the same package again skips files already in place.
    Existing files are never replaced or deleted. The whole run holds
    publish_lock, so recovery cannot run in the middle of it.
    """
    with publish_lock(Path(backup_dir) / JOURNALS):
        return _apply(database, payload, files, backup_dir, source_dir, diagram_dir, package_sha256)


def _apply(database, payload, files, backup_dir, source_dir, diagram_dir, package_sha256):
    entry, rows = diagram_intended(payload, source_dir)
    if not re.fullmatch(r'[0-9a-f]{64}', package_sha256 or ''):
        raise ValueError('Invalid package checksum.')
    for record in payload['diagrams']:
        data = files.get(record['source_hash'])
        if not isinstance(data, bytes) or hashlib.sha256(data).hexdigest() != record['sha256']:
            raise ValueError(svg_name(record['source_hash']) + ' does not match its checksum.')
        check_svg(data)
    canonical = payload['canonical_name']
    outcome = status(database, diagram_dir, payload, files, source_dir)
    if outcome.startswith('ALREADY PRESENT'):
        return dict(status='ALREADY_PRESENT', canonical=canonical, backup=None)
    if not outcome.startswith(ELIGIBLE):
        raise ValueError(outcome)
    diagram_dir, backup_dir = Path(diagram_dir), Path(backup_dir)
    journals = backup_dir / JOURNALS
    journals.mkdir(parents=True, exist_ok=True)
    journal_path = journals / (package_sha256 + '.json')
    if journal_path.exists():
        journal = json.loads(journal_path.read_text(encoding='utf-8'))
        if journal.get('canonical') != canonical:
            raise ValueError('Journal belongs to a different entry. Nothing changed.')
    else:
        # pre_existing is recorded once, so a retry still knows which files this package created.
        journal = dict(package_sha256=package_sha256, canonical=canonical,
                       started_utc=datetime.now(timezone.utc).isoformat(), backup=None,
                       files={svg_name(r['source_hash']): dict(sha256=r['sha256'],
                                                               pre_existing=file_state(diagram_dir, r) != 'missing',
                                                               state='planned') for r in payload['diagrams']})
    journal.update(status='FILES_PENDING', attempt_utc=datetime.now(timezone.utc).isoformat())
    _write_journal(journal_path, journal)
    _checkpoint('journal')
    incoming = diagram_dir.parent / INCOMING / uuid.uuid4().hex
    try:
        for record in payload['diagrams']:
            name = svg_name(record['source_hash'])
            if file_state(diagram_dir, record) == 'missing':
                if not incoming.exists():
                    # Recorded before the folder exists, so recovery removes only this run's folders.
                    journal.setdefault('incoming', []).append(incoming.name)
                    _write_journal(journal_path, journal)
                    incoming.mkdir(parents=True)
                temporary = incoming / name
                with temporary.open('xb') as stream:
                    stream.write(files[record['source_hash']])
                    stream.flush()
                    os.fsync(stream.fileno())
                if hashlib.sha256(temporary.read_bytes()).hexdigest() != record['sha256']:
                    raise ValueError(name + ' failed verification after writing. Nothing committed.')
                _checkpoint('incoming:' + name)
                try:
                    os.link(temporary, diagram_dir / name)  # Fails rather than replace a file.
                except FileExistsError:
                    pass
            state = file_state(diagram_dir, record)
            if state not in ('identical', 'kept'):
                raise ValueError(name + ' could not be placed (' + state + '). Nothing committed.')
            journal['files'][name]['state'] = 'placed' if state == 'identical' else 'kept_live_copy'
            _write_journal(journal_path, journal)
            _checkpoint('placed:' + name)
    finally:
        shutil.rmtree(incoming, ignore_errors=True)
    journal['status'] = 'FILES_PLACED'
    _write_journal(journal_path, journal)
    _checkpoint('files')
    extract_blocks, _ = helpers(source_dir)
    from services.math.concept_render_service import render_tex_reusing_existing_diagrams
    with closing(sqlite3.connect(Path(database).resolve().as_uri() + '?mode=rw', uri=True, timeout=10)) as db:
        db.execute('PRAGMA foreign_keys=ON')
        db.execute('BEGIN IMMEDIATE')
        # Repeat every check under the write lock; another writer may have acted since.
        outcome = status(database, diagram_dir, payload, files, source_dir, connection=db)
        if outcome.startswith('ALREADY PRESENT'):
            return dict(status='ALREADY_PRESENT', canonical=canonical, backup=None)
        if not outcome.startswith(ELIGIBLE):
            raise ValueError(outcome + '. Nothing committed.')
        if any(file_state(diagram_dir, r) not in ('identical', 'kept') for r in payload['diagrams']):
            raise ValueError('A diagram file is missing after placement. Nothing committed.')
        backup = _backup(database, backup_dir)
        journal['backup'] = str(backup)
        _write_journal(journal_path, journal)
        _checkpoint('backup')
        now = datetime.now(timezone.utc).isoformat()
        if 'entry' in payload:
            ident = insert_entry(db, payload['entry'], '')
        else:
            ident = db.execute('SELECT id FROM math_concepts WHERE canonical_name=?', (canonical,)).fetchone()[0]
            db.execute('UPDATE math_concepts SET cleaned_tex=?, updated_at=? WHERE id=?',
                       (entry['cleaned_tex'], now, ident))
            if 'replacement_synonyms' in payload:
                db.execute('DELETE FROM math_synonyms WHERE concept_id=?', (ident,))
                db.executemany('INSERT INTO math_synonyms(concept_id,synonym_text) VALUES(?,?)',
                               [(ident, synonym) for synonym in entry['synonyms']])
        stale = {r['source_hash'] for r in stored_diagrams(db, canonical)} - {r['source_hash'] for r in rows}
        db.executemany('DELETE FROM math_concept_diagrams WHERE concept_id=? AND source_hash=?',
                       [(ident, source_hash) for source_hash in stale])
        for row in rows:
            db.execute('INSERT INTO math_concept_diagrams(concept_id, block_index, source_hash, source_tex, svg_path, created_at) '
                       'VALUES(?,?,?,?,?,?) ON CONFLICT(concept_id, source_hash) DO UPDATE SET '
                       'block_index=excluded.block_index, source_tex=excluded.source_tex, svg_path=excluded.svg_path',
                       (ident, row['block_index'], row['source_hash'], row['source_tex'], row['svg_path'],
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        try:
            db.execute('DELETE FROM math_concept_diagram_failures WHERE concept_id=?', (ident,))
        except sqlite3.OperationalError:
            pass  # Older databases have no failure table.
        rendered = render_tex_reusing_existing_diagrams(ident, entry['cleaned_tex'], db.cursor())
        if 'Diagram unavailable' in rendered:
            raise ValueError('A diagram would show as unavailable. Nothing committed.')
        db.execute('UPDATE math_concepts SET rendered_tex=? WHERE id=?', (rendered, ident))
        _checkpoint('rows')
        if read_snapshot(database, connection=db).get(canonical) != entry or \
                _row_set(stored_diagrams(db, canonical)) != _row_set(rows):
            raise ValueError('Verification failed. Nothing committed.')
        db.commit()
    journal.update(status='COMMITTED', completed_utc=datetime.now(timezone.utc).isoformat())
    _write_journal(journal_path, journal)
    _checkpoint('committed')
    kept = sorted(name for name, item in journal['files'].items() if item['state'] == 'kept_live_copy')
    return dict(status='APPLIED', canonical=canonical, backup=str(backup), kept_live_copies=kept)


def cleanup(journal_path, database, diagram_dir, remove=False):
    """List (and with remove=True delete) leftovers of one publish attempt.

    Only files this package created, that no diagram row references and that
    still hold the package's bytes are listed, plus the incoming folders this
    package's journal recorded. Files that existed before the attempt, and
    other publishes' folders, are never touched. It holds publish_lock, and
    while deleting it also holds the database's write lock, so no publish or
    other writer can start using a file between the reference check and the
    deletion.
    """
    journal_path, diagram_dir = Path(journal_path), Path(diagram_dir)
    with publish_lock(journal_path.parent):
        journal = json.loads(journal_path.read_text(encoding='utf-8'))
        mode = 'rw' if remove else 'ro'
        with closing(sqlite3.connect(Path(database).resolve().as_uri() + '?mode=' + mode, uri=True,
                                     timeout=10, isolation_level=None)) as db:
            if remove:
                db.execute('BEGIN IMMEDIATE')
            referenced = {row[0].rsplit('/', 1)[-1] for row in db.execute('SELECT svg_path FROM math_concept_diagrams')}
            files = []
            for name, item in sorted(journal['files'].items()):
                path = diagram_dir / name
                if (not item['pre_existing'] and item['state'] == 'placed' and name not in referenced
                        and path.is_file() and not path.is_symlink()
                        and hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256']):
                    files.append(name)
            incoming = diagram_dir.parent / INCOMING
            owned = {name for name in journal.get('incoming', []) if re.fullmatch(r'[0-9a-f]{32}', name)}
            present = {p.name for p in incoming.iterdir()} if incoming.is_dir() else set()
            folders = sorted(name for name in owned & present
                             if (incoming / name).is_dir() and not (incoming / name).is_symlink())
            others = sorted(present - owned)
            if remove:
                for name in files:
                    (diagram_dir / name).unlink()
                for name in folders:
                    shutil.rmtree(incoming / name)
                db.execute('ROLLBACK')  # Nothing was written; the transaction only held the lock.
        if remove:
            journal.setdefault('cleaned', []).append(dict(utc=datetime.now(timezone.utc).isoformat(),
                                                          files=files, incoming=folders))
            _write_journal(journal_path, journal)
    return dict(status=journal.get('status'), unused_files=files, incoming_folders=folders,
                other_incoming_folders=others, removed=remove)


if __name__ == '__main__':
    helpers()
    from config import MATH_DIAGRAM_DIR
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    missing = sub.add_parser('render-missing', help='Render diagrams with no stored SVG into the working copy')
    missing.add_argument('--db', type=Path, required=True, help='Working database (never the live copy)')
    missing.add_argument('--canonical', required=True)
    missing.add_argument('--diagrams', type=Path, default=MATH_DIAGRAM_DIR)
    prep = sub.add_parser('prepare', help='Package one entry with changed diagrams for review')
    for name in ('base', 'local', 'output'):
        prep.add_argument('--' + name, type=Path, required=True)
    prep.add_argument('--canonical', required=True)
    prep.add_argument('--diagrams', type=Path, default=MATH_DIAGRAM_DIR)
    args = parser.parse_args()
    try:
        if args.action == 'render-missing':
            print(json.dumps(render_missing(args.db, args.canonical, args.diagrams), indent=2))
        else:
            print(prepare(args.base, args.local, args.canonical, args.output, args.diagrams))
    except (ValueError, OSError, sqlite3.Error) as error:
        raise SystemExit('Stopped; nothing published. ' + str(error))
