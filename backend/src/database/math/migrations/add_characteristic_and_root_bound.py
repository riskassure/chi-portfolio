"""Add two field theorems and a separately reusable factor theorem.

Catalog review includes entry bodies, not just titles. Existing prime-subfield
proofs assume a characteristic; they do not prove the zero-or-prime result.
The existing defined term 'polynomial' has a universal-algebra meaning, so
qualified polynomial terms below deliberately avoid replacing that target.
"""
import argparse
from datetime import datetime
from pathlib import Path
import re
import sqlite3
import sys

SRC = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(SRC))
from services.math.concept_create_service import create_math_concept
from services.math.public_concept_detail_service import fetch_public_math_concept_detail
from add_eight_algebra_concepts import Links, source

ENTRIES = [
    dict(title="the characteristic of a field is zero or prime",
         slug="characteristic-of-a-field-is-zero-or-prime", canonical="CharacteristicOfAFieldIsZeroOrPrime",
         classifications=["12E99"], synonyms=["field characteristic theorem"],
         definitions=["characteristic of a field", "prime number"],
         related=["field", "integral-domain", "q-is-the-prime-subfield-of-any-field-of-characteristic0-proof-that"],
         escapes=["characteristic", "identity", "product", "order", "prime", "inverse", "strong", "restriction", "arithmetic"],
         reference=("R. Sharifi", "Abstract Algebra, Section 3.4",
                    "https://www.math.ucla.edu/~sharifi/notes/algebra-ch03.html"),
         body=r"""Repeated addition of the multiplicative identity places a strong restriction on field arithmetic.

\begin{definition}
For a field \(K\), write \(m1_K\) for the sum of \(m\) copies of \(1_K\), with \(01_K=0\). The \emph{characteristic of a field} \(K\), denoted \(\operatorname{char}(K)\), is the least positive integer \(n\) with \(n1_K=0\), if one exists; otherwise it is zero. A \emph{prime number} is a positive integer greater than one with no positive divisors other than one and itself.
\end{definition}

\begin{theorem}
The characteristic of a field is either zero or a prime number.
\end{theorem}

\begin{proof}
Suppose \(\operatorname{char}(K)=n>0\). Since \(1_K\ne0\), we have \(n>1\). If \(n\) were not prime, we could write \(n=rs\) with \(1<r,s<n\). Minimality of \(n\) gives \(r1_K\ne0\) and \(s1_K\ne0\). Repeated distributivity gives
\[
(r1_K)(s1_K)=(rs)1_K=n1_K=0.
\]
Multiplying by the inverse of \(r1_K\) gives \(s1_K=0\), a contradiction. Hence \(n\) is prime.
\end{proof}

\begin{example}
The rational field has characteristic zero because a positive sum of ones is a positive rational number. In the field with elements \(0,1\) and arithmetic modulo two, \(1+1=0\) and \(1\ne0\), so its characteristic is two. The field axioms here follow by checking the two possible elements; its sole nonzero element is its own inverse.
\end{example}

\begin{remark}
For the next step, see the existing \PMlinkname{proofs identifying prime subfields}{QIsThePrimeSubfieldOfAnyFieldOfCharacteristic0ProofThat}. This theorem establishes the restriction on characteristic that those proofs assume.
\end{remark}
"""),
    dict(title="factor theorem for polynomials over a field",
         slug="factor-theorem-for-polynomials-over-a-field", canonical="FactorTheoremForPolynomialsOverAField",
         classifications=["12E05"], synonyms=["factor theorem", "polynomial factor theorem"],
         definitions=["polynomial over a field", "degree of a polynomial", "root of a polynomial", "polynomial divisibility"],
         related=["field", "splitting-field-of-a-polynomial"],
         escapes=["polynomial", "root", "degree", "identity", "product", "factor", "constant", "term", "leading", "index", "substitution", "distributive", "quotient"],
         reference=("J. S. Milne", "Fields and Galois Theory, Chapter 1 (polynomial rings)",
                    "https://www.jmilne.org/math/CourseNotes/FT.pdf"),
         body=r"""A root can be removed from a polynomial by factoring out the corresponding linear polynomial.

\begin{definition}
A \emph{polynomial over a field} \(K\) is a formal finite sum \(f(x)=\sum_{i=0}^{n}c_i x^i\), where \(c_i\in K\). Trailing zero coefficients do not change the polynomial, and equality means equality of every coefficient. The set \(K[x]\) has coefficientwise addition and multiplication determined by distributivity and \(x^ix^j=x^{i+j}\). For nonzero \(f\), the \emph{degree of a polynomial} is the largest index \(n\) with \(c_n\ne0\); the zero polynomial has no degree in this entry. A \emph{root of a polynomial} \(f\) in \(K\) is an element \(a\) with \(f(a)=\sum c_i a^i=0\). \emph{Polynomial divisibility}, written \(g\mid f\), means \(f=gh\) for some \(h\in K[x]\).
\end{definition}

\begin{theorem}
For \(f\in K[x]\) and \(a\in K\), we have \(f(a)=0\) if and only if \((x-a)\mid f(x)\). If \(f\ne0\) has degree \(n\ge1\) and \(f(a)=0\), the polynomial \(h\) in \(f=(x-a)h\) has degree \(n-1\).
\end{theorem}

\begin{proof}
For \(i\ge1\), expansion and cancellation of consecutive terms gives
\[
x^i-a^i=(x-a)\sum_{j=0}^{i-1}x^{i-1-j}a^j.
\]
Thus, with \(h(x)=\sum_{i=1}^{n}c_i\sum_{j=0}^{i-1}x^{i-1-j}a^j\),
\[
f(x)-f(a)=(x-a)h(x).
\]
If \(f(a)=0\), this is the required factorization. Conversely, substituting \(a\) into \(f=(x-a)h\) gives zero. Substitution respects products by the distributive law for the finite coefficient sums. For nonzero \(f\) of degree \(n\ge1\), the displayed \(h\) has highest term \(c_nx^{n-1}\). More generally, multiplication of any nonzero polynomial of degree \(m\) by \(x-a\) has degree \(m+1\), since its highest coefficient is unchanged. Hence every such quotient has degree \(n-1\). The zero polynomial is covered by choosing \(h=0\).
\end{proof}

\begin{example}
Over the rational field, \(f(x)=x^2-3x+2\) satisfies \(f(1)=0\), and direct expansion verifies \(f(x)=(x-1)(x-2)\).
\end{example}
"""),
    dict(title="a polynomial has at most its degree many roots",
         slug="polynomial-root-bound", canonical="PolynomialRootBound",
         classifications=["12E05"], synonyms=["polynomial root bound", "root bound for polynomials over a field"],
         definitions=["polynomial function over a field"],
         related=["field", "factor-theorem-for-polynomials-over-a-field", "principle-of-finite-induction"],
         escapes=["polynomial", "root", "degree", "identity", "product", "factor", "constant", "term", "bound", "function", "inverse", "satisfy", "square", "hypothesis"],
         reference=("J. S. Milne", "Fields and Galois Theory, Chapter 1, Exercise 1-4",
                    "https://www.jmilne.org/math/CourseNotes/FT.pdf"),
         body=r"""The degree controls how many distinct solutions a polynomial equation can have in a field.

\begin{theorem}
Let \(K\) be a field and let \(f\in K[x]\) be nonzero of degree \(n\). Then \(f\) has at most \(n\) distinct roots in \(K\).
\end{theorem}

\begin{proof}
We use \PMlinkname{induction}{PrincipleOfFiniteInduction} on \(n\). A nonzero constant has no roots, proving the case \(n=0\). Suppose \(n\ge1\) and the result holds for degree \(n-1\). If \(f\) has no roots there is nothing to prove. Otherwise choose a root \(a\). The \PMlinkname{factor theorem}{FactorTheoremForPolynomialsOverAField} gives \(f(x)=(x-a)h(x)\) with \(h\ne0\) of degree \(n-1\). For any root \(b\ne a\),
\[
0=f(b)=(b-a)h(b).
\]
The nonzero element \(b-a\) has an inverse in \(K\), so \(h(b)=0\). Induction bounds these other roots by \(n-1\); adding \(a\) gives at most \(n\).
\end{proof}

\begin{definition}
The \emph{polynomial function over a field} \(K\) associated to \(f\in K[x]\) is the function \(K\to K\) sending \(a\) to \(f(a)\). The formal polynomial and its associated function are different kinds of objects; the following result says when the function determines the polynomial.
\end{definition}

\begin{corollary}
If \(K\) has infinitely many elements and \(f,g\in K[x]\) satisfy \(f(a)=g(a)\) for every \(a\in K\), then \(f=g\) as polynomials.
\end{corollary}

\begin{proof}
Otherwise the nonzero polynomial \(f-g\) would have every element of \(K\) as a root, contradicting the finite bound given by its degree.
\end{proof}

\begin{example}
The polynomial \(x^2-1=(x-1)(x+1)\) over the rational field has exactly the two roots \(1,-1\), achieving the bound. Repeated factors do not count as distinct roots: \((x-1)^2\) has only the root \(1\), since a nonzero field element has nonzero square. Over the two-element field, \(x^2-x\) is a nonzero formal polynomial but evaluates to zero at both \(0\) and \(1\); thus the infinite-field hypothesis in the corollary is necessary.
\end{example}

\begin{remark}
The zero polynomial is excluded from the theorem because every field element is a root of it. Definitions of polynomial, degree, root, and divisibility are provided in the factor theorem entry.
\end{remark}
"""),
]


def document_types(e):
    names = set(re.findall(r"\\begin\{(definition|theorem|proof|example|remark|corollary)\}", e["body"]))
    return sorted(n.capitalize() for n in names)


def verify(c):
    for e in ENTRIES:
        d = fetch_public_math_concept_detail(c.cursor(), e["slug"])
        assert d and d["owner"] == "CWoo"
        for key in ["synonyms", "definitions"]:
            assert set(d[key]) == set(e[key]), (e["slug"], key)
        assert set(d["types"]) == set(document_types(e))
        assert {r["code"] for r in d["classifications"]} == set(e["classifications"])
        h = d["display_tex"]
        for name in document_types(e):
            assert "math-env-" + name.lower() in h
        assert h.count('class="math-env math-env-proof"') == e["body"].count(r"\begin{proof}")
        assert r"\PMlink" not in h
        maths = r"\\\(.*?\\\)|\\\[.*?\\\]"
        assert re.findall(maths, d["cleaned_tex"], re.S) == re.findall(maths, h, re.S)
        rows = c.execute("SELECT related_concept_id FROM math_related_concepts WHERE concept_id=?", (d["id"],)).fetchall()
        assert len(rows) == len(e["related"]) and all(r[0] for r in rows)
        links = Links(); links.feed(h)
        assert any(a.get("href") == "concept.html?slug=field" for a, _ in links.links)
        assert not any(a.get("href") == "concept.html?slug=polynomials-in-algebraic-systems" for a, _ in links.links)
        if e["slug"] == "polynomial-root-bound":
            for slug in ["factor-theorem-for-polynomials-over-a-field", "principle-of-finite-induction"]:
                assert any(a.get("href") == "concept.html?slug=" + slug for a, _ in links.links)
        print("Verified:", d["id"], e["slug"])


def apply(path):
    if not path.is_file():
        raise FileNotFoundError(path)
    with sqlite3.connect(path) as c:
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA foreign_keys=ON")
        for e in ENTRIES:
            if c.execute("SELECT id FROM math_concepts WHERE slug=?", (e["slug"],)).fetchone():
                continue
            for term in [e["title"], *e["synonyms"], *e["definitions"]]:
                assert not c.execute("""SELECT title FROM math_concepts WHERE lower(title)=lower(?)
                    UNION SELECT synonym_text FROM math_synonyms WHERE lower(synonym_text)=lower(?)
                    UNION SELECT defined_term FROM math_definitions WHERE lower(defined_term)=lower(?)""",
                    (term, term, term)).fetchone(), term
            for code in e["classifications"]:
                assert c.execute("SELECT id FROM math_classifications WHERE code=?", (code,)).fetchone(), code
            related = [c.execute("SELECT canonical_name FROM math_concepts WHERE slug=?", (s,)).fetchone()[0] for s in e["related"]]
            create_math_concept(c.cursor(), e["canonical"], e["slug"], e["title"], datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "CWoo", source(e), 1, e["classifications"], document_types(e), e["synonyms"], e["definitions"], related)
        verify(c)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=SRC.parent / "portfolio.db")
    apply(parser.parse_args().db)
