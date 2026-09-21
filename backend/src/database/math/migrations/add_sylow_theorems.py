"""Add a noncircular proof chain for Sylow's theorems, owned by CWoo.

Order: cosets/Lagrange -> orbit-stabilizer -> p-group fixed points;
normalizers + these results -> Sylow. The Sylow counting lemma also proves
existence of subgroups of every p-power order dividing the group order.
No use of Cauchy's theorem, the class equation, or Sylow in prerequisites.
Existing group-action notes and subgroup-lattice entries were reviewed: they
use these notions but do not supply these standalone theorems and proofs.
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

COMMON_ESCAPES = ["order", "index", "identity", "inverse", "product", "normal", "action",
                  "fixed", "prime", "power", "class", "partition", "injective", "surjective",
                  "restriction", "representative", "equivalent", "conjugate", "orbit", "stabilizer",
                  "closed under", "disjoint union", "fixed point", "formula", "point", "congruence",
                  "closure", "preserve", "chain", "congruent", "elementary", "translation", "closed", "union"]

ENTRIES = [
 dict(title="Lagrange's theorem for finite groups", slug="lagranges-theorem-for-finite-groups",
      canonical="LagrangesTheoremForFiniteGroups", classifications=["20A05"],
      synonyms=["Lagrange's theorem", "Lagrange theorem for groups"],
      definitions=["subgroup", "left coset", "right coset", "index of a subgroup", "order of a group"],
      related=["group", "equivalence-relation", "lattice-of-subgroups"],
      reference=("J. S. Milne", "Group Theory, Chapter 1 (cosets and Lagrange's theorem)", "https://www.jmilne.org/math/CourseNotes/GT.pdf"),
      body=r"""Cosets divide a finite group into equally sized pieces, forcing subgroup sizes to divide the group size.

\begin{definition}
A \emph{subgroup} \(H\) of a group \(G\), written \(H\le G\), is a subset containing the identity \(e\) and closed under multiplication and inverses. It is itself a group with the inherited operation, because associativity is inherited from \(G\). The \emph{order of a group} is its cardinality \(|G|\). For \(g\in G\), the \emph{left coset} \(gH\) is \(\{gh:h\in H\}\), and the \emph{right coset} \(Hg\) is \(\{hg:h\in H\}\). The \emph{index of a subgroup}, \([G:H]\), is the number of distinct left cosets. The notation \(G/H\) here denotes the set of left cosets, without asserting it is a group.
\end{definition}

\begin{lemma}
Left cosets of \(H\) are equal or disjoint, cover \(G\), and each has \(|H|\) elements. Moreover, \(gH=kH\) exactly when \(k^{-1}g\in H\).
\end{lemma}

\begin{proof}
If \(gh_1=kh_2\), then \(k^{-1}g=h_2h_1^{-1}\in H\), so \(gH=kH\): multiplication by an element of \(H\) permutes \(H\), with inverse multiplication by its inverse. Conversely, \(gH=kH\) implies \(g\in kH\), hence \(k^{-1}g\in H\). Thus intersecting cosets coincide. Every \(g\) lies in \(gH\). Finally, \(h\mapsto gh\) has inverse \(u\mapsto g^{-1}u\), so it is a bijection from \(H\) to \(gH\).
\end{proof}

\begin{theorem}
For a finite group \(G\) and \(H\le G\),
\[
|G|=[G:H]|H|.
\]
In particular, \(|H|\) divides \(|G|\).
\end{theorem}

\begin{proof}
The lemma expresses \(G\) as a disjoint union of \([G:H]\) sets, each containing \(|H|\) elements. Count their elements.
\end{proof}

\begin{corollary}
If \(K\le H\le G\) and \(G\) is finite, then \([G:K]=[G:H][H:K]\).
\end{corollary}

\begin{proof}
Substitute \([G:K]=|G|/|K|\), \([G:H]=|G|/|H|\), and \([H:K]=|H|/|K|\) from the theorem and multiply.
\end{proof}

\begin{example}
In the additive group of integers modulo six, \(H=\{0,3\}\) has cosets \(\{0,3\},\{1,4\},\{2,5\}\), so \(6=3\cdot2\).
\end{example}
"""),
 dict(title="orbit-stabilizer theorem", slug="orbit-stabilizer-theorem", canonical="OrbitStabilizerTheorem",
      classifications=["20B05"], synonyms=["orbit stabilizer theorem", "orbit-stabilizer formula"],
      definitions=["group action", "left group action", "orbit of a group action", "stabilizer subgroup", "fixed point of a group action"],
      related=["group", "lagranges-theorem-for-finite-groups", "group-actions-and-homomorphisms"],
      reference=("J. S. Milne", "Group Theory, Chapter 4 (group actions)", "https://www.jmilne.org/math/CourseNotes/GT.pdf"),
      body=r"""The elements sending a point to the same destination form a coset of its stabilizer.

\begin{definition}
A \emph{left group action} of \(G\) on a set \(X\) is a map \((g,x)\mapsto g\cdot x\) with \(e\cdot x=x\) and \((gh)\cdot x=g\cdot(h\cdot x)\). Here \emph{group action} means a left action. The \emph{orbit of a group action} through \(x\) is \(G\cdot x=\{g\cdot x:g\in G\}\). Its \emph{stabilizer subgroup} is \(G_x=\{g:g\cdot x=x\}\). A \emph{fixed point of a group action} is a point fixed by every element of \(G\).
\end{definition}

\begin{lemma}
The set \(G_x\) is a subgroup. Orbits are equal or disjoint and together cover \(X\).
\end{lemma}

\begin{proof}
The identity fixes \(x\); if \(g,h\) fix \(x\), so does \(gh\). Applying \(g^{-1}\) to \(g\cdot x=x\) shows that \(g^{-1}\) fixes \(x\). If \(y=g\cdot x\), then \(x=g^{-1}\cdot y\), and composing actions shows \(G\cdot y=G\cdot x\). Any common point therefore makes two orbits equal. Finally, \(x=e\cdot x\) belongs to its orbit.
\end{proof}

\begin{theorem}
The map
\[
G/G_x\longrightarrow G\cdot x,\qquad gG_x\longmapsto g\cdot x
\]
is a bijection. In particular, for finite \(G\),
\[
|G\cdot x|=[G:G_x]=\frac{|G|}{|G_x|}.
\]
\end{theorem}

\begin{proof}
By the coset criterion in \PMlinkname{Lagrange's theorem}{LagrangesTheoremForFiniteGroups}, \(gG_x=hG_x\) exactly when \(h^{-1}g\in G_x\). By the action axioms this is equivalent to \(g\cdot x=h\cdot x\). The proposed map is consequently well-defined and one-to-one. Every orbit point is \(g\cdot x\) for some \(g\), so it is onto. Lagrange's theorem gives the finite formula.
\end{proof}

\begin{example}
Let \(G\) act on itself by left multiplication. Only \(e\) fixes a given element, since \(gx=x\) implies \(g=e\). There is one orbit: \((yx^{-1})x=y\) for all \(x,y\in G\).
\end{example}
"""),
 dict(title="fixed-point congruence for finite p-group actions", slug="fixed-point-congruence-for-finite-p-group-actions",
      canonical="FixedPointCongruenceForFinitePGroupActions", classifications=["20D15", "20B05"],
      synonyms=["p-group fixed-point congruence", "fixed point congruence for p-groups"],
      definitions=["finite p-group", "p-subgroup"],
      related=["group", "lagranges-theorem-for-finite-groups", "orbit-stabilizer-theorem"],
      reference=("J. S. Milne", "Group Theory, Chapter 4 (actions of p-groups)", "https://www.jmilne.org/math/CourseNotes/GT.pdf"),
      body=r"""For a prime-power group acting on a finite set, every orbit that is not a singleton contributes a multiple of the prime.

\begin{definition}
Fix a prime number \(p\). A \emph{finite p-group} is a group \(P\) with \(|P|=p^b\) for an integer \(b\ge0\); thus the trivial group is allowed. A \emph{p-subgroup} of a finite group is a subgroup of prime-power order \(p^b\). For a group action of \(P\) on \(X\), write \(X^P=\{x:g\cdot x=x\text{ for every }g\in P\}\).
\end{definition}

\begin{theorem}
If a finite p-group \(P\) acts on a finite set \(X\), then
\[
|X|\equiv |X^P|\pmod p.
\]
In particular, if \(p\) does not divide \(|X|\), the action has a fixed point.
\end{theorem}

\begin{proof}
By \PMlinkname{orbit-stabilizer}{OrbitStabilizerTheorem}, each orbit has size \(|P|/|P_x|\). By \PMlinkname{Lagrange's theorem}{LagrangesTheoremForFiniteGroups}, \(|P_x|\) divides \(p^b\), so it is a power of \(p\), as is the orbit size. An orbit is a singleton exactly when its point belongs to \(X^P\). All other orbit sizes are divisible by \(p\). Summing over the disjoint orbits proves the congruence. If \(X^P\) were empty, that congruence would force \(p\mid |X|\).
\end{proof}

\begin{example}
If a two-element group \(P=\{e,t\}\) acts on a finite set, then the number of points moved by \(t\) is even. Indeed, the points fixed by \(t\) are exactly \(X^P\), and the theorem gives \(|X|-|X^P|\equiv0\pmod2\).
\end{example}
"""),
 dict(title="normalizer of a subgroup", slug="normalizer-of-a-subgroup", canonical="NormalizerOfASubgroup",
      classifications=["20A05"], synonyms=["subgroup normalizer"],
      definitions=["conjugate subgroups", "normal subgroup"],
      related=["group", "lagranges-theorem-for-finite-groups", "orbit-stabilizer-theorem", "normal-subgroup-lattice-is-modular"],
      reference=("J. S. Milne", "Group Theory, Chapter 4 (conjugation and normalizers)", "https://www.jmilne.org/math/CourseNotes/GT.pdf"),
      body=r"""The normalizer consists of the elements whose conjugations preserve a given subgroup.

\begin{definition}
For \(H\le G\), its \emph{normalizer} is
\[
N_G(H)=\{g\in G:gHg^{-1}=H\}.
\]
Two subgroups \(H,K\) are \emph{conjugate subgroups} if \(K=gHg^{-1}\) for some \(g\in G\). A \emph{normal subgroup} of \(G\) is a subgroup \(H\) with \(gHg^{-1}=H\) for every \(g\in G\).
\end{definition}

\begin{proposition}
Conjugation defines an action of \(G\) on its subgroups. For every \(H\le G\), we have \(H\le N_G(H)\le G\), and \(H\) is normal in \(N_G(H)\). If \(G\) is finite, the number of distinct conjugates of \(H\) is \([G:N_G(H)]\).
\end{proposition}

\begin{proof}
The set \(gHg^{-1}\) contains \(e\); closure follows from
\[
(gh_1g^{-1})(gh_2g^{-1})=g(h_1h_2)g^{-1},\qquad
(ghg^{-1})^{-1}=gh^{-1}g^{-1}.
\]
Conjugation by \(g^{-1}\) reverses conjugation by \(g\), so it also preserves subgroup size. Identity conjugation does nothing, and successive conjugations by \(b\) and then \(a\) equal conjugation by \(ab\). Thus this is a group action. Its stabilizer at \(H\) is exactly \(N_G(H)\), a subgroup by \PMlinkname{orbit-stabilizer}{OrbitStabilizerTheorem}. For \(h\in H\), closure gives \(hHh^{-1}\subseteq H\), and conjugating by \(h^{-1}\) gives the reverse inclusion; hence \(H\le N_G(H)\). Normality in the normalizer is its defining condition. Finally, orbit-stabilizer counts the orbit of \(H\), namely its conjugates.
\end{proof}

\begin{example}
In an abelian group, \(ghg^{-1}=h\). Consequently every subgroup is normal and has normalizer equal to the whole group.
\end{example}
"""),
 dict(title="Sylow's theorems", slug="sylows-theorems", canonical="SylowsTheorems",
      classifications=["20D20"],
      synonyms=["Sylow theorems", "Sylow's theorem", "first Sylow theorem", "second Sylow theorem", "third Sylow theorem"],
      definitions=["Sylow p-subgroup", "Sylow subgroup"],
      related=["group", "lagranges-theorem-for-finite-groups", "orbit-stabilizer-theorem",
               "fixed-point-congruence-for-finite-p-group-actions", "normalizer-of-a-subgroup"],
      reference=("J. S. Milne", "Group Theory, Chapter 5 (Sylow theorems)", "https://www.jmilne.org/math/CourseNotes/GT.pdf"),
      body=r"""Sylow's theorems describe the existence, conjugacy, and number of subgroups whose orders capture a prime's full contribution to a finite group.

\begin{definition}
Let \(G\) be finite and let \(p\) be a prime number. Write \(|G|=p^a m\), where \(a\ge0\) and \(p\nmid m\). A \emph{Sylow p-subgroup} is a subgroup of order \(p^a\). A \emph{Sylow subgroup} means a Sylow p-subgroup for some specified prime. Write \(n_p\) for the number of Sylow p-subgroups of \(G\).
\end{definition}

The prerequisites are \PMlinkname{Lagrange's theorem}{LagrangesTheoremForFiniteGroups}, \PMlinkname{orbit-stabilizer}{OrbitStabilizerTheorem}, the \PMlinkname{fixed-point congruence}{FixedPointCongruenceForFinitePGroupActions}, and the \PMlinkname{normalizer of a subgroup}{NormalizerOfASubgroup}. Each has a separate proof in the collection.

\subsection*{A counting lemma}
\begin{lemma}
For \(0\le r\le a\), exactly \(p^{a-r}\) divides \(\binom{p^a m}{p^r}\): it is divisible by that power and not by \(p^{a-r+1}\).
\end{lemma}

\begin{proof}
Set \(N=p^a m\) and \(k=p^r\). The binomial coefficient counts the \(k\)-element subsets of an \(N\)-element set: count ordered lists of \(k\) distinct elements and divide by the \(k!\) reorderings of each subset. The resulting formula gives
\[
\binom Nk=\frac Nk\prod_{i=1}^{k-1}\frac{N-i}{k-i}.
\]
For \(1\le i<k\), write \(i=p^t u\), where \(p\nmid u\). Then \(t<r\), and both
\[
N-i=p^t(p^{a-t}m-u),\qquad k-i=p^t(p^{r-t}-u)
\]
contain exactly \(t\) factors of \(p\). Cancel those factors in each numerator and denominator. The remaining product has numerator and denominator not divisible by \(p\), while \(N/k=p^{a-r}m\). Clearing the denominator therefore shows that the integer \(\binom Nk\) contains exactly \(a-r\) factors of \(p\). For \(r=0\), the product is empty and the formula reduces to \(\binom N1=N\).
\end{proof}

\subsection*{First theorem: existence}
\begin{theorem}
For every \(0\le r\le a\), the group \(G\) has a subgroup of order \(p^r\). In particular, Sylow p-subgroups exist.
\end{theorem}

\begin{proof}
Let \(X\) be the set of \(p^r\)-element subsets of \(G\). Left translation, \(g\cdot A=gA\), is a group action: multiplication permutes \(G\), preserves subset size, and satisfies the action axioms. The counting lemma shows that \(|X|\) is not divisible by \(p^{a-r+1}\). Hence at least one orbit has size \(d\) not divisible by \(p^{a-r+1}\); otherwise their sum would be divisible by it.

Choose \(A\) in that orbit and let \(H\) be its stabilizer. Orbit-stabilizer gives \(d|H|=p^a m\), so \(p^r\mid |H|\). Choose \(x\in A\); the map \(h\mapsto hx\) sends \(H\) into \(A\) and is one-to-one, because \(h_1x=h_2x\) implies \(h_1=h_2\) after multiplication by \(x^{-1}\). Thus \(|H|\le |A|=p^r\). These two facts force \(|H|=p^r\).
\end{proof}

\subsection*{Second theorem: containment and conjugacy}
\begin{theorem}
Every p-subgroup \(Q\le G\) is contained in a conjugate of any chosen Sylow p-subgroup \(P\). Consequently, all Sylow p-subgroups are conjugate.
\end{theorem}

\begin{proof}
Let \(Q\) act on the left cosets \(G/P\) by \(q\cdot(gP)=qgP\). This is well-defined since equal cosets remain equal after left multiplication. The set has \([G:P]=m\) elements. Since \(p\nmid m\), the fixed-point congruence supplies a coset \(gP\) fixed by all \(q\in Q\). By the coset criterion, \(qgP=gP\) means \(g^{-1}qg\in P\). Thus \(g^{-1}Qg\le P\), or \(Q\le gPg^{-1}\). If \(Q\) is itself Sylow, both subgroups have \(p^a\) elements, so this inclusion is equality.
\end{proof}

\subsection*{Third theorem: counting}
\begin{theorem}
The number of Sylow p-subgroups satisfies
\[
n_p\mid m,\qquad n_p\equiv1\pmod p.
\]
\end{theorem}

\begin{proof}
Fix a Sylow p-subgroup \(P\). By conjugacy and the normalizer formula,
\[
n_p=[G:N_G(P)].
\]
Since \(P\le N_G(P)\), index multiplication gives \(m=[G:P]=n_p[N_G(P):P]\), proving divisibility.

Now let \(P\) act by conjugation on the set of all Sylow p-subgroups. It fixes \(P\). Suppose it fixes \(Q\); this means \(P\le N_G(Q)\). Put \(N=N_G(Q)\). Both \(P\) and \(Q\) are Sylow p-subgroups of \(N\): their order is \(p^a\), and \(|N|\) divides \(|G|\), so no larger power of \(p\) divides \(|N|\). Apply the already proved second theorem to \(N\): for some \(n\in N\), \(P=nQn^{-1}\). But \(n\) normalizes \(Q\), giving \(P=Q\). Thus this action has exactly one fixed point. The fixed-point congruence gives \(n_p\equiv1\pmod p\).
\end{proof}

\begin{corollary}
A Sylow p-subgroup is normal in \(G\) if and only if it is the unique Sylow p-subgroup.
\end{corollary}

\begin{proof}
If it is normal, every conjugate equals itself, and the second theorem accounts for every Sylow p-subgroup. Conversely, uniqueness forces every conjugate to equal it, which is normality.
\end{proof}

\begin{example}
In any group of order \(15=3\cdot5\), \(n_5\) divides \(3\) and is congruent to \(1\) modulo \(5\). Of the positive divisors \(1,3\), only \(1\) qualifies. Thus there is a unique subgroup of order five, and it is normal. This conclusion uses no classification of groups of order fifteen.
\end{example}

\begin{remark}
When \(p\nmid |G|\), we have \(a=0\) and the sole Sylow p-subgroup is \(\{e\}\). The proofs include this case. The proof chain uses finite counting and elementary prime divisibility in addition to the linked group-theoretic prerequisites; it does not assume Cauchy's theorem or the class equation.
\end{remark}
"""),
]
for entry in ENTRIES:
    entry["escapes"] = list(COMMON_ESCAPES)


def document_types(e):
    names = set(re.findall(r"\\begin\{(definition|theorem|proof|example|remark|corollary|lemma|proposition)\}", e["body"]))
    return sorted({"Result" if n in {"lemma", "proposition"} else n.capitalize() for n in names})


def verify(c):
    reviewed_targets = {e["slug"] for e in ENTRIES} | {
        "group", "integer", "associative", "characteristic-of-a-field-is-zero-or-prime"
    }
    for e in ENTRIES:
        d = fetch_public_math_concept_detail(c.cursor(), e["slug"])
        assert d and d["owner"] == "CWoo"
        for key in ["synonyms", "definitions"]:
            assert set(d[key]) == set(e[key]), (e["slug"], key)
        assert set(d["types"]) == set(document_types(e))
        assert {r["code"] for r in d["classifications"]} == set(e["classifications"])
        html = d["display_tex"]
        for name in re.findall(r"\\begin\{(definition|theorem|proof|example|remark|corollary|lemma|proposition)\}", e["body"]):
            assert "math-env-" + name in html, (e["slug"], name)
        assert html.count('class="math-env math-env-proof"') == e["body"].count(r"\begin{proof}")
        assert r"\PMlink" not in html
        maths = r"\\\(.*?\\\)|\\\[.*?\\\]"
        assert re.findall(maths, d["cleaned_tex"], re.S) == re.findall(maths, html, re.S)
        rows = c.execute("SELECT related_concept_id FROM math_related_concepts WHERE concept_id=?", (d["id"],)).fetchall()
        assert len(rows) == len(e["related"]) and all(r[0] for r in rows)
        links = Links(); links.feed(html)
        for attrs, label in links.links:
            href = attrs.get("href", "")
            if href.startswith("concept.html?slug="):
                assert href.split("=", 1)[1] in reviewed_targets, (e["slug"], label, href)
            if href.startswith("https:"):
                assert " " not in href
        for canonical in re.findall(r"\\PMlinkname\{[^{}]+\}\{([^{}]+)\}", e["body"]):
            target = c.execute("SELECT slug FROM math_concepts WHERE canonical_name=?", (canonical,)).fetchone()
            assert target and any(a.get("href") == "concept.html?slug=" + target[0] for a, _ in links.links), canonical
        print("Verified:", d["id"], e["slug"])
    for origin, target in [
        ("mersenne-numbers-two-small-results-on", "lagranges-theorem-for-finite-groups"),
        ("group-actions-and-homomorphisms", "orbit-stabilizer-theorem"),
    ]:
        detail = fetch_public_math_concept_detail(c.cursor(), origin)
        links = Links(); links.feed(detail["display_tex"])
        assert any(a.get("href") == "concept.html?slug=" + target and a.get("class") == "math-autolink"
                   for a, _ in links.links), (origin, target)


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
