"""Eight computability concepts; Ackermann is already defined in existing entries."""
import argparse
from datetime import datetime
from pathlib import Path
import re
import sqlite3
from add_five_and_snake_lemmas import (
    SRC, source, document_types, create_math_concept,
    fetch_public_math_concept_detail, search_public_math_library, relate, links,
)
from add_twenty_concepts_20260922 import ESCAPES

ENTRIES=[]
def add(title,slug,codes,aliases,definitions,related,body):
    ENTRIES.append(dict(title=title,slug=slug,canonical=''.join(s.capitalize() for s in slug.split('-')),
        classifications=codes.split(),synonyms=aliases,definitions=definitions,related=related.split(),body=body,
        reference=('Andrew Marks','Computability Theory','https://math.berkeley.edu/~marks/notes/computability_notes_v1.pdf'),
        escapes=list(ESCAPES)+['degree','degrees','jump','simple','immune','truth table','index set',
            'complement','diagonal','diagonalization','universal','normal','class','classes','instance',
            'representative','separate','separating','finite stage','stage','stages','eventually',
            'enumeration','enumerable','domain','partial function','halting','machine','uniform','limit',
            'information','reflexive','transitive','converge','nor']))

add('halting problem','halting-problem','03D10 03D25',[],['diagonal halting set'],
    'formal-definition-of-a-turing-machine recursive-set many-one-reducibility turing-jump',r"""
The halting problem asks whether a specified program will finish on a specified input.
\begin{definition}
Fix an effective enumeration \((\varphi_e)_{e\in\mathbb{N}}\) of the partial computable functions and a computable encoding \(\langle e,x\rangle\) of pairs of natural numbers. Write \(\varphi_e(x)\downarrow\) when program \(e\) halts on input \(x\). The \emph{halting problem} is membership in
\[
H=\{\langle e,x\rangle:\varphi_e(x)\downarrow\}.
\]
The \emph{diagonal halting set} is \(K=\{e:\varphi_e(e)\downarrow\}\).
\end{definition}
\begin{theorem}
Both \(H\) and \(K\) are computably enumerable, but neither is computable.
\end{theorem}
\begin{proof}
Simulating a program recognizes a positive instance when it halts, so both sets are [[recursive-set|computably enumerable]]. Suppose a total program decided \(K\). Construct a program which, on input \(e\), loops forever if the decider answers yes and halts if it answers no. Let \(d\) be its index. Applied to \(d\), either answer contradicts the described behavior. Thus \(K\) is not computable. If \(H\) were computable, querying \(\langle e,e\rangle\) would decide \(K\), which is impossible.
\end{proof}
\begin{remark}
Conversely, from \(e,x\) one can effectively write a program that ignores its input and simulates \(\varphi_e(x)\). Its index belongs to \(K\) exactly when \(\langle e,x\rangle\in H\). Thus these two versions are many-one equivalent. Undecidability concerns one algorithm solving every instance, not the impossibility of analyzing any particular program.
\end{remark}
""")

add('Turing degree','turing-degree','03D28',['degree of Turing unsolvability'],['Turing join'],
    'turing-reducibility recursive-set halting-problem turing-jump',r"""
Turing degrees classify sets by the information they provide to an algorithm.
\begin{definition}
Sets \(A,B\subseteq\mathbb{N}\) have the same \emph{Turing degree} if \(A\le_T B\) and \(B\le_T A\), using [[turing-reducibility|Turing reducibility]]. The degree \(\deg_T(A)\) is the equivalence class of \(A\). The order on degrees is induced by \(\le_T\). The degree \(\mathbf0\) consists of the computable sets.
\end{definition}
\begin{definition}
The \emph{Turing join} of sets is
\[
A\oplus B=\{2n:n\in A\}\cup\{2n+1:n\in B\}.
\]
\end{definition}
\begin{proposition}
Turing degrees form a partially ordered set with least element \(\mathbf0\). The degree of \(A\oplus B\) is the least upper bound of the degrees of \(A\) and \(B\).
\end{proposition}
\begin{proof}
Turing reducibility is reflexive by directly querying the oracle and transitive by replacing oracle queries with the corresponding oracle computations. Quotienting by mutual reducibility therefore makes it antisymmetric. A computable set can be decided without consulting any oracle. Querying even or odd positions recovers \(A\) or \(B\) from their join. Conversely, if an oracle computes both sets, test parity and use the corresponding algorithm to decide their join.
\end{proof}
\begin{example}
A set and its complement always have the same degree, since an oracle answer can be negated. The degree of the diagonal halting set is conventionally written \(\mathbf0'\), and is strictly above \(\mathbf0\).
\end{example}
""")

add('Turing jump','turing-jump','03D28 03D55',['jump of a set'],[],
    'turing-reducibility turing-degree halting-problem',r"""
The Turing jump turns an oracle into the halting problem for programs using that oracle.
\begin{definition}
Enumerate oracle programs effectively as \(\Phi_e\). For \(A\subseteq\mathbb{N}\), its \emph{Turing jump} is
\[
A'=\{e:\Phi_e^A(e)\downarrow\}.
\]
The superscript means that membership queries to \(A\) may be answered during the computation. The set \(A'\) is computably enumerable relative to \(A\), by simulation.
\end{definition}
\begin{theorem}
For every \(A\), we have \(A<_T A'\).
\end{theorem}
\begin{proof}
Given \(x\), effectively produce the index \(q(x)\) of an oracle program that ignores its input, asks whether \(x\) is in the oracle, and halts exactly when the answer is yes. Then \(x\in A\) exactly when \(q(x)\in A'\), proving \(A\le_T A'\).

If an \(A\)-oracle program decided \(A'\), form an \(A\)-oracle program that, on input \(e\), halts exactly when this decider says \(e\notin A'\). At its own index \(d\), it halts exactly when it does not halt, a contradiction. Thus \(A'\not\le_T A\).
\end{proof}
\begin{remark}
If \(A\le_T B\), a simulation using the fixed reduction replaces \(A\)-queries by \(B\)-computations. Given \(e\), one can effectively produce a \(B\)-oracle program that ignores its input and simulates \(\Phi_e^A(e)\). Asking \(B'\) whether that program halts decides membership in \(A'\). Hence \(A'\le_T B'\), and the jump is well-defined on Turing degrees. Iterating gives a strictly increasing hierarchy of degrees.
\end{remark}
""")

add('truth-table reducibility','truth-table-reducibility','03D30',['truth-table reduction'],[],
    'turing-reducibility many-one-reducibility recursive-set',r"""
Truth-table reductions make their entire finite list of oracle queries before seeing any answers.
\begin{definition}
For sets \(A,B\subseteq\mathbb{N}\), write \(A\le_{tt}B\) if a total computable procedure, given \(x\), outputs a finite query list \(q_1,\ldots,q_k\) and a Boolean truth table \(t_x:\{0,1\}^k\to\{0,1\}\) such that
\[
\chi_A(x)=t_x(\chi_B(q_1),\ldots,\chi_B(q_k)).
\]
Here \(\chi_B\) is the characteristic function. The table specifies an answer for every possible response pattern, and \(k\) may depend on \(x\), including \(k=0\).
\end{definition}
\begin{proposition}
Many-one reducibility implies truth-table reducibility, which implies Turing reducibility. Truth-table reducibility is transitive.
\end{proposition}
\begin{proof}
A many-one reduction uses one query and returns its answer. A Turing machine can compute the query list, ask its queries, and evaluate the table. For transitivity, replace each query in the first reduction by the finite list and table supplied by the second. Concatenate the finitely many lists and compose their Boolean tables. This yields a total effective procedure of the required form.
\end{proof}
\begin{example}
The complement of \(B\) is truth-table reducible to \(B\): query \(x\) and negate the answer. Unlike an arbitrary Turing reduction, the choice of later questions cannot depend on earlier oracle answers. Unlike polynomial-time reductions, this definition places no efficiency requirement on computing the finite table.
\end{example}
""")

add('limit computable set','limit-computable-set','03D55',
    ['limit-computable set'],[],
    'recursive-set halting-problem arithmetical-hierarchy',r"""
Limit computation permits an algorithm to revise an answer, provided its guesses eventually settle correctly on each input.
\begin{definition}
A set \(A\subseteq\mathbb{N}\) is \emph{limit computable} if there is a total computable function \(a:\mathbb{N}^2\to\{0,1\}\) such that, for each \(x\),
\[
\lim_{s\to\infty}a(x,s)=\chi_A(x).
\]
Because the values are binary, this means that some stage \(s_x\) satisfies \(a(x,s)=\chi_A(x)\) for every \(s\ge s_x\). The stabilization stage need not be computably knowable.
\end{definition}
\begin{proposition}
Every computably enumerable set is limit computable. Limit computable sets are closed under complement, finite union and finite intersection.
\end{proposition}
\begin{proof}
For a computably enumerable set, guess zero until its recognizing program halts on the input, and guess one from then on. Simulating for at most \(s\) steps makes each stage computable. For complement negate the guesses. For union and intersection use Boolean disjunction and conjunction of two approximations; once both have settled on an input, so has the combined approximation.
\end{proof}
\begin{example}
For the [[halting-problem|diagonal halting set]], let \(a(e,s)=1\) exactly when program \(e\) on input \(e\) halts within \(s\) steps. These guesses converge, although the halting set is not computable. This illustrates why convergence of guesses is weaker than an algorithm knowing when its answer is final.
\end{example}
""")

add('immune set','immune-set','03D25',[],[],
    'recursive-set simple-set',r"""
Immunity rules out even an infinite effectively recognizable subset of an infinite set.
\begin{definition}
A set \(I\subseteq\mathbb{N}\) is \emph{immune} if it is infinite and has no infinite computably enumerable subset. Computably enumerable means that membership has a program halting exactly on the positive instances, as in [[recursive-set|recursive and recursively enumerable sets]].
\end{definition}
\begin{proposition}
An infinite set is immune exactly when it has no infinite computable subset. An immune set cannot itself be computably enumerable.
\end{proposition}
\begin{proof}
Every computable set is computably enumerable. Conversely, from an infinite computably enumerable set \(W\), construct a computable strictly increasing sequence: wait for any first enumerated number, then for a number larger than the last chosen, and repeat. Each wait finishes because an infinite subset of \(\mathbb{N}\) is unbounded. Its range is an infinite computable subset of \(W\): to decide whether \(x\) is in the range, compute terms until reaching or exceeding \(x\). This proves the equivalence. If an immune set were computably enumerable, it would itself violate its defining condition.
\end{proof}
\begin{remark}
Removing finitely many elements from an immune set leaves an immune set, since it remains infinite and any computably enumerable subset would also be a subset of the original set. The [[simple-set|simple-set construction]] gives an explicit method of producing a computably enumerable set whose complement is immune.
\end{remark}
""")

add('simple set','simple-set','03D25',[],[],
    'immune-set recursive-set',r"""
Simple sets are computably enumerable sets with complements too sparse in an effective sense to contain an infinite computably enumerable subset.
\begin{definition}
A set \(S\subseteq\mathbb{N}\) is \emph{simple} if it is computably enumerable and its complement is [[immune-set|immune]]. In particular, the complement must be infinite.
\end{definition}
\begin{theorem}
There exists a simple set.
\end{theorem}
\begin{proof}
List all computably enumerable sets as \(W_0,W_1,\ldots\), where \(W_e\) is the halting domain of program \(e\). Obtain finite increasing approximations \(W_{e,s}\) by bounded simulations. Start with \(S\) empty and a separate unfulfilled requirement for each \(e\).

At stage \(s\), examine every \(e\le s\). If its requirement is unfulfilled and \(W_{e,s}\) contains some \(x>2e\), enumerate the least such \(x\) into \(S\) and mark that requirement fulfilled. Each requirement acts at most once, and this is an effective enumeration.

Every infinite \(W_e\) eventually supplies an element larger than \(2e\), so it meets \(S\). The complement is infinite: among \(0,\ldots,2n\), at most \(n\) elements can ever be selected, because a selection there must be made by a requirement \(e<n\), each acting once. Thus at least \(n+1\) of these numbers stay outside \(S\).

If an infinite computably enumerable set were contained in the complement, it would equal some infinite \(W_e\) and would have to meet \(S\), a contradiction. Hence the complement is immune and \(S\) is simple.
\end{proof}
\begin{remark}
A simple set is not computable: otherwise its infinite complement would be computable, hence computably enumerable, contradicting immunity. The word simple here has no connection with simple groups or simple modules.
\end{remark}
""")

add('computably inseparable sets','computably-inseparable-sets','03D25',
    ['recursively inseparable sets'],['computable separator'],
    'recursive-set halting-problem',r"""
Two disjoint sets can be impossible to separate by a computable decision rule, even when each is computably enumerable.
\begin{definition}
For disjoint \(A,B\subseteq\mathbb{N}\), a \emph{computable separator} is a computable set \(D\) with \(A\subseteq D\) and \(D\cap B=\varnothing\). The pair is \emph{computably inseparable} if no such \(D\) exists. The older terminology is recursively inseparable.
\end{definition}
\begin{theorem}
There are disjoint computably enumerable sets that are computably inseparable.
\end{theorem}
\begin{proof}
Fix an effective enumeration \((\varphi_e)\) of partial computable functions and let
\[
A=\{e:\varphi_e(e)\downarrow=0\},\qquad B=\{e:\varphi_e(e)\downarrow=1\}.
\]
They are disjoint, since a halting computation has only one output, and computably enumerable, by simulation. Suppose \(D\) were a computable separator. Its characteristic function is \(\varphi_d\) for some index \(d\). If \(\varphi_d(d)=0\), then \(d\in A\subseteq D\), contradicting that output. If \(\varphi_d(d)=1\), then \(d\in B\), contradicting \(D\cap B=\varnothing\). These exhaust the possible outputs of a characteristic function.
\end{proof}
\begin{remark}
There is no set-theoretic obstacle to separation: \(A\) itself separates the pair. The obstruction is computability. Nor does disjointness alone imply inseparability; if \(A\) is computable, it is already a computable separator from any disjoint \(B\).
\end{remark}
""")

for e in ENTRIES:
    if e['slug'] in {'immune-set','simple-set'}:
        e['reference']=('Alex Simpson','Computability theory lecture notes, Section 9',
            'https://alexksimpson.github.io/Teaching/tinotes.pdf')
    if e['slug']=='truth-table-reducibility':
        e['reference']=('Yannick Forster','Doctoral thesis, Chapter 5: Reducibility',
            'https://ps.uni-saarland.de/~forster/thesis/phd-thesis-yforster-printblack.pdf')


def prepare(c):
    names=dict(c.execute('SELECT slug,canonical_name FROM math_concepts'))
    names.update({e['slug']:e['canonical'] for e in ENTRIES})
    for e in ENTRIES:
        def link(m):
            slug,label=m.groups()
            assert slug in names,slug
            return r'\PMlinkname{'+label+'}{'+names[slug]+'}'
        e['body']=re.sub(r'\[\[([^|\]]+)\|([^\]]+)\]\]',link,e['body'])
        for slug in e['related']: assert slug in names,slug


def verify(c):
    assert len(ENTRIES)==8
    for e in ENTRIES:
        d=fetch_public_math_concept_detail(c.cursor(),e['slug'])
        assert d and d['owner']=='CWoo' and d['cleaned_tex']==source(e)
        assert set(d['types'])==set(document_types(e))
        for key in ['synonyms','definitions']: assert set(d[key])==set(e[key])
        assert {r['code'] for r in d['classifications']}==set(e['classifications'])
        html=d['display_tex']
        pattern=r'\\\(.*?\\\)|\\\[.*?\\\]'
        assert re.findall(pattern,source(e),re.S)==re.findall(pattern,html,re.S),e['slug']
        for env in ['definition','proof','theorem','proposition','example','remark']:
            assert html.count('class="math-env math-env-'+env+'"')==e['body'].count(r'\begin{'+env+'}'),(e['slug'],env)
        for label,target in re.findall(r'\\PMlinkname\{([^{}]*)\}\{([^{}]*)\}',e['body']):
            row=c.execute('SELECT slug FROM math_concepts WHERE canonical_name=?',(target,)).fetchone()
            assert row and row[0] in links(html),(label,target)
        assert any(r['slug']==e['slug'] for r in search_public_math_library(c.cursor(),e['title'])['data'])
        rows=c.execute('SELECT related_concept_id FROM math_related_concepts WHERE concept_id=?',(d['id'],)).fetchall()
        assert len(rows)>=len(e['related']) and all(r[0] for r in rows)
        print('Verified',d['id'],e['slug'])
    assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    assert not c.execute('PRAGMA foreign_key_check').fetchall()


def apply(path):
    if not path.is_file(): raise FileNotFoundError(path)
    with sqlite3.connect(path) as c:
        c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON');prepare(c)
        for e in ENTRIES:
            if c.execute('SELECT 1 FROM math_concepts WHERE slug=?',(e['slug'],)).fetchone(): continue
            for term in [e['title'],*e['synonyms'],*e['definitions']]:
                assert not c.execute('''SELECT title FROM math_concepts WHERE lower(title)=lower(?)
                    UNION SELECT synonym_text FROM math_synonyms WHERE lower(synonym_text)=lower(?)
                    UNION SELECT defined_term FROM math_definitions WHERE lower(defined_term)=lower(?)''',(term,term,term)).fetchone(),term
            for code in e['classifications']:
                assert c.execute('SELECT 1 FROM math_classifications WHERE code=?',(code,)).fetchone(),code
            create_math_concept(c.cursor(),e['canonical'],e['slug'],e['title'],datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'CWoo',source(e),1,e['classifications'],document_types(e),e['synonyms'],e['definitions'],[])
        for e in ENTRIES:
            for target in e['related']: relate(c,e['slug'],target)
        for origin,target in [('turing-reducibility','turing-degree'),('turing-reducibility','turing-jump'),
                ('many-one-reducibility','truth-table-reducibility'),('recursive-set','halting-problem'),
                ('arithmetical-hierarchy','limit-computable-set')]: relate(c,origin,target)
        verify(c)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--db',type=Path,default=SRC.parent/'portfolio.db')
    apply(p.parse_args().db)
