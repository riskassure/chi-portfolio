"""Review and transactionally publish plain-text biography/resume revisions."""
from contextlib import closing
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import uuid


def page_state(database, page, connection=None):
    if page not in ('bio', 'resume'):
        raise ValueError('Unsupported profile page.')
    if connection is None:
        with closing(sqlite3.connect(Path(database).resolve().as_uri()+'?mode=ro', uri=True)) as db:
            return page_state(database, page, db)
    exists = connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='profile_page_revisions'").fetchone()
    row = connection.execute('SELECT revision,content FROM profile_page_revisions WHERE page=? ORDER BY revision DESC LIMIT 1', (page,)).fetchone() if exists else None
    return dict(version=row[0], fields=json.loads(row[1])) if row else dict(version=0, fields={})


def template_info(frontend, page):
    data = (Path(frontend)/(page+'.html')).read_bytes()
    keys = set(re.findall(r'data-page-text="([^"]+)"', data.decode('utf-8')))
    if not keys:
        raise ValueError('No editable fields found in profile template.')
    return hashlib.sha256(data).hexdigest(), keys


def validate_payload(payload):
    if set(payload) != {'kind','page','expected','replacement','template_sha256'} or payload['kind'] != 'profile':
        raise ValueError('Invalid profile payload.')
    if payload['page'] not in ('bio','resume'):
        raise ValueError('Unsupported profile page.')
    expected = payload['expected']
    if not isinstance(expected,dict) or set(expected) != {'version','fields'} or type(expected['version']) is not int or expected['version'] < 0:
        raise ValueError('Invalid expected page revision.')
    for fields in (expected['fields'], payload['replacement']):
        if not isinstance(fields,dict) or any(not isinstance(k,str) or not isinstance(v,str) or len(v)>20000 for k,v in fields.items()) or sum(map(len,fields.values()))>200000:
            raise ValueError('Invalid profile text fields.')
    if not re.fullmatch('[a-f0-9]{64}', payload['template_sha256']):
        raise ValueError('Invalid template fingerprint.')


def prepare_payload(base, working, page, frontend):
    expected = page_state(base, page)
    proposed = page_state(working, page)
    fingerprint, keys = template_info(frontend, page)
    if proposed['fields'] == expected['fields']:
        raise ValueError('No profile content changes to prepare.')
    if set(proposed['fields']) != keys:
        raise ValueError('Local saved fields differ from the template. Reload and save the local page first.')
    payload = dict(kind='profile', page=page, expected=expected,
                   replacement=proposed['fields'], template_sha256=fingerprint)
    validate_payload(payload)
    return payload


def status(database, payload, frontend, connection=None):
    validate_payload(payload)
    fingerprint, keys = template_info(frontend, payload['page'])
    if fingerprint != payload['template_sha256'] or set(payload['replacement']) != keys:
        return 'CONFLICT - page template differs; synchronize site files first'
    current = page_state(database, payload['page'], connection)
    if current['fields'] == payload['replacement']:
        return 'ALREADY PRESENT - no update needed'
    if current == payload['expected']:
        return 'EXPECTED TEXT MATCHES - eligible for further review'
    return 'CONFLICT - live profile revision differs from the baseline'


def apply(database, payload, backups, frontend):
    validate_payload(payload)
    with closing(sqlite3.connect(Path(database).resolve().as_uri()+'?mode=rw', uri=True, timeout=10)) as db:
        db.execute('BEGIN IMMEDIATE')
        outcome = status(database, payload, frontend, db)
        if outcome.startswith('ALREADY PRESENT'):
            return dict(status='ALREADY_PRESENT', canonical=payload['page'], backup=None)
        if not outcome.startswith('EXPECTED TEXT MATCHES'):
            raise ValueError(outcome)
        backups = Path(backups)
        backups.mkdir(parents=True, exist_ok=True)
        backup = backups/('before-profile-update-'+uuid.uuid4().hex+'.db')
        with backup.open('xb'):
            pass
        with closing(sqlite3.connect(Path(database).resolve().as_uri()+'?mode=ro', uri=True)) as source, closing(sqlite3.connect(backup)) as target:
            source.backup(target)
            if target.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise ValueError('Backup verification failed.')
        db.execute('CREATE TABLE IF NOT EXISTS profile_page_revisions (page TEXT NOT NULL, revision INTEGER NOT NULL, content TEXT NOT NULL, saved_at TEXT DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(page,revision))')
        revision = payload['expected']['version'] + 1
        db.execute('INSERT INTO profile_page_revisions(page,revision,content) VALUES(?,?,?)',
                   (payload['page'], revision, json.dumps(payload['replacement'])))
        if page_state(database, payload['page'], db) != dict(version=revision, fields=payload['replacement']):
            raise ValueError('Profile verification failed; changes rolled back.')
        db.commit()
    return dict(status='APPLIED', canonical=payload['page'], backup=str(backup), revision=revision)
