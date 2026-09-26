"""Make both strict steps in the lattice hierarchy explicit."""
import argparse
from datetime import datetime
from pathlib import Path
import re
import sqlite3
from add_desarguesian_lattice import E, SRC, source, fetch_public_math_concept_detail, relate, links
from services.math.concept_render_service import render_tex_reusing_existing_diagrams

EXAMPLE=r"""
\section*{Modular but not Arguesian: the projective Moulton plane}
\begin{example}
Start with the \PMlinkname{Moulton plane}{MoultonPlane}, the affine plane with bent lines described in its own entry. Form its projective completion \(P\): add one point for each parallel class of affine lines, put that point on every line of its class, and add a line at infinity containing all the new points.

Define \(L(P)\) to consist of a bottom element \(0\), all projective points, all projective lines, and a top element \(1\). Order a point below a line exactly when they are incident, with \(0\) below everything and \(1\) above everything. Distinct points join to their unique joining line; distinct lines meet at their unique intersection point. A point and a nonincident line have meet \(0\) and join \(1\). These rules specify the lattice completely.
\end{example}
\begin{proposition}
The lattice \(L(P)\) is modular but is not Arguesian.
\end{proposition}
\begin{proof}
We first prove modularity for the incidence lattice of any projective plane. In the modular identity with \(x\le z\), the cases \(x=0\), \(z=1\), or \(x=z\) are immediate. The only other case has \(x\) a point on the line \(z\). For \(y\) a point on \(z\), both sides equal \(x\vee y\); for a point off \(z\), both equal \(x\). For \(y=z\), both equal \(z\). If \(y\) is a different line through \(x\), both sides equal \(x\). If \(y\) is a line not through \(x\), its intersection with \(z\) is a point different from \(x\), so both sides equal \(z\). The remaining choices \(y=0,1\) are immediate. This exhausts the lattice elements.

The projective completion of the Moulton plane fails Desargues' theorem. Thus it contains two nondegenerate triangles with concurrent corresponding-vertex lines but noncollinear corresponding-side intersections. Label their vertices \(a_i,b_i\). Concurrency gives
\[
(a_0\vee b_0)\wedge(a_1\vee b_1)\le a_2\vee b_2,
\]
whereas noncollinearity gives \(c_2\not\le c_0\vee c_1\), with the \(c_i\) defined above. Hence the Arguesian implication fails. The geometric failure of Desargues' theorem is the classical Moulton counterexample; it is illustrated in the linked entry and established in the reference below.
\end{proof}
This example uses the projective completion, not just the affine points and lines: in an affine plane two parallel lines have no intersection point, and the projective-plane modularity argument would not apply.
\begin{thebibliography}{9}
\bibitem{moulton} F. R. Moulton, \PMlinkexternal{A Simple Non-Desarguesian Plane Geometry (1902)}{https://www.ime.usp.br/~pleite/pub/artigos/moulton/a_simple_non-desarguesian_geometry.pdf}.
\end{thebibliography}
"""

def apply(path):
    old=source(E)
    e=dict(E)
    e['body']=E['body'].replace(
        'The five-element diamond',r'\textbf{Arguesian but not distributive.} The five-element diamond',1)
    e['body']=e['body'].replace(
        'The failure of distributivity is shown in the '+r'\PMlinkname{modular lattice}{ModularLattice} entry.',
        r'Explicitly, label the three middle elements \(a,b,c\). Their pairwise meets are \(0\) and pairwise joins are \(1\), so \(a\wedge(b\vee c)=a\ne0=(a\wedge b)\vee(a\wedge c)\). Thus distributivity fails, while the subspace realization proves the Arguesian law.')
    e['body']+='\n'+EXAMPLE
    tex=source(e)
    with sqlite3.connect(path) as c:
        c.row_factory=sqlite3.Row
        d=fetch_public_math_concept_detail(c.cursor(),E['slug'])
        assert d['cleaned_tex'] in (old,tex),'Entry changed since this migration was written'
        if d['cleaned_tex']!=tex:
            rendered=render_tex_reusing_existing_diagrams(d['id'],tex,c.cursor())
            c.execute('UPDATE math_concepts SET cleaned_tex=?,rendered_tex=?,updated_at=? WHERE id=?',
                (tex,rendered,datetime.now().strftime('%Y-%m-%d %H:%M:%S'),d['id']))
        relate(c,E['slug'],'moulton-plane');relate(c,'moulton-plane',E['slug'])
        d=fetch_public_math_concept_detail(c.cursor(),E['slug'])
        pat=r'\\\(.*?\\\)|\\\[.*?\\\]'
        assert re.findall(pat,tex,re.S)==re.findall(pat,d['display_tex'],re.S)
        assert 'moulton-plane' in links(d['display_tex'])
        assert d['display_tex'].count('class="math-env math-env-proof"')==2
        assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        print('Verified both strict-hierarchy examples and Moulton link')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--db',type=Path,default=SRC.parent/'portfolio.db')
    args=p.parse_args()
    if not args.db.is_file():raise FileNotFoundError(args.db)
    apply(args.db)
