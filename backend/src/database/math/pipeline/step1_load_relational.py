# backend/src/utils/math/step1_load_relational.py

import sys
import re
import sqlite3
from pathlib import Path
from datetime import datetime

SRC_DIR = Path(__file__).resolve().parents[3]
sys.path.append(str(SRC_DIR))
from config import DB_PATH


def generate_slug(canonical_name):
    if not canonical_name:
        return None

    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1-\2", canonical_name)
    s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", s1)

    return (
        s2.lower()
        .replace("_", "-")
        .replace("--", "-")
    )


def normalize_to_iso_datetime(date_string):
    """
    Normalizes mixed legacy date configurations from PlanetMath macro blocks
    into a uniform 'YYYY-MM-DD HH:MM:SS' string format.
    """
    if not date_string:
        return None

    # Strip literal double/single quotes, commas, or outer spaces.
    cleaned = date_string.strip().strip('"').strip("'").strip()

    # Try parsing: YYYY-MM-DD HH:MM:SS
    try:
        dt = datetime.strptime(cleaned, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        pass

    # Try parsing shorter style: YYYY-MM-DD
    try:
        dt = datetime.strptime(cleaned, "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d 00:00:00")
    except ValueError:
        pass

    # Fallback to python-dateutil smart parsing if arbitrary text strings are hit.
    try:
        from dateutil import parser

        dt = parser.parse(cleaned)
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    except Exception:
        # Final fallback: return current clock string if completely unparsable.
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def transform_latex_content(raw_content):
    """Processes a raw LaTeX string and extracts its semantic layers."""
    metadata = {
        "canonical_name": None,
        "slug": None,
        "title": None,
        "created": None,
        "modified": None,
        "owner": None,
        "types": [],
        "defines": [],
        "related": [],
        "synonyms": [],
        "classifications": [],
        "escaped_words": [],
        "cleaned_tex": "",
    }

    try:
        header_match = re.search(
            r"\\documentclass.*\\endmetadata",
            raw_content,
            re.DOTALL
        )

        if not header_match:
            return None

        header_block = header_match.group(0)

        canon_match = re.search(r"\\pmcanonicalname\{([^}]+)\}", header_block)
        title_match = re.search(r"\\pmtitle\{([^}]+)\}", header_block)
        owner_match = (
            re.search(r"\\pmowner\{([^}]+)\}", header_block)
            or re.search(r"\\pmauthor\{([^}]+)\}", header_block)
        )
        created_match = re.search(r"\\pmcreated\{([^}]+)\}", header_block)
        modified_match = re.search(r"\\pmmodified\{([^}]+)\}", header_block)

        if canon_match:
            metadata["canonical_name"] = canon_match.group(1).strip()

        if title_match:
            metadata["title"] = title_match.group(1).strip()

        if owner_match:
            metadata["owner"] = owner_match.group(1).strip()

        if created_match:
            metadata["created"] = normalize_to_iso_datetime(created_match.group(1))

        if modified_match:
            metadata["modified"] = normalize_to_iso_datetime(modified_match.group(1))
        else:
            metadata["modified"] = metadata["created"]

        metadata["slug"] = generate_slug(metadata["canonical_name"])

        # Multi-type extraction.
        for t in re.findall(r"\\pmtype\{([^}]+)\}", header_block):
            metadata["types"].append(t.strip().capitalize())

        # Exact \pmclassification{msc}{CODE} syntax.
        for _cl_type, cl_code in re.findall(
            r"\\pmclassification\{([^}]+)\}\s*\{([^}]+)\}",
            header_block
        ):
            clean_code = cl_code.strip().replace('"', "").replace("'", "").upper()

            if clean_code:
                metadata["classifications"].append(clean_code)

        # Fallback legacy \pmclass block variants.
        for cl_block in re.findall(r"\\pmclass\{([^}]+)\}", header_block):
            for raw_code in cl_block.split(","):
                stripped_code = raw_code.strip().replace('"', "").replace("'", "")
                clean_code = re.sub(
                    r"^(msc|msc2000|msc2010):",
                    "",
                    stripped_code,
                    flags=re.IGNORECASE
                )

                if clean_code:
                    metadata["classifications"].append(clean_code.upper())

        # Side arrays.
        for d in re.findall(r"\\pmdefines\{([^}]+)\}", header_block):
            metadata["defines"].append(d.strip())

        for r in re.findall(r"\\pmrelated\{([^}]+)\}", header_block):
            metadata["related"].append(r.strip())

        for s in re.findall(r"\\pmsynonym\{([^}]+)\}", header_block):
            metadata["synonyms"].append(s.strip())

        for esc in re.findall(r"\\pmnolink\{([^}]+)\}", header_block):
            metadata["escaped_words"].append(esc.strip())

        content_match = re.search(
            r"\\begin\{document\}(.*)\\end\{document\}",
            raw_content,
            re.DOTALL
        )

        metadata["cleaned_tex"] = (
            content_match.group(1).strip()
            if content_match
            else ""
        )

        return metadata

    except Exception as e:
        print(f"⚠️ Parsing optimization failure: {e}")
        return None


def build_relational_tables():
    print("[STEP 1] Rebuilding application tables and running relational transformations...")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Drop dependent tables first.
    cursor.execute("DROP TABLE IF EXISTS math_concept_classifications;")
    cursor.execute("DROP TABLE IF EXISTS math_concept_types;")
    cursor.execute("DROP TABLE IF EXISTS math_synonyms;")
    cursor.execute("DROP TABLE IF EXISTS math_definitions;")
    cursor.execute("DROP TABLE IF EXISTS math_link_exclusions;")
    cursor.execute("DROP TABLE IF EXISTS math_related_concepts;")
    cursor.execute("DROP TABLE IF EXISTS math_concepts;")

    # Primary concept table.
    #
    # source_staging_id is intentionally a soft link, not a foreign key.
    # stg_math_import is still operationally a staging table, so this avoids
    # over-constraining rebuild workflows.
    cursor.execute("""
        CREATE TABLE math_concepts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            canonical_name TEXT NOT NULL UNIQUE,
            slug TEXT NOT NULL,
            title TEXT NOT NULL,
            created_at TEXT,
            updated_at TEXT,
            owner TEXT,
            source_staging_id INTEGER,
            source_file_name TEXT,
            cleaned_tex TEXT,
            rendered_tex TEXT,
            is_cleaned INTEGER DEFAULT 0
        );
    """)

    # Many-to-many bridge: concepts to document types.
    cursor.execute("""
        CREATE TABLE math_concept_types (
            concept_id INTEGER,
            type_id INTEGER,
            PRIMARY KEY (concept_id, type_id),
            FOREIGN KEY (concept_id)
                REFERENCES math_concepts(id)
                ON DELETE CASCADE,
            FOREIGN KEY (type_id)
                REFERENCES math_types(id)
                ON DELETE CASCADE
        );
    """)

    # Many-to-many bridge: concepts to classifications.
    cursor.execute("""
        CREATE TABLE math_concept_classifications (
            concept_id INTEGER,
            classification_id INTEGER,
            PRIMARY KEY (concept_id, classification_id),
            FOREIGN KEY (concept_id)
                REFERENCES math_concepts(id)
                ON DELETE CASCADE,
            FOREIGN KEY (classification_id)
                REFERENCES math_classifications(id)
                ON DELETE CASCADE
        );
    """)

    # Metadata tables.
    cursor.execute("""
        CREATE TABLE math_synonyms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            concept_id INTEGER,
            synonym_text TEXT,
            FOREIGN KEY(concept_id)
                REFERENCES math_concepts(id)
                ON DELETE CASCADE
        );
    """)

    cursor.execute("""
        CREATE TABLE math_definitions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            concept_id INTEGER,
            defined_term TEXT,
            FOREIGN KEY(concept_id)
                REFERENCES math_concepts(id)
                ON DELETE CASCADE
        );
    """)

    cursor.execute("""
        CREATE TABLE math_link_exclusions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            concept_id INTEGER,
            word TEXT,
            FOREIGN KEY(concept_id)
                REFERENCES math_concepts(id)
                ON DELETE CASCADE
        );
    """)

    cursor.execute("""
        CREATE TABLE math_related_concepts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            concept_id INTEGER NOT NULL,
            related_canonical_name TEXT NOT NULL,
            related_concept_id INTEGER,
            FOREIGN KEY(concept_id)
                REFERENCES math_concepts(id)
                ON DELETE CASCADE,
            FOREIGN KEY(related_concept_id)
                REFERENCES math_concepts(id)
                ON DELETE SET NULL
        );
    """)

    # Process staging items. Step 0 now supplies id, file_name, raw_content.
    cursor.execute("""
        SELECT id, file_name, raw_content
        FROM stg_math_import
        ORDER BY id ASC;
    """)

    staged_rows = cursor.fetchall()
    processed_count = 0

    for staging_id, file_name, raw_content in staged_rows:
        item = transform_latex_content(raw_content)

        if not item or not item["canonical_name"]:
            continue

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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, 0);
        """, (
            item["canonical_name"],
            item["slug"],
            item["title"],
            item["created"],
            item["modified"],
            item["owner"],
            staging_id,
            file_name,
            item["cleaned_tex"]
        ))

        concept_id = cursor.lastrowid

        # Synonyms.
        for syn in item["synonyms"]:
            if syn.strip():
                cursor.execute("""
                    INSERT INTO math_synonyms (concept_id, synonym_text)
                    VALUES (?, ?);
                """, (concept_id, syn.strip()))

        # Defined terms.
        for d_term in item["defines"]:
            if d_term.strip():
                cursor.execute("""
                    INSERT INTO math_definitions (concept_id, defined_term)
                    VALUES (?, ?);
                """, (concept_id, d_term.strip()))

        # Autolinker exclusions.
        for word in item["escaped_words"]:
            if word.strip():
                cursor.execute("""
                    INSERT INTO math_link_exclusions (concept_id, word)
                    VALUES (?, ?);
                """, (concept_id, word.strip()))

        # Related concepts are resolved after all currently known concepts are loaded.
        for rel in item["related"]:
            if rel.strip():
                cursor.execute("""
                    INSERT INTO math_related_concepts (
                        concept_id,
                        related_canonical_name
                    )
                    VALUES (?, ?);
                """, (concept_id, rel.strip()))

        # Map document types.
        for t_name in item["types"]:
            cursor.execute("""
                SELECT id
                FROM math_types
                WHERE type_name = ?;
            """, (t_name,))

            t_row = cursor.fetchone()

            if t_row:
                cursor.execute("""
                    INSERT OR IGNORE INTO math_concept_types (
                        concept_id,
                        type_id
                    )
                    VALUES (?, ?);
                """, (concept_id, t_row[0]))

        # Map classifications.
        for clean_code in item["classifications"]:
            cursor.execute("""
                SELECT id
                FROM math_classifications
                WHERE code = ?;
            """, (clean_code,))

            row = cursor.fetchone()

            if not row:
                fallback_code = re.sub(r"[^A-Z0-9]", "", clean_code)

                cursor.execute("""
                    SELECT id
                    FROM math_classifications
                    WHERE code = ?;
                """, (fallback_code,))

                row = cursor.fetchone()

            if row:
                cursor.execute("""
                    INSERT OR IGNORE INTO math_concept_classifications (
                        concept_id,
                        classification_id
                    )
                    VALUES (?, ?);
                """, (concept_id, row[0]))

        processed_count += 1

    # Resolve related concepts after all concepts have been inserted.
    cursor.execute("""
        UPDATE math_related_concepts
        SET related_concept_id = (
            SELECT mc.id
            FROM math_concepts mc
            WHERE mc.canonical_name = math_related_concepts.related_canonical_name
        )
        WHERE related_concept_id IS NULL;
    """)

    cursor.execute("""
        SELECT COUNT(*)
        FROM math_related_concepts
        WHERE related_concept_id IS NULL;
    """)

    unresolved = cursor.fetchone()[0]

    conn.commit()
    conn.close()

    print("✅ Related concept links resolved.")
    print(f"   Unresolved references: {unresolved}")
    print(f"✅ [STEP 1] Complete: Relational transformation completed for {processed_count} files.")


if __name__ == "__main__":
    build_relational_tables()