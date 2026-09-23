"""Graph foundations and explicit immediate-predecessor terminology for Collatz.

Preserves the legacy path entry and diagrams, adding a convention note rather
than silently changing examples that deliberately allow repeated vertices.
Apply after add_collatz_conjecture.py. Safe to rerun without duplicate metadata.
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
from services.math.concept_render_service import render_tex_reusing_existing_diagrams
from services.math.public_concept_detail_service import fetch_public_math_concept_detail
from services.math.public_search_service import search_public_math_library
from add_eight_algebra_concepts import source, Links
from add_sylow_theorems import document_types
from add_collatz_conjecture import EXCLUSIONS


def entry(title, slug, canonical, codes, synonyms, definitions, related, body, reference):
    return dict(title=title, slug=slug, canonical=canonical, classifications=codes,
                synonyms=synonyms, definitions=definitions, related=related, body=body,
                reference=reference, escapes=list(EXCLUSIONS)+["edge", "edges", "loop", "loops", "parallel",
                "walk", "trail", "circuit", "simple", "weak", "strong", "connected", "degree",
                "source", "target", "tail", "head", "component", "successor", "predecessor", "cycle",
                "adjacent vertices", "reachability", "strongly connected", "deterministic", "inverse image"])


GRAPH_REF = ("OpenStax", "Contemporary Mathematics, 12.4: Navigating Graphs",
             "https://openstax.org/books/contemporary-mathematics/pages/12-4-navigating-graphs")
ENTRIES = [
entry("directed graph", "directed-graph", "DirectedGraph", ["05C20"], ["digraph"],
      ["directed edge", "in-degree", "out-degree", "weakly connected digraph", "strongly connected digraph"],
      ["graph-homomorphism", "subgraph", "collatz-conjecture"], r"""
\begin{definition}
A \emph{directed graph}, or \emph{digraph}, is a pair \(G=(V,E)\), where \(V\) is a set of vertices and \(E\subseteq V\times V\). A \emph{directed edge} \((u,v)\) is written \(u\to v\); its tail is \(u\) and its head is \(v\). We allow loops \(v\to v\) but no parallel copies of an edge. The graph may be infinite. A directed multigraph instead uses a separate edge set with tail and head maps to \(V\), allowing distinct edges with the same endpoints.

The \emph{out-degree} of \(v\) is \(|\{w:(v,w)\in E\}|\), and its \emph{in-degree} is \(|\{u:(u,v)\in E\}|\). A loop contributes one to each. These degrees may be infinite.
\end{definition}
\begin{definition}
A nonempty digraph is a \emph{weakly connected digraph} if any two vertices can be joined by a finite sequence of adjacent vertices after directions are ignored. It is a \emph{strongly connected digraph} if for every ordered pair \((u,v)\) there is a directed walk from \(u\) to \(v\). A directed walk follows arrows in their given direction, allowing repetitions. The corresponding components are the equivalence classes of weak connectivity and mutual directed reachability, respectively; length-zero walks allow a vertex to reach itself.
\end{definition}
\begin{example}
With vertices \(a,b,c\) and arrows \(a\to b,b\to c\), the graph is weakly but not strongly connected: there is no directed walk from \(c\) to \(a\). Adding \(c\to a\) makes it strongly connected.
\end{example}
\begin{remark}
The Collatz graph is a digraph with out-degree one everywhere. Allowing loops is essential for the Syracuse graph, where \(1\to1\). Other authors exclude loops when saying digraph; always check the convention. The existing graph homomorphism entry explains the more general incidence-map formulation.
\end{remark}
""", GRAPH_REF),
entry("walks, paths and cycles in graphs", "walks-paths-and-cycles-in-graphs", "WalksPathsAndCyclesInGraphs", ["05C38", "05C20"],
      ["graph walks and cycles"], ["graph walk", "directed walk", "graph trail", "directed trail", "closed walk",
      "simple path", "directed path", "graph cycle", "directed cycle", "closed trail"],
      ["directed-graph", "path1", "hamiltonian-cycle", "euler-path", "collatz-conjecture"], r"""
This entry distinguishes walks, trails, paths and cycles. Its path convention is stricter than the \PMlinkname{legacy path entry}{Path1}, which explicitly permits repetitions.
\begin{definition}
A \emph{graph walk} of length \(k\ge0\) is a finite alternating sequence \(v_0,e_1,v_1,\ldots,e_k,v_k\), where each edge joins its neighboring vertices. A \emph{directed walk} in a directed graph requires \(e_i\) to point from \(v_{i-1}\) to \(v_i\). Edges can be omitted from the notation when the vertices determine them uniquely. Vertices and edges may repeat. A length-zero walk consists of one vertex.

A \emph{graph trail} is a walk with no repeated edge; a \emph{directed trail} also respects edge directions. A \emph{simple path}, called a path here, has no repeated vertex. A \emph{directed path} is a directed walk with no repeated vertex. A \emph{closed walk} has \(v_k=v_0\); a \emph{closed trail} is a closed walk without repeated edges.

A \emph{graph cycle} is a positive-length closed trail in which \(v_0,\ldots,v_{k-1}\) are distinct. A \emph{directed cycle} additionally follows the directions of all its edges. In a simple undirected graph a cycle has length at least three. With loops allowed, a loop is a cycle of length one; in a digraph, two opposite arrows can form a cycle of length two. Traversing one undirected edge forward and backward is not a cycle, because that edge repeats.
\end{definition}
\begin{proposition}
If a finite directed walk joins \(u\) to \(v\), then a directed path joins \(u\) to \(v\).
\end{proposition}
\begin{proof}
If a vertex occurs twice, delete the portion between two occurrences. The remaining sequence still follows valid arrows, has the same endpoints, and is shorter. Repeating this operation must stop because lengths are nonnegative integers. The resulting walk has no repeated vertices. When \(u=v\), the length-zero path suffices.
\end{proof}
\begin{example}
In a digraph with arrows \(a\to b,b\to a,b\to c\), the sequence \(a,b,a,b,c\) is a directed walk but not a trail or path. The sequence \(a,b,c\) is a directed path, and \(a,b,a\) is a directed cycle. In Collatz, \(1,4,2,1\) is a directed cycle; in Syracuse, \(1,1\) describes the loop cycle.
\end{example}
\begin{remark}
Terminology varies. The existing path entry uses path for what is called walk here. Also, the established name Euler path usually means an edge-exhausting trail, not necessarily a simple path; Euler circuit similarly means an edge-exhausting closed trail, not necessarily a cycle under the definition above. A Hamiltonian cycle visits each vertex exactly once before returning to its start.
\end{remark}
""", GRAPH_REF),
entry("functional graph", "functional-graph", "FunctionalGraph", ["05C20", "05C05"], ["successor graph"],
      ["immediate predecessor set", "forward orbit of a self-map", "periodic point of a self-map"],
      ["directed-graph", "walks-paths-and-cycles-in-graphs", "collatz-conjecture"], r"""
\begin{definition}
For a self-map \(F:X\to X\), its \emph{functional graph}, or \emph{successor graph}, has vertex set \(X\) and the arrow \(x\to F(x)\) at each vertex. Thus every vertex has out-degree exactly one. Conversely, a digraph with out-degree one determines a unique self-map. Loops are allowed.

The \emph{forward orbit of a self-map} from \(x\) is \(x,F(x),F^2(x),\ldots\). A \emph{periodic point of a self-map} satisfies \(F^r(x)=x\) for some integer \(r\ge1\); its least such \(r\) is its period. The \emph{immediate predecessor set} of \(y\) is \(F^{-1}(\{y\})=\{x:F(x)=y\}\). This is an inverse image, not an assertion that \(F\) has an inverse function. Vertices reaching \(y\) after several steps need not be immediate predecessors.
\end{definition}
\begin{proposition}
In a finite nonempty functional graph, every forward orbit eventually enters a directed cycle. Each weakly connected component contains exactly one directed cycle.
\end{proposition}
\begin{proof}
The sequence \(x,F(x),F^2(x),\ldots\) in a finite set repeats a vertex. From that point the deterministic rule repeats the same finite segment; taking the segment up to its first repetition gives a directed cycle. If \(u\to v\), the orbit of \(u\) continues as the orbit of \(v\), so both eventually reach the same cycle. Equality of eventual cycles therefore propagates along any finite undirected path. All vertices in a weak component have one common eventual cycle, and each component contains that cycle.
\end{proof}
\begin{example}
The rules \(F(a)=b,F(b)=c,F(c)=b,F(d)=c\) give the cycle \(b\to c\to b\) with \(a\) and \(d\) feeding into it. The immediate predecessors of \(c\) are \(b,d\); although \(a\) reaches \(c\) after two steps, it is not in that set.
\end{example}
\begin{remark}
Finiteness is essential: on \(\mathbb N\), the map \(F(n)=n+1\) has no cycle. An infinite functional graph can also have infinitely many incoming neighbors. Thus the finite theorem does not settle the Collatz conjecture. For a component known to reach a cycle, collapsing the cycle and removing its edges leaves a tree directed toward the collapsed root: an additional undirected cycle would force a further directed cycle, since each vertex has only one outgoing edge. The Collatz entry and its Syracuse discussion illustrate these structures on infinite vertex sets.
\end{remark}
""", ("USACO Guide", "Introduction to Functional Graphs", "https://usaco.guide/silver/func-graphs")),
]

PREDECESSOR_DEFINITION = r"""\begin{definition}
For a positive odd target \(m\), its \emph{Syracuse predecessor family} means its \PMlinkname{immediate predecessor set}{FunctionalGraph}:
\[
P_S(m)=S^{-1}(\{m\})=\{x\in\mathbb N_{>0}:x\text{ is odd and }S(x)=m\}.
\]
Here predecessor family is descriptive terminology for this entry, not a different map or a claim of standard terminology. It includes exactly one-step predecessors. The proposition below proves that this family is empty when \(3\mid m\), and otherwise is exactly one family generated by \(f(x)=4x+1\) from its least member.
\end{definition}

"""
PATH_NOTE = r"""\begin{remark}
Terminology convention: this legacy entry uses path in the broad sense permitting repeated vertices and edges. In the companion \PMlinkname{walks, paths and cycles entry}{WalksPathsAndCyclesInGraphs}, such sequences are called walks, and a path has no repeated vertices. The examples below retain the broad convention. Directed examples must still follow every arrow's direction.
\end{remark}

"""


def linked_slugs(html):
    p = Links(); p.feed(html)
    return {a["href"].split("slug=", 1)[1] for a, _ in p.links if a.get("href", "").startswith("concept.html?slug=")}


def relate(c, origin, target):
    a = c.execute("SELECT id FROM math_concepts WHERE slug=?", (origin,)).fetchone()[0]
    b = c.execute("SELECT id,canonical_name FROM math_concepts WHERE slug=?", (target,)).fetchone()
    if not c.execute("SELECT 1 FROM math_related_concepts WHERE concept_id=? AND related_canonical_name=?", (a,b[1])).fetchone():
        c.execute("INSERT INTO math_related_concepts(concept_id,related_canonical_name,related_concept_id) VALUES(?,?,?)", (a,b[1],b[0]))


def update_text(c, slug, text, now):
    row = c.execute("SELECT id,cleaned_tex FROM math_concepts WHERE slug=?", (slug,)).fetchone()
    if row[1] != text:
        rendered = render_tex_reusing_existing_diagrams(row[0], text, c.cursor())
        c.execute("UPDATE math_concepts SET cleaned_tex=?,rendered_tex=?,updated_at=? WHERE id=?", (text,rendered,now,row[0]))


def verify(c):
    for e in ENTRIES:
        d = fetch_public_math_concept_detail(c.cursor(),e["slug"])
        assert d["cleaned_tex"] == source(e) and d["owner"] == "CWoo"
        for key in ["synonyms", "definitions"]: assert set(d[key])==set(e[key])
        assert set(d["types"])==set(document_types(e))
        assert {r["code"] for r in d["classifications"]}==set(e["classifications"])
        assert e["slug"] not in linked_slugs(d["display_tex"])
        assert linked_slugs(d["display_tex"]) <= {"collatz-conjecture", "directed-graph",
            "walks-paths-and-cycles-in-graphs", "functional-graph", "path1", "integer",
            "graph-homomorphism", "euler-circuit", "euler-path", "hamiltonian-cycle"}
        assert r"\PMlink" not in d["display_tex"]
        assert d["display_tex"].count('class="math-env math-env-proof"')==e["body"].count(r"\begin{proof}")
        pattern=r"\\\(.*?\\\)|\\\[.*?\\\]"
        assert re.findall(pattern,source(e),re.S)==re.findall(pattern,d["display_tex"],re.S)
        assert any(r.get("slug")==e["slug"] for r in search_public_math_library(c.cursor(),e["title"])["data"])
        related=c.execute("SELECT related_concept_id FROM math_related_concepts WHERE concept_id=?",(d["id"],)).fetchall()
        assert len(related)==len(e["related"]) and all(r[0] for r in related)
        print("Verified",d["id"],e["slug"])
    collatz=fetch_public_math_concept_detail(c.cursor(),"collatz-conjecture")
    assert PREDECESSOR_DEFINITION.strip() in collatz["cleaned_tex"]
    assert "Syracuse predecessor family" in collatz["definitions"]
    assert {e["slug"] for e in ENTRIES} <= linked_slugs(collatz["display_tex"])
    assert "walks-paths-and-cycles-in-graphs" in linked_slugs(fetch_public_math_concept_detail(c.cursor(),"path1")["display_tex"])
    assert c.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
    assert not c.execute("PRAGMA foreign_key_check").fetchall()


def apply(path):
    if not path.is_file(): raise FileNotFoundError(path)
    with sqlite3.connect(path) as c:
        c.row_factory=sqlite3.Row
        c.execute("PRAGMA foreign_keys=ON")
        now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for e in ENTRIES:
            if c.execute("SELECT 1 FROM math_concepts WHERE slug=?",(e["slug"],)).fetchone(): continue
            for t in [e["title"],*e["synonyms"],*e["definitions"]]:
                assert not c.execute("""SELECT title FROM math_concepts WHERE lower(title)=lower(?)
                    UNION SELECT synonym_text FROM math_synonyms WHERE lower(synonym_text)=lower(?)
                    UNION SELECT defined_term FROM math_definitions WHERE lower(defined_term)=lower(?)""",(t,t,t)).fetchone(),t
            # Related new entries occur earlier in this list.
            related=[c.execute("SELECT canonical_name FROM math_concepts WHERE slug=?",(s,)).fetchone()[0] for s in e["related"]]
            create_math_concept(c.cursor(),e["canonical"],e["slug"],e["title"],now,"CWoo",source(e),1,
                                e["classifications"],document_types(e),e["synonyms"],e["definitions"],related)
        row=c.execute("SELECT id,cleaned_tex FROM math_concepts WHERE slug='collatz-conjecture'").fetchone()
        text=row[1]
        if PREDECESSOR_DEFINITION.strip() not in text:
            marker=r"\begin{proposition}"+"\nFor a positive odd target"
            assert text.count(marker)==1
            text=text.replace(marker,PREDECESSOR_DEFINITION+marker)
        # Specific links avoid enabling ambiguous bare 'path', 'cycle', 'graph'.
        replacements={"is a directed graph with positive integers":r"is a \PMlinkname{directed graph}{DirectedGraph} with positive integers",
                      "is often called a functional graph":r"is often called a \PMlinkname{functional graph}{FunctionalGraph}",
                      "has a directed path to the known cycle":r"has a \PMlinkname{directed path}{WalksPathsAndCyclesInGraphs} to the known cycle"}
        for old,new in replacements.items(): text=text.replace(old,new)
        update_text(c,"collatz-conjecture",text,now)
        for term in ["Syracuse predecessor family", "predecessor family"]:
            if not c.execute("SELECT 1 FROM math_definitions WHERE concept_id=? AND defined_term=?",(row[0],term)).fetchone():
                c.execute("INSERT INTO math_definitions(concept_id,defined_term) VALUES(?,?)",(row[0],term))
        for e in ENTRIES: relate(c,"collatz-conjecture",e["slug"])
        text=c.execute("SELECT cleaned_tex FROM math_concepts WHERE slug='path1'").fetchone()[0]
        if PATH_NOTE.strip() not in text: update_text(c,"path1",PATH_NOTE+text,now)
        c.execute("""INSERT OR IGNORE INTO math_concept_types(concept_id,type_id)
            SELECT c.id,t.id FROM math_concepts c,math_types t
            WHERE c.slug='path1' AND t.type_name='Remark'""")
        relate(c,"path1","walks-paths-and-cycles-in-graphs")
        verify(c)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db",type=Path,default=SRC.parent/"portfolio.db")
    apply(p.parse_args().db)
