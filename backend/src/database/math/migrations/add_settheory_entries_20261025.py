"""Naive set theory entries: sets, set operations, ordered pairs and products, relation
properties, total orders, partitions, and functions (built from binary relations).

Nineteen entries in the order they were published. Related
links and explicit links point only to earlier entries or existing ones. Published on
2026-10-25 with helper option 20 (batch settheory).
"""
from math_entry_batch import run_batch

HAMMACK = ("R. Hammack", "Book of Proof, 3rd edition",
           "https://richardhammack.github.io/BookOfProof/")

# Escapes added to every entry on top of the standard migration list, minus the words
# this batch wants linked (KEEP_LINKED).
EXTRA_ESCAPES = ["algebra", "theory", "assumption", "length", "nor", "information", "similar",
                 "instance", "model", "language", "top", "type", "square", "complete",
                 # Wrong targets found in the preview (2026-10-25).
                 "ambiguous", "arithmetic", "context", "object", "congruence", "block", "blocks",
                 "left inverse", "right inverse", "left inverses", "right inverses", "plane",
                 "projection", "projections", "labelling", "logic", "interval", "Archimedean",
                 "archimedean", "circle", "restriction", "useful", "rectangle"]
# Escapes needed in one entry only. An entry's own synonyms resolve to OTHER entries in its
# own text (self links are skipped), so the words that older entries also define are escaped
# where this entry is the right target.
ENTRY_ESCAPES = {
    "set-operations": ["union", "unions", "disjoint union"],
    "reflexive": ["reflexive", "composition"],
    "symmetric-relation": ["symmetric", "composition"],
    "transitive-relation": ["transitive", "composition"],
    "antisymmetric-relation": ["composition"],
    "image": ["image", "inverse image"],
    "injective-function": ["injective"],
    "surjective-function": ["surjective"],
    "bijective-function": ["bijective"],
}

# Words of the standard escape list that this batch defines and wants linked.
KEEP_LINKED = {"function", "map", "image", "union", "disjoint union", "total", "partial", "bijective",
               "range", "chain", "composition", "partition"}

E = []


def entry(title, slug, codes, synonyms, definitions, related, body, ref=HAMMACK, types=None):
    E.append(dict(title=title, slug=slug, classifications=codes, synonyms=synonyms,
                  definitions=definitions, related=related, body=body, reference=ref,
                  types=types))

# Part 1 of the naive set theory entries: entries 1 (naive set theory), 2 (ordered pair),
# 3 (Cartesian product), in global order.
#
# Ordinary English words in these bodies that might be mis-autolinked to unrelated entries:
# element, member, class, property, universe, primitive, order, ordered, pair, coordinate,
# component, first, second, product, square, power, plane, line, row, point, list, listing,
# finite, number, induction, natural, integer, real, union, intersection, difference,
# complement, distributive, distributivity, associative, commutative, correspondence,
# identify, condition, statement, case, contradiction, reflexive, transitive, empty,
# notation, theory, paradox, diagram, construction, length.
#
# Notes for the assembler / reviewer:
# - "reflexive", "transitive" (entry 1) and "union", "intersection", "difference", "power set",
#   "one-to-one correspondence" (entry 3) appear as plain words only; they will autolink to the
#   later entries 4, 5, 7, 16 once those exist. No explicit link points forward.
# - Entry 1 uses "functions" only twice, in passing (first sentence; "sets of functions" in the
#   last remark), never in a defining role; these will autolink to entry 11.
# - Entries 1-3 contain no thebibliography and no ref= argument (the assembler adds references).


entry("naive set theory", "naive-set-theory", ["03E99", "03-01"],
      [],
      ["subset", "subsets", "proper subset", "empty set", "singleton", "unordered pair",
       "set-builder notation", "extensionality"],
      ["russells-paradox", "venn-diagram"], r"""
Almost every object studied in mathematics can be described as a set, so a small stock of conventions about sets, their elements and their subsets underlies all of the other entries on relations, orders and functions.

In naive set theory the notions of \textit{set} and of \textit{element} are not defined; they are primitive. For an object \(x\) and a set \(A\) we write \(x\in A\) if \(x\) is an element (or member) of \(A\), and \(x\notin A\) otherwise. The elements of a set may themselves be sets. The only thing that matters about a set is which objects are its elements, and this is made precise by the following principle.

\begin{definition}
The principle of \emph{extensionality} states that two sets \(A\) and \(B\) are equal if and only if they have the same elements, that is,
\[
A=B \quad\Longleftrightarrow\quad \text{for every } x,\ (x\in A \iff x\in B).
\]
\end{definition}

\begin{definition}
Let \(A\) and \(B\) be sets.
\begin{enumerate}
\item \(A\) is a \emph{subset} of \(B\), written \(A\subseteq B\) (or \(B\supseteq A\)), if every element of \(A\) is an element of \(B\).
\item \(A\) is a \emph{proper subset} of \(B\), written \(A\subsetneq B\), if \(A\subseteq B\) and \(A\ne B\).
\item An \emph{empty set} is a set that has no elements. We take for granted that such a set exists; it is unique by the proposition below, and it is denoted \(\varnothing\).
\end{enumerate}
\end{definition}

Note the difference between \(\in\) and \(\subseteq\): \(x\in A\) says that \(x\) is one of the elements of \(A\), while \(S\subseteq A\) says that all elements of the set \(S\) are elements of \(A\).

\begin{definition}
For objects \(a_1,\dots,a_n\), the set \(\{a_1,\dots,a_n\}\) is the set whose elements are exactly \(a_1,\dots,a_n\):
\[
x\in\{a_1,\dots,a_n\} \quad\Longleftrightarrow\quad x=a_1 \text{ or } x=a_2 \text{ or } \dots \text{ or } x=a_n.
\]
In particular, for objects \(a\) and \(b\), the set \(\{a\}\), whose only element is \(a\), is called a \emph{singleton}, and the set \(\{a,b\}\), whose elements are exactly \(a\) and \(b\), is called the \emph{unordered pair} of \(a\) and \(b\).
\end{definition}

By extensionality, a set given by a list depends neither on the order in which the elements are listed nor on repetitions. For instance \(\{a,a,b\}=\{b,a\}\): for every \(x\),
\[
x\in\{a,a,b\} \iff (x=a \text{ or } x=a \text{ or } x=b) \iff (x=b \text{ or } x=a) \iff x\in\{b,a\}.
\]
In the same way \(\{a,a\}=\{a\}\), so the unordered pair \(\{a,b\}\) is a singleton when \(a=b\).

\begin{definition}
Let \(A\) be a set and let \(P(x)\) be a statement about an object \(x\) (a property). The set
\[
\{x\in A\mid P(x)\}
\]
is the set of those elements \(x\) of \(A\) for which \(P(x)\) is true; thus \(y\in\{x\in A\mid P(x)\}\) if and only if \(y\in A\) and \(P(y)\) holds. This way of describing a set is called \emph{set-builder notation}. The set it describes is always a subset of \(A\).
\end{definition}

One also writes \(\{t(x)\mid x\in A\}\) for the set of all objects of the form \(t(x)\) with \(x\in A\), where \(t(x)\) is an expression in \(x\); for example \(\{2k\mid k\in\mathbb{Z}\}\) is the set of even integers.

Set-builder notation always selects elements from a given set \(A\). The unrestricted form \(\{x\mid P(x)\}\), the collection of all objects whatsoever with property \(P\), cannot be allowed for every property, as the remark on Russell's paradox below explains.

\begin{proposition}
Let \(A\), \(B\) and \(C\) be sets.
\begin{enumerate}
\item \(A=B\) if and only if \(A\subseteq B\) and \(B\subseteq A\).
\item Inclusion is reflexive and transitive: \(A\subseteq A\), and if \(A\subseteq B\) and \(B\subseteq C\), then \(A\subseteq C\). Moreover, if \(A\subseteq B\) and \(B\subseteq A\), then \(A=B\).
\item \(A\subsetneq B\) if and only if \(A\subseteq B\) and there is an element \(b\in B\) with \(b\notin A\).
\end{enumerate}
\end{proposition}

\begin{proof}
\textit{(1)} If \(A=B\), then every element of \(A\) is an element of \(B\) and conversely, so \(A\subseteq B\) and \(B\subseteq A\). Conversely, suppose \(A\subseteq B\) and \(B\subseteq A\). For every \(x\), the first inclusion gives \(x\in A\Rightarrow x\in B\) and the second gives \(x\in B\Rightarrow x\in A\), so \(x\in A\iff x\in B\). By extensionality \(A=B\).

\textit{(2)} Every element of \(A\) is an element of \(A\), so \(A\subseteq A\). If \(A\subseteq B\subseteq C\) and \(x\in A\), then \(x\in B\) because \(A\subseteq B\), and then \(x\in C\) because \(B\subseteq C\); hence \(A\subseteq C\). The last statement is the ``if'' part of (1).

\textit{(3)} Suppose \(A\subsetneq B\). Then \(A\subseteq B\) and \(A\ne B\), so by (1) \(B\subseteq A\) fails; that is, some \(b\in B\) satisfies \(b\notin A\). Conversely, if \(A\subseteq B\) and \(b\in B\), \(b\notin A\), then \(A\) and \(B\) do not have the same elements, so \(A\ne B\) by extensionality, and \(A\subsetneq B\).
\end{proof}

Part (1) is the usual way to prove that two sets are equal: one shows each inclusion separately, by taking an arbitrary element of one set and showing that it lies in the other.

\begin{proposition}
\begin{enumerate}
\item The empty set is a subset of every set: \(\varnothing\subseteq A\) for every set \(A\).
\item There is only one empty set: if \(E\) and \(E'\) are sets without elements, then \(E=E'\).
\item For every set \(A\), \(A\subseteq\varnothing\) if and only if \(A=\varnothing\).
\end{enumerate}
\end{proposition}

\begin{proof}
\textit{(1)} We must show that every \(x\) with \(x\in\varnothing\) satisfies \(x\in A\). Since no \(x\) satisfies \(x\in\varnothing\), there is nothing to check: the implication \(x\in\varnothing\Rightarrow x\in A\) has a false hypothesis for every \(x\), and so it is true.

\textit{(2)} The argument of (1) applies to any set without elements, so \(E\subseteq E'\) and \(E'\subseteq E\). By part (1) of the previous proposition, \(E=E'\).

\textit{(3)} If \(A=\varnothing\), then \(A\subseteq\varnothing\) by reflexivity of inclusion. If \(A\subseteq\varnothing\), then also \(\varnothing\subseteq A\) by (1), so \(A=\varnothing\).
\end{proof}

\begin{proposition}
Let \(a,b,c,d\) be objects.
\begin{enumerate}
\item \(\{a\}=\{b\}\) if and only if \(a=b\).
\item \(\{a,b\}=\{c\}\) if and only if \(a=b=c\).
\item \(\{a,b\}=\{c,d\}\) if and only if either \(a=c\) and \(b=d\), or \(a=d\) and \(b=c\).
\end{enumerate}
\end{proposition}

\begin{proof}
\textit{(1)} If \(a=b\), then \(\{a\}\) and \(\{b\}\) are the same set. Conversely, if \(\{a\}=\{b\}\), then \(a\in\{a\}=\{b\}\), so \(a=b\).

\textit{(2)} If \(\{a,b\}=\{c\}\), then \(a\in\{c\}\) and \(b\in\{c\}\), so \(a=c\) and \(b=c\). Conversely, if \(a=b=c\), then \(\{a,b\}=\{c,c\}=\{c\}\), as noted after the definition of listing notation.

\textit{(3)} If \(a=c\) and \(b=d\), the two sets are the same. If \(a=d\) and \(b=c\), then for every \(x\) we have \(x\in\{a,b\}\iff(x=a\text{ or }x=b)\iff(x=d\text{ or }x=c)\iff x\in\{c,d\}\), so the sets are equal by extensionality.

Conversely, suppose \(\{a,b\}=\{c,d\}\). Since \(a\in\{c,d\}\), we have \(a=c\) or \(a=d\).

\textit{Case \(a=c\).} Since \(b\in\{c,d\}\), we have \(b=c\) or \(b=d\). If \(b=d\), then \(a=c\) and \(b=d\), as required. If \(b=c\), then \(b=c=a\), so \(\{a,b\}=\{a\}\); since \(d\in\{c,d\}=\{a\}\), we get \(d=a\). Then \(a=d\) and \(b=c\), as required.

\textit{Case \(a=d\).} Since \(b\in\{c,d\}\), we have \(b=c\) or \(b=d\). If \(b=c\), then \(a=d\) and \(b=c\), as required. If \(b=d\), then \(b=d=a\), so \(\{a,b\}=\{a\}\); since \(c\in\{c,d\}=\{a\}\), we get \(c=a\). Then \(a=c\) and \(b=d\), as required.
\end{proof}

The following consequence of restricting set-builder notation to a given set shows that no set contains every set.

\begin{proposition}
Let \(A\) be a set and let \(B=\{x\in A\mid x\notin x\}\). Then \(B\notin A\). In particular, there is no set of which every set is an element.
\end{proposition}

\begin{proof}
Suppose \(B\in A\). By the definition of \(B\), an object \(y\) belongs to \(B\) if and only if \(y\in A\) and \(y\notin y\). Taking \(y=B\) and using \(B\in A\), we get \(B\in B\iff B\notin B\), which is impossible. Hence \(B\notin A\). If some set \(A\) had every set as an element, then in particular \(B\in A\) for this \(A\), a contradiction.
\end{proof}

\begin{example}
\(\{x\in\mathbb{Z}\mid x^2=1\}=\{-1,1\}\). Indeed, if \(x\in\mathbb{Z}\) and \(x^2=1\), then \((x-1)(x+1)=x^2-1=0\), and since a product of two integers is \(0\) only when one factor is \(0\), we get \(x=1\) or \(x=-1\). Conversely \((-1)^2=1^2=1\) and \(-1,1\in\mathbb{Z}\). So both sets have the same elements. Note that \(\{x\in\mathbb{N}\mid x^2=1\}=\{1\}\), where \(\mathbb{N}=\{0,1,2,\dots\}\): the set from which the elements are selected matters.
\end{example}

\begin{example}
\(\varnothing\ne\{\varnothing\}\): the set \(\{\varnothing\}\) has an element, namely \(\varnothing\), while \(\varnothing\) has none. By part (1) of the proposition on singletons and pairs, it follows that \(\{\varnothing\}\ne\{\{\varnothing\}\}\), since \(\varnothing\ne\{\varnothing\}\). Thus \(\varnothing\), \(\{\varnothing\}\) and \(\{\{\varnothing\}\}\) are three different sets (the last two differ from \(\varnothing\) because they have an element). Also \(\varnothing\subseteq\varnothing\), but \(\varnothing\notin\varnothing\).
\end{example}

\begin{example}
Let \(X=\{\varnothing,\{\varnothing\}\}\), a set whose two elements are themselves sets; they are distinct by the previous example, so \(X\) has exactly two elements.
\begin{itemize}
\item \(\varnothing\in X\), and also \(\varnothing\subseteq X\), like for every set.
\item \(\{\varnothing\}\in X\), and also \(\{\varnothing\}\subseteq X\), because the only element of \(\{\varnothing\}\) is \(\varnothing\), which lies in \(X\).
\item \(\{\{\varnothing\}\}\subseteq X\), because its only element \(\{\varnothing\}\) lies in \(X\); but \(\{\{\varnothing\}\}\notin X\), because \(\{\{\varnothing\}\}\) is different from \(\varnothing\) and from \(\{\varnothing\}\) by the previous example.
\item \(X\) has exactly four subsets, namely \(\varnothing\), \(\{\varnothing\}\), \(\{\{\varnothing\}\}\) and \(X\). Indeed, a subset \(S\subseteq X\) is determined by extensionality by which of the two elements of \(X\) it contains, which gives these four possibilities. The proper subsets of \(X\) are the first three.
\end{itemize}
\end{example}

\begin{remark}
Without the restriction to a given set \(A\), set-builder notation leads to a contradiction. If every property \(P(x)\) determined a set \(\{x\mid P(x)\}\), we could form \(R=\{x\mid x\notin x\}\), and then \(R\in R\) if and only if \(R\notin R\). This is \PMlinkname{Russell's paradox}{RussellsParadox}. Restricting to elements of a given set avoids it: as shown above, the same construction inside a set \(A\) merely proves that the resulting set is not an element of \(A\).
\end{remark}

\begin{remark}
Relations between a few subsets of a given set are conveniently pictured by \PMlinkname{Venn diagrams}{VennDiagram}, in which the sets are drawn as overlapping regions of the plane. Such pictures help intuition but are not proofs.
\end{remark}

\begin{remark}
The word ``naive'' means that we do not list axioms from which the existence of sets is derived. Instead, we take for granted that the usual constructions produce sets: sets given by a list, subsets defined by a property (as above), unions, power sets, Cartesian products and sets of functions, together with the familiar sets of numbers. An axiomatic treatment, such as Zermelo--Fraenkel set theory, justifies each of these constructions from a short list of axioms; for the mathematics in this collection the naive point of view is sufficient.
\end{remark}
""")


entry("ordered pair", "ordered-pair", ["03E20"],
      ["ordered pairs"],
      ["Kuratowski pair", "ordered triple", "n-tuple"],
      ["naive-set-theory"], r"""
Coordinates of points in the plane, relations and functions all need pairs in which it matters which entry comes first, whereas the unordered pair \(\{a,b\}\) is the same set as \(\{b,a\}\).

We use the facts on singletons and unordered pairs proved in the entry \PMlinkname{naive set theory}{NaiveSetTheory}: \(\{a\}=\{b\}\) if and only if \(a=b\); \(\{a,b\}=\{c\}\) if and only if \(a=b=c\); and \(\{a,b\}=\{c,d\}\) if and only if either \(a=c\) and \(b=d\), or \(a=d\) and \(b=c\).

\begin{definition}
Let \(a\) and \(b\) be objects. The \emph{ordered pair} of \(a\) and \(b\) is the set
\[
(a,b)=\{\{a\},\{a,b\}\}.
\]
This is also called the \emph{Kuratowski pair}. The object \(a\) is the first coordinate (or first component) of \((a,b)\), and \(b\) is its second coordinate.
\end{definition}

For example \((a,a)=\{\{a\},\{a,a\}\}=\{\{a\},\{a\}\}=\{\{a\}\}\). The definition is designed so that the following theorem holds.

\begin{theorem}
For all objects \(a,b,c,d\),
\[
(a,b)=(c,d)\quad\Longleftrightarrow\quad a=c \text{ and } b=d.
\]
\end{theorem}

\begin{proof}
If \(a=c\) and \(b=d\), then \((a,b)\) and \((c,d)\) are the same set. Conversely, suppose that \(\{\{a\},\{a,b\}\}=\{\{c\},\{c,d\}\}\).

\textit{Case 1: \(a=b\).} Then \((a,b)=\{\{a\}\}\), as computed above, so \(\{\{c\},\{c,d\}\}=\{\{a\}\}\). By the fact on \(\{x,y\}=\{z\}\), applied to the sets \(x=\{c\}\), \(y=\{c,d\}\) and \(z=\{a\}\), we get \(\{c\}=\{a\}\) and \(\{c,d\}=\{a\}\). The first equality gives \(c=a\), and the second gives \(c=d=a\). Hence \(a=c\) and \(b=a=d\).

\textit{Case 2: \(a\ne b\).} By the fact on equal unordered pairs, applied to the elements \(\{a\},\{a,b\}\) and \(\{c\},\{c,d\}\), either
\begin{enumerate}
\item \(\{a\}=\{c\}\) and \(\{a,b\}=\{c,d\}\), or
\item \(\{a\}=\{c,d\}\) and \(\{a,b\}=\{c\}\).
\end{enumerate}
In the second alternative, \(\{a,b\}=\{c\}\) gives \(a=b=c\), contradicting \(a\ne b\). So the first alternative holds. From \(\{a\}=\{c\}\) we get \(a=c\), and then \(\{a,b\}=\{c,d\}=\{a,d\}\). Applying the fact on equal unordered pairs once more, either \(a=a\) and \(b=d\), or \(a=d\) and \(b=a\). The latter contradicts \(a\ne b\), so \(b=d\). Together with \(a=c\) this proves the claim.
\end{proof}

In particular \((a,b)\ne(b,a)\) whenever \(a\ne b\): if \((a,b)=(b,a)\), the theorem gives \(a=b\).

\begin{remark}
The theorem, called the characteristic property of ordered pairs, is the only property of \((a,b)\) used anywhere else; the particular set \(\{\{a\},\{a,b\}\}\) only serves to show that objects with this property exist. Other definitions work equally well, for example Wiener's definition \(\{\{\{a\},\varnothing\},\{\{b\}\}\}\), and any of them could be used instead. Note that an ordered pair is in general different from the unordered pair of its coordinates. For instance, with \(a=\varnothing\) and \(b=\{\varnothing\}\), we have \(\varnothing\in\{a,b\}\), whereas both elements \(\{a\}\) and \(\{a,b\}\) of \((a,b)\) are nonempty, so \(\varnothing\notin(a,b)\); hence \((a,b)\ne\{a,b\}\) by extensionality.
\end{remark}

Ordered pairs are used repeatedly to build longer finite sequences.

\begin{definition}
For objects \(a,b,c\), the \emph{ordered triple} is \((a,b,c)=((a,b),c)\). More generally, the \emph{n-tuple} \((a_1,\dots,a_n)\) is defined for \(n\ge2\) by recursion on \(n\): for \(n=2\) it is the ordered pair \((a_1,a_2)\), and for \(n\ge3\),
\[
(a_1,\dots,a_n)=((a_1,\dots,a_{n-1}),a_n).
\]
The object \(a_i\) is the \(i\)-th coordinate of the n-tuple.
\end{definition}

\begin{proposition}
Let \(n\ge2\). For all objects \(a_1,\dots,a_n\) and \(b_1,\dots,b_n\),
\[
(a_1,\dots,a_n)=(b_1,\dots,b_n)\quad\Longleftrightarrow\quad a_i=b_i \text{ for } i=1,\dots,n.
\]
\end{proposition}

\begin{proof}
We use \PMlinkname{induction}{PrincipleOfFiniteInduction} on \(n\ge2\). For \(n=2\) this is the theorem above. Let \(n\ge2\) and assume the statement for \(n\). By definition and by the theorem,
\[
(a_1,\dots,a_{n+1})=(b_1,\dots,b_{n+1})
\iff ((a_1,\dots,a_n),a_{n+1})=((b_1,\dots,b_n),b_{n+1})
\iff (a_1,\dots,a_n)=(b_1,\dots,b_n) \text{ and } a_{n+1}=b_{n+1}.
\]
By the induction hypothesis, the right-hand side holds if and only if \(a_i=b_i\) for \(i=1,\dots,n\) and \(a_{n+1}=b_{n+1}\), that is, if and only if \(a_i=b_i\) for \(i=1,\dots,n+1\). This completes the induction.
\end{proof}

\begin{remark}
The length of a tuple is not recorded in the set itself: the triple \((a,b,c)=((a,b),c)\) is also the ordered pair whose first coordinate is \((a,b)\) and whose second coordinate is \(c\). In practice the length is always clear from the context, and the proposition is applied only to tuples of the same, known length. One can also view an n-tuple \((a_1,\dots,a_n)\) as a family of objects indexed by \(\{1,\dots,n\}\), that is, as the rule assigning \(a_i\) to each index \(i\); the two points of view agree up to an obvious one-to-one correspondence, and both satisfy the property of the proposition.
\end{remark}
""")


entry("Cartesian product", "cartesian-product", ["03E20"],
      ["Cartesian products", "product of sets", "cartesian product of sets"],
      ["Cartesian square", "Cartesian power"],
      ["ordered-pair", "relation"], r"""
Pairing every element of one set with every element of another produces, for instance, the plane \(\mathbb{R}^2\) from the real line, and it provides the setting in which relations and functions are defined.

We use \PMlinkname{ordered pairs}{OrderedPair} and their characteristic property: \((a,b)=(c,d)\) if and only if \(a=c\) and \(b=d\).

\begin{definition}
Let \(A\) and \(B\) be sets. The \emph{Cartesian product} of \(A\) and \(B\) is the set of all ordered pairs whose first coordinate lies in \(A\) and whose second coordinate lies in \(B\):
\[
A\times B=\{(a,b)\mid a\in A,\ b\in B\}.
\]
Thus \(z\in A\times B\) if and only if \(z=(a,b)\) for some \(a\in A\) and \(b\in B\). The set \(A^2=A\times A\) is the \emph{Cartesian square} of \(A\). More generally, for \(n\ge2\) and sets \(A_1,\dots,A_n\), the set \(A_1\times\cdots\times A_n\) is the set of all n-tuples \((a_1,\dots,a_n)\) with \(a_i\in A_i\) for \(i=1,\dots,n\), and \(A^n=A\times\cdots\times A\) (\(n\) factors) is the \(n\)-th \emph{Cartesian power} of \(A\). One also puts \(A^1=A\).
\end{definition}

Since \((a_1,\dots,a_n)=((a_1,\dots,a_{n-1}),a_n)\) for \(n\ge3\), and \((a_1,\dots,a_{n-1})\) ranges over \(A_1\times\cdots\times A_{n-1}\) when each \(a_i\) ranges over \(A_i\), we have
\[
A_1\times\cdots\times A_n=(A_1\times\cdots\times A_{n-1})\times A_n \qquad (n\ge3).
\]

\begin{remark}
In naive set theory we take for granted that \(A\times B\) is a set, and this is justified as follows. For \(a\in A\) and \(b\in B\), the sets \(\{a\}\) and \(\{a,b\}\) are subsets of the union \(A\cup B\), so \((a,b)=\{\{a\},\{a,b\}\}\) is a set of subsets of \(A\cup B\). Hence each such pair is an element of the power set of the power set of \(A\cup B\), and \(A\times B\) is the subset of that set consisting of those elements \(z\) of the form \((a,b)\) with \(a\in A\) and \(b\in B\).
\end{remark}

In the following results, union, intersection and difference have their usual meaning: \(x\in B\cup C\) if and only if \(x\in B\) or \(x\in C\); \(x\in B\cap C\) if and only if \(x\in B\) and \(x\in C\); \(x\in B\setminus C\) if and only if \(x\in B\) and \(x\notin C\).

\begin{proposition}
Let \(A,B,C,D\) be sets.
\begin{enumerate}
\item \(A\times B=\varnothing\) if and only if \(A=\varnothing\) or \(B=\varnothing\).
\item If \(A\subseteq C\) and \(B\subseteq D\), then \(A\times B\subseteq C\times D\). Conversely, if \(A\) and \(B\) are nonempty and \(A\times B\subseteq C\times D\), then \(A\subseteq C\) and \(B\subseteq D\).
\item \(A\times B=B\times A\) if and only if \(A=B\), or \(A=\varnothing\), or \(B=\varnothing\).
\end{enumerate}
\end{proposition}

\begin{proof}
\textit{(1)} If \(A\) and \(B\) are both nonempty, choose \(a\in A\) and \(b\in B\); then \((a,b)\in A\times B\), so \(A\times B\ne\varnothing\). Conversely, if \(A=\varnothing\), there is no \(a\in A\), so no element of the form \((a,b)\) with \(a\in A\) exists and \(A\times B=\varnothing\); the case \(B=\varnothing\) is the same.

\textit{(2)} Suppose \(A\subseteq C\) and \(B\subseteq D\). If \(z\in A\times B\), then \(z=(a,b)\) with \(a\in A\subseteq C\) and \(b\in B\subseteq D\), so \(z\in C\times D\).

Now let \(A,B\) be nonempty with \(A\times B\subseteq C\times D\). Let \(a\in A\), and choose some \(b\in B\). Then \((a,b)\in C\times D\), so \((a,b)=(c,d)\) for some \(c\in C\) and \(d\in D\). By the characteristic property, \(a=c\in C\). Hence \(A\subseteq C\). Exchanging the roles of the two coordinates (choose \(a\in A\) and let \(b\in B\) be arbitrary) gives \(B\subseteq D\).

\textit{(3)} If \(A=B\), the two products are the same set. If \(A=\varnothing\) or \(B=\varnothing\), both products are empty by (1). Conversely, suppose \(A\times B=B\times A\), and suppose \(A\) and \(B\) are both nonempty. From \(A\times B\subseteq B\times A\) and (2) we get \(A\subseteq B\) and \(B\subseteq A\), so \(A=B\).
\end{proof}

The hypothesis that \(A\) and \(B\) are nonempty in the second part of (2) is needed: for \(A=\varnothing\), \(B=\{0\}\) and \(C=D=\varnothing\), both \(A\times B\) and \(C\times D\) are empty by (1), so \(A\times B\subseteq C\times D\), but \(B\not\subseteq D\).

\begin{proposition}
Let \(A,B,C,D\) be sets. Then
\begin{align*}
A\times(B\cup C)&=(A\times B)\cup(A\times C),\\
A\times(B\cap C)&=(A\times B)\cap(A\times C),\\
A\times(B\setminus C)&=(A\times B)\setminus(A\times C),\\
(A\times B)\cap(C\times D)&=(A\cap C)\times(B\cap D),
\end{align*}
and
\[
(A\times B)\cup(C\times D)\subseteq(A\cup C)\times(B\cup D).
\]
The same distributive laws hold with the product taken on the other side, for instance \((B\cup C)\times A=(B\times A)\cup(C\times A)\).
\end{proposition}

\begin{proof}
\textit{Union.} Let \(z\in A\times(B\cup C)\). Then \(z=(a,x)\) with \(a\in A\) and \(x\in B\cup C\). If \(x\in B\), then \(z\in A\times B\); if \(x\in C\), then \(z\in A\times C\). Either way \(z\in(A\times B)\cup(A\times C)\). Conversely, \(B\subseteq B\cup C\) and \(C\subseteq B\cup C\), so \(A\times B\) and \(A\times C\) are subsets of \(A\times(B\cup C)\) by part (2) of the previous proposition, and therefore so is their union.

\textit{Intersection.} Since \(B\cap C\subseteq B\) and \(B\cap C\subseteq C\), the previous proposition gives \(A\times(B\cap C)\subseteq(A\times B)\cap(A\times C)\). Conversely, let \(z\in(A\times B)\cap(A\times C)\). Then \(z=(a,b)\) with \(a\in A\), \(b\in B\), and also \(z=(a',c)\) with \(a'\in A\), \(c\in C\). By the characteristic property, \(a=a'\) and \(b=c\). Hence \(b\in B\cap C\), and \(z=(a,b)\in A\times(B\cap C)\).

\textit{Difference.} Let \(z\in A\times(B\setminus C)\), so \(z=(a,x)\) with \(a\in A\), \(x\in B\) and \(x\notin C\). Then \(z\in A\times B\). If we had \(z\in A\times C\), then \(z=(a',c)\) with \(c\in C\), and the characteristic property would give \(x=c\in C\), a contradiction. Hence \(z\in(A\times B)\setminus(A\times C)\). Conversely, let \(z\in(A\times B)\setminus(A\times C)\), so \(z=(a,b)\) with \(a\in A\), \(b\in B\). If \(b\in C\), then \(z\in A\times C\), which is not the case; so \(b\in B\setminus C\), and \(z\in A\times(B\setminus C)\).

\textit{Intersection of two products.} If \(z\in(A\cap C)\times(B\cap D)\), then \(z=(x,y)\) with \(x\in A\cap C\) and \(y\in B\cap D\), so \(z\in A\times B\) and \(z\in C\times D\). Conversely, if \(z\in(A\times B)\cap(C\times D)\), then \(z=(a,b)=(c,d)\) with \(a\in A\), \(b\in B\), \(c\in C\), \(d\in D\). By the characteristic property \(a=c\) and \(b=d\), so \(a\in A\cap C\), \(b\in B\cap D\), and \(z\in(A\cap C)\times(B\cap D)\).

\textit{Union of two products.} Since \(A\subseteq A\cup C\) and \(B\subseteq B\cup D\), the previous proposition gives \(A\times B\subseteq(A\cup C)\times(B\cup D)\), and likewise \(C\times D\subseteq(A\cup C)\times(B\cup D)\); hence their union is contained in \((A\cup C)\times(B\cup D)\).

\textit{Other side.} The proofs of the laws with the product on the other side are the same, with the two coordinates exchanged.
\end{proof}

The last inclusion can be strict. Take \(A=B=\{0\}\) and \(C=D=\{1\}\). Then \((A\times B)\cup(C\times D)=\{(0,0),(1,1)\}\), while \((A\cup C)\times(B\cup D)=\{0,1\}^2\) contains \((0,1)\). The pair \((0,1)\) equals neither \((0,0)\) nor \((1,1)\), since by the characteristic property this would require \(1=0\) or \(0=1\).

\begin{proposition}
Let \(A\) be a finite set with \(m\) elements and \(B\) a finite set with \(n\) elements. Then \(A\times B\) has exactly \(mn\) elements.
\end{proposition}

\begin{proof}
If \(m=0\) or \(n=0\), then \(A\times B=\varnothing\) by part (1) of the first proposition, and \(mn=0\). Otherwise write \(A=\{a_1,\dots,a_m\}\) and \(B=\{b_1,\dots,b_n\}\) with the \(a_i\) pairwise distinct and the \(b_j\) pairwise distinct. Every element of \(A\times B\) is one of the \(mn\) pairs \((a_i,b_j)\), \(1\le i\le m\), \(1\le j\le n\), and each of these pairs lies in \(A\times B\). These pairs are pairwise distinct: if \((a_i,b_j)=(a_k,b_l)\), then \(a_i=a_k\) and \(b_j=b_l\) by the characteristic property, hence \(i=k\) and \(j=l\). So \(A\times B\) has exactly \(mn\) elements.

In other words, \(A\times B\) is the union of the \(m\) sets \(\{a_i\}\times B=\{(a_i,b_1),\dots,(a_i,b_n)\}\), the ``rows'' of the product; each row has \(n\) elements, and two different rows have no element in common, because their elements have different first coordinates.
\end{proof}

\begin{example}
Let \(x\) and \(y\) be two distinct objects, both different from \(1\) and \(2\). Then
\[
\{1,2\}\times\{x,y\}=\{(1,x),(1,y),(2,x),(2,y)\},
\]
a set with \(2\cdot2=4\) elements, while \(\{x,y\}\times\{1,2\}=\{(x,1),(x,2),(y,1),(y,2)\}\). These two products are different: \((1,x)\) lies in the first, but not in the second, since \((1,x)=(u,v)\) with \(u\in\{x,y\}\) would force \(1=x\) or \(1=y\). This agrees with part (3) of the first proposition.
\end{example}

\begin{example}
The Cartesian square \(\mathbb{R}^2=\mathbb{R}\times\mathbb{R}\) is the set of pairs \((x,y)\) of real numbers, which is the usual model of the plane: \(x\) and \(y\) are the coordinates of the point \((x,y)\), and by the characteristic property two points are equal exactly when both of their coordinates agree. Similarly \(\mathbb{R}^3\) is the set of triples \((x,y,z)\) of real numbers, a model of space. For \(a\le b\) and \(c\le d\), the product \([a,b]\times[c,d]\) of two closed intervals is a closed rectangle in the plane.
\end{example}

\begin{remark}
A binary \PMlinkname{relation}{Relation} from \(A\) to \(B\) is by definition a subset of \(A\times B\), and a relation on \(A\) is a subset of \(A^2\). Functions from \(A\) to \(B\) are described by their graphs, which are also subsets of \(A\times B\).
\end{remark}

\begin{remark}
The Cartesian product is not associative in the strict sense: the elements of \((A\times B)\times C\) are pairs \(((a,b),c)\), while those of \(A\times(B\times C)\) are pairs \((a,(b,c))\), and these sets can differ. For example, let \(A=B=C=\{\varnothing\}\). The only element of \((A\times B)\times C\) is \(((\varnothing,\varnothing),\varnothing)\), and the only element of \(A\times(B\times C)\) is \((\varnothing,(\varnothing,\varnothing))\). If these were equal, the characteristic property would give \((\varnothing,\varnothing)=\varnothing\), which is false because \((\varnothing,\varnothing)=\{\{\varnothing\}\}\) has an element. However, by the characteristic property, \(((a,b),c)=((a',b'),c')\) if and only if \(a=a'\), \(b=b'\) and \(c=c'\), and the same holds for \((a,(b,c))\); so matching \(((a,b),c)\) with \((a,(b,c))\) is a one-to-one correspondence between the two sets. One therefore usually identifies them, and both with \(A\times B\times C\), which by our definition equals \((A\times B)\times C\). Similarly, \(A\times B\) and \(B\times A\) are matched one-to-one by \((a,b)\leftrightarrow(b,a)\), although they are equal only in the cases described in part (3) of the first proposition.
\end{remark}
""")

# Part 2 of the naive set theory entries: entries 4 (set operations) and 19 (indicator function).
#
# Ordinary English words in these bodies that might be mis-autolinked to unrelated entries:
# set, element, member, universe (used for "ambient set", not a Grothendieck universe), law,
# laws, commutative, associative, idempotence, absorption, distributive, distributivity,
# complement, power, pair, product, sum, value, values, constant, identity, inverse, image,
# finite, even, odd, remainder, induction, collection, condition, case, table, diagram,
# characteristic (in "characteristic function" of probability theory), distribution, transform,
# convex, predicate, representing, membership, counting, choice, bound, connective(s), logic.
#
# Notes for the assembler / reviewer:
# - Entry 4 uses the words "injection" (synonym of entry 14) and "indicator function" (entry 19)
#   in plain text only; these become autolinks to LATER entries. No explicit \PMlinkname points
#   forward. If the publisher also forbids forward autolinks, escape "injections" and
#   "indicator function" in entry 4. Entry 4's last two remarks also use "function(s)" (entry 11),
#   "least upper bound" and "greatest lower bound" (may match order-theory/analysis entries).
# - Entry 4's text says "complement" and "intersection" in the intended senses, so they autolink
#   to the existing Complement and Intersection entries, as wanted.
# - Entry 19 uses the phrase "characteristic function" in the probability remark; it is this
#   entry's own synonym, so it is not linked there.


entry("set operations", "set-operations", ["03E20"],
      ["union", "unions", "set difference", "disjoint union", "power set", "powerset",
       "union of sets", "set operation"],
      ["pairwise disjoint", "disjoint sets", "power set of a set"],
      ["naive-set-theory", "cartesian-product", "intersection", "complement",
       "symmetric-difference"], r"""
Almost every construction in mathematics produces new sets from given ones by a small number of basic operations: taking the elements common to two sets, putting the elements of two sets together, removing the elements of one set from another, and collecting all subsets of a set.

We work in \PMlinkname{naive set theory}{NaiveSetTheory}: sets and membership are primitive, two sets are equal when they have the same elements (extensionality), and we take for granted that the constructions below produce sets.

\begin{definition}
Let \(A\) and \(B\) be sets, and let \(\mathcal{S}\) be a set whose elements are sets.
\begin{enumerate}
\item The \emph{union} of \(A\) and \(B\) is \(A\cup B=\{x\mid x\in A \text{ or } x\in B\}\). The union of \(\mathcal{S}\) is
\[
\bigcup\mathcal{S}=\{x\mid x\in S \text{ for some } S\in\mathcal{S}\}.
\]
Thus \(A\cup B=\bigcup\{A,B\}\), and \(\bigcup\varnothing=\varnothing\), since no \(x\) belongs to some member of the empty set.
\item The \emph{intersection} of \(A\) and \(B\) is \(A\cap B=\{x\in A\mid x\in B\}\). If \(\mathcal{S}\neq\varnothing\), the intersection of \(\mathcal{S}\) is
\[
\bigcap\mathcal{S}=\{x\in S_0\mid x\in S \text{ for all } S\in\mathcal{S}\},
\]
where \(S_0\) is any member of \(\mathcal{S}\); the result does not depend on the choice of \(S_0\), since an element lying in every member of \(\mathcal{S}\) lies in each particular one. Thus \(A\cap B=\bigcap\{A,B\}\).
\item Two sets \(A\) and \(B\) are \emph{disjoint sets} (or simply disjoint) if \(A\cap B=\varnothing\). A set \(\mathcal{S}\) of sets is \emph{pairwise disjoint} if any two distinct members of \(\mathcal{S}\) are disjoint.
\item The \emph{set difference} of \(A\) and \(B\) is \(A\setminus B=\{x\in A\mid x\notin B\}\); it is also called the complement of \(B\) in \(A\). Here \(B\) need not be a subset of \(A\).
\item Fix a set \(X\), the ambient set (or universe) of the discussion. For \(A\subseteq X\), the \emph{complement} of \(A\) in \(X\) is \(A^{\complement}=X\setminus A\).
\item The \emph{symmetric difference} of \(A\) and \(B\) is \(A\triangle B=(A\setminus B)\cup(B\setminus A)\).
\item The \emph{disjoint union} of \(A\) and \(B\) is
\[
A\sqcup B=(A\times\{0\})\cup(B\times\{1\}).
\]
It comes with two injections: the rule sending \(a\in A\) to \((a,0)\), and the rule sending \(b\in B\) to \((b,1)\).
\item The \emph{power set} of \(X\), or \emph{power set of a set} \(X\), is the set \(\mathcal{P}(X)=\{S\mid S\subseteq X\}\) of all subsets of \(X\).
\end{enumerate}
\end{definition}

The intersection of a set of sets is defined only for \(\mathcal{S}\neq\varnothing\). For \(\mathcal{S}=\varnothing\) the condition ``\(x\in S\) for all \(S\in\mathcal{S}\)'' holds vacuously for every \(x\), and there is no set \(S_0\) to restrict to; the collection of all \(x\) is not a set (compare \PMlinkname{Russell's paradox}{RussellsParadox}). When all sets under consideration are subsets of a fixed ambient set \(X\), one sets \(\bigcap\varnothing=X\) by convention. For more on intersections see the entry \PMlinkname{intersection}{Intersection}; for complements, \PMlinkname{complement}{Complement}; for symmetric differences, \PMlinkname{symmetric difference}{SymmetricDifference}. Pictures of these operations are given by \PMlinkname{Venn diagrams}{VennDiagram}.

In every proof below, an equality \(E=F\) of sets is proved by extensionality, that is, by showing that \(x\in E\) if and only if \(x\in F\) for every \(x\), or by proving \(E\subseteq F\) and \(F\subseteq E\).

\begin{theorem}
\textit{(Laws for union and intersection.)} For all sets \(A\), \(B\), \(C\):
\begin{enumerate}
\item \(A\cap B\subseteq A\subseteq A\cup B\);
\item (commutativity) \(A\cup B=B\cup A\) and \(A\cap B=B\cap A\);
\item (associativity) \((A\cup B)\cup C=A\cup(B\cup C)\) and \((A\cap B)\cap C=A\cap(B\cap C)\);
\item (idempotence) \(A\cup A=A\) and \(A\cap A=A\);
\item \(A\cup\varnothing=A\) and \(A\cap\varnothing=\varnothing\);
\item (absorption) \(A\cup(A\cap B)=A\) and \(A\cap(A\cup B)=A\);
\item (distributivity) \(A\cap(B\cup C)=(A\cap B)\cup(A\cap C)\) and \(A\cup(B\cap C)=(A\cup B)\cap(A\cup C)\);
\item \(A\subseteq B\) if and only if \(A\cup B=B\), if and only if \(A\cap B=A\).
\end{enumerate}
\end{theorem}

\begin{proof}
\textit{(1)} An element of \(A\cap B\) is in particular an element of \(A\), and an element of \(A\) satisfies ``\(x\in A\) or \(x\in B\)''.

\textit{(2)} For every \(x\): \(x\in A\cup B\) iff (\(x\in A\) or \(x\in B\)) iff (\(x\in B\) or \(x\in A\)) iff \(x\in B\cup A\). Likewise \(x\in A\cap B\) iff (\(x\in A\) and \(x\in B\)) iff (\(x\in B\) and \(x\in A\)) iff \(x\in B\cap A\).

\textit{(3)} For every \(x\): \(x\in(A\cup B)\cup C\) iff ((\(x\in A\) or \(x\in B\)) or \(x\in C\)) iff (\(x\in A\) or (\(x\in B\) or \(x\in C\))) iff \(x\in A\cup(B\cup C)\). The same chain with ``and'' in place of ``or'' proves the second identity.

\textit{(4)} The statements ``\(x\in A\) or \(x\in A\)'' and ``\(x\in A\) and \(x\in A\)'' are both equivalent to \(x\in A\).

\textit{(5)} Since \(x\in\varnothing\) is false for every \(x\), ``\(x\in A\) or \(x\in\varnothing\)'' is equivalent to \(x\in A\), and ``\(x\in A\) and \(x\in\varnothing\)'' is false.

\textit{(6)} By (1), \(A\subseteq A\cup(A\cap B)\). Conversely, if \(x\in A\cup(A\cap B)\), then \(x\in A\) or \(x\in A\cap B\), and in the second case also \(x\in A\); so \(A\cup(A\cap B)\subseteq A\). For the second identity, \(A\cap(A\cup B)\subseteq A\) by (1); conversely, if \(x\in A\), then \(x\in A\cup B\) by (1), so \(x\in A\cap(A\cup B)\).

\textit{(7)} First identity. Let \(x\in A\cap(B\cup C)\). Then \(x\in A\), and \(x\in B\) or \(x\in C\). If \(x\in B\), then \(x\in A\cap B\); otherwise \(x\in C\) and \(x\in A\cap C\). In both cases \(x\in(A\cap B)\cup(A\cap C)\). Conversely, if \(x\in A\cap B\), then \(x\in A\) and \(x\in B\subseteq B\cup C\), so \(x\in A\cap(B\cup C)\); the case \(x\in A\cap C\) is the same with \(C\) in place of \(B\).

Second identity. Let \(x\in A\cup(B\cap C)\). If \(x\in A\), then \(x\in A\cup B\) and \(x\in A\cup C\). If \(x\in B\cap C\), then \(x\in B\subseteq A\cup B\) and \(x\in C\subseteq A\cup C\). In both cases \(x\in(A\cup B)\cap(A\cup C)\). Conversely, let \(x\in(A\cup B)\cap(A\cup C)\). If \(x\in A\), then \(x\in A\cup(B\cap C)\). If \(x\notin A\), then \(x\in A\cup B\) forces \(x\in B\), and \(x\in A\cup C\) forces \(x\in C\); so \(x\in B\cap C\subseteq A\cup(B\cap C)\).

\textit{(8)} Suppose \(A\subseteq B\). Then \(A\cup B\subseteq B\), because an element of \(A\cup B\) lies in \(A\) or in \(B\), and in both cases in \(B\); together with \(B\subseteq A\cup B\) from (1), \(A\cup B=B\). Next, if \(A\cup B=B\), then \(A\cap B=A\cap(A\cup B)=A\) by (6). Finally, if \(A\cap B=A\), then \(A=A\cap B\subseteq B\) by (1).
\end{proof}

\begin{theorem}
\textit{(Laws for differences and complements.)} Let \(A\), \(B\), \(C\) be sets.
\begin{enumerate}
\item (De Morgan's laws for differences)
\[
C\setminus(A\cup B)=(C\setminus A)\cap(C\setminus B),\qquad C\setminus(A\cap B)=(C\setminus A)\cup(C\setminus B).
\]
\item If \(\mathcal{S}\) is a nonempty set of sets, then
\[
C\setminus\bigcup\mathcal{S}=\bigcap\{C\setminus S\mid S\in\mathcal{S}\},\qquad C\setminus\bigcap\mathcal{S}=\bigcup\{C\setminus S\mid S\in\mathcal{S}\}.
\]
\item Let \(X\) be a set, let \(A,B\subseteq X\), and take complements in \(X\). Then
\begin{itemize}
\item \(A\cup A^{\complement}=X\) and \(A\cap A^{\complement}=\varnothing\);
\item \((A^{\complement})^{\complement}=A\);
\item \(A\setminus B=A\cap B^{\complement}\);
\item \((A\cup B)^{\complement}=A^{\complement}\cap B^{\complement}\) and \((A\cap B)^{\complement}=A^{\complement}\cup B^{\complement}\);
\item \(A\subseteq B\) if and only if \(B^{\complement}\subseteq A^{\complement}\).
\end{itemize}
\end{enumerate}
\end{theorem}

\begin{proof}
\textit{(1)} For every \(x\): \(x\in C\setminus(A\cup B)\) iff \(x\in C\) and not (\(x\in A\) or \(x\in B\)), iff \(x\in C\) and \(x\notin A\) and \(x\notin B\), iff \(x\in C\setminus A\) and \(x\in C\setminus B\). Similarly, \(x\in C\setminus(A\cap B)\) iff \(x\in C\) and not (\(x\in A\) and \(x\in B\)), iff \(x\in C\) and (\(x\notin A\) or \(x\notin B\)), iff (\(x\in C\) and \(x\notin A\)) or (\(x\in C\) and \(x\notin B\)), iff \(x\in(C\setminus A)\cup(C\setminus B)\).

\textit{(2)} The set \(\{C\setminus S\mid S\in\mathcal{S}\}\) is nonempty because \(\mathcal{S}\) is, so its intersection is defined. For every \(x\): \(x\in C\setminus\bigcup\mathcal{S}\) iff \(x\in C\) and there is no \(S\in\mathcal{S}\) with \(x\in S\), iff \(x\in C\) and \(x\notin S\) for all \(S\in\mathcal{S}\). Because \(\mathcal{S}\neq\varnothing\), the condition ``\(x\in C\)'' is equivalent to ``\(x\in C\) for all \(S\in\mathcal{S}\)'', so the last statement is equivalent to ``\(x\in C\setminus S\) for all \(S\in\mathcal{S}\)'', that is, to \(x\in\bigcap\{C\setminus S\mid S\in\mathcal{S}\}\). For the second identity: \(x\in C\setminus\bigcap\mathcal{S}\) iff \(x\in C\) and \(x\notin S\) for some \(S\in\mathcal{S}\), iff \(x\in C\setminus S\) for some \(S\in\mathcal{S}\), iff \(x\in\bigcup\{C\setminus S\mid S\in\mathcal{S}\}\).

\textit{(3)} Both \(A\) and \(A^{\complement}\) are subsets of \(X\), so \(A\cup A^{\complement}\subseteq X\); conversely, each \(x\in X\) satisfies \(x\in A\) or \(x\notin A\), that is, \(x\in A\) or \(x\in A^{\complement}\). No \(x\) satisfies both \(x\in A\) and \(x\notin A\), so \(A\cap A^{\complement}=\varnothing\).

For \(x\in X\) we have \(x\in(A^{\complement})^{\complement}\) iff \(x\notin X\setminus A\) iff \(x\in A\) (since \(x\in X\)); both sides are subsets of \(X\), so \((A^{\complement})^{\complement}=A\).

An element \(x\) lies in \(A\cap B^{\complement}\) iff \(x\in A\), \(x\in X\) and \(x\notin B\); since \(A\subseteq X\), this holds iff \(x\in A\) and \(x\notin B\), that is, iff \(x\in A\setminus B\).

The two De Morgan laws are (1) with \(C=X\).

If \(A\subseteq B\) and \(x\in B^{\complement}\), then \(x\in X\) and \(x\notin B\), hence \(x\notin A\), so \(x\in A^{\complement}\). Conversely, if \(B^{\complement}\subseteq A^{\complement}\), the implication just proved, applied to this inclusion, gives \((A^{\complement})^{\complement}\subseteq(B^{\complement})^{\complement}\), that is, \(A\subseteq B\).
\end{proof}

\begin{proposition}
For all sets \(A\) and \(B\), an element \(x\) belongs to \(A\triangle B\) if and only if it belongs to exactly one of \(A\) and \(B\). Consequently
\[
A\triangle B=(A\cup B)\setminus(A\cap B),\qquad A\triangle B=B\triangle A,\qquad A\triangle\varnothing=A,\qquad A\triangle A=\varnothing.
\]
\end{proposition}

\begin{proof}
By definition, \(x\in A\triangle B\) iff (\(x\in A\) and \(x\notin B\)) or (\(x\in B\) and \(x\notin A\)), which says exactly that \(x\) lies in one of the two sets but not in the other. Also \(x\in(A\cup B)\setminus(A\cap B)\) iff \(x\) lies in at least one of \(A\), \(B\) but not in both, which is the same condition. The condition is symmetric in \(A\) and \(B\); for \(B=\varnothing\) it reads \(x\in A\); and no \(x\) lies in exactly one of \(A\) and \(A\).
\end{proof}

Further properties of the symmetric difference, such as its associativity, are proved in the entry \PMlinkname{symmetric difference}{SymmetricDifference}.

\begin{proposition}
Let \(A\), \(B\) and \(X\) be sets.
\begin{enumerate}
\item \(\varnothing\in\mathcal{P}(X)\) and \(X\in\mathcal{P}(X)\).
\item \(A\subseteq B\) if and only if \(\mathcal{P}(A)\subseteq\mathcal{P}(B)\).
\item \(\mathcal{P}(A\cap B)=\mathcal{P}(A)\cap\mathcal{P}(B)\).
\item \(\mathcal{P}(A)\cup\mathcal{P}(B)\subseteq\mathcal{P}(A\cup B)\), and the inclusion can be strict.
\item If \(X\) has \(n\) elements, then \(\mathcal{P}(X)\) has \(2^n\) elements.
\end{enumerate}
\end{proposition}

\begin{proof}
\textit{(1)} The empty set is a subset of every set, and \(X\subseteq X\).

\textit{(2)} If \(A\subseteq B\) and \(S\in\mathcal{P}(A)\), then \(S\subseteq A\subseteq B\), so \(S\in\mathcal{P}(B)\). Conversely, if \(\mathcal{P}(A)\subseteq\mathcal{P}(B)\), then \(A\in\mathcal{P}(A)\) by (1), so \(A\in\mathcal{P}(B)\), that is, \(A\subseteq B\).

\textit{(3)} A set \(S\) is a subset of \(A\cap B\) iff every element of \(S\) lies in \(A\) and in \(B\), iff \(S\subseteq A\) and \(S\subseteq B\), iff \(S\in\mathcal{P}(A)\cap\mathcal{P}(B)\).

\textit{(4)} Since \(A\subseteq A\cup B\) and \(B\subseteq A\cup B\), (2) gives \(\mathcal{P}(A)\subseteq\mathcal{P}(A\cup B)\) and \(\mathcal{P}(B)\subseteq\mathcal{P}(A\cup B)\), hence the inclusion. For \(A=\{1\}\) and \(B=\{2\}\), the set \(\{1,2\}\) belongs to \(\mathcal{P}(A\cup B)\) but is a subset of neither \(A\) nor \(B\), so the inclusion is strict.

\textit{(5)} We use \PMlinkname{induction}{PrincipleOfFiniteInduction} on \(n\ge0\). If \(n=0\), then \(X=\varnothing\); its only subset is \(\varnothing\), since a subset of \(\varnothing\) has no elements, so \(\mathcal{P}(X)=\{\varnothing\}\) has \(1=2^0\) element. Suppose the claim holds for sets with \(n\) elements, and let \(X\) have \(n+1\) elements. Choose \(x\in X\) and put \(X'=X\setminus\{x\}\), a set with \(n\) elements. Every subset of \(X\) either does not contain \(x\) or contains \(x\), and not both, so it suffices to count the two kinds and add.
\begin{itemize}
\item The subsets of \(X\) not containing \(x\) are exactly the subsets of \(X'\); by the induction hypothesis there are \(2^n\) of them.
\item The subsets of \(X\) containing \(x\) are in one-to-one correspondence with the subsets of \(X'\), via \(S\mapsto S\setminus\{x\}\) with inverse \(T\mapsto T\cup\{x\}\). Indeed, \(S\setminus\{x\}\subseteq X'\); \(T\cup\{x\}\) is a subset of \(X\) containing \(x\); \((S\setminus\{x\})\cup\{x\}=S\) because \(x\in S\); and \((T\cup\{x\})\setminus\{x\}=T\) because \(x\notin T\). So there are also \(2^n\) of them.
\end{itemize}
Hence \(\mathcal{P}(X)\) has \(2^n+2^n=2^{n+1}\) elements.
\end{proof}

\begin{proposition}
Let \(A\) and \(B\) be sets.
\begin{enumerate}
\item \(A\times\{0\}\) and \(B\times\{1\}\) are disjoint, even when \(A=B\).
\item For \(a,a'\in A\), \((a,0)=(a',0)\) implies \(a=a'\); for \(b,b'\in B\), \((b,1)=(b',1)\) implies \(b=b'\).
\item If \(A\) has \(m\) elements and \(B\) has \(n\) elements, then \(A\sqcup B\) has \(m+n\) elements.
\end{enumerate}
\end{proposition}

\begin{proof}
\textit{(1)} An element of both sets would have the form \((a,0)=(b,1)\) with \(a\in A\), \(b\in B\). By the characteristic property of \PMlinkname{ordered pairs}{OrderedPair}, this forces \(0=1\), which is false.

\textit{(2)} By the same property, \((a,0)=(a',0)\) gives \(a=a'\), and \((b,1)=(b',1)\) gives \(b=b'\).

\textit{(3)} Every element of \(A\times\{0\}\) has the form \((a,0)\) with \(a\in A\), and by (2) distinct elements of \(A\) give distinct pairs; so the rule \(a\mapsto(a,0)\) is a one-to-one correspondence between \(A\) and \(A\times\{0\}\), and \(A\times\{0\}\) has \(m\) elements. Likewise \(B\times\{1\}\) has \(n\) elements. By (1) these two finite sets are disjoint, so their union \(A\sqcup B\) has \(m+n\) elements.
\end{proof}

Thus the disjoint union keeps a separate copy of each set even when \(A\) and \(B\) overlap. If \(A\cap B=\varnothing\), the rule sending \((a,0)\) to \(a\) and \((b,1)\) to \(b\) is a one-to-one correspondence between \(A\sqcup B\) and \(A\cup B\): every element of \(A\cup B\) is reached, and two elements of \(A\sqcup B\) cannot be sent to the same point, by (2) and because no point lies in both \(A\) and \(B\). In this case one usually identifies \(A\sqcup B\) with \(A\cup B\), and one speaks of the union of disjoint sets as a disjoint union.

\begin{example}
Let \(A=\{1,2,3\}\) and \(B=\{3,4\}\). Checking each element:
\[
A\cup B=\{1,2,3,4\},\quad A\cap B=\{3\},\quad A\setminus B=\{1,2\},\quad B\setminus A=\{4\},\quad A\triangle B=\{1,2,4\}.
\]
In the ambient set \(X=\{1,2,3,4,5\}\), \(A^{\complement}=\{4,5\}\) and \(B^{\complement}=\{1,2,5\}\), and indeed \((A\cap B)^{\complement}=\{1,2,4,5\}=A^{\complement}\cup B^{\complement}\). The power set of \(B\) is \(\mathcal{P}(B)=\{\varnothing,\{3\},\{4\},\{3,4\}\}\), with \(4=2^2\) elements. The disjoint union is
\[
A\sqcup B=\{(1,0),(2,0),(3,0),(3,1),(4,1)\},
\]
with \(5=3+2\) elements, whereas \(A\cup B\) has only \(4\), because the common element \(3\) is counted once in \(A\cup B\) but appears twice, as \((3,0)\) and \((3,1)\), in \(A\sqcup B\).
\end{example}

\begin{example}
Let \(E\) be the set of even integers and \(O\) the set of odd integers. Every integer \(k\) leaves remainder \(0\) or \(1\) on division by \(2\), so \(k\in E\) or \(k\in O\); hence \(\mathbb{Z}=E\cup O\). The sets are disjoint: if \(k=2p=2q+1\) with integers \(p,q\), then \(1=2(p-q)\), which is impossible since \(2\) does not divide \(1\). So \(\mathbb{Z}\) is the union of the disjoint sets \(E\) and \(O\), and with ambient set \(\mathbb{Z}\) we have \(E^{\complement}=O\) and \(O^{\complement}=E\). The set \(\{E,O\}\) is pairwise disjoint, while \(\{E,O,\mathbb{Z}\}\) is not, since \(E\cap\mathbb{Z}=E\neq\varnothing\).
\end{example}

\begin{remark}
The laws above are mirrored by the laws of logic: \(\cup\), \(\cap\) and complement in \(X\) correspond to ``or'', ``and'' and ``not'', which is why each proof reduces to a statement about these connectives. In the language of order theory, \(\mathcal{P}(X)\) ordered by \(\subseteq\) is a \PMlinkname{partially ordered set}{PartiallyOrderedSet} in which \(A\cup B\) is the least upper bound and \(A\cap B\) the greatest lower bound of \(A\) and \(B\): by part (1) of the first theorem \(A\cup B\) contains \(A\) and \(B\), and a set containing both \(A\) and \(B\) contains every element of \(A\cup B\); dually for \(A\cap B\).
\end{remark}

\begin{remark}
A subset \(S\) of \(X\) can be recorded by the rule that assigns \(1\) to the elements of \(S\) and \(0\) to the other elements of \(X\). This identifies \(\mathcal{P}(X)\) with the set of all functions from \(X\) to \(\{0,1\}\), and explains the alternative notation \(2^X\) for the power set; the details are in the entry on the indicator function.
\end{remark}
""")


entry("indicator function", "indicator-function", ["03E20"],
      ["characteristic function of a set", "characteristic function", "indicator functions",
       "characteristic functions"],
      [],
      ["function", "set-operations", "bijective-function"], r"""
Encoding a subset by a function with values \(0\) and \(1\) turns the operations on sets into arithmetic on numbers, which is often the simplest way to compute with sets and to count.

Throughout, \(X\) is a fixed set, and complements are taken in \(X\). The values \(0\) and \(1\) are regarded as integers, so that indicator functions can be added and multiplied pointwise.

\begin{definition}
Let \(S\subseteq X\). The \emph{indicator function} (or \emph{characteristic function}) of \(S\) is the \PMlinkname{function}{Function} \(\chi_S\colon X\to\{0,1\}\) given by
\begin{equation*}
\chi_S(x)=\begin{cases}1 & \text{if } x\in S,\\ 0 & \text{if } x\in X\setminus S.\end{cases}
\end{equation*}
\end{definition}

Other common notations are \(\mathbf{1}_S\) and \(1_S\). For functions \(f,g\colon X\to\mathbb{Z}\) we write \(f+g\), \(fg\), \(1-f\) and \(\lvert f-g\rvert\) for the functions \(x\mapsto f(x)+g(x)\), \(x\mapsto f(x)g(x)\), \(x\mapsto 1-f(x)\) and \(x\mapsto\lvert f(x)-g(x)\rvert\), and \(f\le g\) means \(f(x)\le g(x)\) for all \(x\in X\). Two functions on \(X\) with the same codomain are equal exactly when they take the same value at every point, so the identities below are proved pointwise. For the operations on sets used here see \PMlinkname{set operations}{SetOperations}.

\begin{proposition}
For all \(S,T\subseteq X\):
\begin{enumerate}
\item \(\chi_\varnothing=0\), \(\chi_X=1\), and \(\chi_S^2=\chi_S\);
\item \(\chi_{S\cap T}=\chi_S\chi_T\);
\item \(\chi_{X\setminus S}=1-\chi_S\);
\item \(\chi_{S\cup T}=\chi_S+\chi_T-\chi_S\chi_T\);
\item \(\chi_{S\triangle T}=\lvert\chi_S-\chi_T\rvert=\chi_S+\chi_T-2\chi_S\chi_T\); in particular \(\chi_{S\triangle T}(x)\equiv\chi_S(x)+\chi_T(x)\pmod{2}\) for every \(x\in X\);
\item \(S\subseteq T\) if and only if \(\chi_S\le\chi_T\);
\item \(S=T\) if and only if \(\chi_S=\chi_T\).
\end{enumerate}
\end{proposition}

\begin{proof}
Fix \(x\in X\) and write \(s=\chi_S(x)\) and \(t=\chi_T(x)\); both lie in \(\{0,1\}\), and \(s=1\) iff \(x\in S\), \(t=1\) iff \(x\in T\).

\textit{(1)} No \(x\) lies in \(\varnothing\) and every \(x\in X\) lies in \(X\). Since \(s\in\{0,1\}\), \(s^2=s\).

\textit{(2)} The product \(st\) lies in \(\{0,1\}\), and \(st=1\) iff \(s=t=1\), iff \(x\in S\) and \(x\in T\), iff \(x\in S\cap T\). So \(st=\chi_{S\cap T}(x)\).

\textit{(3)} The number \(1-s\) lies in \(\{0,1\}\), and \(1-s=1\) iff \(s=0\), iff \(x\notin S\), iff \(x\in X\setminus S\).

\textit{(4)} By De Morgan's law, \(S\cup T=X\setminus\bigl((X\setminus S)\cap(X\setminus T)\bigr)\). Applying (3), then (2), then (3) again,
\[
\chi_{S\cup T}(x)=1-(1-s)(1-t)=s+t-st.
\]

\textit{(5)} The element \(x\) lies in \(S\triangle T\) iff it lies in exactly one of \(S\) and \(T\), iff \(s\neq t\). Since \(s,t\in\{0,1\}\), the number \(\lvert s-t\rvert\) lies in \(\{0,1\}\) and equals \(1\) iff \(s\neq t\); so \(\chi_{S\triangle T}(x)=\lvert s-t\rvert\). Moreover \(\lvert s-t\rvert=(s-t)^2=s^2-2st+t^2=s+t-2st\), using \(s^2=s\) and \(t^2=t\). Finally \(s+t-2st\equiv s+t\pmod 2\).

\textit{(6)} Suppose \(S\subseteq T\). If \(s=1\), then \(x\in S\subseteq T\), so \(t=1\ge s\); if \(s=0\), then \(s\le t\) because \(t\ge0\). Conversely, suppose \(\chi_S\le\chi_T\) and let \(x\in S\). Then \(1=s\le t\le1\), so \(t=1\) and \(x\in T\).

\textit{(7)} If \(S=T\), then clearly \(\chi_S=\chi_T\). If \(\chi_S=\chi_T\), then \(\chi_S\le\chi_T\) and \(\chi_T\le\chi_S\), so \(S\subseteq T\) and \(T\subseteq S\) by (6), hence \(S=T\).
\end{proof}

Let \(\{0,1\}^X\) denote the set of all functions \(X\to\{0,1\}\).

\begin{theorem}
The map \(\Phi\colon\mathcal{P}(X)\to\{0,1\}^X\), \(\Phi(S)=\chi_S\), is a bijection. Its inverse is the map \(\Psi\colon\{0,1\}^X\to\mathcal{P}(X)\) given by
\[
\Psi(g)=g^{-1}(\{1\})=\{x\in X\mid g(x)=1\}.
\]
\end{theorem}

\begin{proof}
Both maps are well defined: \(\chi_S\) is a function \(X\to\{0,1\}\), and \(g^{-1}(\{1\})\) is a subset of \(X\). We show that both composites are identity functions.

\textit{\(\Psi\circ\Phi=\operatorname{id}_{\mathcal{P}(X)}\).} For \(S\subseteq X\),
\[
\Psi(\Phi(S))=\{x\in X\mid\chi_S(x)=1\}=\{x\in X\mid x\in S\}=S,
\]
where the last step uses \(S\subseteq X\).

\textit{\(\Phi\circ\Psi=\operatorname{id}_{\{0,1\}^X}\).} Let \(g\colon X\to\{0,1\}\) and put \(S=g^{-1}(\{1\})\). For \(x\in X\): if \(g(x)=1\), then \(x\in S\) and \(\chi_S(x)=1=g(x)\); if \(g(x)\neq1\), then \(g(x)=0\) because \(g\) takes only the values \(0\) and \(1\), and \(x\notin S\), so \(\chi_S(x)=0=g(x)\). Hence \(\chi_S\) and \(g\) have the same domain, the same codomain and the same values, so \(\Phi(\Psi(g))=\chi_S=g\).

A function with a two-sided inverse is a \PMlinkname{bijection}{BijectiveFunction}, so \(\Phi\) is a bijection with inverse \(\Psi\).
\end{proof}

\begin{remark}
The theorem is the reason why the power set \(\mathcal{P}(X)\) is often written \(2^X\): it is in canonical one-to-one correspondence with the set \(\{0,1\}^X\) of functions from \(X\) to a two-element set (in axiomatic set theory the number \(2\) is usually defined to be \(\{0,1\}\)). If \(X\) has \(n\) elements, then \(\{0,1\}^X\) has \(2^n\) elements, since there are two choices of value at each of the \(n\) points; as a bijection between finite sets preserves the number of elements, \(\mathcal{P}(X)\) has \(2^n\) elements, which recovers the count proved by induction in the set operations entry. Under the correspondence, intersection, complement and symmetric difference of subsets become the operations \(\chi_S\chi_T\), \(1-\chi_S\) and addition modulo \(2\), by the proposition above.
\end{remark}

\begin{example}
Let \(X=\{1,2,3,4\}\), \(S=\{1,2\}\) and \(T=\{2,3\}\). Listing the values at \(1,2,3,4\) in order, \(\chi_S\) is \((1,1,0,0)\) and \(\chi_T\) is \((0,1,1,0)\). Then \(\chi_S\chi_T\) is \((0,1,0,0)\), the indicator function of \(S\cap T=\{2\}\); \(\chi_S+\chi_T-\chi_S\chi_T\) is \((1,1,1,0)\), that of \(S\cup T=\{1,2,3\}\); \(\lvert\chi_S-\chi_T\rvert\) is \((1,0,1,0)\), that of \(S\triangle T=\{1,3\}\); and \(1-\chi_S\) is \((0,0,1,1)\), that of \(X\setminus S=\{3,4\}\).
\end{example}

\begin{example}
\textit{(Counting.)} Let \(X\) be finite and write \(\lvert S\rvert\) for the number of elements of \(S\subseteq X\). Then \(\lvert S\rvert=\sum_{x\in X}\chi_S(x)\), because the sum has one term equal to \(1\) for each \(x\in S\) and all other terms equal to \(0\). Summing the identity \(\chi_{S\cup T}=\chi_S+\chi_T-\chi_{S\cap T}\) (part (4) of the proposition, with part (2)) over \(x\in X\) gives
\[
\lvert S\cup T\rvert=\lvert S\rvert+\lvert T\rvert-\lvert S\cap T\rvert,
\]
the simplest case of the inclusion-exclusion principle.
\end{example}

\begin{remark}
The name ``characteristic function'' has other meanings. In probability theory, the characteristic function of a random variable or a probability distribution is its Fourier transform, \(t\mapsto\mathbb{E}\bigl[e^{itY}\bigr]\), which is unrelated to the notion here; for this reason probabilists say ``indicator function'' for \(\chi_S\). In convex analysis, the indicator function of a set \(S\) is often the function that is \(0\) on \(S\) and \(+\infty\) outside \(S\).
\end{remark}

\begin{remark}
In recursion theory, the characteristic function of a set \(S\subseteq\mathbb{N}\), where \(\mathbb{N}=\{0,1,2,\dots\}\), is the function \(\chi_S\colon\mathbb{N}\to\{0,1\}\) defined above, and \(S\) is called decidable (or recursive) when \(\chi_S\) is computable. Some authors, following Kleene's representing functions of predicates, use the opposite convention, with value \(0\) on \(S\) and \(1\) off \(S\); the two functions are \(\chi_S\) and \(1-\chi_S\), so the choice does not affect which sets are decidable.
\end{remark}
""")

# Part 3 of the naive set theory entries: entries 5, 6, 7, 8 (reflexive, symmetric,
# transitive, antisymmetric relation).
#
# Ordinary English words in these bodies that might be mis-autolinked to unrelated entries:
# relation, order, ordered, set, element, pair, diagonal, converse, composition, composite,
# closure, smallest, largest, union, intersection, empty, identity, inverse, product, power,
# condition, property, chain, matrix, symmetric (in "symmetric matrix", "symmetric group",
# "symmetric difference": the longer phrases should win), interior, sibling, parent, people,
# divides, divisibility, multiple, congruence, congruent, residue, successor, natural, integer,
# real, positive, superset, subset, finite, induction, step, length, path, preorder, strict,
# vacuous, vacuously, total, partial, inclusion.
#
# Notes for the assembler / reviewer:
# - "composition" is a synonym of the later entry "composition of functions"; in these four
#   entries it always means relational composition (S o R), so an autolink of "composition"
#   here goes to a closely related but not identical notion. Consider
#   \PMlinkescapeword{composition} for entries 5-8 if that is judged misleading.
# - "closure" (topological closure) and "reflexive closure"/"symmetric closure"/"transitive
#   closure" (probably defined terms of ClosureOfARelationWithRespectToAProperty) appear in
#   remarks/theorems; the longer phrases should link to the closure entry, which is intended.
# - Entry 7 proves associativity of relational composition with the convention of the spec
#   (S o R = first R, then S) because the transitive closure proof needs R^m o R^n = R^{m+n}.
# - Entry 8 defines "asymmetric relation"/"asymmetric"; no existing entry uses them that we
#   know of, but "asymmetric" might also occur in unrelated senses (asymmetric cryptography).


entry("reflexive relation", "reflexive", ["03E20", "08A02"],
      ["reflexive", "reflexive relations", "reflexivity"],
      [],
      ["naive-set-theory", "irreflexive", "relation"], r"""
Equality, the order \(\le\) on the real numbers and inclusion of sets all relate every object to itself, and reflexivity is the name of this common feature.

Throughout, a \PMlinkname{relation}{Relation} on a set \(A\) is a subset \(R\subseteq A\times A\), and \(aRb\) means \((a,b)\in R\). We write \(\Delta_A=\{(a,a)\mid a\in A\}\) for the diagonal relation on \(A\), and \(R^{-1}=\{(b,a)\mid (a,b)\in R\}\) for the \PMlinkname{converse}{OperationsOnRelations} of \(R\). For relations \(R\) and \(S\) on \(A\) we use the composite
\[
S\circ R=\{(a,c)\in A\times A\mid aRb \text{ and } bSc \text{ for some } b\in A\},
\]
``first \(R\), then \(S\)'', which agrees with the usual order \(g\circ f\) for functions (the entry on operations on relations writes composites in the opposite order).

\begin{definition}
A relation \(R\) on a set \(A\) is \emph{reflexive} (on \(A\)) if \(aRa\) for every \(a\in A\).
\end{definition}

\begin{proposition}
A relation \(R\) on \(A\) is reflexive if and only if \(\Delta_A\subseteq R\).
\end{proposition}

\begin{proof}
The elements of \(\Delta_A\) are exactly the pairs \((a,a)\) with \(a\in A\). Hence \(\Delta_A\subseteq R\) says precisely that \((a,a)\in R\), that is \(aRa\), for every \(a\in A\).
\end{proof}

Reflexivity depends on the underlying set \(A\), not only on the set of pairs \(R\). For example, \(R=\{(1,1)\}\) is a relation on \(\{1\}\) and also on \(\{1,2\}\); it is reflexive on \(\{1\}\) but not on \(\{1,2\}\), since \((2,2)\notin R\). In particular, the empty relation \(\varnothing\) on \(A\) is reflexive if and only if \(A=\varnothing\): if \(A=\varnothing\) then \(\Delta_A=\varnothing\subseteq\varnothing\), and if \(a\in A\) then \((a,a)\in\Delta_A\) but \((a,a)\notin\varnothing\).

\begin{proposition}
Let \(R\) and \(S\) be reflexive relations on \(A\), and let \(\mathcal{R}\) be a nonempty set of reflexive relations on \(A\).
\begin{enumerate}
\item Every relation \(T\) on \(A\) with \(R\subseteq T\) is reflexive.
\item The converse \(R^{-1}\) is reflexive.
\item The intersection \(\bigcap\mathcal{R}\) and the union \(\bigcup\mathcal{R}\) are reflexive.
\item The composite \(S\circ R\) is reflexive, and it contains both \(R\) and \(S\).
\end{enumerate}
\end{proposition}

\begin{proof}
\textit{(1)} \(\Delta_A\subseteq R\subseteq T\).

\textit{(2)} For \(a\in A\) we have \((a,a)\in R\), and the converse of the pair \((a,a)\) is \((a,a)\) itself, so \((a,a)\in R^{-1}\).

\textit{(3)} Each \(R'\in\mathcal{R}\) contains \(\Delta_A\), so \(\Delta_A\subseteq\bigcap\mathcal{R}\). Since \(\mathcal{R}\) is nonempty, we may choose \(R_0\in\mathcal{R}\); then \(\Delta_A\subseteq R_0\subseteq\bigcup\mathcal{R}\).

\textit{(4)} If \(aRb\), then \(bSb\) because \(S\) is reflexive, so \((a,b)\in S\circ R\) (with intermediate element \(b\)). If \(aSb\), then \(aRa\), so \((a,b)\in S\circ R\) (with intermediate element \(a\)). Thus \(R\subseteq S\circ R\) and \(S\subseteq S\circ R\), and \(S\circ R\) is reflexive by (1).
\end{proof}

The hypothesis in (3) that \(\mathcal{R}\) is nonempty is needed for the union: the union of the empty set of relations is \(\varnothing\), which is not reflexive on a nonempty \(A\). The converse of (4) fails, since a composite can be reflexive although its factors are not: on \(A=\{1,2\}\) the relation \(R=\{(1,2),(2,1)\}\) is not reflexive, but \(R\circ R=\{(1,1),(2,2)\}=\Delta_A\) is.

\begin{remark}
A relation \(R\) on \(A\) is \PMlinkname{irreflexive}{Irreflexive} if \(aRa\) holds for no \(a\in A\), that is, \(R\cap\Delta_A=\varnothing\). Irreflexive is not the negation of reflexive. If \(A\ne\varnothing\), no relation on \(A\) is both: for \(a\in A\), reflexivity requires \(aRa\) and irreflexivity forbids it. (On \(A=\varnothing\) the only relation, \(\varnothing\), is both.) The relation \(\{(1,1)\}\) on \(\{1,2\}\) is neither: it is not reflexive since \((2,2)\) is missing, and not irreflexive since it contains \((1,1)\).
\end{remark}

\begin{proposition}
Let \(R\) be a relation on \(A\). Then \(R\cup\Delta_A\) is reflexive, contains \(R\), and is contained in every reflexive relation on \(A\) that contains \(R\). In particular, \(R\) is reflexive if and only if \(R=R\cup\Delta_A\).
\end{proposition}

\begin{proof}
Clearly \(\Delta_A\subseteq R\cup\Delta_A\) and \(R\subseteq R\cup\Delta_A\). If \(T\) is reflexive and \(R\subseteq T\), then \(\Delta_A\subseteq T\) as well, so \(R\cup\Delta_A\subseteq T\). Finally, \(R=R\cup\Delta_A\) holds if and only if \(\Delta_A\subseteq R\), which is reflexivity.
\end{proof}

The relation \(R\cup\Delta_A\) is therefore the smallest reflexive relation on \(A\) containing \(R\); it is called the reflexive closure of \(R\). See \PMlinkname{closure of a relation with respect to a property}{ClosureOfARelationWithRespectToAProperty} for the general notion.

\begin{example}
The following relations are reflexive.
\begin{itemize}
\item Equality on any set \(A\); as a set of pairs it is \(\Delta_A\) itself.
\item The order \(\le\) on \(\mathbb{N}\), \(\mathbb{Z}\), \(\mathbb{Q}\) or \(\mathbb{R}\), since \(a\le a\).
\item Divisibility on \(\mathbb{Z}\) (and on \(\mathbb{N}=\{0,1,2,\dots\}\)): \(a\mid b\) means \(b=ac\) for some integer \(c\), and \(a=a\cdot 1\). Note that \(0\mid 0\), since \(0=0\cdot 1\).
\item Inclusion \(\subseteq\) on the power set \(\mathcal{P}(X)\) of a set \(X\), since every set is a subset of itself.
\item Congruence modulo a positive integer \(n\) on \(\mathbb{Z}\), where \(a\equiv b \pmod n\) means \(n\mid b-a\): we have \(a-a=0=n\cdot 0\).
\item The full relation \(A\times A\), which contains \(\Delta_A\).
\end{itemize}
\end{example}

\begin{example}
The following relations are not reflexive.
\begin{itemize}
\item The strict order \(<\) on \(\mathbb{R}\) (or on any nonempty set of numbers): \(a<a\) is false. It is irreflexive.
\item ``Is a sibling of'' on a nonempty set of people, where \(x\) is a sibling of \(y\) if \(x\ne y\) and \(x\) and \(y\) have the same mother and the same father: by definition nobody is a sibling of himself or herself, so this relation is irreflexive.
\item The empty relation on a nonempty set, as shown above.
\item The relation \(R=\{(x,y)\in\mathbb{R}\times\mathbb{R}\mid xy>0\}\) on \(\mathbb{R}\) is neither reflexive nor irreflexive: \(1\cdot 1>0\) gives \(1R1\), while \(0\cdot 0=0\) shows that \((0,0)\notin R\).
\end{itemize}
\end{example}
""")


entry("symmetric relation", "symmetric-relation", ["03E20", "08A02"],
      ["symmetric", "symmetric relations", "symmetry of a relation"],
      [],
      ["reflexive", "relation"], r"""
Some relations, such as equality or ``is a sibling of'', make no distinction between the two objects they relate, and symmetry is the property that captures this.

A relation on a set \(A\) is a subset \(R\subseteq A\times A\), and \(aRb\) means \((a,b)\in R\). We write \(R^{-1}=\{(b,a)\mid(a,b)\in R\}\) for the \PMlinkname{converse}{OperationsOnRelations} of \(R\), \(\Delta_A=\{(a,a)\mid a\in A\}\) for the diagonal, and, for relations \(R\) and \(S\) on \(A\),
\[
S\circ R=\{(a,c)\in A\times A\mid aRb \text{ and } bSc \text{ for some } b\in A\}
\]
(``first \(R\), then \(S\)'', matching \(g\circ f\) for functions; the entry on operations on relations writes composites in the opposite order). Two facts about the converse are used repeatedly; both follow at once from the definition: \((R^{-1})^{-1}=R\), because reversing a pair twice gives the pair back, and \(R\subseteq S\) implies \(R^{-1}\subseteq S^{-1}\), because \((b,a)\in R^{-1}\) means \((a,b)\in R\), hence \((a,b)\in S\), that is \((b,a)\in S^{-1}\).

\begin{definition}
A relation \(R\) on a set \(A\) is \emph{symmetric} if, for all \(a,b\in A\), \(aRb\) implies \(bRa\).
\end{definition}

\begin{proposition}
For a relation \(R\) on \(A\) the following are equivalent:
\begin{enumerate}
\item \(R\) is symmetric;
\item \(R\subseteq R^{-1}\);
\item \(R=R^{-1}\).
\end{enumerate}
\end{proposition}

\begin{proof}
\textit{(1) implies (2).} If \((a,b)\in R\), then \((b,a)\in R\) by symmetry, which means \((a,b)\in R^{-1}\).

\textit{(2) implies (3).} Taking converses in \(R\subseteq R^{-1}\) gives \(R^{-1}\subseteq(R^{-1})^{-1}=R\). Together with \(R\subseteq R^{-1}\) this gives \(R=R^{-1}\).

\textit{(3) implies (1).} If \(aRb\), then \((a,b)\in R=R^{-1}\), so \((b,a)\in R\), that is \(bRa\).
\end{proof}

Unlike \PMlinkname{reflexivity}{Reflexive}, symmetry does not depend on the underlying set: the condition only mentions pairs that already belong to \(R\), so a set of pairs is symmetric as a relation on \(A\) if and only if it is symmetric as a relation on any larger set.

\begin{proposition}
Let \(R\) and \(S\) be relations on \(A\), and let \(\mathcal{R}\) be a set of symmetric relations on \(A\).
\begin{enumerate}
\item If \(R\) is symmetric, so is \(R^{-1}\).
\item If \(\mathcal{R}\ne\varnothing\), then \(\bigcap\mathcal{R}\) is symmetric; and \(\bigcup\mathcal{R}\) is symmetric.
\item \((S\circ R)^{-1}=R^{-1}\circ S^{-1}\).
\item If \(R\) and \(S\) are symmetric, then \(S\circ R\) is symmetric if and only if \(S\circ R=R\circ S\). In particular \(R\circ R\) is symmetric whenever \(R\) is.
\end{enumerate}
\end{proposition}

\begin{proof}
\textit{(1)} \(R^{-1}=R\) by the previous proposition.

\textit{(2)} Let \((a,b)\in\bigcap\mathcal{R}\). Then \((a,b)\in R'\) for every \(R'\in\mathcal{R}\), hence \((b,a)\in R'\) for every \(R'\in\mathcal{R}\), so \((b,a)\in\bigcap\mathcal{R}\). Similarly, if \((a,b)\in\bigcup\mathcal{R}\), then \((a,b)\in R'\) for some \(R'\in\mathcal{R}\), so \((b,a)\in R'\subseteq\bigcup\mathcal{R}\). (If \(\mathcal{R}=\varnothing\) the union is \(\varnothing\), which is symmetric.)

\textit{(3)} For \(a,c\in A\): \((c,a)\in(S\circ R)^{-1}\) iff \((a,c)\in S\circ R\) iff there is \(b\) with \((a,b)\in R\) and \((b,c)\in S\) iff there is \(b\) with \((c,b)\in S^{-1}\) and \((b,a)\in R^{-1}\) iff \((c,a)\in R^{-1}\circ S^{-1}\).

\textit{(4)} By (3) and \(R=R^{-1}\), \(S=S^{-1}\), we get \((S\circ R)^{-1}=R\circ S\). Hence \(S\circ R=(S\circ R)^{-1}\), which is symmetry of \(S\circ R\) by the previous proposition, holds if and only if \(S\circ R=R\circ S\). Taking \(S=R\) gives the last claim.
\end{proof}

\begin{example}
The composite of two symmetric relations need not be symmetric. On \(A=\{1,2,3\}\) let \(R=\{(1,2),(2,1)\}\) and \(S=\{(2,3),(3,2)\}\); both are symmetric. The only pairs \((a,b)\in R\) and \((b,c)\in S\) with matching middle element are \((1,2)\) and \((2,3)\), so \(S\circ R=\{(1,3)\}\), which is not symmetric. Accordingly \(R\circ S=\{(3,1)\}\ne S\circ R\).
\end{example}

\begin{proposition}
Let \(R\) be a relation on \(A\). Then \(R\cup R^{-1}\) is symmetric, contains \(R\), and is contained in every symmetric relation on \(A\) containing \(R\).
\end{proposition}

\begin{proof}
A pair \((b,a)\) belongs to \((R\cup R^{-1})^{-1}\) iff \((a,b)\in R\cup R^{-1}\) iff \((b,a)\in R^{-1}\cup R\); so \((R\cup R^{-1})^{-1}=R^{-1}\cup R=R\cup R^{-1}\), which is symmetric by the first proposition. Clearly \(R\subseteq R\cup R^{-1}\). If \(T\) is symmetric and \(R\subseteq T\), then \(R^{-1}\subseteq T^{-1}=T\), hence \(R\cup R^{-1}\subseteq T\).
\end{proof}

Thus \(R\cup R^{-1}\) is the smallest symmetric relation containing \(R\), the symmetric closure of \(R\); see \PMlinkname{closure of a relation with respect to a property}{ClosureOfARelationWithRespectToAProperty}. For instance, the symmetric closure of the relation ``\(y=x+1\)'' on \(\mathbb{Z}\) is ``\(|x-y|=1\)''.

\begin{example}
The following relations are symmetric.
\begin{itemize}
\item Equality on any set: \(\Delta_A^{-1}=\Delta_A\). More generally every subset of \(\Delta_A\) is symmetric, since each of its pairs is its own reverse.
\item Congruence modulo a positive integer \(n\) on \(\mathbb{Z}\): if \(b-a=nk\), then \(a-b=n(-k)\).
\item ``Is a sibling of'' (that is, \(x\ne y\) and \(x\), \(y\) have the same mother and the same father) on a set of people: both conditions are unchanged when \(x\) and \(y\) are exchanged.
\item The relation \(x^2+y^2=1\) on \(\mathbb{R}\), since \(x^2+y^2=y^2+x^2\).
\item The empty relation (vacuously) and the full relation \(A\times A\) on any set \(A\).
\end{itemize}
\end{example}

\begin{example}
The following relations are not symmetric.
\begin{itemize}
\item The orders \(\le\) and \(<\) on \(\mathbb{R}\): \(0\le 1\) and \(0<1\), but neither \(1\le 0\) nor \(1<0\).
\item Divisibility on \(\mathbb{N}\) or \(\mathbb{Z}\): \(1\mid 2\) since \(2=1\cdot 2\), but \(2\nmid 1\), since \(1=2c\) has no integer solution.
\item Inclusion on \(\mathcal{P}(X)\) when \(X\ne\varnothing\): for \(x\in X\) we have \(\varnothing\subseteq\{x\}\) but not \(\{x\}\subseteq\varnothing\). (If \(X=\varnothing\), then \(\mathcal{P}(X)=\{\varnothing\}\) and inclusion is \(\Delta_{\mathcal{P}(X)}\), which is symmetric.)
\item ``Is a sister of'' on a set of people containing a girl \(x\) and her brother \(y\): \(x\) is a sister of \(y\), but \(y\) is not a sister of \(x\).
\end{itemize}
\end{example}

\begin{remark}
If \(A=\{a_1,\dots,a_n\}\) is finite with the \(a_i\) distinct, a relation \(R\) on \(A\) is recorded by the \(n\times n\) matrix \(M\) with \(M_{ij}=1\) if \(a_iRa_j\) and \(M_{ij}=0\) otherwise. The matrix of \(R^{-1}\) is the transpose of \(M\), so \(R\) is symmetric if and only if \(M\) is a symmetric matrix. Apart from this, the word ``symmetric'' has unrelated meanings in other contexts, such as symmetric matrices in general, the symmetric group and the symmetric difference of sets; this entry is about relations.
\end{remark}
""")


entry("transitive relation", "transitive-relation", ["03E20", "08A02"],
      ["transitive", "transitive relations", "transitivity"],
      [],
      ["reflexive", "symmetric-relation", "relation"], r"""
Order relations and equivalences share the feature that a relation holding along two consecutive steps also holds directly between the first and the last object, and this is what transitivity expresses.

A relation on a set \(A\) is a subset \(R\subseteq A\times A\), and \(aRb\) means \((a,b)\in R\); \(R^{-1}=\{(b,a)\mid(a,b)\in R\}\) is the converse of \(R\). For relations \(R\) and \(S\) on \(A\) we write
\[
S\circ R=\{(a,c)\in A\times A\mid aRb \text{ and } bSc \text{ for some } b\in A\}
\]
(``first \(R\), then \(S\)'', matching \(g\circ f\) for functions; the entry on operations on relations writes composites in the opposite order, but \(R\circ R\) is the same in both conventions).

\begin{definition}
A relation \(R\) on a set \(A\) is \emph{transitive} if, for all \(a,b,c\in A\), \(aRb\) and \(bRc\) imply \(aRc\).
\end{definition}

\begin{proposition}
A relation \(R\) on \(A\) is transitive if and only if \(R\circ R\subseteq R\).
\end{proposition}

\begin{proof}
By definition, \((a,c)\in R\circ R\) if and only if there is \(b\in A\) with \(aRb\) and \(bRc\). So \(R\circ R\subseteq R\) says exactly that \(aRb\) and \(bRc\) imply \(aRc\).
\end{proof}

Transitivity does not depend on the underlying set, since the condition only concerns pairs in \(R\). We shall need two general facts about composition.

\begin{lemma}
Let \(R\), \(S\), \(T\) be relations on \(A\). Then \(T\circ(S\circ R)=(T\circ S)\circ R\). If \(R\subseteq R'\) and \(S\subseteq S'\), then \(S\circ R\subseteq S'\circ R'\).
\end{lemma}

\begin{proof}
A pair \((a,d)\) lies in \(T\circ(S\circ R)\) iff there is \(c\) with \((a,c)\in S\circ R\) and \(cTd\), iff there are \(b,c\) with \(aRb\), \(bSc\) and \(cTd\). Likewise \((a,d)\in(T\circ S)\circ R\) iff there is \(b\) with \(aRb\) and \((b,d)\in T\circ S\), iff there are \(b,c\) with \(aRb\), \(bSc\), \(cTd\). The two conditions coincide. For the second claim, an intermediate element \(b\) witnessing \((a,c)\in S\circ R\) also witnesses \((a,c)\in S'\circ R'\).
\end{proof}

\begin{proposition}
Let \(R\) and \(S\) be transitive relations on \(A\).
\begin{enumerate}
\item \(R^{-1}\) is transitive.
\item If \(\mathcal{R}\) is a nonempty set of transitive relations on \(A\), then \(\bigcap\mathcal{R}\) is transitive.
\item If \(\mathcal{R}\) is a set of transitive relations on \(A\) any two of which are comparable under \(\subseteq\), then \(\bigcup\mathcal{R}\) is transitive.
\item If \(S\circ R=R\circ S\), then \(S\circ R\) is transitive.
\end{enumerate}
\end{proposition}

\begin{proof}
\textit{(1)} Suppose \((a,b),(b,c)\in R^{-1}\). Then \(cRb\) and \(bRa\), so \(cRa\), that is \((a,c)\in R^{-1}\).

\textit{(2)} If \((a,b),(b,c)\in\bigcap\mathcal{R}\), then both pairs lie in every \(R'\in\mathcal{R}\), so \((a,c)\in R'\) for every \(R'\in\mathcal{R}\), that is \((a,c)\in\bigcap\mathcal{R}\).

\textit{(3)} Let \((a,b)\in R_1\) and \((b,c)\in R_2\) with \(R_1,R_2\in\mathcal{R}\). One of \(R_1,R_2\) contains the other; call the larger one \(R'\). Then \((a,b),(b,c)\in R'\), so \((a,c)\in R'\subseteq\bigcup\mathcal{R}\).

\textit{(4)} Using the lemma, \(R\circ S=S\circ R\), and \(R\circ R\subseteq R\), \(S\circ S\subseteq S\):
\[
(S\circ R)\circ(S\circ R)=S\circ(R\circ S)\circ R=S\circ(S\circ R)\circ R=(S\circ S)\circ(R\circ R)\subseteq S\circ R.
\]
\end{proof}

\begin{example}
Without the hypotheses of (3) and (4), unions and composites of transitive relations need not be transitive.
\begin{itemize}
\item On \(A=\{1,2,3\}\) let \(R=\{(1,2)\}\) and \(S=\{(2,3)\}\). Each is transitive, because \(R\circ R=\varnothing=S\circ S\) (no pair of \(R\) ends where a pair of \(R\) starts, and similarly for \(S\)). But \(R\cup S\) contains \((1,2)\) and \((2,3)\) and not \((1,3)\).
\item On \(A=\{1,2,3,4\}\) let \(R=\{(1,2),(3,4)\}\) and \(S=\{(2,3),(4,1)\}\). Again \(R\circ R=\varnothing=S\circ S\), so both are transitive. Following a pair of \(R\) by a pair of \(S\) gives \(S\circ R=\{(1,3),(3,1)\}\), which contains \((1,3)\) and \((3,1)\) but not \((1,1)\), so it is not transitive.
\end{itemize}
\end{example}

For a relation \(R\) on \(A\), define the powers \(R^1=R\) and \(R^{n+1}=R\circ R^n\) for \(n\ge 1\).

\begin{theorem}
Let \(R\) be a relation on \(A\) and \(R^+=\bigcup_{n\ge 1}R^n\), the union of the sets \(R^n\), one for each integer \(n\ge 1\).
\begin{enumerate}
\item \(R^m\circ R^n=R^{m+n}\) for all \(m,n\ge 1\).
\item For \(n\ge1\), \(aR^nc\) holds if and only if there are \(x_0,\dots,x_n\in A\) with \(x_0=a\), \(x_n=c\) and \(x_{i-1}Rx_i\) for \(i=1,\dots,n\).
\item \(R^+\) is transitive, contains \(R\), and is contained in every transitive relation on \(A\) that contains \(R\).
\end{enumerate}
\end{theorem}

\begin{proof}
\textit{(1)} By \PMlinkname{induction}{PrincipleOfFiniteInduction} on \(m\), for fixed \(n\). For \(m=1\), \(R^1\circ R^n=R\circ R^n=R^{n+1}\) by definition. If \(R^m\circ R^n=R^{m+n}\), then by the lemma
\[
R^{m+1}\circ R^n=(R\circ R^m)\circ R^n=R\circ(R^m\circ R^n)=R\circ R^{m+n}=R^{m+n+1}.
\]

\textit{(2)} By induction on \(n\). For \(n=1\) take \(x_0=a\), \(x_1=c\). Suppose the claim holds for \(n\). By definition \(aR^{n+1}c\) iff there is \(b\) with \(aR^nb\) and \(bRc\); by the induction hypothesis this holds iff there are \(x_0=a,x_1,\dots,x_n=b\) with \(x_{i-1}Rx_i\) for \(i\le n\), and \(bRc\); putting \(x_{n+1}=c\), this is the claim for \(n+1\).

\textit{(3)} \(R=R^1\subseteq R^+\). If \((a,b)\in R^m\) and \((b,c)\in R^n\), then \((a,c)\in R^n\circ R^m=R^{m+n}\subseteq R^+\) by (1); so \(R^+\) is transitive. Let \(T\) be transitive with \(R\subseteq T\). We show \(R^n\subseteq T\) for all \(n\ge1\) by induction: \(R^1=R\subseteq T\), and if \(R^n\subseteq T\) and \((a,c)\in R^{n+1}=R\circ R^n\), there is \(b\) with \(aR^nb\) and \(bRc\), so \(aTb\) and \(bTc\), hence \(aTc\). Therefore \(R^+\subseteq T\).
\end{proof}

So \(R^+\) is the smallest transitive relation containing \(R\), the transitive closure of \(R\); by (2), \(aR^+c\) means that \(c\) can be reached from \(a\) by finitely many, but at least one, steps of \(R\). The union must start at \(n=1\): including \(R^0=\Delta_A\) would add all pairs \((a,a)\), giving the smallest reflexive and transitive relation containing \(R\) instead. For example, the empty relation on a nonempty set is transitive, so it is its own transitive closure, although \(\Delta_A\ne\varnothing\). See \PMlinkname{closure of a relation with respect to a property}{ClosureOfARelationWithRespectToAProperty}.

\begin{example}
Let \(R=\{(n,n+1)\mid n\in\mathbb{N}\}\) on \(\mathbb{N}=\{0,1,2,\dots\}\). By induction, \(R^k=\{(n,n+k)\mid n\in\mathbb{N}\}\) for \(k\ge1\): if this holds for \(k\), then \((a,c)\in R\circ R^k\) iff \(c=b+1\) for some \(b=a+k\), iff \(c=a+k+1\). Hence \(R^+=\{(a,c)\mid c=a+k \text{ for some } k\ge1\}\), which is the strict order \(<\) on \(\mathbb{N}\).
\end{example}

\begin{example}
The following relations are transitive: equality; \(\le\) and \(<\) on \(\mathbb{R}\); inclusion on \(\mathcal{P}(X)\) (if \(A\subseteq B\subseteq C\), every element of \(A\) lies in \(B\), hence in \(C\)); divisibility on \(\mathbb{Z}\) (if \(b=ac\) and \(d=be\), then \(d=a(ce)\)); congruence modulo a positive integer \(n\) on \(\mathbb{Z}\) (if \(b-a=nk\) and \(c-b=nl\), then \(c-a=n(k+l)\)); the empty relation and \(A\times A\).

The following are not transitive. ``Is a sibling of'' (\(x\ne y\) with the same mother and the same father), on a set of people containing two siblings \(x,y\): \(x\) is a sibling of \(y\) and \(y\) of \(x\), but nobody is his or her own sibling. The relation \(|a-b|=1\) on \(\mathbb{Z}\): \(|0-1|=|1-2|=1\) but \(|0-2|=2\).
\end{example}

\begin{remark}
A relation that is \PMlinkname{reflexive}{Reflexive} and transitive is called a preorder. A relation that is reflexive, \PMlinkname{symmetric}{SymmetricRelation} and transitive is an \PMlinkname{equivalence relation}{EquivalenceRelation}; congruence modulo \(n\) is an example, and so is ``has the same mother and the same father as'' (unlike the sibling relation, which differs from it exactly by the diagonal). A \PMlinkname{partial order}{PartiallyOrderedSet} is a reflexive and transitive relation that is moreover antisymmetric, a property treated in its own entry.

The phrase ``transitive set'' (a set every element of which is a subset of it) refers to a different notion, about the membership relation, and is not a special case of the definition above.
\end{remark}
""")


entry("antisymmetric relation", "antisymmetric-relation", ["03E20", "06A06"],
      ["antisymmetric", "antisymmetric relations", "antisymmetry", "anti-symmetric"],
      ["asymmetric relation", "asymmetric"],
      ["reflexive", "symmetric-relation", "transitive-relation", "irreflexive", "partially-ordered-set"], r"""
The axioms of a partial order must exclude two distinct elements lying each below the other, and antisymmetry is the condition that does this.

A relation on a set \(A\) is a subset \(R\subseteq A\times A\), and \(aRb\) means \((a,b)\in R\). We write \(\Delta_A=\{(a,a)\mid a\in A\}\) and \(R^{-1}=\{(b,a)\mid(a,b)\in R\}\) for the converse of \(R\); note that \((R^{-1})^{-1}=R\). For relations \(R\) and \(S\) on \(A\),
\[
S\circ R=\{(a,c)\in A\times A\mid aRb \text{ and } bSc \text{ for some } b\in A\}
\]
(``first \(R\), then \(S\)''; the entry on operations on relations writes composites in the opposite order).

\begin{definition}
Let \(R\) be a relation on a set \(A\).
\begin{enumerate}
\item \(R\) is \emph{antisymmetric} if, for all \(a,b\in A\), \(aRb\) and \(bRa\) imply \(a=b\).
\item \(R\) is \emph{asymmetric} if, for all \(a,b\in A\), \(aRb\) implies that \(bRa\) does not hold.
\end{enumerate}
\end{definition}

\begin{proposition}
Let \(R\) be a relation on \(A\). Then \(R\) is antisymmetric if and only if \(R\cap R^{-1}\subseteq\Delta_A\), and \(R\) is asymmetric if and only if \(R\cap R^{-1}=\varnothing\).
\end{proposition}

\begin{proof}
A pair \((a,b)\) lies in \(R\cap R^{-1}\) if and only if \(aRb\) and \(bRa\), and it lies in \(\Delta_A\) if and only if \(a=b\). So \(R\cap R^{-1}\subseteq\Delta_A\) says that \(aRb\) and \(bRa\) imply \(a=b\), and \(R\cap R^{-1}=\varnothing\) says that \(aRb\) and \(bRa\) never hold together.
\end{proof}

Neither condition depends on the underlying set, since both only concern pairs in \(R\).

\begin{proposition}
A relation \(R\) on \(A\) is asymmetric if and only if it is antisymmetric and \PMlinkname{irreflexive}{Irreflexive}.
\end{proposition}

\begin{proof}
Suppose \(R\) is asymmetric. Then \(aRb\) and \(bRa\) never hold together, so the implication defining antisymmetry is vacuously true. If \(aRa\) held for some \(a\), asymmetry with \(b=a\) would give that \(aRa\) does not hold; hence \(aRa\) holds for no \(a\), and \(R\) is irreflexive.

Conversely, let \(R\) be antisymmetric and irreflexive, and suppose \(aRb\) and \(bRa\). By antisymmetry \(a=b\), so \(aRa\), contradicting irreflexivity. Hence \(aRb\) implies that \(bRa\) fails.
\end{proof}

Antisymmetry is not the negation of \PMlinkname{symmetry}{SymmetricRelation}. In fact a relation \(R\) is both symmetric and antisymmetric if and only if \(R\subseteq\Delta_A\): if \(R\) is both, then \(R=R\cap R^{-1}\subseteq\Delta_A\); conversely, if \(R\subseteq\Delta_A\), each pair in \(R\) has the form \((a,a)\), which is its own reverse, so \(R=R^{-1}\) and \(R\cap R^{-1}=R\subseteq\Delta_A\). Thus equality \(\Delta_A\) and the empty relation are both symmetric and antisymmetric. On the other hand, \(R=\{(1,2),(2,1),(1,3)\}\) on \(\{1,2,3\}\) is neither: it contains \((1,3)\) but not \((3,1)\), and it contains \((1,2)\) and \((2,1)\) although \(1\ne2\).

\begin{proposition}
Let \(R\) and \(S\) be relations on \(A\).
\begin{enumerate}
\item If \(R\) is antisymmetric, so is \(R^{-1}\).
\item If \(R\) is antisymmetric and \(S\subseteq R\), then \(S\) is antisymmetric. In particular, if \(\mathcal{R}\) is a nonempty set of relations on \(A\) at least one of which is antisymmetric, then \(\bigcap\mathcal{R}\) is antisymmetric.
\item The same two statements hold with ``asymmetric'' in place of ``antisymmetric''.
\end{enumerate}
\end{proposition}

\begin{proof}
\textit{(1)} \(R^{-1}\cap(R^{-1})^{-1}=R^{-1}\cap R\subseteq\Delta_A\).

\textit{(2)} Taking converses preserves inclusion (if \((b,a)\in S^{-1}\) then \((a,b)\in S\subseteq R\), so \((b,a)\in R^{-1}\)), hence \(S\cap S^{-1}\subseteq R\cap R^{-1}\subseteq\Delta_A\). If \(R_0\in\mathcal{R}\) is antisymmetric, apply this to \(\bigcap\mathcal{R}\subseteq R_0\).

\textit{(3)} The same computations, with \(\varnothing\) in place of \(\Delta_A\).
\end{proof}

\begin{example}
Unions and composites of antisymmetric relations need not be antisymmetric. On \(\{1,2\}\), the relations \(\{(1,2)\}\) and \(\{(2,1)\}\) are antisymmetric (even asymmetric), but their union contains \((1,2)\) and \((2,1)\). On \(\{1,2,3\}\), let \(R=\{(1,3),(2,3)\}\) and \(S=\{(3,1),(3,2)\}\); neither contains a pair together with its reverse, so both are antisymmetric. Every pair of \(R\) ends at \(3\) and every pair of \(S\) starts at \(3\), so \(S\circ R=\{1,2\}\times\{1,2\}\), which contains \((1,2)\) and \((2,1)\).
\end{example}

\begin{remark}
Unlike reflexivity, symmetry and transitivity, antisymmetry has no closure in general. By (2) above, a relation \(R\) is contained in some antisymmetric relation only if \(R\) itself is antisymmetric, and then \(R\) is the smallest one; so a non-antisymmetric relation has no antisymmetric relation containing it at all. For instance, if \(A=\{1,2\}\), every relation on \(A\) containing \(A\times A\) contains \((1,2)\) and \((2,1)\), so no antisymmetric relation contains \(A\times A\). Compare \PMlinkname{closure of a relation with respect to a property}{ClosureOfARelationWithRespectToAProperty}.
\end{remark}

\begin{example}
The following relations are antisymmetric.
\begin{itemize}
\item Equality, and more generally every subset of \(\Delta_A\).
\item \(\le\) on \(\mathbb{R}\): \(a\le b\) and \(b\le a\) give \(a=b\). The strict order \(<\) is asymmetric, since \(a<b\) and \(b<a\) would give \(a<a\).
\item Inclusion on \(\mathcal{P}(X)\): if \(B\subseteq C\) and \(C\subseteq B\), then \(B\) and \(C\) have the same elements, so \(B=C\).
\item Divisibility on \(\mathbb{N}=\{0,1,2,\dots\}\). Suppose \(b=ac\) and \(a=bd\) with integers \(c,d\). If \(a=0\), then \(b=0=a\). Otherwise \(a=acd\) gives \(cd=1\), so \(c=\pm1\); since \(a>0\) and \(b=ac\ge0\), we get \(c=1\) and \(b=a\).
\item The empty relation, which is also asymmetric.
\end{itemize}
The following are not antisymmetric. Divisibility on \(\mathbb{Z}\): \(1\mid -1\) and \(-1\mid 1\), since \(-1=1\cdot(-1)\) and \(1=(-1)\cdot(-1)\), but \(1\ne-1\). Congruence modulo a positive integer \(n\) on \(\mathbb{Z}\): \(0\equiv n\) and \(n\equiv 0\), but \(0\ne n\). ``Is a sibling of'' on a set of people containing two siblings \(x\ne y\). The full relation \(A\times A\) when \(A\) has two distinct elements \(a,b\), since it contains \((a,b)\) and \((b,a)\); if \(A\) has at most one element, \(A\times A=\Delta_A\) is antisymmetric.
\end{example}

A \PMlinkname{partial order}{PartiallyOrderedSet} is a relation that is \PMlinkname{reflexive}{Reflexive}, antisymmetric and \PMlinkname{transitive}{TransitiveRelation}. A strict order is a relation that is asymmetric and transitive. An irreflexive transitive relation \(R\) is automatically asymmetric: \(aRb\) and \(bRa\) would give \(aRa\). The two notions are linked as follows.

\begin{proposition}
Let \(\le\) be a partial order on a set \(P\), and define \(a<b\) to mean \(a\le b\) and \(a\ne b\). Then \(<\) is irreflexive, asymmetric and transitive; that is, \(<\) is a strict order.
\end{proposition}

\begin{proof}
\textit{Irreflexive.} \(a<a\) would require \(a\ne a\).

\textit{Asymmetric.} If \(a<b\) and \(b<a\), then \(a\le b\) and \(b\le a\), so \(a=b\) by antisymmetry, contradicting \(a\ne b\).

\textit{Transitive.} Let \(a<b\) and \(b<c\). Then \(a\le b\) and \(b\le c\), so \(a\le c\) by transitivity of \(\le\). If \(a=c\), then \(b\le c=a\) and \(a\le b\) give \(a=b\) by antisymmetry, contradicting \(a<b\). Hence \(a\ne c\), and \(a<c\).
\end{proof}
""")

# Part 4 of the naive set theory entries: entries 9 (total order) and 10 (partition of a set).
#
# Ordinary English words in these bodies that might be mis-autolinked to unrelated entries:
# order, ordered, total, partial, linear, strict, chain, element, member, least, greatest,
# maximal, minimal, bound, comparable, converse, reverse, product, pair, word, letter, alphabet,
# position, length, finite, nonempty, induction, case, power, divides, divisibility, interval,
# block, part, cell, class, residue, remainder, even, odd, cover, union, lattice, refinement,
# finer, coarser, sum, number, identity, function, value, condition.
#
# Notes for the assembler / reviewer:
# - Titles, slugs, codes, synonyms, defined terms and related slugs are exactly as in SPEC.md.
# - "trichotomy" is a defined term of entry 9; if an existing entry already defines
#   "trichotomy" (e.g. for the reals or cardinals), the publisher may refuse or the two collide.
# - Entry 10 uses \mathcal{P}, \mathcal{Q}, \mathcal{R} for partitions as the spec says; to avoid
#   a clash with the power set notation \mathcal{P}(S), the power set is never written in entry 10
#   (it says "set of subsets of S" instead).
# - Entry 10 orders partitions by refinement with the finer partition below. The existing entry
#   PartitionsFormALattice could not be checked from here; if it uses the reverse convention,
#   the sentence linking it already warns that some sources reverse the order.
# - In entry 9 the words "function" (remark on the word "total") and in entry 10 nothing else
#   point to later entries; they are plain words, not explicit links.


entry("total order", "total-order", ["06A05"],
      ["linear order", "total ordering", "linear ordering", "totally ordered set", "linearly ordered set",
       "totally ordered", "linearly ordered", "total orders"],
      ["strict total order", "trichotomy", "lexicographic order"],
      ["partially-ordered-set", "chain", "antisymmetric-relation", "transitive-relation", "reflexive"], r"""
In the usual order of the real numbers, as in the alphabetical order of a dictionary, any two distinct objects can be compared, one of them coming before the other; total orders are the partial orders with this property.

We use the terminology of \PMlinkname{partially ordered sets}{PartiallyOrderedSet}: a partial order \(\le\) on a set \(A\) is a reflexive, antisymmetric and transitive relation on \(A\); we write \(a<b\) when \(a\le b\) and \(a\ne b\); two elements \(a,b\) are comparable if \(a\le b\) or \(b\le a\).

\begin{definition}
A \emph{total order} (or \emph{linear order}) on a set \(A\) is a partial order \(\le\) on \(A\) in which any two elements are comparable: for all \(a,b\in A\),
\[
a\le b\quad\text{or}\quad b\le a.
\]
A \emph{totally ordered set} (or \emph{linearly ordered set}) is a pair \((A,\le)\) consisting of a set \(A\) and a total order \(\le\) on \(A\).
\end{definition}

In the language of the poset entry, a partial order on \(A\) is total exactly when \(A\) is a \PMlinkname{chain}{Chain} in itself.

\begin{definition}
A \emph{strict total order} on a set \(A\) is a relation \(<\) on \(A\) such that
\begin{enumerate}
\item \(<\) is \PMlinkname{irreflexive}{Irreflexive}: \(a<a\) holds for no \(a\in A\);
\item \(<\) is transitive: if \(a<b\) and \(b<c\), then \(a<c\);
\item \(<\) satisfies \emph{trichotomy}: for all \(a,b\in A\), exactly one of
\[
a<b,\qquad a=b,\qquad b<a
\]
holds.
\end{enumerate}
\end{definition}

Condition (1) is in fact a consequence of (3): taking \(b=a\), the statement \(a=a\) holds, so \(a<a\) cannot. We list it to make the comparison with partial orders visible. Trichotomy also says that \(a<b\) and \(b<a\) never hold together, so a strict total order is asymmetric.

\begin{theorem}
Let \(A\) be a set.
\begin{enumerate}
\item If \(\le\) is a total order on \(A\), then the relation \(<\) defined by
\[
a<b \iff a\le b \text{ and } a\ne b
\]
is a strict total order on \(A\).
\item If \(<\) is a strict total order on \(A\), then the relation \(\le\) defined by
\[
a\le b \iff a<b \text{ or } a=b
\]
is a total order on \(A\).
\item The two constructions are inverse to each other. Hence they are mutually inverse bijections between the set of total orders on \(A\) and the set of strict total orders on \(A\).
\end{enumerate}
\end{theorem}

\begin{proof}
\textit{(1)} Irreflexivity: \(a<a\) would require \(a\ne a\). Transitivity: let \(a<b\) and \(b<c\). Then \(a\le b\) and \(b\le c\), so \(a\le c\). If we had \(a=c\), then \(b\le c=a\) together with \(a\le b\) would give \(a=b\) by antisymmetry, contradicting \(a\ne b\); so \(a\ne c\) and \(a<c\). Trichotomy: at least one of the three statements holds, because if \(a\ne b\), then \(a\le b\) or \(b\le a\) by comparability, that is, \(a<b\) or \(b<a\). At most one holds: each of \(a<b\) and \(b<a\) includes \(a\ne b\), so neither is compatible with \(a=b\); and \(a<b\) together with \(b<a\) would give \(a\le b\) and \(b\le a\), hence \(a=b\) by antisymmetry, a contradiction.

\textit{(2)} Reflexivity: \(a=a\), so \(a\le a\). Antisymmetry: let \(a\le b\) and \(b\le a\), and suppose \(a\ne b\). Then \(a<b\) and \(b<a\), which trichotomy forbids; so \(a=b\). Transitivity: let \(a\le b\) and \(b\le c\). If \(a=b\), then \(a\le c\) is the hypothesis \(b\le c\); if \(b=c\), then \(a\le c\) is the hypothesis \(a\le b\); otherwise \(a<b\) and \(b<c\), so \(a<c\) and hence \(a\le c\). Comparability: by trichotomy one of \(a<b\), \(a=b\), \(b<a\) holds, so \(a\le b\) or \(b\le a\).

\textit{(3)} Start with a total order \(\le\), form \(<\) as in (1), and then \(\le'\) as in (2). For \(a,b\in A\), \(a\le' b\) means that \(a\le b\) and \(a\ne b\), or \(a=b\). If \(a\le b\), this holds (according as \(a\ne b\) or \(a=b\)); conversely, if it holds, then \(a\le b\), using reflexivity in the case \(a=b\). So \(\le'\) equals \(\le\).

Start with a strict total order \(<\), form \(\le\) as in (2), and then \(<'\) as in (1). Then \(a<'b\) means that (\(a<b\) or \(a=b\)) and \(a\ne b\), that is, \(a<b\) and \(a\ne b\). Since \(a<b\) implies \(a\ne b\) by irreflexivity, \(a<'b\) holds exactly when \(a<b\). So \(<'\) equals \(<\). Both composites are identities, which proves the last statement.
\end{proof}

In terms of sets of pairs, the two constructions are \(R\mapsto R\setminus\Delta_A\) and \(R\mapsto R\cup\Delta_A\), where \(\Delta_A=\{(a,a)\mid a\in A\}\). Because of the theorem one passes freely between \(\le\) and \(<\), and we write \(b\ge a\), \(b>a\) for \(a\le b\), \(a<b\).

\begin{proposition}
Let \((A,\le)\) be a totally ordered set.
\begin{enumerate}
\item The converse relation \(\ge\) is a total order on \(A\).
\item An element of \(A\) is maximal if and only if it is the greatest element, and it is minimal if and only if it is the least element. In particular \(A\) has at most one maximal and at most one minimal element.
\item If \(A\) is finite and nonempty, then \(A\) has a least and a greatest element.
\item Every subset \(B\subseteq A\) is totally ordered by the restriction of \(\le\) to \(B\).
\item For \(a,b\in A\), the set \(\{a,b\}\) has a greatest element \(\max(a,b)\) and a least element \(\min(a,b)\): if \(a\le b\), then \(\max(a,b)=b\) and \(\min(a,b)=a\), and otherwise \(\max(a,b)=a\) and \(\min(a,b)=b\).
\end{enumerate}
\end{proposition}

\begin{proof}
\textit{(1)} Each of the four conditions for \(\ge\) (reflexivity, antisymmetry, transitivity, comparability) is the corresponding condition for \(\le\) with the letters renamed: for instance, \(a\ge b\) and \(b\ge c\) mean \(c\le b\) and \(b\le a\), which give \(c\le a\), that is, \(a\ge c\).

\textit{(2)} A greatest element is maximal by the poset entry. Conversely, let \(m\) be maximal and let \(p\in A\). By comparability, \(p\le m\) or \(m\le p\). In the second case \(p=m\) by maximality, and then \(p\le m\) by reflexivity. So \(p\le m\) for every \(p\), and \(m\) is greatest. Minimal and least elements of \((A,\le)\) are by definition the maximal and greatest elements of \((A,\ge)\), which is totally ordered by (1); so the statement for them follows from the one just proved. A poset has at most one greatest element (poset entry), hence \(A\) has at most one maximal element, and likewise at most one minimal element.

\textit{(3)} By the poset entry, the finite nonempty poset \((A,\le)\) has a maximal element, which is greatest by (2). Applying the same result to \((A,\ge)\), which is finite, nonempty and totally ordered by (1), gives a maximal element of \((A,\ge)\), that is, a minimal element of \((A,\le)\), which is least by (2).

\textit{(4)} The restriction is a partial order on \(B\) (poset entry), and any two elements of \(B\) are elements of \(A\), hence comparable.

\textit{(5)} If \(a\le b\), then \(b\) is greatest and \(a\) least in \(\{a,b\}\), by reflexivity. Otherwise \(b\le a\) by comparability, and the roles are exchanged. Both elements are unique by (2) applied to the totally ordered set \(\{a,b\}\) of (4).
\end{proof}

Part (3) fails for infinite sets: \((\mathbb{Z},\le)\) has neither a greatest nor a least element, since \(n-1<n<n+1\) for every integer \(n\), and the interval \((0,1)\) of \(\mathbb{R}\) has no least element, since \(0<x/2<x\) for every \(x\in(0,1)\).

\begin{definition}
Let \((A,\le_A)\) and \((B,\le_B)\) be totally ordered sets, with strict orders \(<_A\) and \(<_B\). The \emph{lexicographic order} on \(A\times B\) is the relation \(<\) given by
\[
(a,b)<(a',b') \iff a<_A a' \text{ or } \bigl(a=a' \text{ and } b<_B b'\bigr),
\]
together with the corresponding relation \(\le\) (\((a,b)\le(a',b')\) if \((a,b)<(a',b')\) or \((a,b)=(a',b')\)).
\end{definition}

\begin{proposition}
The lexicographic order \(<\) is a strict total order on \(A\times B\); consequently \(\le\) is a total order on \(A\times B\).
\end{proposition}

\begin{proof}
Recall that \((a,b)=(a',b')\) if and only if \(a=a'\) and \(b=b'\).

\textit{Irreflexivity.} \((a,b)<(a,b)\) would require \(a<_A a\) or \(b<_B b\), and neither holds.

\textit{Transitivity.} Let \((a,b)<(a',b')\) and \((a',b')<(a'',b'')\). If \(a<_A a'\) and \(a'<_A a''\), then \(a<_A a''\). If \(a<_A a'\) and \(a'=a''\), or if \(a=a'\) and \(a'<_A a''\), then again \(a<_A a''\). Finally, if \(a=a'=a''\), then \(b<_B b'\) and \(b'<_B b''\), so \(b<_B b''\). In every case \((a,b)<(a'',b'')\).

\textit{Trichotomy.} Let \((a,b),(a',b')\in A\times B\). By trichotomy in \(A\), exactly one of \(a<_A a'\), \(a=a'\), \(a'<_A a\) holds. If \(a<_A a'\), then \((a,b)<(a',b')\); moreover \((a,b)\ne(a',b')\) since \(a\ne a'\), and \((a',b')<(a,b)\) fails because it would need \(a'<_A a\) or \(a'=a\). The case \(a'<_A a\) is symmetric. If \(a=a'\), then neither \(a<_A a'\) nor \(a'<_A a\) holds, so \((a,b)<(a',b')\) holds exactly when \(b<_B b'\), \((a',b')<(a,b)\) exactly when \(b'<_B b\), and \((a,b)=(a',b')\) exactly when \(b=b'\); by trichotomy in \(B\), exactly one of these holds.

The last statement follows from part (2) of the theorem.
\end{proof}

The lexicographic order should be compared with the product order of \PMlinkname{the product of posets}{ProductOfPosets}, in which \((a,b)\le(a',b')\) means \(a\le_A a'\) and \(b\le_B b'\). The product order is contained in the lexicographic order: if \(a\le_A a'\) and \(b\le_B b'\), then either \(a<_A a'\), or \(a=a'\) and \(b\le_B b'\), and in both cases \((a,b)\le(a',b')\) lexicographically. But the product order is usually not total.

\begin{proposition}
Let \(A\) and \(B\) be totally ordered sets. The product order on \(A\times B\) is a total order if and only if \(A\) or \(B\) has at most one element.
\end{proposition}

\begin{proof}
Suppose \(A\) has at most one element, and let \((a,b),(a',b')\in A\times B\). Then \(a=a'\), so \(a\le_A a'\) and \(a'\le_A a\); since \(b\le_B b'\) or \(b'\le_B b\), the two pairs are comparable. The case where \(B\) has at most one element is the same.

Conversely, suppose \(A\) and \(B\) both have two distinct elements. Two distinct elements of \(A\) are comparable, so we may name them \(a<_A a'\); similarly choose \(b<_B b'\). Then \((a,b')\) and \((a',b)\) are not comparable: \((a,b')\le(a',b)\) would need \(b'\le_B b\), which together with \(b\le_B b'\) gives \(b=b'\); and \((a',b)\le(a,b')\) would need \(a'\le_A a\), which similarly gives \(a=a'\). Both conclusions are false.
\end{proof}

For example, in \(\mathbb{N}\times\mathbb{N}\), where \(\mathbb{N}=\{0,1,2,\dots\}\) has its usual order, the pairs \((0,1)\) and \((1,0)\) are not comparable in the product order, whereas \((0,1)<(1,0)\) in the lexicographic order.

\begin{example}
The sets \(\mathbb{N}\), \(\mathbb{Z}\), \(\mathbb{Q}\) and \(\mathbb{R}\) with their usual orders are totally ordered: it is a basic property of these number systems that \(x\le y\) or \(y\le x\) for any two numbers \(x,y\), and the usual order is a partial order. The corresponding strict orders are the usual relations \(<\), and trichotomy for them is the familiar statement that a number is negative, zero or positive, applied to \(y-x\). By part (4) of the proposition, every set of real numbers, such as an interval or the set of primes, is totally ordered by \(\le\). If \((A,\le)\) is totally ordered, so is \((A,\ge)\) by part (1); for instance \(\mathbb{N}\) with the reversed order has the greatest element \(0\) and no least element.
\end{example}

\begin{example}
\textit{(Dictionary order on words of fixed length.)} Let \((A,\le)\) be a totally ordered set, the alphabet, and let \(n\ge1\). Words of length \(n\) are \(n\)-tuples \((u_1,\dots,u_n)\in A^n\), where \(A^1=A\) and \(A^k=A^{k-1}\times A\), so that \((u_1,\dots,u_k)=((u_1,\dots,u_{k-1}),u_k)\). Order \(A^1\) by \(\le\) and, for \(k\ge2\), order \(A^k\) lexicographically as the product of the totally ordered sets \(A^{k-1}\) and \(A\). By the proposition and \PMlinkname{induction}{PrincipleOfFiniteInduction} on \(k\), each \(A^k\) is totally ordered. We claim that for distinct words \(u,v\in A^n\),
\[
u<v \iff u_j<v_j, \text{ where } j \text{ is the first index with } u_j\ne v_j.
\]
For \(n=1\) this is the definition. Let \(n\ge2\), assume the claim for \(n-1\), and write \(u=(u',u_n)\), \(v=(v',v_n)\) with \(u',v'\in A^{n-1}\). By definition \(u<v\) if and only if \(u'<v'\), or \(u'=v'\) and \(u_n<v_n\). If \(u'\ne v'\), the first index where \(u\) and \(v\) differ is the first index where \(u'\) and \(v'\) differ, and the claim follows from the induction hypothesis. If \(u'=v'\), then \(u'<v'\) is false, the first index where \(u\) and \(v\) differ is \(n\), and \(u<v\) if and only if \(u_n<v_n\). With the Latin alphabet ordered \(a<b<\dots<z\), this is dictionary order; for instance \(\mathrm{cat}<\mathrm{cow}\), since the words first differ in the second letter and \(a<o\).
\end{example}

\begin{example}
\textit{(Partial orders that are not total.)} Let \(X=\{x,y\}\) with \(x\ne y\), and order the set of subsets of \(X\) by inclusion. Then \(\{x\}\) and \(\{y\}\) are not comparable: \(\{x\}\subseteq\{y\}\) would mean \(x\in\{y\}\), that is, \(x=y\), and similarly for the reverse inclusion. Divisibility on \(\mathbb{N}\) is a partial order (see the poset entry) that is not total: \(2\nmid 3\), since \(3=2c\) has no integer solution (\(c\le1\) gives \(2c\le2\) and \(c\ge2\) gives \(2c\ge4\)), and \(3\nmid 2\), since \(c\le0\) gives \(3c\le0\) and \(c\ge1\) gives \(3c\ge3\).
\end{example}

\begin{remark}
Some authors define a total order as a relation \(\le\) on \(A\) that is antisymmetric, transitive and \emph{connex}: \(a\le b\) or \(b\le a\) for all \(a,b\in A\), with no separate reflexivity condition. The two definitions agree. A total order in our sense is connex by comparability. Conversely, if \(\le\) is connex, then taking \(b=a\) gives \(a\le a\), so \(\le\) is reflexive; being also antisymmetric and transitive, it is a partial order, and connexity says that any two elements are comparable, so it is a total order. Note that the word ``total'' here refers to comparability of elements; it is unrelated to the use of ``total'' for a function that is defined at every point of its domain.
\end{remark}
""")


entry("partition of a set", "partition", ["03E20", "03E05"],
      ["partition", "partitions", "partitions of a set", "set partition"],
      ["block of a partition", "refinement of a partition"],
      ["set-operations", "equivalence-relation", "partition-is-equivalent-to-an-equivalence-relation"], r"""
Sorting the elements of a set into nonoverlapping groups, as the integers are sorted into even and odd numbers, is one of the most common constructions in mathematics, and a partition is the set of groups produced by such a sorting.

\begin{definition}
Let \(S\) be a set. A \emph{partition} of \(S\) is a set \(\mathcal{P}\) of subsets of \(S\) such that
\begin{enumerate}
\item every member of \(\mathcal{P}\) is nonempty, that is, \(\varnothing\notin\mathcal{P}\);
\item any two distinct members of \(\mathcal{P}\) are disjoint: if \(B,C\in\mathcal{P}\) and \(B\ne C\), then \(B\cap C=\varnothing\);
\item the union of \(\mathcal{P}\) is \(S\): \(\bigcup\mathcal{P}=S\).
\end{enumerate}
The members of \(\mathcal{P}\) are called the \emph{blocks} of the partition (also parts or cells).
\end{definition}

Condition (2) says that \(\mathcal{P}\) is pairwise disjoint as a set of sets.

\begin{proposition}
Let \(S\) be a set and \(\mathcal{P}\) a set of nonempty subsets of \(S\).
\begin{enumerate}
\item \(\mathcal{P}\) is a partition of \(S\) if and only if every element of \(S\) belongs to exactly one member of \(\mathcal{P}\).
\item If \(\mathcal{P}\) is a partition of \(S\) and \([x]_{\mathcal{P}}\) denotes the block containing \(x\in S\), then a block \(B\) equals \([x]_{\mathcal{P}}\) for every \(x\in B\), and \(\mathcal{P}=\{[x]_{\mathcal{P}}\mid x\in S\}\).
\end{enumerate}
\end{proposition}

\begin{proof}
\textit{(1)} Suppose \(\mathcal{P}\) is a partition and let \(x\in S\). Since \(S=\bigcup\mathcal{P}\), there is \(B\in\mathcal{P}\) with \(x\in B\). If also \(x\in C\in\mathcal{P}\) with \(C\ne B\), then \(x\in B\cap C=\varnothing\), which is impossible. So \(x\) lies in exactly one member.

Conversely, suppose every element of \(S\) lies in exactly one member of \(\mathcal{P}\). Condition (1) of the definition holds by hypothesis. For (3), \(\bigcup\mathcal{P}\subseteq S\) because every member is a subset of \(S\), and \(S\subseteq\bigcup\mathcal{P}\) because every \(x\in S\) lies in some member. For (2), let \(B,C\in\mathcal{P}\) with \(B\ne C\), and suppose \(x\in B\cap C\). Then \(x\in S\), because \(B\subseteq S\), and \(x\) lies in the two distinct members \(B\) and \(C\), a contradiction. Hence \(B\cap C=\varnothing\).

\textit{(2)} If \(x\in B\in\mathcal{P}\), then \(B\) is a block containing \(x\), and by (1) it is the only one, so \(B=[x]_{\mathcal{P}}\). Every block \(B\) is nonempty, so it contains some \(x\), and then \(B=[x]_{\mathcal{P}}\); conversely each \([x]_{\mathcal{P}}\) is a block. This proves \(\mathcal{P}=\{[x]_{\mathcal{P}}\mid x\in S\}\).
\end{proof}

\begin{example}
\textit{(Partitions of \(\mathbb{Z}\).)} Let \(m\ge1\) be an integer, and for \(r=0,1,\dots,m-1\) let
\[
R_r=\{qm+r\mid q\in\mathbb{Z}\}
\]
be the set of integers leaving remainder \(r\) on division by \(m\). Then \(\{R_0,\dots,R_{m-1}\}\) is a partition of \(\mathbb{Z}\) with exactly \(m\) blocks. Indeed, \(r\in R_r\), so each \(R_r\) is nonempty; and by division with remainder every integer \(n\) can be written as \(n=qm+r\) with \(q\in\mathbb{Z}\) and \(r\in\{0,\dots,m-1\}\), where \(q\) and \(r\) are uniquely determined by \(n\). Existence says that \(n\) lies in some \(R_r\); uniqueness of \(r\) says that it lies in only one, and also that the sets \(R_0,\dots,R_{m-1}\) are pairwise distinct (since \(r\in R_r\) but \(r\notin R_s\) for \(s\ne r\)). By part (1) of the proposition this is a partition. Its blocks are the residue classes modulo \(m\), the elements of \PMlinkname{the integers modulo \(m\)}{IntegersModuloN}. For \(m=2\) we obtain the partition of \(\mathbb{Z}\) into the even integers \(R_0\) and the odd integers \(R_1\); for \(m=1\) we obtain the one-block partition \(\{\mathbb{Z}\}\).
\end{example}

\begin{example}
\textit{(The finest and the coarsest partition.)} For any set \(S\), the set \(\{\{x\}\mid x\in S\}\) of singletons is a partition of \(S\): each singleton is nonempty, and an element \(y\in S\) lies in \(\{x\}\) if and only if \(x=y\), so it lies in exactly one of them. If \(S\ne\varnothing\), then \(\{S\}\) is a partition of \(S\) with a single block: its only member is nonempty and contains every element of \(S\). If \(S\) has exactly one element, the two partitions coincide.
\end{example}

\begin{example}
\textit{(The empty set.)} The empty set has exactly one partition, namely \(\mathcal{P}=\varnothing\). This \(\varnothing\) is a partition of \(\varnothing\): conditions (1) and (2) are vacuous, since there are no members, and \(\bigcup\varnothing=\varnothing\). Conversely, let \(\mathcal{P}\) be a partition of \(\varnothing\). Every block is a subset of \(\varnothing\), hence equal to \(\varnothing\), but blocks are nonempty; so \(\mathcal{P}\) has no members, and \(\mathcal{P}=\varnothing\). In particular \(\{\varnothing\}\) is not a partition of \(\varnothing\), because its member \(\varnothing\) is empty. (So the one-block partition \(\{S\}\) of the previous example exists only for \(S\ne\varnothing\).)
\end{example}

\begin{example}
\textit{(A set with three elements.)} Let \(S=\{a,b,c\}\) with \(a,b,c\) distinct. The partitions of \(S\) are exactly the following five:
\[
\bigl\{\{a\},\{b\},\{c\}\bigr\},\quad \bigl\{\{a,b\},\{c\}\bigr\},\quad \bigl\{\{a,c\},\{b\}\bigr\},\quad \bigl\{\{a\},\{b,c\}\bigr\},\quad \bigl\{\{a,b,c\}\bigr\}.
\]
Each of them is a partition, because its members are nonempty subsets of \(S\) and each of \(a,b,c\) lies in exactly one member. They are pairwise distinct, since they differ in which pairs of elements share a block. To see that there are no others, let \(\mathcal{P}\) be a partition of \(S\) and recall from part (2) of the proposition that \(\mathcal{P}=\{[a]_{\mathcal{P}},[b]_{\mathcal{P}},[c]_{\mathcal{P}}\}\), where distinct blocks are disjoint. The block \([a]_{\mathcal{P}}\) is a subset of \(S\) containing \(a\), so it is \(\{a,b,c\}\), \(\{a,b\}\), \(\{a,c\}\) or \(\{a\}\).
\begin{itemize}
\item If \([a]_{\mathcal{P}}=S\), then \([b]_{\mathcal{P}}=[c]_{\mathcal{P}}=S\) by part (2), so \(\mathcal{P}=\{S\}\).
\item If \([a]_{\mathcal{P}}=\{a,b\}\), then \([b]_{\mathcal{P}}=\{a,b\}\), and \([c]_{\mathcal{P}}\) is a block different from \(\{a,b\}\) (it contains \(c\)), hence disjoint from it, so \([c]_{\mathcal{P}}=\{c\}\). Thus \(\mathcal{P}=\{\{a,b\},\{c\}\}\). The case \([a]_{\mathcal{P}}=\{a,c\}\) is the same with \(b\) and \(c\) exchanged.
\item If \([a]_{\mathcal{P}}=\{a\}\), then \([b]_{\mathcal{P}}\) is a block different from \(\{a\}\) (it contains \(b\)), hence disjoint from \(\{a\}\); as it contains \(b\), it is \(\{b,c\}\) or \(\{b\}\). In the first case \([c]_{\mathcal{P}}=\{b,c\}\) and \(\mathcal{P}=\{\{a\},\{b,c\}\}\); in the second, \([c]_{\mathcal{P}}\) is disjoint from \(\{a\}\) and \(\{b\}\), so \([c]_{\mathcal{P}}=\{c\}\) and \(\mathcal{P}\) is the partition into singletons.
\end{itemize}
\end{example}

\begin{example}
\textit{(The real line.)} The sets \((-\infty,0)\), \(\{0\}\) and \((0,\infty)\) form a partition of \(\mathbb{R}\). They are nonempty, containing \(-1\), \(0\) and \(1\), and by \PMlinkname{trichotomy}{TotalOrder} for the usual order of \(\mathbb{R}\), every real number \(x\) satisfies exactly one of \(x<0\), \(x=0\), \(0<x\), so it lies in exactly one of the three sets.
\end{example}

\begin{example}
\textit{(Non-examples.)} Let \(S=\{1,2,3\}\).
\begin{itemize}
\item \(\{\{1,2\},\{2,3\}\}\) is not a partition of \(S\): its two distinct members both contain \(2\).
\item \(\{\{1\},\{3\}\}\) is not a partition of \(S\): its union \(\{1,3\}\) misses \(2\).
\item \(\{\varnothing,\{1,2,3\}\}\) is not a partition of \(S\): it has the empty set as a member.
\item \(\{\{1,2\},\{3,4\}\}\) is not a partition of \(S\): the member \(\{3,4\}\) is not a subset of \(S\) (it is a partition of \(\{1,2,3,4\}\)).
\end{itemize}
\end{example}

Partitions of the same set can be compared according to how fine their blocks are.

\begin{definition}
Let \(\mathcal{P}\) and \(\mathcal{Q}\) be partitions of a set \(S\). We say that \(\mathcal{P}\) \emph{refines} \(\mathcal{Q}\), or that \(\mathcal{P}\) is a \emph{refinement} of \(\mathcal{Q}\), and write \(\mathcal{P}\preceq\mathcal{Q}\), if every block of \(\mathcal{P}\) is contained in some block of \(\mathcal{Q}\). We then also say that \(\mathcal{P}\) is finer than \(\mathcal{Q}\) and that \(\mathcal{Q}\) is coarser than \(\mathcal{P}\).
\end{definition}

\begin{lemma}
Let \(\mathcal{P}\) and \(\mathcal{Q}\) be partitions of \(S\). Then \(\mathcal{P}\preceq\mathcal{Q}\) if and only if \([x]_{\mathcal{P}}\subseteq[x]_{\mathcal{Q}}\) for every \(x\in S\).
\end{lemma}

\begin{proof}
Suppose \(\mathcal{P}\preceq\mathcal{Q}\) and let \(x\in S\). The block \([x]_{\mathcal{P}}\) is contained in some block \(C\) of \(\mathcal{Q}\). Then \(x\in C\), so \(C=[x]_{\mathcal{Q}}\) by part (2) of the proposition, and \([x]_{\mathcal{P}}\subseteq[x]_{\mathcal{Q}}\). Conversely, suppose the inclusions hold and let \(B\) be a block of \(\mathcal{P}\). Choose \(x\in B\) (blocks are nonempty); then \(B=[x]_{\mathcal{P}}\subseteq[x]_{\mathcal{Q}}\), a block of \(\mathcal{Q}\).
\end{proof}

\begin{theorem}
Let \(S\) be a set and let \(\Pi(S)\) be the set of all partitions of \(S\). Refinement \(\preceq\) is a partial order on \(\Pi(S)\). The partition into singletons is its least element, and if \(S\ne\varnothing\), the one-block partition \(\{S\}\) is its greatest element.
\end{theorem}

\begin{proof}
We use the lemma throughout. Reflexivity: \([x]_{\mathcal{P}}\subseteq[x]_{\mathcal{P}}\). Transitivity: if \(\mathcal{P}\preceq\mathcal{Q}\) and \(\mathcal{Q}\preceq\mathcal{R}\), then \([x]_{\mathcal{P}}\subseteq[x]_{\mathcal{Q}}\subseteq[x]_{\mathcal{R}}\) for every \(x\in S\), so \(\mathcal{P}\preceq\mathcal{R}\). Antisymmetry: if \(\mathcal{P}\preceq\mathcal{Q}\) and \(\mathcal{Q}\preceq\mathcal{P}\), then \([x]_{\mathcal{P}}=[x]_{\mathcal{Q}}\) for every \(x\in S\), and by part (2) of the proposition
\[
\mathcal{P}=\{[x]_{\mathcal{P}}\mid x\in S\}=\{[x]_{\mathcal{Q}}\mid x\in S\}=\mathcal{Q}.
\]
If \(\mathcal{O}\) is the partition into singletons, then \([x]_{\mathcal{O}}=\{x\}\subseteq[x]_{\mathcal{Q}}\) for every partition \(\mathcal{Q}\) and every \(x\), so \(\mathcal{O}\preceq\mathcal{Q}\). If \(S\ne\varnothing\), then \([x]_{\{S\}}=S\supseteq[x]_{\mathcal{P}}\) for every partition \(\mathcal{P}\) and every \(x\), so \(\mathcal{P}\preceq\{S\}\).
\end{proof}

\begin{remark}
Antisymmetry really uses the fact that we compare partitions. For arbitrary sets of sets the condition ``every member of \(\mathcal{A}\) is contained in some member of \(\mathcal{B}\)'' is reflexive and transitive but not antisymmetric: \(\mathcal{A}=\{\{1\},\{1,2\}\}\) and \(\mathcal{B}=\{\{1,2\}\}\) satisfy it in both directions, since every member of either is contained in \(\{1,2\}\), and yet \(\mathcal{A}\ne\mathcal{B}\). (Here \(\mathcal{A}\) is not a partition, as its members overlap.)
\end{remark}

\begin{example}
Refinement is in general not a total order. For \(S=\{a,b,c\}\) as above, the partitions \(\{\{a,b\},\{c\}\}\) and \(\{\{a,c\},\{b\}\}\) are not comparable: the block \(\{a,b\}\) is not contained in \(\{a,c\}\) or in \(\{b\}\), and the block \(\{a,c\}\) is not contained in \(\{a,b\}\) or in \(\{c\}\). In \(\mathbb{Z}\), the partition into residue classes modulo \(4\) refines the partition into even and odd integers, since \(4q+r=2(2q)+r\) has the same parity as \(r\), so each class modulo \(4\) lies in the parity class of its remainder. In fact \(\Pi(S)\) is a lattice under refinement; see \PMlinkname{partitions form a lattice}{PartitionsFormALattice} (some sources order partitions in the reverse direction, with the finest partition on top).
\end{example}

\begin{remark}
Partitions of \(S\) are the same thing as \PMlinkname{equivalence relations}{EquivalenceRelation} on \(S\). A partition \(\mathcal{P}\) determines the relation \(x\sim_{\mathcal{P}}y\) if and only if \(x\) and \(y\) lie in the same block, that is, \([x]_{\mathcal{P}}=[y]_{\mathcal{P}}\); this is an equivalence relation whose equivalence classes are exactly the blocks. Conversely, the equivalence classes of an equivalence relation on \(S\) form a partition of \(S\), and the two constructions are inverse to each other; see \PMlinkname{partition is equivalent to an equivalence relation}{PartitionIsEquivalentToAnEquivalenceRelation}. Under this correspondence refinement becomes inclusion of relations: \(\mathcal{P}\preceq\mathcal{Q}\) if and only if \(\sim_{\mathcal{P}}\subseteq\sim_{\mathcal{Q}}\). Indeed, \(x\sim_{\mathcal{P}}y\) means \(y\in[x]_{\mathcal{P}}\), so the inclusion of relations says exactly that \(y\in[x]_{\mathcal{P}}\) implies \(y\in[x]_{\mathcal{Q}}\) for all \(x,y\), that is, \([x]_{\mathcal{P}}\subseteq[x]_{\mathcal{Q}}\) for all \(x\), which is the condition of the lemma.
\end{remark}

\begin{remark}
In number theory the word ``partition'' has an unrelated meaning: a partition of a positive integer \(n\) is a way of writing \(n\) as a sum of positive integers, without regard to the order of the summands, such as \(4=2+1+1\). This entry is about partitions of sets.
\end{remark}
""")

# Part 5 of the naive set theory entries: entries 11 (function), 12 (image and inverse image),
# 13 (composition of functions), in global order.
#
# Ordinary English words in these bodies that might be mis-autolinked to unrelated entries:
# domain (ring-theory "domain" entry; escape "domain" in all three entries), graph (graph theory;
# escape "graph" in entries 11, 12, 13), range, image (in entries 11 and 13 "image" should link to
# entry 12, which is correct), identity, inverse (both defined terms of "multivalued function"),
# value, values, constant, extension (field extension), restriction, inclusion, total, partial,
# element, point, table, product, power, order, family, choice, program, undefined, fibre, fiber
# (fibre bundle), kernel, monoid, iterate, iterates, square, root, circle, interval, rule,
# source, copy, partition (entry 12 uses it in the intended sense, entry 10), class.
#
# Notes for the assembler / reviewer:
# - All titles, slugs, codes, synonyms, defined terms and related slugs are exactly as in SPEC.md.
# - Explicit links point only to existing entries or to earlier new entries (Relation,
#   OrderedPair, CartesianProduct, SetOperations, Partition, RussellsParadox, MultivaluedFunction,
#   Subfunction, PropertiesOfAFunction, EquivalenceRelation, Function, Image,
#   OperationsOnRelations, PrincipleOfFiniteInduction).
# - Later concepts (injective, surjective, bijective, inverse function, indexed family, indicator
#   function) are mentioned only in plain words; they will autolink forward once the batch is
#   live, which seems intended.
# - The "new point" for partial functions is introduced as an object * not in B, with
#   B_* = B u {*}; existence of such an object is proved, before the proposition, by the
#   Russell argument (the set {b in B | b not in b} is not an element of B), so no axiom is needed.
#   The spec's B \sqcup \{\ast\} is mentioned there as an equivalent choice (identify b with (b,0));
#   B u {*} is kept because it leaves the values of f unchanged and gives graph = g cap (A x B).


entry("function", "function", ["03E20"],
      ["functions", "partial function", "partial functions", "total function", "total functions"],
      ["functional relation", "codomain", "domain of definition", "graph of a function",
       "identity function", "constant function", "empty function", "restriction of a function",
       "extension of a function", "inclusion map"],
      ["relation", "cartesian-product", "ordered-pair", "naive-set-theory"], r"""
A function assigns to each input exactly one output, and in set theory this rule is captured by the set of all its input-output pairs, which is a \PMlinkname{binary relation}{Relation}.

Throughout, a binary relation from a set \(A\) to a set \(B\) is a subset \(R\) of the \PMlinkname{Cartesian product}{CartesianProduct} \(A\times B\), and we write \(aRb\) for \((a,b)\in R\). Its domain and range are
\[
\operatorname{dom}R=\{a\mid aRb \text{ for some } b\},\qquad \operatorname{ran}R=\{b\mid aRb \text{ for some } a\}.
\]
For \(R\subseteq A\times B\) we have \(\operatorname{dom}R\subseteq A\) and \(\operatorname{ran}R\subseteq B\).

\begin{definition}
Let \(A\) and \(B\) be sets.
\begin{enumerate}
\item A relation \(f\subseteq A\times B\) is a \emph{functional relation} (or is single-valued) if, for all \(a\in A\) and \(b,b'\in B\), \((a,b)\in f\) and \((a,b')\in f\) imply \(b=b'\).
\item A \emph{partial function} from \(A\) to \(B\) is a triple \((A,B,f)\) in which \(f\subseteq A\times B\) is a functional relation; we write \(f\colon A\rightharpoonup B\). The set \(\operatorname{dom}f\) is the \emph{domain of definition} of the partial function. For \(a\in\operatorname{dom}f\) the unique \(b\in B\) with \((a,b)\in f\) is called the value of \(f\) at \(a\) and is denoted \(f(a)\); we say that \(f(a)\) is defined if and only if \(a\in\operatorname{dom}f\).
\item A partial function \(f\colon A\rightharpoonup B\) is \emph{total} if \(\operatorname{dom}f=A\). A \emph{total function}, or simply a \emph{function} (also called a map or mapping) from \(A\) to \(B\), is a total partial function; we write \(f\colon A\to B\). The set \(A\) is the domain of \(f\), the set \(B\) is its \emph{codomain}, and the relation \(f\subseteq A\times B\) is the \emph{graph} of \(f\).
\end{enumerate}
\end{definition}

Following common usage, the same letter \(f\) denotes the triple and its graph. The triple is the \PMlinkname{ordered triple}{OrderedPair} \(((A,B),f)\); only the fact that two triples are equal exactly when their corresponding coordinates are equal will be used. In other entries of this collection, ``function'' means total function unless the word ``partial'' is said.

\begin{proposition}
Let \(A\) and \(B\) be sets and \(f\subseteq A\times B\). Then \((A,B,f)\) is a function \(A\to B\) if and only if for every \(a\in A\) there is exactly one \(b\in B\) with \((a,b)\in f\).
\end{proposition}

\begin{proof}
Suppose \((A,B,f)\) is a function and let \(a\in A\). Since \(\operatorname{dom}f=A\), there is some \(b\) with \((a,b)\in f\), and \(b\in B\) because \(f\subseteq A\times B\). If also \((a,b')\in f\), then \(b'=b\) because \(f\) is functional.

Conversely, suppose that for every \(a\in A\) there is exactly one \(b\in B\) with \((a,b)\in f\). If \((a,b)\in f\) and \((a,b')\in f\), then \(a\in A\) and \(b,b'\in B\) because \(f\subseteq A\times B\), so \(b=b'\) by the uniqueness part of the hypothesis; thus \(f\) is functional. Every \(a\in A\) lies in \(\operatorname{dom}f\) by the existence part, so \(A\subseteq\operatorname{dom}f\), and \(\operatorname{dom}f\subseteq A\) because \(f\subseteq A\times B\). Hence \(\operatorname{dom}f=A\).
\end{proof}

By the proposition, a function \(f\colon A\to B\) can be specified by giving, for every \(a\in A\), an element \(f(a)\in B\): its graph is then \(\{(a,f(a))\mid a\in A\}\). One writes \(a\mapsto f(a)\) for such a rule, for instance \(x\mapsto x^2\) for the function \(\mathbb{R}\to\mathbb{R}\) with graph \(\{(x,x^2)\mid x\in\mathbb{R}\}\).

\begin{proposition}
Let \(f\colon A\to B\) and \(g\colon A'\to B'\) be functions. Then \(f=g\) if and only if \(A=A'\), \(B=B'\) and \(f(a)=g(a)\) for every \(a\in A\).
\end{proposition}

\begin{proof}
Two triples are equal if and only if their corresponding coordinates are equal, so \(f=g\) means \(A=A'\), \(B=B'\), and equality of the graphs. If the graphs are equal and \(a\in A\), then \((a,f(a))\in f=g\), so \(f(a)=g(a)\) because \(g(a)\) is the only element paired with \(a\) in \(g\).

Conversely, assume \(A=A'\), \(B=B'\) and \(f(a)=g(a)\) for all \(a\in A\). If \((a,b)\in f\), then \(a\in A\) and \(b=f(a)=g(a)\), so \((a,b)\in g\). In the same way every element of \(g\) lies in \(f\). By extensionality the graphs are equal, and therefore \(f=g\).
\end{proof}

Every function is a partial function, by definition. Conversely, a partial function can be regarded as a total function in two ways: by shrinking its domain to the domain of definition, or by enlarging its codomain by a point that stands for ``undefined''.

For the second way we need an object \(\ast\) that is not an element of \(B\). Such an object always exists: the set \(r=\{b\in B\mid b\notin b\}\) is not an element of \(B\), since \(r\in B\) would give \(r\in r\) if and only if \(r\notin r\), as in \PMlinkname{Russell's paradox}{RussellsParadox}. Which such object is chosen does not matter for what follows. (Equivalently, one may use the \PMlinkname{disjoint union}{SetOperations} \(B\sqcup\{\ast\}\), identifying each \(b\in B\) with its copy \((b,0)\); working with \(B\cup\{\ast\}\) for \(\ast\notin B\) avoids this identification and keeps the values of \(f\) unchanged.)

\begin{proposition}
Let \(A\) and \(B\) be sets.
\begin{enumerate}
\item If \(f\colon A\rightharpoonup B\) is a partial function, then \((\operatorname{dom}f,B,f)\) is a function \(\operatorname{dom}f\to B\) with the same values. Conversely, if \(D\subseteq A\) and \(g\colon D\to B\) is a function, then \((A,B,g)\) is a partial function \(A\rightharpoonup B\) with domain of definition \(D\). These two assignments keep the graph and are inverse to each other, so partial functions \(A\rightharpoonup B\) correspond one to one to pairs \((D,g)\) consisting of a subset \(D\subseteq A\) and a function \(g\colon D\to B\).
\item Fix an object \(\ast\) that is not an element of \(B\) and put \(B_\ast=B\cup\{\ast\}\). For a partial function \(f\colon A\rightharpoonup B\), let \(\hat f\colon A\to B_\ast\) be given by \(\hat f(a)=f(a)\) if \(a\in\operatorname{dom}f\) and \(\hat f(a)=\ast\) otherwise. Then \(f\mapsto\hat f\) is a one-to-one correspondence between partial functions \(A\rightharpoonup B\) and functions \(A\to B_\ast\); the partial function corresponding to \(g\colon A\to B_\ast\) has graph \(g\cap(A\times B)\).
\end{enumerate}
\end{proposition}

\begin{proof}
\textit{(1)} Let \(f\colon A\rightharpoonup B\). Every \((a,b)\in f\) has \(a\in\operatorname{dom}f\) and \(b\in B\), so \(f\subseteq\operatorname{dom}f\times B\); the relation \(f\) is functional, and its domain is \(\operatorname{dom}f\). Hence \((\operatorname{dom}f,B,f)\) is a function, and its values are those of \(f\) since the graph is the same. Conversely, let \(D\subseteq A\) and \(g\colon D\to B\). Then \(g\subseteq D\times B\subseteq A\times B\) is functional, so \((A,B,g)\) is a partial function, and \(\operatorname{dom}g=D\) because \(g\) is total on \(D\). Starting from \(f\), the first assignment gives \((\operatorname{dom}f,f)\) and the second returns \((A,B,f)\); starting from \((D,g)\), the second gives \((A,B,g)\), and the first returns \((\operatorname{dom}g,g)=(D,g)\).

\textit{(2)} For each \(a\in A\) the rule defining \(\hat f(a)\) gives exactly one element of \(B_\ast\), so \(\hat f\) is a function \(A\to B_\ast\). Given a function \(g\colon A\to B_\ast\), let \(\check g=g\cap(A\times B)=\{(a,g(a))\mid a\in A,\ g(a)\ne\ast\}\). It is a subset of \(A\times B\) and is functional, being contained in the functional relation \(g\); so \(\check g\colon A\rightharpoonup B\) is a partial function, with \(\operatorname{dom}\check g=\{a\in A\mid g(a)\ne\ast\}\) and \(\check g(a)=g(a)\) there. We show that the two assignments are inverse to each other.
\begin{itemize}
\item For a partial function \(f\), the graph of \(\check{\hat f}\) consists of the pairs \((a,\hat f(a))\) with \(\hat f(a)\ne\ast\). Since \(\ast\notin B\), we have \(\hat f(a)\ne\ast\) exactly when \(a\in\operatorname{dom}f\), and then \(\hat f(a)=f(a)\). So the graph is \(\{(a,f(a))\mid a\in\operatorname{dom}f\}=f\), and \(\check{\hat f}=f\).
\item For a function \(g\colon A\to B_\ast\) and \(a\in A\): if \(g(a)\ne\ast\), then \(a\in\operatorname{dom}\check g\) and \(\hat{\check g}(a)=\check g(a)=g(a)\); if \(g(a)=\ast\), then \(a\notin\operatorname{dom}\check g\) and \(\hat{\check g}(a)=\ast=g(a)\). By the previous proposition \(\hat{\check g}=g\).
\end{itemize}
\end{proof}

\begin{example}
Partial functions arise naturally whenever a formula does not make sense for every input.
\begin{itemize}
\item The relation \(\{(x,y)\in\mathbb{R}\times\mathbb{R}\mid xy=1\}\) is functional, since \(xy=1=xy'\) forces \(x\ne0\) and then \(y=y'=1/x\). Its domain of definition is \(\mathbb{R}\setminus\{0\}\): for \(x\ne0\) the pair \((x,1/x)\) belongs to it, and no pair \((0,y)\) does. So \(x\mapsto1/x\) is a partial function \(\mathbb{R}\rightharpoonup\mathbb{R}\) that is not total, and a total function \(\mathbb{R}\setminus\{0\}\to\mathbb{R}\).
\item The relation \(\{(x,y)\in\mathbb{R}\times\mathbb{R}\mid y\ge0,\ y^2=x\}\) is the graph of the square root \(x\mapsto\sqrt{x}\) as a partial function \(\mathbb{R}\rightharpoonup\mathbb{R}\). It is functional because every \(x\ge0\) has exactly one square root \(y\ge0\) (a known fact about \(\mathbb{R}\)); its domain of definition is \([0,\infty)\), because for \(x<0\) no real \(y\) has \(y^2=x<0\le y^2\).
\item With \(\mathbb{N}=\{0,1,2,\dots\}\), subtraction \((m,n)\mapsto m-n\) is a partial function \(\mathbb{N}\times\mathbb{N}\rightharpoonup\mathbb{N}\) with domain of definition \(\{(m,n)\mid n\le m\}\), since \(m-n\in\mathbb{N}\) exactly when \(n\le m\).
\item In computability theory, a program that reads a natural number and may or may not halt computes a partial function \(\mathbb{N}\rightharpoonup\mathbb{N}\), defined exactly at the inputs on which it halts. Here partial functions cannot be avoided: by the classical unsolvability of the halting problem, there is in general no program that decides whether a given input lies in the domain of definition, so one cannot simply restrict attention to total functions.
\end{itemize}
\end{example}

\begin{definition}
Let \(f\colon A\to B\) be a function.
\begin{enumerate}
\item For \(S\subseteq A\), the \emph{restriction} of \(f\) to \(S\) is the function \(f|_S\colon S\to B\) with graph \(f\cap(S\times B)\); thus \(f|_S(s)=f(s)\) for \(s\in S\).
\item If \(A\subseteq A'\), a function \(g\colon A'\to B\) with \(g|_A=f\) is called an \emph{extension} of \(f\) to \(A'\).
\end{enumerate}
\end{definition}

The restriction is indeed a function: \(f\cap(S\times B)\) is contained in \(S\times B\), is functional as a subset of \(f\), and contains \((s,f(s))\) for every \(s\in S\). The same formula restricts a partial function \(f\colon A\rightharpoonup B\) to a partial function \(S\rightharpoonup B\) with domain of definition \(S\cap\operatorname{dom}f\); in particular, part (1) of the last proposition says that the restriction of a partial function to its domain of definition is total.

\begin{proposition}
Let \(f\colon A\to B\) and \(g\colon A'\to B\) be functions with \(A\subseteq A'\). Then \(g\) is an extension of \(f\) if and only if \(f\subseteq g\) as graphs.
\end{proposition}

\begin{proof}
If \(g|_A=f\), then \(f=g\cap(A\times B)\subseteq g\). Conversely, let \(f\subseteq g\). Then \(f\subseteq g\cap(A\times B)\). For the reverse inclusion let \((a,b)\in g\) with \(a\in A\). Since \((a,f(a))\in f\subseteq g\) and \(g\) is functional, \(b=f(a)\), so \((a,b)\in f\). Hence \(g\cap(A\times B)=f\), that is, \(g|_A=f\).
\end{proof}

Thus a function extends another exactly when its graph is larger; see also \PMlinkname{subfunction}{Subfunction}.

\begin{definition}
Let \(A\) and \(B\) be sets.
\begin{enumerate}
\item The \emph{identity function} of \(A\) is \(\operatorname{id}_A\colon A\to A\), \(a\mapsto a\); its graph is the diagonal \(\Delta_A=\{(a,a)\mid a\in A\}\).
\item If \(S\subseteq A\), the \emph{inclusion map} \(\iota\colon S\hookrightarrow A\) is the function \(S\to A\), \(s\mapsto s\); its graph is \(\Delta_S\subseteq S\times A\).
\item For \(b\in B\), the \emph{constant function} with value \(b\) is \(A\to B\), \(a\mapsto b\); its graph is \(A\times\{b\}\).
\item The \emph{empty function} from \(\varnothing\) to \(B\) is \((\varnothing,B,\varnothing)\).
\end{enumerate}
\end{definition}

Each of the first three is a function by the first proposition, since the rule assigns one element of the codomain to each element of the domain.

\begin{proposition}
Let \(A\) and \(B\) be sets.
\begin{enumerate}
\item The empty function is the only function \(\varnothing\to B\).
\item If \(A\ne\varnothing\), there is no function \(A\to\varnothing\).
\end{enumerate}
\end{proposition}

\begin{proof}
\textit{(1)} The empty relation \(\varnothing\subseteq\varnothing\times B\) is functional, since the condition on pairs in it is vacuous, and \(\operatorname{dom}\varnothing=\varnothing\); so \((\varnothing,B,\varnothing)\) is a function. If \(f\colon\varnothing\to B\) is any function, then \(f\subseteq\varnothing\times B=\varnothing\), because there is no pair \((a,b)\) with \(a\in\varnothing\). Hence \(f\) has the empty graph and equals the empty function.

\textit{(2)} A function \(f\colon A\to\varnothing\) would satisfy \(f\subseteq A\times\varnothing=\varnothing\), so \(\operatorname{dom}f=\varnothing\ne A\), contradicting totality.
\end{proof}

In particular there is exactly one function \(\varnothing\to\varnothing\), namely \(\operatorname{id}_\varnothing\), the empty function.

For sets \(A\) and \(B\), let \(B^A\) denote the set of all functions \(A\to B\). It is a set: a function \(A\to B\) is determined by its graph, which is a subset of \(A\times B\), so \(B^A\) is in one-to-one correspondence with a set of subsets of \(A\times B\) (the functional, total ones).

\begin{proposition}
Let \(A\) and \(B\) be finite sets with \(m\) and \(n\) elements. Then \(B^A\) has \(n^m\) elements (with \(0^0=1\)), and there are exactly \((n+1)^m\) partial functions \(A\rightharpoonup B\).
\end{proposition}

\begin{proof}
We prove the first statement by \PMlinkname{induction}{PrincipleOfFiniteInduction} on \(m\), for fixed \(B\). If \(m=0\), then \(A=\varnothing\), and by the previous proposition there is exactly one function \(\varnothing\to B\); and \(n^0=1\).

Let \(m\ge0\), assume the statement for sets with \(m\) elements, and let \(A\) have \(m+1\) elements. Choose \(a_0\in A\) and put \(A'=A\setminus\{a_0\}\), a set with \(m\) elements. Consider the assignment
\[
F\colon B^A\to B^{A'}\times B,\qquad F(f)=(f|_{A'},f(a_0)).
\]
It is injective: if \(F(f)=F(g)\), then \(f(a)=g(a)\) for \(a\in A'\) and \(f(a_0)=g(a_0)\), so \(f=g\) by equality of functions. Every pair \((h,b)\in B^{A'}\times B\) is a value of \(F\): the relation \(h\cup\{(a_0,b)\}\subseteq A\times B\) pairs each element of \(A'\) with exactly one element (its value under \(h\), as \(a_0\notin A'\)) and \(a_0\) with exactly \(b\), so it is the graph of a function \(f\colon A\to B\), and \(F(f)=(h,b)\). Hence \(B^A\) has as many elements as \(B^{A'}\times B\), which by the induction hypothesis and the counting rule for Cartesian products is \(n^m\cdot n=n^{m+1}\).

For the second statement, part (2) of the proposition comparing partial and total functions gives a one-to-one correspondence between partial functions \(A\rightharpoonup B\) and functions \(A\to B_\ast\). Since \(\ast\notin B\), the set \(B_\ast\) has \(n+1\) elements, so by the first statement there are \((n+1)^m\) of them.
\end{proof}

\begin{example}
Let \(A=\{1,2,3\}\) and \(B=\{x,y\}\). The table
\begin{equation*}
\begin{array}{c|ccc}
a & 1 & 2 & 3\\
f(a) & x & y & x
\end{array}
\end{equation*}
defines a function \(f\colon A\to B\) with graph \(\{(1,x),(2,y),(3,x)\}\subseteq A\times B\). There are \(2^3=8\) functions \(A\to B\) and \(3^3=27\) partial functions \(A\rightharpoonup B\). For \(A=\{1\}\) and \(B=\{x\}\), the two partial functions are the empty one and \(\{(1,x)\}\), in accordance with \((1+1)^1=2\).
\end{example}

\begin{example}
The unit circle \(C=\{(x,y)\in\mathbb{R}\times\mathbb{R}\mid x^2+y^2=1\}\) is a relation from \(\mathbb{R}\) to \(\mathbb{R}\) that is not functional, since \((0,1)\in C\) and \((0,-1)\in C\). So \(C\) is not even a partial function from \(\mathbb{R}\) to \(\mathbb{R}\). By contrast, the relation \(\{(x,y)\in C\mid y\ge0\}\) is functional, because \(y\ge0\) and \(y^2=1-x^2\) determine \(y=\sqrt{1-x^2}\); it is a partial function with domain of definition \([-1,1]\), and it is not total.
\end{example}

\begin{remark}
The codomain is part of the data of a function. For instance, \(\operatorname{id}_{\mathbb{N}}\colon\mathbb{N}\to\mathbb{N}\) and the inclusion map \(\mathbb{N}\hookrightarrow\mathbb{Z}\) have the same graph \(\Delta_{\mathbb{N}}\) and the same domain, but they are different functions: every element of the codomain \(\mathbb{N}\) is a value of the first, whereas \(-1\) is not a value of the second. Properties such as being surjective depend on the codomain, which is why we keep it. Some authors instead identify a function with its graph, that is, a function is a functional relation and its domain is \(\operatorname{dom}f\); then the codomain is not determined by the function, and statements involving it must name it separately.
\end{remark}

\begin{remark}
The words ``map'' and ``mapping'' are used as synonyms of ``function''. Dropping the requirement that a relation be functional leads to \PMlinkname{multivalued functions}{MultivaluedFunction}, which assign to each input a set of outputs.
\end{remark}
""")


entry("image and inverse image", "image", ["03E20"],
      ["image", "images", "inverse image", "inverse images", "preimage", "preimages",
       "image of a function"],
      ["fibre of a function", "fiber of a function"],
      ["function", "set-operations"], r"""
A function sends points to points, and it is equally useful to know where it sends a whole subset of its domain, and which points it sends into a given subset of its codomain.

\begin{definition}
Let \(f\colon A\to B\) be a function.
\begin{enumerate}
\item For \(S\subseteq A\), the \emph{image} of \(S\) under \(f\) is
\[
f(S)=\{f(a)\mid a\in S\}=\{b\in B\mid b=f(a)\text{ for some }a\in S\}.
\]
The set \(f(A)\) is called the image of \(f\).
\item For \(T\subseteq B\), the \emph{inverse image} (or \emph{preimage}) of \(T\) under \(f\) is
\[
f^{-1}(T)=\{a\in A\mid f(a)\in T\}.
\]
\item For \(b\in B\), the set \(f^{-1}(\{b\})=\{a\in A\mid f(a)=b\}\) is the \emph{fibre} (also spelled fiber) of \(f\) over \(b\).
\end{enumerate}
\end{definition}

The image of \(f\) is the range of its graph: \(\operatorname{ran}f=\{b\mid (a,b)\in f\text{ for some }a\}=\{b\mid b=f(a)\text{ for some }a\in A\}=f(A)\). Directly from the definitions, \(f(\varnothing)=\varnothing\), \(f^{-1}(\varnothing)=\varnothing\) and \(f^{-1}(B)=A\); and for \(a\in A\) we have \(f(\{a\})=\{f(a)\}\).

\begin{remark}
The notation \(f^{-1}(T)\) is defined for every function \(f\), whether or not \(f\) has an inverse function; it does not presuppose that \(f\) can be inverted. When \(f\) is bijective, so that an inverse function \(B\to A\) exists, the set \(f^{-1}(T)\) also denotes the image of \(T\) under that inverse function, and the two readings give the same set; this is checked in the entry on bijective functions. Similarly, the notation \(f(S)\) is ambiguous in the rare case that \(S\) is both an element and a subset of \(A\); the context then has to say which is meant.
\end{remark}

For a partial function \(f\colon A\rightharpoonup B\), with \(S\subseteq A\) and \(T\subseteq B\), one uses only the points at which \(f\) is defined:
\[
f(S)=\{f(a)\mid a\in S\cap\operatorname{dom}f\},\qquad f^{-1}(T)=\{a\in\operatorname{dom}f\mid f(a)\in T\}.
\]
These are the image of \(S\cap\operatorname{dom}f\) and the inverse image of \(T\) under the total function \(\operatorname{dom}f\to B\) with the same graph, so the results below apply to them, with \(\operatorname{dom}f\) in place of \(A\) where \(A\) appears explicitly; for example \(f^{-1}(B)=\operatorname{dom}f\), and \(f^{-1}(B\setminus T)=\operatorname{dom}f\setminus f^{-1}(T)\).

\begin{proposition}
Let \(f\colon A\to B\) be a function, let \(S,S_1,S_2\subseteq A\) and \(T,T_1,T_2\subseteq B\), let \(\mathcal{S}\) be a set of subsets of \(A\), and let \(\mathcal{T}\) be a set of subsets of \(B\).
\begin{enumerate}
\item If \(S_1\subseteq S_2\), then \(f(S_1)\subseteq f(S_2)\). If \(T_1\subseteq T_2\), then \(f^{-1}(T_1)\subseteq f^{-1}(T_2)\).
\item \(f\bigl(\bigcup\mathcal{S}\bigr)=\bigcup\{f(S)\mid S\in\mathcal{S}\}\); in particular \(f(S_1\cup S_2)=f(S_1)\cup f(S_2)\).
\item \(f(S_1\cap S_2)\subseteq f(S_1)\cap f(S_2)\).
\item \(f^{-1}\bigl(\bigcup\mathcal{T}\bigr)=\bigcup\{f^{-1}(T)\mid T\in\mathcal{T}\}\), and if \(\mathcal{T}\ne\varnothing\), then \(f^{-1}\bigl(\bigcap\mathcal{T}\bigr)=\bigcap\{f^{-1}(T)\mid T\in\mathcal{T}\}\). In particular \(f^{-1}(T_1\cup T_2)=f^{-1}(T_1)\cup f^{-1}(T_2)\) and \(f^{-1}(T_1\cap T_2)=f^{-1}(T_1)\cap f^{-1}(T_2)\).
\item \(f^{-1}(T_1\setminus T_2)=f^{-1}(T_1)\setminus f^{-1}(T_2)\), and \(f^{-1}(B\setminus T)=A\setminus f^{-1}(T)\); that is, \(f^{-1}(T^{\complement})=f^{-1}(T)^{\complement}\), with complements taken in \(B\) and in \(A\) respectively.
\item \(S\subseteq f^{-1}(f(S))\).
\item \(f(f^{-1}(T))=T\cap f(A)\); in particular \(f(f^{-1}(T))\subseteq T\).
\end{enumerate}
\end{proposition}

\begin{proof}
\textit{(1)} If \(b\in f(S_1)\), then \(b=f(a)\) with \(a\in S_1\subseteq S_2\), so \(b\in f(S_2)\). If \(a\in f^{-1}(T_1)\), then \(f(a)\in T_1\subseteq T_2\), so \(a\in f^{-1}(T_2)\).

\textit{(2)} For \(b\in B\): \(b\in f(\bigcup\mathcal{S})\) if and only if \(b=f(a)\) for some \(a\) lying in some \(S\in\mathcal{S}\), if and only if there is \(S\in\mathcal{S}\) with \(b\in f(S)\), if and only if \(b\in\bigcup\{f(S)\mid S\in\mathcal{S}\}\). The particular case is \(\mathcal{S}=\{S_1,S_2\}\).

\textit{(3)} Since \(S_1\cap S_2\subseteq S_1\) and \(S_1\cap S_2\subseteq S_2\), part (1) gives \(f(S_1\cap S_2)\subseteq f(S_1)\) and \(f(S_1\cap S_2)\subseteq f(S_2)\).

\textit{(4)} For \(a\in A\): \(a\in f^{-1}(\bigcup\mathcal{T})\) if and only if \(f(a)\in T\) for some \(T\in\mathcal{T}\), if and only if \(a\in f^{-1}(T)\) for some \(T\in\mathcal{T}\). Likewise, for \(\mathcal{T}\ne\varnothing\), \(a\in f^{-1}(\bigcap\mathcal{T})\) if and only if \(f(a)\in T\) for every \(T\in\mathcal{T}\), if and only if \(a\in f^{-1}(T)\) for every \(T\in\mathcal{T}\). The particular cases are \(\mathcal{T}=\{T_1,T_2\}\).

\textit{(5)} For \(a\in A\): \(a\in f^{-1}(T_1\setminus T_2)\) if and only if \(f(a)\in T_1\) and \(f(a)\notin T_2\), if and only if \(a\in f^{-1}(T_1)\) and \(a\notin f^{-1}(T_2)\). Taking \(T_1=B\) and using \(f^{-1}(B)=A\) gives the statement on complements.

\textit{(6)} If \(a\in S\), then \(f(a)\in f(S)\), so \(a\in f^{-1}(f(S))\).

\textit{(7)} If \(b\in f(f^{-1}(T))\), then \(b=f(a)\) for some \(a\) with \(f(a)\in T\); so \(b\in T\), and \(b\in f(A)\). Conversely, if \(b\in T\cap f(A)\), write \(b=f(a)\) with \(a\in A\); then \(f(a)\in T\), so \(a\in f^{-1}(T)\) and \(b\in f(f^{-1}(T))\).
\end{proof}

So inverse images behave perfectly with respect to all the operations of the \PMlinkname{algebra of sets}{SetOperations}, while images preserve unions but in general not intersections or differences. A longer list of such rules is in \PMlinkname{properties of a function}{PropertiesOfAFunction}.

\begin{proposition}
Let \(f\colon A\to B\) be a function. The fibres of \(f\) over the points of \(f(A)\) form a \PMlinkname{partition}{Partition} of \(A\); that is, the set \(\{f^{-1}(\{b\})\mid b\in f(A)\}\) is a partition of \(A\). For \(b\in B\setminus f(A)\) the fibre over \(b\) is empty.
\end{proposition}

\begin{proof}
Each fibre is a subset of \(A\). If \(b\in f(A)\), then \(b=f(a)\) for some \(a\in A\), and \(a\in f^{-1}(\{b\})\), so the fibre is nonempty. Every \(a\in A\) lies in the fibre over \(f(a)\in f(A)\), so the union of the fibres is \(A\). Let \(b,b'\in f(A)\) be such that the fibres over \(b\) and \(b'\) are distinct; then \(b\ne b'\), and if some \(a\) lay in both fibres, we would have \(b=f(a)=b'\). So distinct fibres are disjoint. Finally, if \(b\notin f(A)\), no \(a\in A\) has \(f(a)=b\), so the fibre over \(b\) is empty.
\end{proof}

The corresponding \PMlinkname{equivalence relation}{EquivalenceRelation} on \(A\) is ``\(a\) and \(a'\) have the same value'', that is, \(f(a)=f(a')\), and the blocks of the partition are its equivalence classes.

\begin{example}
Let \(f\colon\mathbb{R}\to\mathbb{R}\), \(f(x)=x^2\).
\begin{itemize}
\item \(f([-1,2])=[0,4]\). If \(-1\le x\le2\), then \(\abs{x}\le2\), so \(0\le x^2\le4\). Conversely, if \(0\le y\le4\), then \(x=\sqrt{y}\) satisfies \(0\le x\le2\), so \(x\in[-1,2]\) and \(f(x)=y\).
\item \(f^{-1}([1,4])=[-2,-1]\cup[1,2]\). For real \(x\), \(1\le x^2\le4\) holds if and only if \(1\le\abs{x}\le2\), because \(\abs{x}=\sqrt{x^2}\) and, for \(s,t\ge0\), \(s\le t\) holds if and only if \(s^2\le t^2\); and \(1\le\abs{x}\le2\) means \(x\in[1,2]\) or \(x\in[-2,-1]\).
\item \(f^{-1}(\{-1\})=\varnothing\), since \(x^2\ge0>-1\) for every real \(x\). The fibre over \(4\) is \(\{-2,2\}\), and the fibre over \(0\) is \(\{0\}\). The image of \(f\) is \([0,\infty)\): each \(x^2\) is \(\ge0\), and each \(y\ge0\) equals \(f(\sqrt{y})\).
\item The inclusion in part (3) of the proposition can be strict: with \(S_1=[-1,0]\) and \(S_2=[0,1]\) we get \(f(S_1\cap S_2)=f(\{0\})=\{0\}\), whereas \(f(S_1)=f(S_2)=[0,1]\) (by the same argument as in the first item), so \(f(S_1)\cap f(S_2)=[0,1]\).
\item The inclusion in part (6) can be strict: \(f([0,1])=[0,1]\) and \(f^{-1}([0,1])=\{x\mid x^2\le1\}=[-1,1]\), which is strictly larger than \([0,1]\).
\item The inclusion \(f(f^{-1}(T))\subseteq T\) can be strict: for \(T=[-1,1]\), \(f^{-1}(T)=\{x\mid x^2\le1\}=[-1,1]\) and \(f([-1,1])=[0,1]\ne T\). In agreement with part (7), \(T\cap f(\mathbb{R})=[-1,1]\cap[0,\infty)=[0,1]\).
\end{itemize}
\end{example}

\begin{example}
For a constant function \(c\colon A\to B\) with value \(b_0\) and \(A\ne\varnothing\), the image of \(c\) is \(\{b_0\}\), the fibre over \(b_0\) is \(A\), and for \(T\subseteq B\) we have \(c^{-1}(T)=A\) if \(b_0\in T\) and \(c^{-1}(T)=\varnothing\) otherwise. For the inclusion map \(\iota\colon S\hookrightarrow A\) of a subset \(S\subseteq A\), \(\iota^{-1}(T)=S\cap T\) for every \(T\subseteq A\), because \(\iota(s)=s\).
\end{example}
""")


entry("composition of functions", "composition-of-functions", ["03E20"],
      ["composition", "functional composition", "function composition", "composite function",
       "composite of functions"],
      [],
      ["function", "image", "operations-on-relations"], r"""
Applying one function and then another to the result is the most basic way of building new functions from old ones.

\begin{definition}
Let \(f\colon A\to B\) and \(g\colon B\to C\) be functions. The \emph{composition} (or composite) of \(f\) and \(g\) is the function
\[
g\circ f\colon A\to C,\qquad (g\circ f)(a)=g(f(a)).
\]
\end{definition}

This is a function, since for each \(a\in A\) the rule gives exactly one element \(g(f(a))\) of \(C\). Note the order: \(g\circ f\) means ``first \(f\), then \(g\)''. The composite is defined when the codomain of \(f\) is the domain of \(g\).

The graph of \(g\circ f\) is obtained from the graphs of \(f\) and \(g\) by composing relations. For relations \(R\subseteq A\times B\) and \(S\subseteq B\times C\) we use the convention
\[
S\circ R=\{(a,c)\in A\times C\mid aRb\text{ and }bSc\text{ for some }b\in B\},
\]
``first \(R\), then \(S\)'', which matches the order in \(g\circ f\). (The entry \PMlinkname{operations on relations}{OperationsOnRelations} writes composites of relations in the opposite order.)

\begin{proposition}
Let \(f\colon A\to B\) and \(g\colon B\to C\) be functions. Then the graph of \(g\circ f\) is the relational composite \(g\circ f\) of the graphs of \(f\) and \(g\).
\end{proposition}

\begin{proof}
The graph of the function \(g\circ f\) is \(\{(a,g(f(a)))\mid a\in A\}\). Each such pair lies in the relational composite, with \(b=f(a)\): indeed \((a,f(a))\in f\) and \((f(a),g(f(a)))\in g\). Conversely, if \((a,b)\in f\) and \((b,c)\in g\), then \(b=f(a)\) and \(c=g(b)=g(f(a))\), so \((a,c)\) lies in the graph of the function \(g\circ f\).
\end{proof}

\begin{remark}
The requirement that the codomain of \(f\) equal the domain of \(g\) can be relaxed. If \(f\colon A\to B\) and \(g\colon B'\to C\) with \(f(A)\subseteq B'\) (see \PMlinkname{image}{Image}), then the triple \((A,B',f)\) is a function \(A\to B'\): its graph \(f\) lies in \(A\times B'\) because all values are in \(f(A)\subseteq B'\), and it is functional and total because \((A,B,f)\) is. Composing this function with \(g\) gives a function \(A\to C\) with values \(g(f(a))\), which is also written \(g\circ f\). The change of codomain is harmless here, but it is a change, since the codomain is part of the data of a function.
\end{remark}

\begin{theorem}
Let \(f\colon A\to B\), \(g\colon B\to C\) and \(h\colon C\to D\) be functions.
\begin{enumerate}
\item \textit{(Associativity)} \(h\circ(g\circ f)=(h\circ g)\circ f\).
\item \textit{(Identity laws)} \(\operatorname{id}_B\circ f=f=f\circ\operatorname{id}_A\).
\end{enumerate}
\end{theorem}

\begin{proof}
We use that two functions are equal if and only if they have the same domain, the same codomain and the same values.

\textit{(1)} Both sides are defined: \(g\circ f\colon A\to C\) can be followed by \(h\), and \(f\) can be followed by \(h\circ g\colon B\to D\). Both have domain \(A\) and codomain \(D\). For \(a\in A\),
\[
(h\circ(g\circ f))(a)=h((g\circ f)(a))=h(g(f(a)))=(h\circ g)(f(a))=((h\circ g)\circ f)(a).
\]

\textit{(2)} All three functions have domain \(A\) and codomain \(B\), and for \(a\in A\) we have \((\operatorname{id}_B\circ f)(a)=f(a)\) and \((f\circ\operatorname{id}_A)(a)=f(a)\).
\end{proof}

Because of associativity, parentheses may be omitted, and one writes \(h\circ g\circ f\).

\begin{example}
Composition is not commutative. Let \(f,g\colon\mathbb{R}\to\mathbb{R}\) be \(f(x)=x+1\) and \(g(x)=x^2\). Then \((g\circ f)(x)=(x+1)^2\) and \((f\circ g)(x)=x^2+1\); at \(x=1\) these are \(4\) and \(2\), so \(g\circ f\ne f\circ g\). Moreover, one composite may be defined when the other is not: for \(f\colon A\to B\) and \(g\colon B\to C\) the composite \(f\circ g\) only makes sense when \(C=A\).
\end{example}

\begin{proposition}
Let \(f\colon A\to B\) and \(g\colon B\to C\) be functions, \(S\subseteq A\) and \(U\subseteq C\). Then
\[
(g\circ f)(S)=g(f(S))\quad\text{and}\quad (g\circ f)^{-1}(U)=f^{-1}(g^{-1}(U)).
\]
\end{proposition}

\begin{proof}
For \(c\in C\): \(c\in(g\circ f)(S)\) if and only if \(c=g(f(a))\) for some \(a\in S\). If this holds, then \(b=f(a)\in f(S)\) and \(c=g(b)\), so \(c\in g(f(S))\). Conversely, if \(c\in g(f(S))\), then \(c=g(b)\) for some \(b\in f(S)\), and \(b=f(a)\) for some \(a\in S\), so \(c=g(f(a))\in(g\circ f)(S)\).

For \(a\in A\): \(a\in(g\circ f)^{-1}(U)\) if and only if \(g(f(a))\in U\), if and only if \(f(a)\in g^{-1}(U)\), if and only if \(a\in f^{-1}(g^{-1}(U))\).
\end{proof}

For partial functions \(f\colon A\rightharpoonup B\) and \(g\colon B\rightharpoonup C\), the composite \(g\circ f\colon A\rightharpoonup C\) is defined to have as graph the relational composite of the graphs. A value \(g(f(a))\) exists exactly when \(f\) is defined at \(a\) and \(g\) is defined at \(f(a)\).

\begin{proposition}
Let \(f\colon A\rightharpoonup B\) and \(g\colon B\rightharpoonup C\) be partial functions.
\begin{enumerate}
\item The relation \(g\circ f\subseteq A\times C\) is functional, so \(g\circ f\colon A\rightharpoonup C\) is a partial function.
\item Its domain of definition is
\[
\operatorname{dom}(g\circ f)=\{a\in\operatorname{dom}f\mid f(a)\in\operatorname{dom}g\}=f^{-1}(\operatorname{dom}g),
\]
and \((g\circ f)(a)=g(f(a))\) for \(a\) in this set.
\item If \(f\) and \(g\) are total, then \(g\circ f\) is the composite of functions defined above.
\end{enumerate}
\end{proposition}

\begin{proof}
\textit{(1)} Let \((a,c)\) and \((a,c')\) be in \(g\circ f\), say \((a,b),(b,c)\) and \((a,b'),(b',c')\) in the respective graphs. Since \(f\) is functional, \(b=b'\); since \(g\) is functional, \(c=c'\).

\textit{(2)} If \(a\in\operatorname{dom}(g\circ f)\), there are \(b,c\) with \((a,b)\in f\) and \((b,c)\in g\); thus \(a\in\operatorname{dom}f\), \(b=f(a)\), \(f(a)\in\operatorname{dom}g\) and \(c=g(f(a))\). Conversely, if \(a\in\operatorname{dom}f\) and \(f(a)\in\operatorname{dom}g\), then \((a,f(a))\in f\) and \((f(a),g(f(a)))\in g\), so \((a,g(f(a)))\in g\circ f\). The second description of the set is the definition of the inverse image of \(\operatorname{dom}g\) under the partial function \(f\).

\textit{(3)} This is the proposition above on graphs of composites.
\end{proof}

For example, if \(f\colon\mathbb{R}\rightharpoonup\mathbb{R}\) is \(x\mapsto x-1\) (defined everywhere) and \(g\colon\mathbb{R}\rightharpoonup\mathbb{R}\) is \(y\mapsto\sqrt{y}\) (defined on \([0,\infty)\)), then \(g\circ f\) is \(x\mapsto\sqrt{x-1}\) with domain of definition \(f^{-1}([0,\infty))=[1,\infty)\).

\begin{proposition}
Composition of relations is associative: for \(R\subseteq A\times B\), \(S\subseteq B\times C\) and \(T\subseteq C\times D\),
\[
T\circ(S\circ R)=(T\circ S)\circ R=\{(a,d)\mid aRb,\ bSc,\ cTd\text{ for some }b\in B,\ c\in C\}.
\]
Consequently, composition of partial functions is associative, and the identity laws \(\operatorname{id}_B\circ f=f=f\circ\operatorname{id}_A\) hold for every partial function \(f\colon A\rightharpoonup B\).
\end{proposition}

\begin{proof}
Let \(W\) denote the set on the right. A pair \((a,d)\) lies in \(T\circ(S\circ R)\) if and only if there is \(c\) with \((a,c)\in S\circ R\) and \(cTd\), that is, if and only if there are \(c\) and \(b\) with \(aRb\), \(bSc\) and \(cTd\); so \(T\circ(S\circ R)=W\). Similarly \((a,d)\in(T\circ S)\circ R\) if and only if there is \(b\) with \(aRb\) and \((b,d)\in T\circ S\), that is, there are \(b\) and \(c\) with \(aRb\), \(bSc\) and \(cTd\); so \((T\circ S)\circ R=W\).

For partial functions \(f\colon A\rightharpoonup B\), \(g\colon B\rightharpoonup C\), \(h\colon C\rightharpoonup D\), both \(h\circ(g\circ f)\) and \((h\circ g)\circ f\) are partial functions from \(A\) to \(D\) whose graphs are the two sides of the identity just proved, so they are equal. For the identity laws: \((a,b)\in\operatorname{id}_B\circ f\) if and only if \((a,b')\in f\) and \(b'=b\) for some \(b'\), that is, \((a,b)\in f\); and \((a,b)\in f\circ\operatorname{id}_A\) if and only if \(a'=a\) and \((a',b)\in f\) for some \(a'\in A\), that is, \((a,b)\in f\).
\end{proof}

Since the graph of a composite of functions is the relational composite, this gives a second proof of the associativity of composition of functions: both \(h\circ(g\circ f)\) and \((h\circ g)\circ f\) have domain \(A\), codomain \(D\) and graph \(W\).

\begin{definition}
Let \(f\colon A\to A\) be a function. Its iterates \(f^n\colon A\to A\), for \(n\in\mathbb{N}=\{0,1,2,\dots\}\), are defined by \(f^0=\operatorname{id}_A\) and \(f^{n+1}=f\circ f^n\).
\end{definition}

Thus \(f^1=f\), \(f^2=f\circ f\), and \(f^n(a)\) is obtained from \(a\) by applying \(f\) \(n\) times.

\begin{proposition}
Let \(f\colon A\to A\) be a function. Then \(f^m\circ f^n=f^{m+n}\) for all \(m,n\in\mathbb{N}\). In particular \(f^m\circ f^n=f^n\circ f^m\).
\end{proposition}

\begin{proof}
Fix \(n\) and use \PMlinkname{induction}{PrincipleOfFiniteInduction} on \(m\). For \(m=0\), \(f^0\circ f^n=\operatorname{id}_A\circ f^n=f^n\) by the identity law. If \(f^m\circ f^n=f^{m+n}\), then, by associativity,
\[
f^{m+1}\circ f^n=(f\circ f^m)\circ f^n=f\circ(f^m\circ f^n)=f\circ f^{m+n}=f^{m+n+1}.
\]
The last statement follows since \(m+n=n+m\).
\end{proof}

\begin{example}
Let \(s\colon\mathbb{N}\to\mathbb{N}\), \(s(k)=k+1\). Then \(s^n(k)=k+n\) for all \(n,k\in\mathbb{N}\): this holds for \(n=0\), and if \(s^n(k)=k+n\), then \(s^{n+1}(k)=s(s^n(k))=k+n+1\).
\end{example}

\begin{remark}
The notation \(f^n\) for iterates must not be confused with other uses: \(f^{-1}\) denotes an inverse function or, applied to a subset, an inverse image, and in analysis \(\sin^2x\) usually means \((\sin x)^2\), not \(\sin(\sin x)\).
\end{remark}

\begin{remark}
For a set \(A\), the set \(A^A\) of all functions \(A\to A\) is closed under composition, composition is associative on it, and \(\operatorname{id}_A\) is a two-sided identity element. In algebraic language, \(A^A\) is a monoid under composition. It is not commutative as soon as \(A\) has at least two elements: for distinct \(a,b\in A\), the constant functions \(c_a\) and \(c_b\) with values \(a\) and \(b\) satisfy \(c_a\circ c_b=c_a\ne c_b=c_b\circ c_a\).
\end{remark}
""")

# Part 6 of the naive set theory entries: entries 14 (injective function), 15 (surjective
# function), 16 (bijective function), in global order.
#
# Ordinary English words in these bodies that might be mis-autolinked to unrelated entries:
# domain, range, value, values, graph, identity, inverse, converse, image, element, order,
# ordered, total, totally, finite, restriction, constant, product, projection, floor, class,
# residue, choice, axiom, group, symmetric (in "symmetric group"), monoid, cancel, cancellable,
# least, set, family, power, pair, step, case, number, enumeration, listing, table, exp, log,
# pigeonhole, square, root, successor.
#
# Notes for the assembler / reviewer:
# - Titles, slugs, codes, synonyms, defined terms and related slugs are exactly as in SPEC.md.
# - Explicit links point only to existing entries (PropertiesOfAFunction, SurjectionAndAxiomOfChoice,
#   IntegersModuloN, PropertiesOfBijections) or to earlier new entries (Function, Image,
#   CompositionOfFunctions, TotalOrder, CartesianProduct, InjectiveFunction, SurjectiveFunction).
# - Entry 14 speaks of one-to-one correspondences only in plain words (bijections come in entry 16);
#   the synonym "one-to-one correspondence" of entry 16 may still autolink there, which is the
#   intended meaning.
# - Entry 15 builds the {0,1}-valued functions for right cancellation inline (indicator functions
#   come later, entry 19).
# - Entry 16 mentions the name "symmetric group"; if an entry with that title exists the longer
#   phrase wins, otherwise "symmetric" would link to the symmetric relation entry and should be
#   escaped.
# - "Number of elements" of a finite set is used informally (a set with n elements is one that can
#   be listed as a_1, ..., a_n without repetition); removing one element from a set with n >= 1
#   elements leaves n - 1 elements. This is the level of the counting results in entries 3, 4, 11.


entry("injective function", "injective-function", ["03E20"],
      ["injective", "injection", "injections", "injectivity", "one-to-one function",
       "injective functions", "injective map"],
      ["left inverse of a function"],
      ["function", "composition-of-functions", "image"], r"""
A function that never sends two different inputs to the same output loses no information, so its input can be recovered from its output; such functions are called injective.

Throughout, functions are total \PMlinkname{functions}{Function} \(f\colon A\to B\), with domain \(A\) and codomain \(B\); \(f(S)\) is the image of \(S\subseteq A\), \(f^{-1}(T)\) the inverse image of \(T\subseteq B\), and \(f^{-1}(\{b\})\) the fibre of \(f\) over \(b\in B\).

\begin{definition}
A function \(f\colon A\to B\) is \emph{injective}, or an \emph{injection}, if for all \(a,a'\in A\),
\[
f(a)=f(a')\ \text{implies}\ a=a'.
\]
A function \(g\colon B\to A\) is a \emph{left inverse} of \(f\) if \(g\circ f=\operatorname{id}_A\), that is, \(g(f(a))=a\) for every \(a\in A\).
\end{definition}

\begin{proposition}
For a function \(f\colon A\to B\) the following are equivalent:
\begin{enumerate}
\item \(f\) is injective;
\item for all \(a,a'\in A\), if \(a\ne a'\) then \(f(a)\ne f(a')\);
\item every fibre \(f^{-1}(\{b\})\), \(b\in B\), has at most one element.
\end{enumerate}
\end{proposition}

\begin{proof}
Condition (2) is the contrapositive of the implication in (1), so (1) and (2) are equivalent. Assume (1), let \(b\in B\) and let \(a,a'\in f^{-1}(\{b\})\). Then \(f(a)=b=f(a')\), so \(a=a'\); this is (3). Conversely, assume (3) and let \(f(a)=f(a')=b\). Then \(a\) and \(a'\) both lie in \(f^{-1}(\{b\})\), which has at most one element, so \(a=a'\).
\end{proof}

\begin{proposition}
Let \(f\colon A\to B\) and \(g\colon B\to C\) be functions.
\begin{enumerate}
\item If \(f\) and \(g\) are injective, then \(g\circ f\) is injective.
\item If \(g\circ f\) is injective, then \(f\) is injective.
\item If \(f\) is injective and \(S\subseteq A\), then the restriction \(f|_S\colon S\to B\) is injective.
\end{enumerate}
\end{proposition}

\begin{proof}
\textit{(1)} If \(g(f(a))=g(f(a'))\), then \(f(a)=f(a')\) because \(g\) is injective, and then \(a=a'\) because \(f\) is injective.

\textit{(2)} If \(f(a)=f(a')\), then \(g(f(a))=g(f(a'))\), so \(a=a'\) because \(g\circ f\) is injective.

\textit{(3)} If \(s,s'\in S\) and \(f|_S(s)=f|_S(s')\), then \(f(s)=f(s')\), so \(s=s'\).
\end{proof}

In (2), \(g\) need not be injective: take \(A=C=\{0\}\), \(B=\{0,1\}\), \(f(0)=0\) and \(g\) the constant function with value \(0\). Then \(g\circ f=\operatorname{id}_{\{0\}}\) is injective, but \(g(0)=g(1)\).

\begin{theorem}
Let \(f\colon A\to B\) be a function.
\begin{enumerate}
\item If \(f\) has a left inverse, then \(f\) is injective.
\item If \(f\) is injective and \(A\ne\varnothing\), then \(f\) has a left inverse.
\end{enumerate}
\end{theorem}

\begin{proof}
\textit{(1)} Let \(g\circ f=\operatorname{id}_A\). If \(f(a)=f(a')\), then \(a=g(f(a))=g(f(a'))=a'\).

\textit{(2)} Fix an element \(a_0\in A\). For \(b\in f(A)\) the fibre \(f^{-1}(\{b\})\) is nonempty, and it has at most one element by the previous proposition, so it consists of exactly one element; call it \(a_b\). Define \(g\colon B\to A\) by
\begin{equation*}
g(b)=\begin{cases} a_b & \text{if } b\in f(A),\\ a_0 & \text{if } b\notin f(A).\end{cases}
\end{equation*}
Each \(b\in B\) receives exactly one value, so \(g\) is a function. For \(a\in A\), the element \(b=f(a)\) lies in \(f(A)\) and \(a\in f^{-1}(\{b\})\), so \(a_b=a\), that is, \(g(f(a))=a\). Hence \(g\circ f=\operatorname{id}_A\).
\end{proof}

The construction in (2) makes only one choice, of the fixed element \(a_0\), so it does not use the axiom of choice. The hypothesis \(A\ne\varnothing\) is needed: the empty function \(\varnothing\to B\) is injective (the condition is vacuous), but if \(B\ne\varnothing\) there is no function \(B\to\varnothing\) at all, hence no left inverse. A left inverse is in general not unique, since the value \(a_0\) on \(B\setminus f(A)\) is arbitrary.

\begin{proposition}
For a function \(f\colon A\to B\) the following are equivalent:
\begin{enumerate}
\item \(f\) is injective;
\item \(f\) is left cancellable: for every set \(C\) and all functions \(g,h\colon C\to A\), \(f\circ g=f\circ h\) implies \(g=h\);
\item \(f^{-1}(f(S))=S\) for every \(S\subseteq A\);
\item \(f(S\cap T)=f(S)\cap f(T)\) for all \(S,T\subseteq A\).
\end{enumerate}
\end{proposition}

\begin{proof}
\textit{(1) implies (2).} Let \(f\circ g=f\circ h\) with \(g,h\colon C\to A\). For each \(c\in C\), \(f(g(c))=f(h(c))\), hence \(g(c)=h(c)\). Since \(g\) and \(h\) also have the same domain and codomain, \(g=h\).

\textit{(2) implies (1).} Let \(f(a)=f(a')\). Take a one-element set \(C=\{\ast\}\) and define \(g,h\colon C\to A\) by \(g(\ast)=a\), \(h(\ast)=a'\). Then \((f\circ g)(\ast)=f(a)=f(a')=(f\circ h)(\ast)\), so \(f\circ g=f\circ h\), hence \(g=h\) and \(a=g(\ast)=h(\ast)=a'\).

\textit{(1) implies (3).} If \(a\in S\), then \(f(a)\in f(S)\), so \(a\in f^{-1}(f(S))\). Conversely, if \(a\in f^{-1}(f(S))\), then \(f(a)\in f(S)\), so \(f(a)=f(s)\) for some \(s\in S\), and \(a=s\in S\) by injectivity.

\textit{(3) implies (1).} Let \(f(a)=f(a')\). Then \(a'\in f^{-1}(\{f(a)\})=f^{-1}(f(\{a\}))=\{a\}\), so \(a'=a\).

\textit{(1) implies (4).} Since \(S\cap T\) is contained in \(S\) and in \(T\), we have \(f(S\cap T)\subseteq f(S)\cap f(T)\). Conversely, if \(b\in f(S)\cap f(T)\), then \(b=f(s)=f(t)\) with \(s\in S\), \(t\in T\); injectivity gives \(s=t\in S\cap T\), so \(b\in f(S\cap T)\).

\textit{(4) implies (1).} Let \(f(a)=f(a')\) and put \(S=\{a\}\), \(T=\{a'\}\). Then \(f(S)\cap f(T)=\{f(a)\}\ne\varnothing\), so \(f(S\cap T)\ne\varnothing\), hence \(S\cap T\ne\varnothing\), which means \(a=a'\).
\end{proof}

For a general function only the inclusions \(S\subseteq f^{-1}(f(S))\) and \(f(S\cap T)\subseteq f(S)\cap f(T)\) hold; see \PMlinkname{image and inverse image}{Image} and \PMlinkname{properties of a function}{PropertiesOfAFunction}.

If \(f\colon A\to B\) is injective, the function \(A\to f(A)\), \(a\mapsto f(a)\), which has the same graph as \(f\) but codomain \(f(A)\), is again injective, and every element of \(f(A)\) is one of its values. It is therefore a one-to-one correspondence between \(A\) and \(f(A)\), with inverse \(f(A)\to A\), \(b\mapsto a_b\), in the notation of the theorem. In this sense an injection identifies \(A\) with the subset \(f(A)\) of \(B\).

\begin{theorem}
Let \(A\) be a set with \(m\) elements and \(B\) a set with \(n\) elements, where \(m,n\in\mathbb{N}=\{0,1,2,\dots\}\). There is an injective function \(A\to B\) if and only if \(m\le n\).
\end{theorem}

\begin{proof}
\textit{If.} List the elements without repetition, \(A=\{a_1,\dots,a_m\}\) and \(B=\{b_1,\dots,b_n\}\). Since \(m\le n\), we may define \(f\colon A\to B\) by \(f(a_i)=b_i\) for \(i=1,\dots,m\). If \(f(a_i)=f(a_j)\), then \(b_i=b_j\), so \(i=j\) and \(a_i=a_j\).

\textit{Only if.} We prove by induction on \(n\) that, for every \(m\), every set \(A\) with \(m\) elements and every set \(B\) with \(n\) elements, the existence of an injection \(f\colon A\to B\) implies \(m\le n\). If \(n=0\), then \(B=\varnothing\); a function \(A\to\varnothing\) can exist only if \(A=\varnothing\), because an element \(a\in A\) would need a value \(f(a)\in\varnothing\). So \(m=0\le n\).

Let \(n\ge0\), assume the statement for \(n\), and let \(f\colon A\to B\) be injective, where \(B\) has \(n+1\) elements. If \(m=0\), then \(m\le n+1\). Otherwise choose \(a\in A\) and put \(b=f(a)\). For \(a'\in A\setminus\{a\}\) we have \(f(a')\ne b\) by injectivity, so \(a'\mapsto f(a')\) is a function \(A\setminus\{a\}\to B\setminus\{b\}\), and it is injective because its values are those of \(f\). The set \(A\setminus\{a\}\) has \(m-1\) elements and \(B\setminus\{b\}\) has \(n\), so the induction hypothesis gives \(m-1\le n\), that is, \(m\le n+1\).
\end{proof}

Read contrapositively, this is the pigeonhole principle: if \(m>n\), then every function from a set with \(m\) elements to a set with \(n\) elements takes the same value at two distinct elements.

\begin{example}
\begin{enumerate}
\item For \(S\subseteq A\), the inclusion map \(S\to A\), \(s\mapsto s\), is injective, since \(s=s'\) is exactly what has to be shown. In particular \(\operatorname{id}_A\) is injective.
\item The function \(\mathbb{Z}\to\mathbb{Z}\), \(x\mapsto 2x\), is injective: \(2x=2x'\) gives \(x=x'\) after dividing by \(2\).
\item The function \(\mathbb{R}\to\mathbb{R}\), \(x\mapsto x^2\), is not injective, since \((-1)^2=1^2\) and \(-1\ne1\). Its restriction to \([0,\infty)\) is injective: if \(x,y\ge0\) and \(x^2=y^2\), then \((x-y)(x+y)=0\); if \(x+y=0\), then \(x=y=0\) because both are nonnegative, and otherwise \(x-y=0\). In either case \(x=y\).
\item Let \(P\) be a \PMlinkname{totally ordered set}{TotalOrder}, let \(Q\) be a partially ordered set, and let \(f\colon P\to Q\) be strictly increasing, that is, \(a<a'\) implies \(f(a)<f(a')\). Then \(f\) is injective. Indeed, if \(a\ne a'\), then \(a<a'\) or \(a'<a\) because the order of \(P\) is total, so \(f(a)<f(a')\) or \(f(a')<f(a)\); in both cases \(f(a)\ne f(a')\), since \(x<y\) means \(x\le y\) and \(x\ne y\).
\end{enumerate}
\end{example}

\begin{remark}
Injective functions are also called one-to-one functions. Since ``one-to-one correspondence'' is used for a function that is both injective and onto its codomain, the word ``injective'' avoids an ambiguity. The definition applies verbatim to a partial function \(f\colon A\rightharpoonup B\), with \(a,a'\) ranging over its domain of definition.
\end{remark}
""")


entry("surjective function", "surjective-function", ["03E20", "03E25"],
      ["surjective", "surjection", "surjections", "surjectivity", "onto function",
       "surjective functions", "surjective map"],
      ["right inverse of a function"],
      ["function", "composition-of-functions", "image", "injective-function",
       "surjection-and-axiom-of-choice"], r"""
A function whose values exhaust its codomain allows every element of the codomain to be written as a value, so that the codomain is described entirely by the domain; such functions are called surjective.

Throughout, \(f\colon A\to B\) is a \PMlinkname{function}{Function} with domain \(A\) and codomain \(B\); \(f(S)\) and \(f^{-1}(T)\) denote \PMlinkname{image and inverse image}{Image}.

\begin{definition}
A function \(f\colon A\to B\) is \emph{surjective}, or a \emph{surjection}, or \(f\) maps \(A\) onto \(B\), if \(f(A)=B\), that is, if for every \(b\in B\) there is \(a\in A\) with \(f(a)=b\). A function \(h\colon B\to A\) is a \emph{right inverse} of \(f\) if \(f\circ h=\operatorname{id}_B\), that is, \(f(h(b))=b\) for every \(b\in B\).
\end{definition}

Since \(f(A)\subseteq B\) always holds, \(f\) is surjective if and only if \(B\subseteq f(A)\). Equivalently, \(f\) is surjective if and only if every fibre \(f^{-1}(\{b\})\), \(b\in B\), is nonempty, because \(a\in f^{-1}(\{b\})\) means exactly \(f(a)=b\).

Surjectivity depends on the codomain, which is part of the data of a function. The function \(\mathbb{R}\to\mathbb{R}\), \(x\mapsto x^2\), is not surjective, since \(x^2\ge0>-1\) for all real \(x\); the function \(\mathbb{R}\to[0,\infty)\), \(x\mapsto x^2\), with the same graph, is surjective, since \(y=(\sqrt{y})^2\) for \(y\ge0\). In general, every function \(f\colon A\to B\) gives a surjective function \(A\to f(A)\), \(a\mapsto f(a)\), with the same graph.

\begin{proposition}
Let \(f\colon A\to B\) and \(g\colon B\to C\) be functions.
\begin{enumerate}
\item If \(f\) and \(g\) are surjective, then \(g\circ f\) is surjective.
\item If \(g\circ f\) is surjective, then \(g\) is surjective.
\end{enumerate}
\end{proposition}

\begin{proof}
\textit{(1)} Let \(c\in C\). Since \(g\) is surjective, \(c=g(b)\) for some \(b\in B\), and since \(f\) is surjective, \(b=f(a)\) for some \(a\in A\). Then \(c=g(f(a))=(g\circ f)(a)\).

\textit{(2)} Let \(c\in C\). Then \(c=g(f(a))\) for some \(a\in A\), so \(c=g(b)\) with \(b=f(a)\in B\).
\end{proof}

In (2), \(f\) need not be surjective: take \(A=C=\{0\}\), \(B=\{0,1\}\), \(f(0)=0\) and \(g\) the constant function with value \(0\). Then \(g\circ f=\operatorname{id}_{\{0\}}\) is surjective, but \(1\notin f(A)\).

\begin{proposition}
Let \(f\colon A\to B\) be a function.
\begin{enumerate}
\item If \(f\) has a right inverse \(h\), then \(f\) is surjective and \(h\) is injective.
\item If \(f\) is surjective and \(A\subseteq\mathbb{N}=\{0,1,2,\dots\}\), then \(f\) has a right inverse.
\item If \(f\) is surjective and \(B\) is finite, then \(f\) has a right inverse.
\end{enumerate}
\end{proposition}

\begin{proof}
\textit{(1)} For \(b\in B\) we have \(b=f(h(b))\), so \(b\in f(A)\). If \(h(b)=h(b')\), then \(b=f(h(b))=f(h(b'))=b'\); so \(h\) is injective (it has the left inverse \(f\)).

\textit{(2)} For \(b\in B\) the fibre \(f^{-1}(\{b\})\) is a nonempty subset of \(\mathbb{N}\), so it has a least element; let \(h(b)\) be this least element. Then \(h\colon B\to A\) is a function, and \(f(h(b))=b\) because \(h(b)\in f^{-1}(\{b\})\).

\textit{(3)} We use induction on the number \(n\) of elements of \(B\), for all sets \(A\) and all surjections \(A\to B\) at once. If \(n=0\), then \(B=\varnothing\), and since there is no function from a nonempty set to \(\varnothing\), also \(A=\varnothing\); the empty function \(h\colon\varnothing\to\varnothing\) satisfies \(f\circ h=\operatorname{id}_\varnothing\), as both are the empty function \(\varnothing\to\varnothing\). Now let \(B\) have \(n+1\) elements and assume the claim for sets with \(n\) elements. Pick \(b_0\in B\) and an element \(a_0\in f^{-1}(\{b_0\})\), which is nonempty. Put \(B'=B\setminus\{b_0\}\) and \(A'=A\setminus f^{-1}(\{b_0\})\). For \(a\in A'\) we have \(f(a)\ne b_0\), so \(f'\colon A'\to B'\), \(a\mapsto f(a)\), is a function. It is surjective: if \(b\in B'\), then \(b=f(a)\) for some \(a\in A\), and \(a\in A'\) because \(f(a)=b\ne b_0\). Since \(B'\) has \(n\) elements, the induction hypothesis gives \(h'\colon B'\to A'\) with \(f'(h'(b))=b\) for all \(b\in B'\). Define \(h\colon B\to A\) by \(h(b_0)=a_0\) and \(h(b)=h'(b)\) for \(b\in B'\). Then \(f(h(b_0))=f(a_0)=b_0\) and \(f(h(b))=f'(h'(b))=b\) for \(b\in B'\), so \(f\circ h=\operatorname{id}_B\).
\end{proof}

In general, a right inverse is obtained by choosing, for every \(b\in B\) simultaneously, one element of the nonempty fibre \(f^{-1}(\{b\})\). The statement ``every surjective function has a right inverse'' is equivalent to the axiom of choice; see \PMlinkname{surjection and axiom of choice}{SurjectionAndAxiomOfChoice}. Parts (2) and (3) are cases where no such principle is needed: in (2) the least element of each fibre is a definite choice, and in (3) only finitely many choices are made, one at each step of the induction. A right inverse is in general not unique: both \(y\mapsto\sqrt{y}\) and \(y\mapsto-\sqrt{y}\) are right inverses of \(\mathbb{R}\to[0,\infty)\), \(x\mapsto x^2\).

\begin{proposition}
For a function \(f\colon A\to B\) the following are equivalent:
\begin{enumerate}
\item \(f\) is surjective;
\item \(f\) is right cancellable: for every set \(C\) and all functions \(g,h\colon B\to C\), \(g\circ f=h\circ f\) implies \(g=h\);
\item \(f(f^{-1}(T))=T\) for every \(T\subseteq B\).
\end{enumerate}
\end{proposition}

\begin{proof}
\textit{(1) implies (2).} Let \(g\circ f=h\circ f\) and \(b\in B\). Write \(b=f(a)\); then \(g(b)=g(f(a))=h(f(a))=h(b)\). As \(g\) and \(h\) have the same domain and codomain, \(g=h\).

\textit{(2) implies (1).} Suppose \(f\) is not surjective and pick \(b_0\in B\setminus f(A)\). Let \(C=\{0,1\}\), let \(g\colon B\to C\) be the constant function with value \(0\), and define \(h\colon B\to C\) by \(h(b)=0\) if \(b\in f(A)\) and \(h(b)=1\) if \(b\notin f(A)\). For every \(a\in A\), \(f(a)\in f(A)\), so \(h(f(a))=0=g(f(a))\); thus \(g\circ f=h\circ f\). But \(g(b_0)=0\ne1=h(b_0)\), so \(g\ne h\), and \(f\) is not right cancellable.

\textit{(1) implies (3).} If \(b\in f(f^{-1}(T))\), then \(b=f(a)\) with \(f(a)\in T\), so \(b\in T\); this inclusion holds for every function. Conversely, let \(b\in T\). By surjectivity \(b=f(a)\) for some \(a\in A\), and \(a\in f^{-1}(T)\) since \(f(a)\in T\); hence \(b\in f(f^{-1}(T))\).

\textit{(3) implies (1).} Take \(T=B\). Since \(f^{-1}(B)=A\), we get \(f(A)=B\).
\end{proof}

\begin{theorem}
Let \(A\) be a set with \(m\) elements and \(B\) a set with \(n\) elements, \(m,n\in\mathbb{N}\).
\begin{enumerate}
\item If \(n=0\), there is a surjective function \(A\to B\) if and only if \(m=0\).
\item If \(n\ge1\), there is a surjective function \(A\to B\) if and only if \(m\ge n\).
\end{enumerate}
\end{theorem}

\begin{proof}
\textit{(1)} Here \(B=\varnothing\). A function \(A\to\varnothing\) exists only if \(A=\varnothing\), and the empty function \(\varnothing\to\varnothing\) is surjective because its codomain is empty.

\textit{(2)} Suppose \(m\ge n\ge1\). List \(A=\{a_1,\dots,a_m\}\) and \(B=\{b_1,\dots,b_n\}\) without repetition and define \(f(a_i)=b_i\) for \(1\le i\le n\) and \(f(a_i)=b_1\) for \(n<i\le m\). Then \(b_j=f(a_j)\) for every \(j\le n\), so \(f\) is surjective. Conversely, let \(f\colon A\to B\) be surjective. By part (3) of the proposition on right inverses above, \(f\) has a right inverse \(h\colon B\to A\), and \(h\) is injective by part (1) of the same proposition. By the counting theorem for \PMlinkname{injective functions}{InjectiveFunction}, an injection from a set with \(n\) elements to a set with \(m\) elements exists only if \(n\le m\).
\end{proof}

\begin{example}
\begin{enumerate}
\item Let \(A\) and \(B\) be sets with \(B\ne\varnothing\). The first projection \(\pi_1\colon A\times B\to A\), \((a,b)\mapsto a\), of the \PMlinkname{Cartesian product}{CartesianProduct} is surjective: fix some \(b_0\in B\); then \(a=\pi_1(a,b_0)\) for every \(a\in A\). If \(B=\varnothing\) and \(A\ne\varnothing\), then \(A\times B=\varnothing\) and \(\pi_1\) is not surjective.
\item The floor function \(\mathbb{R}\to\mathbb{Z}\), \(x\mapsto\lfloor x\rfloor\), where \(\lfloor x\rfloor\) is the greatest integer \(k\) with \(k\le x\), is surjective, since \(\lfloor k\rfloor=k\) for every \(k\in\mathbb{Z}\). It is not injective, since \(\lfloor 0\rfloor=\lfloor 1/2\rfloor=0\). The inclusion \(\mathbb{Z}\to\mathbb{R}\) is a right inverse of it.
\item For an integer \(n\ge1\), reduction modulo \(n\), the function \(\mathbb{Z}\to\mathbb{Z}/n\mathbb{Z}\) sending \(k\) to its residue class \(k+n\mathbb{Z}\) (see \PMlinkname{integers modulo n}{IntegersModuloN}), is surjective, because by definition every element of \(\mathbb{Z}/n\mathbb{Z}\) is the class of some integer. Sending each class to its least nonnegative member, which lies in \(\{0,1,\dots,n-1\}\) by division with remainder, gives a right inverse.
\item The function \(\mathbb{N}\to\mathbb{N}\), \(n\mapsto n+1\), is not surjective, because \(0\) is not a value; the function \(\mathbb{Z}\to\mathbb{Z}\), \(k\mapsto k+1\), is surjective, since \(k=(k-1)+1\).
\end{enumerate}
\end{example}
""")


entry("bijective function", "bijective-function", ["03E20"],
      ["bijective", "bijection", "bijections", "bijectivity", "one-to-one correspondence",
       "bijective functions", "bijective map"],
      ["inverse function", "permutation of a set"],
      ["injective-function", "surjective-function", "composition-of-functions",
       "properties-of-bijections"], r"""
A function that pairs off the elements of two sets exactly, each element of the codomain being the value at exactly one element of the domain, can be run backwards, and such functions are the basis for comparing the sizes of sets.

Throughout, \(f\colon A\to B\) is a \PMlinkname{function}{Function} with domain \(A\) and codomain \(B\); composition is written \(g\circ f\), and \(f^{-1}(T)\) denotes the inverse image of \(T\subseteq B\).

\begin{definition}
A function \(f\colon A\to B\) is \emph{bijective}, or a \emph{bijection}, or a \emph{one-to-one correspondence} between \(A\) and \(B\), if it is both injective and surjective.
\end{definition}

A function is injective if and only if each of its fibres \(f^{-1}(\{b\})\), \(b\in B\), has at most one element, and surjective if and only if each fibre is nonempty. Hence \(f\) is bijective if and only if every fibre \(f^{-1}(\{b\})\), \(b\in B\), has exactly one element.

\begin{definition}
Let \(f\colon A\to B\) be bijective. The \emph{inverse function} of \(f\) is the function \(f^{-1}\colon B\to A\) that sends \(b\in B\) to the unique element of the fibre \(f^{-1}(\{b\})\); thus \(f^{-1}(b)\) is the unique \(a\in A\) with \(f(a)=b\). A bijection \(A\to A\) is called a \emph{permutation} of the set \(A\).
\end{definition}

The notation is consistent: for bijective \(f\) we have \(f^{-1}(\{b\})=\{f^{-1}(b)\}\). More generally, see the proposition on inverse images below.

\begin{theorem}
Let \(f\colon A\to B\) be a function.
\begin{enumerate}
\item If \(g\colon B\to A\) is a left inverse of \(f\) (\(g\circ f=\operatorname{id}_A\)) and \(h\colon B\to A\) is a right inverse of \(f\) (\(f\circ h=\operatorname{id}_B\)), then \(g=h\).
\item \(f\) is bijective if and only if there is a function \(g\colon B\to A\) with \(g\circ f=\operatorname{id}_A\) and \(f\circ g=\operatorname{id}_B\).
\item Such a two-sided inverse \(g\) is unique, and it is the inverse function \(f^{-1}\).
\item If \(f\) has a left inverse and a right inverse, then \(f\) is bijective.
\end{enumerate}
\end{theorem}

\begin{proof}
\textit{(1)} Using the identity laws and the associativity of \PMlinkname{composition}{CompositionOfFunctions},
\[
g=g\circ\operatorname{id}_B=g\circ(f\circ h)=(g\circ f)\circ h=\operatorname{id}_A\circ h=h.
\]

\textit{(2)} Let \(f\) be bijective and \(g=f^{-1}\). For \(a\in A\), the element \(a\) satisfies \(f(a)=f(a)\), so it is the unique element of the fibre over \(f(a)\), and \(g(f(a))=a\). For \(b\in B\), \(g(b)\) is an element with \(f(g(b))=b\). So \(g\circ f=\operatorname{id}_A\) and \(f\circ g=\operatorname{id}_B\). Conversely, suppose such a \(g\) exists. If \(f(a)=f(a')\), then \(a=g(f(a))=g(f(a'))=a'\), so \(f\) is injective; and every \(b\in B\) equals \(f(g(b))\), so \(f\) is surjective.

\textit{(3)} If \(g\) and \(g'\) are two-sided inverses of \(f\), then \(g\) is a left inverse and \(g'\) a right inverse, so \(g=g'\) by (1). By the proof of (2), \(f^{-1}\) is a two-sided inverse, so every two-sided inverse equals \(f^{-1}\).

\textit{(4)} If \(g\) is a left inverse and \(h\) a right inverse, then \(g=h\) by (1), so \(g\) is a two-sided inverse and \(f\) is bijective by (2).
\end{proof}

Part (4) uses no form of the axiom of choice: the inverse is given by the left (equivalently, the right) inverse itself.

\begin{proposition}
Let \(f\colon A\to B\) be a function with graph \(\Gamma\subseteq A\times B\), and let \(\Gamma^{-1}=\{(b,a)\mid (a,b)\in\Gamma\}\subseteq B\times A\) be the converse relation.
\begin{enumerate}
\item \(\Gamma^{-1}\) is the graph of a function \(B\to A\) if and only if \(f\) is bijective.
\item If \(f\) is bijective, then \(\Gamma^{-1}\) is the graph of the inverse function \(f^{-1}\).
\end{enumerate}
\end{proposition}

\begin{proof}
A relation \(R\subseteq B\times A\) is the graph of a function \(B\to A\) if and only if for every \(b\in B\) there is exactly one \(a\in A\) with \((b,a)\in R\). For \(R=\Gamma^{-1}\), the condition \((b,a)\in\Gamma^{-1}\) means \((a,b)\in\Gamma\), that is, \(f(a)=b\), that is, \(a\in f^{-1}(\{b\})\). So \(\Gamma^{-1}\) is the graph of a function \(B\to A\) if and only if every fibre of \(f\) has exactly one element, which is bijectivity; this proves (1). In that case the function with graph \(\Gamma^{-1}\) sends \(b\) to the unique \(a\) with \(f(a)=b\), which is \(f^{-1}(b)\); this proves (2).
\end{proof}

When a function is identified with its graph, part (2) says that the inverse function \(f^{-1}\) is the converse relation of \(f\), so the two uses of the notation \(f^{-1}\) agree.

\begin{proposition}
Let \(f\colon A\to B\) and \(g\colon B\to C\) be bijective.
\begin{enumerate}
\item \(f^{-1}\) is bijective and \((f^{-1})^{-1}=f\).
\item \(g\circ f\) is bijective and \((g\circ f)^{-1}=f^{-1}\circ g^{-1}\).
\item \(\operatorname{id}_A\) is bijective and \(\operatorname{id}_A^{-1}=\operatorname{id}_A\).
\end{enumerate}
\end{proposition}

\begin{proof}
\textit{(1)} The equations \(f^{-1}\circ f=\operatorname{id}_A\) and \(f\circ f^{-1}=\operatorname{id}_B\) say that \(f\colon A\to B\) is a two-sided inverse of \(f^{-1}\colon B\to A\). By the theorem, \(f^{-1}\) is bijective and its inverse is \(f\).

\textit{(2)} By associativity,
\[
(g\circ f)\circ(f^{-1}\circ g^{-1})=g\circ(f\circ f^{-1})\circ g^{-1}=g\circ\operatorname{id}_B\circ g^{-1}=g\circ g^{-1}=\operatorname{id}_C,
\]
and likewise \((f^{-1}\circ g^{-1})\circ(g\circ f)=f^{-1}\circ(g^{-1}\circ g)\circ f=f^{-1}\circ f=\operatorname{id}_A\). So \(f^{-1}\circ g^{-1}\) is a two-sided inverse of \(g\circ f\), and the theorem applies.

\textit{(3)} \(\operatorname{id}_A\circ\operatorname{id}_A=\operatorname{id}_A\), so \(\operatorname{id}_A\) is a two-sided inverse of itself.
\end{proof}

\begin{proposition}
Let \(f\colon A\to B\) be bijective and \(T\subseteq B\). The inverse image \(f^{-1}(T)=\{a\in A\mid f(a)\in T\}\) equals the image \(\{f^{-1}(b)\mid b\in T\}\) of \(T\) under the inverse function.
\end{proposition}

\begin{proof}
If \(f(a)\in T\), put \(b=f(a)\); then \(a=f^{-1}(b)\) with \(b\in T\). Conversely, if \(a=f^{-1}(b)\) with \(b\in T\), then \(f(a)=b\in T\).
\end{proof}

So for a bijection the two readings of \(f^{-1}(T)\) agree, and no ambiguity arises.

\begin{theorem}
Let \(A\) and \(B\) be finite sets with the same number \(n\) of elements, and let \(f\colon A\to B\). Then \(f\) is injective if and only if \(f\) is surjective, and hence if and only if \(f\) is bijective.
\end{theorem}

\begin{proof}
We use two counting facts: there is no injection from a set with \(n\) elements to a set with fewer elements (the counting theorem in \PMlinkname{injective function}{InjectiveFunction}), and if \(n\ge1\) there is no surjection from a set with fewer than \(n\) elements onto a set with \(n\) elements (the counting theorem in \PMlinkname{surjective function}{SurjectiveFunction}).

Let \(f\) be injective and suppose some \(b\in B\) is not a value of \(f\). Then \(a\mapsto f(a)\) is an injection from \(A\), with \(n\) elements, to \(B\setminus\{b\}\), with \(n-1\) elements, which is impossible. So \(f\) is surjective.

Let \(f\) be surjective and suppose \(f(a)=f(a')\) with \(a\ne a'\). Then \(n\ge2\). The restriction of \(f\) to \(A\setminus\{a'\}\) is still surjective onto \(B\): a value \(f(x)\) with \(x\ne a'\) is attained at \(x\), and the value \(f(a')\) is attained at \(a\in A\setminus\{a'\}\). But \(A\setminus\{a'\}\) has \(n-1\) elements, which is impossible. So \(f\) is injective.
\end{proof}

For infinite sets this fails: \(\mathbb{N}\to\mathbb{N}\), \(n\mapsto n+1\), is injective but \(0\) is not a value, and \(\mathbb{N}\to\mathbb{N}\), \(n\mapsto\lfloor n/2\rfloor\), is surjective (\(k=\lfloor 2k/2\rfloor\)) but not injective (\(\lfloor 0/2\rfloor=\lfloor 1/2\rfloor=0\)). Here \(\mathbb{N}=\{0,1,2,\dots\}\).

The set of all permutations of a set \(A\) is a group under composition, called the symmetric group on \(A\): the composite of two permutations is a permutation by part (2) of the proposition above, composition is associative, \(\operatorname{id}_A\) is a permutation and is an identity element, and each permutation \(\sigma\) has the permutation \(\sigma^{-1}\) with \(\sigma\circ\sigma^{-1}=\sigma^{-1}\circ\sigma=\operatorname{id}_A\).

\begin{example}
\begin{enumerate}
\item The function \(f\colon\mathbb{R}\to\mathbb{R}\), \(f(x)=2x+1\), is bijective with inverse \(g(y)=(y-1)/2\): indeed \(g(f(x))=(2x+1-1)/2=x\) and \(f(g(y))=2\cdot\frac{y-1}{2}+1=y\).
\item The exponential function \(\exp\colon\mathbb{R}\to(0,\infty)\) is bijective; its inverse is the natural logarithm \(\log\colon(0,\infty)\to\mathbb{R}\). (We take these facts from analysis.) As a function \(\mathbb{R}\to\mathbb{R}\) it is not bijective, since \(0\) is not a value.
\item The function \(\mathbb{Z}\to\mathbb{Z}\), \(k\mapsto k+1\), is bijective with inverse \(k\mapsto k-1\), since \((k+1)-1=k=(k-1)+1\). On \(\mathbb{N}\) the same formula gives an injection that is not surjective, as noted above.
\item Define \(f\colon\mathbb{N}\to\mathbb{Z}\) by \(f(n)=n/2\) for even \(n\) and \(f(n)=-(n+1)/2\) for odd \(n\), so that \(0,1,2,3,4,\dots\) go to \(0,-1,1,-2,2,\dots\); both formulas give integers. Define \(g\colon\mathbb{Z}\to\mathbb{N}\) by \(g(k)=2k\) for \(k\ge0\) and \(g(k)=-2k-1\) for \(k<0\); both values are in \(\mathbb{N}\), since \(-2k-1\ge1\) when \(k\le-1\). If \(n\) is even, then \(f(n)=n/2\ge0\) and \(g(f(n))=n\). If \(n\) is odd, then \(f(n)=-(n+1)/2\le-1\) and \(g(f(n))=(n+1)-1=n\). If \(k\ge0\), then \(g(k)=2k\) is even and \(f(g(k))=k\). If \(k<0\), then \(g(k)=-2k-1\) is odd and \(f(g(k))=-(-2k-1+1)/2=k\). So \(g\) is a two-sided inverse of \(f\), and \(f\) is a bijection.
\item On \(A=\{1,2,3\}\), let \(\sigma\) be the permutation exchanging \(1\) and \(2\) and fixing \(3\), and \(\tau\) the permutation \(1\mapsto2\), \(2\mapsto3\), \(3\mapsto1\). Then \((\sigma\circ\tau)(1)=\sigma(2)=1\) but \((\tau\circ\sigma)(1)=\tau(2)=3\), so \(\sigma\circ\tau\ne\tau\circ\sigma\): the symmetric group on a set with three elements is not commutative.
\end{enumerate}
\end{example}

\begin{remark}
Two sets \(A\) and \(B\) are said to have the same cardinality, or to be equinumerous, if there is a bijection \(A\to B\). By the propositions above, every set is equinumerous with itself (\(\operatorname{id}_A\)), equinumerosity is symmetric (\(f^{-1}\)), and it is transitive (\(g\circ f\)). Item 4 of the example shows that \(\mathbb{N}\) and \(\mathbb{Z}\) are equinumerous although \(\mathbb{N}\) is a proper subset of \(\mathbb{Z}\). This cannot happen for a finite set \(A\) with \(n\) elements: if \(S\subsetneq A\) and \(a\in A\setminus S\), an injection \(A\to S\) would give an injection from \(A\) to \(A\setminus\{a\}\), a set with \(n-1\) elements, which the counting theorem for injective functions excludes. Further closure properties of bijections are collected in \PMlinkname{properties of bijections}{PropertiesOfBijections}.
\end{remark}
""")

# Part 7 of the naive set theory entries: entries 17 (indexed family) and
# 18 (generalized Cartesian product), in global order.
#
# Ordinary English words in these bodies that might be mis-autolinked to unrelated entries:
# family, families, index, term, terms, value, values, range, union, intersection, image,
# product, projection, coordinate, component, choice, choose, constant, universe, order,
# natural, element, member, interval, sequence, tuple, factor, factors, empty, pair,
# identify, identification, least, nonempty, finite, induction, condition, label, collection,
# vacuously, canonical.
#
# Notes for the assembler / reviewer:
# - Entry 18 defines "choice function". If an existing entry (for example one of the axiom of
#   choice entries) already lists "choice function" as a title, synonym or defined term, the
#   two collide; kept as specified.
# - Entry 18, "if all A_i = A then the product is A^I": with the spec's convention that the
#   codomain is part of a function, this is an equality only for I nonempty. For I empty the
#   product's unique element is the empty function into the empty set, while A^I consists of
#   the empty function into A; the entry states the equality for I nonempty and notes this.
#   The same caveat is noted for {0,1}^X with X empty.
# - Entry 17 states reindexing for a surjective sigma (which covers the bijective case in the
#   spec), since the proof only uses surjectivity.
# - Entry 18 adds a short reindexing proposition (x -> x o sigma is a bijection between the
#   products); it explains why the product does not depend on any ordering of the factors.


entry("indexed family", "indexed-family", ["03E20"],
      ["indexed families", "family of sets", "families of sets", "indexed family of sets"],
      ["index set", "union of a family", "intersection of a family", "disjoint union of a family"],
      ["function", "set-operations"], r"""
Mathematics constantly deals with objects labelled by indices, such as the terms \(x_0,x_1,x_2,\dots\) of a sequence or the sets \(A_1,\dots,A_n\) in a finite union, and an indexed family records both the objects and the labelling, including repetitions.

Throughout, functions are total functions in the sense of the entry \PMlinkname{function}{Function}, and \(\mathbb{N}=\{0,1,2,\dots\}\).

\begin{definition}
Let \(I\) and \(X\) be sets. An \emph{indexed family} (or simply a family) of elements of \(X\) indexed by \(I\) is a function \(x\colon I\to X\). The set \(I\) is the \emph{index set} of the family. For \(i\in I\) one writes \(x_i\) instead of \(x(i)\), and the family itself is written \((x_i)_{i\in I}\) or \(i\mapsto x_i\). The set of values of the family is
\[
\{x_i\mid i\in I\}=x(I)\subseteq X.
\]
\end{definition}

Since a family is a function, two families \((x_i)_{i\in I}\) and \((y_j)_{j\in J}\) of elements of \(X\) are equal if and only if \(I=J\) and \(x_i=y_i\) for every \(i\in I\). A family is therefore more than its set of values: the set of values forgets which index carries which value, and how often a value occurs.

\begin{example}
Consider the families \((x_n)_{n\in\mathbb{N}}\) and \((y_n)_{n\in\mathbb{N}}\) of integers given by \(x_n=(-1)^n\) and \(y_n=(-1)^{n+1}\). They are different, since \(x_0=1\ne-1=y_0\). Both have the set of values \(\{-1,1\}\): every value of either family is \(1\) or \(-1\), and both values occur (\(x_0=1\), \(x_1=-1\), \(y_0=-1\), \(y_1=1\)). Likewise, on the index set \(\{1,2\}\), the families \(i\mapsto i\) and \(i\mapsto 3-i\) are different (their values at \(1\) are \(1\) and \(2\)), although both have the set of values \(\{1,2\}\). Finally, the constant family \((0)_{n\in\mathbb{N}}\) has infinitely many terms, all equal, and its set of values is \(\{0\}\).
\end{example}

\textit{Sequences and tuples.} A family indexed by \(\mathbb{N}\) (or by \(\{1,2,3,\dots\}\)) is a sequence of elements of \(X\); \(x_n\) is its \(n\)-th term. A family indexed by \(\{1,\dots,n\}\) is a finite list \(x_1,\dots,x_n\), and it carries the same information as the \(n\)-tuple \((x_1,\dots,x_n)\) of the entry on ordered pairs.

\begin{proposition}
Let \(X\) be a set and \(n\ge2\). Let \(X^n\) be the set of \(n\)-tuples of elements of \(X\), defined by iterated ordered pairs, and let \(X^{\{1,\dots,n\}}\) be the set of families of elements of \(X\) indexed by \(\{1,\dots,n\}\). The rule \(\Phi\) sending \((a_1,\dots,a_n)\) to the family \(k\mapsto a_k\) is a bijection \(X^n\to X^{\{1,\dots,n\}}\).
\end{proposition}

\begin{proof}
Two \(n\)-tuples are equal if and only if their corresponding coordinates are equal. The forward implication shows that the coordinates \(a_1,\dots,a_n\) are determined by the tuple, so \(\Phi\) is a well-defined function. If \(\Phi(a_1,\dots,a_n)=\Phi(b_1,\dots,b_n)\), the two families have the same value at each \(k\), that is \(a_k=b_k\) for \(k=1,\dots,n\), and the reverse implication gives \((a_1,\dots,a_n)=(b_1,\dots,b_n)\); so \(\Phi\) is injective. Given a family \((x_k)_{k\in\{1,\dots,n\}}\), the tuple \((x_1,\dots,x_n)\) is mapped to it; so \(\Phi\) is surjective.
\end{proof}

Because of this correspondence one freely identifies \(n\)-tuples with families indexed by \(\{1,\dots,n\}\).

\textit{Families of sets.} A \emph{family of sets} is a family \((A_i)_{i\in I}\) whose terms \(A_i\) are sets. Formally it is a function from \(I\) to some set of sets, for instance to the set of values \(\{A_i\mid i\in I\}\), or to \(\mathcal{P}(X)\) when all \(A_i\) are subsets of a fixed set \(X\); the constructions below depend only on the sets \(A_i\), not on this choice.

\begin{definition}
Let \((A_i)_{i\in I}\) be a family of sets.
\begin{enumerate}
\item The \emph{union of a family} \((A_i)_{i\in I}\) is the union of its set of values,
\[
\bigcup_{i\in I}A_i=\bigcup\{A_i\mid i\in I\}.
\]
\item If \(I\ne\varnothing\), the \emph{intersection of a family} \((A_i)_{i\in I}\) is the intersection of its (nonempty) set of values,
\[
\bigcap_{i\in I}A_i=\bigcap\{A_i\mid i\in I\}.
\]
\item The family is pairwise disjoint if \(A_i\cap A_j=\varnothing\) for all \(i,j\in I\) with \(i\ne j\).
\end{enumerate}
\end{definition}

An object \(x\) lies in \(\bigcup\{A_i\mid i\in I\}\) if and only if \(x\in S\) for some member \(S\) of \(\{A_i\mid i\in I\}\), that is, if and only if \(x\in A_i\) for some \(i\in I\). In the same way, for \(I\ne\varnothing\), \(x\in\bigcap_{i\in I}A_i\) if and only if \(x\in A_i\) for every \(i\in I\). For any fixed \(k\in I\) the intersection is the subset \(\{x\in A_k\mid x\in A_i \text{ for all } i\in I\}\) of \(A_k\). Directly from these descriptions, \(\bigcap_{i\in I}A_i\subseteq A_j\subseteq\bigcup_{i\in I}A_i\) for every \(j\in I\), and if \(A_i\subseteq C\) for all \(i\) then \(\bigcup_{i\in I}A_i\subseteq C\).

Being pairwise disjoint is a property of the family, not of its set of values: for \(A_1=A_2=\{0\}\), the family \((A_i)_{i\in\{1,2\}}\) is not pairwise disjoint, since \(A_1\cap A_2=\{0\}\), while its set of values \(\{\{0\}\}\) has only one member and is pairwise disjoint.

\begin{remark}
For the empty index set, \(\bigcup_{i\in\varnothing}A_i=\bigcup\varnothing=\varnothing\), since no \(x\) lies in some \(A_i\). The intersection is a different matter. The condition ``\(x\in A_i\) for every \(i\in\varnothing\)'' holds vacuously for every object \(x\), so the intersection would have to contain everything. In \PMlinkname{naive set theory}{NaiveSetTheory} there is no set of all sets: if \(V\) were one, then \(\{x\in V\mid x\notin x\}\) would lead to \PMlinkname{Russell's paradox}{RussellsParadox}. Hence \(\bigcap_{i\in\varnothing}A_i\) is left undefined in general. When all \(A_i\) are subsets of a fixed universe \(X\), one reads the condition inside \(X\) and puts
\[
\bigcap_{i\in\varnothing}A_i=\{x\in X\mid x\in A_i \text{ for all } i\in\varnothing\}=X.
\]
With this convention the identities below that are stated for \(I\ne\varnothing\) remain true for \(I=\varnothing\) whenever all sets involved are subsets of the universes concerned; see also the entry \PMlinkname{intersection}{Intersection}.
\end{remark}

\begin{proposition}
Let \((A_i)_{i\in I}\) and \((B_i)_{i\in I}\) be families of sets, and let \(A\) and \(X\) be sets.
\begin{enumerate}
\item \(A\cap\bigcup_{i\in I}B_i=\bigcup_{i\in I}(A\cap B_i)\).
\item If \(I\ne\varnothing\), then \(A\cup\bigcap_{i\in I}B_i=\bigcap_{i\in I}(A\cup B_i)\).
\item If \(I\ne\varnothing\), then \(X\setminus\bigcup_{i\in I}A_i=\bigcap_{i\in I}(X\setminus A_i)\) and \(X\setminus\bigcap_{i\in I}A_i=\bigcup_{i\in I}(X\setminus A_i)\).
\item \textit{(Reindexing.)} Let \(\sigma\colon J\to I\) be a surjective function, for instance a bijection. Then \(\bigcup_{j\in J}A_{\sigma(j)}=\bigcup_{i\in I}A_i\), and if \(I\ne\varnothing\) then also \(J\ne\varnothing\) and \(\bigcap_{j\in J}A_{\sigma(j)}=\bigcap_{i\in I}A_i\).
\end{enumerate}
\end{proposition}

\begin{proof}
\textit{(1)} An object \(x\) lies in the left side if and only if \(x\in A\) and \(x\in B_i\) for some \(i\), that is, if and only if \(x\in A\cap B_i\) for some \(i\), which means that \(x\) lies in the right side.

\textit{(2)} Let \(x\) lie in the left side. If \(x\in A\), then \(x\in A\cup B_i\) for every \(i\). If \(x\in\bigcap_{i\in I}B_i\), then \(x\in B_i\subseteq A\cup B_i\) for every \(i\). Either way \(x\) lies in the right side. Conversely, let \(x\in A\cup B_i\) for every \(i\in I\). If \(x\in A\), then \(x\) lies in the left side. Otherwise \(x\notin A\), so \(x\in B_i\) for every \(i\), hence \(x\in\bigcap_{i\in I}B_i\), and again \(x\) lies in the left side.

\textit{(3)} An object \(x\) lies in \(X\setminus\bigcup_{i\in I}A_i\) if and only if \(x\in X\) and there is no \(i\) with \(x\in A_i\). This implies that \(x\in X\setminus A_i\) for every \(i\). Conversely, if \(x\in X\setminus A_i\) for every \(i\in I\), then \(x\in X\) (choose any \(i\in I\); here \(I\ne\varnothing\) is used) and \(x\notin A_i\) for every \(i\). This proves the first identity. For the second, \(x\in X\setminus\bigcap_{i\in I}A_i\) if and only if \(x\in X\) and it is not the case that \(x\in A_i\) for every \(i\), that is, \(x\in X\) and \(x\notin A_i\) for some \(i\), that is, \(x\in X\setminus A_i\) for some \(i\in I\).

\textit{(4)} If \(x\in A_{\sigma(j)}\) for some \(j\in J\), then \(x\in A_i\) with \(i=\sigma(j)\in I\). Conversely, if \(x\in A_i\) for some \(i\in I\), choose \(j\in J\) with \(\sigma(j)=i\), which exists because \(\sigma\) is surjective; then \(x\in A_{\sigma(j)}\). This proves the statement about unions. If \(I\ne\varnothing\), pick \(i\in I\); surjectivity gives some \(j\in J\) with \(\sigma(j)=i\), so \(J\ne\varnothing\). If \(x\in A_i\) for all \(i\in I\), then in particular \(x\in A_{\sigma(j)}\) for all \(j\in J\). Conversely, suppose \(x\in A_{\sigma(j)}\) for all \(j\in J\), and let \(i\in I\); choosing \(j\) with \(\sigma(j)=i\) gives \(x\in A_i\). This proves the statement about intersections.
\end{proof}

\begin{proposition}
Let \(f\colon X\to Y\) be a function, let \((A_i)_{i\in I}\) be a family of subsets of \(X\) and let \((B_i)_{i\in I}\) be a family of subsets of \(Y\). Then
\[
f\Bigl(\bigcup_{i\in I}A_i\Bigr)=\bigcup_{i\in I}f(A_i),\qquad f^{-1}\Bigl(\bigcup_{i\in I}B_i\Bigr)=\bigcup_{i\in I}f^{-1}(B_i),
\]
and, if \(I\ne\varnothing\),
\[
f^{-1}\Bigl(\bigcap_{i\in I}B_i\Bigr)=\bigcap_{i\in I}f^{-1}(B_i),\qquad f\Bigl(\bigcap_{i\in I}A_i\Bigr)\subseteq\bigcap_{i\in I}f(A_i).
\]
\end{proposition}

\begin{proof}
For \(y\in Y\): \(y\in f(\bigcup_{i}A_i)\) if and only if \(y=f(a)\) for some \(a\) that lies in some \(A_i\), if and only if there is an \(i\) with \(y\in f(A_i)\), which means \(y\in\bigcup_i f(A_i)\). For \(a\in X\): \(a\in f^{-1}(\bigcup_i B_i)\) if and only if \(f(a)\in B_i\) for some \(i\), if and only if \(a\in f^{-1}(B_i)\) for some \(i\). Now let \(I\ne\varnothing\). An object \(a\) lies in \(f^{-1}(\bigcap_i B_i)\) if and only if \(a\in X\) and \(f(a)\in B_i\) for every \(i\). It lies in \(\bigcap_i f^{-1}(B_i)\) if and only if, for every \(i\), \(a\in X\) and \(f(a)\in B_i\). Since \(I\ne\varnothing\), these two conditions are the same. Finally, if \(y=f(a)\) with \(a\in A_i\) for every \(i\), then \(y\in f(A_i)\) for every \(i\).
\end{proof}

The last inclusion can be strict. For the constant function \(f\colon\{1,2\}\to\{0\}\) and \(A_1=\{1\}\), \(A_2=\{2\}\), we have \(f(A_1\cap A_2)=f(\varnothing)=\varnothing\), but \(f(A_1)\cap f(A_2)=\{0\}\). More facts of this kind are in the entry \PMlinkname{properties of a function}{PropertiesOfAFunction}.

\begin{definition}
Let \((A_i)_{i\in I}\) be a family of sets. The \emph{disjoint union of a family} \((A_i)_{i\in I}\) is the set
\[
\bigsqcup_{i\in I}A_i=\bigcup_{i\in I}\bigl(A_i\times\{i\}\bigr)=\{(a,i)\mid i\in I,\ a\in A_i\}.
\]
For \(j\in I\), the injection of the \(j\)-th set is the function \(\iota_j\colon A_j\to\bigsqcup_{i\in I}A_i\), \(a\mapsto(a,j)\).
\end{definition}

The disjoint union is a subset of \(\bigl(\bigcup_{i\in I}A_i\bigr)\times I\). For \(I=\{0,1\}\), \(A_0=A\) and \(A_1=B\), it is \((A\times\{0\})\cup(B\times\{1\})=A\sqcup B\), the \PMlinkname{disjoint union}{SetOperations} of two sets.

\begin{proposition}
Let \((A_i)_{i\in I}\) be a family of sets and \(D=\bigsqcup_{i\in I}A_i\).
\begin{enumerate}
\item Each \(\iota_j\) is injective, and \(\iota_j(A_j)=A_j\times\{j\}\).
\item The family \((A_i\times\{i\})_{i\in I}\) is pairwise disjoint, and its union is \(D\). Hence every element of \(D\) lies in \(\iota_i(A_i)\) for exactly one \(i\in I\).
\item If the family \((A_i)_{i\in I}\) is pairwise disjoint, then \(p\colon D\to\bigcup_{i\in I}A_i\), \((a,i)\mapsto a\), is a bijection.
\end{enumerate}
\end{proposition}

\begin{proof}
\textit{(1)} If \(\iota_j(a)=\iota_j(b)\), then \((a,j)=(b,j)\), so \(a=b\) by the characteristic property of ordered pairs. The equality \(\iota_j(A_j)=\{(a,j)\mid a\in A_j\}=A_j\times\{j\}\) is the definition of the two sides.

\textit{(2)} If \(i\ne k\) and \((a,i)=(b,k)\) with \(a\in A_i\), \(b\in A_k\), then \(i=k\) by the characteristic property of ordered pairs, a contradiction; so \((A_i\times\{i\})\cap(A_k\times\{k\})=\varnothing\). The union of the family is \(D\) by definition. So every element of \(D\) lies in at least one set \(A_i\times\{i\}\), and by disjointness in exactly one.

\textit{(3)} The rule is a function, because the first coordinate of a pair is determined by the pair, and \(a\in A_i\subseteq\bigcup_k A_k\). It is surjective: if \(a\in\bigcup_k A_k\), then \(a\in A_i\) for some \(i\), and \(p(a,i)=a\). It is injective: if \(p(a,i)=p(b,k)\), then \(a=b\in A_i\cap A_k\), so \(A_i\cap A_k\ne\varnothing\), hence \(i=k\) because the family is pairwise disjoint, and \((a,i)=(b,k)\).
\end{proof}

Part (3) is why, for a pairwise disjoint family, one usually identifies the disjoint union with the ordinary union. Without disjointness the two differ. For \(A_0=A_1=\{a\}\), the union is \(\{a\}\), with one element, while the disjoint union is \(\{(a,0),(a,1)\}\), with two elements, because \(0\ne1\).

\begin{example}
In \(\mathbb{R}\) let \(A_n=[-n,n]\) for \(n\ge1\). Then
\[
\bigcup_{n\ge1}A_n=\mathbb{R},\qquad \bigcap_{n\ge1}A_n=[-1,1].
\]
For the union, let \(x\in\mathbb{R}\). By the Archimedean property of \(\mathbb{R}\), which we take as known, there is an integer \(n\ge1\) with \(n\ge|x|\), and then \(x\in[-n,n]\). For the intersection, \([-1,1]\subseteq[-n,n]\) for every \(n\ge1\), so \([-1,1]\) is contained in the intersection, and the intersection is contained in \(A_1=[-1,1]\).
\end{example}

\begin{example}
In \(\mathbb{R}\) let \(A_n=(0,1/n)\) for \(n\ge1\). Then \(\bigcap_{n\ge1}A_n=\varnothing\), although each \(A_n\) is nonempty and \(A_{n+1}\subseteq A_n\) for every \(n\). Indeed, suppose \(x\in A_n\) for every \(n\ge1\). Then \(x>0\), and by the Archimedean property there is an integer \(n\ge1\) with \(n>1/x\), that is, \(x>1/n\); so \(x\notin A_n\), a contradiction. Here the union is \(A_1=(0,1)\), since every \(A_n\) is contained in \(A_1\).
\end{example}
""")


entry("generalized Cartesian product", "generalized-cartesian-product", ["03E20", "03E25"],
      ["product of a family of sets", "Cartesian product of a family",
       "infinite Cartesian product", "generalized product of sets"],
      ["coordinate projection", "choice function"],
      ["indexed-family", "cartesian-product", "function",
       "product-of-nonempty-set-of-nonempty-sets-is-nonempty"], r"""
An element of the Cartesian product \(A_1\times A_2\) amounts to a choice of one element from each factor, and describing such a choice as a family indexed by the factors gives a product of arbitrarily many sets, including infinitely many.

We use \PMlinkname{indexed families}{IndexedFamily}: a family \((x_i)_{i\in I}\) is a function on the index set \(I\), with \(x_i=x(i)\). Functions are total and have a fixed codomain, as in the entry \PMlinkname{function}{Function}.

\begin{definition}
Let \((A_i)_{i\in I}\) be a family of sets and \(U=\bigcup_{i\in I}A_i\). The \emph{generalized Cartesian product} (or simply product) of the family is the set
\[
\prod_{i\in I}A_i=\bigl\{x\colon I\to U\ \big|\ x(i)\in A_i \text{ for all } i\in I\bigr\}.
\]
Its elements are written as families \((x_i)_{i\in I}\); \(x_i\) is the \(i\)-th coordinate of \(x\), and the sets \(A_i\) are the factors. For \(j\in I\), the \emph{coordinate projection} onto the \(j\)-th factor is
\[
\pi_j\colon\prod_{i\in I}A_i\to A_j,\qquad x\mapsto x_j.
\]
A \emph{choice function} for the family \((A_i)_{i\in I}\) is a function \(c\) with domain \(I\) (and some codomain containing every \(A_i\)) such that \(c(i)\in A_i\) for every \(i\in I\).
\end{definition}

The product is a subset of the set \(U^I\) of all functions \(I\to U\), so it is a set. Two elements \(x,y\) of the product are equal if and only if \(x_i=y_i\) for every \(i\in I\), because both are functions with domain \(I\) and codomain \(U\). The codomain \(U\) is fixed so that each choice of values \(x_i\in A_i\) gives exactly one element. With it, the elements of the product are precisely the choice functions for the family, regarded as functions into \(U\). For a set \(\mathcal{S}\) of sets one uses the family \((S)_{S\in\mathcal{S}}\) indexed by \(\mathcal{S}\) itself, and a choice function is then a function \(c\) on \(\mathcal{S}\) with \(c(S)\in S\) for each \(S\in\mathcal{S}\), the usual notion in connection with the axiom of choice.

\begin{proposition}
Let \((A_i)_{i\in I}\) be a family of sets.
\begin{enumerate}
\item If \(I=\varnothing\), then \(\prod_{i\in I}A_i\) has exactly one element, the empty function \(\varnothing\to\varnothing\).
\item If \(A_j=\varnothing\) for some \(j\in I\), then \(\prod_{i\in I}A_i=\varnothing\). Equivalently, if the product is nonempty, then every factor is nonempty.
\item If \(I\ne\varnothing\) and \(A_i=A\) for every \(i\in I\), then \(\prod_{i\in I}A_i=A^I\), the set of all functions \(I\to A\).
\end{enumerate}
\end{proposition}

\begin{proof}
\textit{(1)} Here \(U=\bigcup\varnothing=\varnothing\), and the condition \(x(i)\in A_i\) for all \(i\in\varnothing\) holds vacuously. So the product is the set of all functions \(\varnothing\to\varnothing\). There is exactly one such function, the empty function, whose graph is the only subset \(\varnothing\) of \(\varnothing\times\varnothing=\varnothing\); it is functional and total vacuously.

\textit{(2)} If \(x\) were an element of the product, then \(x_j\in A_j=\varnothing\), which is impossible.

\textit{(3)} Since \(I\ne\varnothing\), the set of values of the family is \(\{A\}\), so \(U=\bigcup\{A\}=A\). Every function \(x\colon I\to A\) satisfies \(x(i)\in A=A_i\) for all \(i\). Hence the product is the set of all functions \(I\to A\).
\end{proof}

In (3) the hypothesis \(I\ne\varnothing\) is needed only because the codomain is part of a function. For \(I=\varnothing\), both \(\prod_{i\in\varnothing}A\) and \(A^{\varnothing}\) have exactly one element, the empty function into \(\varnothing\) and the empty function into \(A\) respectively, and one identifies them.

\begin{proposition}
Let \(A_1\) and \(A_2\) be sets. The map
\[
\Phi\colon\prod_{i\in\{1,2\}}A_i\to A_1\times A_2,\qquad x\mapsto(x_1,x_2),
\]
is a bijection, and \(p_k\circ\Phi=\pi_k\) for \(k=1,2\), where \(p_1(a,b)=a\) and \(p_2(a,b)=b\).
\end{proposition}

\begin{proof}
\(\Phi\) is a function into \(A_1\times A_2\) because \(x_1\in A_1\) and \(x_2\in A_2\). It is injective: if \((x_1,x_2)=(y_1,y_2)\), then \(x_1=y_1\) and \(x_2=y_2\) by the characteristic property of ordered pairs, so \(x\) and \(y\) agree at every point of \(\{1,2\}\), and \(x=y\). It is surjective: given \((a,b)\in A_1\times A_2\), the set \(\{(1,a),(2,b)\}\subseteq\{1,2\}\times(A_1\cup A_2)\) is functional, since \(1\ne2\), and its domain is \(\{1,2\}\). It is therefore the graph of an element \(x\) of the product with \(x_1=a\), \(x_2=b\), and \(\Phi(x)=(a,b)\). Finally \(p_k(\Phi(x))=x_k=\pi_k(x)\).
\end{proof}

In the same way, using the identification of \(n\)-tuples with families indexed by \(\{1,\dots,n\}\) from the indexed family entry, \(\prod_{i\in\{1,\dots,n\}}A_i\) corresponds to \(A_1\times\cdots\times A_n\). The generalized product thus extends the \PMlinkname{Cartesian product}{CartesianProduct} of finitely many sets. Since the index set is just a set, the generalized product does not depend on any ordering of the factors, as the next result makes precise.

\begin{proposition}
Let \((A_i)_{i\in I}\) be a family of sets and \(\sigma\colon J\to I\) a bijection. Then \(x\mapsto x\circ\sigma\) is a bijection from \(\prod_{i\in I}A_i\) onto \(\prod_{j\in J}A_{\sigma(j)}\).
\end{proposition}

\begin{proof}
By reindexing (in the indexed family entry), both families have the same union \(U\). For \(x\) in the first product, \(x\circ\sigma\colon J\to U\) satisfies \((x\circ\sigma)(j)=x(\sigma(j))\in A_{\sigma(j)}\), so it lies in the second product. For \(y\) in the second product, \(y\circ\sigma^{-1}\colon I\to U\) satisfies \(y(\sigma^{-1}(i))\in A_{\sigma(\sigma^{-1}(i))}=A_i\), so it lies in the first product. By associativity of composition and \(\sigma^{-1}\circ\sigma=\operatorname{id}_J\), \(\sigma\circ\sigma^{-1}=\operatorname{id}_I\), we get \((x\circ\sigma)\circ\sigma^{-1}=x\) and \((y\circ\sigma^{-1})\circ\sigma=y\). So the two maps are inverse to each other, and both are bijections.
\end{proof}

\begin{theorem}
\textit{(Universal property.)} Let \((A_i)_{i\in I}\) be a family of sets, \(C\) a set, and \((f_i)_{i\in I}\) a family of functions \(f_i\colon C\to A_i\). Then there is exactly one function \(f\colon C\to\prod_{i\in I}A_i\) with \(\pi_i\circ f=f_i\) for every \(i\in I\), namely \(f(c)=(f_i(c))_{i\in I}\).
\end{theorem}

\begin{proof}
\textit{Existence.} For \(c\in C\), the family \(i\mapsto f_i(c)\) is a function \(I\to U\) with \(f_i(c)\in A_i\) for every \(i\), so it is an element \(f(c)\) of the product. This defines a function \(f\colon C\to\prod_{i\in I}A_i\). For each \(i\), the functions \(\pi_i\circ f\) and \(f_i\) both go from \(C\) to \(A_i\), and \(\pi_i(f(c))=f(c)_i=f_i(c)\) for every \(c\in C\); hence \(\pi_i\circ f=f_i\).

\textit{Uniqueness.} Let \(g\colon C\to\prod_{i\in I}A_i\) satisfy \(\pi_i\circ g=f_i\) for all \(i\). For \(c\in C\) and \(i\in I\), \(g(c)_i=\pi_i(g(c))=f_i(c)=f(c)_i\). So the elements \(g(c)\) and \(f(c)\) of the product have the same coordinates, and \(g(c)=f(c)\). As this holds for every \(c\in C\), and \(f\) and \(g\) have the same domain and codomain, \(g=f\).
\end{proof}

\begin{proposition}
Let \((A_i)_{i\in I}\) be a family of nonempty sets with \(I\) finite. Then \(\prod_{i\in I}A_i\ne\varnothing\).
\end{proposition}

\begin{proof}
We use induction on the number \(n\) of elements of \(I\). If \(n=0\), then \(I=\varnothing\) and the product has an element by part (1) of the first proposition. Suppose the claim holds for index sets with \(n\) elements, and let \(I\) have \(n+1\) elements. Pick \(k\in I\) and put \(I'=I\setminus\{k\}\), which has \(n\) elements. By the induction hypothesis there is \(y\in\prod_{i\in I'}A_i\), a function \(I'\to U'\) with \(U'=\bigcup_{i\in I'}A_i\) and \(y(i)\in A_i\) for \(i\in I'\). Since \(A_k\ne\varnothing\), there is some \(a\in A_k\). Let \(U=\bigcup_{i\in I}A_i\), so that \(U'\subseteq U\) and \(a\in U\). Then the graph of \(y\) is a subset of \(I'\times U\), and the set \(x=\{(i,y(i))\mid i\in I'\}\cup\{(k,a)\}\subseteq I\times U\) is functional, since \(k\notin I'\), and has domain \(I'\cup\{k\}=I\). It is therefore the graph of a function \(x\colon I\to U\) with \(x_i=y(i)\in A_i\) for \(i\ne k\) and \(x_k=a\in A_k\). So \(x\in\prod_{i\in I}A_i\).
\end{proof}

Each step of this proof picks one element of one nonempty set, which is ordinary logic. For an infinite index set, infinitely many such choices would have to be made at once, and the induction gives no way of doing this. In fact, the statement that \(\prod_{i\in I}A_i\) is nonempty whenever every \(A_i\) is nonempty, for arbitrary families of sets, is equivalent to the axiom of choice; see \PMlinkname{product of non-empty set of non-empty sets is non-empty}{ProductOfNonemptySetOfNonemptySetsIsNonempty} and \PMlinkname{variations on axiom of choice}{VariationsOnAxiomOfChoice}. This equivalence is not proved here. In particular cases no choice is needed, because a rule singling out one element of each factor is available:
\begin{itemize}
\item if every \(A_i\) equals one nonempty set \(A\), pick one \(a\in A\); the constant family \((a)_{i\in I}\) lies in the product;
\item if every \(A_i\) is a nonempty subset of \(\mathbb{N}\), the family \((\min A_i)_{i\in I}\) lies in the product, because every nonempty subset of \(\mathbb{N}\) has a least element.
\end{itemize}

\begin{proposition}
Let \((A_i)_{i\in I}\) be a family of sets and \(j\in I\). The projection \(\pi_j\) is surjective if and only if \(A_j=\varnothing\) or \(\prod_{i\in I}A_i\ne\varnothing\). In particular, if the product is nonempty (for instance, if all factors are nonempty and \(I\) is finite), every projection is surjective.
\end{proposition}

\begin{proof}
If \(A_j=\varnothing\), then \(\pi_j\) is surjective, as there is nothing to hit. Suppose the product contains an element \(y\), and let \(a\in A_j\). Define \(x\) by \(x_j=a\) and \(x_i=y_i\) for \(i\ne j\), that is, take the graph \(\{(i,y_i)\mid i\in I,\ i\ne j\}\cup\{(j,a)\}\subseteq I\times U\), which is functional with domain \(I\). Then \(x_i\in A_i\) for every \(i\), so \(x\) lies in the product, and \(\pi_j(x)=a\). Hence \(\pi_j\) is surjective. Conversely, if \(\pi_j\) is surjective and \(A_j\ne\varnothing\), then some \(a\in A_j\) equals \(\pi_j(x)\) for some \(x\) in the product, so the product is nonempty. The last sentence follows from the previous proposition.
\end{proof}

The nonemptiness of the product cannot be omitted: for \(A_1=\{0\}\) and \(A_2=\varnothing\), the product \(\prod_{i\in\{1,2\}}A_i\) is empty, so \(\pi_1\colon\varnothing\to\{0\}\) is not surjective.

\begin{example}
If \(A_n=\mathbb{R}\) for every \(n\in\mathbb{N}\), then \(\prod_{n\in\mathbb{N}}A_n=\mathbb{R}^{\mathbb{N}}\) by part (3) of the first proposition. This is the set of all real sequences \((x_n)_{n\in\mathbb{N}}\), and \(\pi_n\) sends a sequence to its \(n\)-th term.
\end{example}

\begin{example}
Let \(A_n=\{0,1,\dots,n\}\) for \(n\ge1\). An element of \(\prod_{n\ge1}A_n\) is a sequence \((x_n)_{n\ge1}\) of integers with \(0\le x_n\le n\) for every \(n\). The product is nonempty without any appeal to choice, since the sequences \(x_n=0\) and \(x_n=n\) belong to it. It is infinite: for \(k\ge1\) let \(e^{(k)}\) be the sequence with \(e^{(k)}_k=1\) and \(e^{(k)}_n=0\) for \(n\ne k\), which lies in the product because \(1\in A_k\). If \(k\ne l\), then \(e^{(k)}_k=1\ne0=e^{(l)}_k\), so these sequences are pairwise distinct. By the previous proposition every projection \(\pi_m\) is onto \(A_m\).
\end{example}

\begin{example}
Let \(X\) be a nonempty set and \(A_x=\{0,1\}\) for every \(x\in X\). Then \(\prod_{x\in X}A_x=\{0,1\}^X\), the set of functions \(X\to\{0,1\}\). Such families correspond exactly to subsets of \(X\). To a subset \(S\subseteq X\) assign the family \(s\) with \(s_x=1\) if \(x\in S\) and \(s_x=0\) if \(x\notin S\); to a family \(s\) assign the subset \(\{x\in X\mid s_x=1\}\). Starting from \(S\), one gets back \(\{x\in X\mid s_x=1\}=S\). Starting from \(s\), one gets back a family that takes the value \(1\) exactly where \(s\) does. Since both take only the values \(0\) and \(1\), the two families agree everywhere. So the two assignments are mutually inverse. These \(\{0,1\}\)-valued functions are studied further as indicator functions of subsets.
\end{example}
""")


# Publishing order (as on the live site, where option 20 chose it); the parts were drafted
# in a different dependency order.
ORDER = ["naive-set-theory", "ordered-pair", "cartesian-product", "reflexive", "set-operations",
         "function", "indexed-family", "generalized-cartesian-product", "symmetric-relation",
         "transitive-relation", "antisymmetric-relation", "total-order", "partition", "image",
         "composition-of-functions", "injective-function", "surjective-function",
         "bijective-function", "indicator-function"]
assert sorted(ORDER) == sorted(e["slug"] for e in E)
E.sort(key=lambda e: ORDER.index(e["slug"]))


if __name__ == "__main__":
    run_batch(E, EXTRA_ESCAPES, __doc__, ENTRY_ESCAPES, KEEP_LINKED)
