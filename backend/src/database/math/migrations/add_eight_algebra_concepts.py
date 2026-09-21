"""Create eight reviewed gaps in the algebra catalog using the CMS services.

Existing entries are never overwritten. Creation and verification are atomic;
rerunning validates the existing entries without duplicating metadata.
"""

import argparse
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
import re
import sqlite3
import sys

SRC = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(SRC))

from services.math.concept_create_service import create_math_concept
from services.math.public_concept_detail_service import fetch_public_math_concept_detail


ENTRIES = [
    dict(
        title="Jacobson radical", slug="jacobson-radical", canonical="JacobsonRadical",
        classifications=["16N20"], synonyms=["Jacobson radicals"], definitions=[],
        related=["semisimple-ring", "upper-nilradical", "prime-radical"],
        origins=[("semisimple-ring", "Jacobson radical"), ("upper-nilradical", "Jacobson radical")],
        escapes=["field", "ideal", "maximal ideal", "identity", "unit", "left", "right", "radical", "useful"],
        reference=("R. Sharifi", "Abstract Algebra, Section 8.2",
                   "https://math.ucla.edu/~sharifi/notes/algebra-ch08.html"),
        body=r"""The Jacobson radical associates an ideal to an associative ring that measures an obstruction to semisimplicity.

\begin{definition}
Let \(R\) be an associative ring with identity. Its \emph{Jacobson radical} is
\[
J(R)=\bigcap\{L\subseteq R:L\text{ is a maximal left ideal of }R\}.
\]
For the zero ring, the intersection of this empty family is understood to be \(R\).
\end{definition}

Although the definition uses left ideals, \(J(R)\) is a two-sided ideal. It is also the intersection of the maximal right ideals. A useful characterization is
\[
x\in J(R)\quad\Longleftrightarrow\quad
1-rx\text{ is invertible for every }r\in R.
\]

\begin{example}
In \(\mathbb{Z}/8\mathbb{Z}\), the unique maximal ideal consists of the residue classes \(0,2,4,6\), so this ideal is the Jacobson radical. In a field the Jacobson radical is zero. Also \(J(\mathbb{Z})=0\), since an integer divisible by every prime must be zero.
\end{example}

\begin{remark}
For a commutative ring, the Jacobson radical need not equal the nilradical. For example, in the localization \(\mathbb{Z}_{(p)}\) at a prime \(p\), the Jacobson radical is \(p\mathbb{Z}_{(p)}\), while the nilradical is zero.
\end{remark}
""",
    ),
    dict(
        title="endomorphism ring", slug="endomorphism-ring", canonical="EndomorphismRing",
        classifications=["16S50"], synonyms=["endomorphism rings", "ring of endomorphisms"], definitions=[],
        related=["fittings-lemma", "hopfian-module", "matrix-ring", "ibn"],
        origins=[("fittings-lemma", "endomorphism ring"), ("ibn", "endomorphism ring")],
        escapes=["field", "identity", "zero", "left", "right", "structure", "basis"],
        reference=("R. Sharifi", "Abstract Algebra, Sections 3.4 and 13.1",
                   "https://math.ucla.edu/~sharifi/notes/algebra-ch13.html"),
        body=r"""Addition and composition turn the linear self-maps of a module into a ring.

\begin{definition}
Let \(R\) be an associative ring with identity and \(M\) a unital left \(R\)-module. The \emph{endomorphism ring} of \(M\) is
\[
\operatorname{End}_R(M)=\{f:M\to M\mid f\text{ is }R\text{-linear}\},
\]
with operations
\[
(f+g)(m)=f(m)+g(m),\qquad (fg)(m)=f(g(m)).
\]
Its zero is the zero map, and its multiplicative identity is \(\operatorname{id}_M\).
\end{definition}

The same construction applies to an abelian group by viewing it as a \(\mathbb{Z}\)-module. The addition requires the additive structure; an arbitrary set of self-maps does not carry this ring structure.

\begin{example}
Every endomorphism of the additive group \(\mathbb{Z}\) is multiplication by a unique integer. Consequently \(\operatorname{End}_{\mathbb{Z}}(\mathbb{Z})\cong\mathbb{Z}\). If \(K\) is a field, choosing a basis identifies \(\operatorname{End}_K(K^n)\) with the matrix ring \(M_n(K)\).
\end{example}

\begin{remark}
The units of \(\operatorname{End}_R(M)\) are precisely the \(R\)-module automorphisms of \(M\). Even when \(R\) is commutative, its modules can have noncommutative endomorphism rings, as \(M_2(K)\) illustrates.
\end{remark}
""",
    ),
    dict(
        title="division ring", slug="division-ring", canonical="DivisionRing",
        classifications=["16K40"], synonyms=["division rings", "skew field", "skew fields"], definitions=[],
        related=["hermitian-form-over-a-division-ring", "wedderburn-artin-theorem", "matrix-ring"],
        origins=[("hermitian-form-over-a-division-ring", "division ring"), ("semisimple-ring", "division rings")],
        escapes=["field", "identity", "inverse", "unit", "center"],
        reference=("R. Sharifi", "Abstract Algebra, Section 3.1",
                   "https://math.ucla.edu/~sharifi/notes/algebra-ch03.html"),
        body=r"""A division ring permits division by nonzero elements while allowing multiplication to be noncommutative.

\begin{definition}
A \emph{division ring}, also called a \emph{skew field}, is an associative ring \(D\) with \(1\ne0\) in which each \(a\ne0\) has a two-sided multiplicative inverse:
\[
aa^{-1}=a^{-1}a=1.
\]
Thus \(D\setminus\{0\}\) is a group under multiplication. A commutative division ring is a field.
\end{definition}

\begin{example}
Every field is a division ring. The real quaternions \(\mathbb{H}\) form a noncommutative division ring: \(ij=k=-ji\), and for a nonzero quaternion \(q\),
\[
q^{-1}=\frac{\overline q}{q\overline q},
\]
where \(q\overline q\) is a strictly positive real number.
\end{example}

\begin{remark}
The two-sided inverse condition distinguishes division rings from rings with only some invertible elements. For example, \(M_2(K)\) is not a division ring: it contains nonzero singular matrices.
\end{remark}
""",
    ),
    dict(
        title="integral domain", slug="integral-domain", canonical="IntegralDomain",
        classifications=["13G05"], synonyms=["integral domains"], definitions=[],
        related=["integer", "bezout-domain", "gcd-domain", "reduced-ring"],
        origins=[("bezout-domain", "integral domain"), ("reduced-ring", "integral domains")],
        escapes=["field", "domain", "identity", "unit", "product", "injective"],
        reference=("R. Sharifi", "Abstract Algebra, Section 3.4",
                   "https://math.ucla.edu/~sharifi/notes/algebra-ch03.html"),
        body=r"""Integral domains abstract the absence of zero divisors in the integers.

\begin{definition}
An \emph{integral domain} is a commutative ring \(D\) with \(1\ne0\) such that
\[
ab=0\quad\Longrightarrow\quad a=0\text{ or }b=0.
\]
\end{definition}

\begin{example}
The integers and every field are integral domains. The ring \(\mathbb{Z}/6\mathbb{Z}\) is not: its nonzero residue classes \(2\) and \(3\) have product zero.
\end{example}

\begin{proposition}
Multiplication by a nonzero element of an integral domain is injective.
\end{proposition}

\begin{proof}
If \(a\ne0\) and \(ab=ac\), then \(a(b-c)=0\). The defining property forces \(b-c=0\), hence \(b=c\).
\end{proof}

\begin{remark}
Commutativity is part of the convention here. Some authors also study noncommutative rings without zero divisors under the broader name ``domain''.
\end{remark}
""",
    ),
    dict(
        title="field extension", slug="field-extension", canonical="FieldExtension",
        classifications=["12F99"], synonyms=["field extensions", "extension field", "extension fields"],
        definitions=["degree of a field extension", "finite field extension", "algebraic field extension"],
        related=["pythagorean-field", "quadratic-extension", "dependence-relation"],
        origins=[("pythagorean-field", "field extension"), ("dependence-relation", "field extension")],
        escapes=["field", "degree", "dimension", "root", "base", "finite", "embedding", "image", "quotient", "polynomial", "basis", "relation"],
        reference=("The Stacks Project", "Field extensions and Finite extensions",
                   "https://stacks.math.columbia.edu/tag/09FT"),
        body=r"""A field extension studies a field together with a specified smaller field of scalars.

\begin{definition}
If \(K\) is a subfield of \(L\), then \(L\) is a \emph{field extension} of \(K\), written \(L/K\). More generally, one specifies an embedding \(K\hookrightarrow L\) and identifies \(K\) with its image. The notation \(L/K\) denotes an extension, not a quotient.
\end{definition}

\begin{definition}
The \emph{degree of a field extension} is its vector-space dimension
\[
[L:K]=\dim_K L.
\]
It is a \emph{finite field extension} when this dimension is finite. It is an \emph{algebraic field extension} when each element of \(L\) satisfies a nonzero polynomial with coefficients in \(K\).
\end{definition}

\begin{example}
The extension \(\mathbb{Q}(\sqrt{2})/\mathbb{Q}\) has basis \(1,\sqrt{2}\) and degree \(2\). By contrast, \(K(t)/K\), with \(t\) an indeterminate, is not algebraic: no nonzero polynomial over \(K\) vanishes at \(t\).
\end{example}

\begin{remark}
Every finite field extension is algebraic. If \([L:K]=n\), the \(n+1\) elements \(1,\alpha,\ldots,\alpha^n\) are linearly dependent for each \(\alpha\in L\), giving the required polynomial relation.
\end{remark}
""",
    ),
    dict(
        title="splitting field of a polynomial", slug="splitting-field-of-a-polynomial", canonical="SplittingFieldOfAPolynomial",
        classifications=["12F05", "12E05"],
        synonyms=["splitting field", "splitting fields", "splitting fields of polynomials"], definitions=[],
        related=["example-of-nonperfect-field", "quadratic-extension"],
        origins=[("example-of-nonperfect-field", "splitting field")],
        escapes=["field", "root", "degree", "normal", "simple", "polynomial", "base"],
        reference=("The Stacks Project", "Splitting fields, Section 9.16",
                   "https://stacks.math.columbia.edu/tag/09HT"),
        body=r"""A splitting field is the extension needed to contain all roots of a given polynomial.

\begin{definition}
Let \(f\in K[x]\) be a nonconstant polynomial over a field \(K\). A \emph{splitting field} of \(f\) over \(K\) is an extension \(L/K\) such that \(f\) factors into linear polynomials in \(L[x]\) and \(L\) is generated over \(K\) by its roots. Thus, if those roots are \(\alpha_1,\ldots,\alpha_m\), then
\[
L=K(\alpha_1,\ldots,\alpha_m).
\]
\end{definition}

Every nonconstant polynomial has a splitting field, unique up to an isomorphism that fixes \(K\). Its degree over \(K\) is finite. Repeated roots are allowed in this definition.

\begin{example}
The splitting field of \(x^2-2\) over \(\mathbb{Q}\) is \(\mathbb{Q}(\sqrt{2})\), since it contains both roots. The splitting field of \(x^3-2\) is \(\mathbb{Q}(\sqrt[3]{2},\zeta)\), where \(\zeta=e^{2\pi i/3}\). The smaller real field \(\mathbb{Q}(\sqrt[3]{2})\) misses the two nonreal roots.
\end{example}

\begin{remark}
The base field matters: \(x^2-2\) already splits over \(\mathbb{R}\), so its splitting field over \(\mathbb{R}\) is \(\mathbb{R}\) itself.
\end{remark}
""",
    ),
    dict(
        title="perfect field", slug="perfect-field", canonical="PerfectField",
        classifications=["12F10", "12F15"], synonyms=["perfect fields"], definitions=["imperfect field"],
        related=["example-of-nonperfect-field"],
        origins=[("example-of-nonperfect-field", "perfect field")],
        escapes=["field", "root", "characteristic", "degree", "irreducible", "polynomial", "equivalent", "power", "injective", "surjective"],
        reference=("K. Conrad", "Perfect fields",
                   "https://kconrad.math.uconn.edu/blurbs/galoistheory/perfect.pdf"),
        body=r"""Perfect fields are those over which irreducible polynomials have no repeated roots.

\begin{definition}
A field \(K\) is \emph{perfect} if every irreducible polynomial in \(K[x]\) has distinct roots in a splitting field. A field that fails this condition is an \emph{imperfect field}.
\end{definition}

Every field of characteristic zero is perfect. In characteristic \(p>0\), perfection is equivalent to surjectivity of the Frobenius map
\[
K\longrightarrow K,\qquad a\longmapsto a^p.
\]
Equivalently, every element of \(K\) is a \(p\)-th power in \(K\).

\begin{example}
Finite fields are perfect: their Frobenius map is injective, and an injective self-map of a finite set is surjective. The rational function field \(\mathbb{F}_p(t)\) is imperfect, since \(t\) is not a \(p\)-th power there. The polynomial \(x^p-t\) is irreducible over this field but has a repeated root in its splitting field.
\end{example}

\begin{remark}
The definition concerns irreducible polynomials. Even over a perfect field, the polynomial \((x-1)^2\) has a repeated root.
\end{remark}
""",
    ),
    dict(
        title="algebraically closed field", slug="algebraically-closed-field", canonical="AlgebraicallyClosedField",
        classifications=["12F05"], synonyms=["algebraically closed fields"], definitions=["algebraic closure"],
        related=["example-of-strongly-minimal", "nonsingular-variety"],
        origins=[("nonsingular-variety", "algebraically closed field"), ("example-of-strongly-minimal", "algebraically closed field")],
        escapes=["field", "closed", "root", "degree", "polynomial", "equivalent", "closure", "base"],
        reference=("The Stacks Project", "Algebraic closure, Section 9.10",
                   "https://stacks.math.columbia.edu/tag/09GP"),
        body=r"""An algebraically closed field already contains solutions to all nonconstant polynomial equations in one variable over itself.

\begin{definition}
A field \(K\) is \emph{algebraically closed} if every nonconstant polynomial \(f\in K[x]\) has a root in \(K\).
\end{definition}

Equivalently, every such polynomial factors completely into linear factors over \(K\). Successively dividing by \(x-\alpha\), where \(\alpha\) is a root, proves this equivalence. Another equivalent condition is that \(K\) has no proper algebraic field extension.

\begin{example}
The complex numbers form an algebraically closed field, by the fundamental theorem of algebra. The real numbers do not: \(x^2+1\) has no real root.
\end{example}

\begin{definition}
An \emph{algebraic closure} of \(K\) is an algebraic field extension \(\overline{K}/K\) whose larger field is algebraically closed.
\end{definition}

\begin{remark}
An algebraic closure exists for every field and is unique up to isomorphism fixing the base field, but that isomorphism need not be unique. In particular, \(\mathbb{C}\) is an algebraic closure of \(\mathbb{R}\), but not of \(\mathbb{Q}\), because \(\mathbb{C}/\mathbb{Q}\) is not algebraic.
\end{remark}
""",
    ),
]


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.current = [dict(attrs), ""]

    def handle_data(self, data):
        if self.current is not None:
            self.current[1] += data

    def handle_endtag(self, tag):
        if tag == "a" and self.current is not None:
            self.links.append(self.current)
            self.current = None


def source(entry):
    author, title, url = entry["reference"]
    # The legacy prose renderer interprets literal tildes as LaTeX spaces.
    url = url.replace("~", r"\%7E")
    exclusions = "\n".join(r"\PMlinkescapeword{" + word + "}" for word in entry["escapes"])
    return (exclusions + "\n\n" + entry["body"].strip() + "\n\n"
            + r"\begin{thebibliography}{9}" + "\n"
            + r"\bibitem{reference} " + author + ", "
            + r"\PMlinkexternal{" + title + "}{" + url + "}.\n"
            + r"\end{thebibliography}" + "\n")


def types(entry):
    names = re.findall(r"\\begin\{(definition|example|remark|proof|proposition)\}", entry["body"])
    return sorted({"Result" if name == "proposition" else name.capitalize() for name in names})


def verify(connection):
    """Check metadata, formal sections and incoming automatic links."""
    report = []
    for entry in ENTRIES:
        detail = fetch_public_math_concept_detail(connection.cursor(), entry["slug"])
        if not detail or detail["owner"] != "CWoo":
            raise ValueError(f"Missing entry or wrong owner: {entry['slug']}")
        assert set(detail["types"]) == set(types(entry)), entry["slug"]
        assert {item["code"] for item in detail["classifications"]} == set(entry["classifications"])
        assert set(detail["synonyms"]) == set(entry["synonyms"])
        assert set(detail["definitions"]) == set(entry["definitions"])
        assert 'math-env-definition' in detail["display_tex"]
        assert 'math-env-example' in detail["display_tex"]
        assert r"\PMlink" not in detail["display_tex"]
        related = connection.execute(
            "SELECT related_concept_id FROM math_related_concepts WHERE concept_id = ?",
            (detail["id"],),
        ).fetchall()
        assert len(related) == len(entry["related"]) and all(row[0] for row in related)
        for origin, phrase in entry["origins"]:
            parent = fetch_public_math_concept_detail(connection.cursor(), origin)
            parser = Links()
            parser.feed(parent["display_tex"])
            matching = [attrs for attrs, label in parser.links
                        if label.casefold() == phrase.casefold()
                        and attrs.get("href") == "concept.html?slug=" + entry["slug"]
                        and attrs.get("class") == "math-autolink"]
            if not matching:
                raise ValueError(f"No automatic link from {origin} to {entry['slug']}")
        report.append((detail["id"], entry["slug"], len(entry["origins"])))
    return report


def apply(db_path):
    if not db_path.is_file():
        raise FileNotFoundError(db_path)
    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        cursor = connection.cursor()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        created = 0
        for entry in ENTRIES:
            existing = cursor.execute("SELECT id FROM math_concepts WHERE slug = ?", (entry["slug"],)).fetchone()
            if existing:
                continue
            for term in [entry["title"], *entry["synonyms"], *entry["definitions"]]:
                collision = cursor.execute("""
                    SELECT title FROM math_concepts WHERE lower(title) = lower(?)
                    UNION SELECT synonym_text FROM math_synonyms WHERE lower(synonym_text) = lower(?)
                    UNION SELECT defined_term FROM math_definitions WHERE lower(defined_term) = lower(?)
                """, (term, term, term)).fetchone()
                if collision:
                    raise ValueError(f"Existing catalog term needs review: {term}")
            for code in entry["classifications"]:
                if not cursor.execute("SELECT id FROM math_classifications WHERE code = ?", (code,)).fetchone():
                    raise ValueError(f"Unknown MSC code: {code}")
            related_names = []
            for slug in entry["related"]:
                row = cursor.execute("SELECT canonical_name FROM math_concepts WHERE slug = ?", (slug,)).fetchone()
                if row is None:
                    raise ValueError(f"Missing related entry: {slug}")
                related_names.append(row[0])
            create_math_concept(
                cursor=cursor, canonical_name=entry["canonical"], slug=entry["slug"],
                title=entry["title"], timestamp=timestamp, owner="CWoo",
                cleaned_tex=source(entry), is_cleaned_flag=1,
                classifications=entry["classifications"], types=types(entry),
                synonyms=entry["synonyms"], definitions=entry["definitions"],
                related_concepts=related_names,
            )
            created += 1
        report = verify(connection)
    return created, report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=SRC.parent / "portfolio.db")
    args = parser.parse_args()
    count, result = apply(args.db)
    print(f"Created {count} concepts; verified all eight:")
    for concept_id, slug, origins in result:
        print(f"  {concept_id}: {slug} ({origins} incoming-link checks)")
