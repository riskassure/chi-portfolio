# backend/src/services/math/public_concept_detail_service.py

from services.math.autolink_service import (
    apply_math_autolinker,
)
from services.math.retirement import (
    redirects,
    retirement_info,
)


def _fetch_public_concept_row(
    cursor,
    identifier,
):
    identifier_text = str(identifier)

    if identifier_text.isdigit():
        cursor.execute("""
            SELECT
                mc.id,
                mc.title,
                mc.slug,
                mc.owner,
                mc.created_at,
                mc.updated_at,
                mc.cleaned_tex,
                mc.rendered_tex
            FROM math_concepts mc
            WHERE mc.slug = ?
               OR mc.id = ?;
        """, (
            identifier_text,
            int(identifier_text),
        ))
    else:
        cursor.execute("""
            SELECT
                mc.id,
                mc.title,
                mc.slug,
                mc.owner,
                mc.created_at,
                mc.updated_at,
                mc.cleaned_tex,
                mc.rendered_tex
            FROM math_concepts mc
            WHERE mc.slug = ?;
        """, (identifier_text,))

    return cursor.fetchone()


def _fetch_public_concept_types(
    cursor,
    concept_id: int,
) -> list[str]:
    cursor.execute("""
        SELECT mt.type_name
        FROM math_types mt
        JOIN math_concept_types mct
            ON mt.id = mct.type_id
        WHERE mct.concept_id = ?
        ORDER BY mt.type_name ASC;
    """, (concept_id,))

    return [
        row["type_name"]
        for row in cursor.fetchall()
    ]


def _fetch_public_concept_classifications(
    cursor,
    concept_id: int,
) -> list[dict]:
    cursor.execute("""
        SELECT mcl.code, mcl.text
        FROM math_classifications mcl
        JOIN math_concept_classifications mcc
            ON mcl.id = mcc.classification_id
        WHERE mcc.concept_id = ?
        ORDER BY mcl.code ASC;
    """, (concept_id,))

    return [
        {
            "code": row["code"],
            "text": row["text"],
        }
        for row in cursor.fetchall()
    ]


def _fetch_public_concept_synonyms(
    cursor,
    concept_id: int,
) -> list[str]:
    cursor.execute("""
        SELECT synonym_text
        FROM math_synonyms
        WHERE concept_id = ?
        ORDER BY synonym_text ASC;
    """, (concept_id,))

    return [
        row["synonym_text"]
        for row in cursor.fetchall()
    ]


def _fetch_public_concept_definitions(
    cursor,
    concept_id: int,
) -> list[str]:
    cursor.execute("""
        SELECT defined_term
        FROM math_definitions
        WHERE concept_id = ?
        ORDER BY defined_term ASC;
    """, (concept_id,))

    return [
        row["defined_term"]
        for row in cursor.fetchall()
    ]


def _fetch_public_related_concepts(
    cursor,
    concept_id: int,
) -> list[dict]:
    """Related entries, with a link to a merged entry shown as its survivor.

    Links to an entry retired without a survivor are dropped, as are links
    that a redirect turns into duplicates or into links back to this entry.
    The stored rows are never changed here.
    """
    moved = redirects(cursor)

    cursor.execute("""
        SELECT related_concept_id
        FROM math_related_concepts
        WHERE concept_id = ?
          AND related_concept_id IS NOT NULL;
    """, (concept_id,))

    stored = [row[0] for row in cursor.fetchall()]
    targets = [target for target in stored if target not in moved]
    for target in stored:
        survivor = moved.get(target, target)
        if target in moved and survivor is not None and survivor != concept_id and survivor not in targets:
            targets.append(survivor)

    related = []
    for target in targets:
        cursor.execute("""
            SELECT
                mc.id,
                mc.title,
                mc.canonical_name,
                mc.slug
            FROM math_concepts mc
            WHERE mc.id = ?;
        """, (target,))
        row = cursor.fetchone()
        if row:
            related.append(dict(row))

    return sorted(related, key=lambda item: item["title"] or "")


def fetch_public_math_concept_detail(
    cursor,
    identifier,
    _redirect_depth=0,
):
    """Return an entry's public page data, or None if no entry has this slug or id.

    For a retired entry merged into another, return the survivor's data with
    merged_from naming the retired entry. For one retired without a survivor,
    return only its title, slug and retirement details with retired=True.
    """
    concept_row = _fetch_public_concept_row(
        cursor,
        identifier,
    )

    if not concept_row:
        return None

    concept_data = dict(concept_row)
    concept_id = concept_data["id"]

    retired = retirement_info(cursor, concept_id)
    if retired:
        survivor_id = redirects(cursor).get(concept_id)
        if survivor_id is not None and _redirect_depth < 1:
            # The old URL shows the survivor; the page then switches its address.
            survivor = fetch_public_math_concept_detail(
                cursor,
                survivor_id,
                _redirect_depth=_redirect_depth + 1,
            )
            if survivor is not None:
                survivor["merged_from"] = {
                    "title": concept_data["title"],
                    "slug": concept_data["slug"],
                }
                return survivor
        return {
            "id": concept_id,
            "title": concept_data["title"],
            "slug": concept_data["slug"],
            "retired": True,
            "retired_at": retired["retired_at"],
            "retirement_reason": retired["retirement_reason"],
        }

    display_tex = (
        concept_data["rendered_tex"]
        or concept_data["cleaned_tex"]
    )

    concept_data["display_tex"] = apply_math_autolinker(
        concept_id,
        display_tex,
        cursor,
    )

    concept_data["types"] = (
        _fetch_public_concept_types(
            cursor,
            concept_id,
        )
    )

    concept_data["classifications"] = (
        _fetch_public_concept_classifications(
            cursor,
            concept_id,
        )
    )

    concept_data["synonyms"] = (
        _fetch_public_concept_synonyms(
            cursor,
            concept_id,
        )
    )

    concept_data["definitions"] = (
        _fetch_public_concept_definitions(
            cursor,
            concept_id,
        )
    )

    concept_data["related_concepts"] = (
        _fetch_public_related_concepts(
            cursor,
            concept_id,
        )
    )

    return concept_data