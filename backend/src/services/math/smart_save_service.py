# backend/src/services/math/smart_save_service.py

from collections import Counter

from services.math.render_helper import (
    extract_all_pstricks_diagram_blocks,
)


def normalize_tex_for_save_compare(tex: str) -> str:
    """
    Normalize enough to avoid false positives from trivial outer whitespace,
    but do not aggressively rewrite the TeX.
    """
    return (tex or "").strip()


def compare_pstricks_hashes(old_tex: str, new_tex: str) -> dict:
    old_hashes = [
        block["source_hash"]
        for block in extract_all_pstricks_diagram_blocks(old_tex)
    ]

    new_hashes = [
        block["source_hash"]
        for block in extract_all_pstricks_diagram_blocks(new_tex)
    ]

    old_counter = Counter(old_hashes)
    new_counter = Counter(new_hashes)

    added_hashes = list((new_counter - old_counter).elements())
    removed_hashes = list((old_counter - new_counter).elements())
    unchanged_hashes = list((old_counter & new_counter).elements())

    return {
        "old_count": len(old_hashes),
        "new_count": len(new_hashes),
        "unchanged_count": len(unchanged_hashes),
        "added_count": len(added_hashes),
        "removed_count": len(removed_hashes),
        "old_hashes": old_hashes,
        "new_hashes": new_hashes,
        "added_hashes": added_hashes,
        "removed_hashes": removed_hashes,
        "pstricks_changed": old_counter != new_counter,
    }


def determine_smart_save_mode(old_tex: str, new_tex: str) -> dict:
    old_clean = normalize_tex_for_save_compare(old_tex)
    new_clean = normalize_tex_for_save_compare(new_tex)

    tex_changed = old_clean != new_clean
    diagram_compare = compare_pstricks_hashes(old_clean, new_clean)

    if not tex_changed:
        return {
            "save_mode": "metadata_only",
            "tex_changed": False,
            "pstricks_changed": False,
            "diagram_compare": diagram_compare,
            "message": "Saved metadata only. TeX source was unchanged.",
        }

    if not diagram_compare["pstricks_changed"]:
        return {
            "save_mode": "text_render_only",
            "tex_changed": True,
            "pstricks_changed": False,
            "diagram_compare": diagram_compare,
            "message": (
                "Saved TeX changes. PSTricks diagram blocks were unchanged."
            ),
        }

    return {
        "save_mode": "diagram_rebuild_needed",
        "tex_changed": True,
        "pstricks_changed": True,
        "diagram_compare": diagram_compare,
        "message": (
            "Saved TeX changes. PSTricks diagram blocks changed and were rebuilt."
        ),
    }
