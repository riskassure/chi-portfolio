"""Add analytic continuation, absent from titles, aliases and entry text."""
import argparse
from pathlib import Path
import add_number_theory_and_geometry_foundations as base

base.ENTRIES.clear()
base.add('analytic continuation','analytic-continuation','AnalyticContinuation','30B40',
    ['holomorphic continuation'], ['germ of a holomorphic function'],
    'analytic-function simply-connected connectedness-of-a-topological-space',r"""
Analytic continuation extends local analytic information while preserving
the function on the region where it was already known. This entry concerns
complex functions of one variable. A domain means a nonempty connected open
subset of \(\mathbb C\).
\begin{definition}
Let \(f\) be holomorphic on a domain \(U\). If \(U\subseteq V\) and \(V\)
is a domain, a holomorphic function \(F:V\to\mathbb C\) with \(F|_U=f\)
is an \emph{analytic continuation} of \(f\) to \(V\).
More locally, holomorphic functions on overlapping domains continue one
another across a specified component of their overlap when they agree there.
To glue them into a single function on the union, agreement is required
on the entire overlap, not merely on one of several components.
\end{definition}
Here holomorphic and [[analytic-function|complex-analytic]] are equivalent.
Continuation need not mean that the original Taylor series converges on
the larger domain; new series centered at other points can be used.
\begin{example}
The series \(\sum_{n\ge0}z^n\) defines a holomorphic function for
\(|z|<1\). Its sum \(1/(1-z)\) extends it to \(\mathbb C\setminus\{1\}\),
although the original series still diverges when \(|z|>1\).
There is no holomorphic extension through 1: if one existed, continuity
of \((1-z)F(z)\), which equals 1 nearby away from 1, would give both
0 and 1 at that point.
\end{example}
\begin{proposition}
An analytic continuation to a specified domain containing the original
domain is unique, if it exists.
\end{proposition}
\begin{proof}
Suppose \(F,G\) are two such continuations on \(V\), and put \(H=F-G\).
The set \(A\) of points where \(H\) vanishes on a neighborhood is nonempty
and open. It is also closed in \(V\): if \(a_j\in A\) tends to \(a\in V\),
continuity of every derivative implies \(H^{(k)}(a)=0\) for all \(k\).
The convergent Taylor expansion at \(a\) then shows that \(H\) vanishes
on a neighborhood of \(a\). Connectedness gives \(A=V\), hence \(F=G\).
This is the open-set form of the identity theorem.
\end{proof}
\section*{Continuation along a path}
\begin{definition}
A \emph{germ of a holomorphic function} at \(a\) is an equivalence class
of holomorphic functions defined near \(a\); two representatives are
equivalent when they agree on some neighborhood of \(a\).
For a continuous path \(\gamma:[0,1]\to\mathbb C\), a continuation along
\(\gamma\) is a family of germs \(f_t\) at \(\gamma(t)\) such that locally
in \(t\) they are represented by one holomorphic function: for every
\(t_0\), there are a neighborhood \(W\) of \(\gamma(t_0)\), a holomorphic
\(h\) on \(W\), and an interval about \(t_0\) relative to \([0,1]\)
on which \(\gamma(t)\in W\) and \(f_t\) is the germ of \(h\) at \(\gamma(t)\).
The initial germ \(f_0\) is prescribed.
\end{definition}
If continuation exists along a fixed path, it is unique. Local agreement
propagates along the path by the identity theorem. This does not say that
different paths with the same endpoints produce the same final germ.
\begin{example}
Start with the logarithm near 1 having value zero there, and continue
along \(\gamma(t)=e^{2\pi i t}\) in \(\mathbb C\setminus\{0\}\).
Its value along the path is \(2\pi i t\): the derivative of a local
logarithm is \(1/z\), so along this curve the derivative of its value is
\(\gamma'(t)/\gamma(t)=2\pi i\). Upon returning to 1 the value is
\(2\pi i\), not zero. Thus the endpoint germ depends on the path.
There is no single-valued holomorphic logarithm on the entire punctured plane.
\end{example}
This path dependence is called monodromy. The monodromy theorem states
that if a germ in a simply connected domain can be continued along every
path starting at its base point, the continuations define a single-valued
holomorphic function throughout that domain. Both simple connectedness
and the existence of continuation along every path are hypotheses;
simple connectedness alone does not eliminate a singularity. A proof
of this theorem is given in Chapter 10 of the reference.

Real-analytic functions also admit a notion of continuation through
overlapping real neighborhoods. Smooth functions do not have the same
uniqueness principle: a smooth function can vanish on an open interval
and be nonzero elsewhere.
""",('Jiri Lebl','Guide to Cultivating Complex Analysis, Chapter 10: Analytic Continuation',
        'https://www.jirka.org/ca/'))
base.ENTRIES[0]['escapes'] += ['domain','domains','component','components',
    'connected','open','closed','analytic','continuation','local','global','path',
    'paths','interval','intervals','neighborhood','derivative','identity',
    'restriction','series','normal','extension','germ','base point','converges','open interval']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--db',type=Path,default=base.SRC.parent/'portfolio.db')
    args=p.parse_args()
    if not args.db.is_file():raise FileNotFoundError(args.db)
    base.apply(args.db)
