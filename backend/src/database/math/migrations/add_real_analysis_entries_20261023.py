"""Real analysis entries for "integral powers force an integral exponent".

Fourteen entries, in dependency order, ending with the root theorem: if N^x is an
integer for every positive integer N, then x is an integer. The others build the
needed analysis from the field axioms, induction and the existence of R.
Related links that pointed to entries published later were dropped (or reversed
when there was no reverse link), because the live publisher only accepts related
entries that are already live. Published on 2026-10-23 with the helper (options 2-5).
"""
from math_entry_batch import run_batch

LEBL = ("Jiri Lebl", "Basic Analysis I: Introduction to Real Analysis",
        "https://www.jirka.org/ra/html/ra.html")

EXTRA_ESCAPES = [
    "reflexive", "transitive", "square", "positive element", "Archimedean", "complete",
    "instance", "absolute value", "distance", "measure", "interval", "open interval",
    "ordering principle", "interior point", "open", "near", "key", "information", "height",
    "nor", "arithmetic", "length", "useful", "reduced", "theory", "symmetric",
]

E = []


def entry(title, slug, codes, synonyms, definitions, related, body, ref=LEBL):
    E.append(dict(title=title, slug=slug, classifications=codes, synonyms=synonyms,
                  definitions=definitions, related=related, body=body, reference=ref))


# ---- from part4.py ----
# Words in these bodies that might be mis-autolinked (ordinary-English or context-dependent uses):
# order, ordered, total, positive, negative, square, squares, sum, sums, product, products,
# field, characteristic, identity, element, inverse, compatible, induction, bound, bounds,
# bounded, set, complete, completeness, property, least, greatest, approximation, nonempty,
# even, odd, integer, integers, case, cases, contradiction, inequality, inequalities,
# maximum, distance, value, absolute, interval, symmetric, triangle, reverse, unique.


entry("ordered field", "ordered-field", ["12J15", "06F25"],
      ["ordered fields"], [],
      ["field"], r"""
Every inequality manipulation used in analysis, from multiplying through by a positive number to taking reciprocals, follows from a short list of axioms describing how an order interacts with addition and multiplication.

\begin{definition}
An \emph{ordered field} is a \PMlinkname{field}{Field} \(F\) together with a total order \(\le\) on \(F\) such that, for all \(a,b,c\in F\),
\begin{enumerate}
\item if \(a\le b\), then \(a+c\le b+c\);
\item if \(0\le a\) and \(0\le b\), then \(0\le ab\).
\end{enumerate}
We write \(a<b\) when \(a\le b\) and \(a\ne b\), and \(b\ge a\), \(b>a\) for \(a\le b\), \(a<b\). An element \(a\in F\) with \(a>0\) is called a \emph{positive element}; an element with \(a<0\) is called negative.
\end{definition}

Recall that a total order is reflexive, antisymmetric (\(a\le b\) and \(b\le a\) imply \(a=b\)), transitive, and total (for all \(a,b\), \(a\le b\) or \(b\le a\)). Consequently, for any \(a,b\) exactly one of \(a<b\), \(a=b\), \(b<a\) holds, and \(a\le b<c\) or \(a<b\le c\) implies \(a<c\): indeed \(a\le c\) by transitivity, and \(a=c\) would give \(b\le a\le b\) with one of the inequalities strict, which is impossible by antisymmetry. We also use the elementary consequences of the field axioms \(a\cdot0=0\), \((-a)b=-(ab)\), \((-a)(-b)=ab\), and the absence of zero divisors: \(ab=0\) implies \(a=0\) or \(b=0\).

\begin{proposition}
Let \(F\) be an ordered field and let \(a,b,c,d\in F\).
\begin{enumerate}
\item If \(a<b\), then \(a+c<b+c\). If \(a\le b\) and \(c\le d\), then \(a+c\le b+d\), and the conclusion is strict if either hypothesis is strict.
\item \(a\le b\) if and only if \(0\le b-a\), and \(a<b\) if and only if \(0<b-a\).
\item \(a\le b\) if and only if \(-b\le -a\), and \(a<b\) if and only if \(-b<-a\). In particular \(a>0\) if and only if \(-a<0\).
\item If \(a>0\) and \(b>0\), then \(ab>0\) and \(a+b>0\).
\item \(a^2\ge0\), with equality only for \(a=0\). In particular \(1>0\) and \(-1<0\).
\item If \(a<b\) and \(c>0\), then \(ac<bc\). If \(a<b\) and \(c<0\), then \(ac>bc\). The same holds with \(\le\) in place of \(<\) throughout, provided \(c\ge0\), respectively \(c\le0\).
\item If \(a>0\), then \(1/a>0\). If \(0<a<b\), then \(0<1/b<1/a\).
\item If \(0\le a<b\), then \(a^2<b^2\).
\end{enumerate}
\end{proposition}

\begin{proof}
\textit{(1)} If \(a<b\), then \(a+c\le b+c\) by axiom 1, and \(a+c=b+c\) would give \(a=b\) after adding \(-c\); hence \(a+c<b+c\). If \(a\le b\) and \(c\le d\), then \(a+c\le b+c\) and \(b+c\le b+d\) by axiom 1, so \(a+c\le b+d\) by transitivity; if either hypothesis is strict, the corresponding step is strict by the first part, and the chain gives \(a+c<b+d\).

\textit{(2)} Adding \(-a\) to \(a\le b\) gives \(0\le b-a\); adding \(a\) to \(0\le b-a\) gives \(a\le b\). The strict version follows in the same way from (1).

\textit{(3)} Adding \(-a-b\) to \(a\le b\) gives \(-b\le-a\), and adding \(a+b\) to \(-b\le-a\) gives \(a\le b\). The strict version follows from (1). Taking \(a=0\) gives the last statement.

\textit{(4)} By axiom 2, \(ab\ge0\), and \(ab\ne0\) because \(a\ne0\), \(b\ne0\) and a field has no zero divisors. By (1), \(a+b>0+b=b>0\).

\textit{(5)} If \(a\ge0\), then \(a^2=a\cdot a\ge0\) by axiom 2. If \(a<0\), then \(-a>0\) by (3), and \(a^2=(-a)(-a)\ge0\). If \(a\ne0\), then \(a^2\ne0\) since there are no zero divisors, so \(a^2>0\). Since \(1=1^2\) and \(1\ne0\) in a field, \(1>0\), and then \(-1<0\) by (3).

\textit{(6)} Let \(a<b\). By (2), \(b-a>0\). If \(c>0\), then \(c(b-a)=bc-ac>0\) by (4), so \(ac<bc\) by (2). If \(c<0\), then \(-c>0\), so \(ac-bc=(-c)(b-a)>0\), and \(bc<ac\). For the non-strict statements, \(b-a\ge0\) and \(c\ge0\) give \(bc-ac=c(b-a)\ge0\) by axiom 2, and \(c\le0\) gives \(ac-bc=(-c)(b-a)\ge0\).

\textit{(7)} Let \(a>0\). Since \(a\cdot(1/a)=1\ne0\), we have \(1/a\ne0\). If \(1/a<0\), then multiplying \(1/a<0\) by \(a>0\) as in (6) would give \(1<0\), contradicting (5). Hence \(1/a>0\). Now let \(0<a<b\). Then \(ab>0\) by (4), so \(1/(ab)>0\), and multiplying \(a<b\) by \(1/(ab)\) gives \(1/b<1/a\) by (6). Finally \(1/b>0\) by the first part, since \(b>0\).

\textit{(8)} Multiplying \(a<b\) by \(b>0\) gives \(ab<b^2\), and multiplying \(a\le b\) by \(a\ge0\) gives \(a^2\le ab\) by (6). Hence \(a^2<b^2\).
\end{proof}

\begin{proposition}
Let \(F\) be an ordered field. For a positive integer \(n\) write \(n\cdot1=1+1+\dots+1\) (\(n\) summands). Then \(n\cdot1>0\) for every positive integer \(n\), and \(m\cdot1<n\cdot1\) whenever \(m<n\). Consequently \(F\) has characteristic \(0\), and \(n\mapsto n\cdot1\) is an injective, order-preserving map from the positive integers into \(F\).
\end{proposition}

\begin{proof}
We use \PMlinkname{induction}{PrincipleOfFiniteInduction} on \(n\). For \(n=1\), \(1\cdot1=1>0\) by part (5) of the previous proposition. If \(n\cdot1>0\), then \((n+1)\cdot1=n\cdot1+1>0\) by part (4), as a sum of two positive elements.

If \(m<n\) are positive integers, then \(n\cdot1=m\cdot1+(n-m)\cdot1\) by associativity of addition, and \((n-m)\cdot1>0\), so \(m\cdot1<n\cdot1\) by part (2). In particular \(n\cdot1\ne0\) for all \(n\ge1\), which is the statement that \(F\) has characteristic \(0\), and distinct positive integers have distinct images.
\end{proof}

Because of this proposition one identifies each natural number \(n\) with \(n\cdot1\in F\); the identification respects addition, multiplication and order. Since the characteristic is \(0\), the prime subfield of \(F\) is a copy of \(\mathbb{Q}\), so every ordered field contains the rational numbers. In particular a finite field cannot be ordered.

\begin{example}
The field \(\mathbb{Q}\) of rational numbers and the field \(\mathbb{R}\) of real numbers, with their usual orders, are ordered fields. The real numbers are distinguished among ordered fields by the \PMlinkname{least upper bound property}{LeastUpperBoundProperty}, which \(\mathbb{Q}\) lacks.
\end{example}

\begin{example}
The field \(\mathbb{C}\) of complex numbers cannot be made into an ordered field, whatever total order is chosen. Indeed, in any ordered field every square is \(\ge0\) and \(-1<0\), by part (5) of the first proposition. In \(\mathbb{C}\) the element \(-1=i^2\) is a square, so it would satisfy both \(-1\ge0\) and \(-1<0\), which is impossible.
\end{example}

The order of an ordered field gives rise to the \PMlinkname{absolute value}{AbsoluteValueOfARealNumber} \(\abs{a}=\max(a,-a)\) and its triangle inequality, the basic tool for estimates in analysis.
""")


entry("least upper bound property", "least-upper-bound-property", ["26A03", "12J15"],
      ["completeness axiom"],
      ["complete ordered field"],
      ["supremum", "ordered-field"], r"""
The rational numbers already satisfy all the algebraic and order axioms that the real numbers do, and what separates the two is a single further axiom saying that sets bounded above have a least upper bound.

Throughout, \(F\) is an \PMlinkname{ordered field}{OrderedField} and \(S\subseteq F\).

\begin{definition}
An element \(u\in F\) is an \emph{upper bound} of \(S\) if \(x\le u\) for all \(x\in S\), and \(S\) is \emph{bounded above} if it has an upper bound. Similarly, \(l\in F\) is a \emph{lower bound} of \(S\) if \(l\le x\) for all \(x\in S\), and \(S\) is \emph{bounded below} if it has a lower bound. A set that is bounded above and below is called bounded.
\end{definition}

An upper bound \(s\) of \(S\) with \(s\le u\) for every upper bound \(u\) of \(S\) is the least upper bound, or \PMlinkname{supremum}{Supremum}, of \(S\), written \(\sup S\). It is unique when it exists: if \(s\) and \(s'\) are both least upper bounds, then \(s\le s'\) and \(s'\le s\), so \(s=s'\).

\begin{definition}
A lower bound \(t\) of \(S\) with \(l\le t\) for every lower bound \(l\) of \(S\) is the greatest lower bound, or \emph{infimum}, of \(S\), written \(\inf S\). As for the supremum, it is unique when it exists.
\end{definition}

\begin{definition}
An ordered field \(F\) has the \emph{least upper bound property} if every nonempty subset of \(F\) that is bounded above has a supremum in \(F\). An ordered field with the least upper bound property is called a \emph{complete ordered field}.
\end{definition}

The requirement that the set be nonempty is essential: every element of \(F\) is an upper bound of the empty set, and an ordered field has no least element (for any \(a\), \(a-1<a\)), so the empty set has no supremum.

It is a theorem, which we cite and do not prove here, that a complete ordered field exists, and that it is unique up to isomorphism: if \(F\) and \(G\) are complete ordered fields, there is exactly one field isomorphism \(F\to G\), and it preserves the order. Such a field can be constructed from \(\mathbb{Q}\), for instance by Dedekind cuts or as equivalence classes of Cauchy sequences of rational numbers. The field \(\mathbb{R}\) of real numbers is, by definition, this complete ordered field, so the least upper bound property is often taken as the completeness axiom for \(\mathbb{R}\). One of its first consequences is the \PMlinkname{Archimedean property}{ArchimedeanPropertyOfTheRealNumbers}.

\begin{proposition}
Let \(F\) be a complete ordered field and let \(S\subseteq F\) be nonempty and bounded below. Then \(S\) has an infimum, and
\[
\inf S=-\sup(-S),\qquad\text{where } -S=\{-x : x\in S\}.
\]
\end{proposition}

\begin{proof}
Let \(l\) be a lower bound of \(S\). For every \(x\in S\) we have \(l\le x\), hence \(-x\le-l\). So \(-l\) is an upper bound of \(-S\), and \(-S\) is nonempty because \(S\) is. By the least upper bound property, \(s=\sup(-S)\) exists. We show that \(-s\) is the infimum of \(S\).

For \(x\in S\), the element \(-x\) lies in \(-S\), so \(-x\le s\) and therefore \(-s\le x\); thus \(-s\) is a lower bound of \(S\). If \(l\) is any lower bound of \(S\), then \(-l\) is an upper bound of \(-S\), as shown above, so \(s\le-l\), that is, \(l\le-s\). Hence \(-s\) is the greatest lower bound of \(S\).
\end{proof}

So in a complete ordered field the greatest lower bound property, with infima in place of suprema, holds as well. The next proposition is the form in which suprema are most often used; it holds in any ordered field.

\begin{proposition}
Let \(S\subseteq F\) be nonempty and let \(s\in F\). Then \(s=\sup S\) if and only if
\begin{enumerate}
\item \(s\) is an upper bound of \(S\), and
\item for every \(\varepsilon>0\) there is \(x\in S\) with \(x>s-\varepsilon\).
\end{enumerate}
Similarly, \(t=\inf S\) if and only if \(t\) is a lower bound of \(S\) and for every \(\varepsilon>0\) there is \(x\in S\) with \(x<t+\varepsilon\).
\end{proposition}

\begin{proof}
Suppose \(s=\sup S\). Then (1) holds by definition. Let \(\varepsilon>0\). Then \(s-\varepsilon<s\), so \(s-\varepsilon\) is not an upper bound of \(S\): otherwise \(s\le s-\varepsilon\) since \(s\) is the least upper bound. Hence there is \(x\in S\) for which \(x\le s-\varepsilon\) fails, and by totality of the order \(x>s-\varepsilon\).

Conversely, suppose (1) and (2) hold, and let \(u\) be any upper bound of \(S\). If \(u<s\), put \(\varepsilon=s-u>0\). By (2) there is \(x\in S\) with \(x>s-\varepsilon=u\), contradicting that \(u\) is an upper bound. Hence \(s\le u\), by totality, and \(s\) is the least upper bound.

The statement about infima is proved in the same way, with all inequalities reversed.
\end{proof}

\begin{example}
The ordered field \(\mathbb{Q}\) does not have the least upper bound property. Let
\[
A=\{q\in\mathbb{Q} : q^2<2\}.
\]
Then \(A\) is nonempty, since \(1\in A\), and it is bounded above by \(2\): if \(q>2\), then \(q^2>4>2\) by part (8) of the first proposition in the entry on ordered fields, so \(q\notin A\). We show that no rational number is the supremum of \(A\).

\textit{Step 1: no rational number has square \(2\).} Suppose \(r\in\mathbb{Q}\) with \(r^2=2\). Replacing \(r\) by \(-r\) if necessary, and noting \(r\ne0\), we may write \(r=m/n\) with \(m,n\) positive integers, so that \(m^2=2n^2\). By the \PMlinkname{well-ordering principle}{WellorderingPrincipleForNaturalNumbers}, we may choose such a pair with \(n\) as small as possible. Then \(m^2\) is even. The square of an odd integer \(2j+1\) is \(4j^2+4j+1\), which is odd, so \(m\) is even, say \(m=2m'\) with \(m'\) a positive integer. Then \(4m'^2=2n^2\), so \(n^2=2m'^2\). Moreover \(m'^2=n^2/2<n^2\), so \(m'<n\). Thus the pair \((n,m')\) of positive integers satisfies \(n^2=2m'^2\) with \(m'<n\), contradicting the minimality of \(n\).

\textit{Step 2: a rational supremum would satisfy \(s^2=2\).} Suppose \(s\in\mathbb{Q}\) is the supremum of \(A\) in \(\mathbb{Q}\). Since \(1\in A\), we have \(s\ge1>0\).

Suppose \(s^2<2\). Put
\[
h=\min\Bigl(1,\ \frac{2-s^2}{2(2s+1)}\Bigr),
\]
a positive rational number with \(h\le1\), so \(h^2\le h\). Then
\[
(s+h)^2=s^2+2sh+h^2\le s^2+h(2s+1)\le s^2+\frac{2-s^2}{2}<2.
\]
So \(s+h\in A\) and \(s+h>s\), contradicting that \(s\) is an upper bound of \(A\).

Suppose \(s^2>2\). Put \(h=(s^2-2)/(2s)\), a positive rational number. Since \(h=s/2-1/s<s\), the number \(s-h\) is positive and smaller than \(s\), and
\[
(s-h)^2=s^2-2sh+h^2>s^2-2sh=2.
\]
We claim that \(s-h\) is an upper bound of \(A\). If \(q\in A\) had \(q>s-h\), then \(0<s-h<q\), so \(q^2>(s-h)^2>2\), contradicting \(q^2<2\). So \(s-h\) is an upper bound of \(A\) smaller than \(s\), contradicting that \(s\) is the least upper bound.

By totality of the order, the only remaining possibility is \(s^2=2\), which Step 1 rules out. Hence \(A\) has no supremum in \(\mathbb{Q}\). The same argument, run in \(\mathbb{R}\), shows that \(\sup A\) exists there and is the positive real number whose square is \(2\).
\end{example}
""")


entry("absolute value of a real number", "absolute-value-of-a-real-number", ["26A03"],
      [], ["reverse triangle inequality"],
      ["ordered-field"], r"""
To say that two numbers are close one needs a measure of the size of their difference, and the absolute value provides it, together with the triangle inequality that makes estimates add up.

The definition and all the properties below use only the axioms of an \PMlinkname{ordered field}{OrderedField}, so they hold in \(\mathbb{Q}\) and \(\mathbb{R}\) alike. Throughout, \(F\) is an ordered field.

\begin{definition}
The absolute value of \(a\in F\) is
\[
\abs{a}=\begin{cases} a, & a\ge0,\\ -a, & a<0.\end{cases}
\]
\end{definition}

Two reformulations are used repeatedly. First, if \(a\le0\), then \(\abs{a}=-a\): for \(a<0\) this is the definition, and for \(a=0\) both sides are \(0\). Second,
\[
\abs{a}=\max(a,-a)\qquad\text{for all } a\in F.
\]
Indeed, if \(a\ge0\), then \(-a\le0\le a\), so \(\max(a,-a)=a=\abs{a}\); if \(a<0\), then \(a<0<-a\), so \(\max(a,-a)=-a=\abs{a}\). Since \(\max(a,-a)=\max(-a,a)\), it follows that \(\abs{-a}=\abs{a}\).

\begin{proposition}
For all \(a,b,c\in F\):
\begin{enumerate}
\item \(\abs{a}\ge0\), and \(\abs{a}=0\) if and only if \(a=0\);
\item \(\abs{ab}=\abs{a}\,\abs{b}\);
\item \(-\abs{a}\le a\le\abs{a}\);
\item \(\abs{a}\le c\) if and only if \(-c\le a\le c\), and \(\abs{a}<c\) if and only if \(-c<a<c\).
\end{enumerate}
\end{proposition}

\begin{proof}
\textit{(1)} If \(a\ge0\), then \(\abs{a}=a\ge0\). If \(a<0\), then \(\abs{a}=-a>0\). In the second case \(\abs{a}\ne0\), and in the first \(\abs{a}=0\) means \(a=0\). Hence \(\abs{a}=0\) exactly when \(a=0\).

\textit{(2)} If \(a\ge0\) and \(b\ge0\), then \(ab\ge0\), so \(\abs{ab}=ab=\abs{a}\,\abs{b}\). If \(a\ge0\) and \(b<0\), then \(a(-b)\ge0\), so \(ab=-(a(-b))\le0\) and \(\abs{ab}=-ab=a(-b)=\abs{a}\,\abs{b}\). The case \(a<0\), \(b\ge0\) is the same with the roles of \(a\) and \(b\) exchanged. If \(a<0\) and \(b<0\), then \(ab=(-a)(-b)>0\), so \(\abs{ab}=(-a)(-b)=\abs{a}\,\abs{b}\).

\textit{(3)} Since \(\abs{a}=\max(a,-a)\), we have \(a\le\abs{a}\) and \(-a\le\abs{a}\); the latter is equivalent to \(-\abs{a}\le a\).

\textit{(4)} Suppose \(\abs{a}\le c\). By (3), \(a\le\abs{a}\le c\) and \(-a\le\abs{a}\le c\), and the second inequality gives \(-c\le a\). Conversely, if \(-c\le a\le c\), then \(a\le c\) and \(-a\le c\), so \(\abs{a}=\max(a,-a)\le c\). The strict version is proved in the same way, since \(a\le\abs{a}<c\) gives \(a<c\), and \(\max(a,-a)<c\) whenever \(a<c\) and \(-a<c\).
\end{proof}

\begin{theorem}
For all \(a,b\in F\),
\[
\abs{a+b}\le\abs{a}+\abs{b}\qquad\text{and}\qquad\bigl\lvert\abs{a}-\abs{b}\bigr\rvert\le\abs{a-b}.
\]
The first inequality is the \emph{triangle inequality} and the second the \emph{reverse triangle inequality}.
\end{theorem}

\begin{proof}
By part (3) of the proposition, \(-\abs{a}\le a\le\abs{a}\) and \(-\abs{b}\le b\le\abs{b}\). Adding these inequalities gives
\[
-\bigl(\abs{a}+\abs{b}\bigr)\le a+b\le\abs{a}+\abs{b},
\]
and part (4), with \(c=\abs{a}+\abs{b}\), gives \(\abs{a+b}\le\abs{a}+\abs{b}\).

For the second inequality, apply the triangle inequality to \(a=(a-b)+b\):
\[
\abs{a}\le\abs{a-b}+\abs{b},\qquad\text{so}\qquad \abs{a}-\abs{b}\le\abs{a-b}.
\]
Exchanging \(a\) and \(b\), and using \(\abs{b-a}=\abs{-(a-b)}=\abs{a-b}\), gives \(\abs{b}-\abs{a}\le\abs{a-b}\), that is, \(-\abs{a-b}\le\abs{a}-\abs{b}\). By part (4), with \(c=\abs{a-b}\), we conclude \(\bigl\lvert\abs{a}-\abs{b}\bigr\rvert\le\abs{a-b}\).
\end{proof}

By induction on the number of terms, the triangle inequality extends to finite sums: \(\abs{a_1+\dots+a_n}\le\abs{a_1}+\dots+\abs{a_n}\), since \(\abs{a_1+\dots+a_{n+1}}\le\abs{a_1+\dots+a_n}+\abs{a_{n+1}}\).

The number \(\abs{x-y}\) is the distance between \(x\) and \(y\). By the results above it satisfies \(\abs{x-y}\ge0\), with equality exactly when \(x=y\); it is symmetric, \(\abs{x-y}=\abs{y-x}\); and it satisfies
\[
\abs{x-z}\le\abs{x-y}+\abs{y-z},
\]
by the triangle inequality applied to \(x-z=(x-y)+(y-z)\).

\begin{proposition}
Let \(x,c\in F\) and \(\delta>0\). Then
\[
\abs{x-c}<\delta\quad\text{if and only if}\quad c-\delta<x<c+\delta,
\]
and likewise \(\abs{x-c}\le\delta\) if and only if \(c-\delta\le x\le c+\delta\).
\end{proposition}

\begin{proof}
By part (4) of the first proposition, \(\abs{x-c}<\delta\) if and only if \(-\delta<x-c<\delta\). Adding \(c\) to each side of both inequalities, which preserves and reflects strict inequalities in an ordered field, this is equivalent to \(c-\delta<x<c+\delta\). The non-strict statement is proved in the same way.
\end{proof}

So for real numbers the set of \(x\) with \(\abs{x-c}<\delta\) is the open interval \((c-\delta,c+\delta)\). This is how the condition \(0<\abs{x-c}<\delta\) in the \PMlinkname{definition of a limit}{LimitOfARealFunction} is to be read: \(x\) lies in \((c-\delta,c+\delta)\) and \(x\ne c\).
""")

# ---- from part5.py ----
# Words in these bodies that might be mis-autolinked (ordinary-English or context-dependent uses):
# positive, negative, integer, integers, bounded, bound, upper bound, order, ordered, total,
# field, polynomial, polynomials, degree, leading coefficient, coefficient, constant, sum,
# product, square, squares, sign, contradiction, least element, rational, rationals, dense,
# interval, unique, uniqueness, property, numerator, denominator, representation, function,
# part, greatest, largest, smallest, between, step, case, closed, finite, contains.


entry("Archimedean property of the real numbers", "archimedean-property-of-the-real-numbers",
      ["26A03", "12J15"],
      [], [],
      ["least-upper-bound-property", "ordered-field"], r"""
No real number, however large, exceeds every positive integer, and this innocent-looking fact is what lets one compare arbitrary real numbers with integers and with the reciprocals \(1/n\).

Throughout, \(\mathbb{N}=\{1,2,3,\dots\}\) denotes the positive integers. In any \PMlinkname{ordered field}{OrderedField} \(F\) the elements \(1,\ 1+1,\ 1+1+1,\dots\) are positive and pairwise distinct, so \(\mathbb{N}\) is contained in \(F\), and with it \(\mathbb{Z}\) and \(\mathbb{Q}\). Every \(n\in\mathbb{N}\) satisfies \(n>0\). We use the \PMlinkname{least upper bound property}{LeastUpperBoundProperty} of \(\mathbb{R}\): every nonempty subset of \(\mathbb{R}\) that is bounded above has a \PMlinkname{supremum}{Supremum}.

\begin{theorem}
\begin{enumerate}
\item For every \(x\in\mathbb{R}\) there is \(n\in\mathbb{N}\) with \(n>x\).
\item For every \(\varepsilon>0\) in \(\mathbb{R}\) there is \(n\in\mathbb{N}\) with \(1/n<\varepsilon\).
\item For every \(a>0\) and every \(b\) in \(\mathbb{R}\) there is \(n\in\mathbb{N}\) with \(na>b\).
\end{enumerate}
\end{theorem}

\begin{proof}
\textit{Part 1.} Suppose, to the contrary, that some \(x\in\mathbb{R}\) satisfies \(n\le x\) for every \(n\in\mathbb{N}\). Then \(\mathbb{N}\) is a nonempty subset of \(\mathbb{R}\) that is bounded above by \(x\), so it has a supremum \(s\). Since \(s-1<s\), the number \(s-1\) is not an upper bound of \(\mathbb{N}\), so there is \(n\in\mathbb{N}\) with \(n>s-1\). Then \(n+1>s\). But \(n+1\in\mathbb{N}\) and \(s\) is an upper bound of \(\mathbb{N}\), so \(n+1\le s\), a contradiction.

\textit{Part 2.} Let \(\varepsilon>0\). Then \(1/\varepsilon>0\), and by part 1 there is \(n\in\mathbb{N}\) with \(n>1/\varepsilon\). From \(0<1/\varepsilon<n\) it follows, by taking reciprocals in an ordered field, that
\[
0<\frac{1}{n}<\frac{1}{1/\varepsilon}=\varepsilon.
\]

\textit{Part 3.} Let \(a>0\) and \(b\in\mathbb{R}\). By part 1 there is \(n\in\mathbb{N}\) with \(n>b/a\). Multiplying this inequality by the positive number \(a\) gives \(na>b\).
\end{proof}

The three statements are equivalent in every ordered field, not only in \(\mathbb{R}\); the least upper bound property is used only to prove the first one.

\begin{proposition}
In an ordered field \(F\), the following are equivalent.
\begin{enumerate}
\item For every \(x\in F\) there is \(n\in\mathbb{N}\) with \(n>x\).
\item For every \(\varepsilon>0\) in \(F\) there is \(n\in\mathbb{N}\) with \(1/n<\varepsilon\).
\item For every \(a>0\) and every \(b\) in \(F\) there is \(n\in\mathbb{N}\) with \(na>b\).
\end{enumerate}
An ordered field with these properties is called Archimedean.
\end{proposition}

\begin{proof}
The proofs of parts 2 and 3 of the theorem used only part 1 and the rules of an ordered field, so statement 1 implies statements 2 and 3 in \(F\).

Statement 3 implies statement 1: given \(x\), apply statement 3 with \(a=1\) and \(b=x\).

Statement 2 implies statement 1: let \(x\in F\). If \(x\le0\), then \(n=1\) works, since \(1>0\ge x\). If \(x>0\), then \(1/x>0\), and statement 2 gives \(n\in\mathbb{N}\) with \(0<1/n<1/x\). Taking reciprocals reverses the inequality between positive elements, so \(n>x\).
\end{proof}

\begin{corollary}
\begin{enumerate}
\item For every \(x\in\mathbb{R}\) there are integers \(m\) and \(n\) with \(m<x<n\).
\item If \(x\in\mathbb{R}\) satisfies \(0\le x\le 1/n\) for every \(n\in\mathbb{N}\), then \(x=0\).
\end{enumerate}
\end{corollary}

\begin{proof}
For the first statement, the theorem gives \(n\in\mathbb{N}\) with \(n>x\), and \(j\in\mathbb{N}\) with \(j>-x\); put \(m=-j\), so that \(m<x\).

For the second, suppose \(x>0\). By part 2 of the theorem, with \(\varepsilon=x\), there is \(n\in\mathbb{N}\) with \(1/n<x\), contradicting \(x\le1/n\). Hence \(x\le0\), and together with \(x\ge0\) this gives \(x=0\).
\end{proof}

The first statement of the corollary is the starting point for the \PMlinkname{floor function}{FloorFunction}, which locates every real number between two consecutive integers.

\begin{example}
The field \(\mathbb{Q}\) is Archimedean, although it lacks the least upper bound property. Indeed, every rational number can be written \(x=p/q\) with \(p\in\mathbb{Z}\) and \(q\in\mathbb{N}\). Since \(q\ge1\), we have \(x\le\abs{p}/q\le\abs{p}<\abs{p}+1\), and \(n=\abs{p}+1\in\mathbb{N}\).
\end{example}

\begin{remark}
Not every ordered field is Archimedean, so the least upper bound property, or some substitute, is really needed in the proof of the theorem. The standard example is the \PMlinkname{field}{Field} \(\mathbb{R}(t)\) of rational functions \(f=p/q\), where \(p,q\) are polynomials with real coefficients and \(q\ne0\); two quotients \(p/q\) and \(p'/q'\) are equal exactly when \(pq'=p'q\).

For a nonzero polynomial \(p\), write \(\operatorname{lc}(p)\) for its leading coefficient, the coefficient of its highest power of \(t\). Since \(\mathbb{R}\) has no zero divisors, \(\operatorname{lc}(pq)=\operatorname{lc}(p)\operatorname{lc}(q)\) for nonzero \(p,q\).

\textit{The positive elements.} Call a nonzero \(f=p/q\) positive if \(\operatorname{lc}(p)\operatorname{lc}(q)>0\). This does not depend on the representation: if \(p/q=p'/q'\) with \(p\ne0\), then \(p'\ne0\) and \(pq'=p'q\), so \(\operatorname{lc}(p)\operatorname{lc}(q')=\operatorname{lc}(p')\operatorname{lc}(q)\). Multiplying both sides by \(\operatorname{lc}(q)\operatorname{lc}(q')\) gives
\[
\operatorname{lc}(p)\operatorname{lc}(q)\cdot\operatorname{lc}(q')^2=\operatorname{lc}(p')\operatorname{lc}(q')\cdot\operatorname{lc}(q)^2,
\]
and since the squares are positive real numbers, \(\operatorname{lc}(p)\operatorname{lc}(q)\) and \(\operatorname{lc}(p')\operatorname{lc}(q')\) have the same sign. Replacing \(p,q\) by \(-p,-q\) if necessary, every element can be written \(p/q\) with \(\operatorname{lc}(q)>0\); then a nonzero \(f\) is positive exactly when \(\operatorname{lc}(p)>0\). Let \(P\) be the set of positive elements. It has three properties.
\begin{itemize}
\item For every \(f\), exactly one of \(f\in P\), \(f=0\), \(-f\in P\) holds. Indeed, if \(f=p/q\ne0\), then \(p\ne0\) and \(\operatorname{lc}(p)\operatorname{lc}(q)\) is a nonzero real number, while \(-f=(-p)/q\) has \(\operatorname{lc}(-p)\operatorname{lc}(q)=-\operatorname{lc}(p)\operatorname{lc}(q)\).
\item \(P\) is closed under multiplication: if \(f_i=p_i/q_i\in P\) for \(i=1,2\), then
\(\operatorname{lc}(p_1p_2)\operatorname{lc}(q_1q_2)=\bigl(\operatorname{lc}(p_1)\operatorname{lc}(q_1)\bigr)\bigl(\operatorname{lc}(p_2)\operatorname{lc}(q_2)\bigr)>0\).
\item \(P\) is closed under addition: write \(f_i=p_i/q_i\in P\) with \(\operatorname{lc}(q_i)>0\), so \(\operatorname{lc}(p_i)>0\). Then \(f_1+f_2=(p_1q_2+p_2q_1)/(q_1q_2)\) with \(\operatorname{lc}(q_1q_2)>0\). The polynomials \(p_1q_2\) and \(p_2q_1\) both have positive leading coefficients. If their degrees differ, the leading coefficient of the sum is that of the summand of larger degree; if the degrees are equal, it is the sum of the two leading coefficients. Either way it is positive, so the numerator is nonzero and \(f_1+f_2\in P\).
\end{itemize}

\textit{The order.} Define \(f<g\) if \(g-f\in P\), and \(f\le g\) if \(f<g\) or \(f=g\). This is a total order: it is reflexive by definition; if \(f\le g\) and \(g\le f\) with \(f\ne g\), then both \(g-f\) and \(f-g=-(g-f)\) lie in \(P\), which the first property forbids; if \(f\le g\le h\), then \(h-f=(h-g)+(g-f)\) is \(0\), or lies in \(P\) by the third property, so \(f\le h\); and for any \(f,g\) the first property applied to \(g-f\) gives \(f<g\), \(f=g\) or \(g<f\). It is compatible with the field operations: if \(f\le g\), then \((g+h)-(f+h)=g-f\), so \(f+h\le g+h\); and if \(0\le f\) and \(0\le g\), then \(fg=0\) or \(fg\in P\) by the second property, so \(0\le fg\). Hence \(\mathbb{R}(t)\) is an ordered field. On constants it is the usual order of \(\mathbb{R}\), since a nonzero constant \(c=c/1\) is positive exactly when \(c>0\).

\textit{Failure of the Archimedean property.} For every \(n\in\mathbb{N}\) the element \(t-n=(t-n)/1\) has numerator with leading coefficient \(1>0\), so \(n<t\). Thus \(\mathbb{N}\) is bounded above by \(t\) in \(\mathbb{R}(t)\), and statement 1 of the proposition fails. Equivalently, \(1/t\) is a positive element smaller than every \(1/n\): the difference \(1/n-1/t=(t-n)/(nt)\) has numerator and denominator with positive leading coefficients \(1\) and \(n\). By the theorem's proof, \(\mathbb{R}(t)\) cannot have the least upper bound property; indeed the set \(\mathbb{N}\), which is nonempty and bounded above, has no supremum in \(\mathbb{R}(t)\).
\end{remark}
""")


entry("floor function", "floor-function", ["26A09", "11A25"],
      ["greatest integer function"], ["ceiling function", "fractional part"],
      ["archimedean-property-of-the-real-numbers"], r"""
Every real number lies between two consecutive integers, and naming the lower of the two gives a function from \(\mathbb{R}\) to \(\mathbb{Z}\) that is used constantly to round, to count lattice points, and to split a number into an integer and a remainder.

Throughout, \(\mathbb{N}=\{1,2,3,\dots\}\) and \(\mathbb{Z}=\mathbb{N}\cup\{0\}\cup\{-n : n\in\mathbb{N}\}\), regarded as subsets of \(\mathbb{R}\). We use the \PMlinkname{Archimedean property}{ArchimedeanPropertyOfTheRealNumbers}, \PMlinkname{induction}{PrincipleOfFiniteInduction}, and the \PMlinkname{well-ordering principle}{WellorderingPrincipleForNaturalNumbers}: every nonempty subset of \(\mathbb{N}\) has a least element.

\begin{lemma}
\begin{enumerate}
\item Every \(n\in\mathbb{N}\) satisfies \(n\ge1\). Consequently there is no integer \(m\) with \(0<m<1\).
\item If \(k\) and \(m\) are integers with \(k<m\), then \(k+1\le m\). In particular, there is no integer strictly between \(k\) and \(k+1\).
\end{enumerate}
\end{lemma}

\begin{proof}
For the first statement, use induction on \(n\). Clearly \(1\ge1\). If \(n\ge1\), then \(n+1\ge1+1>1\), since \(1>0\). Now let \(m\) be an integer with \(0<m<1\). Since \(m>0\), we have \(m\ne0\) and \(m\) is not of the form \(-n\) with \(n\in\mathbb{N}\), because such numbers are negative. So \(m\in\mathbb{N}\), and then \(m\ge1\), contradicting \(m<1\).

For the second, \(m-k\) is an integer with \(m-k>0\). By the first part \(m-k\) is not in \((0,1)\), so \(m-k\ge1\), that is, \(m\ge k+1\). An integer \(m\) with \(k<m<k+1\) would contradict this.
\end{proof}

\begin{theorem}
For every \(x\in\mathbb{R}\) there is exactly one integer \(k\) such that
\[
k\le x<k+1.
\]
\end{theorem}

\begin{proof}
\textit{Existence.} By the Archimedean property there are \(n_1,n_2\in\mathbb{N}\) with \(n_1>x\) and \(n_2>-x\), so that \(-n_2<x<n_1\). Consider
\[
A=\{j\in\mathbb{N} : -n_2+j>x\}.
\]
It contains \(j=n_1+n_2\), because \(-n_2+n_1+n_2=n_1>x\). By the well-ordering principle \(A\) has a least element \(j_0\). Put \(k=-n_2+j_0-1\), an integer. Then \(k+1=-n_2+j_0>x\) because \(j_0\in A\). To see \(k\le x\), consider two cases. If \(j_0=1\), then \(k=-n_2<x\). If \(j_0\ne1\), then \(j_0-1\in\mathbb{N}\), and \(j_0-1\notin A\) because it is smaller than the least element \(j_0\); that is, \(k=-n_2+(j_0-1)\le x\).

\textit{Uniqueness.} Suppose \(k\) and \(k'\) are integers with \(k\le x<k+1\) and \(k'\le x<k'+1\). If \(k<k'\), then the lemma gives \(k'\ge k+1>x\), contradicting \(k'\le x\). By symmetry \(k'<k\) is impossible too, so \(k=k'\).
\end{proof}

\begin{definition}
For \(x\in\mathbb{R}\), the \emph{floor} of \(x\), written \(\lfloor x\rfloor\), is the unique integer \(k\) with \(k\le x<k+1\). The map \(x\mapsto\lfloor x\rfloor\) is the floor function. The \emph{ceiling function} is
\[
\lceil x\rceil=-\lfloor -x\rfloor,
\]
and the \emph{fractional part} of \(x\) is
\[
\{x\}=x-\lfloor x\rfloor.
\]
\end{definition}

The notation \([x]\) for \(\lfloor x\rfloor\) is also common, especially in older texts. For example, \(\lfloor 2.5\rfloor=2\), \(\lfloor -2.5\rfloor=-3\), \(\lceil -2.5\rceil=-2\), \(\{2.5\}=0.5\) and \(\{-2.5\}=0.5\).

\begin{proposition}
Let \(x,y\in\mathbb{R}\) and \(m\in\mathbb{Z}\).
\begin{enumerate}
\item \(\lfloor x\rfloor\) is the greatest integer that is \(\le x\): if \(m\le x\), then \(m\le\lfloor x\rfloor\).
\item \(x-1<\lfloor x\rfloor\le x\), and \(0\le\{x\}<1\).
\item \(\lfloor x+m\rfloor=\lfloor x\rfloor+m\), and hence \(\{x+m\}=\{x\}\).
\item \(\lfloor x\rfloor=x\) if and only if \(x\in\mathbb{Z}\); equivalently, \(\{x\}=0\) if and only if \(x\in\mathbb{Z}\).
\item If \(x\le y\), then \(\lfloor x\rfloor\le\lfloor y\rfloor\).
\item \(\lceil x\rceil\) is the unique integer \(c\) with \(c-1<x\le c\), and it is the least integer that is \(\ge x\). Moreover \(\lceil x\rceil=\lfloor x\rfloor\) if \(x\in\mathbb{Z}\), and \(\lceil x\rceil=\lfloor x\rfloor+1\) otherwise.
\end{enumerate}
\end{proposition}

\begin{proof}
Write \(k=\lfloor x\rfloor\), so \(k\le x<k+1\).

\textit{1.} If \(m\) is an integer with \(m>k\), then \(m\ge k+1>x\) by the lemma. So every integer \(m\le x\) satisfies \(m\le k\).

\textit{2.} Subtracting \(1\) from \(x<k+1\) gives \(x-1<k\), and \(k\le x\) holds by definition. Subtracting \(k\) from \(k\le x<k+1\) gives \(0\le x-k<1\).

\textit{3.} Adding \(m\) gives \(k+m\le x+m<(k+m)+1\), and \(k+m\) is an integer, so by uniqueness \(\lfloor x+m\rfloor=k+m\). Then \(\{x+m\}=x+m-(k+m)=x-k=\{x\}\).

\textit{4.} If \(x\in\mathbb{Z}\), then \(k=x\) is an integer with \(x\le x<x+1\), so \(\lfloor x\rfloor=x\) by uniqueness. Conversely, if \(\lfloor x\rfloor=x\), then \(x\) is an integer because \(\lfloor x\rfloor\) is.

\textit{5.} The integer \(\lfloor x\rfloor\) satisfies \(\lfloor x\rfloor\le x\le y\), so \(\lfloor x\rfloor\le\lfloor y\rfloor\) by statement 1.

\textit{6.} Let \(j=\lfloor -x\rfloor\), so \(j\le -x<j+1\), and \(c=\lceil x\rceil=-j\). Negating reverses the inequalities: \(-j-1<x\le -j\), that is, \(c-1<x\le c\). If \(c'\) is another integer with \(c'-1<x\le c'\), then \(-c'\le -x<-c'+1\), so \(-c'=\lfloor -x\rfloor=j\) by uniqueness and \(c'=c\). If \(m\) is an integer with \(m\ge x\) and \(m<c\), then \(m\le c-1<x\) by the lemma, which is impossible; so \(c\) is the least integer \(\ge x\). Finally, if \(x\in\mathbb{Z}\) then \(c=x=k\), because \(x\) itself is an integer with \(x-1<x\le x\). If \(x\notin\mathbb{Z}\), then \(k<x<k+1\) by statement 4, so \(k+1\) is an integer with \((k+1)-1<x\le k+1\), and \(c=k+1\).
\end{proof}

\begin{corollary}
Let \(x\in\mathbb{R}\) and \(k=\lfloor x\rfloor\). Then \(-1\le x-k-1<0\), and if \(x\notin\mathbb{Z}\), then \(-1<x-k-1<0\).
\end{corollary}

\begin{proof}
By statement 2 of the proposition, \(0\le x-k<1\); subtract \(1\). If \(x\notin\mathbb{Z}\), then \(x\ne k\) by statement 4, so \(x-k>0\) and \(x-k-1>-1\).
\end{proof}

This is exactly how the floor function enters the proof that \PMlinkname{integral powers force an integral exponent}{IntegralPowersForceAnIntegralExponent}: with \(k=\lfloor x\rfloor\), the exponent \(x-k-1\) of the \((k+1)\)st derivative of \(t^x\) is negative, and greater than \(-1\) when \(x\) is not an integer.

\begin{corollary}
Between any two real numbers \(x<y\) there is a rational number.
\end{corollary}

\begin{proof}
By the Archimedean property there is \(n\in\mathbb{N}\) with \(1/n<y-x\), that is, \(nx+1<ny\). Let \(m=\lfloor nx\rfloor+1\). By statement 2 of the proposition, \(nx<m\le nx+1<ny\). Dividing by \(n>0\) gives \(x<m/n<y\).
\end{proof}
""")

# ---- from part6.py ----
# Words in these bodies that might be mis-autolinked (ordinary-English or context-dependent uses):
# limit, limits, point, points, limit point, interval, open, closed, bounded, bound, side,
# order, function, constant, constants, sum, sums, difference, product, products, quotient,
# quotients, multiple, polynomial, polynomials, degree, power, composition, restriction,
# identity, domain, neighbourhood, isolated, sign, positive, interior, value, values, rule,
# rules, chain, step, case, base, induction, contradiction, inequality, increment, formula.


entry("limit of a real function", "limit-of-a-real-function", ["26A03", "26A06"],
      [], ["limit laws"],
      ["onesided-limit", "absolute-value-of-a-real-number"], r"""
Continuity and differentiation both describe what happens to \(f(x)\) as \(x\) approaches a point without necessarily reaching it, and the \(\varepsilon\)-\(\delta\) limit is the precise form of that idea.

Throughout, \(D\subseteq\mathbb{R}\) and \(f,g\colon D\to\mathbb{R}\). The facts about absolute values that we use, in particular the \PMlinkname{triangle inequality}{AbsoluteValueOfARealNumber} \(\abs{a+b}\le\abs{a}+\abs{b}\), its reverse form \(\abs{a}-\abs{b}\le\abs{a-b}\), and \(\abs{ab}=\abs{a}\abs{b}\), are proved in the entry on the absolute value.

\begin{definition}
A real number \(c\) is a \emph{limit point} of \(D\) if for every \(\delta>0\) there is \(x\in D\) with \(0<\abs{x-c}<\delta\).
\end{definition}

A limit point of \(D\) need not belong to \(D\): the point \(0\) is a limit point of \((0,1)\). A point of \(D\) need not be a limit point of \(D\): no point of \(\mathbb{Z}\) is a limit point of \(\mathbb{Z}\), since for \(c\in\mathbb{Z}\) the only integer \(x\) with \(\abs{x-c}<1\) is \(c\) itself. Every point of an interval with more than one point, including its endpoints, is a limit point of that interval.

\begin{definition}
Let \(c\) be a limit point of \(D\) and let \(L\in\mathbb{R}\). We say that \(f(x)\) has \emph{limit} \(L\) as \(x\) tends to \(c\), and write
\[
\lim_{x\to c}f(x)=L,
\]
if for every \(\varepsilon>0\) there is \(\delta>0\) such that
\[
\abs{f(x)-L}<\varepsilon\qquad\text{for all } x\in D \text{ with } 0<\abs{x-c}<\delta.
\]
\end{definition}

The value \(f(c)\), if it is defined at all, plays no role, because \(x=c\) is excluded by the condition \(0<\abs{x-c}\). When the domain must be made explicit we write \(\lim_{x\to c,\,x\in D}f(x)\).

\begin{proposition}
Let \(c\) be a limit point of \(D\). If \(\lim_{x\to c}f(x)=L\) and \(\lim_{x\to c}f(x)=L'\), then \(L=L'\).
\end{proposition}

\begin{proof}
Suppose \(L\ne L'\) and put \(\varepsilon=\abs{L-L'}/2>0\). There are \(\delta_1,\delta_2>0\) such that \(\abs{f(x)-L}<\varepsilon\) for \(x\in D\) with \(0<\abs{x-c}<\delta_1\), and \(\abs{f(x)-L'}<\varepsilon\) for \(x\in D\) with \(0<\abs{x-c}<\delta_2\). Let \(\delta=\min(\delta_1,\delta_2)\). Because \(c\) is a limit point of \(D\), there is \(x\in D\) with \(0<\abs{x-c}<\delta\). For this \(x\),
\[
\abs{L-L'}\le\abs{L-f(x)}+\abs{f(x)-L'}<2\varepsilon=\abs{L-L'},
\]
which is impossible. Hence \(L=L'\).
\end{proof}

The hypothesis that \(c\) is a limit point cannot be dropped. If there were \(\delta_0>0\) with no \(x\in D\) satisfying \(0<\abs{x-c}<\delta_0\), then the condition in the definition would hold vacuously, with \(\delta=\delta_0\), for every \(L\in\mathbb{R}\). This is why limits are only considered at limit points of the domain.

\begin{example}
Let \(c\) be a limit point of \(D\). If \(f(x)=k\) for all \(x\in D\), then \(\lim_{x\to c}f(x)=k\): any \(\delta>0\) works, since \(\abs{f(x)-k}=0\). If \(f(x)=x\) for all \(x\in D\), then \(\lim_{x\to c}f(x)=c\): given \(\varepsilon>0\), take \(\delta=\varepsilon\), so that \(\abs{f(x)-c}=\abs{x-c}<\varepsilon\) whenever \(0<\abs{x-c}<\delta\).
\end{example}

The following restriction lemma says that shrinking the domain does not change a limit, provided \(c\) remains a limit point.

\begin{lemma}
Let \(c\) be a limit point of \(D\), let \(E\subseteq D\), and suppose that \(c\) is also a limit point of \(E\). If \(\lim_{x\to c,\,x\in D}f(x)=L\), then \(\lim_{x\to c,\,x\in E}f(x)=L\).
\end{lemma}

\begin{proof}
A \(\delta\) that works for all \(x\in D\) with \(0<\abs{x-c}<\delta\) works in particular for all such \(x\in E\).
\end{proof}

The following rules, which compute limits of combinations of functions from the limits of the pieces, are called the \emph{limit laws}.

\begin{theorem}
Let \(c\) be a limit point of \(D\), and suppose that \(\lim_{x\to c}f(x)=L\) and \(\lim_{x\to c}g(x)=M\). Then:
\begin{enumerate}
\item \(\lim_{x\to c}\bigl(f(x)+g(x)\bigr)=L+M\);
\item \(\lim_{x\to c}f(x)g(x)=LM\);
\item \(\lim_{x\to c}af(x)=aL\) for every \(a\in\mathbb{R}\);
\item if \(M\ne0\), then there is \(\delta_0>0\) such that \(\abs{g(x)}>\abs{M}/2\) for all \(x\in D\) with \(0<\abs{x-c}<\delta_0\); the point \(c\) is a limit point of \(D'=\{x\in D : g(x)\ne0\}\); and, for the function \(f/g\colon D'\to\mathbb{R}\),
\[
\lim_{x\to c}\frac{f(x)}{g(x)}=\frac{L}{M}.
\]
\end{enumerate}
\end{theorem}

\begin{proof}
\textit{Sums.} Let \(\varepsilon>0\). Choose \(\delta_1,\delta_2>0\) such that \(\abs{f(x)-L}<\varepsilon/2\) for \(x\in D\) with \(0<\abs{x-c}<\delta_1\), and \(\abs{g(x)-M}<\varepsilon/2\) for \(x\in D\) with \(0<\abs{x-c}<\delta_2\). For \(x\in D\) with \(0<\abs{x-c}<\min(\delta_1,\delta_2)\),
\[
\abs{f(x)+g(x)-(L+M)}\le\abs{f(x)-L}+\abs{g(x)-M}<\frac{\varepsilon}{2}+\frac{\varepsilon}{2}=\varepsilon.
\]

\textit{Products.} For every \(x\in D\),
\[
f(x)g(x)-LM=f(x)\bigl(g(x)-M\bigr)+M\bigl(f(x)-L\bigr),
\]
so
\[
\abs{f(x)g(x)-LM}\le\abs{f(x)}\,\abs{g(x)-M}+\abs{M}\,\abs{f(x)-L}.
\]
Applying the definition of \(\lim f=L\) with \(\varepsilon=1\) gives \(\delta_1>0\) such that \(\abs{f(x)-L}<1\), and hence \(\abs{f(x)}\le\abs{L}+\abs{f(x)-L}<\abs{L}+1\), for \(x\in D\) with \(0<\abs{x-c}<\delta_1\). Now let \(\varepsilon>0\). Choose \(\delta_2>0\) with \(\abs{g(x)-M}<\varepsilon/\bigl(2(\abs{L}+1)\bigr)\) for \(x\in D\) with \(0<\abs{x-c}<\delta_2\), and \(\delta_3>0\) with \(\abs{f(x)-L}<\varepsilon/\bigl(2(\abs{M}+1)\bigr)\) for \(x\in D\) with \(0<\abs{x-c}<\delta_3\). For \(x\in D\) with \(0<\abs{x-c}<\min(\delta_1,\delta_2,\delta_3)\),
\[
\abs{f(x)g(x)-LM}<(\abs{L}+1)\cdot\frac{\varepsilon}{2(\abs{L}+1)}+\abs{M}\cdot\frac{\varepsilon}{2(\abs{M}+1)}<\frac{\varepsilon}{2}+\frac{\varepsilon}{2}=\varepsilon.
\]

\textit{Constant multiples.} The constant function \(x\mapsto a\) on \(D\) has limit \(a\) at \(c\) by the example above, so this is the case of products in which \(g\) is that constant function.

\textit{Quotients.} Suppose \(M\ne0\). Applying the definition of \(\lim g=M\) with \(\varepsilon=\abs{M}/2>0\) gives \(\delta_0>0\) such that \(\abs{g(x)-M}<\abs{M}/2\) for \(x\in D\) with \(0<\abs{x-c}<\delta_0\). For such \(x\), the reverse triangle inequality gives
\[
\abs{g(x)}\ge\abs{M}-\abs{g(x)-M}>\abs{M}-\frac{\abs{M}}{2}=\frac{\abs{M}}{2}>0.
\]
In particular \(g(x)\ne0\), so every \(x\in D\) with \(0<\abs{x-c}<\delta_0\) lies in \(D'\). Consequently \(c\) is a limit point of \(D'\): given \(\delta>0\), there is \(x\in D\) with \(0<\abs{x-c}<\min(\delta,\delta_0)\), and this \(x\) belongs to \(D'\).

We first show that \(\lim_{x\to c,\,x\in D'}1/g(x)=1/M\). For \(x\in D'\),
\[
\abs{\frac{1}{g(x)}-\frac{1}{M}}=\frac{\abs{M-g(x)}}{\abs{g(x)}\,\abs{M}}.
\]
Let \(\varepsilon>0\). By the restriction lemma, \(\lim_{x\to c,\,x\in D'}g(x)=M\), so there is \(\delta_1>0\) such that \(\abs{g(x)-M}<\varepsilon\abs{M}^2/2\) for \(x\in D'\) with \(0<\abs{x-c}<\delta_1\). If \(x\in D'\) and \(0<\abs{x-c}<\min(\delta_0,\delta_1)\), then \(\abs{g(x)}>\abs{M}/2\), so
\[
\abs{\frac{1}{g(x)}-\frac{1}{M}}<\frac{\varepsilon\abs{M}^2/2}{(\abs{M}/2)\abs{M}}=\varepsilon.
\]
Finally, by the restriction lemma \(\lim_{x\to c,\,x\in D'}f(x)=L\), and the case of products, applied on the domain \(D'\) to \(f\) and \(1/g\), gives
\[
\lim_{x\to c}\frac{f(x)}{g(x)}=\lim_{x\to c}f(x)\cdot\frac{1}{g(x)}=L\cdot\frac{1}{M}=\frac{L}{M}.
\]
\end{proof}

Since \(f-g=f+(-1)g\), the limit of a difference is the difference of the limits. By induction on the number of terms or factors, the laws for sums and products extend to finitely many functions.

\begin{proposition}
Let \(c\) be a limit point of \(D\), and suppose that \(\lim_{x\to c}f(x)=L\) and \(\lim_{x\to c}g(x)=M\). If there is \(\delta_0>0\) such that \(f(x)\le g(x)\) for all \(x\in D\) with \(0<\abs{x-c}<\delta_0\), then \(L\le M\).
\end{proposition}

\begin{proof}
Suppose instead that \(L>M\), and let \(\varepsilon=(L-M)/2>0\). Choose \(\delta_1,\delta_2>0\) such that \(\abs{f(x)-L}<\varepsilon\) for \(x\in D\) with \(0<\abs{x-c}<\delta_1\), and \(\abs{g(x)-M}<\varepsilon\) for \(x\in D\) with \(0<\abs{x-c}<\delta_2\). Since \(c\) is a limit point of \(D\), there is \(x\in D\) with \(0<\abs{x-c}<\min(\delta_0,\delta_1,\delta_2)\). For this \(x\),
\[
f(x)>L-\varepsilon=\frac{L+M}{2}=M+\varepsilon>g(x),
\]
contradicting \(f(x)\le g(x)\). Hence \(L\le M\).
\end{proof}

Strict inequalities are not preserved: \(f(x)=0<x^2=g(x)\) for \(x\ne0\), yet both functions have limit \(0\) at \(0\).

The next result is the squeeze rule.

\begin{proposition}
Let \(c\) be a limit point of \(D\), and let \(f,g,h\colon D\to\mathbb{R}\). Suppose that there is \(\delta_0>0\) with \(f(x)\le h(x)\le g(x)\) for all \(x\in D\) with \(0<\abs{x-c}<\delta_0\), and that \(\lim_{x\to c}f(x)=\lim_{x\to c}g(x)=L\). Then \(\lim_{x\to c}h(x)=L\).
\end{proposition}

\begin{proof}
Let \(\varepsilon>0\) and choose \(\delta_1,\delta_2>0\) such that \(\abs{f(x)-L}<\varepsilon\) for \(x\in D\) with \(0<\abs{x-c}<\delta_1\), and \(\abs{g(x)-L}<\varepsilon\) for \(x\in D\) with \(0<\abs{x-c}<\delta_2\). For \(x\in D\) with \(0<\abs{x-c}<\min(\delta_0,\delta_1,\delta_2)\),
\[
L-\varepsilon<f(x)\le h(x)\le g(x)<L+\varepsilon,
\]
so \(\abs{h(x)-L}<\varepsilon\).
\end{proof}

Unlike the previous proposition, the squeeze rule proves that a limit exists rather than assuming it.

Let \(D_c^+=D\cap(c,\infty)\) and \(D_c^-=D\cap(-\infty,c)\). If \(c\) is a limit point of \(D_c^+\), the limit of the restriction of \(f\) to \(D_c^+\) is the \PMlinkname{one-sided limit}{OnesidedLimit} from the right,
\[
\lim_{x\to c^+}f(x)=\lim_{x\to c,\,x\in D_c^+}f(x);
\]
explicitly, \(\lim_{x\to c^+}f(x)=L\) means that for every \(\varepsilon>0\) there is \(\delta>0\) with \(\abs{f(x)-L}<\varepsilon\) for all \(x\in D\) with \(c<x<c+\delta\). The limit \(\lim_{x\to c^-}f(x)\) from the left is defined in the same way using \(D_c^-\), that is, \(x\in D\) with \(c-\delta<x<c\). One-sided limits are limits in the sense above, on a smaller domain, so they are unique and obey the limit laws and the order properties.

\begin{theorem}
Suppose that \(c\) is a limit point of both \(D_c^+\) and \(D_c^-\), and let \(L\in\mathbb{R}\). Then \(\lim_{x\to c}f(x)=L\) if and only if both one-sided limits \(\lim_{x\to c^+}f(x)\) and \(\lim_{x\to c^-}f(x)\) exist and equal \(L\).
\end{theorem}

\begin{proof}
A limit point of \(D_c^+\) is a limit point of the larger set \(D\), so \(\lim_{x\to c}f(x)\) makes sense. If \(\lim_{x\to c}f(x)=L\), the restriction lemma, applied with \(E=D_c^+\) and with \(E=D_c^-\), shows that both one-sided limits equal \(L\).

Conversely, suppose both one-sided limits equal \(L\), and let \(\varepsilon>0\). There are \(\delta_+,\delta_->0\) such that \(\abs{f(x)-L}<\varepsilon\) whenever \(x\in D\) and \(c<x<c+\delta_+\), and whenever \(x\in D\) and \(c-\delta_-<x<c\). Let \(\delta=\min(\delta_+,\delta_-)\) and let \(x\in D\) with \(0<\abs{x-c}<\delta\). Then \(x\ne c\). If \(x>c\), then \(c<x<c+\delta_+\); if \(x<c\), then \(c-\delta_-<x<c\). In either case \(\abs{f(x)-L}<\varepsilon\).
\end{proof}

\begin{example}
Let \(f(x)=-1\) for \(x<0\) and \(f(x)=1\) for \(x\ge0\), on \(D=\mathbb{R}\). The one-sided limits at \(0\) are \(-1\) and \(1\), which differ, so \(\lim_{x\to0}f(x)\) does not exist.
\end{example}

\begin{definition}
Suppose that \(D\) is not bounded above, and let \(L\in\mathbb{R}\). We write \(\lim_{x\to\infty}f(x)=L\) if for every \(\varepsilon>0\) there is \(K\in\mathbb{R}\) such that \(\abs{f(x)-L}<\varepsilon\) for all \(x\in D\) with \(x>K\). Limits as \(x\to-\infty\), for \(D\) not bounded below, are defined in the same way with \(x<K\).
\end{definition}

Because \(D\) is not bounded above, for every \(K\) there is \(x\in D\) with \(x>K\), and the proof of uniqueness above goes through with \(x>\max(K_1,K_2)\) in place of \(0<\abs{x-c}<\min(\delta_1,\delta_2)\). For example, on \(D=(0,\infty)\) we have \(\lim_{x\to\infty}1/x=0\): given \(\varepsilon>0\), take \(K=1/\varepsilon\); then \(x>K>0\) gives \(0<1/x<1/K=\varepsilon\).
""")


entry("continuity of real functions", "continuity-of-real-functions", ["26A15"],
      ["continuous real function"], ["continuous at a point"],
      ["limit-of-a-real-function", "differentiable-function"], r"""
A function is continuous at a point when small changes in the input near that point produce small changes in the output, and this is the hypothesis behind the extreme value theorem, the mean value theorem and much of analysis.

Throughout, \(D\subseteq\mathbb{R}\) and \(f,g\colon D\to\mathbb{R}\). Limits are taken in the \(\varepsilon\)-\(\delta\) sense of the entry on the \PMlinkname{limit of a real function}{LimitOfARealFunction}, whose results we use.

\begin{definition}
Let \(c\in D\). The function \(f\) is \emph{continuous at a point} \(c\), or simply continuous at \(c\), if for every \(\varepsilon>0\) there is \(\delta>0\) such that
\[
\abs{f(x)-f(c)}<\varepsilon\qquad\text{for all } x\in D \text{ with } \abs{x-c}<\delta.
\]
The function \(f\) is a \emph{continuous function}, or is continuous on \(D\), if it is continuous at every point of \(D\).
\end{definition}

Continuity at \(c\) depends only on the values of \(f\) on \(D\); points outside \(D\) are never considered. At an endpoint of an interval \(D\), for example, it is continuity from one side.

\begin{proposition}
Let \(c\in D\).
\begin{enumerate}
\item If \(c\) is not a limit point of \(D\), then every function on \(D\) is continuous at \(c\).
\item If \(c\) is a limit point of \(D\), then \(f\) is continuous at \(c\) if and only if \(\lim_{x\to c}f(x)=f(c)\).
\end{enumerate}
\end{proposition}

\begin{proof}
For the first part, since \(c\) is not a limit point of \(D\) there is \(\delta_0>0\) such that no \(x\in D\) satisfies \(0<\abs{x-c}<\delta_0\). Thus the only \(x\in D\) with \(\abs{x-c}<\delta_0\) is \(x=c\), for which \(\abs{f(x)-f(c)}=0\). So \(\delta=\delta_0\) works for every \(\varepsilon>0\).

For the second part, the condition for continuity concerns all \(x\in D\) with \(\abs{x-c}<\delta\), and the condition for \(\lim_{x\to c}f(x)=f(c)\) concerns those with \(0<\abs{x-c}<\delta\). They differ only at \(x=c\), where \(\abs{f(c)-f(c)}=0<\varepsilon\) holds automatically. So the same \(\delta\) serves for both, and the two conditions are equivalent.
\end{proof}

A point of \(D\) that is not a limit point of \(D\) is called an isolated point of \(D\). For example, every function \(f\colon\mathbb{Z}\to\mathbb{R}\) is continuous, since every point of \(\mathbb{Z}\) is isolated.

\begin{example}
Let \(f(x)=0\) for \(x<0\) and \(f(x)=1\) for \(x\ge0\), on \(D=\mathbb{R}\). Then \(f\) is not continuous at \(0\): with \(\varepsilon=1/2\), every \(\delta>0\) admits the point \(x=-\delta/2\), for which \(\abs{x-0}<\delta\) but \(\abs{f(x)-f(0)}=1\). On the other hand, \(x\mapsto1/x\) on \(D=\mathbb{R}\setminus\{0\}\) is a continuous function, by the theorem below, even though it cannot be extended to a function continuous at \(0\); the point \(0\) is simply not in its domain.
\end{example}

\begin{theorem}
Suppose that \(f\) and \(g\) are continuous at \(c\in D\), and let \(a\in\mathbb{R}\). Then \(f+g\), \(fg\) and \(af\) are continuous at \(c\). If moreover \(g(c)\ne0\), then \(f/g\), defined on \(D'=\{x\in D : g(x)\ne0\}\), is continuous at \(c\); in particular \(1/g\) is continuous at \(c\).
\end{theorem}

\begin{proof}
Note that \(c\in D'\) when \(g(c)\ne0\).

\textit{Case 1: \(c\) is not a limit point of \(D\).} Then \(c\) is not a limit point of the subset \(D'\) either, so all four functions are continuous at \(c\) by the first part of the proposition.

\textit{Case 2: \(c\) is a limit point of \(D\).} By the second part of the proposition, \(\lim_{x\to c}f(x)=f(c)\) and \(\lim_{x\to c}g(x)=g(c)\). The limit laws give
\[
\lim_{x\to c}\bigl(f(x)+g(x)\bigr)=f(c)+g(c),\qquad\lim_{x\to c}f(x)g(x)=f(c)g(c),\qquad\lim_{x\to c}af(x)=af(c),
\]
so \(f+g\), \(fg\) and \(af\) are continuous at \(c\), again by the proposition. If \(g(c)\ne0\), the law for quotients says that \(c\) is a limit point of \(D'\) and that \(\lim_{x\to c,\,x\in D'}f(x)/g(x)=f(c)/g(c)\), so \(f/g\) is continuous at \(c\). Taking \(f\) to be the constant \(1\), which is continuous everywhere, shows that \(1/g\) is continuous at \(c\).
\end{proof}

Consequently, sums, products, constant multiples and quotients (where the denominator does not vanish) of continuous functions are continuous functions.

\begin{theorem}
Let \(E\subseteq\mathbb{R}\), let \(f\colon D\to\mathbb{R}\) with \(f(D)\subseteq E\), and let \(g\colon E\to\mathbb{R}\). If \(f\) is continuous at \(c\in D\) and \(g\) is continuous at \(f(c)\), then \(g\circ f\colon D\to\mathbb{R}\) is continuous at \(c\).
\end{theorem}

\begin{proof}
Let \(\varepsilon>0\). By continuity of \(g\) at \(f(c)\), there is \(\eta>0\) such that \(\abs{g(y)-g(f(c))}<\varepsilon\) for all \(y\in E\) with \(\abs{y-f(c)}<\eta\). By continuity of \(f\) at \(c\), applied with \(\eta\) in the role of \(\varepsilon\), there is \(\delta>0\) such that \(\abs{f(x)-f(c)}<\eta\) for all \(x\in D\) with \(\abs{x-c}<\delta\). For such \(x\), the point \(y=f(x)\) lies in \(E\) and satisfies \(\abs{y-f(c)}<\eta\), so \(\abs{g(f(x))-g(f(c))}<\varepsilon\).
\end{proof}

\begin{proposition}
Every polynomial function \(p(x)=a_0+a_1x+\cdots+a_nx^n\), with \(a_0,\ldots,a_n\in\mathbb{R}\), is continuous on \(\mathbb{R}\), and hence on every subset \(D\subseteq\mathbb{R}\). If \(p\) and \(q\) are polynomials, the rational function \(p/q\) is continuous on \(\{x\in D : q(x)\ne0\}\).
\end{proposition}

\begin{proof}
A constant function is continuous at every point, with any \(\delta\). The function \(x\mapsto x\) is continuous at every point \(c\), with \(\delta=\varepsilon\). By induction on \(k\), using \(x^{k+1}=x\cdot x^k\) and the theorem on products, every power \(x\mapsto x^k\) with \(k\ge1\) is continuous; together with the constant \(x^0=1\) this covers all \(k\ge0\). Each term \(a_kx^k\) is then continuous as a constant multiple, and \(p\) is continuous by induction on the number of terms, using the theorem on sums. The statement for \(p/q\) follows from the theorem on quotients. Restriction to \(D\) is handled by the next proposition.
\end{proof}

\begin{proposition}
Let \(E\subseteq D\) and \(c\in E\). If \(f\) is continuous at \(c\), then the restriction \(f|_E\) is continuous at \(c\).
\end{proposition}

\begin{proof}
A \(\delta\) that works for all \(x\in D\) with \(\abs{x-c}<\delta\) works in particular for all such \(x\in E\).
\end{proof}

The next lemma is used constantly: a continuous function that is positive at a point stays positive nearby.

\begin{lemma}
If \(f\) is continuous at \(c\in D\) and \(f(c)>0\), then there is \(\delta>0\) such that
\[
f(x)>\frac{f(c)}{2}>0\qquad\text{for all } x\in D \text{ with } \abs{x-c}<\delta.
\]
Similarly, if \(f(c)<0\), then \(f(x)<f(c)/2<0\) for all \(x\in D\) near \(c\).
\end{lemma}

\begin{proof}
Apply the definition of continuity with \(\varepsilon=f(c)/2>0\). For \(x\in D\) with \(\abs{x-c}<\delta\) we get \(f(x)-f(c)>-f(c)/2\), that is, \(f(x)>f(c)/2\). For \(f(c)<0\), apply this to \(-f\), which is continuous at \(c\) as a constant multiple of \(f\).
\end{proof}

\begin{remark}
A function \PMlinkname{differentiable}{DifferentiableFunction} at an interior point \(c\) of \(D\) is continuous at \(c\); this is proved in the entry on the \PMlinkname{rules of differentiation}{RulesOfDifferentiation}. The converse fails: \(x\mapsto\abs{x}\) is continuous at \(0\) but not differentiable there. Continuity of \(f\) on an interval \([a,b]\) is the hypothesis of the \PMlinkname{extreme value theorem}{ExtremeValueTheorem}.
\end{remark}

\begin{remark}
Give \(D\) the subspace topology from \(\mathbb{R}\), whose open sets are the sets \(U\cap D\) with \(U\) open in \(\mathbb{R}\). Then \(f\colon D\to\mathbb{R}\) is a continuous function in the sense above exactly when it is continuous as a map of topological spaces, in the sense that preimages of open sets are open; see \PMlinkname{continuity of maps between topological spaces}{ContinuityOfMapsBetweenTopologicalSpaces}. The \(\varepsilon\)-\(\delta\) definition is the special case of the topological one for metric spaces, with the sets \(\{x\in D : \abs{x-c}<\delta\}\) as basic neighbourhoods of \(c\) in \(D\).
\end{remark}
""")


entry("rules of differentiation", "rules-of-differentiation", ["26A24"],
      ["chain rule", "product rule", "sum rule"], ["higher derivative", "k times differentiable"],
      ["differentiable-function", "table-of-derivatives", "limit-of-a-real-function"], r"""
Derivatives of most functions met in practice are computed not from the definition but by breaking the function into sums, products and compositions of simpler ones, and the rules of differentiation justify each step.

Throughout, \(D\subseteq\mathbb{R}\), and limits and continuity are in the \(\varepsilon\)-\(\delta\) sense of the entries on the \PMlinkname{limit of a real function}{LimitOfARealFunction} and \PMlinkname{continuity of real functions}{ContinuityOfRealFunctions}. A point \(c\) is an interior point of \(D\) if \((c-r,c+r)\subseteq D\) for some \(r>0\).

\begin{definition}
Let \(f\colon D\to\mathbb{R}\) and let \(c\) be an interior point of \(D\). The function \(f\) is \PMlinkname{differentiable}{DifferentiableFunction} at \(c\) if the limit
\[
f'(c)=\lim_{h\to0}\frac{f(c+h)-f(c)}{h}
\]
exists; \(f'(c)\) is the derivative of \(f\) at \(c\). The difference quotient is defined for all \(h\ne0\) with \(c+h\in D\), a set that contains \((-r,0)\cup(0,r)\), so \(0\) is a limit point of its domain.
\end{definition}

Writing \(x=c+h\), the condition \(0<\abs{h}<\delta\) becomes \(0<\abs{x-c}<\delta\), and so equivalently
\[
f'(c)=\lim_{x\to c}\frac{f(x)-f(c)}{x-c},
\]
the limit being over \(x\in D\setminus\{c\}\). If \(c\) is an interior point of a subset \(E\subseteq D\), then \(f\) is differentiable at \(c\) if and only if \(f|_E\) is, with the same derivative, since the difference quotients near \(h=0\) are the same.

\begin{proposition}
If \(f\) is differentiable at an interior point \(c\) of \(D\), then \(f\) is continuous at \(c\).
\end{proposition}

\begin{proof}
For \(x\in D\) with \(x\ne c\),
\[
f(x)=f(c)+\frac{f(x)-f(c)}{x-c}\,(x-c).
\]
As \(x\to c\), the quotient tends to \(f'(c)\), the factor \(x-c\) tends to \(0\), and \(f(c)\) is constant, so by the limit laws \(\lim_{x\to c}f(x)=f(c)+f'(c)\cdot0=f(c)\). Since \(c\) is a limit point of \(D\), this means that \(f\) is continuous at \(c\).
\end{proof}

\begin{theorem}
Let \(f,g\colon D\to\mathbb{R}\) be differentiable at an interior point \(c\) of \(D\), and let \(a\in\mathbb{R}\). Then \(f+g\), \(af\) and \(fg\) are differentiable at \(c\), and
\[
(f+g)'(c)=f'(c)+g'(c),\qquad(af)'(c)=af'(c),\qquad(fg)'(c)=f'(c)g(c)+f(c)g'(c).
\]
\end{theorem}

\begin{proof}
For \(h\ne0\) with \(c+h\in D\),
\[
\frac{(f+g)(c+h)-(f+g)(c)}{h}=\frac{f(c+h)-f(c)}{h}+\frac{g(c+h)-g(c)}{h},
\]
and
\[
\frac{af(c+h)-af(c)}{h}=a\,\frac{f(c+h)-f(c)}{h}.
\]
By the limit laws for sums and constant multiples, these tend to \(f'(c)+g'(c)\) and \(af'(c)\) as \(h\to0\).

For the product rule, adding and subtracting \(f(c)g(c+h)\) gives
\[
\frac{f(c+h)g(c+h)-f(c)g(c)}{h}=\frac{f(c+h)-f(c)}{h}\,g(c+h)+f(c)\,\frac{g(c+h)-g(c)}{h}.
\]
By the proposition, \(g\) is continuous at \(c\), so \(\lim_{h\to0}g(c+h)=g(c)\): given \(\varepsilon>0\), the \(\delta\) from continuity of \(g\) at \(c\) gives \(\abs{g(c+h)-g(c)}<\varepsilon\) whenever \(c+h\in D\) and \(\abs{h}<\delta\). By the limit laws for products and sums, the right-hand side tends to \(f'(c)g(c)+f(c)g'(c)\).
\end{proof}

Taking \(a=-1\) gives \((f-g)'(c)=f'(c)-g'(c)\), and by induction the sum rule extends to finitely many functions.

\begin{proposition}
Let \(c\in\mathbb{R}\). A constant function \(f(x)=k\) has \(f'(c)=0\). The function \(f(x)=x\) has \(f'(c)=1\). For every integer \(n\ge1\), the function \(f(x)=x^n\) has
\[
f'(c)=nc^{n-1},
\]
where \(c^0=1\).
\end{proposition}

\begin{proof}
For a constant function the difference quotient is \((k-k)/h=0\) for every \(h\ne0\), and for \(f(x)=x\) it is \((c+h-c)/h=1\); the limits of these constant functions are \(0\) and \(1\).

We prove the formula for \(x^n\) by induction on \(n\). The case \(n=1\) is the function \(x\), with derivative \(1=1\cdot c^0\). Suppose the formula holds for \(n\). Since \(x^{n+1}=x\cdot x^n\), the product rule gives
\[
\frac{d}{dx}x^{n+1}\Big|_{x=c}=1\cdot c^n+c\cdot nc^{n-1}=(n+1)c^n,
\]
which is the formula for \(n+1\).
\end{proof}

\begin{corollary}
Every polynomial \(p(x)=a_0+a_1x+\cdots+a_nx^n\) is differentiable at every \(c\in\mathbb{R}\), with
\[
p'(c)=a_1+2a_2c+\cdots+na_nc^{n-1}=\sum_{k=1}^{n}ka_kc^{k-1}.
\]
In particular \(p'\) is again a polynomial, of degree less than that of \(p\) when \(p\) is not constant.
\end{corollary}

\begin{proof}
Each term \(a_kx^k\) is differentiable, by the proposition and the rule for constant multiples, with derivative \(ka_kc^{k-1}\) for \(k\ge1\) and \(0\) for \(k=0\). The sum rule, extended by induction to \(n+1\) terms, gives the formula.
\end{proof}

The natural attempt to prove the chain rule writes
\[
\frac{g(f(x))-g(f(c))}{x-c}=\frac{g(f(x))-g(f(c))}{f(x)-f(c)}\cdot\frac{f(x)-f(c)}{x-c},
\]
but this is meaningless at points \(x\ne c\) where \(f(x)=f(c)\), and for some functions, such as a constant \(f\), there are such points arbitrarily close to \(c\). The following reformulation of differentiability, due to Carath\'eodory, avoids division altogether.

\begin{lemma}
Let \(f\colon D\to\mathbb{R}\) and let \(c\) be an interior point of \(D\). Then \(f\) is differentiable at \(c\) if and only if there is a function \(\varphi\colon D\to\mathbb{R}\) that is continuous at \(c\) and satisfies
\[
f(x)-f(c)=\varphi(x)\,(x-c)\qquad\text{for all } x\in D.
\]
In that case \(\varphi(c)=f'(c)\).
\end{lemma}

\begin{proof}
Suppose that \(f\) is differentiable at \(c\). Define
\[
\varphi(x)=\begin{cases}\dfrac{f(x)-f(c)}{x-c}, & x\in D,\ x\ne c,\\[1ex] f'(c), & x=c.\end{cases}
\]
For \(x\ne c\) the identity \(f(x)-f(c)=\varphi(x)(x-c)\) holds by construction, and for \(x=c\) both sides are \(0\). Since \(c\) is a limit point of \(D\) and
\[
\lim_{x\to c}\varphi(x)=\lim_{x\to c}\frac{f(x)-f(c)}{x-c}=f'(c)=\varphi(c),
\]
the function \(\varphi\) is continuous at \(c\). (The limit only involves \(x\ne c\), where \(\varphi\) is the difference quotient.)

Conversely, suppose that \(\varphi\) is continuous at \(c\) and satisfies the identity. For \(x\in D\) with \(x\ne c\) we may divide by \(x-c\) and get
\[
\frac{f(x)-f(c)}{x-c}=\varphi(x).
\]
Since \(c\) is a limit point of \(D\) and \(\varphi\) is continuous at \(c\), we have \(\lim_{x\to c}\varphi(x)=\varphi(c)\). Hence the difference quotient has limit \(\varphi(c)\), that is, \(f\) is differentiable at \(c\) with \(f'(c)=\varphi(c)\). This also shows that \(\varphi(c)=f'(c)\) for every \(\varphi\) as in the statement, by uniqueness of limits.
\end{proof}

\begin{theorem}
Let \(E\subseteq\mathbb{R}\), let \(f\colon D\to\mathbb{R}\) with \(f(D)\subseteq E\), and let \(g\colon E\to\mathbb{R}\). Suppose that \(c\) is an interior point of \(D\), that \(f(c)\) is an interior point of \(E\), that \(f\) is differentiable at \(c\), and that \(g\) is differentiable at \(f(c)\). Then \(g\circ f\colon D\to\mathbb{R}\) is differentiable at \(c\), and
\[
(g\circ f)'(c)=g'\bigl(f(c)\bigr)\,f'(c).
\]
\end{theorem}

\begin{proof}
Let \(d=f(c)\). By the lemma there are \(\varphi\colon D\to\mathbb{R}\), continuous at \(c\) with \(\varphi(c)=f'(c)\), and \(\psi\colon E\to\mathbb{R}\), continuous at \(d\) with \(\psi(d)=g'(d)\), such that
\[
f(x)-f(c)=\varphi(x)(x-c)\quad(x\in D),\qquad g(y)-g(d)=\psi(y)(y-d)\quad(y\in E).
\]
For \(x\in D\), put \(y=f(x)\in E\) in the second identity and then use the first:
\[
g(f(x))-g(f(c))=\psi(f(x))\bigl(f(x)-f(c)\bigr)=\psi(f(x))\,\varphi(x)\,(x-c).
\]
Let \(\chi(x)=\psi(f(x))\varphi(x)\) for \(x\in D\). By the proposition above, \(f\) is continuous at \(c\); since \(\psi\) is continuous at \(f(c)\), the composite \(\psi\circ f\) is continuous at \(c\); and \(\varphi\) is continuous at \(c\). Hence the product \(\chi\) is continuous at \(c\). The lemma, applied to \(g\circ f\) and \(\chi\), shows that \(g\circ f\) is differentiable at \(c\) with
\[
(g\circ f)'(c)=\chi(c)=\psi(d)\varphi(c)=g'\bigl(f(c)\bigr)f'(c).
\]
\end{proof}

\begin{theorem}
Let \(f,g\colon D\to\mathbb{R}\) be differentiable at an interior point \(c\) of \(D\), with \(g(c)\ne0\). Then \(c\) is an interior point of \(D'=\{x\in D : g(x)\ne0\}\), and \(1/g\) and \(f/g\), as functions on \(D'\), are differentiable at \(c\) with
\[
\Bigl(\frac{1}{g}\Bigr)'(c)=-\frac{g'(c)}{g(c)^2},\qquad\Bigl(\frac{f}{g}\Bigr)'(c)=\frac{f'(c)g(c)-f(c)g'(c)}{g(c)^2}.
\]
\end{theorem}

\begin{proof}
Choose \(r>0\) with \((c-r,c+r)\subseteq D\). Since \(g\) is continuous at \(c\), there is \(\delta>0\) with \(\abs{g(x)-g(c)}<\abs{g(c)}/2\) for \(x\in D\) with \(\abs{x-c}<\delta\), and then \(\abs{g(x)}\ge\abs{g(c)}-\abs{g(x)-g(c)}>\abs{g(c)}/2>0\). Hence \((c-\rho,c+\rho)\subseteq D'\) for \(\rho=\min(r,\delta)\), so \(c\) is an interior point of \(D'\).

For \(h\ne0\) with \(c+h\in D'\),
\[
\frac{1}{h}\Bigl(\frac{1}{g(c+h)}-\frac{1}{g(c)}\Bigr)=-\frac{g(c+h)-g(c)}{h}\cdot\frac{1}{g(c+h)\,g(c)}.
\]
As \(h\to0\), the first factor tends to \(g'(c)\), and \(g(c+h)g(c)\to g(c)^2\ne0\) by continuity of \(g\) at \(c\), so by the limit laws for products and quotients the right-hand side tends to \(-g'(c)/g(c)^2\). This is the formula for \(1/g\). Since \(f|_{D'}\) is differentiable at \(c\) with derivative \(f'(c)\), the product rule applied on \(D'\) to \(f\) and \(1/g\) gives
\[
\Bigl(\frac{f}{g}\Bigr)'(c)=f'(c)\cdot\frac{1}{g(c)}+f(c)\cdot\Bigl(-\frac{g'(c)}{g(c)^2}\Bigr)=\frac{f'(c)g(c)-f(c)g'(c)}{g(c)^2}.
\]
\end{proof}

Let \(I\) be an open interval, so that every point of \(I\) is an interior point of \(I\). A function \(f\colon I\to\mathbb{R}\) is differentiable on \(I\) if it is differentiable at every point of \(I\); its derivative is then a function \(f'\colon I\to\mathbb{R}\), which may itself be differentiable.

\begin{definition}
Let \(f\colon I\to\mathbb{R}\) with \(I\) an open interval. Put \(f^{(0)}=f\). For \(k\ge1\), if \(f^{(k-1)}\) is defined and differentiable on \(I\), put
\[
f^{(k)}=\bigl(f^{(k-1)}\bigr)'.
\]
The function \(f^{(k)}\) is the \(k\)-th \emph{higher derivative} of \(f\), also written \(f''\) and \(f'''\) for \(k=2,3\). The function \(f\) is \emph{\(k\) times differentiable} on \(I\) if \(f^{(k)}\) is defined on all of \(I\), that is, if \(f^{(0)},f^{(1)},\ldots,f^{(k-1)}\) are all differentiable on \(I\).
\end{definition}

If \(f\) is \(k\) times differentiable on \(I\) with \(k\ge1\), then \(f^{(0)},\ldots,f^{(k-1)}\) are continuous on \(I\), by the first proposition, although \(f^{(k)}\) need not be. A function that is \(k\) times differentiable for every \(k\) is called \PMlinkname{smooth}{SmoothFunction}. By the definition, \(f^{(k)}\) is the derivative of order \(k-j\) of \(f^{(j)}\) for \(0\le j\le k\), and the sum and constant multiple rules give \((af+bg)^{(k)}=af^{(k)}+bg^{(k)}\) whenever \(f\) and \(g\) are \(k\) times differentiable, by induction on \(k\).

\begin{example}
Let \(n\ge0\) and \(f(x)=x^n\) on \(\mathbb{R}\). For every \(k\ge0\),
\[
f^{(k)}(x)=\begin{cases} n(n-1)\cdots(n-k+1)\,x^{n-k}, & k\le n,\\ 0, & k>n,\end{cases}
\]
where the empty product for \(k=0\) is \(1\). Indeed, for \(k=0\) this is \(f\) itself. If it holds for some \(k<n\), then \(n-k\ge1\) and the power rule gives \(f^{(k+1)}(x)=n(n-1)\cdots(n-k+1)(n-k)x^{n-k-1}\). If \(k=n\), then \(f^{(n)}=n!\) is constant and \(f^{(n+1)}=0\); if \(k>n\), the derivative of the zero function is \(0\). Consequently every polynomial is smooth on \(\mathbb{R}\), a polynomial of degree \(n\) with leading coefficient \(a_n\) has \(p^{(n)}=n!\,a_n\), and \(p^{(k)}=0\) for \(k>n\).
\end{example}

Derivatives of the elementary functions, obtained by combining these rules with the derivatives of the exponential function and the logarithm, are collected in the \PMlinkname{table of derivatives}{TableOfDerivatives}.
""")

# ---- from part1.py ----
# Words in these bodies that might be mis-autolinked (ordinary-English or context-dependent uses):
# bounded, interval, closed, open, continuous, continuity, limit, limits, maximum, minimum,
# endpoint, endpoints, point, interior, attains, value, values, bound, step, case, sign,
# contradiction, positive, finite, quotient, quotients, inequality, constant, critical point,
# least upper bound, upper bound, neighbourhood, domain, union, cancel.


entry("extreme value theorem", "extreme-value-theorem", ["26A15"],
      ["Weierstrass extreme value theorem"], [],
      ["supremum", "continuity-of-real-functions"], r"""
Many arguments in calculus need a point where a function is as large or as small as it can be, and the extreme value theorem guarantees such points for every continuous function on a closed and bounded interval.

Throughout, \(a<b\) are real numbers and \(f\colon[a,b]\to\mathbb{R}\) is \PMlinkname{continuous}{ContinuityOfRealFunctions} in the usual \(\varepsilon\)-\(\delta\) sense: for every \(c\in[a,b]\) and every \(\varepsilon>0\) there is \(\delta>0\) such that \(\abs{f(x)-f(c)}<\varepsilon\) for all \(x\in[a,b]\) with \(\abs{x-c}<\delta\). At the endpoints \(a\) and \(b\) this is continuity from one side only. The proof uses nothing beyond this definition and the \PMlinkname{least upper bound property}{LeastUpperBoundProperty} of \(\mathbb{R}\): every nonempty subset of \(\mathbb{R}\) that is bounded above has a \PMlinkname{supremum}{Supremum}.

\begin{theorem}
Let \(f\colon[a,b]\to\mathbb{R}\) be continuous. Then \(f\) is bounded, and there are points \(c,d\in[a,b]\) such that
\[
f(d)\le f(x)\le f(c)\qquad\text{for all } x\in[a,b].
\]
In other words, \(f\) attains a maximum value \(f(c)\) and a minimum value \(f(d)\) on \([a,b]\).
\end{theorem}

We prove boundedness first, as a lemma. The proof that follows the lemma then shows that the bounds are attained.

\begin{lemma}
A continuous function \(f\colon[a,b]\to\mathbb{R}\) is bounded: there is \(K\) with \(\abs{f(x)}\le K\) for all \(x\in[a,b]\).
\end{lemma}

\begin{proof}
Let
\[
S=\{t\in[a,b] : f \text{ is bounded on } [a,t]\}.
\]
The set \(S\) contains \(a\), since \(f\) is bounded on \([a,a]=\{a\}\), and \(S\) is bounded above by \(b\). By the least upper bound property, \(s=\sup S\) exists, and \(a\le s\le b\).

Apply continuity at \(s\) with \(\varepsilon=1\): there is \(\delta>0\) such that \(\abs{f(x)-f(s)}<1\), and hence \(\abs{f(x)}<\abs{f(s)}+1\), for all \(x\in[a,b]\) with \(\abs{x-s}<\delta\). Since \(s-\delta<s=\sup S\), the number \(s-\delta\) is not an upper bound of \(S\), so there is \(t\in S\) with \(s-\delta<t\le s\). Let \(B\) be a bound for \(\abs{f}\) on \([a,t]\), and put
\[
u=\min\Bigl(s+\frac{\delta}{2},\,b\Bigr).
\]
Every \(x\in[t,u]\) lies in \([a,b]\) and satisfies \(s-\delta<x<s+\delta\), so \(\abs{f(x)}<\abs{f(s)}+1\). Since \([a,u]=[a,t]\cup[t,u]\), we get \(\abs{f(x)}\le\max\bigl(B,\abs{f(s)}+1\bigr)\) for all \(x\in[a,u]\). Thus \(u\in S\), and therefore \(u\le s\).

If \(s<b\), then \(u=\min(s+\delta/2,b)>s\), which contradicts \(u\le s\). Hence \(s=b\), so \(u=b\), and \(b\in S\). That is, \(f\) is bounded on \([a,b]\).
\end{proof}

\begin{proof}
By the lemma, the set \(f([a,b])=\{f(x) : x\in[a,b]\}\) is nonempty and bounded, so it has a supremum \(M\). By definition \(f(x)\le M\) for every \(x\in[a,b]\); we show that \(f(c)=M\) for some \(c\).

Suppose not. Then \(M-f(x)>0\) for every \(x\in[a,b]\), so the function
\[
g(x)=\frac{1}{M-f(x)}
\]
is defined and positive on \([a,b]\). It is continuous, being the reciprocal of a continuous function that never vanishes. By the lemma there is \(K>0\) with \(g(x)\le K\) for all \(x\in[a,b]\). Then \(M-f(x)\ge 1/K\), that is,
\[
f(x)\le M-\frac{1}{K}\qquad\text{for all } x\in[a,b].
\]
So \(M-1/K\) is an upper bound of \(f([a,b])\) smaller than \(M\), contradicting the choice of \(M\) as the least upper bound. Hence \(f(c)=M\) for some \(c\in[a,b]\), and \(f(c)\) is the maximum value of \(f\).

For the minimum, apply what has just been proved to the continuous function \(-f\). It attains a maximum at some \(d\in[a,b]\), so \(-f(x)\le -f(d)\), that is, \(f(d)\le f(x)\), for all \(x\in[a,b]\).
\end{proof}

\begin{remark}
Each hypothesis is needed.
\begin{itemize}
\item The interval must be closed. On \((0,1]\) the continuous function \(f(x)=1/x\) is unbounded. On \((0,1)\) the continuous function \(f(x)=x\) is bounded, with supremum \(1\) and infimum \(0\), but attains neither.
\item The interval must be bounded. On \([0,\infty)\) the continuous function \(f(x)=x\) is unbounded, and \(f(x)=x/(1+x)\) is bounded, with supremum \(1\), but never equals \(1\).
\item The function must be continuous. On \([0,1]\) let \(f(x)=x\) for \(0\le x<1\) and \(f(1)=0\). Then \(f\) is bounded with supremum \(1\), but \(f(x)<1\) for every \(x\in[0,1]\).
\end{itemize}
\end{remark}

\begin{remark}
The theorem only asserts that extreme values exist; it does not say where they occur. The \PMlinkname{interior extremum theorem}{InteriorExtremumTheorem} narrows the search: an extreme value of \(f\) on \([a,b]\) occurs at an endpoint, at a point where \(f\) is not differentiable, or at a point where \(f'\) vanishes. Together the two theorems give the proof of \PMlinkname{Rolle's theorem}{RollesTheorem}.
\end{remark}
""")


entry("interior extremum theorem", "interior-extremum-theorem", ["26A24"],
      ["Fermat's interior extremum theorem"], ["local maximum", "local minimum"],
      ["differentiable-function", "onesided-limit", "extreme-value-theorem"], r"""
To find where a differentiable function is largest or smallest, it is enough to look at the points where its derivative vanishes, together with the boundary of its domain, and the interior extremum theorem is the reason.

\begin{definition}
Let \(D\subseteq\mathbb{R}\), let \(f\colon D\to\mathbb{R}\), and let \(c\in D\). The function \(f\) has a \emph{local maximum} at \(c\) if there is \(\delta>0\) such that
\[
f(x)\le f(c)\qquad\text{for all } x\in D \text{ with } \abs{x-c}<\delta.
\]
It has a \emph{local minimum} at \(c\) if there is \(\delta>0\) such that \(f(x)\ge f(c)\) for all \(x\in D\) with \(\abs{x-c}<\delta\). A local extremum is a local maximum or a local minimum.
\end{definition}

A maximum of \(f\) over all of \(D\), such as the one supplied by the \PMlinkname{extreme value theorem}{ExtremeValueTheorem}, is in particular a local maximum, with any \(\delta\). A point \(c\in D\) is an interior point of \(D\) if \((c-r,c+r)\subseteq D\) for some \(r>0\); for an interval \(D\) these are the points other than its endpoints.

\begin{theorem}
Let \(D\subseteq\mathbb{R}\), let \(f\colon D\to\mathbb{R}\), and let \(c\) be an interior point of \(D\). If \(f\) has a local maximum or a local minimum at \(c\) and \(f\) is \PMlinkname{differentiable}{DifferentiableFunction} at \(c\), then
\[
f'(c)=0.
\]
\end{theorem}

\begin{proof}
Suppose first that \(f\) has a local maximum at \(c\). Choose \(\delta>0\) so small that \((c-\delta,c+\delta)\subseteq D\) and \(f(x)\le f(c)\) for all \(x\) in this interval; this is possible by taking the smaller of the radius from the definition and the radius from the interiority of \(c\). For \(0<\abs{h}<\delta\) consider the difference quotient
\[
q(h)=\frac{f(c+h)-f(c)}{h}.
\]
Its numerator satisfies \(f(c+h)-f(c)\le 0\). Hence \(q(h)\le 0\) for \(0<h<\delta\), and \(q(h)\ge 0\) for \(-\delta<h<0\).

Because \(f\) is differentiable at \(c\), the limit of \(q(h)\) as \(h\to0\) exists and equals \(f'(c)\). A two-sided limit that exists also exists from each side, with the same value, so the \PMlinkname{one-sided limits}{OnesidedLimit} satisfy
\[
f'(c)=\lim_{h\to0^+}q(h)\qquad\text{and}\qquad f'(c)=\lim_{h\to0^-}q(h).
\]
Non-strict inequalities are preserved under \PMlinkname{limits}{LimitOfARealFunction}. The first limit is a limit of numbers \(q(h)\le0\), so \(f'(c)\le0\); the second is a limit of numbers \(q(h)\ge0\), so \(f'(c)\ge0\). Therefore \(f'(c)=0\).

If instead \(f\) has a local minimum at \(c\), then \(-f\) has a local maximum at \(c\) and is differentiable there with \((-f)'(c)=-f'(c)\). By the case already proved, \(-f'(c)=0\), so \(f'(c)=0\).
\end{proof}

\begin{example}
The converse is false: \(f'(c)=0\) does not force a local extremum at \(c\). Let \(f(x)=x^3\) on \(\mathbb{R}\). Then \(f'(x)=3x^2\), so \(f'(0)=0\). But for every \(\delta>0\), the points \(x=\pm\delta/2\) satisfy
\[
f(-\delta/2)=-\frac{\delta^3}{8}<0=f(0)<\frac{\delta^3}{8}=f(\delta/2),
\]
so \(f\) has neither a local maximum nor a local minimum at \(0\).
\end{example}

\begin{remark}
The other hypotheses cannot be dropped either.
\begin{itemize}
\item Interiority is needed. The function \(f(x)=x\) on \(D=[0,1]\) has a maximum at the endpoint \(1\), and the one-sided derivative there equals \(1\), not \(0\). The proof breaks down because only the quotients with \(h<0\) are available.
\item Differentiability is needed. The function \(f(x)=\abs{x}\) on \(\mathbb{R}\) has a minimum at the interior point \(0\), but \(f\) is not differentiable there: its one-sided difference quotients at \(0\) are \(1\) and \(-1\).
\end{itemize}
\end{remark}

\begin{corollary}
Let \(f\colon[a,b]\to\mathbb{R}\) be continuous, with \(a<b\). Every point \(c\in[a,b]\) at which \(f\) attains its maximum or its minimum value is either an endpoint \(a\) or \(b\), or a point of \((a,b)\) at which \(f\) is not differentiable, or a point of \((a,b)\) with \(f'(c)=0\).
\end{corollary}

\begin{proof}
Such points exist by the extreme value theorem. If \(c\in(a,b)\), then \(c\) is an interior point of \([a,b]\), and a global maximum or minimum is a local one, so if \(f\) is differentiable at \(c\) the theorem gives \(f'(c)=0\).
\end{proof}

This corollary is the heart of \PMlinkname{Rolle's theorem}{RollesTheorem}: if \(f(a)=f(b)\) and \(f\) is differentiable on \((a,b)\), then either \(f\) is constant or one of its extreme values is attained inside \((a,b)\), where the derivative must vanish.
""")

# ---- from part2.py ----
# Entries 3 and 4: Rolle's theorem, mean value theorem.
# Ordinary words in these bodies that might be mis-autolinked:
#   interval, closed, open, endpoint, endpoints, constant, continuous, differentiable,
#   maximum, minimum, value, point, line, slope, secant, chord, increasing, decreasing,
#   nondecreasing, strictly, interior, graph, function, difference, quotient, hypothesis,
#   special case, horizontal, tangent, average, rate, sign, corollary


entry("Rolle's theorem", "rolles-theorem", ["26A24"], [], [],
      ["extreme-value-theorem", "interior-extremum-theorem"], r"""
A smooth curve that starts and ends at the same height must level off somewhere in between, and Rolle's theorem makes this precise; it is the key step from which the mean value theorem, and with it most qualitative information about derivatives, is derived.

\begin{theorem}
Let \(a<b\) and let \(f\colon[a,b]\to\mathbb{R}\) be continuous on \([a,b]\) and differentiable on \((a,b)\). If \(f(a)=f(b)\), then there is a point \(c\in(a,b)\) with
\[
f'(c)=0.
\]
\end{theorem}

\begin{proof}
Since \(f\) is continuous on the closed and bounded interval \([a,b]\), the \PMlinkname{extreme value theorem}{ExtremeValueTheorem} gives points \(p,q\in[a,b]\) such that
\[
f(q)\le f(x)\le f(p)\qquad\text{for all } x\in[a,b].
\]
Put \(M=f(p)\) and \(m=f(q)\), and note \(m\le f(a)\le M\).

\textit{Case 1: \(M=f(a)\) and \(m=f(a)\).} Then \(f(a)\le f(x)\le f(a)\) for every \(x\in[a,b]\), so \(f\) is constant on \([a,b]\). Every difference quotient \(\bigl(f(x)-f(c)\bigr)/(x-c)\) is then \(0\), so \(f'(c)=0\) for every \(c\in(a,b)\); take for instance \(c=(a+b)/2\).

\textit{Case 2: \(M>f(a)\).} Then \(p\ne a\), and since \(f(b)=f(a)<M\), also \(p\ne b\). Hence \(p\in(a,b)\). Because \((a,b)\) is open, there is \(\delta>0\) with \((p-\delta,p+\delta)\subseteq(a,b)\), and \(f(x)\le f(p)\) for all \(x\) in this neighbourhood, so \(f\) has a local maximum at the interior point \(p\). The function \(f\) is differentiable at \(p\), so the \PMlinkname{interior extremum theorem}{InteriorExtremumTheorem} gives \(f'(p)=0\). Take \(c=p\).

\textit{Case 3: \(m<f(a)\).} The same argument with \(q\) in place of \(p\) and minimum in place of maximum shows \(q\in(a,b)\), that \(f\) has a local minimum at \(q\), and hence \(f'(q)=0\). Take \(c=q\).

Since \(m\le f(a)\le M\), the three cases exhaust all possibilities.
\end{proof}

The point \(c\) need not be unique: for \(f(x)=\sin x\) on \([0,3\pi]\), each of \(c=\pi/2\), \(c=3\pi/2\) and \(c=5\pi/2\) satisfies \(f'(c)=0\). The theorem asserts only existence.

\begin{example}
None of the hypotheses can be dropped.
\begin{itemize}
\item \textit{Differentiability on \((a,b)\).} Let \(f(x)=\abs{x}\) on \([-1,1]\). Then \(f\) is continuous and \(f(-1)=f(1)=1\), but \(f'(x)=-1\) for \(x<0\), \(f'(x)=1\) for \(x>0\), and \(f'(0)\) does not exist. No point has derivative \(0\).
\item \textit{Continuity at the endpoints.} Let \(f(x)=x\) for \(0\le x<1\) and \(f(1)=0\). Then \(f(0)=f(1)=0\) and \(f\) is differentiable on \((0,1)\) with \(f'(x)=1\) there. The function fails to be continuous only at \(x=1\), and that is enough for the conclusion to fail.
\item \textit{Equal endpoint values.} The function \(f(x)=x\) on \([0,1]\) is continuous and differentiable, but \(f'(x)=1\) everywhere. Here \(f(0)\ne f(1)\); the \PMlinkname{mean value theorem}{MeanValueTheorem} describes what remains true in that situation.
\end{itemize}
\end{example}

\begin{remark}
Differentiability is not required at the endpoints \(a\) and \(b\). For example, \(f(x)=\sqrt{1-x^2}\) on \([-1,1]\) is continuous, has \(f(-1)=f(1)=0\), and is differentiable on \((-1,1)\), though not at \(\pm1\). Rolle's theorem applies, and indeed \(f'(0)=0\).
\end{remark}

\begin{example}
Rolle's theorem bounds the number of real roots of a function by those of its derivative. Suppose \(f\) is differentiable on an interval \(I\) and has \(n\) distinct zeros \(x_1<x_2<\cdots<x_n\) in \(I\). Applying the theorem on each \([x_i,x_{i+1}]\) gives points \(c_i\in(x_i,x_{i+1})\) with \(f'(c_i)=0\), for \(i=1,\ldots,n-1\). These lie in disjoint open intervals, so they are distinct, and \(f'\) has at least \(n-1\) distinct zeros in \(I\). For instance, \(f(x)=x^3+x+1\) has \(f'(x)=3x^2+1>0\) for all \(x\), so \(f\) has at most one real zero.
\end{example}
""")


entry("mean value theorem", "mean-value-theorem", ["26A24"], ["Lagrange mean value theorem"], [],
      ["rolles-theorem", "differentiable-function"], r"""
The mean value theorem converts information about the derivative of a function into information about its values: the average rate of change over an interval is attained as an instantaneous rate of change at some interior point.

\begin{theorem}
Let \(a<b\) and let \(f\colon[a,b]\to\mathbb{R}\) be continuous on \([a,b]\) and \PMlinkname{differentiable}{DifferentiableFunction} on \((a,b)\). Then there is a point \(c\in(a,b)\) such that
\[
f'(c)=\frac{f(b)-f(a)}{b-a},
\]
or equivalently \(f(b)-f(a)=f'(c)\,(b-a)\).
\end{theorem}

Geometrically, the right side is the slope of the secant line through \((a,f(a))\) and \((b,f(b))\), and the theorem says that some tangent line at an interior point is parallel to it.

\begin{proof}
Let
\[
s=\frac{f(b)-f(a)}{b-a}
\qquad\text{and}\qquad
g(t)=f(t)-f(a)-(t-a)\,s\quad\text{for } t\in[a,b].
\]
The function \(g\) is \(f\) minus a polynomial of degree at most \(1\) in \(t\). Polynomials are continuous and differentiable everywhere, so \(g\) is continuous on \([a,b]\) and differentiable on \((a,b)\), with
\[
g'(t)=f'(t)-s\qquad\text{for } t\in(a,b).
\]
At the endpoints,
\[
g(a)=f(a)-f(a)-0=0,
\qquad
g(b)=f(b)-f(a)-(b-a)\,\frac{f(b)-f(a)}{b-a}=0.
\]
Thus \(g(a)=g(b)\), and \PMlinkname{Rolle's theorem}{RollesTheorem} gives \(c\in(a,b)\) with \(g'(c)=0\), that is, \(f'(c)=s\).
\end{proof}

When \(f(a)=f(b)\) the theorem reduces to Rolle's theorem, so the two statements are equivalent; the auxiliary function \(g\) simply subtracts the secant line from \(f\), which tilts the picture until the endpoint values agree.

\begin{example}
Let \(f(x)=x^2\) and \(a<b\). Then
\[
\frac{f(b)-f(a)}{b-a}=\frac{b^2-a^2}{b-a}=a+b,
\]
and \(f'(c)=2c\), so the point promised by the theorem is \(c=(a+b)/2\), the midpoint. For \(f(x)=x^3\) on \([0,1]\), the secant slope is \(1\) and \(f'(c)=3c^2=1\) gives \(c=1/\sqrt3\in(0,1)\).
\end{example}

The most frequent use of the theorem is to deduce the behaviour of a function from the sign of its derivative. In the following, an interval may be open, closed, half-open, bounded or unbounded, and \(I^\circ\) denotes the interior of \(I\) (the interval with its endpoints removed). Assume \(I\) contains more than one point.

\begin{corollary}
Let \(I\) be an interval and let \(f\colon I\to\mathbb{R}\) be continuous on \(I\) and differentiable on \(I^\circ\).
\begin{enumerate}
\item If \(f'(t)=0\) for all \(t\in I^\circ\), then \(f\) is constant on \(I\).
\item If \(f'(t)>0\) for all \(t\in I^\circ\), then \(f\) is strictly increasing on \(I\): \(x<y\) implies \(f(x)<f(y)\).
\item If \(f'(t)\ge0\) for all \(t\in I^\circ\), then \(f\) is nondecreasing on \(I\): \(x<y\) implies \(f(x)\le f(y)\).
\end{enumerate}
The analogous statements with \(f'<0\) (strictly decreasing) and \(f'\le0\) (nonincreasing) follow by applying these to \(-f\).
\end{corollary}

\begin{proof}
Let \(x,y\in I\) with \(x<y\). Since \(I\) is an interval, \([x,y]\subseteq I\), and \((x,y)\subseteq I^\circ\) because every point of \((x,y)\) has points of \(I\) on both sides of it. Hence \(f\) is continuous on \([x,y]\) and differentiable on \((x,y)\), and the theorem gives \(c\in(x,y)\subseteq I^\circ\) with
\[
f(y)-f(x)=f'(c)\,(y-x).
\]
Here \(y-x>0\). If \(f'\equiv0\) on \(I^\circ\), then \(f(y)=f(x)\); as \(x<y\) were arbitrary, \(f\) takes the same value at every pair of points, so it is constant. If \(f'>0\) on \(I^\circ\), then \(f'(c)>0\) and \(f(y)-f(x)>0\). If \(f'\ge0\) on \(I^\circ\), then \(f(y)-f(x)\ge0\).
\end{proof}

\begin{corollary}
Let \(I\) be an interval and let \(f,g\colon I\to\mathbb{R}\) be continuous on \(I\) and differentiable on \(I^\circ\) with \(f'=g'\) on \(I^\circ\). Then there is a constant \(C\) with \(f(x)=g(x)+C\) for all \(x\in I\).
\end{corollary}

\begin{proof}
Apply part 1 of the previous corollary to \(f-g\), whose derivative on \(I^\circ\) is \(f'-g'=0\).
\end{proof}

\begin{remark}
The hypothesis that the domain is an interval is essential in these corollaries. On \(D=(0,1)\cup(2,3)\), the function equal to \(0\) on \((0,1)\) and to \(1\) on \((2,3)\) has derivative \(0\) at every point of \(D\) but is not constant. Likewise, the converse of part 2 fails: \(f(x)=x^3\) is strictly increasing on \(\mathbb{R}\), yet \(f'(0)=0\). What is true is the converse of part 3: if \(f\) is nondecreasing and differentiable at \(t\), every difference quotient \(\bigl(f(x)-f(t)\bigr)/(x-t)\) is \(\ge0\), so \(f'(t)\ge0\).
\end{remark}

\begin{corollary}
Let \(f\colon[a,b]\to\mathbb{R}\) be continuous on \([a,b]\) and differentiable on \((a,b)\), and suppose \(\abs{f'(t)}\le L\) for all \(t\in(a,b)\). Then
\[
\abs{f(x)-f(y)}\le L\,\abs{x-y}\qquad\text{for all } x,y\in[a,b].
\]
\end{corollary}

\begin{proof}
For \(x=y\) there is nothing to prove. If \(x<y\), the theorem on \([x,y]\) gives \(c\in(x,y)\) with \(\abs{f(y)-f(x)}=\abs{f'(c)}\,(y-x)\le L\,(y-x)\). The case \(y<x\) is symmetric.
\end{proof}

For example, \(\abs{\sin x-\sin y}\le\abs{x-y}\) for all real \(x,y\), since \(\abs{\cos t}\le1\).

\begin{remark}
The theorem is a statement about real-valued functions. For \(f(t)=(\cos t,\sin t)\) from \([0,2\pi]\) to \(\mathbb{R}^2\), one has \(f(2\pi)-f(0)=0\) but \(f'(t)=(-\sin t,\cos t)\) never vanishes, so no \(c\) satisfies \(f(2\pi)-f(0)=f'(c)\,(2\pi-0)\). The inequality of the last corollary does survive for vector-valued functions. A discrete analogue, in which the derivative is replaced by a forward difference, is the \PMlinkname{mean value theorem for forward differences}{MeanValueTheoremForForwardDifferences}.
\end{remark}
""")

# ---- from part3.py ----
# Words in these bodies that might be mis-autolinked (ordinary-English or context-dependent uses):
# integral (meaning "integer-valued", not the integral of calculus), interval, open, closed,
# difference, differences, order, step, shift, domain, point, points, endpoint, power, powers,
# exponent, factor, factors, product, constant, positive, negative, decreasing, increasing,
# floor, value, values, induction, hypothesis, contradiction, case, base, term, node, nodes,
# spacing, mechanism, bound, limit, smooth, real, sufficiently large.


entry("mean value theorem for forward differences", "mean-value-theorem-for-forward-differences",
      ["26A24", "39A70"], ["difference mean value theorem"], [],
      ["finite-difference", "mean-value-theorem", "divided-difference-interpolation-formula"], r"""
A \(k\)-th forward difference of a function is built from its values at \(k+1\) equally spaced points, and this theorem says that it always equals a \(k\)-th derivative of the function somewhere between those points, just as a difference quotient equals a first derivative.

Throughout, the \PMlinkname{forward difference}{FiniteDifference} of a real function \(h\) is
\[
\Delta h(t)=h(t+1)-h(t),
\]
and the higher differences are defined recursively by \(\Delta^0h=h\) and \(\Delta^kh=\Delta(\Delta^{k-1}h)\) for \(k\ge1\). For instance
\[
\Delta^2h(t)=h(t+2)-2h(t+1)+h(t).
\]

\textit{Domains.} If \(h\) is defined on a set \(D\subseteq\mathbb{R}\), then \(\Delta h\) is defined on \(\{t : t\in D \text{ and } t+1\in D\}\). Let \(I=(a,b)\) be an open interval, where \(a\) may be \(-\infty\) and \(b\) may be \(+\infty\), and let \(h\) be defined on \(I\). Then \(\Delta h\) is defined on \(I\cap(I-1)=(a,b-1)\), and by induction on \(k\), \(\Delta^kh\) is defined on the open interval
\[
I_k=(a,b-k)=\{t : t\in I \text{ and } t+k\in I\},
\]
with the convention \(b-k=+\infty\) when \(b=+\infty\) (the interval \(I_k\) may be empty). Thus \(\Delta^kh(x)\) makes sense exactly when \([x,x+k]\subseteq I\), and its value depends only on \(h(x),h(x+1),\ldots,h(x+k)\).

\begin{lemma}
For every function \(h\) and every \(j\ge0\), \(\Delta^j(\Delta h)=\Delta^{j+1}h\), both sides being defined at the same points.
\end{lemma}

\begin{proof}
Induction on \(j\). For \(j=0\) both sides equal \(\Delta h\). If \(\Delta^j(\Delta h)=\Delta^{j+1}h\), then
\[
\Delta^{j+1}(\Delta h)=\Delta\bigl(\Delta^j(\Delta h)\bigr)=\Delta\bigl(\Delta^{j+1}h\bigr)=\Delta^{j+2}h.
\]
Applying \(\Delta\) to equal functions gives equal functions on the same set of points, so the domains agree at every stage.
\end{proof}

\begin{theorem}
Let \(k\ge1\), let \(I\) be an open interval, and let \(f\colon I\to\mathbb{R}\) be \(k\) times differentiable on \(I\). If \(x\in\mathbb{R}\) and \([x,x+k]\subseteq I\), then there is \(\xi\in(x,x+k)\) such that
\[
\Delta^kf(x)=f^{(k)}(\xi).
\]
\end{theorem}

\begin{proof}
We prove, by induction on \(k\ge1\), the statement: for every open interval \(I\), every \(f\) that is \(k\) times differentiable on \(I\), and every \(x\) with \([x,x+k]\subseteq I\), there is \(\xi\in(x,x+k)\) with \(\Delta^kf(x)=f^{(k)}(\xi)\).

\textit{Base case \(k=1\).} The function \(f\) is differentiable on \(I\supseteq[x,x+1]\), so it is continuous on \([x,x+1]\) and differentiable on \((x,x+1)\). The \PMlinkname{mean value theorem}{MeanValueTheorem} gives \(\xi\in(x,x+1)\) with
\[
\Delta f(x)=f(x+1)-f(x)=f'(\xi)\,\bigl((x+1)-x\bigr)=f'(\xi).
\]

\textit{Induction step.} Let \(k\ge2\) and assume the statement for \(k-1\). Let \(I=(a,b)\), \(f\) and \(x\) be as in the statement for \(k\). Put \(J=I\cap(I-1)=(a,b-1)\), an open interval, and define \(g\colon J\to\mathbb{R}\) by
\[
g(t)=\Delta f(t)=f(t+1)-f(t).
\]
For \(t\in J\) both \(t\) and \(t+1\) lie in \(I\). We claim that for \(0\le j\le k-1\) the derivative \(g^{(j)}\) exists on \(J\) and
\[
g^{(j)}(t)=f^{(j)}(t+1)-f^{(j)}(t)\qquad(t\in J).
\]
This holds for \(j=0\). If it holds for some \(j\le k-2\), then \(f^{(j)}\) is differentiable on \(I\), since \(j<k\). By the \PMlinkname{chain rule}{RulesOfDifferentiation} the function \(t\mapsto f^{(j)}(t+1)\) is differentiable on \(J\) with derivative \(f^{(j+1)}(t+1)\), so by the difference rule \(g^{(j+1)}(t)=f^{(j+1)}(t+1)-f^{(j+1)}(t)\). This proves the claim; in particular \(g\) is \(k-1\) times differentiable on \(J\).

Every \(t\in[x,x+k-1]\) satisfies \(t\in[x,x+k]\subseteq I\) and \(t+1\in[x+1,x+k]\subseteq I\), so \([x,x+k-1]\subseteq J\). The induction hypothesis, applied to \(g\) on \(J\) at the point \(x\), gives \(\eta\in(x,x+k-1)\) with
\[
\Delta^{k-1}g(x)=g^{(k-1)}(\eta)=f^{(k-1)}(\eta+1)-f^{(k-1)}(\eta).
\]
By the lemma, \(\Delta^{k-1}g(x)=\Delta^{k-1}(\Delta f)(x)=\Delta^kf(x)\).

Now \(x<\eta<\eta+1<x+k\), so \([\eta,\eta+1]\subseteq I\). The function \(f^{(k-1)}\) is differentiable on \(I\), hence continuous on \([\eta,\eta+1]\) and differentiable on \((\eta,\eta+1)\). By the mean value theorem there is \(\xi\in(\eta,\eta+1)\) with
\[
f^{(k-1)}(\eta+1)-f^{(k-1)}(\eta)=f^{(k)}(\xi).
\]
Combining, \(\Delta^kf(x)=f^{(k)}(\xi)\), and \(x<\eta<\xi<\eta+1<x+k\), so \(\xi\in(x,x+k)\).
\end{proof}

For \(k=1\) the theorem is exactly the mean value theorem on an interval of length \(1\).

\begin{example}
Let \(f(t)=t^k\) on \(I=\mathbb{R}\). Then \(f^{(k)}(t)=k!\) for every \(t\), so the theorem gives
\[
\Delta^k t^k=k!\qquad\text{for every } t\in\mathbb{R},
\]
whatever the point \(\xi\) is. For \(k=2\) this is the identity \((t+2)^2-2(t+1)^2+t^2=2\). Likewise \(\Delta^{k+1}t^k=0\), because the \((k+1)\)-th derivative of \(t^k\) vanishes identically.
\end{example}

The following elementary fact is what makes the theorem useful in arithmetic arguments, such as the proof that \PMlinkname{integral powers force an integral exponent}{IntegralPowersForceAnIntegralExponent}.

\begin{proposition}
Let \(f\) be a function, defined at least at the positive integers, such that \(f(m)\in\mathbb{Z}\) for every positive integer \(m\). Then \(\Delta^kf(n)\in\mathbb{Z}\) for every \(k\ge0\) and every positive integer \(n\).
\end{proposition}

\begin{proof}
Induction on \(k\). For \(k=0\), \(\Delta^0f(n)=f(n)\in\mathbb{Z}\). If \(\Delta^kf(m)\in\mathbb{Z}\) for every positive integer \(m\), then for every positive integer \(n\),
\[
\Delta^{k+1}f(n)=\Delta^kf(n+1)-\Delta^kf(n)
\]
is a difference of two integers, since \(n\) and \(n+1\) are positive integers. Hence it is an integer.
\end{proof}

\begin{remark}
The theorem adapts to any step \(h>0\). Write \(\Delta_hf(t)=f(t+h)-f(t)\) and \(\Delta_h^k=\Delta_h(\Delta_h^{k-1})\). If \(f\) is \(k\) times differentiable on an open interval \(I\supseteq[x,x+kh]\), apply the theorem to \(F(s)=f(hs)\) on the open interval \(\{s : hs\in I\}\), at the point \(x/h\). By induction \(\Delta^jF(s)=\Delta_h^jf(hs)\), and by the chain rule \(F^{(k)}(s)=h^kf^{(k)}(hs)\), so
\[
\Delta_h^kf(x)=h^kf^{(k)}(\xi)\qquad\text{for some } \xi\in(x,x+kh).
\]
Since the divided difference of \(f\) at the equally spaced nodes \(x,x+1,\ldots,x+k\) equals \(\Delta^kf(x)/k!\), the theorem is also the equally spaced case of the mean value theorem for divided differences, \(f[x,x+1,\ldots,x+k]=f^{(k)}(\xi)/k!\).
\end{remark}
""")


entry("integral powers force an integral exponent", "integral-powers-force-an-integral-exponent",
      ["26A24", "11A99"], [], [],
      ["mean-value-theorem-for-forward-differences", "finite-difference", "exponential-function", "floor-function"], r"""
Every integer power of a positive integer is an integer, and the striking fact proved here is a converse: a real exponent that turns every positive integer into an integer must itself be an integer, a statement about arithmetic whose proof is pure calculus.

For \(t>0\) and real \(a\), the power is \(t^a=e^{a\ln t}\), with the \PMlinkname{exponential function}{ExponentialFunction} and the \PMlinkname{natural logarithm}{AlternativeDefinitionOfTheNaturalLogarithm}. We use the standard facts that \(\exp\) is positive and strictly increasing with \(e^0=1\) and \((e^u)'=e^u\), that \(\ln\) is strictly increasing with \((\ln t)'=1/t\) and \(\ln t\to\infty\) as \(t\to\infty\), and that \(e^{u+v}=e^ue^v\). When \(a\) is a nonnegative integer, \(t^a\) is the usual product of \(a\) factors equal to \(t\).

\begin{lemma}
For every real \(a\), the function \(t\mapsto t^a\) is differentiable on \((0,\infty)\), with derivative \(at^{a-1}\). Consequently, for every real \(x\) the function \(f(t)=t^x\) is \PMlinkname{infinitely differentiable}{SmoothFunction} on \((0,\infty)\), and for every \(j\ge0\),
\[
f^{(j)}(t)=x(x-1)\cdots(x-j+1)\,t^{x-j},
\]
where for \(j=0\) the empty product is \(1\).
\end{lemma}

\begin{proof}
By the \PMlinkname{chain rule}{RulesOfDifferentiation},
\[
\frac{d}{dt}\,e^{a\ln t}=e^{a\ln t}\cdot\frac{a}{t}=a\,e^{a\ln t}e^{-\ln t}=a\,e^{(a-1)\ln t}=a\,t^{a-1}.
\]
The formula for \(f^{(j)}\) holds for \(j=0\). If it holds for \(j\), then by the first part, applied with \(a=x-j\),
\[
f^{(j+1)}(t)=x(x-1)\cdots(x-j+1)\,(x-j)\,t^{x-j-1},
\]
which is the formula for \(j+1\).
\end{proof}

With the lemma in hand, the theorem follows from the mean value theorem for forward differences.

\begin{theorem}
Let \(x\in\mathbb{R}\). If \(N^x\in\mathbb{Z}\) for every positive integer \(N\), then \(x\in\mathbb{Z}\); in fact \(x\) is a nonnegative integer.
\end{theorem}

\begin{proof}
\textit{Step 1: \(x\ge0\).} Suppose \(x<0\). Then \(x\ln2<0\), so \(0<2^x=e^{x\ln2}<e^0=1\). No integer lies strictly between \(0\) and \(1\), so \(2^x\notin\mathbb{Z}\), contrary to the hypothesis. Hence \(x\ge0\).

\textit{Step 2: setting up.} Let \(k=\lfloor x\rfloor\), the \PMlinkname{floor}{FloorFunction} of \(x\), be the integer with \(k\le x<k+1\); by Step 1, \(k\ge0\). Let \(f(t)=t^x\) on the open interval \(I=(0,\infty)\). By the lemma, \(f\) is \(k+1\) times differentiable on \(I\) and
\[
f^{(k+1)}(t)=c\,t^{x-k-1},\qquad\text{where } c=x(x-1)\cdots(x-k)
\]
is a product of \(k+1\) factors.

\textit{Step 3: the differences are integers.} By hypothesis \(f(m)=m^x\in\mathbb{Z}\) for every positive integer \(m\). By the proposition in the entry on the \PMlinkname{mean value theorem for forward differences}{MeanValueTheoremForForwardDifferences}, \(\Delta^{k+1}f(n)\in\mathbb{Z}\) for every positive integer \(n\). (Directly: \(\Delta^{j+1}f(n)=\Delta^jf(n+1)-\Delta^jf(n)\), so by induction on \(j\) every \(\Delta^jf(n)\) is a difference of integers.) Here \(\Delta\) is the \PMlinkname{forward difference}{FiniteDifference}, \(\Delta h(t)=h(t+1)-h(t)\).

\textit{Step 4: the differences are derivatives.} Let \(n\) be a positive integer. Then \([n,n+k+1]\subseteq I\), so the mean value theorem for forward differences, of order \(k+1\), gives \(\xi_n\in(n,n+k+1)\) with
\[
\Delta^{k+1}f(n)=f^{(k+1)}(\xi_n)=c\,\xi_n^{\,x-k-1}.
\]

\textit{Step 5: if \(x\notin\mathbb{Z}\), the differences are too small.} Suppose that \(x\) is not an integer. Then \(k<x<k+1\). For \(0\le i\le k\) we have \(x-i\ge x-k>0\), so every factor of \(c\) is positive and \(c>0\). Also \(x-k-1\in(-1,0)\). For a negative exponent \(\beta\), the map \(t\mapsto t^\beta=e^{\beta\ln t}\) is strictly decreasing on \((0,\infty)\), because \(\ln\) is increasing and \(\exp\) is increasing. Since \(\xi_n>n\), Step 4 gives
\[
0<\Delta^{k+1}f(n)=c\,\xi_n^{\,x-k-1}<c\,n^{x-k-1}.
\]
Put \(\gamma=k+1-x\in(0,1)\). Then \(c\,n^{x-k-1}=c\,n^{-\gamma}<1\) exactly when \(n^\gamma>c\), that is, when \(n>c^{1/\gamma}\). By the \PMlinkname{Archimedean property}{ArchimedeanPropertyOfTheRealNumbers}, there is a positive integer \(n>c^{1/\gamma}\). For this \(n\), the number \(\Delta^{k+1}f(n)\) satisfies \(0<\Delta^{k+1}f(n)<1\). By Step 3 it is an integer, and no integer lies strictly between \(0\) and \(1\). This contradiction shows that \(x\) is an integer, and by Step 1 it is nonnegative.
\end{proof}

If \(x\) is an integer the argument produces no contradiction, as it must: then \(x=k\), the factor \(x-k\) of \(c\) is zero, and indeed \(\Delta^{k+1}n^k=0\) for every \(n\). Conversely, if \(x\) is a nonnegative integer then \(N^x\) is an integer for every positive integer \(N\), while if \(x\) is a negative integer then \(2^x=1/2^{-x}\) is not. So the hypothesis of the theorem holds exactly when \(x\in\{0,1,2,\ldots\}\).

\begin{example}
Let \(x=\tfrac12\). Then \(1^{1/2}=1\) and \(4^{1/2}=2\) are integers, but \(2^{1/2}=\sqrt2\) is not, so the hypothesis fails at \(N=2\). The proof shows how it must fail somewhere: here \(k=0\), \(c=\tfrac12\), and for every positive integer \(n\),
\[
\Delta f(n)=\sqrt{n+1}-\sqrt n=\frac{1}{\sqrt{n+1}+\sqrt n}\in(0,1),
\]
so for every \(n\ge1\) at least one of \(\sqrt n\) and \(\sqrt{n+1}\) is not an integer.
\end{example}

\begin{remark}
The proof uses the hypothesis only at \(N=2\) in Step 1 and at the values \(N=n,n+1,\ldots,n+k+1\) for one large \(n\) in Steps 3 to 5. Hence the following stronger statement holds, with the same proof: if there is an integer \(n_0\ge1\) such that \(N^x\in\mathbb{Z}\) for every integer \(N\ge n_0\), then \(x\) is a nonnegative integer. For Step 1 any single integer \(N>1\) with \(N^x\in\mathbb{Z}\) suffices, since \(x<0\) and \(N>1\) give \(0<N^x<1\); take for instance \(N=\max(n_0,2)\). In Step 3 apply the induction to the values \(f(m)\) with \(m\ge n_0\), which gives \(\Delta^{k+1}f(n)\in\mathbb{Z}\) for every integer \(n\ge n_0\), and in Step 5 choose \(n\ge n_0\) as well as \(n>c^{1/\gamma}\).

The hypothesis cannot be reduced to a single \(N\): for example \(4^{1/2}=2\) is an integer. Much deeper results from transcendental number theory show that three values suffice: if \(2^x\), \(3^x\) and \(5^x\) are all integers, then \(x\) is an integer, by the six exponentials theorem. Whether \(2^x,3^x\in\mathbb{Z}\) alone forces \(x\in\mathbb{Z}\) is not known; it would follow from the four exponentials conjecture.
\end{remark}
""")


if __name__ == "__main__":
    run_batch(E, EXTRA_ESCAPES, __doc__)
