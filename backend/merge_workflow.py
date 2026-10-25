"""Option 21 of the website helper: merge and retire math entries.

This first part prepares the one-time schema upgrade that retirement needs,
as a reviewed package for options 3 (stage), 4 (check live) and 5 (publish).
Merging, retiring and undoing are added on top of it; see
docs/features/math/MERGING_ENTRIES.md.
"""
import uuid

import math_schema
from inspect_staged_package import preview
from stage_pythonanywhere_package import read_package
from website_workflow import ROOT, digest


def prepare_schema_upgrade(state, save):
    """Write the schema package and make it the active job; return its review text."""
    folder = ROOT / 'dist' / 'math-workflow' / uuid.uuid4().hex
    folder.mkdir(parents=True)
    package = folder / 'package.zip'
    math_schema.write_package(package)
    report = preview(read_package(package))
    (folder / 'review.txt').write_text(report, encoding='utf-8')
    state['job'] = dict(kind=math_schema.KIND, canonical='Math schema upgrade', package=str(package),
                        sha256=digest(package), proposed=None, remote=None, checked=False)
    save(state)
    return report


def run(state, save):
    print('1. Prepare the one-time schema upgrade for retiring entries\n0. Back')
    choice = input('Choose: ').strip()
    if choice == '1':
        print(prepare_schema_upgrade(state, save))
        print('Nothing changed yet. Use 3 (stage), 4 (check live), 5 (publish).')
