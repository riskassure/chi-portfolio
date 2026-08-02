# backend/src/services/math/public_catalog_service.py


def build_public_catalog_query(
    classification_filter=None,
    search_query=None,
) -> tuple[str, list]:
    query = """
        SELECT
            mc.id,
            mc.title,
            mc.slug,
            mc.owner,
            mc.created_at,
            mc.updated_at,
            mc.is_cleaned,
            GROUP_CONCAT(DISTINCT mt.type_name) AS type_names,
            GROUP_CONCAT(DISTINCT mcl.code) AS classification_codes
        FROM math_concepts mc
        LEFT JOIN math_concept_types mct
            ON mc.id = mct.concept_id
        LEFT JOIN math_types mt
            ON mct.type_id = mt.id
        LEFT JOIN math_concept_classifications mcc
            ON mc.id = mcc.concept_id
        LEFT JOIN math_classifications mcl
            ON mcc.classification_id = mcl.id
    """

    conditions = []
    params = []

    if classification_filter:
        conditions.append("""
            mc.id IN (
                SELECT concept_id
                FROM math_concept_classifications
                WHERE classification_id = (
                    SELECT id
                    FROM math_classifications
                    WHERE code = ?
                )
            )
        """)
        params.append(
            classification_filter.upper().strip()
        )

    if search_query:
        clean_search_query = search_query.strip()

        conditions.append("""
            (
                mc.title LIKE ?
                OR mc.slug LIKE ?
                OR mcl.code LIKE ?
            )
        """)

        like_param = f"%{clean_search_query}%"
        params.extend([
            like_param,
            like_param,
            like_param,
        ])

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += """
        GROUP BY mc.id
        ORDER BY mc.title ASC;
    """

    return query, params


def serialize_public_catalog_rows(rows) -> list[dict]:
    concepts = []

    for row in rows:
        concept = dict(row)

        concept["types"] = (
            concept["type_names"].split(",")
            if concept["type_names"]
            else []
        )

        concept["classification_codes"] = (
            concept["classification_codes"].split(",")
            if concept["classification_codes"]
            else []
        )

        concept.pop("type_names", None)
        concepts.append(concept)

    return concepts


def fetch_public_math_catalog(
    cursor,
    classification_filter=None,
    search_query=None,
) -> list[dict]:
    query, params = build_public_catalog_query(
        classification_filter=classification_filter,
        search_query=search_query,
    )

    cursor.execute(query, params)

    return serialize_public_catalog_rows(
        cursor.fetchall()
    )
