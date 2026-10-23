"""Add a batch of new math entries (title, slug, metadata, body) and verify them.

Shared by the add_*_entries_20261023.py migrations. Each entry dict carries title,
slug, classifications, synonyms, definitions (defined terms), related slugs, body
and reference; entries are created in list order with fresh ids. Run a migration
with --db PATH to preview on a temporary copy, and add --apply to back up and write.
"""
import argparse
from datetime import datetime
import re
import sqlite3

from add_eight_algebra_concepts import SRC, source, Links  # noqa: F401  (SRC puts backend/src on sys.path)
from add_twenty_concepts_20260922 import ESCAPES
from services.math.concept_create_service import create_math_concept
from services.math.slug_helper import new_entry_names
from services.math.public_concept_detail_service import fetch_public_math_concept_detail
from services.math.public_search_service import search_public_math_library

TYPE = {"definition": "Definition", "theorem": "Theorem", "proof": "Proof", "example": "Example",
        "remark": "Remark", "corollary": "Corollary", "lemma": "Result", "proposition": "Result"}


def document_types(entry):
    return sorted({TYPE[n] for n in re.findall(r"\\begin\{(\w+)\}", entry["body"]) if n in TYPE})


def links(html):
    parser = Links(); parser.feed(html)
    return [x["href"].split("slug=", 1)[1] for x, _ in parser.links
            if x.get("href", "").startswith("concept.html?slug=")]


def add_entries(c, entries):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Check every title, synonym and defined term before writing anything.
    for e in entries:
        for term in [e["title"], *e["synonyms"], *e["definitions"]]:
            hit = c.execute("""SELECT title FROM math_concepts WHERE lower(title)=lower(?)
                UNION SELECT synonym_text FROM math_synonyms WHERE lower(synonym_text)=lower(?)
                UNION SELECT defined_term FROM math_definitions WHERE lower(defined_term)=lower(?)""",
                            (term, term, term)).fetchone()
            assert not hit, (e["slug"], term, "already used")
    for e in entries:
        canonical, slug = new_entry_names(c.cursor(), e["title"], e["slug"])
        create_math_concept(c.cursor(), canonical, slug, e["title"], now, "CWoo", source(e), 1,
                            e["classifications"], document_types(e), e["synonyms"], e["definitions"], [])
    for e in entries:
        cid = c.execute("SELECT id FROM math_concepts WHERE slug=?", (e["slug"],)).fetchone()[0]
        for target in e["related"]:
            row = c.execute("SELECT id, canonical_name FROM math_concepts WHERE slug=?", (target,)).fetchone()
            assert row, (e["slug"], "related entry missing", target)
            c.execute("INSERT INTO math_related_concepts(concept_id,related_canonical_name,related_concept_id) "
                      "VALUES(?,?,?)", (cid, row[1], row[0]))


def verify(c, entries):
    for e in entries:
        html = fetch_public_math_concept_detail(c.cursor(), e["slug"])["display_tex"]
        assert r"\PMlink" not in html, (e["slug"], "unrendered link")
        found = links(html)
        for target in re.findall(r"\\PMlinkname\{[^{}]*\}\{([^{}]*)\}", e["body"]):
            assert c.execute("SELECT 1 FROM math_concepts WHERE canonical_name=?", (target,)).fetchone(), \
                (e["slug"], "explicit link target missing", target)
        for target in found:
            assert c.execute("SELECT 1 FROM math_concepts WHERE slug=?", (target,)).fetchone(), \
                (e["slug"], "link to a missing entry", target)
        assert e["slug"] not in found, (e["slug"], "links to itself")
        assert html.count("math-env-proof") >= e["body"].count(r"\begin{proof}"), (e["slug"], "proofs")
        assert any(r.get("slug") == e["slug"] for r in search_public_math_library(c.cursor(), e["title"])["data"])
        print("Verified", e["slug"])
    assert c.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def run_batch(entries, extra_escapes, description):
    from migration_db import migration_target
    for e in entries:
        e["escapes"] = list(dict.fromkeys(ESCAPES + extra_escapes))
    with migration_target(argparse.ArgumentParser(description=description)) as db:
        with sqlite3.connect(db) as c:
            c.row_factory = sqlite3.Row
            c.execute("PRAGMA foreign_keys=ON")
            add_entries(c, entries)
            verify(c, entries)
        c.close()
