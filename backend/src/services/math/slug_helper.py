# backend/src/services/math/slug_helper.py

import re
import unicodedata


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
    """Return (canonical_name, slug) for a new entry, or raise ValueError."""
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
