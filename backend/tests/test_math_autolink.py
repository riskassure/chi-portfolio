from pathlib import Path
import sqlite3
import sys
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from services.math.autolink_service import apply_math_autolinker


class MathAutolinkTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.addCleanup(self.db.close)
        self.db.executescript("""
            CREATE TABLE math_concepts (
                id INTEGER PRIMARY KEY,
                title TEXT,
                slug TEXT,
                canonical_name TEXT
            );
            CREATE TABLE math_synonyms (
                concept_id INTEGER,
                synonym_text TEXT
            );
            CREATE TABLE math_definitions (
                concept_id INTEGER,
                defined_term TEXT
            );
            CREATE TABLE math_link_exclusions (
                concept_id INTEGER,
                word TEXT
            );
        """)
        self.db.executemany(
            "INSERT INTO math_concepts VALUES (?, ?, ?, ?)",
            [
                (1, "source", "source", "source"),
                (2, "relation", "relation", "relation"),
                (3, "logical conjunction", "logical-conjunction", "logicalconjunction"),
                (4, "finite automaton", "finite-automaton", "finiteautomaton"),
                (5, "other relation", "other-relation", "otherrelation"),
            ],
        )
        self.db.executemany(
            "INSERT INTO math_synonyms VALUES (?, ?)",
            [(3, "and"), (4, "DFA"), (5, "relation")],
        )
        self.db.executemany(
            "INSERT INTO math_definitions VALUES (?, ?)",
            [(3, "logical and"), (5, "field")],
        )

    def render(self, text):
        return apply_math_autolinker(1, text, self.db.cursor())

    def test_grammatical_stop_word_is_not_linked(self):
        self.assertEqual(self.render("A and B are sets."), "A and B are sets.")

    def test_lowercase_single_word_alias_can_be_linked(self):
        output = self.render("The field is nonempty.")
        self.assertIn('slug=other-relation">field</a>', output)

    def test_phrase_and_abbreviation_aliases_are_linked(self):
        output = self.render("A logical and can be represented by a DFA.")
        self.assertIn('slug=logical-conjunction">logical and</a>', output)
        self.assertIn('slug=finite-automaton">DFA</a>', output)

    def test_exact_title_wins_over_same_spelling_synonym(self):
        output = self.render("A relation is given.")
        self.assertIn('slug=relation">relation</a>', output)
        self.assertNotIn("other-relation", output)

    def test_phrase_escape_suppresses_autolink(self):
        output = self.render(
            r"\PMlinkescapephrase{logical and} A logical and is used."
        )
        self.assertEqual(output, " A logical and is used.")


if __name__ == "__main__":
    unittest.main()
