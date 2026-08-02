# backend/src/services/math/public_concept_detail_service.py

from services.math.autolink_service import (
    apply_math_autolinker,
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
    cursor.execute("""
        SELECT
            rc.related_concept_id AS id,
            mc.title,
            mc.canonical_name,
            mc.slug
        FROM math_related_concepts rc
        JOIN math_concepts mc
            ON mc.id = rc.related_concept_id
        WHERE rc.concept_id = ?
        ORDER BY mc.title ASC;
    """, (concept_id,))

    return [
        dict(row)
        for row in cursor.fetchall()
    ]


def fetch_public_math_concept_detail(
    cursor,
    identifier,
):
    concept_row = _fetch_public_concept_row(
        cursor,
        identifier,
    )

    if not concept_row:
        return None

    concept_data = dict(concept_row)
    concept_id = concept_data["id"]

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