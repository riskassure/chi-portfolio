"""Publish a reviewed batch of new math entries, one at a time (helper option 20).

The batch keeps the single-entry standards: nothing in the working copy,
baseline or live site changes before you type PUBLISH ALL (only review files
under dist/math-batches/<batch id>/ are written); each entry is published from
the package you reviewed, through the existing stage, live check and publish
steps; and authored links are never changed to make an order work.

1. Select new entries and name the batch. Every blocker is reported first.
2. Order them so each entry follows the entries it needs: its related concepts
   and its \\PMlinkname targets. A loop blocks the batch; remove the entries in
   it (and the entries that need them) from the selection, or wait for a
   publisher that can handle loops.
3. Freeze one package per entry, write a review, and check the whole batch
   against a projected copy of the live database (read-only, over SSH).
4. After PUBLISH ALL, publish each package. Right before each one, a live check
   confirms that its dependencies really exist on the site. It stops at the
   first conflict; an unconfirmed publish is reconciled with the live site
   before any retry.
5. Record your visual check of the live pages, then run option 8.

Progress is saved in the batch manifest after every step, so choosing 20
again resumes where it stopped.
"""
from contextlib import closing, contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import time
import uuid

import batch_check
from batch_links import cycles, dependants, entry_links, name_index, publish_order
import diagram_sync
from preview_math_sync import read_snapshot
from publish_staged_package import publish_staged
from pythonanywhere_api import SETTINGS, validate
from stage_pythonanywhere_package import stage
import website_workflow as w

BATCHES = w.ROOT / 'dist' / 'math-batches'
SITE = 'https://www.cwoo.me'
LOCAL_SITE = 'http://127.0.0.1:5001'
PAUSE = 20
WAITS = (30, 60, 120)
DONE = ('applied', 'already_present')


class BatchStopped(ValueError):
    """The batch stopped at a known point; the manifest says where."""


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ---- Manifest ----
def save_manifest(manifest):
    path = Path(manifest['folder']) / 'manifest.json'
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    w.replace_file(temporary, path)


def load_manifest(state):
    path = state.get('batch')
    if not path:
        return None
    path = Path(path) / 'manifest.json'
    if not path.is_file():
        raise ValueError('The saved batch manifest is missing: ' + str(path))
    return json.loads(path.read_text(encoding='utf-8'))


def fingerprint(manifest):
    """What PUBLISH ALL approves: these exact packages, in this order."""
    frozen = [(name, manifest['entries'][name]['sha256']) for name in manifest['order']]
    return hashlib.sha256(json.dumps(frozen).encode()).hexdigest()


@contextmanager
def locked(manifest):
    """Stop two option 20 runs working on the same batch at once."""
    lock = Path(manifest['folder']) / '.lock'
    try:
        handle = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise BatchStopped('Another option 20 run is working on this batch (lock file ' + str(lock) +
                           '). If no other helper window is running it, delete that file and choose 20 again.') from None
    try:
        os.write(handle, json.dumps(dict(pid=os.getpid(), started=now())).encode())
        os.close(handle)
        yield
    finally:
        lock.unlink(missing_ok=True)


def record(manifest, name, operation, outcome, **details):
    manifest['entries'][name]['history'].append(dict(details, operation=operation, outcome=outcome, at=now()))
    save_manifest(manifest)


# ---- Planning (writes review files only) ----
def draft_digests(working, names):
    """Fingerprint each entry as the working copy holds it now: its record, diagram rows and SVG files."""
    snapshot = read_snapshot(working)
    result = {}
    with closing(sqlite3.connect(Path(working).resolve().as_uri() + '?mode=ro', uri=True)) as db:
        for name in names:
            if name not in snapshot:
                result[name] = None
                continue
            rows = diagram_sync.stored_diagrams(db, name)
            files = []
            for row in rows:
                path = w.DIAGRAMS / row['svg_path'].rsplit('/', 1)[-1]
                files.append(digest(path) if path.is_file() else None)
            result[name] = hashlib.sha256(json.dumps([snapshot[name], rows, files], sort_keys=True,
                                                     ensure_ascii=False).encode()).hexdigest()
    return result


def candidates(state):
    """Return (new entries, other local changes) compared with the baseline."""
    changes = w.changed_entries(state)
    return [c for c in changes if c['new']], [c for c in changes if not c['new']]


def renderer():
    source = str(Path(__file__).resolve().parent / 'src')
    if source not in sys.path:
        sys.path.insert(0, source)
    from services.math.render_helper import render_prose_latex_to_html
    return render_prose_latex_to_html


def duplicates(selected, working):
    """Name clashes between entries of the batch, with the publisher's own matching rules."""
    def key(value):
        return value.strip().lower()
    found = []
    for i, first in enumerate(selected):
        for second in selected[i + 1:]:
            a, b = dict(working[first], canonical_name=first), dict(working[second], canonical_name=second)
            for column in ('canonical_name', 'slug', 'title'):
                if key(a[column]) == key(b[column]):
                    found.append(f'{first} and {second} have the same {column}')
        for other in selected:
            if other == first:
                continue
            terms = {key(t) for t in working[other]['synonyms'] + working[other]['definitions']}
            if key(working[first]['title']) in terms:
                found.append(f"{first}'s title is a synonym or defined term of {other}")
    return found


def dependencies(selected, live, working):
    """Return (graph, links per entry, blockers). graph maps each entry to the batch entries it needs first.

    live is the set of canonical names on the live site now, not the (possibly older) baseline.
    """
    render = renderer()
    index = name_index(sorted(set(live) | set(selected)))
    unselected = name_index(sorted(set(working) - set(live) - set(selected)))
    graph, links, blockers = {}, {}, []
    for name in selected:
        needs = set()
        for target in working[name]['related_concepts']:
            if target in selected:
                needs.add(target)
            elif target not in live:
                blockers.append(f'{name} is related to {target}, which is not on the live site ' +
                                ('and not in this batch' if target in working else 'or in your working copy'))
        links[name] = entry_links(name, working[name]['cleaned_tex'], render, index)
        for link in links[name]:
            if link['status'] == 'ambiguous':
                blockers.append(f"{name}: explicit link \"{link['text']}\" → {link['target']} matches more than one canonical name")
            elif link['status'] == 'unresolved':
                hint = (' (a local entry not in this batch)' if link['target'].casefold() in unselected else '')
                blockers.append(f"{name}: explicit link \"{link['text']}\" → {link['target']} matches no live "
                                f"entry or entry in this batch{hint}")
            elif link['canonical'] in selected and not link['self_link']:
                needs.add(link['canonical'])
        graph[name] = needs
    return graph, links, blockers


def plan(state, selected, title, live_names):
    """Check the selected new entries and, if nothing blocks them, freeze the batch.

    live_names are the canonical names on the live site now (batch_check.live_catalog): related
    concepts and link targets outside the batch must be there, whatever the baseline says.
    Return (manifest or None, report lines). Only files under dist/math-batches are written.
    """
    new = {c['canonical']: c for c in w.changed_entries(state) if c['new']}
    working = read_snapshot(state['working'])
    blockers = [f"{name}: {new[name]['reason']}" for name in selected if not new[name]['supported']]
    blockers += duplicates(selected, working)
    graph, links, found = dependencies(selected, set(live_names), working)
    blockers += found
    for loop in cycles(graph):
        blockers.append('These entries need each other in a loop, so no order works: ' + ' ↔ '.join(loop) +
                        '. Authored links are kept as they are. To go ahead, remove ' +
                        ', '.join(loop + dependants(graph, loop)) + ' from the selection.')
    if blockers:
        return None, ['Nothing was prepared. Fix these first:'] + ['  - ' + b for b in blockers]
    order = publish_order(graph, selected)
    batch_id = datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:6]
    folder = BATCHES / batch_id
    folder.mkdir(parents=True)
    drafts = draft_digests(state['working'], order)
    entries, reviews = {}, []
    for position, name in enumerate(order, 1):
        package, review, _ = w.build_package(state, new[name], folder / 'packages' / f'{position:02d}-{working[name]["slug"]}')
        checksums = []
        if new[name]['diagrams']:
            previews = folder / 'previews'
            previews.mkdir(exist_ok=True)
            payload, files = diagram_sync.unpack(package.read_bytes())
            for record_ in payload['diagrams']:
                svg = previews / (working[name]['slug'] + '-' + diagram_sync.svg_name(record_['source_hash']))
                svg.write_bytes(files[record_['source_hash']])
                checksums.append(dict(file=svg.name, sha256=record_['sha256']))
        entries[name] = dict(position=position, title=working[name]['title'], slug=working[name]['slug'],
                             package=str(package), sha256=digest(package), review=str(package.parent / 'review.txt'),
                             diagrams=bool(new[name]['diagrams']), diagram_files=checksums,
                             related=sorted(working[name]['related_concepts']), links=links[name],
                             needs=sorted(graph[name]), draft=drafts[name], state='pending', remote=None, history=[])
        reviews.append((name, review))
    manifest = dict(version=1, batch_id=batch_id, name=title, folder=str(folder), created=now(),
                    base=state['base'], base_sha256=state['base_sha256'], working=state['working'],
                    username=state['username'], selected=list(selected), order=order,
                    pause_seconds=state.get('batch_pause_seconds', PAUSE), entries=entries,
                    review_file=str(folder / 'review.txt'), checks=[], approval=None, publication='planned',
                    verification=None, synchronization=None)
    (folder / 'review.txt').write_text(review_text(manifest, reviews), encoding='utf-8')
    save_manifest(manifest)
    return manifest, summary(manifest)


def describe_links(entry):
    lines = []
    for link in entry['links']:
        where = 'this entry itself' if link['self_link'] else link['canonical']
        lines.append(f"    explicit link \"{link['text']}\" → {link['target']} resolves to {where}")
    return lines


def summary(manifest):
    lines = [f"Batch \"{manifest['name']}\" ({manifest['batch_id']}): {len(manifest['order'])} entries, in publish order:"]
    for name in manifest['order']:
        entry = manifest['entries'][name]
        lines.append(f"{entry['position']:>3}. {entry['title']} — slug {entry['slug']}, canonical {name}"
                     + (' [diagrams]' if entry['diagrams'] else ''))
        if entry['related']:
            lines.append('    related: ' + ', '.join(entry['related']))
        if entry['needs']:
            lines.append('    published after: ' + ', '.join(entry['needs']))
        lines += describe_links(entry)
    return lines


def review_text(manifest, reviews):
    lines = summary(manifest) + ['', 'Baseline: ' + manifest['base'], 'Working copy: ' + manifest['working'],
                                 'Approving publishes exactly these package files (SHA-256):']
    lines += [f"  {name}: {manifest['entries'][name]['sha256']}" for name in manifest['order']]
    for name, review in reviews:
        entry = manifest['entries'][name]
        lines += ['', '=' * 78, f"{entry['position']}. {entry['title']} ({name})",
                  'Local page while the local server runs: ' + LOCAL_SITE + '/math/concept.html?slug=' + entry['slug']]
        lines += [f"Diagram preview: {Path(manifest['folder']) / 'previews' / item['file']} (SHA-256 {item['sha256']})"
                  for item in entry['diagram_files']]
        lines += ['-' * 78, review]
    return '\n'.join(lines) + '\n'


# ---- Checks against the live site (read-only) ----
def check(manifest, names, projected, remote=False):
    """Run the batch check over SSH for names; return {name: (result, problems)}."""
    folder = Path(manifest['folder']) / 'checks'
    folder.mkdir(exist_ok=True)
    report = folder / (('projected-' if projected else 'live-') + uuid.uuid4().hex[:8] + '.txt')
    items = [dict(package=manifest['entries'][n]['package'], remote=manifest['entries'][n]['remote'] if remote else None)
             for n in names]
    response = batch_check.run(manifest['username'], items, projected, report)
    manifest['checks'].append(dict(at=response['checked_utc'], projected=projected, entries=list(names), report=str(report)))
    save_manifest(manifest)
    return {r['canonical']: (r, batch_check.problems(r, projected)) for r in response['results']}


def retried(step, what):
    """Run a step that is safe to repeat (staging, a read-only check), waiting and retrying on connection errors."""
    for attempt, wait in enumerate(WAITS + (None,), 1):
        try:
            return step()
        except (RuntimeError, OSError, subprocess.CalledProcessError) as error:
            if wait is None:
                raise BatchStopped(f'{what} kept failing ({error}). Nothing more was published; choose 20 to try again.') from None
            print(f'{what} failed ({error}); retry {attempt} in {wait}s', flush=True)
            time.sleep(wait)


# ---- Integrity of what was approved ----
def frozen_problems(manifest):
    """Pending entries whose frozen package is missing or no longer matches the review."""
    found = []
    for name in manifest['order']:
        entry = manifest['entries'][name]
        if entry['state'] in DONE:
            continue
        path = Path(entry['package'])
        if not path.is_file():
            found.append(f'{name}: package missing ({path})')
        elif digest(path) != entry['sha256']:
            found.append(f'{name}: package changed since review ({path})')
    return found


def later_drafts(manifest, state):
    """Pending entries whose working-copy version changed after the batch was frozen."""
    pending = [n for n in manifest['order'] if manifest['entries'][n]['state'] not in DONE]
    current = draft_digests(state['working'], pending) if pending else {}
    return [n for n in pending if current[n] != manifest['entries'][n]['draft']]


def confirm_frozen(manifest, state):
    """Stop if a frozen package changed; explain any later local edits before publishing anything."""
    problems = frozen_problems(manifest)
    if problems:
        manifest['approval'] = None
        manifest['publication'] = 'invalidated'
        save_manifest(manifest)
        raise BatchStopped('The approval no longer holds, because a frozen package changed or went missing:\n  ' +
                           '\n  '.join(problems) + '\nNothing more was published. Set this batch aside with option 20 '
                           'and start a new batch to review those entries again; entries already live will show as '
                           'already present.')
    changed = later_drafts(manifest, state)
    if not changed:
        return
    print('These entries changed in your working copy after you reviewed the batch:', ', '.join(changed))
    print('Their later edits are NOT in the frozen packages. Going ahead publishes the older, reviewed version, '
          'and option 8 will later report the difference. To publish the newer version instead, stop here, '
          'set this batch aside and start a new batch so it can be reviewed.')
    if input('Type PUBLISH REVIEWED to publish the reviewed versions (anything else stops): ').strip() != 'PUBLISH REVIEWED':
        raise BatchStopped('Stopped before publishing. Nothing more changed.')
    for name in changed:
        record(manifest, name, 'later-draft', 'publishing the reviewed version')


# ---- Publishing ----
def strict_check(manifest, name):
    """Check one staged package against the live site as it is now. Return (status, problems)."""
    result, problems = retried(lambda: check(manifest, [name], False, remote=True), 'Live check')[name]
    return result['status'], problems


def publish_one(manifest, name, settings):
    entry = manifest['entries'][name]
    package = Path(entry['package'])
    if not package.is_file() or digest(package) != entry['sha256']:
        raise BatchStopped(f'{name}: the frozen package changed or went missing. Nothing was published for it.')
    unfinished = [d for d in entry['needs'] if manifest['entries'][d]['state'] not in DONE]
    if unfinished:
        raise BatchStopped(f"{name} needs {', '.join(unfinished)}, which did not publish. Nothing was published for it.")
    print('==', entry['title'], f'({name})', flush=True)
    if not entry['remote']:
        record(manifest, name, 'stage', 'started')
        remote, actual = retried(lambda: stage(settings, package), 'Staging')
        if actual != entry['sha256']:
            raise BatchStopped(f'{name}: the staged copy differs from the reviewed package. Nothing was published for it.')
        entry['remote'] = remote
        record(manifest, name, 'stage', 'staged', remote=remote)
    status, problems = strict_check(manifest, name)
    if entry['state'] == 'publishing':
        # An earlier attempt never confirmed; the live check decides what happened.
        record(manifest, name, 'reconcile', status)
    if status.startswith('ALREADY PRESENT') and not problems:
        entry['state'] = 'already_present'
        record(manifest, name, 'live-check', status)
        print('Already live (full match): skipped.', flush=True)
        return
    if problems:
        entry['state'] = 'blocked'
        record(manifest, name, 'live-check', 'blocked', problems=problems)
        raise BatchStopped(f'{name} cannot be published now:\n  ' + '\n  '.join(problems) +
                           '\nNothing was published for it; entries before it stay published.')
    record(manifest, name, 'live-check', status)
    for wait in WAITS + (None,):
        entry['state'] = 'publishing'
        receipt = package.parent / ('receipt-' + uuid.uuid4().hex + '.json')
        record(manifest, name, 'publish', 'started', receipt=str(receipt))
        try:
            result = publish_staged(manifest['username'], entry['remote'], package, receipt)
        except RuntimeError as error:
            record(manifest, name, 'publish', 'unconfirmed', receipt=str(receipt), error=str(error))
            if wait is None:
                raise BatchStopped(f'The publish of {name} is still unconfirmed. Choose 20 again later: '
                                   'the live check will find out whether it went through.') from None
            print(f'Publish unconfirmed; waiting {wait}s, then checking the live site before any retry.', flush=True)
            time.sleep(wait)
            status, problems = strict_check(manifest, name)
            record(manifest, name, 'reconcile', status)
            if status.startswith('ALREADY PRESENT') and not problems:
                entry['state'] = 'already_present'
                record(manifest, name, 'publish', 'confirmed by live check')
                return
            if problems or not status.startswith(batch_check.READY):
                entry['state'] = 'blocked'
                record(manifest, name, 'live-check', 'blocked', problems=problems)
                raise BatchStopped(f'After an unconfirmed publish, {name} is in an unexpected state:\n  ' +
                                   '\n  '.join(problems or [status]) + '\nStopped; nothing was retried.')
            continue  # The live site still has the expected earlier state, so a retry is safe.
        entry['state'] = 'applied' if result['status'] == 'APPLIED' else 'already_present'
        record(manifest, name, 'publish', result['status'], receipt=str(receipt), backup=result.get('backup'))
        return


def publish_all(manifest, state):
    settings = validate(json.loads(SETTINGS.read_text(encoding='utf-8')))
    if settings['username'] != manifest['username']:
        raise ValueError('API account differs from the batch account.')
    manifest['publication'] = 'publishing'
    save_manifest(manifest)
    first = True
    for name in manifest['order']:
        if manifest['entries'][name]['state'] in DONE:
            continue
        if not first:
            time.sleep(manifest['pause_seconds'])
        first = False
        try:
            publish_one(manifest, name, settings)
        except BatchStopped:
            manifest['publication'] = 'stopped'
            save_manifest(manifest)
            print(progress(manifest))
            raise
    manifest['publication'] = 'complete'
    save_manifest(manifest)


def progress(manifest):
    counts = {}
    for name in manifest['order']:
        counts.setdefault(manifest['entries'][name]['state'], []).append(name)
    labels = dict(applied='Published', already_present='Already present', blocked='Blocked',
                  publishing='Uncertain (unconfirmed publish)', pending='Pending')
    return '\n'.join(f"{labels.get(state, state)} ({len(names)}): {', '.join(names)}" for state, names in counts.items())


# ---- After publication ----
def verify(manifest):
    entries = [manifest['entries'][n] for n in manifest['order']]
    print(progress(manifest))
    print('Receipts:')
    for name in manifest['order']:
        receipts = [h['receipt'] for h in manifest['entries'][name]['history']
                    if h['operation'] == 'publish' and h.get('receipt') and h['outcome'] in ('APPLIED', 'ALREADY_PRESENT')]
        print(f'  {name}:', receipts[-1] if receipts else 'none (already present before publishing)')
    text = [e for e in entries if not e['diagrams']]
    picks = [e for e in entries if e['diagrams']] + [text[i] for i in sorted({0, len(text) // 2, len(text) - 1}) if text]
    checklist = Path(manifest['folder']) / 'pages-to-check.txt'
    checklist.write_text('\n'.join(SITE + '/math/concept.html?slug=' + e['slug'] + '  ' + e['title'] for e in entries) + '\n',
                         encoding='utf-8')
    print('Check these live pages (every page with diagrams, and some text pages):')
    for entry in picks:
        print('  ' + SITE + '/math/concept.html?slug=' + entry['slug'])
    print('All', len(entries), 'page links are in', checklist)
    if input('Type VERIFIED once they look right (anything else leaves verification pending): ').strip() != 'VERIFIED':
        print('Verification pending. Choose 20 again after checking the pages.')
        return False
    manifest['verification'] = dict(status='verified', at=now(), pages=[e['slug'] for e in picks])
    save_manifest(manifest)
    return True


def synchronize(manifest, state):
    result = w.bring_home(state)
    if result is None:
        print('Option 8 not run. Choose 20 again to bring the website changes home.')
        return
    manifest['synchronization'] = dict(status='complete' if result['safe'] else 'blocked', at=now(), report=result['report'])
    save_manifest(manifest)
    if result['safe']:
        state.pop('batch', None)
        w.save(state)
        print(f"Batch \"{manifest['name']}\" is finished: published, verified and brought home.")
    else:
        print('Publication complete; synchronization blocked. Your working copy is unchanged. '
              'Review the comparison report, then choose 20 to run option 8 again; nothing will be republished.')


# ---- Menu option 20 ----
def parse_selection(text, count):
    if text.strip().upper() == 'ALL':
        return list(range(count))
    chosen = []
    for part in text.replace(' ', '').split(','):
        match = re.fullmatch(r'(\d+)(?:-(\d+))?', part)
        if not match:
            raise ValueError('Use numbers like 1,3-5 or ALL.')
        low, high = int(match.group(1)), int(match.group(2) or match.group(1))
        if not 1 <= low <= high <= count:
            raise ValueError('Entry numbers must be between 1 and ' + str(count) + '.')
        chosen += [i - 1 for i in range(low, high + 1) if i - 1 not in chosen]
    return chosen


def start(state):
    new, others = candidates(state)
    if not new:
        print('No new local entries compared with your baseline.')
        return None
    print('New local entries:')
    for index, item in enumerate(new, 1):
        print(f"{index}. {item['title']} ({item['canonical']})" + ('' if item['supported'] else ' [cannot publish: ' + item['reason'] + ']'))
    if others:
        print('Other local changes (not part of a batch; they may block option 8 afterwards):',
              ', '.join(c['canonical'] for c in others))
    text = input('Entries for this batch (numbers like 1,3-5, or ALL; blank cancels): ').strip()
    if not text:
        return None
    chosen = parse_selection(text, len(new))
    selected = [new[i]['canonical'] for i in chosen]
    omitted = [c['canonical'] for c in new if c['canonical'] not in selected]
    if omitted:
        print('Left out of this batch:', ', '.join(omitted))
    title = input('Batch name (for example: averages): ').strip()
    if not title:
        return None
    print('Reading the names of the live entries (read-only).', flush=True)
    live = retried(lambda: batch_check.live_catalog(state['username']), 'Reading the live entries')
    manifest, lines = plan(state, selected, title, live)
    print('\n'.join(lines))
    if manifest is None:
        return None
    state['batch'] = manifest['folder']
    w.save(state)
    print('Nothing has changed in your databases or on the website. Review file:', manifest['review_file'])
    return manifest


def approve(manifest, state):
    """Run the projected live check and ask for PUBLISH ALL. Return True when approved."""
    confirm_frozen(manifest, state)
    print('Checking the whole batch against the live site (read-only).', flush=True)
    results = retried(lambda: check(manifest, manifest['order'], True), 'Batch check')
    blocked = {name: found for name, (_, found) in results.items() if found}
    for name in manifest['order']:
        result, found = results[name]
        print(f"  {name}: {result['status']}")
        for problem in found:
            print('    -', problem)
    if blocked:
        raise BatchStopped('The batch cannot be approved. Nothing was published. Fix the entries above, set this '
                           'batch aside with option 20 and start a new one.')
    print(f"Read the review file before approving: {manifest['review_file']}")
    print(f"This publishes {len(manifest['order'])} entries to {SITE}, one at a time, in the order shown, "
          f"pausing {manifest['pause_seconds']} seconds between them.")
    if input('Type PUBLISH ALL to publish exactly these reviewed packages (anything else cancels): ').strip() != 'PUBLISH ALL':
        print('Cancelled. Nothing was published; the batch and its review are kept for later.')
        return False
    manifest['approval'] = dict(fingerprint=fingerprint(manifest), at=now())
    manifest['publication'] = 'approved'
    save_manifest(manifest)
    return True


def resume_choice(manifest):
    print(f"Saved batch \"{manifest['name']}\" ({manifest['batch_id']}): publication {manifest['publication']}, "
          f"verification {(manifest['verification'] or {}).get('status', 'pending')}, "
          f"synchronization {(manifest['synchronization'] or {}).get('status', 'pending')}.")
    print(progress(manifest))
    return input('Type RESUME to continue it, SET ASIDE to keep its history and start a new batch '
                 '(anything else returns to the menu): ').strip()


def reload(manifest):
    """The manifest as saved now; another run may have changed it before this one took the lock."""
    return json.loads((Path(manifest['folder']) / 'manifest.json').read_text(encoding='utf-8'))


def run(state):
    manifest = load_manifest(state)
    if manifest:
        # Take the lock before reading the batch's state or changing anything about it.
        with locked(manifest):
            manifest = reload(manifest)
            choice = resume_choice(manifest)
            if choice == 'RESUME':
                return proceed(manifest, state)
            if choice != 'SET ASIDE':
                return
            manifest['set_aside'] = now()
            save_manifest(manifest)
            state.pop('batch', None)
            w.save(state)
    manifest = start(state)
    if manifest is None:
        return
    with locked(manifest):
        proceed(reload(manifest), state)


def proceed(manifest, state):
    """Carry a batch on from its saved state. The caller holds its lock."""
    if manifest['publication'] == 'invalidated':
        raise BatchStopped('This batch\'s approval no longer holds. Set it aside and start a new batch.')
    if manifest['publication'] in ('planned',):
        if not approve(manifest, state):
            return
    elif manifest['publication'] in ('approved', 'publishing', 'stopped'):
        if manifest['approval'] is None or manifest['approval']['fingerprint'] != fingerprint(manifest):
            raise BatchStopped('The approved package list no longer matches this batch. Set it aside and start a new one.')
        confirm_frozen(manifest, state)
    if manifest['publication'] != 'complete':
        publish_all(manifest, state)
        print(progress(manifest))
    if (manifest['verification'] or {}).get('status') != 'verified' and not verify(manifest):
        return
    synchronize(manifest, state)
