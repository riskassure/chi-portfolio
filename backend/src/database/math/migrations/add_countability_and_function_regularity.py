"""First countability, Alexandroff spaces, function regularity and chart compatibility."""
import argparse
from pathlib import Path
import sqlite3
from datetime import datetime
import add_number_theory_and_geometry_foundations as base
from services.math.concept_render_service import render_tex_reusing_existing_diagrams

base.ENTRIES.clear()
TOPO=('Allen Hatcher','Notes on Introductory Point-Set Topology',
      'https://pi.math.cornell.edu/~hatcher/Top/TopNotes.pdf')
ANALYSIS=('Jiri Lebl','Basic Analysis I and II, differentiation and analytic functions',
          'https://www.jirka.org/ra/html/ra.html')

def add(*args):
    base.add(*args)
    base.ENTRIES[-1]['escapes'] += ['basis','neighborhood','open','closed','closure',
        'countable','sequence','limit','continuous','continuity','differentiable',
        'analytic','smooth','positive','negative','upper','lower','order','discrete',
        'indiscrete','norm','bounded','derivative','language','assumption','useful',
        'extension','relation','field','fields','symmetric','partial','total',
        'reflexive','converge','open interval']

add('first countability','first-countability','FirstCountability','54D70',
    ['first-countable space','first countable space','first countable'], [],
    'topological-space second-countability properties-of-first-countability first-countable-implies-compactly-generated alexandroff-space',r"""
\begin{definition}
A space \(X\) is \emph{first-countable at} \(x\) if there is a countable
family \(\mathcal B_x\) of open sets containing \(x\) such that every
neighborhood of \(x\) contains a member of \(\mathcal B_x\). Such a family
is a countable local basis. The space is \emph{first-countable} if this
holds at every point. Countable includes finite.
\end{definition}
Unlike [[second-countability|second countability]], this does not require
one countable basis for the whole topology. The union of the local bases
over all points can be uncountable.
\begin{example}
Every metric space is first-countable: the balls \(B(x,1/n)\), \(n\ge1\),
form a local basis at \(x\). Every discrete space has the one-member local
basis \(\{\{x\}\}\) at each point. An uncountable discrete space is not
second-countable, since any basis for its topology must contain every singleton.
\end{example}
\begin{proposition}
In a first-countable space, \(x\in\overline A\) if and only if some sequence
of points of \(A\) converges to \(x\).
\end{proposition}
\begin{proof}
List a local basis as \(B_1,B_2,\ldots\), repeating members when it is finite.
Set \(V_n=B_1\cap\cdots\cap B_n\). If \(x\in\overline A\), choose
\(a_n\in V_n\cap A\). Every neighborhood of \(x\) contains some \(B_j\)
and hence all \(a_n\) for \(n\ge j\), proving convergence. Conversely,
if a sequence in \(A\) converges to \(x\), every neighborhood meets \(A\),
which means \(x\in\overline A\).
\end{proof}
\begin{example}
An uncountable set with the cocountable topology is not first-countable.
Here the nonempty open sets have countable complements. If \(U_n\) were
a local basis at \(x\), the complement of \(\bigcap_nU_n\) would be countable.
Choose \(y\ne x\) in that intersection. The open neighborhood
\(X\setminus\{y\}\) of \(x\) contains none of the \(U_n\), a contradiction.
\end{example}
See [[properties-of-first-countability|properties of first countability]]
for consequences concerning closed sets and continuity. First countability
alone imposes no Hausdorff condition; limits need not be unique.
""",TOPO)

add('Alexandroff space','alexandroff-space','AlexandroffSpace','54A05',
    ['Alexandrov space','Alexandroff topology','Alexandrov topology'], [],
    'topological-space first-countability',r"""
\begin{definition}
An \emph{Alexandroff space} (also spelled Alexandrov) is a topological
space in which every intersection of open sets is open, including infinite
intersections. The empty intersection is the whole space.
\end{definition}
This strengthens the usual topology axiom, which requires only finite intersections.
Here the term refers to general topology, not to metric Alexandrov spaces
with curvature bounds or to the Alexandroff one-point compactification.
\begin{proposition}
A space is Alexandroff if and only if each point \(x\) has a smallest
open neighborhood \(U_x\).
\end{proposition}
\begin{proof}
In an Alexandroff space, intersect all open sets containing \(x\); their
intersection is the required open \(U_x\). Conversely, let \(V\) be any
intersection of open sets. For each \(x\in V\), the set \(U_x\) lies in
every member of the intersection. Hence \(V=\bigcup_{x\in V}U_x\) is open.
\end{proof}
In particular every Alexandroff space is [[first-countability|first-countable]],
using the single open set \(U_x\) as a local basis at \(x\).
\begin{example}
Every finite topological space is Alexandroff, since an arbitrary family
contains only finitely many distinct open sets. Discrete and indiscrete
spaces of any cardinality are also examples. The usual real line is not:
\(\bigcap_{n\ge1}(-1/n,1/n)=\{0\}\) is not open.
\end{example}
\section*{Relation with preorders}
Use the convention \(x\preceq y\) when every open set containing \(x\)
also contains \(y\), equivalently \(y\in U_x\). This relation is reflexive
and transitive. The open sets are exactly the upper sets: sets \(A\) such
that \(x\in A\) and \(x\preceq y\) imply \(y\in A\). Indeed, open sets
have this property by definition; conversely an upper set is the union
of the \(U_x\) for its points. Starting with any preorder and declaring
all upper sets open recovers an Alexandroff topology.

For instance, \(0\preceq1\) on \(\{0,1\}\) yields the open sets
\(\varnothing,\{1\},\{0,1\}\). The space is \(T_0\) precisely when
the preorder is antisymmetric; \(T_0\) means distinct points can be
distinguished by membership in some open set. If the space is \(T_1\)
(all singletons closed), then \(U_x=\{x\}\), so it is discrete.
Some sources use the opposite order convention; specifying which sets
are upper avoids this ambiguity.
""",('J. Peter May','Notes on finite spaces and preorders, July 2, 2015',
        'https://math.uchicago.edu/~may/REUDOCS/07-02-2015.pdf'))

add('differentiable function','differentiable-function','DifferentiableFunction','26A24 26B05',
    ['differentiable functions','differentiable map'], ['total derivative'],
    'smooth-function analytic-function continuity-of-maps-between-topological-spaces linear-transformation',r"""
\begin{definition}
Let \(U\subseteq\mathbb R^n\) be open. A function \(f:U\to\mathbb R^m\)
is \emph{differentiable at} \(a\in U\) if there is a linear map
\(Df(a):\mathbb R^n\to\mathbb R^m\) such that
\[
\lim_{h\to0,\quad h\ne0}\frac{\|f(a+h)-f(a)-Df(a)h\|}{\|h\|}=0.
\]
This linear map is its total derivative. The function is differentiable
on \(U\) if it is differentiable at every point of \(U\).
\end{definition}
We use real differentiability here. For \(n=m=1\), this is equivalent
to existence of the finite limit \(f'(a)=\lim_{h\to0}(f(a+h)-f(a))/h\).
In higher dimensions, when the derivative exists, its matrix is the
Jacobian of the partial derivatives. The existence of all partial
derivatives alone does not imply differentiability.
\begin{proposition}
Differentiability at a point implies continuity there.
\end{proposition}
\begin{proof}
The defining approximation gives
\(f(a+h)-f(a)=Df(a)h+r(h)\), with \(\|r(h)\|/\|h\|\to0\).
Both terms tend to zero, since a linear map between finite-dimensional
spaces is continuous. Hence \(f(a+h)\to f(a)\).
\end{proof}
\begin{example}
The function \(x^2\) has derivative \(2x\); \(|x|\) is continuous but
not differentiable at zero, because its two one-sided difference quotients
are 1 and -1. In two variables, define \(f(0,0)=0\) and
\(f(x,y)=xy/(x^2+y^2)\) elsewhere. Both partial derivatives at the origin
are zero, but \(f(t,t)=1/2\) for \(t\ne0\), so it is not even continuous there.
\end{example}
\begin{example}
Differentiable need not mean continuously differentiable. Set \(g(0)=0\)
and \(g(x)=x^2\sin(1/x)\) for \(x\ne0\). Then \(g'(0)=0\), whereas
\(g'(x)=2x\sin(1/x)-\cos(1/x)\) away from zero, which does not converge
to zero as \(x\to0\).
\end{example}
A function is \(C^1\) if it is differentiable and its derivative varies
continuously. Higher regularity leads to [[smooth-function|smooth functions]].
Complex differentiability is stronger than differentiability of the
underlying map \(\mathbb R^2\to\mathbb R^2\); see [[analytic-function|analytic functions]].
""",ANALYSIS)

add('smooth function','smooth-function','SmoothFunction','26B05',
    ['smooth functions','infinitely differentiable function'], [],
    'differentiable-function analytic-function smooth-map-between-manifolds smooth-manifold',r"""
\begin{definition}
For open \(U\subseteq\mathbb R^n\), a function \(f:U\to\mathbb R^m\)
is of class \(C^k\), for an integer \(k\ge0\), if all partial derivatives
of its components of order at most \(k\) exist and are continuous.
Class \(C^0\) means continuous. It is \emph{smooth}, or \(C^\infty\),
if it is \(C^k\) for every finite \(k\).
\end{definition}
Thus smooth means derivatives of every order, not merely once differentiable
or visually without corners. Polynomial functions, exponential functions,
and sine and cosine are smooth. Compositions, sums and products of smooth
functions are smooth on their domains, by repeated chain and product rules.
\begin{example}
The function \(x|x|\) is \(C^1\) on \(\mathbb R\), with derivative
\(2|x|\), but is not twice differentiable at zero. Thus even \(C^1\)
regularity is weaker than smoothness.
\end{example}
\begin{proposition}
Define \(\phi(x)=e^{-1/x^2}\) for \(x\ne0\), and \(\phi(0)=0\).
Then \(\phi\) is smooth and \(\phi^{(k)}(0)=0\) for every \(k\ge0\).
\end{proposition}
\begin{proof}
Away from zero, repeated differentiation expresses every derivative as
\(P_k(1/x)e^{-1/x^2}\), with \(P_k\) a polynomial. For every nonnegative
integer \(N\), \(|x|^{-N}e^{-1/x^2}\to0\) as \(x\to0\): put
\(t=1/x^2\) and use that \(t^{N/2}e^{-t}\to0\).
Inductively extend each derivative to zero with value zero. The displayed
limit proves its continuity; applying it also to the difference quotient
divided by \(x\) proves differentiability there with derivative zero.
This proves the assertion at every order.
\end{proof}
This example is not [[analytic-function|analytic]] at zero: its Taylor
series there is identically zero, but the function is positive elsewhere.

On a smooth manifold, a real function is smooth when its expression in
each smooth coordinate chart is smooth in this Euclidean sense.
More generally, smooth maps between manifolds are defined using source
and target charts in the [[smooth-map-between-manifolds|smooth map entry]].
Smooth compatibility of charts makes this definition independent of
the particular charts chosen.
""",ANALYSIS)

add('analytic function','analytic-function','AnalyticFunction','26E05 30A05',
    ['analytic functions','real-analytic function','real analytic function','complex-analytic function'], [],
    'smooth-function differentiable-function',r"""
\begin{definition}
A function on an open interval of \(\mathbb R\) is \emph{real-analytic}
if for each point \(a\) there are \(r>0\) and coefficients \(c_k\) such that
\[
f(x)=\sum_{k=0}^{\infty}c_k(x-a)^k\qquad (|x-a|<r),
\]
with the interval contained in its domain and the series convergent there.
For open subsets of \(\mathbb R^n\), use locally convergent multivariable
power series \(\sum_{\alpha\in\mathbb N_0^n}c_\alpha(x-a)^\alpha\).
Here \((x-a)^\alpha=\prod_i(x_i-a_i)^{\alpha_i}\); require absolute
convergence on some open box about \(a\).
\end{definition}
Termwise differentiation of power series shows that analytic functions
are smooth, and that \(c_k=f^{(k)}(a)/k!\) in one variable. Analyticity
requires the function to equal that Taylor series near the point;
merely possessing derivatives of every order does not suffice.
\begin{example}
Polynomials and the functions \(e^x,\sin x,\cos x\) are real-analytic.
Also \(1/(1-x)=\sum_{k\ge0}x^k\) for \(|x|<1\). The function
\(1/(1-x)\) is real-analytic on its whole domain \(\mathbb R\setminus\{1\}\),
although this particular series centered at zero has radius one.
Analyticity is a local property, not a demand for one global power series.
\end{example}
The smooth function \(\phi(x)=e^{-1/x^2}\) for \(x\ne0\), with
\(\phi(0)=0\), is not analytic at zero. Its derivatives of every order
vanish there, as proved in [[smooth-function|the smooth function entry]],
but it is not zero on any neighborhood. Consequently, in real analysis,
analytic implies smooth implies differentiable implies continuous, and
none of these implications reverses in general.
\section*{Complex functions}
For \(f:U\to\mathbb C\), \(U\subseteq\mathbb C\) open, complex analyticity
means local representation by convergent power series in \(z-a\).
A function is holomorphic if the complex derivative
\(\lim_{h\to0}(f(z+h)-f(z))/h\) exists at every point of \(U\), with
\(h\) approaching zero from arbitrary complex directions.
The fundamental power-series theorem of complex analysis says that
holomorphic and complex-analytic are equivalent; existence of a complex
derivative at just one point is not enough. This theorem is cited here,
not proved. Complex conjugation is smooth as a real map but is nowhere
complex differentiable, since its difference quotients along real and
imaginary increments are 1 and -1 respectively.
""",ANALYSIS)

COMPATIBLE=r"""
\begin{definition}
Two charts \(x:U\to x(U)\subseteq\mathbb R^n\) and
\(y:V\to y(V)\subseteq\mathbb R^n\) are \emph{smoothly compatible}
if both transition maps
\[
y\circ x^{-1}:x(U\cap V)\longrightarrow y(U\cap V),\qquad
x\circ y^{-1}:y(U\cap V)\longrightarrow x(U\cap V)
\]
are \PMlinkname{smooth}{SmoothFunction}. Their domains are open subsets
of Euclidean space. Thus either transition map is a diffeomorphism:
a bijective smooth map with smooth inverse. For disjoint chart domains
the condition is vacuous. A chart is compatible with an atlas if it is
compatible with every chart in that atlas; a smooth atlas is pairwise compatible.
\end{definition}
\begin{example}
On the usual real line, \(x(t)=t\) and \(y(t)=2t+1\) are compatible,
since the transitions are affine functions with affine inverses.
The charts \(x(t)=t\) and \(z(t)=t^3\) are both homeomorphisms onto
\(\mathbb R\), but are not smoothly compatible: the inverse transition
\(u\mapsto u^{1/3}\) is not differentiable at zero. Checking only one
direction of a coordinate change would therefore be insufficient.
\end{example}
"""

def apply(path):
    base.apply(path)
    with sqlite3.connect(path) as c:
        c.row_factory=sqlite3.Row
        c.execute('PRAGMA foreign_keys=ON')
        d=base.fetch_public_math_concept_detail(c.cursor(),'smooth-manifold')
        tex=d['cleaned_tex']
        if r'\emph{smoothly compatible}' not in tex:
            position=tex.index(r'\end{definition}')+len(r'\end{definition}')
            tex=tex[:position]+'\n'+COMPATIBLE+tex[position:]
            rendered=render_tex_reusing_existing_diagrams(d['id'],tex,c.cursor())
            c.execute('UPDATE math_concepts SET cleaned_tex=?,rendered_tex=?,updated_at=? WHERE id=?',
                (tex,rendered,datetime.now().strftime('%Y-%m-%d %H:%M:%S'),d['id']))
        for term in ['smoothly compatible charts','compatible coordinate charts']:
            if not c.execute('SELECT 1 FROM math_definitions WHERE concept_id=? AND defined_term=?',(d['id'],term)).fetchone():
                c.execute('INSERT INTO math_definitions(concept_id,defined_term) VALUES (?,?)',(d['id'],term))
        for slug in ['smooth-function','differentiable-function']:
            base.relate(c,'smooth-manifold',slug);base.relate(c,slug,'smooth-manifold')
        display=base.fetch_public_math_concept_detail(c.cursor(),'smooth-manifold')['display_tex']
        assert 'smooth-function' in base.links(display)
        assert r'y\circ x^{-1}:x(U\cap V)' in display
        assert not c.execute('PRAGMA foreign_key_check').fetchall()
        print('Verified compatible chart definition and examples')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--db',type=Path,default=base.SRC.parent/'portfolio.db')
    args=p.parse_args()
    if not args.db.is_file():raise FileNotFoundError(args.db)
    apply(args.db)
