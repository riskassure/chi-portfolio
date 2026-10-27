"""Nightly verified backups of the live SQLite database, with rotation and restore.

Commands (all take explicit paths; nothing has a default location):

  backup       Snapshot the database with SQLite's online backup API, check it,
               compress it, verify the compressed copy, then rotate old nightly
               backups (only after the new one is verified).
  check        Re-verify every nightly backup in the folder.
  extract      Decompress one backup into a NEW .db file (never overwrites).
  restore-live Copy one backup INTO the live database. Preview unless --apply;
               a verified before-restore copy of the current database is made first.

Only files named portfolio-YYYYMMDDTHHMMSSZ.db.gz (and their .json notes) in the
nightly folder are ever deleted. Other backups are never touched.

Standard library only, so any Python 3 on the server can run it.
"""
import argparse
from contextlib import closing
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import sys
import uuid

NAME = re.compile(r'portfolio-(\d{8}T\d{6}Z)\.db\.gz')
CHUNK = 1024 * 1024


def _read_only(path):
    return sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True)


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(CHUNK), b''):
            digest.update(block)
    return digest.hexdigest()


def _gunzip_sha256(path):
    digest, size = hashlib.sha256(), 0
    with gzip.open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(CHUNK), b''):
            digest.update(block)
            size += len(block)
    return digest.hexdigest(), size


def check_database(path):
    """Integrity-check a database file and return a few counts; raise if it is not a portfolio database."""
    with closing(_read_only(path)) as db:
        if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise RuntimeError(f'Database failed its integrity check: {path}')
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if 'math_concepts' not in tables:
            raise RuntimeError(f'Not a portfolio database (no math_concepts table): {path}')
        return dict(tables=len(tables), math_concepts=db.execute('SELECT COUNT(*) FROM math_concepts').fetchone()[0])


def snapshot(source, destination):
    """Consistent copy of a database that may be in use, made with the online backup API."""
    # Exclusive creation never overwrites an existing file, even via a symlink.
    with open(destination, 'xb'):
        pass
    with closing(_read_only(source)) as src, closing(sqlite3.connect(destination)) as dst:
        src.backup(dst)


def stamp_of(path):
    match = NAME.fullmatch(Path(path).name)
    return datetime.strptime(match[1], '%Y%m%dT%H%M%SZ').replace(tzinfo=timezone.utc) if match else None


def nightly_backups(folder):
    """Nightly backups in folder, newest first, as (time, path)."""
    found = [(stamp_of(path), path) for path in Path(folder).iterdir() if path.is_file() and not path.is_symlink()]
    return sorted([item for item in found if item[0]], reverse=True)


def to_keep(stamps, daily=7, weekly=4, monthly=6):
    """Newest backup of each of the last `daily` days, `weekly` ISO weeks and `monthly` months."""
    keep, seen = set(), {'d': set(), 'w': set(), 'm': set()}
    for stamp in sorted(stamps, reverse=True):
        for kind, key, limit in (('d', stamp.date(), daily), ('w', stamp.isocalendar()[:2], weekly),
                                 ('m', (stamp.year, stamp.month), monthly)):
            if key not in seen[kind] and len(seen[kind]) < limit:
                seen[kind].add(key)
                keep.add(stamp)
    if stamps:
        keep.add(max(stamps))
    return keep


def rotate(folder, daily=7, weekly=4, monthly=6):
    """Delete nightly backups outside the retention rule; return the deleted names."""
    backups = nightly_backups(folder)
    keep = to_keep([stamp for stamp, _ in backups], daily, weekly, monthly)
    deleted = []
    for stamp, path in backups:
        if stamp not in keep:
            path.unlink()
            note = path.with_name(path.name[:-len('.db.gz')] + '.json')
            if note.is_file() and not note.is_symlink():
                note.unlink()
            deleted.append(path.name)
    return deleted


def backup(database, folder, now=None, daily=7, weekly=4, monthly=6, warn_mb=200):
    """Make one verified nightly backup, then rotate. Returns a report dict."""
    database, folder = Path(database), Path(folder)
    if not database.is_file():
        raise FileNotFoundError(f'Live database not found: {database}')
    folder.mkdir(parents=True, exist_ok=True)
    now = now or datetime.now(timezone.utc)
    for stale in folder.glob('.portfolio-*.partial'):
        # Left behind only if an earlier run was killed mid-way.
        if stale.is_file() and not stale.is_symlink() and now.timestamp() - stale.stat().st_mtime > 86400:
            stale.unlink()
    name = 'portfolio-' + now.strftime('%Y%m%dT%H%M%SZ')
    final, note = folder / (name + '.db.gz'), folder / (name + '.json')
    if final.exists() or note.exists():
        raise FileExistsError(f'A backup with this time already exists: {final}')
    token = uuid.uuid4().hex[:8]
    raw, packed = folder / f'.{name}-{token}.db.partial', folder / f'.{name}-{token}.gz.partial'
    try:
        snapshot(database, raw)
        counts = check_database(raw)
        expected, size = _sha256(raw), raw.stat().st_size
        with open(raw, 'rb') as src, open(packed, 'xb') as out, gzip.GzipFile(fileobj=out, mode='wb', mtime=0) as gz:
            shutil.copyfileobj(src, gz, CHUNK)
        if _gunzip_sha256(packed) != (expected, size):
            raise RuntimeError('Compressed backup does not match the snapshot. Nothing was kept.')
        with open(note, 'x', encoding='utf-8') as stream:
            json.dump(dict(created_utc=now.isoformat(), source=str(database.resolve()), backup=final.name,
                           sha256=expected, size=size, gz_sha256=_sha256(packed),
                           gz_size=packed.stat().st_size, integrity='ok', **counts), stream, indent=2)
        os.replace(packed, final)
    except BaseException:
        if not final.exists() and note.exists():
            note.unlink()
        raise
    finally:
        for path in (raw, packed):
            if path.exists():
                path.unlink()
    deleted = rotate(folder, daily, weekly, monthly)
    total = sum(path.stat().st_size for path in folder.iterdir() if path.is_file())
    report = dict(status='ok', backup=str(final), size=final.stat().st_size, sha256=expected,
                  math_concepts=counts['math_concepts'], deleted=deleted,
                  kept=len(nightly_backups(folder)), folder_mb=round(total / 1048576, 1))
    if total > warn_mb * 1048576:
        report['warning'] = f'Nightly folder uses {report["folder_mb"]} MB, above {warn_mb} MB. Check the disk quota.'
    return report


def verify_backup(path):
    """Check one .db.gz against its note (if any) and its contents' integrity. Returns its counts."""
    path = Path(path)
    if not path.name.endswith('.db.gz'):
        raise ValueError(f'Not a compressed backup (.db.gz): {path}')
    digest, size = _gunzip_sha256(path)
    note = path.with_name(path.name[:-len('.db.gz')] + '.json')
    if note.is_file():
        recorded = json.loads(note.read_text(encoding='utf-8'))
        if (recorded['sha256'], recorded['size']) != (digest, size):
            raise RuntimeError(f'Backup does not match its note (damaged or replaced): {path}')
    return digest


def extract(path, output):
    """Decompress a backup into a new file, verify it, and return its counts."""
    path, output = Path(path), Path(output)
    expected = verify_backup(path)
    partial = output.with_name(f'.{output.name}-{uuid.uuid4().hex[:8]}.partial')
    try:
        with gzip.open(path, 'rb') as src, open(partial, 'xb') as out:
            shutil.copyfileobj(src, out, CHUNK)
        if _sha256(partial) != expected:
            raise RuntimeError('Extracted copy does not match the backup.')
        counts = check_database(partial)
        # Claim the output name first so an existing file is never replaced.
        with open(output, 'xb'):
            pass
        os.replace(partial, output)
        return counts
    finally:
        if partial.exists():
            partial.unlink()


def check_all(folder):
    """Verify every nightly backup in folder; returns (name, ok, detail) rows."""
    rows, temp = [], Path(folder)
    for _, path in nightly_backups(folder):
        target = temp / f'.check-{uuid.uuid4().hex[:8]}.db'
        try:
            counts = extract(path, target)
            rows.append((path.name, True, f'{counts["math_concepts"]} math entries'))
        except Exception as error:
            rows.append((path.name, False, str(error)))
        finally:
            if target.exists():
                target.unlink()
    return rows


def restore_live(path, database, folder, apply=False, now=None):
    """Replace the live database's contents with a backup, after a before-restore copy."""
    path, database, folder = Path(path), Path(database), Path(folder)
    if not database.is_file():
        raise FileNotFoundError(f'Live database not found: {database}')
    now = now or datetime.now(timezone.utc)
    staged = folder / f'.restore-{uuid.uuid4().hex[:8]}.db'
    try:
        counts = extract(path, staged)
        current = check_database(database)
        report = dict(backup=path.name, backup_math_concepts=counts['math_concepts'],
                      live_math_concepts=current['math_concepts'])
        if not apply:
            report['status'] = 'preview'
            return report
        safety = folder / f'before-restore-{now.strftime("%Y%m%dT%H%M%SZ")}-{uuid.uuid4().hex[:8]}.db'
        snapshot(database, safety)
        check_database(safety)
        # The backup API writes pages into the open live file under SQLite's own
        # locking, so the site sees either the old or the new database, never a mix.
        with closing(_read_only(staged)) as src, closing(sqlite3.connect(database, timeout=30)) as dst:
            src.backup(dst)
        after = check_database(database)
        if after['math_concepts'] != counts['math_concepts']:
            raise RuntimeError(f'Restore check failed. The previous database is at {safety}')
        report.update(status='restored', before_restore_copy=str(safety))
        return report
    finally:
        if staged.exists():
            staged.unlink()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest='command', required=True)
    run = commands.add_parser('backup', help='make tonight\'s backup and rotate old ones')
    run.add_argument('--database', required=True, type=Path)
    run.add_argument('--backups', required=True, type=Path, help='nightly folder, e.g. /home/cwoo/backups/nightly')
    run.add_argument('--keep-daily', type=int, default=7)
    run.add_argument('--keep-weekly', type=int, default=4)
    run.add_argument('--keep-monthly', type=int, default=6)
    run.add_argument('--warn-mb', type=int, default=200)
    check = commands.add_parser('check', help='verify every nightly backup')
    check.add_argument('--backups', required=True, type=Path)
    out = commands.add_parser('extract', help='decompress one backup into a new .db file')
    out.add_argument('backup', type=Path)
    out.add_argument('--output', required=True, type=Path)
    restore = commands.add_parser('restore-live', help='put one backup back into the live database')
    restore.add_argument('backup', type=Path)
    restore.add_argument('--database', required=True, type=Path)
    restore.add_argument('--backups', required=True, type=Path, help='where the before-restore copy goes')
    restore.add_argument('--apply', action='store_true', help='actually restore (otherwise preview only)')
    args = parser.parse_args(argv)
    os.umask(0o077)  # Backups hold private site data: owner-only files.
    if args.command == 'backup':
        if min(args.keep_daily, args.keep_weekly, args.keep_monthly) < 1:
            parser.error('keep counts must be at least 1')
        report = backup(args.database, args.backups, daily=args.keep_daily, weekly=args.keep_weekly,
                        monthly=args.keep_monthly, warn_mb=args.warn_mb)
        print(json.dumps(report, indent=2))
    elif args.command == 'check':
        rows = check_all(args.backups)
        for name, ok, detail in rows:
            print(('OK    ' if ok else 'FAILED'), name, '-', detail)
        print(f'{sum(ok for _, ok, _ in rows)} of {len(rows)} nightly backups verified.')
        if not rows or not all(ok for _, ok, _ in rows):
            return 1
    elif args.command == 'extract':
        counts = extract(args.backup, args.output)
        print(f'Verified copy written to {args.output} ({counts["math_concepts"]} math entries).')
    else:
        report = restore_live(args.backup, args.database, args.backups, apply=args.apply)
        print(json.dumps(report, indent=2))
        if report['status'] == 'preview':
            print('PREVIEW ONLY. The live database was not changed. Add --apply to restore.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
