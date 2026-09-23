"""Abel--Ruffini over Q, with a complete finite Galois obstruction proof chain.

Search review: Galois group already defined; fixed field only mentioned in the
Galois-connection example. No radical-solvability or quintic theorem existed.
We prove the necessary direction of the radical criterion, not an unproved iff.
Analysis inputs are the fundamental theorem of algebra, intermediate
value theorem, and elementary derivative monotonicity; the algebraic steps are
proved here or explicitly linked to existing proved results.
"""
import argparse
from datetime import datetime
from pathlib import Path
import re
import sqlite3
import sys
SRC=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(SRC))
from services.math.concept_create_service import create_math_concept
from services.math.concept_render_service import render_tex_reusing_existing_diagrams
from services.math.public_concept_detail_service import fetch_public_math_concept_detail
from services.math.public_search_service import search_public_math_library
from add_eight_algebra_concepts import source, Links
from add_sylow_theorems import document_types
from add_twenty_concepts_20260922 import ESCAPES

FIELD_REF=("J. S. Milne", "Fields and Galois Theory, Chapters 2--5", "https://www.jmilne.org/math/Books/FT0.pdf")
GROUP_REF=("R. Sharifi", "Abstract Algebra, Chapter 7: solvable groups", "https://www.math.ucla.edu/~sharifi/notes/algebra-ch07.html")
POLY_REF=("D. Evans", "Galois Theory III: Fields and polynomials", "https://www.maths.dur.ac.uk/users/daniel.evans/GaloisTheory/Notes/fields-and-polynomials.html")


def entry(title,slug,canonical,codes,aliases,definitions,related,body,ref=FIELD_REF):
    return dict(title=title,slug=slug,canonical=canonical,classifications=codes,synonyms=aliases,
                definitions=definitions,related=related,body=body,reference=ref,
                escapes=list(ESCAPES)+["embedding","simple","normal","solvable","radical","primitive",
                "sign","even","odd","cycle","transitive","transposition","fixed","extension",
                "orbit","stabilizer","surjective","injective","bijective","automorphism","endomorphism",
                "homomorphism","conjugate","conjugation","root of unity","finite group","permutation",
                "symmetric","alternating","perfect","real","complex","bound","context","relation",
                "spanning","relatively prime","Bezout identity","normal subgroup","length","nor",
                "primitive root","top","Absorb","reduced","translation","connected","labeling",
                "theory","Galois correspondence","language","reversal","algebra"])


ENTRIES=[
entry("extension of field embeddings", "extension-of-field-embeddings", "ExtensionOfFieldEmbeddings", ["12F05","12F10"],
      ["field embedding extension lemma"], ["field embedding", "tower law for finite field extensions"],
      ["field-extension","separable-field-extension","splitting-field-of-a-polynomial","galois-group"],r"""
\begin{definition}
A \emph{field embedding} is a field homomorphism preserving one; it is injective, since a nonzero element in its kernel would give \(1=0\) after multiplication by its inverse. A \(K\)-embedding fixes every element of \(K\).
\end{definition}
\begin{lemma}
For finite extensions \(K\subseteq E\subseteq L\), the tower law is \([L:K]=[L:E][E:K]\). If \(a_i\) is a \(K\)-basis of \(E\) and \(b_j\) an \(E\)-basis of \(L\), then \(a_i b_j\) is a \(K\)-basis of \(L\).
\end{lemma}
\begin{proof}
Expand a vector first in the \(b_j\), then each coefficient in the \(a_i\), to obtain spanning. In a zero linear combination, independence of the \(b_j\) makes each coefficient in \(E\) zero, and independence of the \(a_i\) then makes each coefficient in \(K\) zero.
\end{proof}
\begin{lemma}
Let \(E/K\) be finite and \(\Omega\) an algebraically closed field. Every embedding \(\sigma:K\to\Omega\) extends to an embedding \(E\to\Omega\).
\end{lemma}
\begin{proof}
For a simple algebraic extension \(K(\alpha)\), let \(m\) be the minimal polynomial. Polynomial division shows that every polynomial vanishing at \(\alpha\) is divisible by \(m\). The ring \(K[\alpha]\) is a field: for a nonzero polynomial residue \(h\), irreducibility of \(m\) and the Euclidean algorithm give \(uh+vm=1\), hence an inverse. Thus \(K(\alpha)=K[X]/(m)\). Choose a root \(\beta\in\Omega\) of the polynomial obtained by applying \(\sigma\) to the coefficients of \(m\). That transformed polynomial is irreducible over \(\sigma(K)\), so evaluation at \(\beta\) gives the required embedding of the quotient field. A finite extension has finitely many generators (a finite vector-space basis suffices); repeat this step along those generators.
\end{proof}
\begin{proposition}
Let \(L/K\) be a finite splitting field in characteristic zero inside \(\Omega\). Every \(K\)-embedding of \(L\) into \(\Omega\) is an automorphism of \(L\). If \(K\subseteq E\subseteq L\) and \(E/K\) is normal, restriction \(\operatorname{Gal}(L/K)\to\operatorname{Aut}_K(E)\) is onto. If an irreducible polynomial splits in \(L\), these automorphisms act transitively on its roots.
\end{proposition}
\begin{proof}
An embedding permutes the finite set of roots generating the splitting field; injectivity makes that permutation bijective, so its image is \(L\). An automorphism of \(E\) extends to \(L\) by the lemma, proving surjectivity; normality ensures all restrictions preserve \(E\). For two roots of an irreducible polynomial, the quotient-field construction gives an isomorphism of the simple extensions sending one root to the other. Extend it to \(L\).
\end{proof}
\begin{remark}
In characteristic zero every irreducible polynomial is separable: its formal derivative is nonzero of smaller degree, so it is relatively prime to the polynomial. A repeated root would annihilate both and contradict their Bezout identity. Thus finite splitting fields in characteristic zero are Galois. Normality of a splitting field is also proved in the normal-closure entry.
\end{remark}
"""),
entry("normal closure of a field extension", "normal-closure-of-a-field-extension", "NormalClosureOfAFieldExtension", ["12F05","12F10"],
      ["normal closure in field theory"], [], ["normal-field-extension","splitting-field-of-a-polynomial","extension-of-field-embeddings","galois-group"],r"""
Fix a finite extension \(E/K\) inside an algebraically closed field \(\Omega\).
\begin{definition}
The \emph{normal closure of a field extension} \(E/K\), inside the fixed algebraically closed field \(\Omega\) containing \(E\), is the smallest subfield \(N\subseteq\Omega\) that contains \(E\) and is normal over \(K\). Thus
\[
K\subseteq E\subseteq N\subseteq\Omega.
\]
Here an intermediate field means a field between \(K\) and \(\Omega\); requiring it to contain \(E\) narrows the choice to fields between \(E\) and \(\Omega\). We enlarge \(E\) to obtain normality over \(K\), not merely over \(E\).

One may choose \(\Omega\) to be an algebraic closure of \(E\), which is also an algebraic closure of \(K\) because \(E/K\) is finite. A larger algebraically closed ambient field is also allowed, such as \(\mathbb C\) for finite extensions of \(\mathbb Q\) embedded in \(\mathbb C\).
\end{definition}
\begin{theorem}
Write \(E=K(\alpha_1,\ldots,\alpha_r)\) and let \(m_i\) be the minimal polynomials over \(K\). The splitting field \(N\) of \(\prod_i m_i\) in \(\Omega\) is the normal closure. It is finite. In characteristic zero it is Galois.
\end{theorem}
\begin{proof}
Adjoining finitely many algebraic roots gives a finite extension by the tower law. Every \(K\)-embedding of \(N\) into \(\Omega\) preserves \(N\), since it permutes the roots generating it. If an irreducible polynomial \(h\in K[X]\) has a root \(a\in N\), any other root \(b\in\Omega\) gives an embedding \(K(a)\to\Omega\) sending \(a\) to \(b\). The embedding-extension lemma extends it to \(N\), so \(b\in N\). Hence \(h\) splits in \(N\), proving normality. Any normal field containing \(E\) must contain all roots of each \(m_i\), so contains \(N\). Separability in characteristic zero follows from the derivative argument in the embedding entry.
\end{proof}
\begin{example}
The normal closure of \(\mathbb Q(\sqrt[3]{2})/\mathbb Q\) in \(\mathbb C\) is \(\mathbb Q(\sqrt[3]{2},\zeta_3)\), where \(\zeta_3=e^{2\pi i/3}\). The polynomial \(X^3-2\) is irreducible by Eisenstein's criterion at \(2\), and its three roots are \(\sqrt[3]{2}\), \(\zeta_3\sqrt[3]{2}\), and \(\zeta_3^2\sqrt[3]{2}\).
\end{example}
\begin{remark}
Normal closure here is a field-theoretic construction, distinct from the normal closure of a subgroup. In a fixed algebraically closed ambient field the smallest field is unique, not merely unique up to isomorphism.
\end{remark}
"""),
entry("solvable group", "solvable-group", "SolvableGroup", ["20F16","20D10"], ["soluble group"],
      ["derived series", "quotient group"], ["group","commutator-subgroup"],r"""
\begin{definition}
The \emph{derived series} is \(G^{(0)}=G\), \(G^{(i+1)}=[G^{(i)},G^{(i)}]\), using the commutator convention \([a,b]=aba^{-1}b^{-1}\). A \emph{solvable group} has \(G^{(r)}=1\) for some finite \(r\). This definition does not require finiteness of \(G\).

For a normal subgroup \(N\), the \emph{quotient group} \(G/N\) consists of cosets \(gN\) with multiplication \((gN)(hN)=ghN\). Normality makes this independent of representatives: replacing \(g,h\) by \(gn,hm\) introduces the factor \(h^{-1}nhm\in N\). Associativity and inverses descend from \(G\).
\end{definition}
\begin{proposition}
Subgroups and homomorphic images of solvable groups are solvable. If \(N\) is normal in \(G\), and both \(N\) and \(G/N\) are solvable, then \(G\) is solvable.
\end{proposition}
\begin{proof}
For \(H\le G\), induction gives \(H^{(j)}\le G^{(j)}\). For a surjective homomorphism \(\phi:G\to Q\), the identity \(\phi([a,b])=[\phi(a),\phi(b)]\) gives \(\phi(G^{(j)})=Q^{(j)}\). If \((G/N)^{(r)}=1\), then \(G^{(r)}\subseteq N\); if \(N^{(s)}=1\), taking \(s\) more derived subgroups yields \(G^{(r+s)}=1\).
\end{proof}
\begin{example}
Every abelian group is solvable because all its commutators are the identity. Any group built in finitely many steps by extensions with abelian kernels and abelian initial group is solvable by the proposition.
\end{example}
""",GROUP_REF),
entry("symmetric groups of degree at least five are not solvable", "nonsolvability-of-symmetric-groups", "NonsolvabilityOfSymmetricGroups", ["20B30","20F16"],
      ["nonsolvability of S5"], ["permutation cycle", "transposition", "sign of a permutation", "alternating group"],
      ["solvable-group","commutator-subgroup","group-actions-and-homomorphisms","alternating-group-is-a-normal-subgroup-of-the-symmetric-group"],r"""
The symmetric group \(S_n\), already defined as a group of bijections, consists of all permutations of \(\{1,\ldots,n\}\). Products below act from right to left.
\begin{definition}
A \emph{permutation cycle} \((a_1,\ldots,a_r)\) sends each listed element to the next, the last to the first, and fixes the others. A \emph{transposition} is a cycle of length two. The \emph{sign of a permutation} is the factor \(\pm1\) by which it changes \(\prod_{i<j}(X_i-X_j)\) on permuting the variables. The \emph{alternating group} \(A_n\) consists of sign-one permutations.
\end{definition}
\begin{lemma}
Sign is a homomorphism, each transposition has sign \(-1\), and \(A_n\) is generated by the 3-cycles.
\end{lemma}
\begin{proof}
Composition multiplies the factors changing the displayed polynomial; swapping two variables changes its sign (the factor between them changes sign and other factors pair off). Every permutation decomposes into disjoint cycles by following each element's finite orbit, and
\[
(a_1,\ldots,a_r)=(a_1,a_r)\cdots(a_1,a_2).
\]
Thus a sign-one permutation is a product of an even number of transpositions. Pair these factors: identical pairs cancel, pairs sharing one letter give a 3-cycle, and disjoint pairs satisfy \((a,b)(c,d)=(a,c,b)(a,c,d)\). Conversely every 3-cycle is a product of two transpositions and has sign one.
\end{proof}
\begin{theorem}
For \(n\ge5\), \([A_n,A_n]=A_n\ne1\), so neither \(A_n\) nor \(S_n\) is solvable.
\end{theorem}
\begin{proof}
Put \(a=(1,2,3)\) and \(b=(1,2)(4,5)\). Both lie in \(A_n\), and \(bab^{-1}=a^{-1}\). Hence \([a,b]=a^2\), a 3-cycle. Every 3-cycle is conjugate to this one by an element of \(A_n\): first choose a permutation carrying its ordered three letters to the desired letters; if that permutation is odd, compose on the right with a transposition of two unused letters. There are two such letters because \(n\ge5\). This changes parity without changing the conjugate. The commutator subgroup is invariant under conjugation, so it contains every 3-cycle and therefore all of \(A_n\). Its derived series never becomes trivial. Since subgroups of solvable groups are solvable, \(S_n\) cannot be solvable either.
\end{proof}
""",GROUP_REF),
entry("cyclotomic extension", "cyclotomic-extension", "CyclotomicExtension", ["11R18","12F10"], [],
      ["root of unity", "primitive root of unity"], ["galois-group","splitting-field-of-a-polynomial","extension-of-field-embeddings","cyclic-group"],r"""
This entry concerns subfields \(K\subseteq\mathbb C\).
\begin{definition}
An \(n\)-th \emph{root of unity} satisfies \(z^n=1\). It is a \emph{primitive root of unity} of order \(n\) if \(n\) is its multiplicative order. With \(\zeta_n=e^{2\pi i/n}\), a \emph{cyclotomic extension} is \(K(\zeta_n)/K\).
\end{definition}
\begin{proposition}
The extension \(K(\zeta_n)/K\) is finite Galois with abelian Galois group.
\end{proposition}
\begin{proof}
The \(n\) distinct numbers \(1,\zeta_n,\ldots,\zeta_n^{n-1}\) are roots of \(X^n-1\). The polynomial root bound shows that these are all its roots, so the field is its splitting field; characteristic zero gives separability. An automorphism sends \(\zeta_n\) to \(\zeta_n^a\) of the same order, so \(a\) is invertible modulo \(n\). This assignment is injective because \(\zeta_n\) generates the extension. Composition multiplies exponents, and multiplication modulo \(n\) commutes, so the Galois group is abelian. Surjectivity onto all invertible residues is not asserted for arbitrary \(K\).
\end{proof}
\begin{example}
For \(K=\mathbb Q\) and \(n=4\), this is \(\mathbb Q(i)/\mathbb Q\), with identity and complex conjugation as its two automorphisms.
\end{example}
"""),
entry("radical extension", "radical-extension", "RadicalExtension", ["12F05","12F10"], [],
      ["radical tower", "solvability by radicals", "polynomial solvable by radicals"],
      ["field-extension","splitting-field-of-a-polynomial","cyclotomic-extension"],r"""
All fields here are subfields of \(\mathbb C\); complex intermediate radicals are allowed.
\begin{definition}
A \emph{radical tower} over \(K\) is a finite tower \(K=E_0\subseteq E_1\subseteq\cdots\subseteq E_r\), with \(E_i=E_{i-1}(\alpha_i)\) and \(\alpha_i^{m_i}\in E_{i-1}\) for some integer \(m_i\ge1\). Its top field is a \emph{radical extension}. A polynomial is \emph{solvable by radicals} over \(K\) if all its roots lie in some radical extension of \(K\). This is the meaning of \emph{solvability by radicals} here.
\end{definition}
Finite expressions made from elements of \(K\) using field operations and root extraction lie in a radical tower: list the finitely many root extractions in evaluation order. Conversely, membership in such a tower means a rational expression in finitely many successively adjoined radicals. Different finite expressions for finitely many roots can be combined into one tower by adjoining their radicals successively.
\begin{example}
The polynomial \(X^5-2\) is solvable by radicals: its roots are \(2^{1/5}\zeta_5^j\), \(0\le j<5\). First adjoin \(\zeta_5\), a fifth root of \(1\), and then \(2^{1/5}\). Thus unsolvability of quintics in general does not mean that every quintic is unsolvable.
\end{example}
\begin{remark}
A radical extension need not be normal: \(\mathbb Q(\sqrt[3]{2})\) omits the nonreal conjugate roots. Root extraction also means a finite number of operations here, not a limit of radical expressions or an approximation algorithm.
\end{remark}
"""),
entry("radical solvability implies a solvable Galois group", "radical-solvability-implies-solvable-galois-group", "RadicalSolvabilityImpliesSolvableGaloisGroup", ["12F10"], [], [],
      ["radical-extension","solvable-group","cyclotomic-extension","normal-closure-of-a-field-extension","extension-of-field-embeddings","galois-group"],r"""
Let \(K\subseteq\mathbb C\). This entry proves the necessary direction of the radical-solvability criterion, sufficient for Abel--Ruffini. The converse is not assumed or proved here.
\begin{lemma}
If a field \(F\subseteq\mathbb C\) contains all \(m\)-th roots of unity and \(a_1,\ldots,a_s\in F\setminus\{0\}\), the splitting field \(M\) over \(F\) of \(\prod_j(X^m-a_j)\) has abelian Galois group.
\end{lemma}
\begin{proof}
Choose one root \(\beta_j\) of each factor. The other roots are \(\zeta\beta_j\), where \(\zeta^m=1\), so \(M=F(\beta_1,\ldots,\beta_s)\). An automorphism sends each \(\beta_j\) to \(\zeta_j\beta_j\). Since it fixes all roots of unity, the assignment to \((\zeta_1,\ldots,\zeta_s)\) is an injective homomorphism into the abelian group of such tuples. The splitting field is separable in characteristic zero, hence Galois.
\end{proof}
\begin{theorem}
If \(f\in K[X]\) is solvable by radicals and \(L\) is its splitting field, then \(\operatorname{Gal}(L/K)\) is solvable.
\end{theorem}
\begin{proof}
Take a radical tower containing \(L\), omitting trivial steps with \(\alpha_i=0\). Write \(a_i=\alpha_i^{m_i}\), and choose a positive integer \(N\) divisible by all \(m_i\). Set \(M_0=K(\zeta_N)\), a finite Galois extension with abelian group by the cyclotomic proposition.

Inductively suppose \(M_{i-1}/K\) is finite Galois and contains \(E_{i-1}\). Let \(A_i\) be the finite set of all \(\sigma(a_i)\), for \(\sigma\in\operatorname{Gal}(M_{i-1}/K)\), and let \(M_i\) be the splitting field over \(M_{i-1}\) of \(\prod_{a\in A_i}(X^{m_i}-a)\) inside \(\mathbb C\). It contains \(\alpha_i\) and hence \(E_i\).

Every \(K\)-embedding of \(M_i\) into \(\mathbb C\) preserves \(M_{i-1}\) and permutes \(A_i\), so permutes the newly adjoined roots and preserves \(M_i\). The embedding criterion proved in the normal-closure entry makes \(M_i/K\) normal; characteristic zero makes it separable. The restriction homomorphism to \(\operatorname{Gal}(M_{i-1}/K)\) is onto by the embedding-extension lemma. Its kernel is \(\operatorname{Gal}(M_i/M_{i-1})\), abelian by the preceding lemma. The quotient by this kernel is the restriction image: the map from a coset to its image is directly well-defined and bijective. The extension property for solvable groups therefore proves inductively that \(\operatorname{Gal}(M_i/K)\) is solvable.

Finally \(L\subseteq E_r\subseteq M_r\), and restriction onto \(\operatorname{Gal}(L/K)\) is again surjective because \(L/K\) is normal. A homomorphic image of a solvable group is solvable.
\end{proof}
\begin{remark}
This construction uses normal overfields of the radical stages; it does not incorrectly assume the original radical tower is a Galois tower.
\end{remark}
"""),
entry("Gauss's lemma for integer polynomials", "gauss-lemma-for-integer-polynomials", "GaussLemmaForIntegerPolynomials", ["12E05","11C08"],
      ["Gauss lemma for polynomials"], ["primitive integer polynomial", "content of an integer polynomial"],
      ["integer","integral-domain","separable-field-extension"],r"""
\begin{definition}
The \emph{content of an integer polynomial} is the positive greatest common divisor of its coefficients, for a nonzero polynomial. A \emph{primitive integer polynomial} has content one.
\end{definition}
\begin{lemma}
A product of primitive integer polynomials is primitive.
\end{lemma}
\begin{proof}
If a prime divided every coefficient of the product, reducing modulo that prime would make the product zero in \(\mathbb F_p[X]\). But both factors remain nonzero by primitivity, and a polynomial ring over a field has no zero divisors, since the product of leading coefficients is nonzero. This is a contradiction.
\end{proof}
\begin{theorem}
A primitive polynomial of positive degree in \(\mathbb Z[X]\) factors into positive-degree factors over \(\mathbb Q\) if and only if it does so over \(\mathbb Z\).
\end{theorem}
\begin{proof}
Only one direction needs proof. Clear denominators and remove contents from rational factors to write \(f=(a/b)gh\), with \(g,h\) primitive integer polynomials and coprime nonzero integers \(a,b\), \(b>0\). Integrality forces \(b\) to divide every coefficient of \(gh\); by the lemma their greatest common divisor is one, so \(b=1\). Primitivity of \(f\) then gives \(|a|=1\). Absorb its sign into one factor.
\end{proof}
""",POLY_REF),
entry("Eisenstein's irreducibility criterion", "eisenstein-irreducibility-criterion", "EisensteinIrreducibilityCriterion", ["12E05"],
      ["Eisenstein's criterion", "Eisenstein criterion"], [], ["gauss-lemma-for-integer-polynomials","separable-field-extension"],r"""
\begin{theorem}
Let \(f(X)=a_nX^n+\cdots+a_0\in\mathbb Z[X]\) have positive degree. If a prime \(p\) satisfies \(p\nmid a_n\), \(p\mid a_i\) for \(i<n\), and \(p^2\nmid a_0\), then \(f\) is irreducible over \(\mathbb Q\).
\end{theorem}
\begin{proof}
Divide by the content, which is not divisible by \(p\); the hypotheses persist. Gauss's lemma reduces a hypothetical rational factorization to \(f=gh\) in \(\mathbb Z[X]\) with both factors of positive degree. Their leading coefficients are nonzero modulo \(p\), so their degrees survive reduction. Their product reduces to \(\overline{a_n}X^n\). Each reduced factor must be a monomial: factor out its least power of \(X\); the remaining two factors have nonzero constant terms, so their product is constant, and additivity of degrees forces each constant. Both monomials have positive degree, so both original constant terms are divisible by \(p\). Their product \(a_0\) is then divisible by \(p^2\), a contradiction.
\end{proof}
\begin{example}
The quintic \(X^5-10X+5\) satisfies the criterion at \(p=5\). The same argument at \(p=2\) applies to \(X^3-2\).
\end{example}
""",POLY_REF),
entry("a prime-degree transitive group containing a transposition", "prime-degree-transitive-group-with-transposition", "PrimeDegreeTransitiveGroupWithTransposition", ["20B35"], [],
      ["transitive permutation group"], ["group-actions-and-homomorphisms","orbit-stabilizer-theorem","sylows-theorems","nonsolvability-of-symmetric-groups"],r"""
\begin{definition}
A \emph{transitive permutation group} on a set is a subgroup of its symmetric group for which any point can be carried to any other by an element of the subgroup.
\end{definition}
\begin{theorem}
If \(p\) is prime and \(G\le S_p\) is transitive and contains a transposition, then \(G=S_p\).
\end{theorem}
\begin{proof}
Orbit-stabilizer gives \(p\mid |G|\). The existence part of Sylow's theorems supplies a subgroup of order \(p\). Any nonidentity element of that subgroup has order \(p\) by Lagrange's theorem and thus acts as a \(p\)-cycle: its disjoint-cycle lengths divide \(p\), and a nontrivial permutation on \(p\) points must have one cycle of length \(p\).

Label the points by \(\mathbb Z/p\mathbb Z\) so that this cycle is translation by one. Write the given transposition as \((a,b)\), and put \(d=b-a\ne0\). Conjugating by powers of the cycle gives all transpositions \((t,t+d)\). The edges between \(t\) and \(t+d\) form a connected graph: repeated addition of a nonzero \(d\) visits all residues modulo the prime \(p\). Transpositions on the edges of any connected graph generate every transposition. Indeed, along a simple path from \(u\) to \(v\), conjugating the last edge transposition by the product of the preceding edge transpositions produces \((u,v)\). Every permutation is a product of transpositions, as proved in the symmetric-group entry. Therefore \(G=S_p\).
\end{proof}
""",GROUP_REF),
entry("Abel-Ruffini theorem", "abel-ruffini-theorem", "AbelRuffiniTheorem", ["12F10","12E05"],
      ["unsolvability of the quintic", "insolvability of the quintic", "Abel's impossibility theorem"],
      ["Galois group of a polynomial"],
      ["galois-group","radical-extension","radical-solvability-implies-solvable-galois-group","eisenstein-irreducibility-criterion","prime-degree-transitive-group-with-transposition","nonsolvability-of-symmetric-groups","extension-of-field-embeddings"],r"""
There is no formula using finitely many field operations and root extractions that solves every quintic over \(\mathbb Q\). The obstruction is algebraic, not an inability to approximate roots. Some quintics, such as \(X^5-2\), are solvable by radicals.
\begin{definition}
For \(f\in K[X]\) in characteristic zero, the \emph{Galois group of a polynomial} is the Galois group of its splitting field over \(K\). It acts faithfully on the distinct roots, since those roots generate the splitting field. Thus, after labeling the roots of a degree-five irreducible polynomial, it is a subgroup of \(S_5\).
\end{definition}
\begin{theorem}
The polynomial \(f(X)=X^5-10X+5\) is not solvable by radicals over \(\mathbb Q\). Consequently no radical formula solves all quintics, or all polynomials of any specified degree \(n\ge5\) with rational coefficients.
\end{theorem}
\begin{proof}
Eisenstein's criterion at \(5\) proves irreducibility. Let \(L\subseteq\mathbb C\) be its splitting field. It is finite Galois in characteristic zero by the embedding and normal-closure results. Irreducibility and the embedding-extension lemma show that \(G=\operatorname{Gal}(L/\mathbb Q)\) acts transitively on its five roots.

Exactly three of these roots are real. Put \(a=2^{1/4}>1\). The derivative \(f'(x)=5x^4-10\) is positive on \(( -\infty,-a)\) and \((a,\infty)\), and negative on \((-a,a)\). Also \(f(-a)=8a+5>0\) and \(f(a)=5-8a<0\). Strict monotonicity, continuity, and the limits at infinity give exactly one root in each of these three intervals. Neither critical point is a root. The fundamental theorem of algebra accounts for the remaining two roots, which are a nonreal conjugate pair because the coefficients are real.

Complex conjugation preserves \(L\), fixes the three real roots, and exchanges that pair. Thus \(G\) contains a transposition. The prime-degree transposition theorem gives \(G=S_5\), which is not solvable by the symmetric-group theorem. But a radical solution would give a solvable Galois group by the radical-solvability theorem. This contradiction proves the first claim, hence rules out a universal radical formula for quintics.

For \(n>5\), the polynomial \(f(X)\prod_{j=1}^{n-5}(X-j)\) has degree \(n\) and contains all five roots of \(f\). A radical solution for all degree-\(n\) polynomials would solve this one and therefore \(f\), again a contradiction. This last argument concerns all degree-\(n\) polynomials, without claiming that this particular product is irreducible.
\end{proof}
\section*{Guide to the proof and further Galois theory}
The proof separates into two routes. Eisenstein's criterion and the embedding lemma identify a transitive permutation group; real-root counting supplies a transposition, forcing \(S_5\). Independently, a radical tower can be enlarged to a Galois tower with abelian successive kernels, forcing solvability. The incompatible conclusions meet in the theorem above. Every substantial algebraic step has its own linked entry.

For further study, fixed fields relate subgroups to intermediate fields, while normal closures explain how an extension acquires all its conjugate roots. These connect naturally to the existing Galois group entry. The full Galois correspondence and the converse radical-solvability criterion are further theorems, not assumptions hidden in this proof.
\begin{remark}
Abel--Ruffini does not say quintics have no roots, no numerical algorithms, or no descriptions using other special functions. It rules out a universal finite radical solution. The real-variable tools in this particular proof are the intermediate value theorem and derivative monotonicity; the algebraic closure of \(\mathbb C\) is supplied by the fundamental theorem of algebra.
\end{remark}
"""),
entry("fixed field", "fixed-field", "FixedField", ["12F10"], ["fixed field of automorphisms"], [],
      ["galois-group","galois-connection","normal-closure-of-a-field-extension","abel-ruffini-theorem"],r"""
\begin{definition}
Let \(H\) be a group of automorphisms of a field \(L\). Its \emph{fixed field} is
\[
L^H=\{a\in L:\sigma(a)=a\text{ for every }\sigma\in H\}.
\]
If all the automorphisms fix \(K\), then \(K\subseteq L^H\subseteq L\).
\end{definition}
\begin{proposition}
The set \(L^H\) is a subfield. If \(H_1\subseteq H_2\), then \(L^{H_2}\subseteq L^{H_1}\).
\end{proposition}
\begin{proof}
Every automorphism fixes \(0,1\), and preserves sums, differences, products and inverses of nonzero elements. Hence simultaneous fixed elements are closed under all field operations. Being fixed by every element of the larger group imposes every condition coming from the smaller group, giving the reversed inclusion.
\end{proof}
\begin{example}
In \(L=\mathbb Q(\sqrt2)\), conjugation \(a+b\sqrt2\mapsto a-b\sqrt2\) fixes exactly \(\mathbb Q\): equality implies \(2b\sqrt2=0\), hence \(b=0\). The trivial automorphism group fixes all of \(L\).
\end{example}
\begin{remark}
This is a field defined by an automorphism group, not the ordinary-language phrase meaning a field chosen in advance. The inclusion reversal is one part of the Galois correspondence; the full bijection requires its own theorem and hypotheses.
\end{remark}
"""),
]

DEPENDENCY_LABELS = {
    "embedding-extension lemma": "ExtensionOfFieldEmbeddings",
    "embedding lemma": "ExtensionOfFieldEmbeddings",
    "tower law": "ExtensionOfFieldEmbeddings",
    "normal-closure entry": "NormalClosureOfAFieldExtension",
    "cyclotomic proposition": "CyclotomicExtension",
    "solvable groups": "SolvableGroup",
    "Gauss's lemma": "GaussLemmaForIntegerPolynomials",
    "Orbit-stabilizer": "OrbitStabilizerTheorem",
    "symmetric-group entry": "NonsolvabilityOfSymmetricGroups",
    "symmetric-group theorem": "NonsolvabilityOfSymmetricGroups",
    "prime-degree transposition theorem": "PrimeDegreeTransitiveGroupWithTransposition",
    "radical-solvability theorem": "RadicalSolvabilityImpliesSolvableGaloisGroup",
    "fixed fields": "FixedField",
    "normal closures": "NormalClosureOfAFieldExtension",
}
for e in ENTRIES:
    labels = {label: target for label, target in DEPENDENCY_LABELS.items() if target != e['canonical']}
    pattern = re.compile('|'.join(re.escape(label) for label in sorted(labels, key=len, reverse=True)))
    e['body'] = pattern.sub(lambda m: r'\PMlinkname{' + m[0] + '}{' + labels[m[0]] + '}', e['body'])



def links(html):
    p=Links();p.feed(html)
    return {a['href'].split('slug=',1)[1] for a,_ in p.links if a.get('href','').startswith('concept.html?slug=')}


def relate(c,origin,target):
    a=c.execute('SELECT id FROM math_concepts WHERE slug=?',(origin,)).fetchone()[0]
    b=c.execute('SELECT id,canonical_name FROM math_concepts WHERE slug=?',(target,)).fetchone()
    if not c.execute('SELECT 1 FROM math_related_concepts WHERE concept_id=? AND related_canonical_name=?',(a,b[1])).fetchone():
        c.execute('INSERT INTO math_related_concepts(concept_id,related_canonical_name,related_concept_id) VALUES(?,?,?)',(a,b[1],b[0]))


def verify(c):
    for e in ENTRIES:
        d=fetch_public_math_concept_detail(c.cursor(),e['slug'])
        assert d and d['owner']=='CWoo' and d['cleaned_tex']==source(e),e['slug']
        for key in ['synonyms','definitions']: assert set(d[key])==set(e[key]),(e['slug'],key)
        assert set(d['types'])==set(document_types(e))
        assert {r['code'] for r in d['classifications']}==set(e['classifications'])
        html=d['display_tex']; assert r'\PMlink' not in html
        for label, target in re.findall(r'\\PMlinkname\{([^{}]*)\}\{([^{}]*)\}', e['body']):
            row=c.execute('SELECT slug FROM math_concepts WHERE canonical_name=?',(target,)).fetchone()
            assert row and row[0] in links(html),(e['slug'],label,target)
        for target in links(html):
            assert c.execute('SELECT 1 FROM math_concepts WHERE slug=?',(target,)).fetchone(),target
        assert e['slug'] not in links(html)
        assert html.count('class="math-env math-env-proof"')==e['body'].count(r'\begin{proof}')
        pattern=r'\\\(.*?\\\)|\\\[.*?\\\]'
        assert re.findall(pattern,source(e),re.S)==re.findall(pattern,html,re.S),e['slug']
        assert any(r.get('slug')==e['slug'] for r in search_public_math_library(c.cursor(),e['title'])['data'])
        related=c.execute('SELECT related_concept_id FROM math_related_concepts WHERE concept_id=?',(d['id'],)).fetchall()
        assert len(related)>=len(e['related']) and all(r[0] for r in related)
        print('Verified',d['id'],e['slug'])
    assert 'fixed-field' not in links(fetch_public_math_concept_detail(c.cursor(),'signature')['display_tex'])
    assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    assert not c.execute('PRAGMA foreign_key_check').fetchall()


def apply(path):
    if not path.is_file(): raise FileNotFoundError(path)
    with sqlite3.connect(path) as c:
        c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON')
        now=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # Pre-create with no related links, then resolve links after all entries
        # exist; this allows examples to refer forward to independent lemmas.
        for e in ENTRIES:
            if c.execute('SELECT 1 FROM math_concepts WHERE slug=?',(e['slug'],)).fetchone(): continue
            for t in [e['title'],*e['synonyms'],*e['definitions']]:
                assert not c.execute('''SELECT title FROM math_concepts WHERE lower(title)=lower(?)
                    UNION SELECT synonym_text FROM math_synonyms WHERE lower(synonym_text)=lower(?)
                    UNION SELECT defined_term FROM math_definitions WHERE lower(defined_term)=lower(?)''',(t,t,t)).fetchone(),t
            create_math_concept(c.cursor(),e['canonical'],e['slug'],e['title'],now,'CWoo',source(e),1,
                                e['classifications'],document_types(e),e['synonyms'],e['definitions'],[])
        for e in ENTRIES:
            for target in e['related']: relate(c,e['slug'],target)
        for target in ['abel-ruffini-theorem','fixed-field','normal-closure-of-a-field-extension']:
            relate(c,'galois-group',target)
        for target in ['fixed-field','normal-closure-of-a-field-extension']:
            relate(c,'abel-ruffini-theorem',target)
        relate(c,'normal-closure-of-a-field-extension','eisenstein-irreducibility-criterion')
        row=c.execute("SELECT id,cleaned_tex FROM math_concepts WHERE slug='signature'").fetchone()
        exclusion=r'\PMlinkescapeword{fixed field}'
        if exclusion not in row[1]:
            text=exclusion+'\n'+row[1]
            rendered=render_tex_reusing_existing_diagrams(row[0],text,c.cursor())
            c.execute('UPDATE math_concepts SET cleaned_tex=?,rendered_tex=?,updated_at=? WHERE id=?',(text,rendered,now,row[0]))
            c.execute('INSERT INTO math_link_exclusions(concept_id,word) VALUES(?,?)',(row[0],'fixed field'))
        verify(c)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--db',type=Path,default=SRC.parent/'portfolio.db')
    apply(p.parse_args().db)
