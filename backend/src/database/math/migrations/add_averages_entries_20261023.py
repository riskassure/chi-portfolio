"""Entries for "sets closed under averaging contain the rationals".

Five entries, in dependency order, ending with the root theorem: a subset of [0,1]
containing 0 and 1 and closed under arithmetic means of distinct elements contains
every rational number in [0,1]. Related links to later entries were dropped as for
the real analysis batch. Published on 2026-10-23 with the helper (options 2-5).
"""
from math_entry_batch import run_batch

HAMMACK = ("Richard Hammack", "Book of Proof",
           "https://richardhammack.github.io/BookOfProof/")

EXTRA_ESCAPES = [
    "reflexive", "transitive", "square", "positive element", "Archimedean", "complete",
    "instance", "absolute value", "distance", "measure", "interval", "open interval",
    "ordering principle", "interior point", "open", "near", "key", "information", "height",
    "nor", "arithmetic", "length", "useful", "reduced", "theory", "symmetric",
    "injective", "terminating",
]

E = []


def entry(title, slug, codes, synonyms, definitions, related, body, ref=HAMMACK):
    E.append(dict(title=title, slug=slug, classifications=codes, synonyms=synonyms,
                  definitions=definitions, related=related, body=body, reference=ref))


# Words in these bodies that might be mis-autolinked (ordinary-English or context-dependent uses):
# set, sets, closed, closure, distinct, average, mean, means, interval, range, unit, odd, even,
# order, ordered, image, quotient, quotients, field, smallest, characteristic, identify,
# identification, product, products, sum, sums, difference, differences, inverse, contained,
# least, upper bound, property, minimum, maximum, midpoint, distance, equal, list, common,
# denominator, induction, step, case, cases, contradiction, statement, exponent, power, powers.


entry("rational number", "rational-number", ["11A99", "26A03"],
      ["rational numbers"], [],
      ["integer", "field-of-fractions"], r"""
Dividing integers by nonzero integers produces exactly the numbers needed to make the integers into a field, and inside the real numbers these quotients form the smallest field.

By the results in the entry on \PMlinkname{ordered fields}{OrderedField}, the map \(n\mapsto n\cdot1\) from the positive integers into \(\mathbb{R}\) is injective and order-preserving, because \(\mathbb{R}\) has characteristic \(0\). Extending it by \(0\mapsto0\) and \(-n\mapsto-(n\cdot1)\) gives the map from the \PMlinkname{integers}{Integer} \(\mathbb{Z}\) into \(\mathbb{R}\) that respects addition and multiplication; it is still injective and order-preserving, since positive integers go to positive real numbers, negative integers to negative ones, and \(-m\cdot1<-n\cdot1\) whenever \(0<n<m\). We therefore identify \(\mathbb{Z}\) with its image, so that \(\mathbb{Z}\subseteq\mathbb{R}\), and inequalities between integers mean the same thing in \(\mathbb{Z}\) and in \(\mathbb{R}\).

\begin{definition}
A real number \(r\) is \emph{rational} if there are integers \(p\) and \(q\) with \(q\ne0\) such that \(r=p/q\), that is, \(r=pq^{-1}\). The set of rational numbers is denoted \(\mathbb{Q}\). A real number that is not rational is called irrational.
\end{definition}

Every integer \(p\) is rational, since \(p=p/1\). A rational number has many representations: \(p/q=(cp)/(cq)\) for every nonzero integer \(c\).

\begin{proposition}
\begin{enumerate}
\item Every rational number can be written as \(p/q\) with \(p,q\in\mathbb{Z}\) and \(q\ge1\).
\item \(\mathbb{Q}\) is a \PMlinkname{subfield}{Subfield} of \(\mathbb{R}\), and \(\mathbb{Q}\subseteq K\) for every subfield \(K\) of \(\mathbb{R}\). Thus \(\mathbb{Q}\) is the smallest subfield of \(\mathbb{R}\).
\item If \(r\in\mathbb{Q}\) and \(0\le r\le1\), then \(r=p/q\) for some integers \(p,q\) with \(q\ge1\) and \(0\le p\le q\). If moreover \(0<r<1\), then \(1\le p\le q-1\).
\end{enumerate}
\end{proposition}

\begin{proof}
\textit{(1)} Let \(r=p/q\) with \(p,q\in\mathbb{Z}\) and \(q\ne0\). If \(q>0\), there is nothing to prove, because a positive integer is at least \(1\). If \(q<0\), then \(-q>0\), so \(-q\ge1\), and
\[
r=pq^{-1}=(-p)(-q)^{-1}=\frac{-p}{-q},
\]
since \((-p)(-q)^{-1}=(-1)p\cdot(-1)^{-1}q^{-1}=pq^{-1}\), using \((-1)^{-1}=-1\).

\textit{(2)} We have \(0=0/1\) and \(1=1/1\) in \(\mathbb{Q}\). Let \(r=p/q\) and \(s=u/v\) be rational, with \(p,q,u,v\in\mathbb{Z}\) and \(q,v\ne0\). Then \(qv\) is an integer, and \(qv\ne0\) because a field has no zero divisors. By the \PMlinkname{field axioms}{Field},
\[
r-s=\frac{pv-uq}{qv},\qquad rs=\frac{pu}{qv},
\]
as one checks by multiplying each side by \(qv\). Since \(pv-uq\) and \(pu\) are integers, \(r-s\in\mathbb{Q}\) and \(rs\in\mathbb{Q}\). If \(s\ne0\), then \(u\ne0\) (otherwise \(s=0\cdot v^{-1}=0\)), and \(s^{-1}=v/u\), because \((u/v)(v/u)=uv(vu)^{-1}=1\); hence \(s^{-1}\in\mathbb{Q}\). A subset of \(\mathbb{R}\) that contains \(0\) and \(1\) and is closed under subtraction, multiplication and inverses of nonzero elements is a subfield, so \(\mathbb{Q}\) is a subfield of \(\mathbb{R}\).

Now let \(K\) be any subfield of \(\mathbb{R}\). Then \(1\in K\), and if \(n\cdot1\in K\), then \((n+1)\cdot1=n\cdot1+1\in K\); by \PMlinkname{induction}{PrincipleOfFiniteInduction}, \(K\) contains every positive integer. Since \(K\) contains \(0\) and additive inverses, it contains every integer. If \(p,q\in\mathbb{Z}\) and \(q\ne0\), then \(q^{-1}\in K\) and so \(p/q=pq^{-1}\in K\). Hence \(\mathbb{Q}\subseteq K\).

\textit{(3)} By (1), write \(r=p/q\) with \(p,q\in\mathbb{Z}\) and \(q\ge1\). Then \(q>0\), and multiplying the inequalities \(0\le p/q\le1\) by \(q\) preserves them, giving \(0\le p\le q\). If \(0<r<1\), the same multiplication gives \(0<p<q\). An integer \(p\) with \(0<p\) satisfies \(p\ge1\), since there is no integer strictly between \(0\) and \(1\) (see \PMlinkname{the floor function}{FloorFunction}); similarly \(q-p>0\) gives \(q-p\ge1\), that is, \(p\le q-1\).
\end{proof}

\begin{remark}
The construction of the \PMlinkname{field of fractions}{FieldOfFractions} of the integral domain \(\mathbb{Z}\) produces a field isomorphic to \(\mathbb{Q}\): the class of the pair \((p,q)\) corresponds to the real number \(p/q\). With the order inherited from \(\mathbb{R}\), \(\mathbb{Q}\) is an ordered field, but it does not have the \PMlinkname{least upper bound property}{LeastUpperBoundProperty}: the set of rational numbers whose square is less than \(2\) is nonempty and bounded above in \(\mathbb{Q}\) but has no least upper bound in \(\mathbb{Q}\).
\end{remark}
""")


entry("arithmetic mean", "arithmetic-mean", ["26D15"],
      ["arithmetic average"], [],
      ["rational-number"], r"""
The simplest way to summarize finitely many numbers by a single representative value is to add them up and divide by how many there are.

\begin{definition}
Let \(n\ge1\) be an integer and let \(x_1,\dots,x_n\) be real numbers. Their \emph{arithmetic mean} is
\[
A(x_1,\dots,x_n)=\frac{x_1+x_2+\dots+x_n}{n}.
\]
\end{definition}

The division is legitimate because \(n=n\cdot1>0\) in the \PMlinkname{ordered field}{OrderedField} \(\mathbb{R}\). For a single number, \(A(x_1)=x_1\).

Among finitely many real numbers \(x_1,\dots,x_n\) there is a smallest and a largest. Indeed, by \PMlinkname{induction}{PrincipleOfFiniteInduction} on \(n\): for \(n=1\) take \(x_1\); if \(x_j\) is the smallest of \(x_1,\dots,x_{n-1}\), then the smaller of \(x_j\) and \(x_n\) (which exists because the order is total) is the smallest of \(x_1,\dots,x_n\), and likewise for the largest. We write \(\min_i x_i\) and \(\max_i x_i\) for these values.

\begin{proposition}
Let \(n\ge1\), let \(x_1,\dots,x_n\in\mathbb{R}\), and write \(A=A(x_1,\dots,x_n)\), \(m=\min_i x_i\) and \(M=\max_i x_i\).
\begin{enumerate}
\item \(m\le A\le M\). Moreover \(A=m\) if and only if \(x_1=x_2=\dots=x_n\), and \(A=M\) if and only if \(x_1=x_2=\dots=x_n\).
\item If \(n\ge2\) and \(x_1,\dots,x_n\) are pairwise distinct, then \(m<A<M\).
\item If \(a\le b\) and \(x_i\in[a,b]\) for every \(i\), then \(A\in[a,b]\).
\item For all \(c,d\in\mathbb{R}\),
\[
A(cx_1+d,\dots,cx_n+d)=cA+d.
\]
\item For \(n=2\), \(A(x_1,x_2)=(x_1+x_2)/2\) is equidistant from \(x_1\) and \(x_2\): \(A-x_1=x_2-A\).
\end{enumerate}
\end{proposition}

\begin{proof}
\textit{(1)} Each \(x_i\) satisfies \(x_i\ge m\). Adding these \(n\) inequalities (inequalities between sums of the same number of terms may be added, by the ordered field axioms) gives
\[
x_1+\dots+x_n\ge nm,
\]
and the sum is strictly greater than \(nm\) as soon as one of the inequalities \(x_i\ge m\) is strict. Multiplying by \(1/n>0\) gives \(A\ge m\), with \(A>m\) when some \(x_i>m\). If the \(x_i\) are not all equal, then, since \(m\) is one of them, some \(x_j\) differs from \(m\); as \(x_j\ge m\), we get \(x_j>m\) and therefore \(A>m\). Conversely, if \(x_1=\dots=x_n=c\), then \(A=nc/n=c=m\). This proves the statements about \(m\). Applying them to \(-x_1,\dots,-x_n\), whose smallest element is \(-M\) and whose mean is \(-A\), gives \(-A\ge-M\), that is, \(A\le M\), with equality if and only if all \(x_i\) are equal.

\textit{(2)} Pairwise distinct numbers, at least two of them, are not all equal, so \(A\ne m\) and \(A\ne M\) by (1). Together with \(m\le A\le M\) this gives \(m<A<M\).

\textit{(3)} The numbers \(m\) and \(M\) are among the \(x_i\), so \(a\le m\) and \(M\le b\). By (1), \(a\le m\le A\le M\le b\).

\textit{(4)} By the field axioms,
\[
(cx_1+d)+\dots+(cx_n+d)=c(x_1+\dots+x_n)+nd,
\]
and dividing by \(n\) gives \(c(x_1+\dots+x_n)/n+d=cA+d\).

\textit{(5)} We have
\[
A-x_1=\frac{x_1+x_2}{2}-x_1=\frac{x_2-x_1}{2}=x_2-\frac{x_1+x_2}{2}=x_2-A.
\]
\end{proof}

By (5), the mean of two numbers \(x_1<x_2\) is the midpoint of the interval \([x_1,x_2]\). Part (2) is the reason that taking means of distinct elements of a set can produce new elements, as in the theorem on \PMlinkname{sets closed under averaging}{SetsClosedUnderAveragingContainTheRationals}.

\begin{example}
The mean of \(0,\tfrac14,\tfrac12\) is
\[
\frac{0+\tfrac14+\tfrac12}{3}=\frac{3/4}{3}=\frac14,
\]
which here coincides with one of the numbers. The mean of \(0,\tfrac14,\tfrac12,1\) is \(\tfrac{7/4}{4}=\tfrac{7}{16}\), which is not one of them; it lies strictly between \(0\) and \(1\), as part (2) predicts. The mean of the \PMlinkname{rational numbers}{RationalNumber} \(0\) and \(1\) is \(\tfrac12\), and by part (4) the mean of \(1=2\cdot0+1\) and \(3=2\cdot1+1\) is \(2\cdot\tfrac12+1=2\).
\end{example}
""")


entry("dyadic rational", "dyadic-rational", ["11A99"],
      ["dyadic rationals", "dyadic fraction"], [],
      ["rational-number"], r"""
Repeatedly halving and adding, starting from the integers, produces exactly the fractions whose denominators are powers of \(2\), the numbers with terminating binary expansions.

\begin{definition}
A real number \(x\) is a \emph{dyadic rational} if \(x=k/2^m\) for some \(k\in\mathbb{Z}\) and some integer \(m\ge0\).
\end{definition}

Since \(2^m\) is a nonzero integer, every dyadic rational is a \PMlinkname{rational number}{RationalNumber}. Every integer \(k=k/2^0\) is a dyadic rational, and so are \(\tfrac12\), \(\tfrac34\) and \(-\tfrac58\). A dyadic rational has many representations, because
\[
\frac{k}{2^m}=\frac{2^jk}{2^{m+j}}\qquad\text{for every integer } j\ge0.
\]

\begin{proposition}
\begin{enumerate}
\item Finitely many dyadic rationals \(x_1,\dots,x_r\) can be written with a common denominator: there are an integer \(M\ge0\) and integers \(l_1,\dots,l_r\) with \(x_i=l_i/2^M\) for every \(i\). Moreover \(M\) can be taken as large as desired.
\item If \(x\) and \(y\) are dyadic rationals, then so are \(x+y\), \(x-y\), \(xy\) and \((x+y)/2\).
\item If \(x\) is a dyadic rational with \(0\le x\le1\) and \(x=k/2^m\) with \(k\in\mathbb{Z}\) and \(m\ge0\), then \(0\le k\le2^m\).
\end{enumerate}
\end{proposition}

\begin{proof}
\textit{(1)} Write \(x_i=k_i/2^{m_i}\) with \(k_i\in\mathbb{Z}\) and \(m_i\ge0\), and let \(M\) be any integer with \(M\ge m_i\) for all \(i\), for instance \(M=m_1+\dots+m_r\) or anything larger. Then \(M-m_i\ge0\), and the identity displayed above, with \(j=M-m_i\), gives \(x_i=l_i/2^M\) with \(l_i=2^{M-m_i}k_i\in\mathbb{Z}\).

\textit{(2)} By (1), write \(x=k/2^m\) and \(y=l/2^m\) with \(k,l\in\mathbb{Z}\) and the same \(m\ge0\). Then
\[
x+y=\frac{k+l}{2^m},\qquad x-y=\frac{k-l}{2^m},\qquad xy=\frac{kl}{2^{2m}},\qquad \frac{x+y}{2}=\frac{k+l}{2^{m+1}},
\]
and \(k+l\), \(k-l\), \(kl\) are integers.

\textit{(3)} Multiplying \(0\le k/2^m\le1\) by \(2^m>0\) gives \(0\le k\le2^m\).
\end{proof}

Not every rational number is a dyadic rational.

\begin{proposition}
The number \(\tfrac13\) is not a dyadic rational.
\end{proposition}

\begin{proof}
We first show by \PMlinkname{induction}{PrincipleOfFiniteInduction} on \(m\ge0\) that there is an integer \(a_m\) with
\[
2^m=3a_m+(-1)^m.
\]
For \(m=0\), take \(a_0=0\): \(1=3\cdot0+1\). If \(2^m=3a_m+(-1)^m\), then
\[
2^{m+1}=6a_m+2(-1)^m=6a_m+3(-1)^m-(-1)^m=3\bigl(2a_m+(-1)^m\bigr)+(-1)^{m+1},
\]
so \(a_{m+1}=2a_m+(-1)^m\) works.

Suppose, for a contradiction, that \(\tfrac13=k/2^m\) with \(k\in\mathbb{Z}\) and \(m\ge0\). Multiplying by \(3\cdot2^m\) gives \(2^m=3k\). Hence \(3k=3a_m+(-1)^m\), that is, \(3t=(-1)^m\) for the integer \(t=k-a_m\). Replacing \(t\) by \(-t\) if \(m\) is odd, we obtain an integer \(t\) with \(3t=1\). If \(t\le0\), then \(3t\le0<1\); if \(t\ge1\), then \(3t\ge3>1\). Hence \(0<t<1\), but there is no integer strictly between \(0\) and \(1\) (see \PMlinkname{the floor function}{FloorFunction}). This contradiction shows that \(\tfrac13\) is not a dyadic rational.
\end{proof}

\begin{remark}
Let \(D\) be the set of dyadic rationals \(x\) with \(0\le x\le1\). Then \(D\) contains \(0\) and \(1\), and for \(x,y\in D\) the \PMlinkname{arithmetic mean}{ArithmeticMean} \((x+y)/2\) is a dyadic rational by part (2) and lies in \([0,1]\) because the mean of numbers in an interval stays in it. So \(D\) is closed under taking the mean of two elements, yet \(\tfrac13\notin D\). This shows that in the theorem on \PMlinkname{sets closed under averaging}{SetsClosedUnderAveragingContainTheRationals}, which concludes that such a set contains every rational number in \([0,1]\), means of two elements alone do not suffice: means of more than two elements are needed.
\end{remark}
""")


# ---- part2.py: entries 4 and 5 ----
# Words in these bodies that might be mis-autolinked to unrelated entries (ordinary-English
# or context-dependent uses): range, set, sets, closed, distinct, mean, means, average,
# averaging, interval, odd, even, sum, sums, step, steps, index, largest, smallest, list,
# collection, element, elements, order, increasing, finite, count, hypothesis, conclusion,
# best possible, raise, replace, induction, contradiction, value, unit, lemma, theorem.


entry("sums of distinct integers from a range", "sums-of-distinct-integers-from-a-range", ["11B75"],
      [], [],
      ["integer"], r"""
When \(q\) different integers are chosen from \(\{0,1,\dots,N\}\), their sum can be neither smaller than that of the \(q\) smallest available numbers nor larger than that of the \(q\) largest, and every integer value in between is actually attained.

Throughout, we use the following fact about \PMlinkname{integers}{Integer}: there is no integer strictly between \(k\) and \(k+1\) for an integer \(k\) (see \PMlinkname{floor function}{FloorFunction}). Consequently, if \(a<b\) are integers, then \(a+1\le b\). For a finite set \(A\) of integers we write \(\sigma(A)\) for the sum of its elements. To say that an integer \(s\) is the sum of \(q\) distinct elements of a set \(X\) means that \(s=\sigma(A)\) for some subset \(A\subseteq X\) with exactly \(q\) elements.

\begin{lemma}
For every integer \(q\ge1\),
\[
0+1+\dots+(q-1)=\sum_{j=0}^{q-1}j=\frac{q(q-1)}{2}.
\]
In particular \(q(q-1)/2\) is an integer.
\end{lemma}

\begin{proof}
We use \PMlinkname{induction}{PrincipleOfFiniteInduction} on \(q\). For \(q=1\) the sum has the single term \(0\), and \(1\cdot0/2=0\). If the formula holds for \(q\), then
\[
\sum_{j=0}^{q}j=\frac{q(q-1)}{2}+q=\frac{q(q-1)+2q}{2}=\frac{(q+1)q}{2},
\]
which is the formula for \(q+1\). The sum of integers is an integer, so \(q(q-1)/2\) is an integer.
\end{proof}

\begin{theorem}
Let \(q\ge1\) and \(N\ge q-1\) be integers, and put \(T=q(q-1)/2\). An integer \(s\) is the sum of \(q\) distinct elements of \(\{0,1,\dots,N\}\) if and only if
\[
T\le s\le qN-T.
\]
\end{theorem}

The hypothesis \(N\ge q-1\) says exactly that \(\{0,1,\dots,N\}\), which has \(N+1\) elements, has subsets with \(q\) elements. It also gives \(2T=q(q-1)\le qN\), so \(T\le qN-T\) and the range of sums is nonempty.

\begin{proof}
Let \(B=\{N-q+1,N-q+2,\dots,N\}\), the set of the \(q\) largest elements of \(\{0,1,\dots,N\}\); since \(N-q+1\ge0\), it is a \(q\)-element subset of \(\{0,1,\dots,N\}\). By the lemma, substituting \(j=q-i\),
\[
\sigma(B)=\sum_{i=1}^{q}(N-q+i)=qN-\sum_{i=1}^{q}(q-i)=qN-\sum_{j=0}^{q-1}j=qN-T.
\]

\textit{Only if.} Let \(A\subseteq\{0,1,\dots,N\}\) have \(q\) elements, listed in increasing order as \(a_1<a_2<\dots<a_q\). We show
\[
i-1\le a_i\le N-q+i\qquad(1\le i\le q).
\]
For the lower bound we use induction on \(i\). We have \(a_1\ge0\) because \(a_1\in\{0,\dots,N\}\). If \(a_i\ge i-1\) and \(i<q\), then \(a_{i+1}>a_i\), so \(a_{i+1}\ge a_i+1\ge i\) by the fact recalled above. For the upper bound we use induction on \(j=q-i\), for \(j=0,1,\dots,q-1\). For \(j=0\), \(a_q\le N\). If \(a_{i+1}\le N-q+i+1\) for some \(i\ge1\), then \(a_i<a_{i+1}\) gives \(a_i\le a_{i+1}-1\le N-q+i\). Adding the inequalities over \(i=1,\dots,q\) and using the lemma and the computation of \(\sigma(B)\),
\[
T=\sum_{i=1}^{q}(i-1)\le\sigma(A)\le\sum_{i=1}^{q}(N-q+i)=qN-T.
\]

\textit{If.} First we show: \textit{if \(A\subseteq\{0,1,\dots,N\}\) has \(q\) elements and \(A\ne B\), then there is an element \(a\in A\) with \(a+1\le N\) and \(a+1\notin A\).} List \(A\) as \(a_1<\dots<a_q\). By the \textit{only if} part, \(a_i\le N-q+i\) for every \(i\). If equality held for every \(i\), then \(A=B\). Hence the set of indices \(i\) with \(a_i<N-q+i\) is a nonempty subset of \(\{1,\dots,q\}\); let \(i\) be its largest element and put \(a=a_i\). Then \(a+1\le N-q+i\le N\). If \(i=q\), then \(a+1>a_q=\max A\), so \(a+1\notin A\). If \(i<q\), then \(a_{i+1}=N-q+i+1\) by the choice of \(i\), so \(a<a+1\le N-q+i<a_{i+1}\); since \(a_i\) and \(a_{i+1}\) are consecutive in the increasing list of the elements of \(A\), no element of \(A\) lies strictly between them, and again \(a+1\notin A\).

For such \(A\) and \(a\), the set
\[
A'=(A\setminus\{a\})\cup\{a+1\}
\]
is a subset of \(\{0,1,\dots,N\}\) with exactly \(q\) elements, because \(a+1\le N\) and \(a+1\notin A\), and
\[
\sigma(A')=\sigma(A)-a+(a+1)=\sigma(A)+1.
\]

We now prove by induction on \(s-T\) that every integer \(s\) with \(T\le s\le qN-T\) equals \(\sigma(A)\) for some \(q\)-element subset \(A\) of \(\{0,1,\dots,N\}\). For \(s=T\), take \(A_0=\{0,1,\dots,q-1\}\), which is contained in \(\{0,1,\dots,N\}\) because \(q-1\le N\); by the lemma \(\sigma(A_0)=T\). Suppose \(T\le s<qN-T\) and \(s=\sigma(A)\) for a \(q\)-element subset \(A\). Since \(\sigma(A)=s\ne qN-T=\sigma(B)\), we have \(A\ne B\), so the construction above yields a \(q\)-element subset \(A'\) of \(\{0,1,\dots,N\}\) with \(\sigma(A')=s+1\). This completes the induction and the proof.
\end{proof}

\begin{example}
Take \(q=3\) and \(N=4\), so \(T=3\) and \(qN-T=9\). Starting from \(\{0,1,2\}\) and repeatedly applying the step in the proof gives
\[
\{0,1,2\},\ \{0,1,3\},\ \{0,1,4\},\ \{0,2,4\},\ \{0,3,4\},\ \{1,3,4\},\ \{2,3,4\},
\]
with sums \(3,4,5,6,7,8,9\). Every three distinct elements of \(\{0,1,2,3,4\}\) have a sum between \(3\) and \(9\), and each of these values occurs.
\end{example}

\begin{remark}
The requirement that the elements be distinct is what makes the lower and upper bounds nontrivial. This theorem is the counting step in the proof that \PMlinkname{sets closed under averaging contain the rationals}{SetsClosedUnderAveragingContainTheRationals}, where \(N\) is a power of \(2\) and \(s=pN\) for an integer \(1\le p\le q-1\).
\end{remark}
""")


entry("sets closed under averaging contain the rationals", "sets-closed-under-averaging-contain-the-rationals", ["00A07", "11A99"],
      [], [],
      ["arithmetic-mean", "dyadic-rational", "rational-number", "sums-of-distinct-integers-from-a-range"], r"""
Starting only from the endpoints \(0\) and \(1\), repeatedly taking averages of different numbers already obtained produces every rational number between them, although no irrational one need ever appear.

\begin{theorem}
Let \(S\) be a set of real numbers with \(0\le x\le1\) for all \(x\in S\), and with \(0\in S\) and \(1\in S\). Suppose that for every integer \(n\ge1\) and every choice of \(n\) distinct elements \(x_1,\dots,x_n\) of \(S\), the \PMlinkname{arithmetic mean}{ArithmeticMean}
\[
\frac{x_1+x_2+\dots+x_n}{n}
\]
also belongs to \(S\). Then \(S\) contains every \PMlinkname{rational number}{RationalNumber} \(r\) with \(0\le r\le1\).
\end{theorem}

The hypothesis applies to every finite collection of distinct elements, of every size \(n\), but never to a collection with repetitions. If repetitions were allowed, the proof would be one line: \(p/q\) would be the mean of \(p\) copies of \(1\) and \(q-p\) copies of \(0\). The work lies in replacing such a collection by \(q\) distinct numbers with the same mean.

We use repeatedly that for integers \(a<b\) we have \(a+1\le b\), since there is no integer strictly between \(a\) and \(a+1\) (see \PMlinkname{floor function}{FloorFunction}).

\begin{proof}
\textit{Step 1: \PMlinkname{dyadic rationals}{DyadicRational}.} We prove by \PMlinkname{induction}{PrincipleOfFiniteInduction} on \(m\ge0\) that \(k/2^m\in S\) for every integer \(k\) with \(0\le k\le2^m\). For \(m=0\), \(k\) is \(0\) or \(1\), and \(0,1\in S\) by hypothesis. Let \(m\ge1\) and assume the statement for \(m-1\). Let \(k\) be an integer with \(0\le k\le2^m\), and let \(j=\lfloor k/2\rfloor\), so that \(j\le k/2<j+1\), that is, \(2j\le k<2j+2\). Then \(k=2j\) or \(k=2j+1\), because \(k\) is an integer and there is no integer strictly between \(2j\) and \(2j+1\) or strictly between \(2j+1\) and \(2j+2\).

If \(k=2j\), then \(0\le j\le2^{m-1}\) and \(k/2^m=j/2^{m-1}\), which lies in \(S\) by the induction hypothesis.

If \(k=2j+1\), then \(0\le 2j+1\) gives \(j>-1\), so \(j\ge0\), and \(2j+1\le2^m\) gives \(j<2^{m-1}\), so \(j+1\le2^{m-1}\). By the induction hypothesis
\[
x=\frac{j}{2^{m-1}}\in S\quad\text{and}\quad y=\frac{j+1}{2^{m-1}}\in S.
\]
These two elements are distinct, and their mean is
\[
\frac{x+y}{2}=\frac{2j+1}{2^{m}}=\frac{k}{2^m}.
\]
By the hypothesis on \(S\) with \(n=2\), \(k/2^m\in S\). This completes the induction.

\textit{Step 2: reduction and choice of a denominator.} Let \(r\) be rational with \(0\le r\le1\). By the \PMlinkname{entry on rational numbers}{RationalNumber}, \(r=p/q\) for integers \(p,q\) with \(q\ge1\) and \(0\le p\le q\). If \(p=0\), then \(r=0\in S\), and if \(p=q\), then \(r=1\in S\). Assume from now on that \(1\le p\le q-1\); in particular \(q\ge2\). Put \(T=q(q-1)/2\), a positive integer by the lemma in \PMlinkname{sums of distinct integers from a range}{SumsOfDistinctIntegersFromARange}.

We first note that \(2^m\ge m+1\) for every integer \(m\ge0\), by induction: \(2^0=1\), and if \(2^m\ge m+1\), then \(2^{m+1}=2\cdot2^m\ge2m+2\ge m+2\). Take \(m=T\) and \(N=2^m\). Then \(N\ge T+1>T\). Moreover \(T\ge q-1\), because \(q/2\ge1\) and \(q-1\ge0\) give \(T=(q/2)(q-1)\ge q-1\). Hence
\[
N\ge T\ge q-1.
\]

\textit{Step 3: choosing \(q\) distinct numerators.} Since \(1\le p\le q-1\) and \(N\ge T\),
\[
T\le N\le pN\le(q-1)N=qN-N\le qN-T.
\]
Since also \(N\ge q-1\), the theorem in \PMlinkname{sums of distinct integers from a range}{SumsOfDistinctIntegersFromARange} applies with \(s=pN\): there are distinct integers \(a_1,\dots,a_q\) in \(\{0,1,\dots,N\}\) with
\[
a_1+a_2+\dots+a_q=pN.
\]

\textit{Step 4: conclusion.} Put \(x_i=a_i/N=a_i/2^m\) for \(i=1,\dots,q\). Since \(0\le a_i\le2^m\), Step 1 gives \(x_i\in S\). The \(x_i\) are distinct, because \(N\ne0\) and \(a_i/N=a_l/N\) implies \(a_i=a_l\). Their mean is
\[
\frac{x_1+\dots+x_q}{q}=\frac{a_1+\dots+a_q}{qN}=\frac{pN}{qN}=\frac{p}{q}=r.
\]
By the hypothesis on \(S\) with \(n=q\), \(r\in S\).
\end{proof}

\begin{example}
For \(r=1/3\) the proof gives \(q=3\), \(p=1\), \(T=3\), \(m=3\) and \(N=8\), and asks for three distinct integers in \(\{0,\dots,8\}\) with sum \(8\), for instance \(0,1,7\). Indeed \(0\), \(1/8\) and \(7/8\) are in \(S\) by Step 1, and their mean is \((0+1/8+7/8)/3=1/3\). A smaller denominator also works here: \(0\), \(1/4\) and \(3/4\) have mean \(1/3\).
\end{example}

\begin{remark}
The proof uses the hypothesis only for \(n=2\) (in Step 1) and \(n=q\) (in Step 4). Closure under means of two distinct elements alone does not suffice. Let \(D\) be the set of dyadic rationals \(x\) with \(0\le x\le1\). It contains \(0\) and \(1\). If \(x,y\in D\), then by the \PMlinkname{entry on dyadic rationals}{DyadicRational} their mean \((x+y)/2\) is again a dyadic rational, and it lies between \(0\) and \(1\) by the bounds for the \PMlinkname{arithmetic mean}{ArithmeticMean}; so \(D\) is closed under means of two elements. But \(1/3\notin D\), since \(1/3\) is not a dyadic rational. So \(D\) is not closed under means of three distinct elements: for instance \(0\), \(\tfrac14\) and \(\tfrac34\) lie in \(D\), but their mean is \(\tfrac13\).
\end{remark}

\begin{remark}
The conclusion is the best possible. The set \(S=\mathbb{Q}\cap[0,1]\) satisfies the hypotheses: it contains \(0\) and \(1\), and if \(x_1,\dots,x_n\) are rational numbers in \([0,1]\), then their mean is rational, because \(\mathbb{Q}\) is a \PMlinkname{subfield}{Subfield} of \(\mathbb{R}\) and so contains \(x_1+\dots+x_n\) and \(1/n\), and it lies in \([0,1]\) because the mean of numbers in an interval \([a,b]\) lies in \([a,b]\). Hence \(\mathbb{Q}\cap[0,1]\) is the smallest set satisfying the hypotheses: it is contained in every such set by the theorem and is itself one. The set \(S=[0,1]\) also satisfies the hypotheses, by the same bound for the mean, so \(S\) need not consist of rational numbers only.
\end{remark}
""")


if __name__ == "__main__":
    run_batch(E, EXTRA_ESCAPES, __doc__)
