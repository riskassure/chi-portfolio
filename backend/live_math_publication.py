"""Publish one validated math payload using the existing transactional updaters."""
import io
import json
import zipfile

from inspect_staged_package import preview
from preview_math_sync import read_snapshot
from publish_math_entry import apply
from apply_math_text_patch import apply_patch, patch_intended


def publish(data, database, backups, source):
    # Validates archive and supported payload without executing bundled scripts.
    preview(data)
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        name = next(n for n in archive.namelist() if n.endswith('.json'))
        payload = json.loads(archive.read(name))
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
