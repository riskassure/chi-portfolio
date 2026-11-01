"""Keep PythonAnywhere's old access logs before PythonAnywhere deletes them.

PythonAnywhere renames the access log to .1 when it rotates it, compresses older copies
as .2.gz, .3.gz and so on, and after a few weeks deletes the oldest. save_rotated() copies
every rotated copy (never the current log, which is still growing) into an archive folder
as one compressed file per rotated log, named after the first and last request time in it:

    www.cwoo.me.access-20261025T101700Z-20261026T101659Z-<16 hex>.log.gz

The 16 hex characters are the start of the SHA-256 of the uncompressed text. Rotation
renames files (.1 becomes .2.gz) without changing their contents, so the fingerprint, not
the name, says whether a file is already saved. Saved files are never deleted, except a
shorter copy of the same log (same first request) that the longer one fully contains.

Standard library only, so the nightly backup can run it with any Python 3.
"""
from datetime import datetime, timezone
import gzip
import hashlib
import os
from pathlib import Path
import re
import uuid

CHUNK = 1024 * 1024
STAMP = '%Y%m%dT%H%M%SZ'
TIME = re.compile(r'\[(\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2} [+-]\d{4})\]')
ARCHIVED = re.compile(r'(?P<base>.+)-(?P<first>\d{8}T\d{6}Z)-(?P<last>\d{8}T\d{6}Z)-(?P<digest>[0-9a-f]{16})\.log\.gz')


def rotated_logs(log):
    """Rotated copies of log (log.1, log.2.gz, ...), oldest first. The current log is never included."""
    log = Path(log)
    found = []
    for candidate in log.parent.glob(log.name + '.*'):
        suffix = candidate.name[len(log.name) + 1:].removesuffix('.gz')
        if suffix.isdigit() and candidate.is_file() and not candidate.is_symlink():
            found.append((int(suffix), candidate))
    return [path for _, path in sorted(found, reverse=True)]


def read_bytes(path):
    path = Path(path)
    opener = gzip.open if path.name.endswith('.gz') else open
    with opener(path, 'rb') as stream:
        return stream.read()


def request_time(line):
    match = TIME.search(line)
    if not match:
        return None
    try:
        return datetime.strptime(match[1], '%d/%b/%Y:%H:%M:%S %z').astimezone(timezone.utc)
    except ValueError:
        return None


def time_range(data):
    """(first, last) request time in the log text, or (None, None) when it has no requests."""
    times = [when for when in map(request_time, data.decode('utf-8', 'replace').splitlines()) if when]
    return (min(times), max(times)) if times else (None, None)


def archived(folder):
    """Saved logs in folder as dicts with path, first, last (UTC datetimes) and digest; oldest first."""
    folder = Path(folder)
    if not folder.is_dir():
        return []
    found = []
    for path in folder.iterdir():
        match = ARCHIVED.fullmatch(path.name)
        if match and path.is_file() and not path.is_symlink():
            when = lambda text: datetime.strptime(text, STAMP).replace(tzinfo=timezone.utc)
            found.append(dict(path=path, first=when(match['first']), last=when(match['last']),
                              digest=match['digest']))
    return sorted(found, key=lambda item: (item['first'], item['last']))


def save_rotated(log, folder):
    """Copy rotated logs not yet saved into folder. Returns a report dict."""
    log, folder = Path(log), Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    report = dict(saved=[], already_saved=0, replaced=[], empty=0)
    for source in rotated_logs(log):
        data = read_bytes(source)
        first, last = time_range(data)
        if first is None:
            report['empty'] += 1
            continue
        digest = hashlib.sha256(data).hexdigest()[:16]
        existing = archived(folder)
        if any(item['digest'] == digest for item in existing):
            report['already_saved'] += 1
            continue
        same_start = [item for item in existing if item['first'] == first]
        # A copy taken while the server was still finishing the file holds less; keep the
        # longer one, but delete the shorter only when the longer contains all of it.
        if any(len(read_bytes(item['path'])) >= len(data) for item in same_start):
            report['already_saved'] += 1
            continue
        name = f'{log.name.removesuffix(".log")}-{first.strftime(STAMP)}-{last.strftime(STAMP)}-{digest}.log.gz'
        final = folder / name
        partial = folder / f'.{name}-{uuid.uuid4().hex[:8]}.partial'
        try:
            with open(partial, 'xb') as out, gzip.GzipFile(fileobj=out, mode='wb', mtime=0) as packed:
                packed.write(data)
            if read_bytes_gz(partial) != data:
                raise RuntimeError(f'Saved copy of {source.name} does not match it. Nothing was kept.')
            os.replace(partial, final)
        finally:
            if partial.exists():
                partial.unlink()
        report['saved'].append(name)
        for item in same_start:
            if data.startswith(read_bytes(item['path'])):
                item['path'].unlink()
                report['replaced'].append(item['path'].name)
    return report


def read_bytes_gz(path):
    with gzip.open(path, 'rb') as stream:
        return stream.read()


def lines_between(log, folder, start, end):
    """Text lines of every saved log overlapping [start, end), then the current log.

    Call save_rotated first so the rotated copies are in the archive; the current log is
    read as it is. Saved logs that another saved log fully contains are skipped.
    """
    log = Path(log)
    items = [item for item in archived(folder) if item['last'] >= start and item['first'] < end]
    for item in items:
        contained = any(other is not item and other['first'] <= item['first'] and other['last'] >= item['last']
                        and (other['first'], other['last']) != (item['first'], item['last'])
                        for other in items)
        if contained:
            continue
        yield from read_bytes(item['path']).decode('utf-8', 'replace').splitlines(keepends=True)
    if log.is_file():
        with open(log, 'rb') as stream:
            yield from stream.read().decode('utf-8', 'replace').splitlines(keepends=True)
