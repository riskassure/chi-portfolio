# backend/src/services/math/admin_concept_detail_service.py


def _fetch_admin_concept_row(
    cursor,
    concept_id: int,
):
    cursor.execute("""
        SELECT
            mc.id,
            mc.canonical_name,
            mc.slug,
            mc.title,
            mc.owner,
            mc.created_at,
            mc.updated_at,
            mc.source_staging_id,
            mc.source_file_name,
            stg.raw_content AS raw_tex,
            mc.cleaned_tex,
            mc.rendered_tex,
            mc.is_cleaned
        FROM math_concepts mc
        LEFT JOIN stg_math_import stg
            ON stg.id = mc.source_staging_id
        WHERE mc.id = ?;
    """, (concept_id,))

    return cursor.fetchone()


def _fetch_admin_concept_classifications(
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


def _fetch_admin_concept_types(
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


def _fetch_admin_concept_synonyms(
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


def _fetch_admin_concept_definitions(
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


def _fetch_admin_link_exclusions(
    cursor,
    concept_id: int,
) -> list[str]:
    cursor.execute("""
        SELECT word
        FROM math_link_exclusions
        WHERE concept_id = ?
        ORDER BY word ASC;
    """, (concept_id,))

    return [
        row["word"]
        for row in cursor.fetchall()
    ]


def _fetch_admin_related_concepts(
    cursor,
    concept_id: int,
) -> list[dict]:
    cursor.execute("""
        SELECT
            rc.id,
            rc.related_canonical_name,
            rc.related_concept_id,
            mc.title,
            mc.canonical_name,
            mc.slug
        FROM math_related_concepts rc
        LEFT JOIN math_concepts mc
            ON mc.id = rc.related_concept_id
        WHERE rc.concept_id = ?
        ORDER BY
            COALESCE(
                mc.title,
                rc.related_canonical_name
            ) ASC;
    """, (concept_id,))

    return [
        dict(row)
        for row in cursor.fetchall()
    ]


def _fetch_admin_diagram_failures(
    cursor,
    concept_id: int,
) -> list[dict]:
    cursor.execute("""
        SELECT
            id,
            block_index,
            source_hash,
            source_tex,
            failure_stage,
            error_output,
            tex_temp_path,
            created_at
        FROM math_concept_diagram_failures
        WHERE concept_id = ?
        ORDER BY block_index ASC;
    """, (concept_id,))

    return [
        dict(row)
        for row in cursor.fetchall()
    ]


def fetch_admin_math_concept_detail(
    cursor,
    concept_id: int,
):
    concept_row = _fetch_admin_concept_row(
        cursor,
        concept_id,
    )

    if not concept_row:
        return None

    concept_data = dict(concept_row)

    concept_data["classifications"] = (
        _fetch_admin_concept_classifications(
            cursor,
            concept_id,
        )
    )

    concept_data["types"] = (
        _fetch_admin_concept_types(
            cursor,
            concept_id,
        )
    )

    concept_data["synonyms"] = (
        _fetch_admin_concept_synonyms(
            cursor,
            concept_id,
        )
    )

    concept_data["definitions"] = (
        _fetch_admin_concept_definitions(
            cursor,
            concept_id,
        )
    )

    concept_data["link_exclusions"] = (
        _fetch_admin_link_exclusions(
            cursor,
            concept_id,
        )
    )

    concept_data["related_concepts"] = (
        _fetch_admin_related_concepts(
            cursor,
            concept_id,
        )
    )

    concept_data["diagram_failures"] = (
        _fetch_admin_diagram_failures(
            cursor,
            concept_id,
        )
    )

    return concept_data