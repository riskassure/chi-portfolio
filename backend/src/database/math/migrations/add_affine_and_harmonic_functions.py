"""Affine linear functions and a standalone home for harmonic functions."""
import argparse
from pathlib import Path
import sqlite3
from datetime import datetime
import add_number_theory_and_geometry_foundations as base
from services.math.concept_render_service import render_tex_reusing_existing_diagrams

base.ENTRIES.clear()
base.add('affine linear function','affine-linear-function','AffineLinearFunction','15A04',
    ['affine linear functions','affine-linear function'], [],
    'linear-transformation affine-combination harmonic-function',r"""
\begin{definition}
For vector spaces \(V,W\) over a field \(k\), an \emph{affine linear function}
is a map \(f:V\to W\) of the form \(f(v)=T(v)+b\), where \(T:V\to W\)
is linear and \(b\in W\) is fixed. For \(k^n\to k^m\), this becomes
\(f(x)=Ax+b\). In the scalar real case it is
\(f(x_1,\ldots,x_n)=a_1x_1+\cdots+a_nx_n+b\).
\end{definition}
Here linear means linear in the vector-space sense, not the incidence-geometric
meaning used in the collection's separately titled linear function entry.
The offset \(b=f(0)\) distinguishes affine linear maps from linear maps:
an affine linear map is linear exactly when \(b=0\).
\begin{example}
The function \(f(x)=2x+3\) is affine linear but not linear, since \(f(0)=3\).
The function \(g(x,y)=2x-y+4\) is another example. Constant functions
are affine linear with zero linear part. The function \(x^2\) is not
affine linear on \(\mathbb R\).
\end{example}
\begin{proposition}
An affine linear function preserves affine combinations:
\[
f\left(\sum_i\lambda_i v_i\right)=\sum_i\lambda_i f(v_i)
\quad\text{whenever}\quad\sum_i\lambda_i=1.
\]
\end{proposition}
\begin{proof}
Linearity gives \(T(\sum_i\lambda_i v_i)=\sum_i\lambda_iT(v_i)\).
The constant contribution on the right is \((\sum_i\lambda_i)b=b\),
which is the constant contribution on the left.
\end{proof}
For real affine linear functions the first partial derivatives are constant
and all second partial derivatives vanish. Hence scalar affine linear
functions are [[harmonic-function|harmonic]]. They are also smooth and
real-analytic. The derivative of \(x\mapsto Ax+b\) is the same linear
map \(A\) at every point; the derivative does not retain the offset \(b\).
""",('Jiri Lebl','Basic Analysis II, linear algebra and differentiation',
        'https://www.jirka.org/ra/html/ra.html'))
base.add('harmonic function','harmonic-function','HarmonicFunction','31A05 35J05',
    ['harmonic functions'], [],
    'laplace-equation cauchy-riemann-equations holomorphic-function affine-linear-function partial-derivative',r"""
\begin{definition}
A real-valued function \(u\) on an open set \(U\subseteq\mathbb R^n\)
is \emph{harmonic} if it is twice continuously differentiable and satisfies
[[laplace-equation|Laplace's equation]] everywhere on \(U\):
\[
\Delta u=\sum_{j=1}^n\frac{\partial^2u}{\partial x_j^2}=0.
\]
This is the classical Euclidean definition. It requires the sum of the
pure second partial derivatives to vanish, not each derivative separately.
\end{definition}
\begin{example}
Every [[affine-linear-function|affine linear function]] is harmonic.
In two variables \(x^2-y^2\) is harmonic, since its two pure second
partials are 2 and -2. The function \(x^2+y^2\) is not harmonic:
its Laplacian is 4. The function \(\log\sqrt{x^2+y^2}\) is harmonic
on the punctured plane, as calculated in the Laplace's equation entry;
it is not defined at the origin, so that point is excluded from its domain.
\end{example}
\begin{proposition}
Real linear combinations of harmonic functions on a common open set
are harmonic. Products need not be harmonic.
\end{proposition}
\begin{proof}
Differentiation is linear, so
\(\Delta(au+bv)=a\Delta u+b\Delta v=0\) for constant real \(a,b\).
For failure under multiplication, \(u(x,y)=x\) is harmonic but
\(u^2=x^2\) has Laplacian 2.
\end{proof}
In the plane, the real and imaginary parts of a holomorphic function
are harmonic. Conversely, a harmonic function locally has a harmonic
conjugate \(v\) making \(u+iv\) holomorphic. The
[[cauchy-riemann-equations|Cauchy-Riemann equations]] entry proves these
facts and explains the obstruction to a global conjugate on a domain
with holes. Two independently chosen harmonic functions need not be
the real and imaginary parts of one holomorphic function.

A real harmonic function is not necessarily holomorphic when regarded
as a complex-valued function. For example \(u(x,y)=x\) is harmonic,
but \(z\mapsto\operatorname{Re}z\) is not holomorphic. Harmonicity is a
second-order real differential equation; holomorphicity is a complex
differentiability condition. The word harmonic here is unrelated to
convergence of the harmonic series.
""",('Jiri Lebl','Guide to Cultivating Complex Analysis, Chapter 7: Harmonic Functions',
        'https://www.jirka.org/ca/'))
for e in base.ENTRIES:
    e['escapes'] += ['linear function','linear functions','linear','affine','harmonic',
        'domain','open','real','complex','constant','partial','derivative','offset',
        'normal','field','conjugate','second','first']

def apply(path):
    with sqlite3.connect(path) as c:
        prior=c.execute('''SELECT id,concept_id,defined_term FROM math_definitions
            WHERE defined_term IN ('harmonic function','harmonic functions') AND concept_id=
            (SELECT id FROM math_concepts WHERE slug='laplace-equation')''').fetchall()
        for row in prior:c.execute('DELETE FROM math_definitions WHERE id=?',(row[0],))
    try:base.apply(path)
    except Exception:
        with sqlite3.connect(path) as c:
            c.executemany('INSERT INTO math_definitions(id,concept_id,defined_term) VALUES (?,?,?)',prior)
        raise
    with sqlite3.connect(path) as c:
        c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON')
        d=base.fetch_public_math_concept_detail(c.cursor(),'laplace-equation')
        tex=d['cleaned_tex'].replace(r'\emph{harmonic}',r'\PMlinkname{harmonic}{HarmonicFunction}')
        tex=tex.replace('Every affine linear function',r'Every \PMlinkname{affine linear function}{AffineLinearFunction}')
        if tex!=d['cleaned_tex']:
            rendered=render_tex_reusing_existing_diagrams(d['id'],tex,c.cursor())
            c.execute('UPDATE math_concepts SET cleaned_tex=?,rendered_tex=?,updated_at=? WHERE id=?',
                (tex,rendered,datetime.now().strftime('%Y-%m-%d %H:%M:%S'),d['id']))
        display=base.fetch_public_math_concept_detail(c.cursor(),'laplace-equation')['display_tex']
        for slug in ['harmonic-function','affine-linear-function']:assert slug in base.links(display)
        assert not c.execute('PRAGMA foreign_key_check').fetchall()

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--db',type=Path,default=base.SRC.parent/'portfolio.db')
    args=p.parse_args()
    if not args.db.is_file():raise FileNotFoundError(args.db)
    apply(args.db)
