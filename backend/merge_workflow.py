"""Option 21 of the website helper: merge and retire math entries.

1 prepares the one-time schema upgrade that retirement needs. 2 starts a
merge or plain retirement session: it reads both entries from live, checks
that the working copy has the same versions, and freezes them in
dist/merge-sessions/<id>/session.json before the survivor is edited. 3
prepares the session's package from the working copy (the survivor as
edited and published with options 2-5). 4 prepares an undo of a published
merge or retirement. Each package then goes through 3 (stage), 4 (check
live) and 5 (publish). A publish saves its receipt and marks the change
"sync pending": option 21 prepares nothing more until option 8 has brought
it home. See docs/features/math/MERGING_ENTRIES.md.
"""
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import uuid

import math_schema
import merge_sync
from inspect_staged_package import preview
from stage_pythonanywhere_package import read_package
from website_workflow import ROOT, digest

SESSIONS = ROOT / 'dist' / 'merge-sessions'


def prepare_schema_upgrade(state, save):
    """Write the schema package and make it the active job; return its review text."""
    folder = ROOT / 'dist' / 'math-workflow' / uuid.uuid4().hex
    folder.mkdir(parents=True)
    package = folder / 'package.zip'
    math_schema.write_package(package)
    report = preview(read_package(package))
    (folder / 'review.txt').write_text(report, encoding='utf-8')
    state['job'] = dict(kind=math_schema.KIND, canonical='Math schema upgrade', package=str(package),
                        sha256=digest(package), proposed=None, remote=None, checked=False)
    save(state)
    return report


def require_synced(state):
    pending = state.get('merge_pending_sync') or []
    if pending:
        raise ValueError('A published ' + pending[0]['change_set']['action'] + ' is waiting for option 8. '
                         'Verify it on the live site, then run option 8 before preparing another.')


def working(state):
    return closing(sqlite3.connect(Path(state['working']).resolve().as_uri() + '?mode=ro', uri=True))


def frozen_digest(frozen):
    return hashlib.sha256(json.dumps(frozen, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()


def start_session(state, action, absorbed, survivor, reason, view=merge_sync.live_view, sessions=SESSIONS):
    """Freeze the live versions of the entries before anything is edited; return the session folder."""
    require_synced(state)
    if action not in ('merge', 'retire'):
        raise ValueError('Choose merge or retire.')
    if not reason.strip():
        raise ValueError('Give a reason; it is shown on the old page and kept in the log.')
    names = [absorbed] + ([survivor] if action == 'merge' else [])
    if action == 'merge' and absorbed == survivor:
        raise ValueError('An entry cannot be merged into itself.')
    live = view(state['username'], names)
    if live['schema'] != 'current':
        raise ValueError('The live database lacks the schema upgrade. Publish it first (option 21, 1), then option 8.')
    if (live['code_contract'] or 0) < merge_sync.CONTRACT:
        raise ValueError('The live website code does not handle retired entries yet. Publish it with option 15 first.')
    with working(state) as db:
        if math_schema.state(db) != 'current':
            raise ValueError('Your working copy lacks the schema upgrade. Run option 8 first.')
        for name in names:
            item = live['entries'][name]
            if item['entry'] is None:
                raise ValueError(f'{name} is not on the live site.')
            if item['retirement'] is not None:
                raise ValueError(f'{name} is already retired on the live site.')
            if merge_sync.entry_state(db, name) != item['entry']:
                raise ValueError(f'{name} in your working copy differs from live. Publish or undo those local edits '
                                 'first, so the session starts from the published version.')
    if action == 'retire' and live['entries'][absorbed]['retired_into']:
        raise ValueError('These entries are retired into ' + absorbed + ' and would lose their redirect: '
                         + ', '.join(live['entries'][absorbed]['retired_into']) + '. Merge it into a survivor instead.')
    frozen = dict(absorbed=live['entries'][absorbed]['entry'],
                  survivor=live['entries'][survivor]['entry'] if action == 'merge' else None)
    folder = Path(sessions) / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8])
    folder.mkdir(parents=True)
    session = dict(id=folder.name, created_utc=datetime.now(timezone.utc).isoformat(timespec='seconds'),
                   action=action, absorbed=absorbed, survivor=survivor if action == 'merge' else None,
                   reason=reason.strip(), frozen=frozen, frozen_sha256=frozen_digest(frozen))
    with (folder / 'session.json').open('x', encoding='utf-8') as stream:
        json.dump(session, stream, indent=2, ensure_ascii=False)
    return folder


def load_session(folder):
    session = json.loads((Path(folder) / 'session.json').read_text(encoding='utf-8'))
    if frozen_digest(session['frozen']) != session['frozen_sha256']:
        raise ValueError('The session file was changed after it was frozen. Start a new session.')
    return session


def sessions(folder=SESSIONS, published=False):
    """Session folders, oldest first: unpublished ones, or (published=True) those with a receipt and no undo."""
    found = sorted(path.parent for path in Path(folder).glob('*/session.json'))
    if published:
        return [path for path in found if (path / 'receipt.json').exists() and not (path / 'undo-receipt.json').exists()]
    return [path for path in found if not (path / 'receipt.json').exists()]


def make_job(state, save, folder, payload):
    package = Path(folder) / ('package-' + uuid.uuid4().hex[:8] + '.zip')
    merge_sync.write_package(package, payload)
    report = preview(read_package(package), state['working'])
    (package.with_suffix('.review.txt')).write_text(report, encoding='utf-8')
    state['job'] = dict(kind=merge_sync.KIND, canonical=merge_sync.title_of(payload), package=str(package),
                        sha256=digest(package), proposed=None, remote=None, checked=False, session=str(folder))
    save(state)
    return report


def prepare(state, save, folder, keep_title=True, metadata_only=False):
    """Build the session's merge or retirement package from the working copy; return the review text."""
    require_synced(state)
    session = load_session(folder)
    absorbed, survivor = session['absorbed'], session['survivor']
    with working(state) as db:
        if merge_sync.entry_state(db, absorbed) != session['frozen']['absorbed']:
            raise ValueError(f'{absorbed} changed in your working copy since the session started. A merge leaves it '
                             'exactly as it is; put it back or start a new session.')
        after = merge_sync.entry_state(db, survivor) if survivor else None
        links = merge_sync.incoming_links(db, absorbed)
    if session['action'] == 'merge':
        if after == session['frozen']['survivor'] and not metadata_only:
            raise ValueError(f'{survivor} is unchanged. Fold in the content of {absorbed} and publish it with '
                             'options 2-5 first, or prepare a metadata-only merge.')
        payload = dict(kind=merge_sync.KIND, version=merge_sync.VERSION, action='merge', session=session['id'],
                       absorbed=absorbed, survivor=survivor, reason=session['reason'], keep_title=keep_title,
                       metadata_only=metadata_only, absorbed_expected=session['frozen']['absorbed'],
                       survivor_before=session['frozen']['survivor'], survivor_after=after)
    else:
        payload = dict(kind=merge_sync.KIND, version=merge_sync.VERSION, action='retire', session=session['id'],
                       absorbed=absorbed, reason=session['reason'], absorbed_expected=session['frozen']['absorbed'])
    report = make_job(state, save, folder, payload)
    target = f'now lead to {survivor}' if survivor else 'will show as plain text or be hidden'
    report += ('\nEntries linking to ' + absorbed + f' (these links {target}; no text is changed):'
               + '\n  \\PMlinkname: ' + (', '.join(links['explicit']) or 'none')
               + '\n  related concept: ' + (', '.join(links['related']) or 'none'))
    return report


def prepare_undo(state, save, folder):
    """Build the package that undoes the merge or retirement published from this session."""
    require_synced(state)
    receipt = json.loads((Path(folder) / 'receipt.json').read_text(encoding='utf-8'))
    change_set = receipt['change_set']
    payload = dict(kind=merge_sync.KIND, version=merge_sync.VERSION, action='undo',
                   undoes=change_set['package_sha256'], change_set=change_set)
    report = make_job(state, save, folder, payload)
    if change_set['survivor']:
        report += ('\nThe text of ' + change_set['survivor'] + ' stays as it is. Its version from before the merge is in '
                   + str(Path(folder) / 'session.json') + ' (frozen.survivor); restoring it is a normal text edit.')
    return report


def check_job(state, job):
    """Stop if the working copy no longer has what the active merge package was prepared from."""
    payload = merge_sync.unpack(read_package(Path(job['package'])))
    if payload['action'] == 'undo':
        return
    with working(state) as db:
        if merge_sync.entry_state(db, payload['absorbed']) != payload['absorbed_expected'] or (
                payload['action'] == 'merge' and
                merge_sync.entry_state(db, payload['survivor']) != payload['survivor_after']):
            raise ValueError('Local entry changed since preparation. Prepare it again before continuing.')


def record_receipt(state, job, result):
    """Keep a published change set: in its session folder, and as pending until option 8."""
    payload = merge_sync.unpack(read_package(Path(job['package'])))
    name = 'undo-receipt.json' if payload['action'] == 'undo' else 'receipt.json'
    path = Path(job['session']) / name
    if not path.exists():
        path.write_text(json.dumps(dict(result, package=job['package'], package_sha256=job['sha256']), indent=2,
                                   ensure_ascii=False), encoding='utf-8')
    pending = state.setdefault('merge_pending_sync', [])
    if all(item['package_sha256'] != job['sha256'] for item in pending):
        pending.append(dict(package_sha256=job['sha256'], change_set=result['change_set'], receipt=str(path)))
    return path


def choose(folders, label):
    for index, folder in enumerate(folders, 1):
        session = load_session(folder)
        print(f"{index}. {session['action']} {session['absorbed']}"
              + (f" into {session['survivor']}" if session['survivor'] else '') + f" ({folder.name})")
    if not folders:
        print('No ' + label + '.')
        return None
    number = int(input('Number (0 cancels): ') or 0)
    if number == 0:
        return None
    if not 1 <= number <= len(folders):
        raise ValueError('Invalid number.')
    return folders[number - 1]


def run(state, save):
    for item in state.get('merge_pending_sync') or []:
        print('Waiting for option 8:', item['change_set']['action'], '(receipt', item['receipt'] + ')')
    print('1. Prepare the one-time schema upgrade for retiring entries\n'
          '2. Start a merge or retirement session (reads both entries from live)\n'
          '3. Prepare the package for a session\n'
          '4. Prepare an undo of a published merge or retirement\n0. Back')
    choice = input('Choose: ').strip()
    if choice == '1':
        print(prepare_schema_upgrade(state, save))
        print('Nothing changed yet. Use 3 (stage), 4 (check live), 5 (publish).')
    elif choice == '2':
        action = 'retire' if input('Merge into a survivor, or retire with none? (merge/retire): ').strip() == 'retire' else 'merge'
        absorbed = input('Canonical name of the entry to retire: ').strip()
        survivor = input('Canonical name of the survivor: ').strip() if action == 'merge' else None
        reason = input('Reason (shown on the old page and kept in the log): ').strip()
        folder = start_session(state, action, absorbed, survivor, reason)
        print('Session frozen:', folder)
        if action == 'merge':
            print(f'Next: edit {survivor} in your working copy, publish it with options 2-5, verify the page, '
                  'then choose 21 and 3.')
        else:
            print('Next: choose 21 and 3.')
    elif choice == '3':
        folder = choose(sessions(), 'open sessions')
        if folder is not None:
            session = load_session(folder)
            keep_title = metadata_only = False
            if session['action'] == 'merge':
                keep_title = input(f"Keep the title of {session['absorbed']} as a synonym of the survivor? (Y/n): "
                                   ).strip().lower() != 'n'
                metadata_only = input('Is this a metadata-only merge, with the survivor text unchanged? (y/N): '
                                      ).strip().lower() == 'y'
            print(prepare(state, save, folder, keep_title, metadata_only))
            print('Nothing changed yet. Use 3 (stage), 4 (check live), 5 (publish).')
    elif choice == '4':
        folder = choose(sessions(published=True), 'published merges or retirements')
        if folder is not None:
            print(prepare_undo(state, save, folder))
            print('Nothing changed yet. Use 3 (stage), 4 (check live), 5 (publish).')
