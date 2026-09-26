"""Partial derivatives, extracted Cauchy-Riemann criterion, and Laplace's equation."""
import argparse
from pathlib import Path
import sqlite3
from datetime import datetime
import re
import add_number_theory_and_geometry_foundations as base
from services.math.concept_render_service import render_tex_reusing_existing_diagrams
from services.math.concept_metadata_service import _attach_types

base.ENTRIES.clear()
REF=('Jiri Lebl','Guide to Cultivating Complex Analysis, Chapters 2 and 7',
     'https://www.jirka.org/ca/')

def add(*args):
    base.add(*args,REF)
    base.ENTRIES[-1]['escapes'] += ['partial','derivative','derivatives','mixed',
        'continuous','smooth','harmonic','real','complex','domain','domains',
        'open','closed','connected','conjugate','conjugation','gradient','matrix',
        'rows','integral','direction','directions','constant','constants','order',
        'normal','field','fields','criterion','restriction','extension','interval',
        'rectangle','path','linear function']

add('partial derivative','partial-derivative','PartialDerivative','26B05',
    ['partial derivatives','partial differentiation'], ['mixed partial derivative'],
    'differentiable-function smooth-function cauchy-riemann-equations laplace-equation',r"""
\begin{definition}
Let \(f:U\to\mathbb R\), where \(U\subseteq\mathbb R^n\) is open,
and let \(e_i\) be the \(i\)-th coordinate unit vector. The
\emph{partial derivative} with respect to \(x_i\) at \(a\in U\) is
\[
\frac{\partial f}{\partial x_i}(a)=\lim_{t\to0}\frac{f(a+te_i)-f(a)}{t},
\]
if this finite limit exists. It differentiates in one coordinate while
holding the others fixed. Common notations are \(\partial_i f\),
\(f_{x_i}\), and \(\partial f/\partial x_i\).
For vector-valued functions, take partial derivatives component by component.
\end{definition}
\begin{example}
For \(f(x,y)=x^2y+\sin y\), we have \(f_x=2xy\) and
\(f_y=x^2+\cos y\). For example, \(f_x(1,0)=0\), whereas
\(f_y(1,0)=2\): the two coordinate rates of change are different.
\end{example}
\begin{definition}
Higher partial derivatives are obtained by differentiating repeatedly.
A \emph{mixed partial derivative} involves more than one coordinate.
We use \(f_{xy}=\partial_y(\partial_x f)\): first differentiate in \(x\),
then in \(y\). Thus \(f_{xy}=2x=f_{yx}\) for the example above.
\end{definition}
If the second partial derivatives are continuous on a neighborhood,
the equality-of-mixed-partials theorem gives \(f_{xy}=f_{yx}\) there.
The regularity hypothesis matters; mixed partials need not agree merely
because both exist at an isolated point.

If \(f\) is [[differentiable-function|totally differentiable]] at \(a\),
then all its partial derivatives exist there and
\(Df(a)h=\sum_i\partial_i f(a)h_i\). The converse fails:
define \(g(0,0)=0\), and \(g(x,y)=xy/(x^2+y^2)\) elsewhere.
Both partials at the origin are zero, but \(g(t,t)=1/2\) for \(t\ne0\),
so \(g\) is not even continuous there. Continuous first partial
derivatives on a neighborhood are sufficient for total differentiability.

Partial derivatives depend on the chosen coordinates. On a manifold
they are taken in a coordinate chart and transformed by the chain rule.
The [[cauchy-riemann-equations|Cauchy-Riemann equations]] relate the
first partials of a complex function's real and imaginary parts;
[[laplace-equation|Laplace's equation]] involves second partials.
""")
base.ENTRIES[-1]['reference']=('Jiri Lebl','Basic Analysis II, Chapter 8: Several Variables and Differentiation',
                            'https://www.jirka.org/ra/html/ra.html')

add('Cauchy-Riemann equations','cauchy-riemann-equations','CauchyRiemannEquations',
    '30A05', ['Cauchy–Riemann equations','Cauchy Riemann equations'],
    ['harmonic conjugate'],
    'holomorphic-function partial-derivative differentiable-function laplace-equation analytic-continuation',r"""
\begin{definition}
For \(f(x+iy)=u(x,y)+iv(x,y)\), the \emph{Cauchy-Riemann equations} are
\[
u_x=v_y,\qquad u_y=-v_x.
\]
The subscripts denote [[partial-derivative|partial derivatives]]. These
first-order equations express the compatibility required for a real
derivative to be multiplication by a complex number.
\end{definition}
\begin{proposition}
If \(f=u+iv\) is differentiable at \((a,b)\) as a real map
\(\mathbb R^2\to\mathbb R^2\), it is complex differentiable at
\(a+ib\) if and only if the Cauchy-Riemann equations hold there.
In this case \(f'=u_x+i v_x\).
\end{proposition}
\begin{proof}
Multiplication by \(\alpha+i\beta\) has real matrix with rows
\((\alpha,-\beta)\) and \((\beta,\alpha)\). The real derivative of
\(f\) has rows \((u_x,u_y)\) and \((v_x,v_y)\), so it has this form
exactly when the equations hold. The real differentiability remainder
is \(o(|h|)\); dividing it by \(h\) proves complex differentiability.
Conversely, a complex derivative yields this real linear approximation.
\end{proof}
Consequently, if \(u,v\) are \(C^1\) on an open set, their combination
\(u+iv\) is [[holomorphic-function|holomorphic]] exactly when the
equations hold everywhere on that set. Existence of partial derivatives
alone is not the real differentiability hypothesis of the proposition.
\begin{example}
For \(f(z)=z^2\), take \(u=x^2-y^2\) and \(v=2xy\). Then
\(u_x=2x=v_y\) and \(u_y=-2y=-v_x\). By contrast, for
\(f(z)=\overline z\), we have \(u=x\), \(v=-y\), so \(u_x=1\ne-1=v_y\).
\end{example}
\section*{Relation to Laplace's equation}
\begin{proposition}
The real and imaginary parts of a holomorphic function are harmonic:
they satisfy [[laplace-equation|Laplace's equation]],
\(u_{xx}+u_{yy}=0\) and \(v_{xx}+v_{yy}=0\).
More generally, the same conclusion holds for any \(C^2\) pair
\(u,v\) satisfying the Cauchy-Riemann equations.
\end{proposition}
\begin{proof}
Holomorphic functions are analytic, hence their real and imaginary
parts are smooth. Differentiate the Cauchy-Riemann equations to obtain
\[
u_{xx}+u_{yy}=v_{yx}-v_{xy}=0,\qquad
v_{xx}+v_{yy}=-u_{yx}+u_{xy}=0.
\]
Equality of mixed partial derivatives follows from the \(C^2\) hypothesis.
\end{proof}
The converse with an arbitrary pair of harmonic functions is false:
\(u=x\), \(v=0\) are both harmonic, but \(u_x=1\ne0=v_y\).
They must satisfy the first-order compatibility equations as a pair.
\begin{definition}
A \emph{harmonic conjugate} of a real harmonic function \(u\) is a
real function \(v\) such that \(u+iv\) is holomorphic. On a connected
domain a harmonic conjugate, when it exists, is unique up to a real constant,
since the equations prescribe both of its first partial derivatives.
\end{definition}
\begin{proposition}
Every \(C^2\) harmonic function has a harmonic conjugate locally.
\end{proposition}
\begin{proof}
Work in a rectangle about \((a,b)\) inside the domain and define
\[
v(x,y)=-\int_a^x u_y(s,b)\,ds+\int_b^y u_x(x,t)\,dt.
\]
Then \(v_y=u_x\). Differentiating in \(x\) and using \(u_{xx}=-u_{yy}\)
gives
\[
v_x=-u_y(x,b)+\int_b^y u_{xx}(x,t)\,dt=-u_y(x,y).
\]
Thus the Cauchy-Riemann equations hold, and the \(C^1\) criterion applies.
\end{proof}
On a simply connected plane domain a harmonic conjugate exists globally;
one integrates the closed differential form \(-u_y\,dx+u_x\,dy\), whose
integrals are path independent there. On a domain with holes there can
be an obstruction. For \(u(z)=\log|z|\) on the punctured plane, a local
conjugate is the argument, which increases by \(2\pi\) around the unit
circle. It cannot be a single-valued global conjugate, exactly the
logarithm phenomenon in [[analytic-continuation|analytic continuation]].
""")

add("Laplace's equation",'laplace-equation','LaplaceEquation','35J05',
    ['Laplace equation'], ['Laplacian','harmonic function','harmonic functions'],
    'partial-derivative cauchy-riemann-equations holomorphic-function',r"""
\begin{definition}
For a twice continuously differentiable real function \(u\) on an
open set \(U\subseteq\mathbb R^n\), its \emph{Laplacian} is
\[
\Delta u=\sum_{j=1}^n\frac{\partial^2u}{\partial x_j^2}.
\]
\emph{Laplace's equation} is \(\Delta u=0\). A \(C^2\) function satisfying
this equation throughout \(U\) is called \emph{harmonic} on \(U\).
This entry uses the classical Euclidean Laplacian and classical solutions.
\end{definition}
In two dimensions the equation is \(u_{xx}+u_{yy}=0\); in three it is
\(u_{xx}+u_{yy}+u_{zz}=0\). The individual second derivatives need not
vanish: their sum must vanish.
\begin{example}
Every affine linear function is harmonic. On \(\mathbb R^2\), the
functions \(x^2-y^2\) and \(2xy\) are harmonic, whereas
\(x^2+y^2\) is not, since its Laplacian is 4.
The function \(\log\sqrt{x^2+y^2}\) is harmonic away from the origin:
its second derivatives are \((y^2-x^2)/(x^2+y^2)^2\) and
\((x^2-y^2)/(x^2+y^2)^2\), whose sum is zero.
\end{example}
The [[cauchy-riemann-equations|Cauchy-Riemann equations]] imply that
the real and imaginary parts of a holomorphic function are harmonic.
That entry proves the implication and explains how a planar harmonic
function can locally be completed by a harmonic conjugate to form a
holomorphic function. Being harmonic individually does not make an
arbitrary pair satisfy the Cauchy-Riemann equations.

Laplace's equation occurs in potential theory and stationary heat
problems without sources. Prescribing values on the boundary leads to
a Dirichlet boundary-value problem. It is a differential equation,
not the Laplace transform; these share a name but are different constructions.
""")

# The renderer normalizes thin spaces; avoid source/render differences.
for e in base.ENTRIES:e['body']=e['body'].replace(r'\,',' ')

def apply(path):
    # Transfer the embedded term from its old owner to the standalone title.
    with sqlite3.connect(path) as c:
        prior=c.execute('''SELECT id,concept_id,defined_term FROM math_definitions
            WHERE defined_term='Cauchy-Riemann equations' AND concept_id=
            (SELECT id FROM math_concepts WHERE slug='holomorphic-function')''').fetchall()
        for row in prior:c.execute('DELETE FROM math_definitions WHERE id=?',(row[0],))
    try:
        base.apply(path)
    except Exception:
        with sqlite3.connect(path) as c:
            c.executemany('INSERT INTO math_definitions(id,concept_id,defined_term) VALUES (?,?,?)',prior)
        raise
    with sqlite3.connect(path) as c:
        c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON')
        d=base.fetch_public_math_concept_detail(c.cursor(),'holomorphic-function')
        tex=d['cleaned_tex']
        if r'\PMlinkname{Cauchy-Riemann equations}{CauchyRiemannEquations}' not in tex:
            start=tex.index(r'\begin{proposition}')
            end=tex.index(r'\end{proof}',start)+len(r'\end{proof}')
            tex=tex[:start]+r"""
The \PMlinkname{Cauchy-Riemann equations}{CauchyRiemannEquations} entry
contains the precise criterion for complex differentiability, its proof,
and its relationship with Laplace's equation. For \(f=u+iv\) real
differentiable at the point, the criterion is \(u_x=v_y\), \(u_y=-v_x\).
"""+tex[end:]
            rendered=render_tex_reusing_existing_diagrams(d['id'],tex,c.cursor())
            c.execute('UPDATE math_concepts SET cleaned_tex=?,rendered_tex=?,updated_at=? WHERE id=?',
                (tex,rendered,datetime.now().strftime('%Y-%m-%d %H:%M:%S'),d['id']))
            c.execute('DELETE FROM math_concept_types WHERE concept_id=?',(d['id'],))
            _attach_types(c.cursor(),d['id'],base.document_types({'body':tex}))
        base.relate(c,'holomorphic-function','cauchy-riemann-equations')
        base.relate(c,'cauchy-riemann-equations','holomorphic-function')
        d=base.fetch_public_math_concept_detail(c.cursor(),'holomorphic-function')
        assert 'cauchy-riemann-equations' in base.links(d['display_tex'])
        assert r'\begin{proof}' not in d['cleaned_tex']
        assert set(d['types'])==set(base.document_types({'body':tex}))
        assert not c.execute('PRAGMA foreign_key_check').fetchall()
        print('Verified criterion extraction and holomorphic-function metadata')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--db',type=Path,default=base.SRC.parent/'portfolio.db')
    args=p.parse_args()
    if not args.db.is_file():raise FileNotFoundError(args.db)
    apply(args.db)
