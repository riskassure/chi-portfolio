"""Add an explanatory entry on diagram chasing, with a proved example."""
import argparse
from datetime import datetime
from pathlib import Path
import re
import sqlite3

from add_five_and_snake_lemmas import (
    SRC, entry, source, document_types, create_math_concept,
    fetch_public_math_concept_detail, relate, links, SNAKE_REF,
)


ENTRY = entry('diagram chasing', 'diagram-chasing', 'DiagramChasing',
    ['diagram chase', 'diagram chases', 'diagram-chasing'], [],
    ['exact-sequences-of-modules', 'module-kernels-and-cokernels',
     'five-lemma', 'snake-lemma', 'mitchells-embedding-theorem'], r"""
Diagram chasing is a proof technique used throughout homological algebra. This entry explains its elementwise form for unital left modules over an associative unital ring \(R\), including abelian groups when \(R=\mathbb{Z}\).
\begin{definition}
A \emph{diagram chase} is an argument that follows elements through the maps of a commutative diagram, using hypotheses such as exactness, injectivity and surjectivity to obtain lifts, identify images, or show that elements vanish. The technique is called \emph{diagram chasing}. The diagram records the maps and their relations; each step of the argument still needs an algebraic justification.
\end{definition}
\section*{The basic moves}
Moving forward along \(f:M\to N\) sends \(x\) to \(f(x)\). Moving backward requires a reason: a preimage exists if the target element is in \(\im f\), in particular if \(f\) is surjective. Such a preimage is called a lift here and need not be unique.

In an \PMlinkname{exact sequence}{ExactSequencesOfModules} \(A\xrightarrow{i}B\xrightarrow{p}C\), the equation \(p(b)=0\) allows us to write \(b=i(a)\), since \(\ker p=\im i\). Commutativity lets us compare the two paths around a square. Injectivity lets us infer \(x=0\) from \(f(x)=0\). If two choices have the same image under a homomorphism, their difference lies in its kernel; exactness can then supply a correction term.

\section*{A worked chase: detecting injectivity}
\begin{proposition}
Suppose this diagram of module homomorphisms commutes, both rows are exact at their middle terms, and \(i'\) is injective:
\[
\xymatrix{
A\ar[r]^{i}\ar[d]_{\alpha} & B\ar[r]^{p}\ar[d]_{\beta} & C\ar[d]_{\gamma} \\
A'\ar[r]_{i'} & B'\ar[r]_{p'} & C'
}
\]
If \(\alpha\) and \(\gamma\) are injective, then \(\beta\) is injective.
\end{proposition}
\begin{proof}
Start with \(b\in B\) such that \(\beta(b)=0\). Moving right and then down gives
\[
\gamma(p(b))=p'(\beta(b))=0.
\]
Injectivity of \(\gamma\) implies \(p(b)=0\). Exactness of the upper row now supplies a lift \(a\in A\) with \(i(a)=b\).

Move down from \(a\), then right in the lower row. Commutativity gives
\[
i'(\alpha(a))=\beta(i(a))=\beta(b)=0.
\]
Injectivity of \(i'\) gives \(\alpha(a)=0\), and injectivity of \(\alpha\) gives \(a=0\). Consequently \(b=i(a)=0\). Thus \(\ker\beta=0\), which means \(\beta\) is injective.
\end{proof}
\begin{remark}
This is the injectivity part of the short five lemma. The chase actually uses exactness only at \(B\), not at \(B'\); the symmetric row hypotheses situate it in the usual exact-sequence setting. A lift was chosen but no new function was defined, so independence of that choice was unnecessary: any available lift proves the desired conclusion.
\end{remark}
\section*{Constructing maps by chasing}
The \PMlinkname{snake lemma}{SnakeLemma} uses a chase to construct its connecting homomorphism. There, choosing lifts is part of defining a function. One must prove that different choices yield the same output class and that the resulting function is additive and respects scalar multiplication. The snake lemma entry carries out those checks and proves exactness at each term. The \PMlinkname{five lemma}{FiveLemma} provides a longer chase, with separate arguments for injectivity and surjectivity.

\section*{Limits and common pitfalls}
An arrow cannot be traversed backward without an image or surjectivity argument. A commuting square alone does not provide a lift. Also, \(pi=0\) implies only \(\im i\subseteq\ker p\); equality, namely exactness, is needed to lift every element killed by \(p\).

Objects of an arbitrary category need not have elements, so this elementwise method cannot be transferred to every category without justification. In abelian categories, one can use categorical proofs or suitable embedding results; see \PMlinkname{Mitchell's embedding theorem}{MitchellsEmbeddingTheorem}. The concrete module setting used here avoids that additional step.
""", SNAKE_REF)


def verify(c):
    d = fetch_public_math_concept_detail(c.cursor(), ENTRY['slug'])
    assert d and d['owner'] == 'CWoo' and d['cleaned_tex'] == source(ENTRY)
    assert set(d['types']) == set(document_types(ENTRY))
    assert set(d['synonyms']) == set(ENTRY['synonyms'])
    assert {r['code'] for r in d['classifications']} == set(ENTRY['classifications'])
    html = d['display_tex']
    pattern = r'\\\(.*?\\\)|\\\[.*?\\\]'
    assert re.findall(pattern, source(ENTRY), re.S) == re.findall(pattern, html, re.S)
    for label, target in re.findall(r'\\PMlinkname\{([^{}]*)\}\{([^{}]*)\}', ENTRY['body']):
        row = c.execute('SELECT slug FROM math_concepts WHERE canonical_name=?', (target,)).fetchone()
        assert row and row[0] in links(html), (label, target)
    for origin in ['five-lemma', 'snake-lemma']:
        assert ENTRY['slug'] in links(fetch_public_math_concept_detail(c.cursor(), origin)['display_tex']), origin
    assert html.count('class="math-env math-env-proof"') == 1
    assert c.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    assert not c.execute('PRAGMA foreign_key_check').fetchall()
    print('Verified', d['id'], ENTRY['slug'])


def apply(path):
    if not path.is_file():
        raise FileNotFoundError(path)
    with sqlite3.connect(path) as c:
        c.row_factory = sqlite3.Row
        c.execute('PRAGMA foreign_keys=ON')
        e = ENTRY
        if not c.execute('SELECT 1 FROM math_concepts WHERE slug=?', (e['slug'],)).fetchone():
            for term in [e['title'], *e['synonyms']]:
                assert not c.execute('''SELECT title FROM math_concepts WHERE lower(title)=lower(?)
                    UNION SELECT synonym_text FROM math_synonyms WHERE lower(synonym_text)=lower(?)
                    UNION SELECT defined_term FROM math_definitions WHERE lower(defined_term)=lower(?)''',
                    (term, term, term)).fetchone(), term
            create_math_concept(c.cursor(), e['canonical'], e['slug'], e['title'],
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'CWoo', source(e), 1,
                e['classifications'], document_types(e), e['synonyms'], e['definitions'], [])
        for target in e['related']:
            relate(c, e['slug'], target)
        for origin in ['five-lemma', 'snake-lemma', 'exact-sequences-of-modules']:
            relate(c, origin, e['slug'])
        verify(c)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path, default=SRC.parent / 'portfolio.db')
    apply(parser.parse_args().db)
