# backend/src/services/math/retirement.py
"""Retired math entries, as every website reader must treat them.

An entry is retired when math_concepts.retired_at is set. A retired entry
merged into another names its survivor in retired_into_id; one retired
without a survivor leaves it NULL. Retired entries stay in the database with
their names and URLs reserved, but readers show only active entries: the
catalog, search and autolinker skip them, and links or URLs that name one
lead to its survivor.

RETIREMENT_CONTRACT is the version of that behaviour this code implements.
tests/test_retirement_readers.py defines contract 1 and checks every reader
against it; the live database records the minimum version its retirements
need, and the helper compares the two before deploying code or publishing a
retirement. Raise it only together with the tests that define the new
version. It must stay a plain integer literal: the helper reads it with ast
without running this file.

Databases from before the retirement schema upgrade have no such columns;
every function here treats all their entries as active.
"""

RETIREMENT_CONTRACT = 1

# Followed when resolving a redirect; merges flatten redirects, so a longer
# chain means damaged data and the entry is treated as having no survivor.
MAX_REDIRECT_HOPS = 5


def retirement_enabled(cursor) -> bool:
    """Whether this database has the retirement columns."""
    columns = {row[1] for row in cursor.execute("PRAGMA table_info(math_concepts)").fetchall()}
    return "retired_at" in columns


def active_condition(cursor, alias: str = "mc") -> str:
    """SQL condition true for active entries of the math_concepts alias; always true without the schema."""
    if not retirement_enabled(cursor):
        return "1 = 1"
    return f"{alias}.retired_at IS NULL"


def redirects(cursor) -> dict:
    """Return {retired id: final active survivor id, or None when the entry has no survivor}."""
    if not retirement_enabled(cursor):
        return {}
    rows = cursor.execute("""
        SELECT id, retired_into_id
        FROM math_concepts
        WHERE retired_at IS NOT NULL;
    """).fetchall()
    direct = {row[0]: row[1] for row in rows}
    resolved = {}
    for ident, target in direct.items():
        hops = 0
        while target in direct and hops < MAX_REDIRECT_HOPS:
            target = direct[target]
            hops += 1
        resolved[ident] = None if target in direct else target
    return resolved


def resolve_concept_id(cursor, concept_id):
    """Return the active entry concept_id leads to: itself, its survivor, or None if retired without one."""
    return redirects(cursor).get(concept_id, concept_id)


def retired_slug_targets(cursor) -> dict:
    """Return {retired canonical name, casefolded: survivor slug} for retired entries that have a survivor."""
    targets = redirects(cursor)
    if not targets:
        return {}
    slugs = dict(cursor.execute("SELECT id, slug FROM math_concepts").fetchall())
    result = {}
    for ident, canonical in cursor.execute(
            "SELECT id, canonical_name FROM math_concepts WHERE retired_at IS NOT NULL").fetchall():
        survivor = targets.get(ident)
        if canonical and survivor in slugs and slugs[survivor]:
            result[canonical.strip().casefold()] = slugs[survivor].strip()
    return result


def retirement_info(cursor, concept_id) -> dict | None:
    """Return {retired_at, retired_into_id, retirement_reason} for a retired entry, else None."""
    if not retirement_enabled(cursor):
        return None
    row = cursor.execute("""
        SELECT retired_at, retired_into_id, retirement_reason
        FROM math_concepts
        WHERE id = ? AND retired_at IS NOT NULL;
    """, (concept_id,)).fetchone()
    if not row:
        return None
    return {
        "retired_at": row[0],
        "retired_into_id": row[1],
        "retirement_reason": row[2],
    }
