"""Add conservative inflected forms used by the math autolinker.

The legacy corpus often mentions a concept in the plural while its catalog
metadata contains only the singular title. These curated forms have the same
mathematical meaning as their destination. Generic homonyms are intentionally
excluded and should be reviewed entry by entry.
"""

from pathlib import Path
import sqlite3


DB_PATH = Path(__file__).resolve().parents[4] / "portfolio.db"


INFLECTION_SYNONYMS = {
    "angle": "angles",
    "arbitrary-join": "arbitrary joins",
    "atom": "atoms",
    "bisimulation": "bisimulations",
    "bounded-lattice": "bounded lattices",
    "brandt-groupoid": "Brandt groupoids",
    "categorical-pullback": "categorical pullbacks",
    "compact-element": "compact elements",
    "contextfree-language": "context-free languages",
    "contextsensitive-language": "context-sensitive languages",
    "contingency-table": "contingency tables",
    "decimal-fraction": "decimal fractions",
    "deduction": "deductions",
    "elementary-recursive-function": "elementary recursive functions",
    "equalizer": "equalizers",
    "equivalence-relation": "equivalence relations",
    "estimator": "estimators",
    "exponential-function": "exponential functions",
    "formal-grammar": "formal grammars",
    "generalized-linear-model": "generalized linear models",
    "generalized-regular-expression": "generalized regular expressions",
    "gentzen-system": "Gentzen systems",
    "hilbert-system": "Hilbert systems",
    "independent-increment": "independent increments",
    "indeterminate": "indeterminates",
    "integer": "integers",
    "irreducible-ideal": "irreducible ideals",
    "jordan-algebra": "Jordan algebras",
    "kleene-algebra1": "Kleene algebras",
    "labelled-state-transition-system": "labelled state transition systems",
    "linear-transformation": "linear transformations",
    "matrix-ring": "matrix rings",
    "mealy-machine": "Mealy machines",
    "module-homomorphism": "module homomorphisms",
    "monadic-algebra": "monadic algebras",
    "moore-machine": "Moore machines",
    "normal-modal-logic": "normal modal logics",
    "odds-ratio": "odds ratios",
    "order-ideal": "order ideals",
    "orthomodular-lattice": "orthomodular lattices",
    "partially-ordered-group": "partially ordered groups",
    "partially-ordered-ring": "partially ordered rings",
    "partial-algebraic-system": "partial algebraic systems",
    "polyadic-algebra": "polyadic algebras",
    "primitive-recursive-function": "primitive recursive functions",
    "primitive-recursive-vectorvalued-function": (
        "primitive recursive vector-valued functions"
    ),
    "proximity-space": "proximity spaces",
    "quadratic-extension": "quadratic extensions",
    "quantifier": "quantifiers",
    "random-vector": "random vectors",
    "rational-function": "rational functions",
    "regression-model": "regression models",
    "regular-expression": "regular expressions",
    "relative-complement": "relative complements",
    "relative-interior": "relative interiors",
    "relational-system": "relational systems",
    "rooted-tree": "rooted trees",
    "scott-topology": "Scott topologies",
    "semi-thue-system": "semi-Thue systems",
    "stateoutput-machine": "state-output machines",
    "subformula": "subformulas",
    "subobject": "subobjects",
}


def apply(db_path: Path = DB_PATH) -> tuple[int, int]:
    """Insert missing curated synonyms and return (inserted, already_present)."""
    inserted = 0
    already_present = 0

    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()

        for slug, synonym in INFLECTION_SYNONYMS.items():
            concept = cursor.execute(
                "SELECT id FROM math_concepts WHERE slug = ?",
                (slug,),
            ).fetchone()

            if concept is None:
                raise RuntimeError(f"Unknown math concept slug: {slug}")

            exists = cursor.execute(
                """
                SELECT 1
                FROM math_synonyms
                WHERE concept_id = ? AND lower(trim(synonym_text)) = lower(?)
                """,
                (concept[0], synonym),
            ).fetchone()

            if exists:
                already_present += 1
                continue

            cursor.execute(
                "INSERT INTO math_synonyms (concept_id, synonym_text) VALUES (?, ?)",
                (concept[0], synonym),
            )
            inserted += 1

    return inserted, already_present


if __name__ == "__main__":
    added, existing = apply()
    print(f"Added {added} autolink synonyms; {existing} already present.")
