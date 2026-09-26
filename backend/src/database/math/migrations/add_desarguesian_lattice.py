"""Add the Arguesian (Desarguesian) lattice law and a module-lattice proof."""
import argparse
from datetime import datetime
from pathlib import Path
import re
import sqlite3
from add_group_centralizers_and_series import entry, SRC, source, document_types, create_math_concept, fetch_public_math_concept_detail, relate, links
from services.math.autolink_service import apply_math_autolinker

E=entry('Desarguesian lattice','desarguesian-lattice','DesarguesianLattice','06C05',
    ['Arguesian lattice','arguesian lattices','Desarguesian lattices'],[],
    'modular-lattice distributive-lattice normal-subgroup-lattice-is-modular',r"""
The Desarguesian condition, more commonly called the Arguesian law in lattice theory, expresses an algebraic counterpart of Desargues' theorem in projective geometry. It is stronger than modularity and weaker than distributivity.
\begin{definition}
A lattice \(L\) is \emph{Arguesian}, or \emph{Desarguesian}, if the following implication holds for every six elements \(a_0,a_1,a_2,b_0,b_1,b_2\). Put
\[
c_0=(a_1\vee a_2)\wedge(b_1\vee b_2),\qquad
c_1=(a_0\vee a_2)\wedge(b_0\vee b_2),
\]
\[
c_2=(a_0\vee a_1)\wedge(b_0\vee b_1).
\]
Then require
\[
(a_0\vee b_0)\wedge(a_1\vee b_1)\le a_2\vee b_2
\quad\Longrightarrow\quad c_2\le c_0\vee c_1.
\]
Here meet and join are the greatest lower bound and least upper bound. This condition is required for all six-tuples, not just configurations resembling nondegenerate triangles.
\end{definition}
\section*{Geometric meaning}
In the lattice of subspaces of a vector space, join is subspace sum and meet is intersection. In projective-plane language, let \(a_i,b_i\) denote the vertices of two nondegenerate triangles. The hypothesis says that the intersection of two lines joining corresponding vertices lies on the third joining line: the triangles are perspective from a point. The elements \(c_i\) represent intersections of corresponding sides. The conclusion says that the third such intersection lies on the line through the other two: they are collinear. The lattice implication also covers degenerate cases that require care in a drawing.
\begin{proposition}
The lattice of submodules of any module is Arguesian. In particular, every vector-space subspace lattice is Arguesian.
\end{proposition}
\begin{proof}
Write \(A_i,B_i\) for the six submodules and assume
\[
(A_0+B_0)\cap(A_1+B_1)\subseteq A_2+B_2.
\]
Take \(v\in C_2\). Choose \(a_i\in A_i,b_i\in B_i\), for \(i=0,1\), with \(v=a_0+a_1=b_0+b_1\). Then
\[
d=a_0-b_0=b_1-a_1\in(A_0+B_0)\cap(A_1+B_1).
\]
By hypothesis, write \(d=a_2+b_2\) with \(a_2\in A_2,b_2\in B_2\). Set \(t=a_0-a_2=b_0+b_2\). Thus \(t\in C_1\), while \(v-t=a_1+a_2=b_1-b_2\in C_0\). Consequently \(v=(v-t)+t\in C_0+C_1\), proving the required containment.
\end{proof}
\begin{example}
The five-element diamond \(M_3\) is Arguesian but not distributive. Realize it as the sublattice consisting of zero, the whole space \(k^2\), and the three lines \(k(1,0)\), \(k(0,1)\), \(k(1,1)\). The preceding result applies to the subspace lattice, and its implication remains valid in every sublattice. The failure of distributivity is shown in the \PMlinkname{modular lattice}{ModularLattice} entry.
\end{example}
\begin{remark}
The standard hierarchy is
\[
\text{distributive}\quad\Longrightarrow\quad\text{Arguesian}\quad\Longrightarrow\quad\text{modular}.
\]
These implications are discussed in Nation's notes, Chapter 4; their general proofs are not supplied here. Neither converse holds in general. Non-Desarguesian projective planes provide modular lattices that fail the Arguesian law. The pentagon \(N_5\) is not even modular, so cannot be Arguesian. Normal-subgroup lattices are also Arguesian, as explained by Nation's Theorem 4.6 and the discussion following it.
\end{remark}
The classification 06C05 groups this topic with \PMlinkname{modular lattices}{ModularLattice}. See also \PMlinkname{distributive lattices}{DistributiveLattice}.
""")
E['reference']=('J. B. Nation','Notes on Lattice Theory, Chapter 4, Arguesian law and Theorem 4.6','https://math.hawaii.edu/~jb/lattice2017.pdf')
E['escapes']+=['lattice','lattices','modular','distributive','line','lines','point','vertices','intersection','join','meet','normal','subspace','subspaces','geometric','configuration','context','theory','diamond','plane','planes']

def apply(path):
    with sqlite3.connect(path) as c:
        c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON')
        if not c.execute('SELECT 1 FROM math_concepts WHERE slug=?',(E['slug'],)).fetchone():
            for term in [E['title'],*E['synonyms']]:
                assert not c.execute('''SELECT title FROM math_concepts WHERE lower(title)=lower(?)
                    UNION SELECT synonym_text FROM math_synonyms WHERE lower(synonym_text)=lower(?)
                    UNION SELECT defined_term FROM math_definitions WHERE lower(defined_term)=lower(?)''',(term,term,term)).fetchone(),term
            create_math_concept(c.cursor(),E['canonical'],E['slug'],E['title'],datetime.now().strftime('%Y-%m-%d %H:%M:%S'),'CWoo',source(E),1,E['classifications'],document_types(E),E['synonyms'],[],[])
        for slug in E['related']:relate(c,E['slug'],slug);relate(c,slug,E['slug'])
        d=fetch_public_math_concept_detail(c.cursor(),E['slug'])
        assert d['cleaned_tex']==source(E) and d['owner']=='CWoo'
        assert set(d['types'])==set(document_types(E))
        assert {r['code'] for r in d['classifications']}=={'06C05'}
        pat=r'\\\(.*?\\\)|\\\[.*?\\\]'
        assert re.findall(pat,d['cleaned_tex'],re.S)==re.findall(pat,d['display_tex'],re.S)
        for term in [E['title'],*E['synonyms']]:assert E['slug'] in links(apply_math_autolinker(-1,term,c.cursor())),term
        assert 'modular-lattice' in links(d['display_tex'])
        assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        assert not c.execute('PRAGMA foreign_key_check').fetchall()
        print('Verified',d['id'],E['slug'])

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--db',type=Path,default=SRC.parent/'portfolio.db')
    args=p.parse_args()
    if not args.db.is_file():raise FileNotFoundError(args.db)
    apply(args.db)
