# backend/src/services/math/concept_update_service.py

from database.math.pipeline.step2_build_diagrams import (
    process_pstricks_diagrams_in_transaction,
)

from services.math.concept_metadata_service import (
    replace_concept_metadata,
)

from services.math.concept_render_service import (
    render_tex_reusing_existing_diagrams,
)

from services.math.smart_save_service import (
    determine_smart_save_mode,
)


def update_math_concept(
    cursor,
    concept_id: int,
    updated_title: str,
    updated_owner: str,
    updated_tex: str,
    updated_at: str,
    is_cleaned_flag: int,
    classifications: list,
    types: list,
    synonyms: list,
    definitions: list,
    related_concepts: list,
):
    """
    Update one existing concept and its editable metadata.

    The caller owns the surrounding transaction.
    """
    cursor.execute("""
        SELECT
            cleaned_tex,
            slug
        FROM math_concepts
        WHERE id = ?;
    """, (concept_id,))

    existing_row = cursor.fetchone()

    if not existing_row:
        return None

    old_cleaned_tex = existing_row[0] or ""
    current_slug = existing_row[1] or None

    smart_save = determine_smart_save_mode(
        old_cleaned_tex,
        updated_tex,
    )

    if smart_save["save_mode"] in (
        "metadata_only",
        "text_render_only",
    ):
        refreshed_rendered_tex = (
            render_tex_reusing_existing_diagrams(
                concept_id=concept_id,
                cleaned_tex=updated_tex,
                cursor=cursor,
            )
        )

    else:
        pstricks_result = (
            process_pstricks_diagrams_in_transaction(
                cursor=cursor,
                concept_id=concept_id,
                cleaned_tex=updated_tex,
            )
        )

        refreshed_rendered_tex = (
            pstricks_result["rendered_tex"]
        )

        print(
            "[ADMIN SAVE PSTRICKS]",
            f"concept_id={concept_id}",
            f"blocks={pstricks_result['block_count']}",
            f"successes={pstricks_result['success_count']}",
            f"failures={pstricks_result['failure_count']}",
        )

    cursor.execute("""
        UPDATE math_concepts
        SET
            title = ?,
            owner = ?,
            cleaned_tex = ?,
            rendered_tex = ?,
            updated_at = ?,
            is_cleaned = ?
        WHERE id = ?;
    """, (
        updated_title,
        updated_owner,
        updated_tex,
        refreshed_rendered_tex,
        updated_at,
        is_cleaned_flag,
        concept_id,
    ))

    replace_concept_metadata(
        cursor=cursor,
        concept_id=concept_id,
        classifications=classifications,
        types=types,
        synonyms=synonyms,
        definitions=definitions,
        related_concepts=related_concepts,
    )

    return {
        "message": smart_save["message"],
        "concept_id": concept_id,
        "slug": current_slug,
        "save_mode": smart_save["save_mode"],
        "tex_changed": smart_save["tex_changed"],
        "pstricks_changed": smart_save["pstricks_changed"],
        "diagram_compare": smart_save["diagram_compare"],
    }