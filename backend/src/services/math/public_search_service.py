"""Search public math names and classifications with normalized, order-independent words."""

import re
import unicodedata

from services.math.retirement import active_condition


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


def normalize_search_text(value):
    """Ignore case, accents and punctuation; apostrophes do not split possessives."""
    value = unicodedata.normalize("NFKD", value or "").casefold()
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = value.replace("'", "").replace("\u2019", "")
    return " ".join(re.findall(r"[^\W_]+", value))


def match_rank(value, query, words):
    """Lower is better; require every query word in the same searchable field.

    Substring matching keeps incomplete words useful in the quick-search dropdown.
    No stemming or spelling guesses are made, since similar math terms can differ.
    """
    text = normalize_search_text(value)
    if not query or not all(word in text for word in words):
        return None
    if text == query:
        return 0
    if text.startswith(query):
        return 1
    if query in text:
        return 2
    return 3


def _fetch_concept_matches(cursor, query, words):
    # Read only name metadata, never full article bodies. Rank before limiting so
    # multiple matching aliases cannot consume another concept's result slot.
    # Retired entries are not offered; their aliases live on in their survivor's rows.
    rows = cursor.execute(f"""
        SELECT mc.id, mc.title, mc.slug, mc.canonical_name,
               GROUP_CONCAT(DISTINCT mcl.code) AS classification_codes
        FROM math_concepts mc
        LEFT JOIN math_concept_classifications mcc ON mc.id = mcc.concept_id
        LEFT JOIN math_classifications mcl ON mcc.classification_id = mcl.id
        WHERE {active_condition(cursor, "mc")}
        GROUP BY mc.id
    """).fetchall()
    by_id = {row["id"]: row for row in rows}
    best = {}

    def consider(row, value, family, priority):
        rank = match_rank(value, query, words)
        if rank is None:
            return
        key = (priority, rank, normalize_search_text(value), value or "")
        ident = row["id"]
        if ident not in best or key < best[ident][0]:
            best[ident] = (key, row, family, value if family != "title" else None)

    for row in rows:
        consider(row, row["title"], "title", 0)
        consider(row, row["slug"], "title", 1)
        consider(row, row["canonical_name"], "title", 1)
    for table, column, family, priority in (
        ("math_synonyms", "synonym_text", "synonym", 2),
        ("math_definitions", "defined_term", "definition", 3),
    ):
        for alias in cursor.execute(f"SELECT concept_id, {column} FROM {table}").fetchall():
            row = by_id.get(alias["concept_id"])
            if row is not None:
                consider(row, alias[column], family, priority)
    return sorted(best.values(), key=lambda item: (
        item[0][:2], normalize_search_text(item[1]["title"]), item[1]["slug"] or "", item[1]["id"]
    ))


def _fetch_classification_matches(cursor, query, words, limit):
    matches = []
    for row in cursor.execute("SELECT code, text, description FROM math_classifications").fetchall():
        ranks = [(priority, rank) for priority, field in enumerate(("code", "text", "description"))
                 if (rank := match_rank(row[field], query, words)) is not None]
        if ranks:
            matches.append((min(ranks), row))
    matches.sort(key=lambda item: (item[0], item[1]["code"]))
    return [row for _, row in matches[:limit]]


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

    query = normalize_search_text(query_param)
    words = tuple(dict.fromkeys(query.split()))
    concept_results = []
    classification_results = []
    seen_concept_slugs = set()
    seen_class_codes = set()

    if query:
        for _, row, family, matched_text in _fetch_concept_matches(cursor, query, words):
            _append_concept_result(concept_results, seen_concept_slugs, row, family, matched_text)
            if len(concept_results) >= concept_limit:
                break
        classification_rows = _fetch_classification_matches(cursor, query, words, classification_limit)
    else:
        classification_rows = []

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
