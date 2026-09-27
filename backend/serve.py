"""Production entry point; run behind an HTTPS reverse proxy."""
import os
from pathlib import Path
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))
os.environ.setdefault('FLASK_ENV', 'production')
from app import app
from config import DB_PATH

def validate_database():
    if not DB_PATH.is_file():
        raise RuntimeError('Deploy the populated portfolio database before starting the server.')
    with sqlite3.connect(DB_PATH.resolve().as_uri() + '?mode=ro', uri=True) as conn:
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {'math_concepts', 'music_catalog', 'photography_catalog'} <= tables:
            raise RuntimeError('The deployed database is missing required catalog tables.')

if __name__ == '__main__':
    validate_database()
    from waitress import serve
    serve(app, host='127.0.0.1', port=int(os.environ.get('PORT', '8080')), threads=4)
