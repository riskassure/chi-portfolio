"""Add a checked proof chain for the semisimple-module characterization.

Existing semisimple-module defines a direct sum of simples; socle states the
sum-of-simples criterion without proof. Neither supplies the complement theorem.
The new proof does not assume a submodule is a sum of the original summands
(the diagonal in K^2 disproves that shortcut). Zorn's lemma is a foundational
input, with its existing equivalence proof linked rather than duplicated.
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
from services.math.public_search_service import search_public_math_library
from add_eight_algebra_concepts import Links, source
from add_sylow_theorems import document_types
from add_twenty_concepts_20260922 import ESCAPES

REFERENCE = ("N. Elkies", "Characterizations of semisimple modules (with reference to Lang, Algebra, XVII.2)",
             "https://people.math.harvard.edu/~elkies/M250.01/semisimple.html")
ZORN = "equivalence-of-kuratowskis-lemma-and-zorns-lemma"


def entry(title, slug, canonical, definitions, related, body, synonyms=()):
    return dict(title=title, slug=slug, canonical=canonical, definitions=definitions,
                related=related, body=body, synonyms=list(synonyms), classifications=["16D10", "16D60"],
                reference=REFERENCE, escapes=list(ESCAPES) + ["simple", "semisimple", "complement",
                "complementary", "projection", "support", "zero", "proper", "linear", "normal",
                "independent", "independence", "maximal element", "upper bound", "bound",
                "composition", "restriction", "representative", "representatives", "well-defined",
                "injective", "surjective", "relation"])


ENTRIES = [
entry("quotient module", "quotient-module", "QuotientModule", ["canonical quotient homomorphism"],
      ["module", "simple-module", "module-homomorphism"], r"""
Throughout, modules are unital left modules over an associative unital ring \(R\).
\begin{definition}
For a submodule \(N\subseteq M\), the \emph{quotient module} \(M/N\) consists of additive cosets \(m+N\), with
\[
(m+N)+(m'+N)=(m+m')+N,\qquad r(m+N)=rm+N.
\]
Its \emph{canonical quotient homomorphism} is \(q:M\to M/N\), \(q(m)=m+N\).
\end{definition}
\begin{proposition}
These operations are well-defined and make \(M/N\) a module. The map \(q\) is surjective and \(q(m)=0\) exactly when \(m\in N\).
\end{proposition}
\begin{proof}
Replacing \(m,m'\) by \(m+n,m'+n'\), with \(n,n'\in N\), changes their sum by \(n+n'\in N\) and a scalar multiple by \(rn\in N\). Hence the resulting cosets are unchanged. The abelian group and scalar laws descend from those of \(M\). Every coset has a representative, and \(m+N=N\) is equivalent to \(m\in N\).
\end{proof}
\begin{example}
As a \(\mathbb Z\)-module, \(\mathbb Z/4\mathbb Z\) is the quotient by the submodule \(4\mathbb Z\).
\end{example}
""", ["factor module"]),
entry("Schur's lemma for modules", "schurs-lemma-for-modules", "SchursLemmaForModules",
      ["module isomorphism"], ["simple-module", "module-homomorphism", "endomorphism-ring"], r"""
All modules are unital left modules over the same associative unital ring \(R\).
\begin{definition}
A \emph{module isomorphism} is a bijective module homomorphism. Its inverse is also a homomorphism: apply the original map to addition and scalar multiplication of preimages and use injectivity.
\end{definition}
\begin{lemma}
If \(S\) is a simple module and \(f:S\to M\) is a module homomorphism, then its image is either zero or simple. In the nonzero case, \(f\) is an isomorphism onto its image.
\end{lemma}
\begin{proof}
The set \(K=\{s:f(s)=0\}\) is a submodule by additivity and compatibility with scalar multiplication. Simplicity gives \(K=0\) or \(K=S\). A nonzero map has \(K=0\), hence is injective. If \(U\) is a nonzero submodule of \(f(S)\), its preimage is a nonzero submodule of \(S\), so equals \(S\). Therefore \(U=f(S)\), proving simplicity. Surjectivity onto the image is automatic.
\end{proof}
\begin{theorem}
Every nonzero homomorphism between simple modules is an isomorphism.
\end{theorem}
\begin{proof}
The lemma gives injectivity. The nonzero image is a submodule of the simple target, hence is the entire target.
\end{proof}
\begin{corollary}
The endomorphism ring of a simple module is a division ring.
\end{corollary}
\begin{proof}
Its identity is nonzero because a simple module is nonzero. Each nonzero endomorphism is an isomorphism by the theorem, so its inverse is an endomorphism and a multiplicative inverse under composition.
\end{proof}
\begin{example}
For a field \(K\), every \(K\)-linear map \(K\to K\) is multiplication by its value at \(1\). A nonzero value gives an invertible map, illustrating the theorem.
\end{example}
""", ["Schur's lemma", "Schur lemma", "homomorphic images of simple modules"]),
entry("maximal submodules of cyclic modules", "maximal-submodules-of-cyclic-modules", "MaximalSubmodulesOfCyclicModules",
      ["cyclic module", "maximal submodule"], ["module", "simple-module", ZORN], r"""
We work with unital left modules over an associative unital ring, assuming the axiom of choice.
\begin{definition}
A \emph{cyclic module} is a module \(C=Rc\) generated by one element. A \emph{maximal submodule} of \(C\) is a proper submodule \(L\) for which no submodule lies strictly between \(L\) and \(C\).
\end{definition}
\begin{proposition}
Every nonzero cyclic module has a maximal submodule.
\end{proposition}
\begin{proof}
Write \(C=Rc\ne0\). A submodule is proper exactly when it does not contain \(c\). Order the proper submodules by inclusion; the zero submodule belongs to this set. For a nonempty chain, the union is a submodule: any two of its elements lie together in one member of the chain, and scalar multiples remain in that member. The union cannot contain \(c\), since then a member would contain \(c\). Thus the union is a proper upper bound. The empty chain has upper bound \(0\). By \PMlinkname{Zorn's lemma}{EquivalenceOfKuratowskisLemmaAndZornsLemma}, which says that a nonempty partially ordered set with upper bounds for all chains has a maximal element, a maximal proper submodule exists.
\end{proof}
\begin{example}
The submodule \(2\mathbb Z\) is maximal in the cyclic \(\mathbb Z\)-module \(\mathbb Z\): any subgroup containing it and an odd integer contains \(1\), hence all integers.
\end{example}
\begin{remark}
The cyclic hypothesis matters to this proof: it ensures that a union containing the generator is already the whole module at one stage. No claim about arbitrary nonzero modules is needed here.
\end{remark}
"""),
entry("complements in sums of simple submodules", "complements-in-sums-of-simple-submodules", "ComplementsInSumsOfSimpleSubmodules",
      ["sum of submodules", "independent family of submodules"], ["simple-module", "semisimple-module", "direct-summand", ZORN], r"""
Let \(M\) be a unital left module over an associative unital ring. We allow arbitrary index sets and assume the axiom of choice.
\begin{definition}
The \emph{sum of submodules} \(\sum_{i\in I}S_i\) is the submodule of all finite sums of elements from the \(S_i\). A family of submodules is an \emph{independent family of submodules} if a finite relation \(s_{i_1}+\cdots+s_{i_k}=0\), at distinct indices with \(s_{i_j}\in S_{i_j}\), forces every summand to be zero. This is equivalent to uniqueness of finite expressions, so the sum of such a family is an internal direct sum.
\end{definition}
\begin{lemma}
If \(M=\sum_{i\in I}S_i\) with every \(S_i\) simple, then for every submodule \(N\subseteq M\) there is a subset \(J\subseteq I\) such that
\[
M=N\oplus T,\qquad T=\bigoplus_{j\in J}S_j.
\]
\end{lemma}
\begin{proof}
Consider subsets \(J\subseteq I\) whose submodules form an independent family and whose sum \(T_J\) satisfies \(N\cap T_J=0\). The empty subset qualifies. Order these subsets by inclusion. The union of a chain qualifies too: a finite relation, or a particular element of the intersection with \(N\), involves finitely many indices, all in one member of the chain. Independence and the zero-intersection condition follow there. Thus \PMlinkname{Zorn's lemma}{EquivalenceOfKuratowskisLemmaAndZornsLemma} gives a maximal such \(J\).

Put \(T=T_J\). If \(N+T\ne M\), some \(S_i\) is not contained in \(N+T\), since the \(S_i\) sum to \(M\). Simplicity forces \(S_i\cap(N+T)=0\). In particular \(S_i\cap T=0\), so adding \(S_i\) preserves independence. If \(n=t+s\in N\) with \(t\in T,s\in S_i\), then \(s=n-t\in S_i\cap(N+T)=0\); next \(n=t\in N\cap T=0\). Hence adding this index also preserves the zero-intersection condition, contrary to maximality. Consequently \(M=N+T\), and the zero intersection makes the sum direct.
\end{proof}
\begin{example}
In \(K^2\), take the two coordinate lines as \(S_1,S_2\) and the diagonal as \(N\). Either coordinate line complements the diagonal. The diagonal itself is not a sum of a subset of the two coordinate lines.
\end{example}
"""),
entry("characterization of semisimple modules", "characterization-of-semisimple-modules", "CharacterizationOfSemisimpleModules",
      [], ["semisimple-module", "simple-module", "direct-summand", "socle", "complements-in-sums-of-simple-submodules", "maximal-submodules-of-cyclic-modules"], r"""
All modules are unital left modules over an associative unital ring \(R\). Arbitrary direct sums are allowed; we assume the axiom of choice. This entry proves the complement criterion, rather than treating the existing direct-sum definition as a theorem.
\begin{theorem}
For a module \(M\), the following conditions are equivalent:
\begin{enumerate}
\item \(M\) is a semisimple module: an internal direct sum of simple submodules.
\item \(M\) is a sum of simple submodules, without an independence requirement.
\item Every submodule of \(M\) is a direct summand of \(M\).
\end{enumerate}
The zero module satisfies all three conditions, using the empty sum.
\end{theorem}
\begin{proof}
Condition (1) immediately gives (2). The \PMlinkname{complement lemma}{ComplementsInSumsOfSimpleSubmodules} gives (2) implies (3), and, with \(N=0\), also gives (2) implies (1).

Assume (3). First we show that every nonzero submodule \(U\) of \(M\) contains a simple submodule. Choose \(0\ne u\in U\) and put \(C=Ru\). The \PMlinkname{cyclic-module maximal-submodule proposition}{MaximalSubmodulesOfCyclicModules} supplies a maximal proper submodule \(L\subset C\). By (3), write \(M=L\oplus D\). Because \(L\subseteq C\), decomposing each element of \(C\) gives
\[
C=L\oplus(C\cap D).
\]
Indeed, if \(c=l+d\), then \(d=c-l\in C\cap D\). Let \(V=C\cap D\); it is nonzero because \(L\ne C\). If \(0\ne W\subseteq V\) is a submodule, then \(L+W\) properly contains \(L\), so maximality gives \(L+W=C\). Uniqueness in \(C=L\oplus V\) then gives \(W=V\). Thus \(V\) is simple and is contained in \(U\).

Now let \(S\) be the sum of all simple submodules of \(M\), its socle. By (3) there is a complement \(D\) with \(M=S\oplus D\). If \(D\ne0\), the preceding argument produces a simple submodule of \(D\). It lies in \(S\) by definition, contradicting \(S\cap D=0\). Hence \(S=M\), proving (2) and completing the equivalence.
\end{proof}
\begin{example}
The submodule \(N=\{0,2\}\) of \(\mathbb Z/4\mathbb Z\) has no complement: a submodule containing an odd residue is the whole module, and every other submodule is contained in \(N\). Thus the quotient group, as a \(\mathbb Z\)-module, is not semisimple.
\end{example}
\begin{remark}
The proof includes infinite modules. It never assumes that a submodule is assembled from a subset of an already chosen set of simple summands; the diagonal example in the complement lemma shows why that shortcut fails.
\end{remark}
""", ["semisimple module characterization theorem", "direct summand criterion for semisimplicity"]),
entry("submodules and quotients of semisimple modules", "submodules-and-quotients-of-semisimple-modules", "SubmodulesAndQuotientsOfSemisimpleModules",
      [], ["characterization-of-semisimple-modules", "schurs-lemma-for-modules", "quotient-module", "semisimple-module"], r"""
Modules are unital left modules over an associative unital ring, with the same choice convention as the characterization theorem.
\begin{theorem}
Every submodule and every quotient module of a semisimple module is semisimple.
\end{theorem}
\begin{proof}
Write \(M=\bigoplus_{i\in I}S_i\) with simple summands, and let \(N\subseteq M\). By the \PMlinkname{characterization theorem}{CharacterizationOfSemisimpleModules}, choose \(T\) with \(M=N\oplus T\). The projection \(p:M\to N\), \(p(n+t)=n\), is a module homomorphism, since addition and scalar multiplication preserve the two summands. As \(p\) is onto,
\[
N=\sum_{i\in I}p(S_i).
\]
Each nonzero image is simple by the image lemma in \PMlinkname{Schur's lemma for modules}{SchursLemmaForModules}. Discarding zero images, the characterization theorem makes \(N\) semisimple.

For the canonical quotient homomorphism \(q:M\to M/N\), similarly \(M/N=\sum_{i\in I}q(S_i)\). Again all nonzero images are simple, so the characterization theorem makes \(M/N\) semisimple. These image sums need not be direct before applying that theorem.
\end{proof}
\begin{example}
For \(M=K^2\) and its diagonal submodule \(N\), both \(N\) and \(M/N\) are one-dimensional over \(K\), hence simple. The quotient images of the two coordinate lines coincide, illustrating why an image of a direct-sum decomposition need not itself be direct.
\end{example}
"""),
]

ENTRIES[0]["reference"] = ("R. Sharifi", "Abstract Algebra, Chapter 5 (modules)",
                          "https://www.math.ucla.edu/~sharifi/notes/algebra-ch05.html")
REVIEWED_TARGETS = {e["slug"] for e in ENTRIES} | set("""group associative
homomorphism-between-algebraic-systems module simple-module ring division-ring
endomorphism-ring field linear-transformation module-homomorphism integer
lagranges-theorem-for-finite-groups intersection direct-summand semisimple-module
socle equivalence-of-kuratowskis-lemma-and-zorns-lemma""".split())


def targets(html):
    p = Links()
    p.feed(html)
    return {a["href"].split("slug=", 1)[1] for a, _ in p.links
            if a.get("href", "").startswith("concept.html?slug=")}


def verify(c):
    for e in ENTRIES:
        d = fetch_public_math_concept_detail(c.cursor(), e["slug"])
        assert d and d["owner"] == "CWoo" and d["cleaned_tex"] == source(e)
        for key in ["synonyms", "definitions"]:
            assert set(d[key]) == set(e[key]), (e["slug"], key)
        assert set(d["types"]) == set(document_types(e))
        assert {r["code"] for r in d["classifications"]} == set(e["classifications"])
        html = d["display_tex"]
        assert r"\PMlink" not in html
        assert html.count('class="math-env math-env-proof"') == e["body"].count(r"\begin{proof}")
        pattern = r"\\\(.*?\\\)|\\\[.*?\\\]"
        assert re.findall(pattern, d["cleaned_tex"], re.S) == re.findall(pattern, html, re.S)
        assert e["slug"] not in targets(html)
        assert targets(html) <= REVIEWED_TARGETS, (e["slug"], targets(html) - REVIEWED_TARGETS)
        for canonical in re.findall(r"\\PMlinkname\{[^{}]+\}\{([^{}]+)\}", e["body"]):
            row = c.execute("SELECT slug FROM math_concepts WHERE canonical_name=?", (canonical,)).fetchone()
            assert row and row[0] in targets(html), (e["slug"], canonical)
        rows = c.execute("SELECT related_concept_id FROM math_related_concepts WHERE concept_id=?", (d["id"],)).fetchall()
        assert len(rows) == len(e["related"]) and all(r[0] for r in rows)
        assert any(x.get("slug") == e["slug"] for x in search_public_math_library(c.cursor(), e["title"])["data"])
        print("Verified", d["id"], e["slug"])
    assert "quotient-module" in targets(fetch_public_math_concept_detail(c.cursor(), "length-of-a-module")["display_tex"])
    for origin in ["semisimple-module", "socle"]:
        assert c.execute("""SELECT 1 FROM math_related_concepts rc
            JOIN math_concepts c ON c.id=rc.concept_id
            WHERE c.slug=? AND rc.related_canonical_name='CharacterizationOfSemisimpleModules'
            AND rc.related_concept_id IS NOT NULL""", (origin,)).fetchone()
    assert c.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert not c.execute("PRAGMA foreign_key_check").fetchall()


def apply(path):
    if not path.is_file():
        raise FileNotFoundError(path)
    with sqlite3.connect(path) as c:
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA foreign_keys=ON")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for e in ENTRIES:
            if c.execute("SELECT id FROM math_concepts WHERE slug=?", (e["slug"],)).fetchone():
                continue
            for term in [e["title"], *e["synonyms"], *e["definitions"]]:
                collision = c.execute("""SELECT title FROM math_concepts WHERE lower(title)=lower(?)
                    UNION SELECT synonym_text FROM math_synonyms WHERE lower(synonym_text)=lower(?)
                    UNION SELECT defined_term FROM math_definitions WHERE lower(defined_term)=lower(?)""", (term,term,term)).fetchone()
                assert not collision, (e["slug"],term)
            related = [c.execute("SELECT canonical_name FROM math_concepts WHERE slug=?", (s,)).fetchone()[0] for s in e["related"]]
            create_math_concept(c.cursor(), e["canonical"], e["slug"], e["title"], now, "CWoo", source(e), 1,
                e["classifications"], document_types(e), e["synonyms"], e["definitions"], related)
        # Make the theorem discoverable from its existing definition and the
        # socle entry, whose previously unproved criterion it justifies.
        theorem_id = c.execute("SELECT id FROM math_concepts WHERE slug='characterization-of-semisimple-modules'").fetchone()[0]
        for origin in ["semisimple-module", "socle"]:
            origin_id = c.execute("SELECT id FROM math_concepts WHERE slug=?", (origin,)).fetchone()[0]
            if not c.execute("SELECT 1 FROM math_related_concepts WHERE concept_id=? AND related_canonical_name=?",
                             (origin_id, "CharacterizationOfSemisimpleModules")).fetchone():
                c.execute("INSERT INTO math_related_concepts(concept_id,related_canonical_name,related_concept_id) VALUES(?,?,?)",
                          (origin_id, "CharacterizationOfSemisimpleModules", theorem_id))
        verify(c)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=SRC.parent / "portfolio.db")
    apply(parser.parse_args().db)
