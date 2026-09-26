"""Give holomorphic functions a standalone definition with examples and criteria."""
import argparse
from pathlib import Path
import add_number_theory_and_geometry_foundations as base

base.ENTRIES.clear()
base.add('holomorphic function','holomorphic-function','HolomorphicFunction','30A05',
    ['holomorphic functions','holomorphic'], ['entire function'],
    'analytic-function analytic-continuation differentiable-function smooth-function',r"""
\begin{definition}
Let \(U\subseteq\mathbb C\) be open. A function \(f:U\to\mathbb C\) is
\emph{holomorphic on} \(U\) if it is complex differentiable at every
\(a\in U\): the finite limit
\[
f'(a)=\lim_{h\to0}\frac{f(a+h)-f(a)}{h}
\]
exists as the nonzero complex increment \(h\) approaches zero from
arbitrary directions. A function is holomorphic at a point if it is
holomorphic on some open neighborhood of that point. A function
holomorphic on all of \(\mathbb C\) is called \emph{entire}.
\end{definition}
In particular, being complex differentiable at one isolated point does
not mean being holomorphic there. The domain need not be connected for
this definition, although many global theorems require connectedness.
\begin{example}
Polynomials, the exponential function, sine and cosine are entire.
A rational function \(P(z)/Q(z)\), where \(Q\) is a nonzero polynomial,
is holomorphic wherever \(Q(z)\ne0\). In particular, \(1/z\) is
holomorphic on \(\mathbb C\setminus\{0\}\), but is not entire.
\end{example}
\section*{Complex versus real differentiability}
\begin{example}
Complex conjugation \(f(z)=\overline z\) is smooth as a real map
\((x,y)\mapsto(x,-y)\), but is nowhere complex differentiable.
Its difference quotient is \(\overline h/h\), which equals 1 for real
increments and -1 for purely imaginary increments.

The function \(g(z)=|z|^2\) is complex differentiable at zero, since
\(|h|^2/h=\overline h\to0\). Away from zero it is not complex
differentiable, as the criterion below shows. It is therefore not
holomorphic on any neighborhood of zero.
\end{example}
\begin{proposition}
Suppose \(f=u+iv\) is differentiable at \((a,b)\) as a real map
\(\mathbb R^2\to\mathbb R^2\). It is complex differentiable at
\(a+ib\) if and only if the Cauchy-Riemann equations hold there:
\[
u_x=v_y,\qquad u_y=-v_x.
\]
In that case \(f'=u_x+i v_x\).
\end{proposition}
\begin{proof}
Multiplication by \(\alpha+i\beta\) has real matrix with rows
\((\alpha,-\beta)\) and \((\beta,\alpha)\).
The real derivative matrix of \(f\) has rows \((u_x,u_y)\) and
\((v_x,v_y)\). It represents multiplication by a complex scalar
exactly when the displayed equations hold. The real differentiability
remainder is \(o(|h|)\); dividing by \(h\) proves sufficiency.
Conversely, a complex derivative gives just such a real linear
approximation, proving necessity.
\end{proof}
For \(g(z)=|z|^2\), we have \(u=x^2+y^2\), \(v=0\), so these
equations force \(x=y=0\). In applying the criterion, merely knowing
that partial derivatives exist is not a substitute for real differentiability.
Continuous first partial derivatives are a sufficient hypothesis.
\section*{Relation to analyticity}
The fundamental power-series theorem states that a function on an open
subset of \(\mathbb C\) is holomorphic if and only if it is
[[analytic-function|complex-analytic]]: near each point it equals a
convergent power series in \(z-a\). In particular it has complex
derivatives of every order and is smooth as a real map.
This theorem is proved in the reference; the much weaker corresponding
assertion about real differentiable functions is false.

Sums, products and compositions of holomorphic functions are holomorphic
where defined, and reciprocals are holomorphic wherever the function is
nonzero. Extending such a function while preserving its values on the
original domain is [[analytic-continuation|analytic continuation]].
""",('Jiri Lebl','Guide to Cultivating Complex Analysis, Chapter 2: Holomorphic and Analytic Functions',
        'https://www.jirka.org/ca/'))
base.ENTRIES[0]['escapes'] += ['domain','connected','open','entire','derivative',
    'differentiable','real','complex','direction','directions','increments',
    'conjugation','smooth','analytic','criterion','matrix','rows','partial',
    'linear','normal','restriction','extension','isolated','nonzero']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--db',type=Path,default=base.SRC.parent/'portfolio.db')
    args=p.parse_args()
    if not args.db.is_file():raise FileNotFoundError(args.db)
    base.apply(args.db)
