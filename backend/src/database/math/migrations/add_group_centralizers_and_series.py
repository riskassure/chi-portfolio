"""Group centralizers and series; power series and ordinal cofinality already exist."""
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

REF = ('J. S. Milne', 'Group Theory, Chapters 4 and 6', 'https://jmilne.org/math/CourseNotes/GTe6.pdf')
def entry(title,slug,canonical,codes,synonyms,definitions,related,body):
    return dict(title=title,slug=slug,canonical=canonical,classifications=codes.split(),
        synonyms=synonyms,definitions=definitions,related=related.split(),body=body,
        reference=REF,escapes=list(ESCAPES)+['centralizer','centralizers','symmetric',
            'type','types','class','length','factor','series','invariant','refinement',
            'simple','composition','nor','instance','element','kernel','image',
            'transitive','inverse image'])

ENTRIES = [
entry('centralizer in a group','centralizer-in-a-group','CentralizerInAGroup',
    '20E45 20E34', ['group centralizer','centralizer of a subset of a group'], [],
    'group center-of-a-group normalizer-of-a-subgroup centralizer-in-a-ring',r"""
The centralizer collects all elements that commute with a specified subset of a group.
\begin{definition}
For a subset \(S\subseteq G\), its \emph{centralizer in a group} \(G\) is
\[
C_G(S)=\{g\in G:gs=sg\text{ for every }s\in S\}.
\]
For one element \(s\), write \(C_G(s)=C_G(\{s\})\). We have \(C_G(\varnothing)=G\) and \(C_G(G)=Z(G)\), the \PMlinkname{center of the group}{CenterOfAGroup}.
\end{definition}
\begin{proposition}
The centralizer \(C_G(S)\) is a subgroup. If \(H\le G\), then \(C_G(H)\) is normal in \(N_G(H)\), and \(H\cap C_G(H)=Z(H)\).
\end{proposition}
\begin{proof}
The identity commutes with every element. If \(a,b\) commute with every \(s\in S\), then \((ab)s=a(sb)=s(ab)\), and rearranging \(as=sa\) shows that \(a^{-1}\) commutes with \(s\). This proves the subgroup assertion.

An element commuting with all of \(H\) normalizes \(H\), so \(C_G(H)\le N_G(H)\). For \(n\in N_G(H)\), \(c\in C_G(H)\), and \(h\in H\), put \(h_0=n^{-1}hn\in H\). Then
\[
(ncn^{-1})h=nc h_0n^{-1}=n h_0cn^{-1}=h(ncn^{-1}).
\]
Thus conjugation by \(n\) sends the centralizer into itself; conjugation by \(n^{-1}\) gives the reverse inclusion. Finally, elements of \(H\) commuting with all of \(H\) are exactly its center.
\end{proof}
\begin{example}
In \(S_3\), \(C_{S_3}((12))=\{1,(12)\}\). A commuting permutation must preserve the set \(\{1,2\}\), since conjugation sends \((12)\) to \((g(1)\quad g(2))\). Also \(C_{S_3}(\gen{(123)})=\gen{(123)}\), whereas its normalizer is all of \(S_3\). A transposition normalizes this cyclic subgroup but conjugates its generator to its inverse rather than fixing it.
\end{example}
\begin{remark}
The \PMlinkname{normalizer}{NormalizerOfASubgroup} preserves a subgroup as a set under conjugation; the centralizer fixes each of its elements. The same commuting equation defines a \PMlinkname{centralizer in a ring}{CentralizerinaRing}, but the ambient algebraic objects are different. Qualified names keep these meanings separate in the collection.
\end{remark}
"""),
entry('normal and subnormal series of groups','normal-series-of-groups','NormalSeriesOfGroups',
    '20E15 20F14', ['normal series','subnormal series','normal series of a group','subnormal series of a group'],
    ['subnormal subgroup','factor group of a series'],
    'group normalizer-of-a-subgroup composition-series-of-a-group solvable-group',r"""
Subgroup series describe a group in successive quotient layers. Two conventions for the word normal occur in the literature, so we distinguish them explicitly.
\begin{definition}
A finite \emph{subnormal series} of \(G\) is a chain
\[
1=G_0\le G_1\le\cdots\le G_n=G
\]
such that \(G_i\trianglelefteq G_{i+1}\) for every \(i<n\). Its \emph{factor groups} are \(G_{i+1}/G_i\). It is a \emph{normal series} in the convention used here if every \(G_i\) is normal in the whole group \(G\). A series is strict if all displayed inclusions are proper. Repeated terms may be deleted.

A subgroup \(H\le G\) is \emph{subnormal} if a finite chain of successive normal inclusions runs from \(H\) to \(G\).
\end{definition}
\begin{remark}
Some authors call a subnormal series a normal series, and call a series whose terms are all normal in \(G\) an invariant series. The explicit normality requirement matters more than the name. Our convention follows the distinction in the reference below.
\end{remark}
\begin{proposition}
Every normal series is subnormal, but the converse fails. Normality is not transitive.
\end{proposition}
\begin{proof}
If \(G_i\) is normal in \(G\), it is preserved by conjugation from the smaller group \(G_{i+1}\), proving the first assertion. For the converse, in \(S_4\) take
\[
1\trianglelefteq H\trianglelefteq V\trianglelefteq S_4,
\]
where \(H=\gen{(12)(34)}\) and \(V=\{1,(12)(34),(13)(24),(14)(23)\}\). The group \(V\) is abelian, so \(H\) is normal in \(V\). Conjugation in \(S_4\) permutes the three double transpositions, so \(V\) is normal in \(S_4\). But conjugation by \((23)\) takes \((12)(34)\) to \((13)(24)\notin H\). Hence \(H\) is not normal in \(S_4\), and this series is not normal in our stronger convention.
\end{proof}
\begin{example}
The chain \(1\trianglelefteq A_3\trianglelefteq S_3\) is a normal series, with factors isomorphic to \(C_3\) and \(C_2\). Here \(C_m\) denotes a cyclic group of order \(m\).
\end{example}
A strict subnormal series with simple factors is a \PMlinkname{composition series}{CompositionSeriesOfAGroup}. The successive quotients need not themselves be subgroups of \(G\).
"""),
entry('composition series of a group','composition-series-of-a-group','CompositionSeriesOfAGroup',
    '20E15 20E34', ['composition series','group composition series'],
    ['composition factor of a group'],
    'normal-series-of-groups group solvable-group locally-finite-group',r"""
A composition series breaks a group into quotient layers with no further nontrivial normal subgroup structure.
\begin{definition}
A \emph{composition series} of a group \(G\) is a finite strict \PMlinkname{subnormal series}{NormalSeriesOfGroups}
\[
1=G_0\triangleleft G_1\triangleleft\cdots\triangleleft G_n=G
\]
in which every factor \(G_{i+1}/G_i\) is a nontrivial simple group. A group is simple if it is nontrivial and its only normal subgroups are itself and the trivial subgroup. The quotients are the \emph{composition factors of the group}, and \(n\) is the length of the series. The trivial group has the empty series of length zero.
\end{definition}
\begin{proposition}
A finite strict subnormal series is a composition series exactly when no proper subnormal refinement can be inserted into it. Every finite group has a composition series.
\end{proposition}
\begin{proof}
For normal \(N\trianglelefteq K\), an intermediate normal subgroup \(N<L<K\) gives a nontrivial proper normal subgroup \(L/N\) of \(K/N\). Conversely, the inverse image of such a subgroup under \(K\to K/N\) is normal in \(K\) and lies strictly between \(N\) and \(K\). Thus a simple factor prevents any refinement. If a longer subnormal refinement exists, its penultimate subgroup immediately below \(K\) supplies just such an \(L\). This proves the equivalence.

For existence, induct on the order of a finite group. The trivial case is settled. Otherwise choose a maximal proper normal subgroup \(N\), which exists because the group has finitely many subgroups. By the preceding correspondence \(G/N\) is simple. By induction \(N\) has a composition series, and adjoining \(G\) completes one for \(G\).
\end{proof}
\begin{example}
For \(S_3\), the series \(1\triangleleft A_3\triangleleft S_3\) has factors \(C_3,C_2\). A cyclic group of prime order has a one-step composition series. For a cyclic group of order six, the chains through its subgroup of order two and through its subgroup of order three give different series, with the same factors in opposite orders.
\end{example}
\begin{remark}
Infinite groups need not admit a finite composition series. For example, any proposed series for \(\mathbb{Z}\) would start \(0<H\), where \(H=m\mathbb{Z}\) for some \(m\ge1\). But \(2m\mathbb{Z}\) is a nontrivial proper normal subgroup of \(H\), so the first factor is not simple. Also, terms of a composition series need only be normal in the next term, not in all of \(G\).
\end{remark}
"""),
]


def verify(c):
    for e in ENTRIES:
        d=fetch_public_math_concept_detail(c.cursor(),e['slug'])
        assert d and d['owner']=='CWoo' and d['cleaned_tex']==source(e)
        assert set(d['types'])==set(document_types(e))
        assert set(d['synonyms'])==set(e['synonyms'])
        assert set(d['definitions'])==set(e['definitions'])
        assert {r['code'] for r in d['classifications']}==set(e['classifications'])
        html=d['display_tex']
        pattern=r'\\\(.*?\\\)|\\\[.*?\\\]'
        assert re.findall(pattern,source(e),re.S)==re.findall(pattern,html,re.S),e['slug']
        for env in ['definition','proof','proposition','example','remark']:
            assert html.count('class="math-env math-env-'+env+'"')==e['body'].count(r'\begin{'+env+'}'),(e['slug'],env)
        for label,target in re.findall(r'\\PMlinkname\{([^{}]*)\}\{([^{}]*)\}',e['body']):
            row=c.execute('SELECT slug FROM math_concepts WHERE canonical_name=?',(target,)).fetchone()
            assert row and row[0] in links(html),(label,target)
        rows=c.execute('SELECT related_concept_id FROM math_related_concepts WHERE concept_id=?',(d['id'],)).fetchall()
        assert len(rows)>=len(e['related']) and all(r[0] for r in rows)
        assert any(r['slug']==e['slug'] for r in search_public_math_library(c.cursor(),e['title'])['data'])
        print('Verified',d['id'],e['slug'])
    assert 'composition-series-of-a-group' in links(fetch_public_math_concept_detail(c.cursor(),'locally-finite-group')['display_tex'])
    for slug in ['formal-power-series-ring','cofinality-of-an-ordinal']:
        assert fetch_public_math_concept_detail(c.cursor(),slug)
    assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    assert not c.execute('PRAGMA foreign_key_check').fetchall()


def apply(path):
    if not path.is_file(): raise FileNotFoundError(path)
    with sqlite3.connect(path) as c:
        c.row_factory=sqlite3.Row
        c.execute('PRAGMA foreign_keys=ON')
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
        for origin,target in [('center-of-a-group','centralizer-in-a-group'),('normalizer-of-a-subgroup','centralizer-in-a-group'),
                ('centralizer-in-a-ring','centralizer-in-a-group'),('locally-finite-group','composition-series-of-a-group'),
                ('solvable-group','normal-series-of-groups')]: relate(c,origin,target)
        verify(c)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--db',type=Path,default=SRC.parent/'portfolio.db')
    apply(p.parse_args().db)
