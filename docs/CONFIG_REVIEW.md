# Configuration initialization review

Reviewed October 18, 2026 by inspecting source and references; no utilities or
migrations were run and no runtime behavior was changed.

## Finding

`backend/src/config.py` defines paths, then automatically calls
`verify_system_directories()`. Importing a path therefore creates seven data/output
directories if absent. The function also prints messages during imports. No other
explicit calls to this function were found in the searched backend Python code.

Simply removing the final call is not sufficient for all retained utilities.

| Consumer | Observed dependency |
| --- | --- |
| `utils/parse_playlist.py` | Writes individual and consolidated JSON into `MUSIC_PROCESSED_DIR` without creating it; currently relies on config setup |
| `utils/convert_photos.py` | Creates its output directory, but calls `os.listdir(PHOTO_RAW_DIR)` without handling an absent input directory; config currently supplies an empty one |
| `services/photography/google_photos_import.py` | Creates photo output directory when importing a photo |
| `database/math/pipeline/step2_build_diagrams.py` | Creates diagram and temporary directories within rendering/build operations |
| Math diagnostics writing reports | Inspected report generators create their output parents; readers require actual report files, not just directories |
| Music/photo seeding and database utilities | Read inputs or existing database paths; missing input behavior must be checked on an isolated workspace before changing setup |
| Web routes | Import database/output paths; browsing should not require creating unrelated raw music/photo folders |

## Recommended narrow change

1. Keep path values and environment overrides unchanged.
2. Remove automatic setup from config import, retaining an explicitly callable
   setup function and a documented `python backend/src/config.py` setup entry point.
3. Make playlist processing create its output directory when it has input to
   process. Make the photo converter handle a missing input directory explicitly
   as an empty-input case, preserving the previous no-photo outcome.
4. Leave math algorithms and existing operation-specific directory creation alone.
5. Test in an isolated fresh directory tree, including configuration import with
   writes forbidden, explicit setup, absent-input utilities, playlist output,
   and app startup. Existing populated directories would conceal regressions.
6. Run the relevant regression suite before publication; deploy config and any
   modified utility modules together. No database migration should be needed.

Retaining an explicit setup entry point supports users preparing import folders
without silently coupling every import to filesystem writes. Do not move broad
directory creation into web startup merely to recreate the same side effect.

## Limits and status

This is a source review, not a fresh-install execution test or exhaustive audit
of external callers. The original review preceded the implementation recorded below. It is a predictability improvement,
not a measured speed optimization. No production changes are needed for the review.

## Implementation completed locally

Configuration import no longer creates directories. The existing setup function
is available explicitly through `python backend/src/config.py`; directory values
and environment overrides are unchanged. The playlist utility creates its output
folder when processing input, and the photo converter treats an absent input
folder as empty. Math operation-specific setup is unchanged.

Tests cover quiet imports with directory writes forbidden, repeatable explicit
setup in a fresh temporary tree, missing input folders, playlist output, and web
startup without directory creation. No production deployment has been performed.
