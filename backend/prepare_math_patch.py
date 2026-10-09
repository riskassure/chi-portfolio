"""Package one existing entry's content/synonym changes from a known baseline."""
import argparse
import json
from pathlib import Path
import zipfile

from apply_math_text_patch import patch_intended
from inspect_staged_package import preview
from preview_math_sync import read_snapshot


def prepare(base, local, canonical, output):
    baseline = read_snapshot(base)
    working = read_snapshot(local)
    if canonical not in baseline or canonical not in working:
        raise ValueError('Existing entry must appear in both baseline and working database.')
    expected, proposed = baseline[canonical], working[canonical]
    changed = {key for key in expected if expected[key] != proposed[key]}
    if not changed or changed - {'cleaned_tex', 'synonyms'}:
        raise ValueError('Select an entry with changes only to content and/or synonyms.')
    payload = dict(canonical_name=canonical, expected=expected, replacement_tex=proposed['cleaned_tex'])
    if 'synonyms' in changed:
        payload['replacement_synonyms'] = proposed['synonyms']
    if patch_intended(payload) != proposed:
        raise ValueError('Patch does not exactly reproduce the selected local entry.')
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
