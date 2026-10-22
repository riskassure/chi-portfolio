"""Publish one validated math payload using the existing transactional updaters."""
import hashlib
import io
import json
import zipfile

from inspect_staged_package import preview
from preview_math_sync import read_snapshot
from publish_math_entry import apply
from apply_math_text_patch import apply_patch, patch_intended
import profile_sync
import photo_sync
import photo_metadata_sync
import photo_removal_sync
import frontend_sync
import diagram_sync


def publish(data, database, backups, source):
    # Validates archive and supported payload without executing bundled scripts.
    preview(data)
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        name = next(n for n in archive.namelist() if n.endswith('.json'))
        payload = json.loads(archive.read(name))
    if payload.get('kind') == 'website-code':
        return frontend_sync.apply(payload, source.parent.parent, backups)
    if payload.get('kind') == 'frontend-files':
        return frontend_sync.apply(payload, source.parent.parent/'frontend', backups)
    if payload.get('kind') == 'photo-remove':
        return photo_removal_sync.apply(database, payload, backups, source.parent.parent/'frontend')
    if payload.get('kind') == 'photo-edit':
        return photo_metadata_sync.apply(database, payload, backups, source.parent.parent/'frontend')
    if payload.get('kind') == 'photo-add':
        return photo_sync.apply(database,payload,photo_sync.unpack(data,payload),backups,source.parent.parent/'frontend')
    if payload.get('kind') == diagram_sync.KIND:
        payload, files = diagram_sync.unpack(data)
        return diagram_sync.apply(database, payload, files, backups, source,
                                  database.parent/'data'/'math'/'diagrams', hashlib.sha256(data).hexdigest())
    if payload.get('kind') == 'profile':
        return profile_sync.apply(database, payload, backups, source.parent.parent/'frontend')
    canonical = payload['canonical_name']
    patch = 'replacement_tex' in payload
    intended = (patch_intended(payload) if patch else
                {k: sorted(v) if isinstance(v, list) else v
                 for k, v in payload.items() if k != 'canonical_name'})
    current = read_snapshot(database).get(canonical)
    if current == intended:
        return dict(status='ALREADY_PRESENT', canonical=canonical, backup=None)
    # These functions independently repeat conflict checks under BEGIN IMMEDIATE,
    # back up before mutation, verify the stored record and then commit.
    backup = (apply_patch(database, payload, backups, source) if patch else
              apply(database, payload, backups, source))
    return dict(status='APPLIED', canonical=canonical, backup=str(backup))
