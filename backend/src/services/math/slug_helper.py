# backend/src/services/math/slug_helper.py

import re
import unicodedata

from services.math.retirement import active_condition


def generate_slug(
    canonical_name: str | None,
) -> str | None:
    """Convert a canonical math concept name into its URL slug."""
    if not canonical_name:
        return None

    s1 = re.sub(
        r"(.)([A-Z][a-z]+)",
        r"\1-\2",
        canonical_name,
    )
    s2 = re.sub(
        r"([a-z0-9])([A-Z])",
        r"\1-\2",
        s1,
    )

    return (
        s2.lower()
        .replace("_", "-")
        .replace("--", "-")
    )

# New entries made in the editor. generate_slug above is kept for the
# PlanetMath import pipeline, whose output is what existing URLs use.

# Same format publish_math_entry.py requires.
NEW_SLUG_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")

APOSTROPHES = "'’‘ʼ`"


def slug_from_title(title: str | None) -> str:
    """Lowercase ASCII words joined by hyphens; apostrophes are dropped."""
    text = unicodedata.normalize("NFKD", title or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(f"[{APOSTROPHES}]", "", text).lower()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def canonical_from_slug(slug: str) -> str:
    """metric-space -> MetricSpace."""
    return "".join(word[:1].upper() + word[1:] for word in slug.split("-"))


def new_entry_names(cursor, title: str, requested_slug: str | None = None) -> tuple[str, str]:
    """Return (canonical_name, slug) for a new entry, or raise ValueError.

    Refuses what publish_math_entry.check_target would refuse about the
    entry's names, so the problem shows before anything is saved.
    """
    if requested_slug is not None and not isinstance(requested_slug, str):
        raise ValueError("The slug must be text, such as 'metric-space', or left blank to use the title.")
    # Titles and aliases are compared with active entries only: a retired
    # entry's title and terms were copied to its survivor. Its canonical name
    # and slug, checked below against every entry, stay reserved.
    active = active_condition(cursor, "mc")
    checks = (
        ("the title of", f"SELECT mc.title FROM math_concepts mc WHERE lower(trim(mc.title)) = lower(trim(?)) AND {active}"),
        ("a synonym of", "SELECT mc.title FROM math_synonyms s LEFT JOIN math_concepts mc ON mc.id = s.concept_id "
                         f"WHERE lower(trim(s.synonym_text)) = lower(trim(?)) AND {active}"),
        ("a term defined in", "SELECT mc.title FROM math_definitions d LEFT JOIN math_concepts mc ON mc.id = d.concept_id "
                              f"WHERE lower(trim(d.defined_term)) = lower(trim(?)) AND {active}"),
    )
    for kind, query in checks:
        row = cursor.execute(query, (title,)).fetchone()
        if row:
            raise ValueError(f"The title '{title.strip()}' is already {kind} '{row[0] or 'an entry'}'; review that entry first.")
    slug = (requested_slug or "").strip() or slug_from_title(title)
    if not slug:
        raise ValueError("The title has no letters or digits to build a URL slug from; enter a slug.")
    if not NEW_SLUG_PATTERN.fullmatch(slug):
        raise ValueError(f"Slug '{slug}' must be lowercase letters and digits joined by single hyphens.")
    canonical_name = canonical_from_slug(slug)
    for column, value in (("slug", slug), ("canonical_name", canonical_name)):
        row = cursor.execute(
            f"SELECT title FROM math_concepts WHERE lower(trim({column})) = lower(trim(?))",
            (value,),
        ).fetchone()
        if row:
            raise ValueError(f"The {column.replace('_', ' ')} '{value}' is already used by '{row[0]}'; choose another slug.")
    return canonical_name, slug
