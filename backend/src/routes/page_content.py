"""Plain-text overrides for the two public profile pages."""
from contextlib import closing
import json
from pathlib import Path
import re
import sqlite3
from flask import Blueprint, jsonify, request, session, abort
from config import DB_PATH

pages_bp = Blueprint('page_content', __name__)
FRONTEND = Path(__file__).resolve().parents[3] / 'frontend'

@pages_bp.route('/api/pages/<page>', methods=['GET', 'PUT'])
def content(page):
    if page not in ('resume', 'bio'):
        abort(404)
    if request.method == 'PUT' and not session.get('is_admin'):
        return jsonify(error='Administrator login required.'), 403
    keys = set(re.findall(r'data-page-text="([^"]+)"', (FRONTEND / (page+'.html')).read_text(encoding='utf-8')))
    with closing(sqlite3.connect(str(DB_PATH), timeout=10)) as db:
        if request.method == 'GET':
            exists = db.execute("SELECT 1 FROM sqlite_master WHERE name='profile_page_revisions'").fetchone()
            row = db.execute('SELECT revision, content FROM profile_page_revisions WHERE page=? ORDER BY revision DESC LIMIT 1', (page,)).fetchone() if exists else None
            fields = json.loads(row[1]) if row else {}
            # Retired fields (including removed contact details) are not public.
            return jsonify(version=row[0] if row else 0, fields={k:v for k,v in fields.items() if k in keys})
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or type(data.get('version')) is not int or not isinstance(data.get('fields'), dict):
            return jsonify(error='Invalid page content.'), 400
        fields = data['fields']
        if set(fields) != keys or any(not isinstance(v,str) or len(v)>20000 for v in fields.values()) or sum(map(len,fields.values()))>200000:
            return jsonify(error='Invalid text fields. Reload the page and try again.'), 400
        db.execute('BEGIN IMMEDIATE')
        db.execute('CREATE TABLE IF NOT EXISTS profile_page_revisions (page TEXT NOT NULL, revision INTEGER NOT NULL, content TEXT NOT NULL, saved_at TEXT DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(page,revision))')
        version = db.execute('SELECT COALESCE(MAX(revision),0) FROM profile_page_revisions WHERE page=?',(page,)).fetchone()[0]
        if version != data['version']:
            db.rollback()
            return jsonify(error='This page changed in another tab. Copy your edits, reload, and try again.'), 409
        db.execute('INSERT INTO profile_page_revisions(page,revision,content) VALUES(?,?,?)',(page,version+1,json.dumps(fields)))
        db.commit()
        return jsonify(version=version+1, fields=fields)
