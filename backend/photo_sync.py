"""Publish one new gallery image and its metadata; existing photos are never overwritten."""
from contextlib import closing
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import uuid
import zipfile

FIELDS = ('file_path','title','location_name','latitude','longitude','is_currently_displayed')
LIMIT = 25 * 1024 * 1024


def catalog(database):
    with closing(sqlite3.connect(Path(database).resolve().as_uri()+'?mode=ro', uri=True)) as db:
        return {row[0]:dict(zip(FIELDS,row)) for row in db.execute('SELECT '+','.join(FIELDS)+' FROM photography_catalog')}


def validate(payload, image):
    if set(payload) != {'kind','photo','sha256'} or payload['kind'] != 'photo-add':
        raise ValueError('Invalid photo package.')
    photo = payload['photo']
    if not isinstance(photo,dict) or set(photo) != set(FIELDS):
        raise ValueError('Invalid photo metadata.')
    if not isinstance(photo['file_path'],str) or not re.fullmatch(r'images/photography/[A-Za-z0-9_-]+\.webp', photo['file_path']):
        raise ValueError('Photo path must be a simple WebP filename in images/photography.')
    for key in ('title','location_name'):
        if not isinstance(photo[key],str) or len(photo[key])>200:
            raise ValueError('Invalid photo title or location.')
    if not photo['title'].strip():
        raise ValueError('Photo title is required.')
    for key, bound in (('latitude',90),('longitude',180)):
        value=photo[key]
        if type(value) not in (int,float) or not math.isfinite(value) or abs(value)>bound:
            raise ValueError('Invalid coordinates.')
    if type(photo['is_currently_displayed']) is not int or photo['is_currently_displayed'] not in (0,1):
        raise ValueError('Invalid gallery visibility.')
    if len(image)>LIMIT or len(image)<12 or image[:4]!=b'RIFF' or image[8:12]!=b'WEBP':
        raise ValueError('A WebP image of at most 25 MB is required.')
    if hashlib.sha256(image).hexdigest()!=payload['sha256']:
        raise ValueError('Photo checksum does not match.')


def unpack(data, payload):
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        if set(archive.namelist()) != {'photo.json','photo.webp'} or len(archive.namelist())!=2:
            raise ValueError('Photo packages must contain only photo.json and photo.webp.')
        image=archive.read('photo.webp')
    validate(payload,image)
    return image


def target_path(frontend, payload):
    root=Path(frontend).resolve()
    target=root/payload['photo']['file_path']
    if target.is_symlink() or target.resolve()!=target or not target.resolve().is_relative_to(root):
        raise ValueError('Photo destination cannot traverse links or leave frontend.')
    return target


def status(database,payload,image,frontend,connection=None):
    validate(payload,image)
    target=target_path(frontend,payload)
    if target.exists() and (not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest()!=payload['sha256']):
        return 'CONFLICT - image filename already contains different content'
    if connection is None:
        with closing(sqlite3.connect(Path(database).resolve().as_uri()+'?mode=ro',uri=True)) as db:
            return status(database,payload,image,frontend,db)
    row=connection.execute('SELECT '+','.join(FIELDS)+' FROM photography_catalog WHERE file_path=?', (payload['photo']['file_path'],)).fetchone()
    if row:
        if dict(zip(FIELDS,row))==payload['photo'] and target.is_file():
            return 'ALREADY PRESENT - image and metadata match'
        return 'CONFLICT - gallery entry exists or its image is missing; review required'
    return 'NO DUPLICATE FOUND - eligible for further review'


def prepare(base,working,file_path,frontend,output):
    if file_path in catalog(base):
        raise ValueError('This photo exists in the baseline. Only new-photo publishing is supported.')
    photo=catalog(working).get(file_path)
    if not photo:
        raise ValueError('Photo not found in local gallery.')
    payload=dict(kind='photo-add',photo=photo,sha256='')
    # Check the path before reading any file chosen from database content.
    if not re.fullmatch(r'images/photography/[A-Za-z0-9_-]+\.webp',file_path):
        raise ValueError('Unsupported photo filename.')
    image=target_path(frontend,payload).read_bytes()
    payload['sha256']=hashlib.sha256(image).hexdigest()
    validate(payload,image)
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('photo.json',json.dumps(payload,indent=2))
        archive.writestr('photo.webp',image)
    return payload


def apply(database,payload,image,backups,frontend):
    validate(payload,image)
    from PIL import Image
    with Image.open(io.BytesIO(image)) as decoded:
        if decoded.format!='WEBP' or decoded.width>1920 or decoded.height>1920:
            raise ValueError('Publish an optimized WebP image no larger than 1920 by 1920.')
        decoded.load()
    with closing(sqlite3.connect(Path(database).resolve().as_uri()+'?mode=rw',uri=True,timeout=10)) as db:
        db.execute('BEGIN IMMEDIATE')
        outcome=status(database,payload,image,frontend,db)
        if outcome.startswith('ALREADY PRESENT'):
            return dict(status='ALREADY_PRESENT',canonical=payload['photo']['file_path'],backup=None)
        if not outcome.startswith('NO DUPLICATE FOUND'):
            raise ValueError(outcome)
        backups=Path(backups);backups.mkdir(parents=True,exist_ok=True)
        backup=backups/('before-photo-update-'+uuid.uuid4().hex+'.db')
        with backup.open('xb'): pass
        with closing(sqlite3.connect(Path(database).resolve().as_uri()+'?mode=ro',uri=True)) as source, closing(sqlite3.connect(backup)) as dest:
            source.backup(dest)
            if dest.execute('PRAGMA integrity_check').fetchone()[0]!='ok':
                raise ValueError('Photo backup verification failed.')
        target=target_path(frontend,payload)
        target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():
            temporary=target.with_name('.upload-'+uuid.uuid4().hex)
            try:
                with temporary.open('xb') as stream:
                    stream.write(image)
                    stream.flush()
                    os.fsync(stream.fileno())
                # Atomic creation without overwriting any concurrently created image.
                os.link(temporary,target)
            finally:
                temporary.unlink(missing_ok=True)
        if hashlib.sha256(target.read_bytes()).hexdigest()!=payload['sha256']:
            raise ValueError('Image verification failed; no catalog update committed.')
        db.execute('INSERT INTO photography_catalog ('+','.join(FIELDS)+',display_count) VALUES (?,?,?,?,?,?,0)',tuple(payload['photo'][k] for k in FIELDS))
        if not status(database,payload,image,frontend,db).startswith('ALREADY PRESENT'):
            raise ValueError('Photo publication verification failed.')
        db.commit()
    return dict(status='APPLIED',canonical=payload['photo']['file_path'],backup=str(backup))
