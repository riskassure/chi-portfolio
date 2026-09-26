"""Add five topology foundations and connect the smooth-manifold entry.

Existing entries prove continuity criteria, compactness characterizations,
and first-countability properties, but do not supply these general definitions.
Keep qualified aliases separate from order-theoretic and logical meanings.
"""
import argparse
from pathlib import Path
import sqlite3
from datetime import datetime
import add_number_theory_and_geometry_foundations as base
from services.math.concept_render_service import render_tex_reusing_existing_diagrams

base.ENTRIES.clear()
REF=('Allen Hatcher','Notes on Introductory Point-Set Topology, Sections 1-3',
     'https://pi.math.cornell.edu/~hatcher/Top/TopNotes.pdf')

def add(*args):
    base.add(*args,REF)
    base.ENTRIES[-1]['escapes'] += ['continuous','continuity','connected','compact',
        'compactness','path','paths','separation','component','components',
        'basis','neighborhood','subspace','subspaces','topology','dense','countable',
        'interval','intervals','discrete','indiscrete','limit','sequence','cover',
        'covering','closed','finite','normal','regular','closure','restriction',
        'language','assumption','useful','opposite sides','reachable','orientation',
        'connected component','connected components']

add('topological space','topological-space','TopologicalSpace','54A05',
    ['topological spaces'], ['topology on a set','basis for a topology','subspace topology'],
    'continuity-of-maps-between-topological-spaces compactness-of-a-topological-space connectedness-of-a-topological-space second-countability smooth-manifold lattice-of-topologies product-topology',r"""
\begin{definition}
A \emph{topology} on a set \(X\) is a collection \(\tau\) of subsets such that
\(\varnothing,X\in\tau\), every union of members of \(\tau\) belongs to
\(\tau\), and every finite intersection of members belongs to \(\tau\).
The pair \((X,\tau)\) is a \emph{topological space}; the members of \(\tau\)
are its open sets. A set is closed if its complement is open.
\end{definition}
There is no requirement that an open set fail to be closed: both
\(\varnothing\) and \(X\) are always both. Infinite intersections need
not be open: in the usual real topology, \(\bigcap_{n\ge1}(-1/n,1/n)=\{0\}\).
A neighborhood of \(x\) means a set containing an open set containing \(x\).

\begin{definition}
A \emph{basis for a topology} is a collection \(\mathcal B\) of open sets
such that every open set is a union of members of \(\mathcal B\).
Equivalently, for every open \(U\) and \(x\in U\), some \(B\in\mathcal B\)
satisfies \(x\in B\subseteq U\). The \emph{subspace topology} on \(A\subseteq X\)
is \(\{A\cap U:U\in\tau\}\).
\end{definition}
\begin{example}
Open intervals form a basis for the usual topology on \(\mathbb R\).
All subsets form the discrete topology on any set; just \(\varnothing\)
and \(X\) form its indiscrete topology. On \(\{0,1\}\), the collection
\(\{\varnothing,\{1\},\{0,1\}\}\) is another topology, showing that a
topological space need not distinguish its points symmetrically by open sets.
\end{example}
\begin{definition}
A space is Hausdorff if distinct points have disjoint open neighborhoods.
This is an additional condition, not an axiom for all topological spaces.
\end{definition}
Euclidean spaces are Hausdorff; an indiscrete space with two or more points
is not. A [[smooth-manifold|smooth manifold]] imposes both the Hausdorff
condition and [[second-countability|second countability]], in addition to
its local Euclidean structure. Topology supplies the language for
[[continuity-of-maps-between-topological-spaces|continuity]],
[[compactness-of-a-topological-space|compactness]], and
[[connectedness-of-a-topological-space|connectedness]] without requiring a distance function.
""")

add('continuity of maps between topological spaces','continuity-of-maps-between-topological-spaces',
    'ContinuityOfMapsBetweenTopologicalSpaces','54C05',
    ['topological continuity','continuous map of topological spaces'],
    ['continuity at a point'],
    'topological-space testing-for-continuity-via-basic-open-sets testing-continuity-via-filters testing-for-continuity-via-nets smooth-map-between-manifolds',r"""
\begin{definition}
A map \(f:X\to Y\) between topological spaces is \emph{continuous} if
\(f^{-1}(V)\) is open in \(X\) for every open set \(V\subseteq Y\).
It is \emph{continuous at a point} \(x\) if every open neighborhood \(V\)
of \(f(x)\) contains the image of some open neighborhood \(U\) of \(x\).
The inverse image here is a set operation, not an assumption that \(f\) is invertible.
\end{definition}
\begin{proposition}
A map is continuous exactly when it is continuous at every point.
\end{proposition}
\begin{proof}
If inverse images of open sets are open, use \(U=f^{-1}(V)\) at each
point mapping into \(V\). Conversely, suppose continuity holds at every
point, and let \(V\) be open. For each \(x\in f^{-1}(V)\), choose an open
\(U_x\) containing \(x\) and contained in \(f^{-1}(V)\). Their union is
exactly \(f^{-1}(V)\), so that inverse image is open.
\end{proof}
\begin{example}
Every constant map is continuous. Every map out of a discrete space is
continuous, as is every map into an indiscrete space. The identity from
\(\mathbb R\) with its discrete topology to its usual topology is continuous;
the reverse identity is not, because the inverse image of the open singleton
\(\{0\}\) is not open in the usual topology. Thus continuity depends on
the topologies, not just on the formula for the function.
\end{example}
\begin{proposition}
Composites of continuous maps are continuous.
\end{proposition}
\begin{proof}
For \(X\xrightarrow{f}Y\xrightarrow{g}Z\) and an open \(W\subseteq Z\),
\((g\circ f)^{-1}(W)=f^{-1}(g^{-1}(W))\) is open by the two assumptions.
\end{proof}
Equivalently, inverse images of closed sets must be closed, by taking
complements. It suffices to check a basis of the target topology; see
[[testing-for-continuity-via-basic-open-sets|the basis criterion]]. In metric
spaces the definition agrees with the usual epsilon-delta condition.
A homeomorphism is a bijection continuous in both directions. A continuous
bijection need not be a homeomorphism, as the discrete-to-usual identity above shows.

Continuity preserves convergent sequences, but testing sequences alone
does not characterize continuity in all spaces. The
[[testing-for-continuity-via-nets|net criterion]] handles arbitrary spaces.
""")

add('compactness of a topological space','compactness-of-a-topological-space',
    'CompactnessOfATopologicalSpace','54D30', ['topological compactness','compact topological space'],
    ['open cover','finite subcover'],
    'topological-space continuity-of-maps-between-topological-spaces a-space-is-compact-iff-any-family-of-closed-sets-having-fip-has-nonempty-intersection',r"""
\begin{definition}
An \emph{open cover} of \(X\) is a family of open sets whose union is \(X\).
A space is \emph{compact} if every open cover has a finite subfamily still
covering \(X\), called a \emph{finite subcover}. A subset is compact when
it is compact with its subspace topology.
\end{definition}
We do not include Hausdorffness in this definition. Some authors use
quasi-compact for this property and reserve compact for the Hausdorff case.
The empty space and every finite space are compact.
\begin{example}
The Heine-Borel theorem says that a subset of Euclidean space is compact
exactly when it is closed and bounded. In particular \([0,1]\) is compact.
The interval \((0,1)\) is not: the sets \((1/n,1)\), for \(n\ge2\),
cover it and have no finite subcover. An infinite discrete space is not
compact, since its singleton cover has no finite subcover.
\end{example}
\begin{proposition}
Continuous images of compact spaces are compact, and closed subsets of
compact spaces are compact.
\end{proposition}
\begin{proof}
Pull an open cover of the image back along the continuous map. A finite
subcover of the domain yields a finite subcover of its image.
For a closed subset \(A\subseteq X\), write an open cover of \(A\) as
sets \(A\cap U_i\), with \(U_i\) open in \(X\). Adjoin \(X\setminus A\)
to obtain a cover of \(X\). A finite subcover restricts to one of \(A\).
\end{proof}
\begin{proposition}
A compact subset of a Hausdorff space is closed.
\end{proposition}
\begin{proof}
Let \(K\) be compact and \(x\notin K\). For each \(y\in K\), choose
disjoint open neighborhoods \(U_y\) of \(x\) and \(V_y\) of \(y\).
Finitely many \(V_y\) cover \(K\); the intersection of their corresponding
\(U_y\) is an open neighborhood of \(x\) avoiding \(K\). Thus the complement is open.
\end{proof}
Compactness is not generally synonymous with closedness and boundedness:
boundedness requires a metric, and the Euclidean criterion is special.
Sequential compactness means that every sequence has a convergent subsequence
with limit in the space. It is equivalent to compactness for metric spaces,
but not for arbitrary topological spaces. A useful general alternative is
[[a-space-is-compact-iff-any-family-of-closed-sets-having-fip-has-nonempty-intersection|the closed-set finite-intersection criterion]].
""")

add('connectedness of a topological space','connectedness-of-a-topological-space',
    'ConnectednessOfATopologicalSpace','54D05',
    ['topological connectedness','connected topological space','path-connected space','locally connected space','locally path-connected space'],
    ['connected component of a topological space','path component','total disconnectedness','total separatedness'],
    'topological-space continuity-of-maps-between-topological-spaces simply-connected smooth-manifold',r"""
\begin{definition}
A space is \emph{connected} if it cannot be written as a union of two
disjoint nonempty open subsets. Such a decomposition is a separation.
Equivalently, its only subsets both open and closed are \(\varnothing\)
and the whole space. A subset is connected using its subspace topology.
\end{definition}
\begin{definition}
A path from \(x\) to \(y\) is a continuous map \(c:[0,1]\to X\) with
\(c(0)=x\), \(c(1)=y\). A space is \emph{path-connected} if every pair
of points can be joined by a path. It is \emph{locally connected} if
every point has a basis of connected open neighborhoods, and
\emph{locally path-connected} if it has a basis of path-connected open neighborhoods.
\end{definition}
We allow the empty space to be connected and path-connected, vacuously.
The local properties do not assert that the whole space is connected.
\begin{proposition}
Continuous images of connected spaces are connected. Path-connected
spaces are connected, and locally path-connected spaces are locally connected.
\end{proposition}
\begin{proof}
A separation of a continuous image pulls back to a separation of the
domain. If a path-connected space had a separation, a path joining points
in opposite sides would pull it back to a separation of \([0,1]\), which
is connected. Apply this implication to each neighborhood in a local
path-connected basis to obtain the last assertion.
\end{proof}
\section*{Components and local behavior}
The connected component of \(x\) is the maximal connected subset containing
\(x\); it is the union of all connected subsets containing \(x\).
The path component consists of points reachable from \(x\) by a path.
Both notions partition the space, and each path component lies in a
connected component. Connected components are always closed, but need not be open.
\begin{proposition}
In a locally path-connected space, path components are open and coincide
with connected components. In particular, connectedness implies path-connectedness there.
\end{proposition}
\begin{proof}
Every point of a path component has a path-connected open neighborhood
contained in that component, so the component is open. Its complement is
a union of other open path components, hence also open. A connected
component cannot meet two of these disjoint open-and-closed sets. The
reverse containment follows because each path component is connected.
\end{proof}
\begin{example}
Intervals in \(\mathbb R\), convex subsets of Euclidean space, and the circle
are path-connected. A union of two disjoint open intervals is locally
path-connected but disconnected. Smooth manifolds are locally path-connected,
because sufficiently small coordinate balls have this property.
\end{example}
\begin{example}
The closed topologist's sine curve is
\[
S=\{(x,\sin(1/x)):0<x\le1\}\cup(\{0\}\times[-1,1]).
\]
It is connected as the closure of a connected graph, but is not path-connected.
Here is why no path can join the vertical segment to the graph. If such
a path existed, take the component \((a,b]\) (or the corresponding open
interval) of times with positive first coordinate containing a graph point.
At its left endpoint the first coordinate is zero. On arbitrarily short
intervals just after \(a\), continuity and the intermediate value theorem
force the first coordinate to take small positive values with sine equal
to 1 and to -1. The second coordinate therefore cannot be continuous at \(a\).
Reversing a path handles either orientation of its endpoints.
\end{example}
\section*{Further distinctions}
A space is totally disconnected if all connected components are singletons.
It is totally separated if any two distinct points are separated by an
open-and-closed subset containing one and not the other. Total separatedness
implies total disconnectedness. Neither condition means discrete: \(\mathbb Q\)
with its usual subspace topology is totally separated, using an irrational
cut between any two rationals, but has no isolated points.

[[simply-connected|Simple connectedness]] is stronger than path-connectedness:
in a nonempty path-connected space every loop must be deformable to a
constant loop while keeping its base point fixed. The circle is path-connected
but not simply connected. This condition concerns loops, not arbitrary
paths with two different fixed endpoints.
""")

add('second countability','second-countability','SecondCountability','54D70 54D65',
    ['second-countable space','second countable space'], [],
    'topological-space smooth-manifold properties-of-first-countability',r"""
\begin{definition}
A topological space is \emph{second-countable} if it has a countable basis
\(\mathcal B\) for its topology. Thus for every open \(U\) and every
\(x\in U\), some \(B\in\mathcal B\) satisfies \(x\in B\subseteq U\).
Countable here includes finite; the empty space has the empty basis.
\end{definition}
This is one countable family serving the entire space. First countability
instead asks for a countable neighborhood basis at each individual point,
with no requirement of a countable family working for all points.
\begin{example}
The intervals with rational endpoints form a countable basis of \(\mathbb R\).
Similarly, balls with rational centers and positive rational radii form a
countable basis of \(\mathbb R^n\). Every subspace of a second-countable
space is second-countable: intersect a countable basis with the subspace.
\end{example}
\begin{proposition}
Second countability implies first countability, separability, and the Lindelof property.
Here separability means having a countable dense subset, and the Lindelof
property means that every open cover has a countable subcover.
\end{proposition}
\begin{proof}
At \(x\), retain those basis members containing \(x\); they give a countable
local basis. To obtain a dense set, select one point from each nonempty
basis member. Every nonempty open set contains a basis member and hence
one of the selected points. This selection uses the usual axiom of choice.
Finally, for each basis member contained in some set of a given open cover,
choose one such covering set. There are countably many choices, and they
cover the space because the original cover is open and the family is a basis.
\end{proof}
\begin{example}
An uncountable discrete space is first-countable, using just \(\{x\}\)
at each point, but is not second-countable: any basis must contain every
singleton. So the local condition is strictly weaker.
\end{example}
For metric spaces, separability conversely implies second countability:
balls of positive rational radius centered in a countable dense subset
form a basis. That implication is not valid for arbitrary topological spaces.
Our definition of [[smooth-manifold|smooth manifold]] explicitly requires
second countability. A manifold can still have uncountably many points;
it is the basis, not the underlying set, that must be countable.
""")

def apply(path):
    base.apply(path)
    with sqlite3.connect(path) as c:
        c.row_factory=sqlite3.Row
        c.execute('PRAGMA foreign_keys=ON')
        d=base.fetch_public_math_concept_detail(c.cursor(),'smooth-manifold')
        tex=d['cleaned_tex']
        tex=tex.replace('topological space \\(M\\)',r'\PMlinkname{topological space}{TopologicalSpace} \(M\)')
        tex=tex.replace('second countability\nmeans',r'\PMlinkname{second countability}{SecondCountability}'+'\nmeans')
        tex=tex.replace('it is compact, whereas',r'it is \PMlinkname{compact}{CompactnessOfATopologicalSpace}, whereas')
        if tex!=d['cleaned_tex']:
            rendered=render_tex_reusing_existing_diagrams(d['id'],tex,c.cursor())
            c.execute('UPDATE math_concepts SET cleaned_tex=?,rendered_tex=?,updated_at=? WHERE id=?',
                (tex,rendered,datetime.now().strftime('%Y-%m-%d %H:%M:%S'),d['id']))
        for slug in ['topological-space','second-countability','compactness-of-a-topological-space','connectedness-of-a-topological-space']:
            base.relate(c,'smooth-manifold',slug)
            base.relate(c,slug,'smooth-manifold')
        display=base.fetch_public_math_concept_detail(c.cursor(),'smooth-manifold')['display_tex']
        for slug in ['topological-space','second-countability','compactness-of-a-topological-space']:
            assert slug in base.links(display),slug
        assert not c.execute('PRAGMA foreign_key_check').fetchall()
        print('Verified smooth-manifold foundation links')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--db',type=Path,default=base.SRC.parent/'portfolio.db')
    args=p.parse_args()
    if not args.db.is_file():raise FileNotFoundError(args.db)
    apply(args.db)
