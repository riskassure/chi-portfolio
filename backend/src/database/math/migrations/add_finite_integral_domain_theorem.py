"""Add a short theorem with its counting lemma and finite-field definition.

Reviewed the catalog (titles, synonyms, defined terms, and full entry sources)
for finite domains and finite rings without zero divisors before authoring.
Cancellation is already proved in IntegralDomain; no duplicate entry is needed.
"""
import argparse
from datetime import datetime
from pathlib import Path
import sqlite3
import sys

SRC = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(SRC))
from services.math.concept_create_service import create_math_concept
from services.math.public_concept_detail_service import fetch_public_math_concept_detail
from add_eight_algebra_concepts import Links, source

ENTRY = dict(
    title="every finite integral domain is a field",
    slug="every-finite-integral-domain-is-a-field",
    canonical="EveryFiniteIntegralDomainIsAField",
    classifications=["13G05", "12E20"],
    synonyms=["finite integral domains are fields"],
    definitions=["finite field"],
    related=["integral-domain", "field", "ring"],
    escapes=["domain", "identity", "inverse", "product", "order", "list", "assumption"],
    reference=("M. Macauley", "Finite integral domains, Math 4120, Chapter 7",
               "https://www.math.clemson.edu/~macaule/classes/f21_math4120/slides/new/math4120_slides_chapter7_h.pdf"),
    body=r"""Finiteness turns cancellation into the existence of multiplicative inverses.

\begin{definition}
A \emph{finite field} is a field whose underlying set has finitely many elements. Here an integral domain is a commutative unital ring with \(1\ne0\) and with \(ab=0\) only when \(a=0\) or \(b=0\).
\end{definition}

\begin{lemma}
Let \(S\) have exactly \(n\) elements. If \(y_1,\ldots,y_n\) are distinct elements of \(S\), then every element of \(S\) occurs in this list.
\end{lemma}

\begin{proof}
An element of \(S\) outside the list, together with the listed elements, would give \(n+1\) distinct elements of a set with exactly \(n\) elements, a contradiction.
\end{proof}

\begin{theorem}
Every finite integral domain is a field.
\end{theorem}

\begin{proof}
Let \(D=\{x_1,\ldots,x_n\}\) be an integral domain, with the elements listed without repetition. Fix \(a\in D\) with \(a\ne0\). The elements
\[
ax_1,\ldots,ax_n
\]
are distinct by the \PMlinkname{cancellation proposition}{IntegralDomain}: indeed, \(ax_i=ax_j\) implies \(a(x_i-x_j)=0\), hence \(x_i=x_j\). By the lemma these products exhaust \(D\). In particular, \(ax_j=1\) for some \(j\). Commutativity gives \(x_ja=1\) as well. Thus every nonzero element has a multiplicative inverse, which is the remaining field axiom.
\end{proof}

\begin{remark}
Finiteness is essential: the integers form an infinite integral domain, but \(2\) has no integer multiplicative inverse, since \(2m\) is even for every integer \(m\), whereas \(1\) is odd. The commutativity assumption is already included in the definition of integral domain used here.
\end{remark}
""",
)
TYPES = ["Theorem", "Proof", "Definition", "Result", "Remark"]


def verify(c):
    d = fetch_public_math_concept_detail(c.cursor(), ENTRY["slug"])
    assert d and d["owner"] == "CWoo"
    assert set(d["types"]) == set(TYPES)
    assert set(d["synonyms"]) == set(ENTRY["synonyms"])
    assert set(d["definitions"]) == set(ENTRY["definitions"])
    assert {x["code"] for x in d["classifications"]} == set(ENTRY["classifications"])
    html = d["display_tex"]
    for section in ["theorem", "lemma", "definition", "proof", "remark"]:
        assert "math-env-" + section in html, section
    assert html.count('class="math-env math-env-proof"') == 2
    assert r"\PMlink" not in html
    links = Links(); links.feed(html)
    for slug in ENTRY["related"]:
        assert any(a.get("href") == "concept.html?slug=" + slug for a, _ in links.links), slug
    rows = c.execute("SELECT related_concept_id FROM math_related_concepts WHERE concept_id=?", (d["id"],)).fetchall()
    assert len(rows) == 3 and all(r[0] for r in rows)
    return d


def apply(path):
    if not path.is_file():
        raise FileNotFoundError(path)
    with sqlite3.connect(path) as c:
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA foreign_keys=ON")
        if not c.execute("SELECT id FROM math_concepts WHERE slug=?", (ENTRY["slug"],)).fetchone():
            for term in [ENTRY["title"], *ENTRY["synonyms"], *ENTRY["definitions"]]:
                assert not c.execute("""SELECT title FROM math_concepts WHERE lower(title)=lower(?)
                    UNION SELECT synonym_text FROM math_synonyms WHERE lower(synonym_text)=lower(?)
                    UNION SELECT defined_term FROM math_definitions WHERE lower(defined_term)=lower(?)""",
                    (term, term, term)).fetchone(), term
            related = [c.execute("SELECT canonical_name FROM math_concepts WHERE slug=?", (s,)).fetchone()[0]
                       for s in ENTRY["related"]]
            for code in ENTRY["classifications"]:
                assert c.execute("SELECT id FROM math_classifications WHERE code=?", (code,)).fetchone()
            create_math_concept(c.cursor(), ENTRY["canonical"], ENTRY["slug"], ENTRY["title"],
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "CWoo", source(ENTRY), 1,
                ENTRY["classifications"], TYPES, ENTRY["synonyms"], ENTRY["definitions"], related)
        d = verify(c)
        print("Verified:", d["id"], d["slug"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=SRC.parent / "portfolio.db")
    apply(parser.parse_args().db)
