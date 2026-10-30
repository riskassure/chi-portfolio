"""Package one existing entry's content and detail changes from a known baseline."""
import argparse
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import sys
import zipfile

from apply_math_text_patch import PATCH_FIELDS, metadata_conflict_in, missing_diagram_svgs, patch_intended, patch_payload
from inspect_staged_package import preview
from preview_math_sync import read_snapshot


def local_missing_svgs(database, canonical, tex):
    """Count diagrams in tex with no stored SVG in database (the local working copy)."""
    sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))
    from services.math.render_helper import extract_all_pstricks_diagram_blocks
    if not extract_all_pstricks_diagram_blocks(tex):
        return 0
    with closing(sqlite3.connect(Path(database).resolve().as_uri() + '?mode=ro', uri=True)) as db:
        return missing_diagram_svgs(db, canonical, tex, extract_all_pstricks_diagram_blocks)


def prepare(base, local, canonical, output):
    baseline = read_snapshot(base)
    working = read_snapshot(local)
    if canonical not in baseline or canonical not in working:
        raise ValueError('Existing entry must appear in both baseline and working database.')
    expected, proposed = baseline[canonical], working[canonical]
    changed = {key for key in expected if expected[key] != proposed[key]}
    if not changed or changed - PATCH_FIELDS:
        raise ValueError('Select an entry with changes other than its slug.')
    payload = patch_payload(canonical, expected, proposed)
    if patch_intended(payload) != proposed:
        raise ValueError('Patch does not exactly reproduce the selected local entry.')
    conflict = metadata_conflict_in(local, canonical, expected, proposed)
    if conflict:
        raise ValueError(conflict[0].upper() + conflict[1:] + '.')
    missing = local_missing_svgs(local, canonical, proposed['cleaned_tex'])
    if missing:
        raise ValueError(f'{missing} diagram(s) have no stored SVG; publishing would show "[Diagram unavailable]".')
    import io
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('patch.json', json.dumps(payload, ensure_ascii=False, indent=2))
    report = preview(buffer.getvalue())
    with output.open('xb') as stream:
        stream.write(buffer.getvalue())
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('base', 'local', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--canonical', required=True)
    args = parser.parse_args()
    print(prepare(args.base, args.local, args.canonical, args.output))
