"""A small math catalog with the production table layout, for retirement and merge tests."""
from contextlib import closing
from pathlib import Path
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import math_schema  # noqa: E402

# The tables as backend/src/database/math/pipeline builds them.
SCHEMA = '''
CREATE TABLE stg_math_import (id INTEGER PRIMARY KEY, file_name TEXT, raw_content TEXT);
CREATE TABLE math_classifications (id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT NOT NULL UNIQUE,
    text TEXT NOT NULL, description TEXT);
CREATE TABLE math_types (id INTEGER PRIMARY KEY AUTOINCREMENT, type_name TEXT UNIQUE NOT NULL);
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
CREATE TABLE math_concept_types (concept_id INTEGER, type_id INTEGER, PRIMARY KEY (concept_id, type_id),
    FOREIGN KEY (concept_id) REFERENCES math_concepts(id) ON DELETE CASCADE,
    FOREIGN KEY (type_id) REFERENCES math_types(id) ON DELETE CASCADE);
CREATE TABLE math_concept_classifications (concept_id INTEGER, classification_id INTEGER,
    PRIMARY KEY (concept_id, classification_id),
    FOREIGN KEY (concept_id) REFERENCES math_concepts(id) ON DELETE CASCADE,
    FOREIGN KEY (classification_id) REFERENCES math_classifications(id) ON DELETE CASCADE);
CREATE TABLE math_synonyms (id INTEGER PRIMARY KEY AUTOINCREMENT, concept_id INTEGER, synonym_text TEXT,
    FOREIGN KEY(concept_id) REFERENCES math_concepts(id) ON DELETE CASCADE);
CREATE TABLE math_definitions (id INTEGER PRIMARY KEY AUTOINCREMENT, concept_id INTEGER, defined_term TEXT,
    FOREIGN KEY(concept_id) REFERENCES math_concepts(id) ON DELETE CASCADE);
CREATE TABLE math_link_exclusions (id INTEGER PRIMARY KEY AUTOINCREMENT, concept_id INTEGER, word TEXT,
    FOREIGN KEY(concept_id) REFERENCES math_concepts(id) ON DELETE CASCADE);
CREATE TABLE math_related_concepts (id INTEGER PRIMARY KEY AUTOINCREMENT, concept_id INTEGER NOT NULL,
    related_canonical_name TEXT NOT NULL, related_concept_id INTEGER,
    FOREIGN KEY(concept_id) REFERENCES math_concepts(id) ON DELETE CASCADE,
    FOREIGN KEY(related_concept_id) REFERENCES math_concepts(id) ON DELETE SET NULL);
CREATE TABLE math_concept_diagrams (id INTEGER PRIMARY KEY AUTOINCREMENT, concept_id INTEGER NOT NULL,
    block_index INTEGER NOT NULL, source_hash TEXT NOT NULL, source_tex TEXT NOT NULL, svg_path TEXT NOT NULL,
    created_at TEXT NOT NULL, FOREIGN KEY(concept_id) REFERENCES math_concepts(id) ON DELETE CASCADE,
    UNIQUE(concept_id, source_hash));
CREATE TABLE math_concept_diagram_failures (id INTEGER PRIMARY KEY AUTOINCREMENT, concept_id INTEGER NOT NULL,
    block_index INTEGER NOT NULL, source_hash TEXT NOT NULL, source_tex TEXT NOT NULL, failure_stage TEXT,
    error_output TEXT, tex_temp_path TEXT, created_at TEXT NOT NULL,
    FOREIGN KEY(concept_id) REFERENCES math_concepts(id) ON DELETE CASCADE, UNIQUE(concept_id, source_hash));
INSERT INTO math_classifications(code, text) VALUES ('20A05', 'Groups'), ('99Z99', 'Only on a stub');
INSERT INTO math_types(type_name) VALUES ('Definition'), ('Theorem');
'''


def link(text, canonical):
    """The HTML the renderer makes from \\PMlinkname{text}{canonical}."""
    return f'<a class="math-explicit-link" href="concept.html?slug={canonical}">{text}</a>'


def make_catalog(path, upgraded=True):
    """Create the catalog at path; return {name: id}.

    group (1) is active, with the synonym "group alias" and an orbit link.
    monoid with inverses (2) defines "inverse element" and links to group.
    old stub (3) is the only entry classified 99Z99.
    subgroup (4) links to monoid with inverses and old stub, both by
    \\PMlinkname and as related concepts, and to group as a related concept.
    """
    with closing(sqlite3.connect(path)) as db:
        db.executescript(SCHEMA)
        entries = [
            ('Group', 'group', 'group', 'A group is a set with an operation.', [], ['group alias'], []),
            ('MonoidWithInverses', 'monoid-with-inverses', 'monoid with inverses',
             'A monoid with inverses has an inverse element for each element.', [], [], ['inverse element']),
            ('OldStub', 'old-stub', 'old stub', 'Unfinished.', [], [], []),
            ('Subgroup', 'subgroup', 'subgroup',
             'A subgroup of a monoid with inverses. See ' + link('inverses', 'MonoidWithInverses') + ' and '
             + link('the stub', 'OldStub') + '. Every group alias and old stub is mentioned.',
             ['MonoidWithInverses', 'OldStub', 'Group'], [], []),
        ]
        ids = {}
        for canonical, slug, title, html, related, synonyms, definitions in entries:
            ident = db.execute(
                'INSERT INTO math_concepts(canonical_name, slug, title, owner, created_at, updated_at, cleaned_tex, '
                'rendered_tex, is_cleaned) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)',
                (canonical, slug, title, 'CWoo', '2026-10-01', '2026-10-01', html, html)).lastrowid
            ids[title] = ident
            db.execute('INSERT INTO math_concept_types VALUES (?, 1)', (ident,))
            db.execute('INSERT INTO math_concept_classifications VALUES (?, ?)',
                       (ident, 2 if title == 'old stub' else 1))
            db.executemany('INSERT INTO math_synonyms(concept_id, synonym_text) VALUES (?, ?)',
                           [(ident, value) for value in synonyms])
            db.executemany('INSERT INTO math_definitions(concept_id, defined_term) VALUES (?, ?)',
                           [(ident, value) for value in definitions])
            for name in related:
                target = db.execute('SELECT id FROM math_concepts WHERE canonical_name = ?', (name,)).fetchone()[0]
                db.execute('INSERT INTO math_related_concepts(concept_id, related_canonical_name, related_concept_id) '
                           'VALUES (?, ?, ?)', (ident, name, target))
        db.commit()
        if upgraded:
            db.execute('BEGIN')
            math_schema.upgrade(db)
            db.commit()
    return ids


def merge_by_hand(path, absorbed, survivor, reason='merged'):
    """Apply what a merge leaves in the database (design v3 section 3), without the publisher."""
    with closing(sqlite3.connect(path)) as db:
        title = db.execute('SELECT title FROM math_concepts WHERE id = ?', (absorbed,)).fetchone()[0]
        rows = db.execute('SELECT synonym_text FROM math_synonyms WHERE concept_id = ?', (absorbed,)).fetchall()
        for value in [title] + [row[0] for row in rows]:
            db.execute('INSERT INTO math_synonyms(concept_id, synonym_text) VALUES (?, ?)', (survivor, value))
        for row in db.execute('SELECT defined_term FROM math_definitions WHERE concept_id = ?', (absorbed,)).fetchall():
            db.execute('INSERT INTO math_definitions(concept_id, defined_term) VALUES (?, ?)', (survivor, row[0]))
        db.execute('UPDATE math_concepts SET retired_at = ?, retired_into_id = ?, retirement_reason = ? WHERE id = ?',
                   ('2026-10-25T00:00:00Z', survivor, reason, absorbed))
        db.execute("UPDATE math_schema_meta SET value = '1' WHERE key = 'retirement_contract_required'")
        db.commit()


def retire_by_hand(path, ident, reason='retired', into=None):
    with closing(sqlite3.connect(path)) as db:
        db.execute('UPDATE math_concepts SET retired_at = ?, retired_into_id = ?, retirement_reason = ? WHERE id = ?',
                   ('2026-10-25T00:00:00Z', into, reason, ident))
        db.execute("UPDATE math_schema_meta SET value = '1' WHERE key = 'retirement_contract_required'")
        db.commit()
