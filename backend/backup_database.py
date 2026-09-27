"""Create a consistent SQLite snapshot without overwriting an existing file."""
import argparse
from pathlib import Path
import sqlite3

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    parser.add_argument('--source', type=Path, default=Path(__file__).parent / 'portfolio.db')
    args = parser.parse_args()
    if not args.source.is_file(): raise FileNotFoundError(args.source)
    # Exclusive creation also prevents accidental overwriting through a symlink.
    with args.destination.open('xb'): pass
    with sqlite3.connect(args.source.resolve().as_uri() + '?mode=ro', uri=True) as src:
        with sqlite3.connect(args.destination) as dst:
            src.backup(dst)
            if dst.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise RuntimeError('Backup failed its integrity check.')
    print('Database snapshot created.')
