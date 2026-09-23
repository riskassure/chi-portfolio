"""Create a sourced, expandable Collatz topic entry, with proved local identities.

Checked titles, synonyms, defined terms and full sources for Collatz/Syracuse.
Do not mistake the proofs of auxiliary results for a proof of the conjecture.
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
from add_eight_algebra_concepts import Links
from add_twenty_concepts_20260922 import ESCAPES

SLUG = "collatz-conjecture"
TITLE = "Collatz conjecture"
SYNONYMS = ["Collatz problem", "3x+1 problem", "3n+1 problem", "Syracuse problem", "hailstone conjecture"]
DEFINITIONS = ["Collatz map", "shortcut Collatz map", "Syracuse map", "Syracuse function",
               "Collatz graph", "Syracuse graph", "2-adic valuation", "2-adic integers", "2-adic numbers",
               "Collatz parity encoding"]
CODES = ["11B83", "11A07", "05C20", "11S85"]
TYPES = ["Conjecture", "Topic", "Definition", "Result", "Proof", "Example", "Remark"]
RELATED = ["integer", "graph-homomorphism", "subgraph", "distancein-a-graph"]
EXCLUSIONS = list(ESCAPES) + ["odd", "even", "cycle", "cyclic", "orbit", "path", "tree", "rooted",
    "component", "connected", "connected component", "inverse", "inverse map", "shift", "density",
    "logarithmic", "valuation", "metric", "distance", "norm", "rational", "rational number",
    "simple", "normal", "relation", "branch", "branches", "degree", "conjugacy", "topology",
    "continuous", "continuity", "compact", "fixed point", "fixed", "limit", "bound", "bounded",
    "positive", "negative", "binary", "word", "encoding", "code", "induction", "generalization",
    "equivalent", "equivalence", "representative", "representatives", "isometry", "function graph",
    "functional", "function", "natural", "natural number", "sequence", "map", "iteration", "order",
    "compatible", "congruence", "context", "converge", "eventually", "length", "link", "open",
    "useful", "vertex", "vertices"]

BODY = r"""
The Collatz conjecture asks whether an elementary rule eventually brings every positive integer to \(1\). This topic entry is intended as a starting point for further exploration. The conjecture remains open; the propositions proved below describe its structure and do not settle it.

\section*{The problem and three map conventions}
\begin{definition}
Write \(\mathbb N_{>0}=\{1,2,3,\ldots\}\). The \emph{Collatz map} is
\[
C(n)=\begin{cases}n/2&\text{if }n\text{ is even},\cr 3n+1&\text{if }n\text{ is odd}.\end{cases}
\]
The forward orbit of \(n\) is \(n,C(n),C^2(n),\ldots\), where a superscript denotes repeated application, not an ordinary power.
\end{definition}
\begin{conjecture}
For every \(n\in\mathbb N_{>0}\), some integer \(k\ge0\) satisfies \(C^k(n)=1\).
\end{conjecture}
Once \(1\) is reached, the orbit repeats \(1\to4\to2\to1\). The restriction to positive integers matters.
\begin{example}
Starting at \(6\) gives
\[
6\to3\to10\to5\to16\to8\to4\to2\to1.
\]
This proves the claim for this starting value only.
\end{example}
\begin{definition}
For a nonzero integer \(a\), its \emph{2-adic valuation} \(v_2(a)\) is the largest integer \(r\ge0\) such that \(2^r\) divides \(a\). Set \(v_2(0)=+\infty\). The \emph{Syracuse map}, or \emph{Syracuse function}, on positive odd integers is
\[
S(n)=\frac{3n+1}{2^{v_2(3n+1)}}.
\]
It performs an odd Collatz step and then removes every factor of \(2\). Another convention is the \emph{shortcut Collatz map}
\[
T(n)=\begin{cases}n/2&\text{if }n\text{ is even},\cr (3n+1)/2&\text{if }n\text{ is odd}.\end{cases}
\]
\end{definition}
Names vary between authors, so formulas should always be specified. Here \(C\) has the cycle \(1,4,2\), \(T\) has the cycle \(1,2\), and \(S\) fixes \(1\). Their positive-integer convergence claims are equivalent: \(T\) compresses the mandatory halving after an odd step, and \(S\) compresses each finite run of halvings. Any even starting integer reaches an odd one by finitely many halvings. The example above becomes \(3\to5\to1\) under \(S\).

\section*{A brief history and the status of partial results}
The problem is traditionally attributed to Lothar Collatz in 1937. Its circulation under several names explains the alternatives Syracuse problem, \(3x+1\) problem, and hailstone problem. Jeffrey Lagarias's surveys provide historical context and distinguish the original question from its many generalizations; see the references below.

Terence Tao's 2019 work proved that, for any function \(g(n)\) tending to infinity, almost every positive starting integer has some Collatz iterate below \(g(n)\), with almost every interpreted in logarithmic density. For an exceptional set \(E\), logarithmic density zero means
\[
\lim_{X\to\infty}\frac{1}{\log X}\sum_{\substack{n\le X\cr n\in E}}\frac1n=0.
\]
This does not allow \(g(n)=1\), does not exclude all exceptional starting values, and does not prove the conjecture. Likewise, checking finitely many starting values cannot establish a statement about every positive integer. See \PMlinkexternal{Tao's account of the result}{https://terrytao.wordpress.com/2019/09/10/almost-all-collatz-orbits-attain-almost-bounded-values/}.

\section*{The graph-theoretic viewpoint}
\begin{definition}
The \emph{Collatz graph} is a directed graph with positive integers as vertices and one arrow \(n\to C(n)\) from each vertex. A directed graph records ordered pairs of vertices as arrows. A graph built from a self-map in this way is often called a functional graph. The \emph{Syracuse graph} instead uses positive odd vertices and arrows \(n\to S(n)\), optionally labeled by \(v_2(3n+1)\).
\end{definition}
Each vertex has exactly one outgoing arrow, but its incoming arrows need not be unique. In the Collatz graph, \(m\) always has predecessor \(2m\). Its only possible odd predecessor is \((m-1)/3\), which is a positive odd integer exactly when \(m\equiv4\pmod6\). This follows directly by solving the two branches of \(C(n)=m\).

The conjecture says every vertex has a directed path to the known cycle. The graph is not literally a tree because that cycle is present. In the component feeding the cycle, contracting the three cycle vertices to a single root and removing the resulting cycle edges leaves a tree directed toward that root. The conjecture asserts that this component contains every positive integer. Indeed, once a trajectory is known to reach the cycle, any vertex joined to it by an arrow in either direction does too; induction along an undirected finite path proves the component assertion. A further undirected cycle would force another directed cycle because every vertex has only one outgoing arrow.

A counterexample must either enter a different directed cycle or follow an unbounded orbit. A bounded orbit visits finitely many integers, hence repeats a value and is eventually periodic. In the Syracuse graph, the familiar cycle is compressed to the loop \(1\to1\).

\section*{Why the function f(x)=4x+1 is significant}
Put \(f(x)=4x+1\). This is an auxiliary affine map, not another name for a Collatz step.
\begin{proposition}
For every positive odd \(x\),
\[
S(f(x))=S(x),\qquad v_2(3f(x)+1)=v_2(3x+1)+2.
\]
Consequently all the integers \(x,f(x),f^2(x),\ldots\) have the same outgoing neighbor in the Syracuse graph.
\end{proposition}
\begin{proof}
The identity \(3(4x+1)+1=4(3x+1)\) increases the valuation by exactly two and leaves the odd part unchanged. Repeat this argument along the iterates of \(f\).
\end{proof}
\begin{example}
The family \(3,13,53,213,\ldots\) all maps to \(5\) under \(S\); the corresponding valuations are \(1,3,5,7,\ldots\). The family \(1,5,21,85,\ldots\) all maps to \(1\). These are families of incoming neighbors, not consecutive forward Syracuse steps.
\end{example}
\begin{proposition}
For a positive odd target \(m\), every positive odd predecessor under \(S\) is
\[
x_k=\frac{2^k m-1}{3},\qquad k\ge1,
\]
where \(2^k m\equiv1\pmod3\). There are no such predecessors when \(3\mid m\). Otherwise they form exactly one \(f\)-family: \(k=1,3,5,\ldots\) when \(m\equiv2\pmod3\), and \(k=2,4,6,\ldots\) when \(m\equiv1\pmod3\).
\end{proposition}
\begin{proof}
The equation \(S(x)=m\) is equivalent to \(3x+1=2^k m\), with \(k\ge1\). Since \(m\) is odd, this \(k\) is automatically the exact valuation. Integrality is precisely the displayed congruence; an integral \(x_k\) is positive and odd. As \(2\equiv-1\pmod3\), the allowed exponents have the asserted parity, and no exponent works for \(3\mid m\). Finally \(x_{k+2}=4x_k+1\), proving the description of the whole family.
\end{proof}
This explains repeated branching patterns, but it does not prove that every forward orbit reaches \(1\). In particular \(S(f(x))=S(x)\) says that two orbits merge; it does not imply that \(f(x)\) occurs on the forward orbit of \(x\), or that \(S\) commutes with \(f\).

\section*{The 2-adic setting}
\begin{definition}
The ring of \emph{2-adic integers} \(\mathbb Z_2\) consists of compatible residues modulo \(2,4,8,\ldots\): the residue modulo \(2^{j+1}\) reduces to the chosen residue modulo \(2^j\). Addition and multiplication are compatible residuewise operations. Equivalently, its elements have expansions \(\sum_{j\ge0}b_j2^j\) with \(b_j\in\{0,1\}\). The field of \emph{2-adic numbers} \(\mathbb Q_2\) consists of fractions \(2^{-r}z\), with \(z\in\mathbb Z_2\), \(r\ge0\).

For nonzero \(z\in\mathbb Z_2\), \(v_2(z)\) is the first index of a nonzero binary digit. The metric is \(d_2(x,y)=2^{-v_2(x-y)}\), with \(d_2(x,x)=0\). Thus agreeing modulo a large power of \(2\) means being close. Rational numbers with odd denominators belong to \(\mathbb Z_2\), since those denominators are invertible modulo every power of \(2\).
\end{definition}
The formula for \(T\) extends to \(\mathbb Z_2\). On the even residue class \(x/2\) is a 2-adic integer; on the odd class so is \((3x+1)/2\). On each class the formula is continuous in \(d_2\), and these parity classes are open and closed, so \(T\) is continuous on \(\mathbb Z_2\).

\begin{definition}
The \emph{Collatz parity encoding} is
\[
Q(x)=\sum_{j\ge0}\epsilon_j(x)2^j,\qquad \epsilon_j(x)=T^j(x)\bmod2\in\{0,1\}.
\]
\end{definition}
The parity-encoding theorem identifies \(Q\) as a homeomorphism of \(\mathbb Z_2\) and gives \(Q(T(x))=\sigma(Q(x))\), where \(\sigma\) deletes the lowest binary digit: \(\sigma(y)=(y-(y\bmod2))/2\). This known conjugacy theorem is discussed by Bernstein and Lagarias in the reference below; a full treatment can be developed separately. In these coordinates iteration shifts the parity sequence. The difficult remaining question is which parity sequences correspond to positive ordinary integers. The full 2-adic system does not send every point into the positive cycle: \(T(0)=0\) and \(T(-1)=-1\).

\begin{proposition}
For every \(j\ge0\),
\[
f^j(x)=4^j x+\frac{4^j-1}{3},\qquad f^j(x)+\frac13=4^j\left(x+\frac13\right).
\]
For \(x\in\mathbb Z_2\), these iterates converge 2-adically to the fixed point \(-1/3\).
\end{proposition}
\begin{proof}
The first identity follows by induction from \(f(x)=4x+1\), or by summing a finite geometric progression. The second is a rearrangement. If \(x\ne-1/3\), its right-hand side has valuation \(2j+v_2(x+1/3)\), which tends to infinity. If \(x=-1/3\), the sequence is already constant.
\end{proof}
For positive ordinary \(x\), the same iterates grow without bound in the usual real metric. At their 2-adic limit, \(3(-1/3)+1=0\), so the odd-part formula for \(S\) is undefined there: it would require stripping infinitely many factors of \(2\). This is a useful distinction between the continuous shortcut map \(T\) and the odd-only acceleration \(S\).

\section*{Questions for further exploration}
\begin{itemize}
\item Compare finite portions of the \(C\)-graph and \(S\)-graph, keeping truncated edges visibly distinct from actual termination.
\item Label Syracuse arrows by their valuations and organize incoming neighbors into \(4x+1\) families. How does this description interact with successive backward steps?
\item Study which residue classes modulo \(2^r\) determine a chosen finite parity pattern, then develop the parity-encoding theorem in detail.
\item Examine candidate cycles through their valuation sequences. For a Syracuse cycle of length \(r\), returning to the starting value requires \(2^{a_1+\cdots+a_r}>3^r\): composing the steps gives \(2^{a_1+\cdots+a_r}x=3^r x+b\) with \(b>0\). This necessary inequality is not a sufficient condition for a cycle.
\item Keep numerical observations, proved propositions, and open questions separately labeled as this entry grows.
\end{itemize}

\begin{thebibliography}{9}
\bibitem{history} J. C. Lagarias, \PMlinkexternal{The 3x+1 Problem: An Overview}{https://arxiv.org/abs/2111.02635}, overview originally published in 2010, arXiv version 2021.
\bibitem{survey} J. C. Lagarias, \PMlinkexternal{The 3x+1 problem and its generalizations}{https://www.cecm.sfu.ca/organics/papers/lagarias/}, American Mathematical Monthly 92 (1985), 3--23.
\bibitem{tao} T. Tao, \PMlinkexternal{Almost all Collatz orbits attain almost bounded values}{https://terrytao.wordpress.com/2019/09/10/almost-all-collatz-orbits-attain-almost-bounded-values/}, 2019 research announcement and link to the paper.
\bibitem{conjugacy} D. J. Bernstein and J. C. Lagarias, \PMlinkexternal{The 3x+1 conjugacy map}{https://websites.umich.edu/\%7Elagarias/doc/bernstein.pdf}, Canadian Journal of Mathematics 48 (1996), 1154--1169.
\end{thebibliography}
"""


def source():
    return "\n".join(r"\PMlinkescapeword{"+s+"}" for s in dict.fromkeys(EXCLUSIONS)) + "\n\n" + BODY.strip()+"\n"


def verify(c):
    d = fetch_public_math_concept_detail(c.cursor(), SLUG)
    assert d and d["owner"] == "CWoo" and d["cleaned_tex"] == source()
    for key, expected in [("types", TYPES), ("synonyms", SYNONYMS), ("definitions", DEFINITIONS)]:
        assert set(d[key]) == set(expected), key
    assert {r["code"] for r in d["classifications"]} == set(CODES)
    html = d["display_tex"]
    assert r"\PMlink" not in html
    links = Links()
    links.feed(html)
    targets = {a["href"].split("slug=", 1)[1] for a, _ in links.links
               if a.get("href", "").startswith("concept.html?slug=")}
    assert targets <= {"numeration-system", "field", "integer", "ring"}, targets
    for env in ["proof", "proposition", "definition", "conjecture"]:
        assert html.count('class="math-env math-env-'+env+'"') == BODY.count(r"\begin{"+env+"}"), env
    pattern = r"\\\(.*?\\\)|\\\[.*?\\\]"
    assert re.findall(pattern, source(), re.S) == re.findall(pattern, html, re.S)
    assert any(r.get("slug") == SLUG for r in search_public_math_library(c.cursor(), "Collatz")["data"])
    rows = c.execute("SELECT related_concept_id FROM math_related_concepts WHERE concept_id=?", (d["id"],)).fetchall()
    assert len(rows)==len(RELATED) and all(r[0] for r in rows)
    assert c.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert not c.execute("PRAGMA foreign_key_check").fetchall()
    print("Verified", d["id"], SLUG)


def apply(path):
    if not path.is_file():
        raise FileNotFoundError(path)
    with sqlite3.connect(path) as c:
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA foreign_keys=ON")
        if not c.execute("SELECT id FROM math_concepts WHERE slug=?", (SLUG,)).fetchone():
            for term in [TITLE, *SYNONYMS, *DEFINITIONS]:
                assert not c.execute("""SELECT title FROM math_concepts WHERE lower(title)=lower(?)
                    UNION SELECT synonym_text FROM math_synonyms WHERE lower(synonym_text)=lower(?)
                    UNION SELECT defined_term FROM math_definitions WHERE lower(defined_term)=lower(?)""", (term,term,term)).fetchone(), term
            related = [c.execute("SELECT canonical_name FROM math_concepts WHERE slug=?", (s,)).fetchone()[0] for s in RELATED]
            create_math_concept(c.cursor(), "CollatzConjecture", SLUG, TITLE, datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "CWoo", source(), 1, CODES, TYPES, SYNONYMS, DEFINITIONS, related)
        verify(c)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", type=Path, default=SRC.parent/"portfolio.db")
    apply(p.parse_args().db)
