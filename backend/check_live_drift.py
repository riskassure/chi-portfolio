"""Read-only check: which files on the live PythonAnywhere site differ from main on GitHub.

Run on the laptop from the repository folder:

    python backend/check_live_drift.py

It fetches origin/main, reads every file under /home/<user>/chi-portfolio over
SSH (nothing on the server is changed), and writes a report under
dist/live-drift/<time>/ with diffs and copies of the live versions of changed
files. See docs/administration/deployment/LIVE_DRIFT_CHECK.md.
"""
import argparse
from datetime import datetime, timezone
import difflib
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PREFIX = 'LIVE_DRIFT='

# Files the website itself runs or serves. Everything else on the server
# (docs, tests, laptop helper scripts) was copied there by the first
# deployment and is never used by the site.
SITE_CODE = re.compile(r'(?:backend/src/|frontend/).+|backend/(?:pythonanywhere_wsgi\.py|serve\.py|requirements\.txt)')
# Files the live site, or a helper option, rewrites as content rather than code.
CONTENT_FILES = re.compile(r'frontend/(?:images/photography/.+|geography/places-data\.js|photography/gallery-settings\.js)')
TEXT_SUFFIXES = ('.py', '.html', '.css', '.js', '.txt', '.md', '.ps1', '.cfg', '.ini', '.toml')

# Runs on the server with python3.13 -I -B. Reads only; prints one JSON line.
READER = r'''
import hashlib, json, os, sys
request = json.load(sys.stdin)
root = os.path.realpath(request['root'])
main = request['main']
prune_names = set(request['prune_names'])
prune_paths = set(request['prune_paths'])
suffixes = tuple(request['text_suffixes'])
per_file, budget = request['file_limit'], request['total_limit']
files, pruned = {}, []
for folder, dirs, names in os.walk(root):
    rel_folder = os.path.relpath(folder, root).replace(os.sep, '/')
    rel_folder = '' if rel_folder == '.' else rel_folder + '/'
    for name in sorted(dirs):
        path = rel_folder + name
        if name in prune_names or path in prune_paths or os.path.islink(os.path.join(folder, name)):
            dirs.remove(name)
            pruned.append(path + '/')
    for name in names:
        path = rel_folder + name
        full = os.path.join(folder, name)
        if os.path.islink(full) or not os.path.isfile(full):
            files[path] = dict(kind='other')
            continue
        size = os.path.getsize(full)
        entry = dict(kind='file', size=size)
        files[path] = entry
        if name.endswith(('.db', '.db-wal', '.db-shm', '.db-journal', '.sqlite', '.gz', '.zip')) or size > 64 * 1024 * 1024:
            continue
        with open(full, 'rb') as stream:
            data = stream.read()
        entry['raw'] = hashlib.sha256(data).hexdigest()
        entry['lf'] = hashlib.sha256(data.replace(b'\r\n', b'\n')).hexdigest()
        known = main.get(path)
        changed = known is not None and known[1] != entry['lf']
        unknown = known is None and name.endswith(suffixes)
        if (changed or unknown) and size <= per_file and size <= budget and b'\x00' not in data:
            try:
                entry['text'] = data.decode('utf-8')
                budget -= size
            except UnicodeError:
                pass
print('LIVE_DRIFT=' + json.dumps(dict(root=root, files=files, pruned=sorted(pruned))))
'''


def git(root, *args, data=None):
    result = subprocess.run(['git', '-C', str(root), *args], input=data, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, check=False)
    if result.returncode not in (0, 1):
        raise RuntimeError('git ' + ' '.join(args) + ' failed: ' + result.stderr.decode('utf-8', 'replace').strip())
    return result


def main_files(root, ref):
    """{path: bytes} for every regular file in ref, read from git, not from the folder."""
    listing = git(root, 'ls-tree', '-r', '-z', ref).stdout.decode('utf-8')
    blobs = []
    for line in filter(None, listing.split('\0')):
        meta, path = line.split('\t', 1)
        mode, kind, sha = meta.split()
        if kind == 'blob' and mode != '120000':
            blobs.append((path, sha))
    batch = git(root, 'cat-file', '--batch', data=''.join(sha + '\n' for _, sha in blobs).encode()).stdout
    files, offset = {}, 0
    for path, sha in blobs:
        end = batch.index(b'\n', offset)
        size = int(batch[offset:end].split()[2])
        files[path] = batch[end+1:end+1+size]
        offset = end + 2 + size
    return files


def hashes(data):
    return [hashlib.sha256(data).hexdigest(), hashlib.sha256(data.replace(b'\r\n', b'\n')).hexdigest()]


def read_live(username, request):
    """Run READER on PythonAnywhere over SSH (same login the helper uses)."""
    result = subprocess.run(['ssh', username + '@ssh.pythonanywhere.com', 'python3.13 -I -B -c ' + shlex.quote(READER)],
                            input=json.dumps(request), text=True, encoding='utf-8', stdout=subprocess.PIPE, check=True)
    return parse(result.stdout)


def parse(output):
    lines = [line[len(PREFIX):] for line in output.splitlines() if line.startswith(PREFIX)]
    if len(lines) != 1:
        raise ValueError('The server did not return one file listing.')
    return json.loads(lines[0])


def ignored(root, paths):
    """The paths main's .gitignore rules cover (data and generated files git never tracks)."""
    if not paths:
        return set()
    out = git(root, 'check-ignore', '--no-index', '-z', '--stdin', data='\0'.join(paths).encode('utf-8') + b'\0').stdout
    return set(filter(None, out.decode('utf-8').split('\0')))


def area(path):
    if CONTENT_FILES.fullmatch(path):
        return 'content'
    return 'site code' if SITE_CODE.fullmatch(path) else 'other'


def classify(main, live, ignored_paths):
    """Sort every path into one bucket. main: {path: bytes}; live: the READER file map."""
    buckets = {name: [] for name in ('same', 'line endings', 'differs', 'missing on live',
                                     'only on live', 'only on live (ignored)', 'not compared')}
    for path in sorted(main.keys() | live.keys()):
        entry = live.get(path)
        if path not in live:
            bucket = 'missing on live'
        elif path not in main:
            bucket = 'only on live (ignored)' if path in ignored_paths else 'only on live'
        elif 'raw' not in entry:
            bucket = 'not compared'
        else:
            raw, lf = hashes(main[path])
            bucket = 'same' if entry['raw'] == raw else 'line endings' if entry['lf'] == lf else 'differs'
        buckets[bucket].append(path)
    return buckets


def laptop_state(root, ref):
    branch = git(root, 'rev-parse', '--abbrev-ref', 'HEAD').stdout.decode().strip()
    counts = git(root, 'rev-list', '--left-right', '--count', 'HEAD...' + ref).stdout.decode().split()
    status = git(root, 'status', '--porcelain=v1', '-uall').stdout.decode('utf-8', 'replace').splitlines()
    return dict(branch=branch, ahead=int(counts[0]) if counts else 0, behind=int(counts[1]) if counts else 0,
                status=[line for line in status if not line[3:].startswith('dist/')])


def needs_decision(buckets):
    """Live site code that differs from main, and live files git neither tracks nor ignores."""
    return ([p for p in buckets['differs'] if area(p) == 'site code']
            + [p for p in buckets['only on live'] if area(p) != 'content'])


def save_live_copies(live, out):
    saved = []
    for path, entry in live.items():
        if 'text' in entry:
            target = out / 'live' / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(entry['text'].encode('utf-8'))
            saved.append(path)
    return saved


def diff_text(path, main, entry):
    if 'text' not in entry:
        return '(live file not downloaded: binary, too large or not UTF-8)'
    before = main.decode('utf-8', 'replace').replace('\r\n', '\n').splitlines()
    after = entry['text'].replace('\r\n', '\n').splitlines()
    return '\n'.join(difflib.unified_diff(before, after, 'main/' + path, 'live/' + path, lineterm='', n=2))


def by_folder(paths):
    counts = {}
    for path in paths:
        folder = path.rsplit('/', 1)[0] + '/' if '/' in path else './'
        counts[folder] = counts.get(folder, 0) + 1
    return sorted(counts.items())


def report(commit, ref, username, listing, main, buckets, laptop, saved):
    live = listing['files']
    lines = [f'# Live site vs {ref}', '',
             f'- Compared at: {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC',
             f'- main commit: `{commit}`',
             f'- Live folder: `{listing["root"]}` on {username}@ssh.pythonanywhere.com', '']

    def section(title, explanation, paths, show_area=True, diffs=False):
        lines.extend([f'## {title} ({len(paths)})', '', explanation, ''])
        for path in paths:
            lines.append(f'- `{path}`' + (f' ({area(path)})' if show_area else ''))
        if diffs:
            for path in paths:
                lines.extend(['', f'### `{path}`', '', '```diff', diff_text(path, main[path], live[path]), '```'])
        lines.append('')

    code = lambda paths, wanted: [p for p in paths if (area(p) == 'site code') == wanted]
    lines.extend(['## Summary', ''])
    for name, paths in buckets.items():
        lines.append(f'- {name}: {len(paths)}' + (f' ({len(code(paths, True))} site code)' if name != 'same' else ''))
    lines.append('')
    section('Needs a decision: site code that differs from main',
            'The live site runs these files, and their text is not what main has. Someone edited them on the '
            'server, or published them from the laptop before (or without) merging. The next option 14 or 15 '
            'that touches one of them will replace the live text. Diffs are below; the live copies are in the '
            'live/ folder next to this report.', code(buckets['differs'], True), diffs=True)
    section('Needs a decision: files only on live that git does not ignore',
            'These exist on the server but not in main, and .gitignore does not say they are data. '
            'Either they belong in git, or they are leftovers that can be deleted from the server.',
            [p for p in buckets['only on live'] if area(p) != 'content'])
    section('Content files that differ or are only on live',
            'Files the site or a helper option writes as data (photos, travel places, gallery count). '
            'A difference here usually means a publish that has not been committed to git yet, not a code problem.',
            [p for p in buckets['differs'] + buckets['only on live'] if area(p) == 'content'], show_area=False)
    section('Other files that differ',
            'Docs, tests and laptop scripts copied to the server at the first deployment. The site never '
            'uses them, so these differences are harmless.', [p for p in buckets['differs'] if area(p) == 'other'],
            show_area=False)
    section('Same apart from line endings',
            'Only Windows (CRLF) versus Unix (LF) line endings differ. Python, browsers and the site treat '
            'both the same way, so these are harmless.', buckets['line endings'])
    section('Site code in main that is missing on live',
            'main has these website files but the server does not: work merged but never published. '
            'Check whether each one should be published.', code(buckets['missing on live'], True), show_area=False)
    lines.extend([f'## Other files in main that are not on live ({len(code(buckets["missing on live"], False))})', '',
                  'Laptop scripts, tests and docs. The site does not need them on the server.', ''])
    lines.extend(f'- `{folder}`: {count}' for folder, count in by_folder(code(buckets['missing on live'], False)))
    lines.extend(['', f'## Data and generated files only on live ({len(buckets["only on live (ignored)"])})', '',
                  'Covered by .gitignore (databases, diagrams, music data and so on), so expected. Counts by folder:', ''])
    lines.extend(f'- `{folder}`: {count}' for folder, count in by_folder(buckets['only on live (ignored)']))
    lines.extend(['', 'Folders not read: ' + ', '.join(f'`{p}`' for p in listing['pruned']) if listing['pruned'] else '', ''])
    if buckets['not compared']:
        lines.extend(['Files listed but not hashed (databases, archives, very large files): '
                      + ', '.join(f'`{p}`' for p in buckets['not compared']), ''])
    lines.extend(['## The laptop folder', '',
                  f'The helper publishes from the laptop folder, not from GitHub. It is on branch `{laptop["branch"]}`, '
                  f'{laptop["ahead"]} commit(s) ahead of and {laptop["behind"]} behind {ref}.', ''])
    if laptop['status']:
        lines.extend(['Uncommitted or untracked files (git status):', '', '```'] + laptop['status'] + ['```', ''])
    else:
        lines.extend(['No uncommitted or untracked files.', ''])
    if saved:
        lines.extend([f'Live copies saved for review: {len(saved)} file(s) under `live/`.', ''])
    return '\n'.join(lines)


def check(root, username, ref, output, fetch=True, reader=read_live):
    if not re.fullmatch(r'[A-Za-z0-9_]+', username):
        raise ValueError('Invalid account username.')
    if fetch:
        print('Fetching main from GitHub (changes nothing in your folder)...', flush=True)
        result = git(root, 'fetch', 'origin', 'main')
        if result.returncode:
            raise RuntimeError('git fetch failed: ' + result.stderr.decode('utf-8', 'replace').strip())
    commit = git(root, 'rev-parse', ref).stdout.decode().strip()
    if not commit:
        raise ValueError('Unknown git ref: ' + ref)
    main = main_files(root, ref)
    print(f'Reading {len(main)} file checksums from {ref} ({commit[:7]}). Now reading the live site over SSH; '
          'SSH may ask for your key passphrase. Nothing on the server is changed.', flush=True)
    request = dict(root=f'/home/{username}/chi-portfolio', main={p: hashes(d) for p, d in main.items()},
                   prune_names=['.git', '__pycache__', '.venv', '.pytest_cache', 'node_modules'],
                   prune_paths=['dist', 'backend/backups'], text_suffixes=list(TEXT_SUFFIXES),
                   file_limit=2 * 1024 * 1024, total_limit=40 * 1024 * 1024)
    listing = reader(username, request)
    live = listing['files']
    buckets = classify(main, live, ignored(root, sorted(live.keys() - main.keys())))
    out = Path(output) / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out.mkdir(parents=True)
    saved = save_live_copies(live, out)
    text = report(commit, ref, username, listing, main, buckets, laptop_state(root, ref), saved)
    (out / 'report.md').write_text(text, encoding='utf-8')
    (out / 'summary.json').write_text(json.dumps(dict(commit=commit, ref=ref, buckets=buckets), indent=2), encoding='utf-8')
    return out, buckets


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--username', default='cwoo', help='PythonAnywhere account (default cwoo)')
    parser.add_argument('--ref', default='origin/main', help='git ref to compare with (default origin/main)')
    parser.add_argument('--no-fetch', action='store_true', help='compare with the origin/main you already have')
    parser.add_argument('--output', type=Path, default=ROOT / 'dist' / 'live-drift')
    args = parser.parse_args(argv)
    out, buckets = check(ROOT, args.username, args.ref, args.output, fetch=not args.no_fetch)
    decide = needs_decision(buckets)
    print(f'Same: {len(buckets["same"])}, line endings only: {len(buckets["line endings"])}, '
          f'differ: {len(buckets["differs"])}, only on live (not ignored): {len(buckets["only on live"])}, '
          f'missing on live: {len(buckets["missing on live"])}.')
    if decide:
        print(f'{len(decide)} file(s) need a decision:')
        for path in decide:
            print('  ' + path)
    else:
        print('No live site code differs from main.')
    print('Full report:', out / 'report.md')
    return 0


if __name__ == '__main__':
    sys.exit(main())
