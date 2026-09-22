"""Add exactly 3 set, 4 group, 6 ring, 5 field, and 2 computability entries.

Candidate review included titles, synonyms, defined terms, and full sources.
The existing dependence-relation entry already discusses algebraic dependence;
primitive element was chosen instead of adding a duplicate independence entry.
Qualified names avoid the existing lattice center, involutory-ring trace/norm,
stationary stochastic processes, and rewriting-theory reduction terminology.
"""
import argparse
from collections import Counter
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
from add_eight_algebra_concepts import Links, source
from add_sylow_theorems import document_types

SET_REF = ("S. Unger", "Forcing and Independence in Set Theory (lecture notes and exercises)", "https://homepages.math.uic.edu/~shac/forcing/forcing.html")
GROUP_REF = ("R. Sharifi", "Abstract Algebra, Chapters 2 and 4", "https://www.math.ucla.edu/~sharifi/notes/algebra-ch04.html")
RING_REF = ("R. Sharifi", "Abstract Algebra, Chapters 3 and 5", "https://www.math.ucla.edu/~sharifi/notes/algebra-ch05.html")
COMPUTE_REF = ("A. Marks", "Computability Theory, Sections 5 and 15", "https://math.berkeley.edu/~marks/notes/computability_notes_v1.pdf")
FIELD_REF = ("The Stacks Project", "Fields", "https://stacks.math.columbia.edu/tag/09FA")

# Scoped exclusions for ordinary-language and subject-specific homonyms.
ESCAPES = ["order", "identity", "inverse", "product", "normal", "simple", "index", "power", "prime",
           "closed", "closed under", "closure", "unbounded", "bounded", "stationary", "regular", "singular",
           "center", "central", "trace", "norm", "unit", "ideal", "principal", "domain", "degree", "root",
           "polynomial", "irreducible", "basis", "independent", "dependence", "extension", "characteristic",
           "finite", "infinite", "constant", "term", "image", "kernel", "range", "function", "map", "chain",
           "union", "disjoint union", "point", "line", "condition", "formula", "equivalent", "representation",
           "reduction", "reducible", "decidable", "computable", "total", "partial", "left", "right", "fixed",
           "base", "dimension", "quotient", "preserve", "preserves", "contains", "minimal", "maximal",
           "inclusion", "elementary", "operation", "structure", "generated", "generator", "restriction",
           "limit", "alternating", "meets", "bound", "cyclic", "order of a group", "bijective",
           "opposite", "side", "distributive", "principal ideal", "finitely generated", "hypothesis",
           "Euclidean", "maximal ideal", "proper ideal", "induced", "valid", "primitive element",
           "satisfy", "transcendental", "diagonal", "recursive", "simulation"]


def entry(area, title, slug, canonical, codes, synonyms, definitions, related, body, reference=None):
    refs = {"set": SET_REF, "group": GROUP_REF, "ring": RING_REF, "field": FIELD_REF, "computability": COMPUTE_REF}
    return dict(area=area, title=title, slug=slug, canonical=canonical, classifications=codes,
                synonyms=synonyms, definitions=definitions, related=related, body=body,
                reference=reference or refs[area], escapes=list(ESCAPES))


ENTRIES = [
entry("set", "cofinality of an ordinal", "cofinality-of-an-ordinal", "CofinalityOfAnOrdinal", ["03E04"],
      ["ordinal cofinality", "cofinality"], ["cofinal subset of an ordinal", "regular cardinal", "singular cardinal"],
      ["properties-of-ordinals", "ordering-on-cardinalities"], r"""
Cofinality measures how many points are needed to reach arbitrarily far along an ordinal. We work in ZFC.
\begin{definition}
A subset \(A\subseteq\alpha\) is a \emph{cofinal subset of an ordinal} \(\alpha\) if every \(\beta<\alpha\) satisfies \(\beta\le\gamma\) for some \(\gamma\in A\). The \emph{cofinality} \(\operatorname{cf}(\alpha)\) is the least cardinality of such a subset. In particular \(\operatorname{cf}(0)=0\). An infinite cardinal \(\kappa\), viewed as its initial ordinal, is a \emph{regular cardinal} if \(\operatorname{cf}(\kappa)=\kappa\), and a \emph{singular cardinal} otherwise.
\end{definition}
\begin{example}
Every successor ordinal \(\beta+1\) has cofinality one, witnessed by \(\{\beta\}\). The ordinal \(\omega\) has cofinality \(\aleph_0\): the natural numbers are cofinal, while a finite subset has a greatest member and is not cofinal. Likewise \(\operatorname{cf}(\omega^2)=\aleph_0\), using \(\{\omega n:n<\omega\}\); no finite subset is cofinal in this limit ordinal.
\end{example}
\begin{remark}
For a nonzero limit ordinal, cofinality can be described using subsets with supremum equal to the ordinal. That description needs adjustment for successors, which is why the definition above uses the explicit inequality.
\end{remark}
"""),
entry("set", "closed unbounded set", "closed-unbounded-set", "ClosedUnboundedSet", ["03E05"],
      ["club set", "closed unbounded subset"], ["unbounded subset of a cardinal"],
      ["cofinality-of-an-ordinal", "ordinal-space"], r"""
Closed unbounded sets combine unbounded reach with closure under ordinal limits.
\begin{definition}
Let \(\kappa\) be a regular uncountable cardinal. An \emph{unbounded subset of a cardinal} \(\kappa\) is a set \(C\subseteq\kappa\) such that for every \(\alpha<\kappa\), some \(\beta\in C\) satisfies \(\alpha<\beta\). It is closed if every nonzero limit ordinal \(\delta<\kappa\) with \(\sup(C\cap\delta)=\delta\) belongs to \(C\). A \emph{closed unbounded set}, or club set, satisfies both conditions.
\end{definition}
\begin{proposition}
The intersection of two club subsets of \(\kappa\) is club.
\end{proposition}
\begin{proof}
An ordinal limit of points of the intersection is a limit of points of each set, proving closure. For unboundedness, start above any \(\alpha<\kappa\) and choose a strictly increasing sequence alternating between the two clubs. Its supremum \(\delta\) is below \(\kappa\): a countable set cannot be cofinal in a regular uncountable cardinal. Both alternating subsequences are cofinal in \(\delta\), so closure puts \(\delta\) in both clubs, above \(\alpha\).
\end{proof}
\begin{example}
Every final segment \(\{\beta<\kappa:\gamma\le\beta\}\), for \(\gamma<\kappa\), is club: it is unbounded, and every limit point of it is still at least \(\gamma\).
\end{example}
"""),
entry("set", "stationary set", "stationary-set", "StationarySet", ["03E05"],
      ["stationary subset of a cardinal"], ["nonstationary set"],
      ["closed-unbounded-set", "cofinality-of-an-ordinal"], r"""
A stationary set meets every closed unbounded test set in its ambient cardinal.
\begin{definition}
For a regular uncountable cardinal \(\kappa\), a subset \(S\subseteq\kappa\) is a \emph{stationary set} if \(S\cap C\ne\varnothing\) for every club set \(C\subseteq\kappa\). A \emph{nonstationary set} is a subset disjoint from at least one club.
\end{definition}
\begin{proposition}
Every club is stationary, and every stationary subset of \(\kappa\) is unbounded.
\end{proposition}
\begin{proof}
Two clubs have club intersection by the closed unbounded set entry; in particular, they intersect. If \(S\) were bounded, a final segment beginning beyond its bound would be a club disjoint from \(S\), contrary to stationarity.
\end{proof}
\begin{example}
The whole set \(\kappa\) and each of its final segments are stationary, since they are clubs. Every finite subset is nonstationary, since it is bounded. Being unbounded alone is not the definition of stationarity: the requirement is intersection with every club.
\end{example}
\begin{remark}
This is the set-theoretic meaning of stationary; it has no connection with stationary stochastic processes. The ambient cardinal is part of the definition.
\end{remark}
"""),
entry("group", "cyclic group", "cyclic-group", "CyclicGroup", ["20A05"], ["cyclic groups"],
      ["cyclic subgroup", "order of a group element"], ["group", "lagranges-theorem-for-finite-groups", "subsemigroup-of-a-cyclic-semigroup"], r"""
A cyclic group is generated by repeated powers of a single element.
\begin{definition}
For \(g\in G\), the \emph{cyclic subgroup} generated by \(g\) is \(\langle g\rangle=\{g^n:n\in\mathbb{Z}\}\). Negative powers use \(g^{-1}\), and \(g^0=e\). A \emph{cyclic group} is a group equal to \(\langle g\rangle\) for some \(g\). The \emph{order of a group element} \(g\) is the least positive \(n\) with \(g^n=e\), or infinity if there is none.
\end{definition}
\begin{proposition}
Every subgroup of a cyclic group is cyclic.
\end{proposition}
\begin{proof}
Let \(H\le\langle g\rangle\). If \(H=\{e\}\), it is generated by \(e\). Otherwise the set of positive \(n\) with \(g^n\in H\) is nonempty, using inverses if necessary; let \(d\) be its least member. For \(g^n\in H\), divide \(n=qd+r\) with \(0\le r<d\). Then \(g^r=g^n(g^d)^{-q}\in H\), so minimality forces \(r=0\). Hence \(H=\langle g^d\rangle\).
\end{proof}
\begin{example}
The additive groups \(\mathbb{Z}\) and \(\mathbb{Z}/n\mathbb{Z}\) are generated by \(1\) and its residue class, respectively. Every cyclic group is abelian since \(g^a g^b=g^{a+b}=g^{b+a}\).
\end{example}
"""),
entry("group", "characteristic subgroup", "characteristic-subgroup", "CharacteristicSubgroup", ["20E07"],
      ["characteristic subgroups"], ["group automorphism"], ["group", "normalizer-of-a-subgroup"], r"""
A characteristic subgroup is preserved by every symmetry of the ambient group.
\begin{definition}
A \emph{group automorphism} is a bijective map \(\phi:G\to G\) preserving multiplication. A subgroup \(H\le G\) is a \emph{characteristic subgroup}, written \(H\operatorname{char}G\), if \(\phi(H)=H\) for every group automorphism \(\phi\).
\end{definition}
\begin{proposition}
Characteristic subgroups are normal. If \(K\operatorname{char}H\) and \(H\operatorname{char}G\), then \(K\operatorname{char}G\).
\end{proposition}
\begin{proof}
Conjugation by \(g\in G\) is an automorphism, so it preserves a characteristic subgroup, giving normality. For the second assertion, any automorphism of \(G\) restricts to an automorphism of \(H\), since it maps \(H\) onto itself. This restriction preserves \(K\).
\end{proof}
\begin{example}
The subgroups \(\{e\}\) and \(G\) are characteristic. A subgroup that is the unique subgroup of its order in a finite group is characteristic: automorphisms preserve subgroup cardinality and must send it to itself.
\end{example}
"""),
entry("group", "center of a group", "center-of-a-group", "CenterOfAGroup", ["20A05"], ["group center", "centre of a group"],
      ["central element of a group"], ["group", "characteristic-subgroup", "cyclic-group"], r"""
The center consists of the elements commuting with the entire group.
\begin{definition}
The \emph{center of a group} \(G\) is
\[
Z(G)=\{z\in G:zg=gz\text{ for all }g\in G\}.
\]
Its members are called \emph{central elements of the group}.
\end{definition}
\begin{proposition}
The center is a characteristic subgroup of \(G\).
\end{proposition}
\begin{proof}
The identity commutes with everything. Products of central elements commute with everything, and \(zg=gz\) implies \(z^{-1}g=gz^{-1}\), so \(Z(G)\) is a subgroup. If \(\phi\) is an automorphism and \(h=\phi(g)\), then \(\phi(z)h=\phi(zg)=\phi(gz)=h\phi(z)\). Surjectivity of \(\phi\) shows \(\phi(z)\) is central, and applying \(\phi^{-1}\) gives equality of the images.
\end{proof}
\begin{example}
For every abelian group, including every cyclic group, \(Z(G)=G\). Conversely, \(Z(G)=G\) says exactly that every pair of elements commutes, so the group is abelian.
\end{example}
"""),
entry("group", "commutator subgroup", "commutator-subgroup", "CommutatorSubgroup", ["20E07"], ["derived subgroup"],
      ["group commutator"], ["group", "characteristic-subgroup", "center-of-a-group"], r"""
Commutators record failures of two group elements to commute.
\begin{definition}
Use the convention \([g,h]=ghg^{-1}h^{-1}\) for a \emph{group commutator}. The \emph{commutator subgroup} \([G,G]\), also written \(G'\) and called the derived subgroup, is the subgroup generated by all commutators: its elements are finite products of commutators and their inverses, including the empty product \(e\).
\end{definition}
\begin{proposition}
The commutator subgroup is a characteristic subgroup, and \([G,G]=\{e\}\) if and only if \(G\) is abelian.
\end{proposition}
\begin{proof}
An automorphism satisfies \(\phi([g,h])=[\phi(g),\phi(h)]\); it therefore preserves the generated subgroup, with equality by its inverse. Finally, \([g,h]=e\) is equivalent to \(gh=hg\), by multiplying on the right by \(hg\). All commutators are trivial exactly when all pairs commute.
\end{proof}
\begin{example}
Every cyclic group has trivial commutator subgroup. The commutator subgroup should not be confused with the set of individual commutators: the definition includes their finite products.
\end{example}
"""),
entry("ring", "opposite ring", "opposite-ring", "OppositeRing", ["16S99"], ["opposite rings"],
      ["opposite multiplication"], ["ring", "module", "matrix-ring"], r"""
The opposite ring reverses the order of multiplication while keeping addition unchanged.
\begin{definition}
For an associative ring \(R\), its \emph{opposite ring} \(R^{\operatorname{op}}\) has the same additive group, with \emph{opposite multiplication} \(a*b=ba\), where the right side is computed in \(R\). If \(R\) is unital, its identity remains the identity of the opposite ring.
\end{definition}
\begin{proposition}
This construction is an associative ring and satisfies \((R^{\operatorname{op}})^{\operatorname{op}}=R\).
\end{proposition}
\begin{proof}
We have \((a*b)*c=c(ba)=(cb)a=a*(b*c)\). The distributive laws follow from those in \(R\) with left and right interchanged. Reversing multiplication twice restores \(ab\).
\end{proof}
\begin{example}
If \(R\) is commutative, its opposite multiplication is unchanged. A right \(R\)-module becomes a left \(R^{\operatorname{op}}\)-module by \(a\cdot m=ma\): \((a*b)\cdot m=m(ba)=(mb)a=a\cdot(b\cdot m)\).
\end{example}
"""),
entry("ring", "group of units of a ring", "group-of-units-of-a-ring", "GroupOfUnitsOfARing", ["16U60"],
      ["unit group", "group of units"], ["invertible element of a ring"], ["ring", "group", "division-ring"], r"""
The invertible elements of a unital ring form a group under multiplication.
\begin{definition}
In an associative unital ring \(R\), an \emph{invertible element of a ring}, or unit, is an \(a\in R\) admitting \(b\in R\) with \(ab=ba=1\). The \emph{group of units of a ring} is \(R^\times=\{a:a\text{ is invertible}\}\), with the ring multiplication.
\end{definition}
\begin{proof}
The identity is a unit. If \(a,b\) are units, then \((ab)^{-1}=b^{-1}a^{-1}\), as multiplication verifies on both sides. Each unit's inverse is itself a unit; associativity is inherited from \(R\). Inverses are unique: if \(ba=1=ac\), then \(b=b(ac)=(ba)c=c\).
\end{proof}
\begin{example}
The integers have units \(1,-1\). A division ring has \(R^\times=R\setminus\{0\}\). In the zero ring, \(1=0\) and the unit group is the one-element group; the definition does not exclude this case.
\end{example}
"""),
entry("ring", "principal ideal domain", "principal-ideal-domain", "PID", ["13F10"], ["PID", "principal ideal domains"],
      ["principal ideal of a commutative ring"], ["integral-domain", "bezout-domain", "gcd-domain", "integer"], r"""
A principal ideal domain requires every ideal, not just each finitely generated ideal, to have one generator.
\begin{definition}
For a commutative unital ring \(R\), the \emph{principal ideal of a commutative ring} generated by \(a\) is \((a)=\{ra:r\in R\}\). A \emph{principal ideal domain} is an integral domain in which every ideal equals \((a)\) for some element \(a\). The zero ideal is \((0)\).
\end{definition}
\begin{example}
The integers form a principal ideal domain. If an ideal \(I\ne0\) is given, choose its least positive member \(d\). For \(a\in I\), division gives \(a=qd+r\), \(0\le r<d\). Since \(r=a-qd\in I\), minimality forces \(r=0\). Thus \(I=(d)\). Every field is another example, since its only ideals are \(0\) and itself.
\end{example}
\begin{remark}
The integral-domain hypothesis excludes rings with zero divisors. A Bezout domain imposes the one-generator condition only on finitely generated ideals; the stronger requirement here applies to every ideal.
\end{remark}
"""),
entry("ring", "Euclidean domain", "euclidean-domain", "EuclideanRing", ["13F10"], ["Euclidean ring", "Euclidean domains"],
      ["Euclidean function"], ["principal-ideal-domain", "integral-domain", "integer"], r"""
A Euclidean domain permits division with a remainder smaller according to a chosen function.
\begin{definition}
An integral domain \(D\) is a \emph{Euclidean domain} if it admits a \emph{Euclidean function} \(d:D\setminus\{0\}\to\mathbb{N}\) such that for all \(a,b\in D\), \(b\ne0\), there exist \(q,r\in D\) with \(a=bq+r\) and either \(r=0\) or \(d(r)<d(b)\). Here \(\mathbb{N}\) includes zero. No additional monotonicity axiom on \(d\) is imposed in this convention.
\end{definition}
\begin{proposition}
Every Euclidean domain is a principal ideal domain.
\end{proposition}
\begin{proof}
For a nonzero ideal \(I\), choose \(b\in I\setminus\{0\}\) with \(d(b)\) minimal. Dividing any \(a\in I\) by \(b\) gives a remainder \(r=a-bq\in I\). If it were nonzero, its smaller value of \(d\) would contradict minimality. Hence every \(a\in I\) is divisible by \(b\), so \(I=(b)\). The zero ideal is already principal.
\end{proof}
\begin{example}
For \(\mathbb{Z}\), take \(d(n)=|n|\); ordinary integer division supplies the required remainder. This Euclidean notion concerns rings, not Euclidean geometry or Euclidean fields.
\end{example}
"""),
entry("ring", "local ring", "local-ring", "LocalRing", ["13H99", "16U60"], ["commutative local ring", "local rings"],
      ["maximal ideal of a commutative ring", "residue field of a local ring"], ["ring", "group-of-units-of-a-ring", "field"], r"""
A local ring is defined by a uniqueness condition on maximal left ideals. The commutative case is especially important in algebraic geometry.
\begin{definition}
A \emph{local ring} is a nonzero associative unital ring with exactly one maximal left ideal. Here a maximal left ideal is a proper additive subgroup closed under multiplication from the left by ring elements and contained in no larger proper left ideal.

For commutative rings, left ideals are simply ideals. A \emph{maximal ideal of a commutative ring} is a proper ideal contained in no larger proper ideal, so a commutative ring is local precisely when it has exactly one maximal ideal \(\mathfrak m\). Its \emph{residue field} is \(R/\mathfrak m\), whose elements are additive cosets with addition and multiplication induced from \(R\).
\end{definition}
\begin{proposition}
For a commutative local ring, the residue field is indeed a field.
\end{proposition}
\begin{proof}
If \(a\notin\mathfrak m\), maximality implies \(\mathfrak m+(a)=R\). Thus \(1=u+ra\) for \(u\in\mathfrak m\), and the coset of \(r\) is an inverse of the coset of \(a\). The quotient is nonzero because \(\mathfrak m\) is proper. The ideal property makes coset multiplication well-defined.
\end{proof}
\begin{example}
Every field is local, with maximal ideal \(0\). The ring \(\mathbb{Z}/4\mathbb{Z}\) is local with maximal ideal \(\{0,2\}\): a proper ideal cannot contain the units \(1\) or \(3\), and \(\{0,2\}\) is the largest remaining proper ideal.
\end{example}
\begin{remark}
For noncommutative rings, the definition uses maximal left ideals, not merely maximal two-sided ideals. The residue-field assertion above is restricted to the commutative case.
\end{remark}
"""),
entry("ring", "formal power series ring", "formal-power-series-ring", "FormalPowerSeriesRing", ["13F25"],
      ["ring of formal power series"], ["formal power series"], ["ring", "group-of-units-of-a-ring", "local-ring"], r"""
Formal power series are coefficient sequences; their definition involves no analytic convergence.
\begin{definition}
For a commutative unital ring \(R\), a \emph{formal power series} is \(f=\sum_{n\ge0}a_nx^n\) with \(a_n\in R\). The \emph{formal power series ring} \(R[[x]]\) uses coefficientwise addition and multiplication
\[
\left(\sum_{n\ge0}a_nx^n\right)\left(\sum_{n\ge0}b_nx^n\right)
=\sum_{n\ge0}\left(\sum_{i=0}^n a_i b_{n-i}\right)x^n.
\]
Each coefficient uses only a finite sum. The ring laws follow by rearranging finite sums for each coefficient.
\end{definition}
\begin{proposition}
A series is invertible exactly when its constant coefficient is invertible in \(R\).
\end{proposition}
\begin{proof}
An inverse forces \(a_0b_0=1\). Conversely set \(b_0=a_0^{-1}\) and recursively set \(b_n=-a_0^{-1}\sum_{i=1}^n a_i b_{n-i}\) for \(n\ge1\). The coefficient formula then gives \(fg=1\); commutativity gives \(gf=1\).
\end{proof}
\begin{example}
The identity \((1-x)(1+x+x^2+\cdots)=1\) is valid formally over every such \(R\), since all positive-degree coefficients cancel. It imposes no numerical bound on \(x\).
\end{example}
"""),
entry("field", "primitive element of a field extension", "primitive-element-of-a-field-extension", "PrimitiveElementOfAFieldExtension", ["12F05"],
      ["primitive field-extension element"], ["simple field extension"], ["field-extension", "quadratic-extension"], r"""
A primitive element generates the whole extension from its base field.
\begin{definition}
For \(\alpha\in L\), let \(K(\alpha)\) be the smallest subfield of \(L\) containing \(K\) and \(\alpha\), equivalently the intersection of all such subfields. An extension \(L/K\) is a \emph{simple field extension} if \(L=K(\alpha)\) for some \(\alpha\). Such an \(\alpha\) is a \emph{primitive element of the field extension}.
\end{definition}
\begin{example}
The element \(\sqrt{2}\) is primitive for \(\mathbb{Q}(\sqrt{2})/\mathbb{Q}\). So is \(1+\sqrt{2}\), because subtracting \(1\) recovers \(\sqrt{2}\). The indeterminate \(t\) is primitive for \(K(t)/K\), showing that simple extensions need not be algebraic or finite.
\end{example}
\begin{remark}
This meaning of primitive is different from a generator of a finite field's multiplicative group or a primitive root modulo an integer. No separability hypothesis belongs in this definition.
\end{remark}
"""),
entry("field", "purely inseparable field extension", "purely-inseparable-field-extension", "PurelyInseparableFieldExtension", ["12F15"],
      ["purely inseparable extension"], ["purely inseparable element"], ["field-extension", "separable-field-extension", "example-of-nonperfect-field"], r"""
In a purely inseparable extension, taking sufficiently high prime-power powers returns every element to the base field.
\begin{definition}
Suppose \(K\) has characteristic \(p>0\). An element \(\alpha\in L\) is \emph{purely inseparable} over \(K\) if \(\alpha^{p^n}\in K\) for some integer \(n\ge0\). The extension \(L/K\) is \emph{purely inseparable} if this holds for every \(\alpha\in L\). Such elements are algebraic, since they satisfy \(x^{p^n}-\alpha^{p^n}\in K[x]\). In characteristic zero, only the trivial extension \(K/K\) is called purely inseparable.
\end{definition}
\begin{example}
For an indeterminate \(t\), the extension \(\mathbb{F}_p(t)/\mathbb{F}_p(t^p)\) is purely inseparable. Every rational function \(f(t)/g(t)\) has \(p\)-th power \(f(t^p)/g(t^p)\), which belongs to the base field. This follows from the binomial theorem: the intermediate binomial coefficients are divisible by \(p\), and coefficients in \(\mathbb{F}_p\) have \(p\)-th power equal to themselves.
\end{example}
\begin{remark}
The exponent \(n\) may depend on the element; a single uniform exponent is not required for an arbitrary extension. The trivial extension satisfies the definition by taking \(n=0\).
\end{remark}
""", ("The Stacks Project", "Purely inseparable extensions", "https://stacks.math.columbia.edu/tag/09HE")),
entry("field", "transcendence basis", "transcendence-basis", "TranscendenceBasis", ["12F20"], ["transcendence bases"],
      ["algebraically independent family"], ["field-extension", "dependence-relation", "rational-function"], r"""
A transcendence basis separates freely varying transcendental elements from the algebraic part of an extension.
\begin{definition}
A subset \(B\subseteq L\) is an \emph{algebraically independent family} over \(K\) if no nonzero polynomial over \(K\) vanishes at any finite tuple of distinct elements of \(B\). It is a \emph{transcendence basis} for \(L/K\) if it is algebraically independent and every element of \(L\) is algebraic over \(K(B)\), the smallest subfield containing \(K\cup B\).
\end{definition}
\begin{example}
For independent indeterminates \(t_1,\ldots,t_n\), the set \(\{t_1,\ldots,t_n\}\) is a transcendence basis of \(K(t_1,\ldots,t_n)/K\): no formal nonzero polynomial becomes zero on those indeterminates, and adjoining them already gives the whole field. The empty set is a transcendence basis precisely for algebraic extensions, since \(K(\varnothing)=K\).
\end{example}
\begin{remark}
This is not a vector-space basis: the expressions allowed involve polynomial and rational operations, followed by algebraic extension, rather than just linear combinations. The dependence relation entry explains the associated algebraic dependence viewpoint.
\end{remark}
""", ("The Stacks Project", "Transcendence", "https://stacks.math.columbia.edu/tag/030D")),
entry("field", "field trace", "field-trace", "FieldTrace", ["12F05"], ["trace of a finite field extension"],
      ["multiplication endomorphism of a field extension"], ["field-extension", "matrix-ring", "quadratic-extension"], r"""
Field trace converts an element of a finite extension into a scalar in the base field.
\begin{definition}
Let \(L/K\) have finite degree \(n\). For \(\alpha\in L\), its \emph{multiplication endomorphism} is the \(K\)-linear map \(m_\alpha:L\to L\), \(x\mapsto\alpha x\). The \emph{field trace} \(\operatorname{Tr}_{L/K}(\alpha)\) is the sum of the diagonal entries of a matrix representing \(m_\alpha\) in a \(K\)-basis of \(L\).
\end{definition}
\begin{proposition}
This value is independent of the chosen basis and is \(K\)-linear in \(\alpha\).
\end{proposition}
\begin{proof}
Changing basis replaces a matrix \(A\) by \(P^{-1}AP\). The identity \(\operatorname{tr}(UV)=\operatorname{tr}(VU)\) follows by interchanging the two finite indices in \(\sum_{i,j}u_{ij}v_{ji}\). It gives \(\operatorname{tr}(P^{-1}AP)=\operatorname{tr}(A)\). Finally \(m_{\alpha+\beta}=m_\alpha+m_\beta\) and \(m_{c\alpha}=c m_\alpha\), proving linearity.
\end{proof}
\begin{example}
For \(L=\mathbb{Q}(\sqrt{2})\), multiplication by \(u+v\sqrt{2}\) has matrix \(\begin{pmatrix}u&2v\cr v&u\end{pmatrix}\) in the basis \(1,\sqrt{2}\), so its trace is \(2u\). For \(c\in K\), the matrix is \(cI_n\), giving \(\operatorname{Tr}_{L/K}(c)=nc\).
\end{example}
""", ("The Stacks Project", "Trace and norm", "https://stacks.math.columbia.edu/tag/0BIE")),
entry("field", "field norm", "field-norm", "FieldNorm", ["12F05"], ["norm of a finite field extension"],
      ["norm-one element"], ["field-extension", "field-trace", "group-of-units-of-a-ring"], r"""
The field norm is the determinant analogue of field trace; it is not a metric or vector-space norm.
\begin{definition}
For a finite extension \(L/K\), the \emph{field norm} is \(N_{L/K}(\alpha)=\det(m_\alpha)\), where \(m_\alpha:x\mapsto\alpha x\) is regarded as a \(K\)-linear endomorphism of \(L\). A \emph{norm-one element} is an \(\alpha\in L\) with \(N_{L/K}(\alpha)=1\).
\end{definition}
\begin{proposition}
The norm is independent of basis, is multiplicative, and maps nonzero elements to nonzero elements. Norm-one elements form a subgroup of \(L^\times\).
\end{proposition}
\begin{proof}
Basis changes conjugate the matrix by an invertible matrix, leaving its determinant unchanged by determinant multiplicativity. Since \(m_{\alpha\beta}=m_\alpha m_\beta\), the same determinant identity gives \(N(\alpha\beta)=N(\alpha)N(\beta)\). For \(\alpha\ne0\), \(m_{\alpha^{-1}}\) is the inverse map, so \(N(\alpha)N(\alpha^{-1})=1\). Also \(N(1)=1\). These identities establish the subgroup assertion.
\end{proof}
\begin{example}
Using the matrix in the field trace entry gives \(N_{\mathbb{Q}(\sqrt{2})/\mathbb{Q}}(u+v\sqrt{2})=u^2-2v^2\). Thus \(3+2\sqrt{2}\) has norm one, while \(\sqrt{2}\) has norm \(-2\); positivity is not part of this algebraic notion.
\end{example}
""", ("The Stacks Project", "Trace and norm", "https://stacks.math.columbia.edu/tag/0BIE")),
entry("computability", "many-one reducibility", "many-one-reducibility", "ManyOneReducibility", ["03D30"],
      ["many-one reduction", "mapping reducibility"], ["many-one equivalent sets"], ["recursive-set", "formal-definition-of-a-turing-machine"], r"""
Many-one reduction translates each membership question into one membership question about another set.
\begin{definition}
For \(A,B\subseteq\mathbb{N}\), write \(A\le_m B\) if there is a total computable function \(f:\mathbb{N}\to\mathbb{N}\) with \(x\in A\) if and only if \(f(x)\in B\). This is \emph{many-one reducibility}. The sets are \emph{many-one equivalent} when both \(A\le_m B\) and \(B\le_m A\) hold. Computable means implementable by a \PMlinkname{Turing machine}{FormalDefinitionOfATuringMachine}; total requires halting on every input.
\end{definition}
\begin{proposition}
If \(A\le_m B\) and \(B\) is a \PMlinkname{recursive set}{RecursiveSet}, then \(A\) is recursive.
\end{proposition}
\begin{proof}
On input \(x\), compute \(f(x)\) and run a halting membership algorithm for \(B\) on that output. Both stages halt, and the defining equivalence gives the correct answer for \(A\).
\end{proof}
\begin{example}
Let \(A\) be the even natural numbers and \(B=\{0\}\). The function returning \(0\) on even inputs and \(1\) on odd inputs witnesses \(A\le_m B\). Unlike polynomial-time reducibility, this definition imposes no running-time bound beyond termination.
\end{example}
"""),
entry("computability", "Turing reducibility", "turing-reducibility", "TuringReducibility", ["03D28", "03D10"],
      ["Turing reduction", "relative computability"], ["oracle Turing machine", "Turing equivalent sets"],
      ["many-one-reducibility", "recursive-set", "formal-definition-of-a-turing-machine"], r"""
Turing reduction permits an algorithm to ask membership questions of an oracle while computing its answer.
\begin{definition}
An \emph{oracle Turing machine} with oracle \(B\subseteq\mathbb{N}\) may query whether a chosen number belongs to \(B\) and receive the correct yes-or-no answer. For sets \(A,B\), write \(A\le_T B\) if such a machine halts on every input and decides membership in \(A\). This is \emph{Turing reducibility}. Queries may depend on earlier answers; each halting computation uses finitely many queries, without a required uniform bound. Sets are \emph{Turing equivalent} if each is Turing reducible to the other.
\end{definition}
\begin{proposition}
Many-one reducibility implies Turing reducibility. If \(A\le_T B\) and \(B\) is a \PMlinkname{recursive set}{RecursiveSet}, then \(A\) is recursive.
\end{proposition}
\begin{proof}
For a many-one reduction, compute \(f(x)\) and make one oracle query. For the second assertion, replace each oracle query by the halting membership algorithm for \(B\). On each input the original computation halts after finitely many queries, so its simulation halts too.
\end{proof}
\begin{example}
For any \(B\), its complement is Turing reducible to \(B\): ask whether \(x\in B\) and reverse the answer. The definition does not require that the oracle set itself be computable.
\end{example}
"""),
]

EXPECTED_COUNTS = {"set": 3, "group": 4, "ring": 6, "field": 5, "computability": 2}

# Targets reviewed in their mathematical context, rather than accepted merely
# because their spelling matched a catalog alias.
REVIEWED_TARGETS = set("""supremum intersection group lagranges-theorem-for-finite-groups
homomorphism-between-algebraic-systems associative commutative module ring division-ring
integer bezout-domain integral-domain field artinian-ring field-extension indeterminate
every-finite-integral-domain-is-a-field primitive-root rational-function dependence-relation
linear-transformation invertible-matrix complement recursive-set
formal-definition-of-a-turing-machine""".split()) | {e["slug"] for e in ENTRIES}
INCOMING = {
    "gcd-domain": {"group-of-units-of-a-ring", "euclidean-domain", "principal-ideal-domain"},
    "bezout-domain": {"principal-ideal-domain"},
    "subsemigroup-of-a-cyclic-semigroup": {"cyclic-group"},
    "fittings-lemma": {"local-ring"},
    "primitive-root": {"group-of-units-of-a-ring", "cyclic-group"},
}


def link_targets(html):
    links = Links()
    links.feed(html)
    return {a["href"].split("slug=", 1)[1] for a, _ in links.links
            if a.get("href", "").startswith("concept.html?slug=")}


def verify(c):
    assert Counter(e["area"] for e in ENTRIES) == EXPECTED_COUNTS
    for e in ENTRIES:
        d = fetch_public_math_concept_detail(c.cursor(), e["slug"])
        assert d and d["owner"] == "CWoo"
        assert d["cleaned_tex"] == source(e), e["slug"]
        for key in ["synonyms", "definitions"]:
            assert set(d[key]) == set(e[key]), (e["slug"], key)
        assert set(d["types"]) == set(document_types(e))
        assert {r["code"] for r in d["classifications"]} == set(e["classifications"])
        html = d["display_tex"]
        targets = link_targets(html)
        assert targets <= REVIEWED_TARGETS, (e["slug"], targets - REVIEWED_TARGETS)
        assert e["slug"] not in targets
        assert r"\PMlink" not in html and "math-env-definition" in html and "math-env-example" in html
        assert html.count('class="math-env math-env-proof"') == e["body"].count(r"\begin{proof}")
        math_pattern = r"\\\(.*?\\\)|\\\[.*?\\\]"
        assert re.findall(math_pattern, d["cleaned_tex"], re.S) == re.findall(math_pattern, html, re.S)
        rows = c.execute("SELECT related_concept_id FROM math_related_concepts WHERE concept_id=?", (d["id"],)).fetchall()
        assert len(rows) == len(e["related"]) and all(r[0] for r in rows)
        assert any(r.get("slug") == e["slug"] for r in search_public_math_library(c.cursor(), e["title"])["data"])
        print("Verified:", d["id"], e["area"], e["slug"])
    for slug, expected in INCOMING.items():
        detail = fetch_public_math_concept_detail(c.cursor(), slug)
        assert expected <= link_targets(detail["display_tex"]), slug
    assert c.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert not c.execute("PRAGMA foreign_key_check").fetchall()
    print("Verified incoming links, reviewed outgoing targets, and database integrity.")


def apply(path):
    if not path.is_file():
        raise FileNotFoundError(path)
    with sqlite3.connect(path) as c:
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA foreign_keys=ON")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for e in ENTRIES:
            if c.execute("SELECT id FROM math_concepts WHERE slug=?", (e["slug"],)).fetchone():
                continue
            for term in [e["title"], *e["synonyms"], *e["definitions"]]:
                collision = c.execute("""SELECT title FROM math_concepts WHERE lower(title)=lower(?)
                    UNION SELECT synonym_text FROM math_synonyms WHERE lower(synonym_text)=lower(?)
                    UNION SELECT defined_term FROM math_definitions WHERE lower(defined_term)=lower(?)""", (term,term,term)).fetchone()
                assert not collision, (e["slug"],term)
            for code in e["classifications"]:
                assert c.execute("SELECT id FROM math_classifications WHERE code=?", (code,)).fetchone(), code
            related = [c.execute("SELECT canonical_name FROM math_concepts WHERE slug=?", (s,)).fetchone()[0] for s in e["related"]]
            create_math_concept(c.cursor(), e["canonical"], e["slug"], e["title"], now, "CWoo", source(e), 1,
                e["classifications"], document_types(e), e["synonyms"], e["definitions"], related)
        verify(c)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=SRC.parent / "portfolio.db")
    apply(parser.parse_args().db)
