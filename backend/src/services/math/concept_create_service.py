# backend/src/services/math/concept_create_service.py

from database.math.pipeline.step2_build_diagrams import (
    process_pstricks_diagrams_in_transaction,
)

from services.math.concept_metadata_service import (
    attach_concept_metadata,
)


def create_math_concept(
    cursor,
    canonical_name: str,
    slug: str,
    title: str,
    timestamp: str,
    owner: str,
    cleaned_tex: str,
    is_cleaned_flag: int,
    classifications: list,
    types: list,
    synonyms: list,
    definitions: list,
    related_concepts: list,
) -> dict:
    """
    Create one concept, render its diagrams, and attach its metadata.

    The caller owns the surrounding transaction.
    """
    cursor.execute("""
        INSERT INTO math_concepts (
            canonical_name,
            slug,
            title,
            created_at,
            updated_at,
            owner,
            source_staging_id,
            source_file_name,
            cleaned_tex,
            rendered_tex,
            is_cleaned
        )
        VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, ?, NULL, ?);
    """, (
        canonical_name,
        slug,
        title,
        timestamp,
        timestamp,
        owner,
        cleaned_tex,
        is_cleaned_flag,
    ))

    concept_id = cursor.lastrowid

    pstricks_result = (
        process_pstricks_diagrams_in_transaction(
            cursor=cursor,
            concept_id=concept_id,
            cleaned_tex=cleaned_tex,
        )
    )

    cursor.execute("""
        UPDATE math_concepts
        SET rendered_tex = ?
        WHERE id = ?;
    """, (
        pstricks_result["rendered_tex"],
        concept_id,
    ))

    print(
        "[ADMIN CREATE PSTRICKS]",
        f"concept_id={concept_id}",
        f"blocks={pstricks_result['block_count']}",
        f"successes={pstricks_result['success_count']}",
        f"failures={pstricks_result['failure_count']}",
    )

    attach_concept_metadata(
        cursor=cursor,
        concept_id=concept_id,
        classifications=classifications,
        types=types,
        synonyms=synonyms,
        definitions=definitions,
        related_concepts=related_concepts,
    )

    return {
        "message": "New concept created and rendered successfully!",
        "concept_id": concept_id,
        "id": concept_id,
        "slug": slug,
    }