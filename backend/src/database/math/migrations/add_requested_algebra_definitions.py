"""Fill seven algebra definition gaps and index three existing definitions."""
import argparse
from datetime import datetime
from pathlib import Path
import re
import sqlite3
import sys

SRC = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(SRC))
from services.math.concept_create_service import create_math_concept
from services.math.concept_render_service import render_tex_reusing_existing_diagrams
from services.math.public_concept_detail_service import fetch_public_math_concept_detail
from services.math.public_search_service import search_public_math_library
from add_eight_algebra_concepts import Links, source
from add_sylow_theorems import document_types

FIELD_REF = ("The Stacks Project", "Fields: review of algebraic extensions", "https://stacks.math.columbia.edu/tag/037H")
MODULE_REF = ("R. Sharifi", "Abstract Algebra, Chapters 5 and 13", "https://www.math.ucla.edu/~sharifi/notes/algebra-ch13.html")
ESCAPES = ["identity", "inverse", "product", "normal", "simple", "semisimple", "separable", "characteristic",
           "root", "degree", "polynomial", "constant", "term", "order", "index", "closed", "closure", "chain",
           "left", "right", "basis", "dimension", "quotient", "general", "condition", "fixed", "power", "finite",
           "irreducible", "minimal", "transcendental", "base", "bijective", "theory", "context", "ideal", "side",
           "unit", "closed under", "instance", "line"]

ENTRIES = [
 dict(title="separable field extension", slug="separable-field-extension", canonical="SeparableFieldExtension",
      synonyms=["separable extension", "separability in field theory"], classifications=["12F10", "12F15"],
      definitions=["separable polynomial", "separable algebraic element", "minimal polynomial of an algebraic element", "irreducible polynomial"],
      related=["field-extension", "perfect-field", "example-of-nonperfect-field", "factor-theorem-for-polynomials-over-a-field"], reference=FIELD_REF,
      body=r"""Separability distinguishes algebraic elements whose defining irreducible polynomials have no repeated roots.
\begin{definition}
A nonconstant polynomial over a field \(K\) is an \emph{irreducible polynomial} if it cannot be expressed as a product of two polynomials of positive degree. For an algebraic element \(\alpha\) over \(K\), the \emph{minimal polynomial of an algebraic element} is the monic polynomial \(m_\alpha\in K[x]\) of least positive degree with \(m_\alpha(\alpha)=0\). Here monic means highest coefficient equal to one.
\end{definition}
\begin{proposition}
The minimal polynomial exists, is unique, and is irreducible.
\end{proposition}
\begin{proof}
Choose a nonzero polynomial of least degree vanishing at \(\alpha\), and divide by its highest coefficient. A nonzero constant cannot vanish. Two monic polynomials of that same least degree have a difference of smaller degree vanishing at \(\alpha\), so the difference is zero. If the chosen polynomial factored into two positive-degree polynomials, evaluation in the extension field would force one of these smaller-degree factors to vanish, contradicting minimality.
\end{proof}
\begin{definition}
A nonzero polynomial is a \emph{separable polynomial} if its roots in a splitting field are distinct. An algebraic element is a \emph{separable algebraic element} over \(K\) if its minimal polynomial is separable. An algebraic field extension \(L/K\) is a \emph{separable field extension} if every element of \(L\) is separable over \(K\).
\end{definition}
\begin{example}
Every element of \(\mathbb{Q}(\sqrt{2})\) has the form \(u+v\sqrt{2}\), with \(u,v\in\mathbb{Q}\). If \(v=0\), its minimal polynomial is linear. Otherwise it has minimal polynomial \((x-u)^2-2v^2\), whose two roots \(u\pm v\sqrt{2}\) are distinct; a linear polynomial cannot vanish there because \(\sqrt{2}\) is irrational. Thus this extension is separable. See the existing example of a nonperfect field for an inseparable contrast.
\end{example}
\begin{remark}
The definition here concerns algebraic extensions. Separability of general transcendental extensions requires a broader definition. It is unrelated to separability of metric or Hilbert spaces.
\end{remark}
"""),
 dict(title="normal field extension", slug="normal-field-extension", canonical="NormalFieldExtension",
      synonyms=["normal extension", "normality in field theory"], classifications=["12F05", "12F10"],
      definitions=["splitting of a polynomial"], related=["field-extension", "separable-field-extension", "splitting-field-of-a-polynomial"], reference=FIELD_REF,
      body=r"""Normality requires an algebraic extension to contain all conjugate roots once it contains one.
\begin{definition}
The \emph{splitting of a polynomial} \(f\ne0\) over \(L\) means a factorization \(f(x)=c\prod_{i=1}^n(x-a_i)\) with \(c\in L\setminus\{0\}\) and all \(a_i\in L\); repeated roots are allowed. An algebraic extension \(L/K\) is a \emph{normal field extension} if every irreducible polynomial in \(K[x]\) having a root in \(L\) splits over \(L\).
\end{definition}
\begin{example}
The extension \(\mathbb{Q}(\sqrt{2})/\mathbb{Q}\) is normal. Its map \(\sigma(u+v\sqrt{2})=u-v\sqrt{2}\) preserves sums and products by direct expansion. If a polynomial \(f\in\mathbb{Q}[x]\) vanishes at \(u+v\sqrt{2}\), applying \(\sigma\) shows it vanishes at \(u-v\sqrt{2}\) too. For \(v\ne0\), these distinct roots give the quadratic factor \((x-u)^2-2v^2\) by the factor theorem. If \(f\) is irreducible, it must be a scalar multiple of this quadratic. When \(v=0\), an irreducible polynomial having that rational root is linear. In either case it splits in the extension.
\end{example}
\begin{remark}
Normality does not require roots to be distinct; that is the role of separability. The requirement that \(L/K\) be algebraic is part of this definition. A normal field extension is different from a normal subgroup or a normal ring.
\end{remark}
"""),
 dict(title="Galois group", slug="galois-group", canonical="GaloisGroup",
      synonyms=["Galois groups"], classifications=["12F10"],
      definitions=["Galois extension", "field automorphism over a base field"],
      related=["group", "field-extension", "separable-field-extension", "normal-field-extension", "quadratic-extension"],
      reference=("The Stacks Project", "Galois theory", "https://stacks.math.columbia.edu/tag/09DU"),
      body=r"""A Galois group describes symmetries of an extension that leave its base field unchanged.
\begin{definition}
A \emph{field automorphism over a base field} \(K\) of \(L/K\) is a bijection \(\sigma:L\to L\) preserving addition, multiplication, and one, with \(\sigma(c)=c\) for every \(c\in K\). Write \(\operatorname{Aut}_K(L)\) for these maps. A \emph{Galois extension} is an algebraic extension that is both \PMlinkname{normal}{NormalFieldExtension} and \PMlinkname{separable}{SeparableFieldExtension}. Its \emph{Galois group} is \(\operatorname{Gal}(L/K)=\operatorname{Aut}_K(L)\), with composition as operation.
\end{definition}
\begin{proposition}
For any field extension, \(\operatorname{Aut}_K(L)\) is a group.
\end{proposition}
\begin{proof}
Composition preserves field operations and fixes \(K\); it is associative as composition of functions. The identity map qualifies. The inverse of a bijective operation-preserving map preserves the same operations: apply the original map to the required equality and use injectivity. Its inverse also fixes each element of \(K\). These give all group axioms.
\end{proof}
\begin{example}
The extension \(\mathbb{Q}(\sqrt{2})/\mathbb{Q}\) is normal and separable, as proved in the corresponding entries. An automorphism must send \(\sqrt{2}\) to a root of \(x^2-2\), hence to \(\sqrt{2}\) or \(-\sqrt{2}\). Both choices give maps \(u+v\sqrt{2}\mapsto u\pm v\sqrt{2}\) preserving operations, and the negative choice squares to the identity. Its Galois group therefore has exactly two elements.
\end{example}
\begin{remark}
Some authors use the term Galois group for \(\operatorname{Aut}_K(L)\) even without assuming the extension is Galois. Here that group is called the automorphism group in that generality. Normality and separability remain explicit hypotheses when invoking Galois theory.
\end{remark}
"""),
 dict(title="Artinian ring", slug="artinian-ring", canonical="ArtinianRing",
      synonyms=["Artin ring", "Artinian rings"], classifications=["16P20"],
      definitions=["left Artinian ring", "right Artinian ring", "left ideal", "right ideal"],
      related=["ring", "equivalent-defining-conditions-on-a-noetherian-ring", "semisimple-ring", "wedderburn-artin-theorem"],
      reference=("R. Sharifi", "Abstract Algebra, Chapter 5 (chain conditions)", "https://www.math.ucla.edu/~sharifi/notes/algebra-ch05.html"),
      body=r"""Artinian rings prohibit endlessly decreasing chains of one-sided ideals. Rings in this entry are associative and unital.
\begin{definition}
A \emph{left ideal} of \(R\) is an additive subgroup \(I\subseteq R\) such that \(ri\in I\) for every \(r\in R,i\in I\); a \emph{right ideal} instead requires \(ir\in I\). A \emph{left Artinian ring} is a ring in which every descending chain of left ideals \(I_1\supseteq I_2\supseteq\cdots\) stabilizes: some \(n\) satisfies \(I_j=I_n\) for all \(j\ge n\). A \emph{right Artinian ring} satisfies the corresponding condition for right ideals. Here \emph{Artinian ring} means both left and right Artinian. For commutative rings the two conditions coincide.
\end{definition}
\begin{example}
Every finite ring is Artinian: a strictly decreasing chain of subsets strictly decreases their finite cardinalities, so it must stop. Every field is Artinian, since an ideal containing \(a\ne0\) contains \(a^{-1}a=1\) and then every element, leaving only the ideals \(0\) and the whole field. The integers are not Artinian, as \(2\mathbb{Z}\supsetneq4\mathbb{Z}\supsetneq8\mathbb{Z}\supsetneq\cdots\).
\end{example}
\begin{remark}
Artinian uses descending chains; Noetherian uses ascending chains. In a noncommutative context, retain the side specified in a statement rather than silently replacing it by the two-sided convention.
\end{remark}
"""),
 dict(title="division algebra", slug="division-algebra", canonical="DivisionAlgebra",
      synonyms=["division algebras"], classifications=["16K40", "17A35"],
      definitions=["associative division algebra"],
      related=["algebra", "division-ring", "nonassociative-algebra", "octonion"],
      reference=("Encyclopedia of Mathematics", "Division algebra", "https://encyclopediaofmath.org/wiki/Division_algebra"),
      body=r"""Division algebras allow unique division on either side. The distinction between associative and nonassociative conventions matters here.
\begin{definition}
Let \(A\ne0\) be an algebra over a field \(K\). In the general, possibly nonassociative convention, \(A\) is a \emph{division algebra} if for every \(a\ne0\) and every \(b\in A\), each equation \(ax=b\) and \(ya=b\) has a unique solution in \(A\). Equivalently, multiplication on either side by a nonzero element is bijective. An \emph{associative division algebra} here is an associative unital \(K\)-algebra whose underlying ring is a division ring.
\end{definition}
\begin{proposition}
For associative unital algebras, these conventions agree.
\end{proposition}
\begin{proof}
Unique division supplies \(ax=1\) and \(ya=1\); associativity gives \(y=y(ax)=(ya)x=x\), a two-sided inverse. Conversely, in a division ring the unique solutions are \(x=a^{-1}b\) and \(y=ba^{-1}\), as multiplication by \(a^{-1}\) verifies.
\end{proof}
\begin{example}
Every field extension \(L/K\) is an associative division algebra over \(K\). The real quaternions are a noncommutative associative example, described in the division ring entry. The real octonions are a nonassociative example; see the octonion entry for their multiplication and norm.
\end{example}
\begin{remark}
In associative ring theory, authors often assume associativity and a unit whenever they say division algebra. For arbitrary nonassociative algebras, merely possessing two-sided inverses does not replace the unique-division requirement. Finite dimension over \(K\) is not assumed here.
\end{remark}
"""),
 dict(title="simple module", slug="simple-module", canonical="SimpleModule",
      synonyms=["irreducible module", "simple modules"], classifications=["16D60"],
      definitions=["submodule"], related=["module", "module-homomorphism", "division-ring"], reference=MODULE_REF,
      body=r"""A simple module is a nonzero module with no smaller nonzero submodule. Modules here are unital left modules over an associative unital ring \(R\).
\begin{definition}
A \emph{submodule} of \(M\) is an additive subgroup \(N\subseteq M\) closed under scalar multiplication: \(rn\in N\) for \(r\in R,n\in N\). A \emph{simple module}, also called an irreducible module, is a nonzero module whose only submodules are \(0\) and itself.
\end{definition}
\begin{proposition}
A nonzero module \(M\) is simple if and only if \(Rm=M\) for every nonzero \(m\in M\), where \(Rm=\{rm:r\in R\}\).
\end{proposition}
\begin{proof}
Distributivity and associativity show that \(Rm\) is a submodule, and \(m=1m\) belongs to it. Thus simplicity forces \(Rm=M\). Conversely, if a submodule contains \(m\ne0\), it contains \(Rm=M\).
\end{proof}
\begin{example}
A field \(K\), as a module over itself, is simple: if a submodule contains \(a\ne0\), then it contains \((b/a)a=b\) for every \(b\in K\). The \(\mathbb{Z}\)-module \(\mathbb{Z}\) is not simple, since \(2\mathbb{Z}\) is a proper nonzero submodule.
\end{example}
\begin{remark}
The zero module is excluded. Simplicity depends on the scalar ring: \(\mathbb{Q}\) is simple as a module over itself but has the proper nonzero submodule \(\mathbb{Z}\) when viewed as a \(\mathbb{Z}\)-module. Right simple modules are defined analogously.
\end{remark}
"""),
 dict(title="semisimple module", slug="semisimple-module", canonical="SemisimpleModule",
      synonyms=["completely reducible module", "semisimple modules"], classifications=["16D60"],
      definitions=["internal direct sum of submodules"],
      related=["module", "simple-module", "semisimple-ring"], reference=MODULE_REF,
      body=r"""Semisimple modules are assembled from simple submodules without overlap between their summands. Modules here are unital left modules over an associative unital ring.
\begin{definition}
A module \(M\) is an \emph{internal direct sum of submodules} \(M_i\), written \(M=\bigoplus_{i\in I}M_i\), if every element has a unique expression as a sum of elements \(m_i\in M_i\) with only finitely many nonzero \(m_i\). A \emph{semisimple module}, or completely reducible module, is an internal direct sum of \PMlinkname{simple submodules}{SimpleModule}. The empty direct sum is allowed, so the zero module is semisimple.
\end{definition}
\begin{example}
Over a field \(K\), the module \(K^n\) is the direct sum of its coordinate lines, each simple because a nonzero coordinate generates its line. More generally a vector-space basis expresses any vector space as a direct sum of one-dimensional subspaces, so vector spaces are semisimple modules over their field. The \(\mathbb{Z}\)-module \(\mathbb{Z}/4\mathbb{Z}\) is not semisimple: a submodule containing an odd residue is the whole module, and its only proper nonzero submodule is \(\{0,2\}\). Thus its only simple submodule is \(\{0,2\}\), which cannot sum to the whole module.
\end{example}
\begin{remark}
Semisimple does not mean simple or finite-dimensional. For instance, \(K^2\) is semisimple but not simple because either coordinate line is proper and nonzero. Distinguish a semisimple module from a semisimple ring; the latter is defined in its own entry.
\end{remark}
"""),
]
for e in ENTRIES:
    e["escapes"] = list(ESCAPES)

EXISTING = {
    "polyadic-semigroup": ["semigroup", "semigroups"],
    "identity-in-a-class": ["monoid", "monoids"],
    "equivalent-defining-conditions-on-a-noetherian-ring": ["Noetherian ring", "left Noetherian ring", "right Noetherian ring"],
}


def index_existing(c, timestamp):
    for slug, terms in EXISTING.items():
        row = c.execute("SELECT id,cleaned_tex FROM math_concepts WHERE slug=?", (slug,)).fetchone()
        text = row["cleaned_tex"]
        if slug == "polyadic-semigroup":
            text = text.replace("Recall that a semigroup is a non-empty set, together with an associative binary operation on it.",
                r"\begin{definition} A \emph{semigroup} is a nonempty set with an associative binary operation. \end{definition}")
        if slug == "identity-in-a-class":
            # Correct the existing monoid identity typo, preserving the entry.
            text = text.replace(r"$e\cdot x=e$", r"$e\cdot x=x$")
            marker = r"\emph{monoid}"
            if marker not in text:
                text += r"""
\begin{definition}
A \emph{monoid} is a nonempty set with an associative binary operation and an identity element \(e\) satisfying \(ex=xe=x\) for every element \(x\). Inverses are not required.
\end{definition}
"""
        if slug == "equivalent-defining-conditions-on-a-noetherian-ring" and r"\emph{Noetherian ring}" not in text:
            text += r"""
\begin{definition}
A \emph{left Noetherian ring} satisfies the ascending chain condition on left ideals: every chain \(I_1\subseteq I_2\subseteq\cdots\) is eventually constant. A \emph{right Noetherian ring} satisfies the corresponding condition on right ideals. Here a \emph{Noetherian ring} means a ring satisfying both conditions; for commutative rings they coincide. The equivalent finite-generation and maximality conditions are proved above.
\end{definition}
"""
        if text != row["cleaned_tex"]:
            rendered = render_tex_reusing_existing_diagrams(row["id"], text, c.cursor())
            c.execute("UPDATE math_concepts SET cleaned_tex=?,rendered_tex=?,updated_at=? WHERE id=?", (text,rendered,timestamp,row["id"]))
        for term in terms:
            if not c.execute("SELECT 1 FROM math_definitions WHERE concept_id=? AND lower(defined_term)=lower(?)", (row["id"],term)).fetchone():
                c.execute("INSERT INTO math_definitions(concept_id,defined_term) VALUES (?,?)", (row["id"],term))
        c.execute("INSERT OR IGNORE INTO math_concept_types(concept_id,type_id) SELECT ?,id FROM math_types WHERE type_name='Definition'", (row["id"],))


def connect_existing(c, timestamp):
    changes = {
        "operations-on-relations": [(r"\PMlinkname{monoid}{Monoid}", r"\PMlinkname{monoid}{IdentityInAClass}")],
        "semisimple-ring": [("All left $R$-modules are semisimple.", r"All left $R$-modules are \PMlinkname{semisimple}{SemisimpleModule}.")],
    }
    for slug, replacements in changes.items():
        row=c.execute("SELECT id,cleaned_tex FROM math_concepts WHERE slug=?",(slug,)).fetchone()
        text=row["cleaned_tex"]
        for old,new in replacements:
            text=text.replace(old,new)
        if text!=row["cleaned_tex"]:
            rendered=render_tex_reusing_existing_diagrams(row["id"],text,c.cursor())
            c.execute("UPDATE math_concepts SET cleaned_tex=?,rendered_tex=?,updated_at=? WHERE id=?",(text,rendered,timestamp,row["id"]))


def verify(c):
    allowed = {e["slug"] for e in ENTRIES} | {
        "factor-theorem-for-polynomials-over-a-field", "field", "field-extension", "splitting-field-of-a-polynomial",
        "normalizer-of-a-subgroup", "ring", "associative", "group", "homomorphism-between-algebraic-systems",
        "commutative", "integer", "lagranges-theorem-for-finite-groups", "algebra", "division-ring", "octonion", "module", "semisimple-ring"
    }
    for e in ENTRIES:
        d = fetch_public_math_concept_detail(c.cursor(),e["slug"])
        assert d and d["owner"] == "CWoo"
        for key in ["synonyms","definitions"]:
            assert set(d[key]) == set(e[key])
        assert set(d["types"]) == set(document_types(e))
        assert {r["code"] for r in d["classifications"]} == set(e["classifications"])
        h=d["display_tex"]
        assert "math-env-definition" in h and r"\PMlink" not in h
        assert h.count('class="math-env math-env-proof"') == e["body"].count(r"\begin{proof}")
        links=Links();links.feed(h)
        for attrs,label in links.links:
            href=attrs.get("href","")
            if href.startswith("concept.html?slug="):
                assert href.split("=",1)[1] in allowed,(e["slug"],label,href)
        maths=r"\\\(.*?\\\)|\\\[.*?\\\]"
        assert re.findall(maths,d["cleaned_tex"],re.S)==re.findall(maths,h,re.S)
        rows=c.execute("SELECT related_concept_id FROM math_related_concepts WHERE concept_id=?",(d["id"],)).fetchall()
        assert len(rows)==len(e["related"]) and all(r[0] for r in rows)
        print("Verified:",d["id"],e["slug"])
    for slug,terms in EXISTING.items():
        d=fetch_public_math_concept_detail(c.cursor(),slug)
        assert set(terms)<=set(d["definitions"])
        assert "Definition" in d["types"]
    searches = [(term,slug) for slug,terms in EXISTING.items() for term in terms]
    searches += [(e["title"],e["slug"]) for e in ENTRIES]
    for term,slug in searches:
        result=search_public_math_library(c.cursor(),term)
        assert any(r.get("slug")==slug for r in result["data"]),(term,slug)
    for origin,target in [("operations-on-relations","identity-in-a-class"),("semisimple-ring","semisimple-module"),
                          ("quadratic-extension","galois-group"),("wedderburn-artin-theorem","artinian-ring"),
                          ("octonion","division-algebra")]:
        links=Links();links.feed(fetch_public_math_concept_detail(c.cursor(),origin)["display_tex"])
        assert any(a.get("href")=="concept.html?slug="+target for a,label in links.links),(origin,target)
    links=Links();links.feed(fetch_public_math_concept_detail(c.cursor(),"examples-of-semigroups")["display_tex"])
    for term,target in [("semigroup","polyadic-semigroup"),("semigroups","polyadic-semigroup"),("monoid","identity-in-a-class")]:
        assert any(label.lower()==term and a.get("href")=="concept.html?slug="+target
                   and a.get("class")=="math-autolink" for a,label in links.links),term


def apply(path):
    if not path.is_file():
        raise FileNotFoundError(path)
    with sqlite3.connect(path) as c:
        c.row_factory=sqlite3.Row
        c.execute("PRAGMA foreign_keys=ON")
        now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        index_existing(c,now)
        for e in ENTRIES:
            if c.execute("SELECT id FROM math_concepts WHERE slug=?",(e["slug"],)).fetchone():
                continue
            for term in [e["title"],*e["synonyms"],*e["definitions"]]:
                assert not c.execute("""SELECT title FROM math_concepts WHERE lower(title)=lower(?)
                UNION SELECT synonym_text FROM math_synonyms WHERE lower(synonym_text)=lower(?)
                UNION SELECT defined_term FROM math_definitions WHERE lower(defined_term)=lower(?)""",(term,term,term)).fetchone(),term
            for code in e["classifications"]:
                assert c.execute("SELECT id FROM math_classifications WHERE code=?",(code,)).fetchone(),code
            related=[c.execute("SELECT canonical_name FROM math_concepts WHERE slug=?",(s,)).fetchone()[0] for s in e["related"]]
            create_math_concept(c.cursor(),e["canonical"],e["slug"],e["title"],now,"CWoo",source(e),1,e["classifications"],document_types(e),e["synonyms"],e["definitions"],related)
        connect_existing(c,now)
        verify(c)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db",type=Path,default=SRC.parent/"portfolio.db")
    apply(parser.parse_args().db)
