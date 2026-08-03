# backend/src/services/math/slug_helper.py

import re


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