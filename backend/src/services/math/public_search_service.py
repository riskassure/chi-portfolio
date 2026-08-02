# backend/src/services/math/public_search_service.py


def clamp_int(
    value,
    default: int,
    min_value: int = 1,
    max_value: int = 200,
) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default

    return max(min_value, min(parsed, max_value))


def escape_like_term(term: str) -> str:
    """Escape SQLite LIKE wildcards so user text is treated literally."""
    return (
        term
        .replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )


def parse_csv_list(value) -> list[str]:
    if not value:
        return []

    return [
        item.strip()
        for item in value.split(",")
        if item and item.strip()
    ]


def resolve_search_limits(
    overall_limit_value,
    concept_limit_value,
    classification_limit_value,
    explicit_family_limits: bool,
) -> dict:
    overall_limit = clamp_int(
        overall_limit_value,
        default=20,
        max_value=200,
    )

    if explicit_family_limits:
        concept_limit = clamp_int(
            concept_limit_value,
            default=overall_limit,
            max_value=200,
        )
        classification_limit = clamp_int(
            classification_limit_value,
            default=overall_limit,
            max_value=200,
        )
    else:
        concept_limit = overall_limit
        classification_limit = overall_limit

    return {
        "overall_limit": overall_limit,
        "concept_limit": concept_limit,
        "classification_limit": classification_limit,
    }


def _append_concept_result(
    concept_results: list[dict],
    seen_concept_slugs: set[str],
    row,
    match_type: str,
    matched_text=None,
) -> None:
    slug = row["slug"]

    if not slug or slug in seen_concept_slugs:
        return

    seen_concept_slugs.add(slug)

    concept_results.append({
        "kind": "concept",
        "match_type": match_type,
        "id": row["id"],
        "title": row["title"],
        "label": row["title"],
        "slug": slug,
        "matched_text": matched_text,
        "classification_codes": parse_csv_list(
            row["classification_codes"]
        ),
    })


def _combine_search_results(
    concept_results: list[dict],
    classification_results: list[dict],
    overall_limit: int,
    explicit_family_limits: bool,
) -> list[dict]:
    if explicit_family_limits:
        return concept_results + classification_results

    if (
        concept_results
        and classification_results
        and overall_limit >= 4
    ):
        reserved_class_slots = min(
            len(classification_results),
            max(1, overall_limit // 4),
        )

        concept_take = min(
            len(concept_results),
            overall_limit - reserved_class_slots,
        )

        class_take = min(
            len(classification_results),
            overall_limit - concept_take,
        )

        return (
            concept_results[:concept_take]
            + classification_results[:class_take]
        )

    return (
        concept_results
        + classification_results
    )[:overall_limit]


def _fetch_title_matches(
    cursor,
    like_param: str,
    query_param: str,
    prefix_param: str,
    limit: int,
):
    cursor.execute("""
        SELECT
            mc.id,
            mc.title,
            mc.slug,
            GROUP_CONCAT(DISTINCT mcl.code) AS classification_codes
        FROM math_concepts mc
        LEFT JOIN math_concept_classifications mcc
            ON mc.id = mcc.concept_id
        LEFT JOIN math_classifications mcl
            ON mcc.classification_id = mcl.id
        WHERE mc.title LIKE ? ESCAPE '\\'
           OR mc.slug LIKE ? ESCAPE '\\'
           OR mc.canonical_name LIKE ? ESCAPE '\\'
        GROUP BY mc.id
        ORDER BY
            CASE
                WHEN LOWER(mc.title) = LOWER(?) THEN 0
                WHEN LOWER(mc.title) LIKE LOWER(?) ESCAPE '\\' THEN 1
                ELSE 2
            END,
            mc.title ASC
        LIMIT ?;
    """, (
        like_param,
        like_param,
        like_param,
        query_param,
        prefix_param,
        limit,
    ))

    return cursor.fetchall()


def _fetch_synonym_matches(
    cursor,
    like_param: str,
    query_param: str,
    prefix_param: str,
    limit: int,
):
    cursor.execute("""
        SELECT
            mc.id,
            mc.title,
            mc.slug,
            ms.synonym_text AS matched_text,
            GROUP_CONCAT(DISTINCT mcl.code) AS classification_codes
        FROM math_synonyms ms
        JOIN math_concepts mc
            ON ms.concept_id = mc.id
        LEFT JOIN math_concept_classifications mcc
            ON mc.id = mcc.concept_id
        LEFT JOIN math_classifications mcl
            ON mcc.classification_id = mcl.id
        WHERE ms.synonym_text LIKE ? ESCAPE '\\'
        GROUP BY ms.id
        ORDER BY
            CASE
                WHEN LOWER(ms.synonym_text) = LOWER(?) THEN 0
                WHEN LOWER(ms.synonym_text) LIKE LOWER(?) ESCAPE '\\' THEN 1
                ELSE 2
            END,
            ms.synonym_text ASC
        LIMIT ?;
    """, (
        like_param,
        query_param,
        prefix_param,
        limit,
    ))

    return cursor.fetchall()


def _fetch_definition_matches(
    cursor,
    like_param: str,
    query_param: str,
    prefix_param: str,
    limit: int,
):
    cursor.execute("""
        SELECT
            mc.id,
            mc.title,
            mc.slug,
            md.defined_term AS matched_text,
            GROUP_CONCAT(DISTINCT mcl.code) AS classification_codes
        FROM math_definitions md
        JOIN math_concepts mc
            ON md.concept_id = mc.id
        LEFT JOIN math_concept_classifications mcc
            ON mc.id = mcc.concept_id
        LEFT JOIN math_classifications mcl
            ON mcc.classification_id = mcl.id
        WHERE md.defined_term LIKE ? ESCAPE '\\'
        GROUP BY md.id
        ORDER BY
            CASE
                WHEN LOWER(md.defined_term) = LOWER(?) THEN 0
                WHEN LOWER(md.defined_term) LIKE LOWER(?) ESCAPE '\\' THEN 1
                ELSE 2
            END,
            md.defined_term ASC
        LIMIT ?;
    """, (
        like_param,
        query_param,
        prefix_param,
        limit,
    ))

    return cursor.fetchall()


def _fetch_classification_matches(
    cursor,
    like_param: str,
    query_param: str,
    prefix_param: str,
    limit: int,
):
    cursor.execute("""
        SELECT
            code,
            text,
            description
        FROM math_classifications
        WHERE code LIKE ? ESCAPE '\\'
           OR text LIKE ? ESCAPE '\\'
           OR COALESCE(description, '') LIKE ? ESCAPE '\\'
        ORDER BY
            CASE
                WHEN LOWER(code) = LOWER(?) THEN 0
                WHEN LOWER(code) LIKE LOWER(?) ESCAPE '\\' THEN 1
                WHEN LOWER(text) LIKE LOWER(?) ESCAPE '\\' THEN 2
                ELSE 3
            END,
            code ASC
        LIMIT ?;
    """, (
        like_param,
        like_param,
        like_param,
        query_param,
        prefix_param,
        prefix_param,
        limit,
    ))

    return cursor.fetchall()


def search_public_math_library(
    cursor,
    query_param: str,
    overall_limit_value=None,
    concept_limit_value=None,
    classification_limit_value=None,
    explicit_family_limits: bool = False,
) -> dict:
    limits = resolve_search_limits(
        overall_limit_value=overall_limit_value,
        concept_limit_value=concept_limit_value,
        classification_limit_value=classification_limit_value,
        explicit_family_limits=explicit_family_limits,
    )

    overall_limit = limits["overall_limit"]
    concept_limit = limits["concept_limit"]
    classification_limit = limits["classification_limit"]

    safe_query = escape_like_term(query_param)
    like_param = f"%{safe_query}%"
    prefix_param = f"{safe_query}%"

    concept_results = []
    classification_results = []

    seen_concept_slugs = set()
    seen_class_codes = set()

    title_rows = _fetch_title_matches(
        cursor=cursor,
        like_param=like_param,
        query_param=query_param,
        prefix_param=prefix_param,
        limit=concept_limit,
    )

    for row in title_rows:
        _append_concept_result(
            concept_results=concept_results,
            seen_concept_slugs=seen_concept_slugs,
            row=row,
            match_type="title",
        )

    remaining_concept_slots = max(
        0,
        concept_limit - len(seen_concept_slugs),
    )

    if remaining_concept_slots > 0:
        synonym_rows = _fetch_synonym_matches(
            cursor=cursor,
            like_param=like_param,
            query_param=query_param,
            prefix_param=prefix_param,
            limit=remaining_concept_slots,
        )

        for row in synonym_rows:
            _append_concept_result(
                concept_results=concept_results,
                seen_concept_slugs=seen_concept_slugs,
                row=row,
                match_type="synonym",
                matched_text=row["matched_text"],
            )

    remaining_concept_slots = max(
        0,
        concept_limit - len(seen_concept_slugs),
    )

    if remaining_concept_slots > 0:
        definition_rows = _fetch_definition_matches(
            cursor=cursor,
            like_param=like_param,
            query_param=query_param,
            prefix_param=prefix_param,
            limit=remaining_concept_slots,
        )

        for row in definition_rows:
            _append_concept_result(
                concept_results=concept_results,
                seen_concept_slugs=seen_concept_slugs,
                row=row,
                match_type="definition",
                matched_text=row["matched_text"],
            )

    classification_rows = _fetch_classification_matches(
        cursor=cursor,
        like_param=like_param,
        query_param=query_param,
        prefix_param=prefix_param,
        limit=classification_limit,
    )

    for row in classification_rows:
        code = row["code"]

        if not code or code in seen_class_codes:
            continue

        seen_class_codes.add(code)

        classification_results.append({
            "kind": "classification",
            "match_type": "classification",
            "code": code,
            "label": f"{code} — {row['text']}",
            "text": row["text"],
            "description": row["description"],
        })

    results = _combine_search_results(
        concept_results=concept_results,
        classification_results=classification_results,
        overall_limit=overall_limit,
        explicit_family_limits=explicit_family_limits,
    )

    return {
        "count": len(results),
        "data": results,
        "meta": {
            "concept_candidate_count": len(concept_results),
            "classification_candidate_count": len(
                classification_results
            ),
            "overall_limit": overall_limit,
            "concept_limit": concept_limit,
            "classification_limit": classification_limit,
        },
    }
