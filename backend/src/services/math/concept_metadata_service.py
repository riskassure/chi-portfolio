# backend/src/services/math/concept_metadata_service.py


def _attach_classifications(
    cursor,
    concept_id: int,
    classifications: list,
) -> None:
    for code in classifications:
        clean_code = code.upper().strip()

        if not clean_code:
            continue

        cursor.execute("""
            SELECT id
            FROM math_classifications
            WHERE code = ?;
        """, (clean_code,))

        row = cursor.fetchone()

        if row:
            cursor.execute("""
                INSERT OR IGNORE INTO math_concept_classifications (
                    concept_id,
                    classification_id
                )
                VALUES (?, ?);
            """, (
                concept_id,
                row[0],
            ))


def _attach_types(
    cursor,
    concept_id: int,
    types: list,
) -> None:
    for type_name in types:
        clean_type = type_name.strip().capitalize()

        if not clean_type:
            continue

        cursor.execute("""
            SELECT id
            FROM math_types
            WHERE type_name = ?;
        """, (clean_type,))

        row = cursor.fetchone()

        if row:
            cursor.execute("""
                INSERT OR IGNORE INTO math_concept_types (
                    concept_id,
                    type_id
                )
                VALUES (?, ?);
            """, (
                concept_id,
                row[0],
            ))


def _attach_synonyms(
    cursor,
    concept_id: int,
    synonyms: list,
) -> None:
    for synonym in synonyms:
        clean_synonym = synonym.strip()

        if clean_synonym:
            cursor.execute("""
                INSERT INTO math_synonyms (
                    concept_id,
                    synonym_text
                )
                VALUES (?, ?);
            """, (
                concept_id,
                clean_synonym,
            ))


def _attach_definitions(
    cursor,
    concept_id: int,
    definitions: list,
) -> None:
    for defined_term in definitions:
        clean_term = defined_term.strip()

        if clean_term:
            cursor.execute("""
                INSERT INTO math_definitions (
                    concept_id,
                    defined_term
                )
                VALUES (?, ?);
            """, (
                concept_id,
                clean_term,
            ))


def _attach_related_concepts(
    cursor,
    concept_id: int,
    related_concepts: list,
) -> None:
    for related_name in related_concepts:
        clean_related_name = related_name.strip()

        if clean_related_name:
            cursor.execute("""
                INSERT INTO math_related_concepts (
                    concept_id,
                    related_canonical_name
                )
                VALUES (?, ?);
            """, (
                concept_id,
                clean_related_name,
            ))

    cursor.execute("""
        UPDATE math_related_concepts
        SET related_concept_id = (
            SELECT mc.id
            FROM math_concepts mc
            WHERE mc.canonical_name =
                math_related_concepts.related_canonical_name
        )
        WHERE concept_id = ?;
    """, (concept_id,))


def attach_concept_metadata(
    cursor,
    concept_id: int,
    classifications: list,
    types: list,
    synonyms: list,
    definitions: list,
    related_concepts: list,
) -> None:
    """
    Attach metadata to a newly created concept.

    The caller owns the surrounding transaction.
    """
    _attach_classifications(
        cursor,
        concept_id,
        classifications,
    )

    _attach_types(
        cursor,
        concept_id,
        types,
    )

    _attach_synonyms(
        cursor,
        concept_id,
        synonyms,
    )

    _attach_definitions(
        cursor,
        concept_id,
        definitions,
    )

    _attach_related_concepts(
        cursor,
        concept_id,
        related_concepts,
    )


def replace_concept_metadata(
    cursor,
    concept_id: int,
    classifications: list,
    types: list,
    synonyms: list,
    definitions: list,
    related_concepts: list,
) -> None:
    """
    Replace all editable metadata for an existing concept.

    The caller owns the surrounding transaction.
    """
    cursor.execute("""
        DELETE FROM math_concept_classifications
        WHERE concept_id = ?;
    """, (concept_id,))

    cursor.execute("""
        DELETE FROM math_concept_types
        WHERE concept_id = ?;
    """, (concept_id,))

    cursor.execute("""
        DELETE FROM math_synonyms
        WHERE concept_id = ?;
    """, (concept_id,))

    cursor.execute("""
        DELETE FROM math_definitions
        WHERE concept_id = ?;
    """, (concept_id,))

    cursor.execute("""
        DELETE FROM math_related_concepts
        WHERE concept_id = ?;
    """, (concept_id,))

    attach_concept_metadata(
        cursor=cursor,
        concept_id=concept_id,
        classifications=classifications,
        types=types,
        synonyms=synonyms,
        definitions=definitions,
        related_concepts=related_concepts,
    )