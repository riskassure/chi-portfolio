"""Back up application files, media and a consistent database snapshot privately."""
import argparse
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import zipfile


def backup(root, destination):
    root, destination = root.resolve(), destination.resolve()
    if destination.is_relative_to(root):
        raise ValueError('Store backups outside the site directory.')
    source = root / 'backend/portfolio.db'
    if not source.is_file():
        raise FileNotFoundError(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temp:
        snapshot = Path(temp) / 'portfolio.db'
        with closing(sqlite3.connect(source.as_uri() + '?mode=ro', uri=True)) as src:
            with closing(sqlite3.connect(snapshot)) as dst:
                src.backup(dst)
                if dst.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                    raise RuntimeError('Database integrity check failed.')
        with zipfile.ZipFile(destination, 'x', zipfile.ZIP_DEFLATED) as archive:
            for tree in ('frontend', 'backend'):
                for path in sorted((root / tree).rglob('*')):
                    relative = path.relative_to(root)
                    if path.is_symlink() or not path.is_file():
                        continue
                    if any(part.startswith('.') or part == '__pycache__' for part in relative.parts):
                        continue
                    if relative.parts[:2] == ('backend', 'data') and relative.parts[:4] != ('backend', 'data', 'math', 'diagrams'):
                        continue
                    if path.suffix in ('.pyc', '.db') or path.name.startswith('portfolio.db'):
                        continue
                    archive.write(path, relative.as_posix())
            archive.write(snapshot, 'backend/portfolio.db')
        with zipfile.ZipFile(destination) as archive:
            if archive.testzip() is not None:
                raise RuntimeError('Backup archive verification failed.')
    print(f'Backup verified: {destination}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    backup(args.root, args.destination)
