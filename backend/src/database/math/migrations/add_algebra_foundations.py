"""Add group, ring, field, module and an algebra overview, with explicit conventions.

Uses the CMS creation service. Existing entries are preserved on reruns.
"""
import argparse
from datetime import datetime
from pathlib import Path
import re
import sqlite3
import sys

SRC = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(SRC))
from services.math.concept_create_service import create_math_concept
from services.math.concept_render_service import render_tex_reusing_existing_diagrams
from services.math.public_concept_detail_service import fetch_public_math_concept_detail
from add_eight_algebra_concepts import Links, source, types

ENTRIES = [
    dict(title="group", slug="group", canonical="Group", classifications=["20A05"],
         synonyms=["groups"], definitions=["abelian group"],
         related=["group-extension", "algebraic-system"],
         escapes=["identity", "inverse", "order", "product"],
         reference=("R. Sharifi", "Abstract Algebra, Chapter 2", "https://www.math.ucla.edu/~sharifi/notes/algebra-ch02.html"),
         body=r"""Groups describe operations that can be composed and undone, including symmetries.

\begin{definition}
A \emph{group} is a nonempty set \(G\) with a binary operation \(G\times G\to G\), written \((a,b)\mapsto ab\), satisfying:
\begin{enumerate}
\item Associativity: \((ab)c=a(bc)\) for all \(a,b,c\in G\).
\item Identity: there exists \(e\in G\) such that \(ea=ae=a\) for every \(a\in G\).
\item Inverses: for every \(a\in G\) there exists \(a^{-1}\in G\) such that \(aa^{-1}=a^{-1}a=e\).
\end{enumerate}
The group is \emph{abelian} if \(ab=ba\) for all \(a,b\in G\).
\end{definition}

\begin{example}
The integers under addition form an abelian group: the identity is \(0\), and the inverse of \(n\) is \(-n\). The permutations of \(\{1,2,3\}\) under composition form a nonabelian group. Positive integers under addition do not form a group.
\end{example}

\begin{remark}
The operation is part of the data. Nonzero rational numbers form a group under multiplication, but all rational numbers do not, because zero has no multiplicative inverse. Additive notation writes the identity as \(0\) and the inverse of \(a\) as \(-a\).
\end{remark}
"""),
    dict(title="ring", slug="ring", canonical="Ring", classifications=["16B99"],
         synonyms=["rings"], definitions=["unital ring", "commutative ring"],
         related=["matrix-ring", "integral-domain", "division-ring"],
         escapes=["identity", "inverse", "product", "distributive", "state", "generalization"],
         reference=("R. Sharifi", "Abstract Algebra, Chapter 3", "https://www.math.ucla.edu/~sharifi/notes/algebra-ch03.html"),
         body=r"""Rings combine an additive group with a distributive multiplication.

\begin{definition}
A \emph{ring} is a set \(R\) with addition and multiplication such that \((R,+)\) is an abelian group, multiplication is associative, and both distributive laws hold:
\[
a(b+c)=ab+ac,\qquad (a+b)c=ac+bc.
\]
A \emph{unital ring} has an element \(1\) with \(1a=a1=a\) for all \(a\in R\). A \emph{commutative ring} satisfies \(ab=ba\) for all \(a,b\in R\).
\end{definition}

\begin{example}
The integers form a commutative unital ring. The even integers under ordinary addition and multiplication form a ring without a multiplicative identity. The matrix ring \(M_2(\mathbb{Q})\) is unital and noncommutative.
\end{example}

\begin{remark}
This definition allows rings without identity. Many authors require an identity whenever they say ``ring''; entries that need one state it explicitly. A unital ring may have \(1=0\), in which case it is the zero ring. Fields and integral domains require \(1\ne0\). Associativity remains required here; nonassociative rings are a separate generalization.
\end{remark}
"""),
    dict(title="field", slug="field", canonical="Field", classifications=["12E99"],
         synonyms=["fields"], definitions=[],
         related=["division-ring", "integral-domain", "field-extension", "perfect-field"],
         escapes=["identity", "inverse", "product", "field", "fields", "arithmetic", "term", "structure"],
         reference=("The Stacks Project", "Fields: basic definitions", "https://stacks.math.columbia.edu/tag/09FA"),
         body=r"""Fields provide arithmetic in which every nonzero element can be divided by.

\begin{definition}
A \emph{field} is a commutative unital ring \(K\) with \(1\ne0\) such that each nonzero \(a\in K\) has an element \(a^{-1}\in K\) satisfying \(aa^{-1}=1\). Equivalently, \((K,+)\) and \((K\setminus\{0\},\cdot)\) are abelian groups, and multiplication distributes over addition.
\end{definition}

\begin{example}
The rational, real, and complex numbers are fields. For a prime \(p\), the residue classes \(\mathbb{Z}/p\mathbb{Z}\) form a field. The integers do not form a field, since \(2\) has no inverse in \(\mathbb{Z}\).
\end{example}

\begin{remark}
Commutativity distinguishes fields from general division rings. In addition, zero never has an inverse in a field. The term ``field of a relation'' and the term ``field of sets'' refer to different concepts; they do not assert this field structure.
\end{remark}
"""),
    dict(title="module", slug="module", canonical="Module", classifications=["16D10"],
         synonyms=["modules"], definitions=["left module", "right module"],
         related=["module-homomorphism", "endomorphism-ring", "hopfian-module"],
         escapes=["identity", "left", "right", "structure", "distributive", "instance", "basis"],
         reference=("R. Sharifi", "Abstract Algebra, Section 5.1", "https://www.math.ucla.edu/~sharifi/notes/algebra-ch05.html"),
         body=r"""Modules generalize vector spaces by allowing scalars from a ring.

\begin{definition}
Let \(R\) be an associative unital ring. A unital \emph{left module} over \(R\) is an abelian group \((M,+)\) with scalar multiplication \(R\times M\to M\) satisfying, for \(r,s\in R\) and \(m,n\in M\),
\[
r(m+n)=rm+rn,\qquad (r+s)m=rm+sm,
\]
\[
(rs)m=r(sm),\qquad 1m=m.
\]
A unital \emph{right module} uses \(M\times R\to M\), with the corresponding distributive laws, \((mr)s=m(rs)\), and \(m1=m\).
\end{definition}

\begin{example}
Modules over a field are vector spaces. Every abelian group is a \(\mathbb{Z}\)-module, with integer multiplication given by repeated addition and additive inverses. A ring \(R\) is itself a left module over \(R\) under multiplication.
\end{example}

\begin{remark}
Here an unspecified module means a unital left module. Over a noncommutative ring the distinction between left and right matters. Modules need not admit bases; for instance, the \(\mathbb{Z}\)-module \(\mathbb{Z}/2\mathbb{Z}\) has no basis. Its nonzero element is killed by the nonzero scalar \(2\).
\end{remark}
"""),
    dict(title="algebra", slug="algebra", canonical="Algebra", classifications=["17A01", "08A05"],
         synonyms=["algebras"], definitions=["algebra over a ring", "associative algebra", "unital algebra"],
         related=["algebraic-system", "nonassociative-algebra", "matrix-ring", "module-homomorphism"],
         escapes=["identity", "product", "type", "structure", "word algebra", "polynomial algebra", "polynomial"],
         reference=("R. Sharifi", "Abstract Algebra, Section 5.9", "https://www.math.ucla.edu/~sharifi/notes/algebra-ch05.html"),
         body=r"""The word algebra has two major structural meanings: an algebra over a scalar ring, and an algebra in universal algebra.

\begin{definition}
Let \(R\) be a commutative unital ring. An \emph{algebra over a ring} \(R\) is an \(R\)-module \(A\) with an \(R\)-bilinear multiplication \(A\times A\to A\). Thus multiplication distributes over addition and satisfies
\[
(ra)b=r(ab)=a(rb)\qquad(r\in R,\quad a,b\in A).
\]
It is an \emph{associative algebra} if \((ab)c=a(bc)\), and a \emph{unital algebra} if it has a two-sided multiplicative identity. These additional conditions are stated explicitly here. Over a field, the underlying module is a vector space.
\end{definition}

\begin{example}
The polynomial algebra \(R[x]\) and the matrix algebra \(M_n(R)\) are associative and unital. For \(n\ge2\) and nonzero \(R\), the latter is noncommutative.
\end{example}

\begin{remark}
In universal algebra, an algebra means an algebraic system: a set equipped with specified operations, without requiring a scalar ring or a module. Groups and lattices are examples in this sense. See \PMlinkname{algebraic system}{AlgebraicSystem} for its formal definition. The separate entry on nonassociative algebras explains the convention that associativity is not assumed.
\end{remark}
"""),
]

# These are the other established meanings of "field" in this collection.
FIELD_ESCAPES = ["relation", "ring-of-sets", "representing-a-boolean-algebra-by-field-of-sets",
                 "representing-a-distributive-lattice-by-ring-of-sets"]
RING_FIELD_ENTRIES = ["jacobson-radical", "endomorphism-ring", "division-ring", "integral-domain",
                     "field-extension", "splitting-field-of-a-polynomial", "perfect-field", "algebraically-closed-field"]


def apply(path):
    if not path.is_file():
        raise FileNotFoundError(path)
    with sqlite3.connect(path) as c:
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA foreign_keys = ON")
        cursor = c.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        created = []
        for e in ENTRIES:
            if cursor.execute("SELECT id FROM math_concepts WHERE slug=?", (e['slug'],)).fetchone():
                continue
            names = []
            for slug in e['related']:
                row = cursor.execute("SELECT canonical_name FROM math_concepts WHERE slug=?", (slug,)).fetchone()
                if not row:
                    raise ValueError(f'Missing related entry: {slug}')
                names.append(row[0])
            for code in e['classifications']:
                if not cursor.execute('SELECT id FROM math_classifications WHERE code=?', (code,)).fetchone():
                    raise ValueError(f'Missing classification: {code}')
            result = create_math_concept(cursor, e['canonical'], e['slug'], e['title'], now, 'CWoo',
                                         source(e), 1, e['classifications'], types(e), e['synonyms'],
                                         e['definitions'], names)
            created.append(result['slug'])

        for slug in FIELD_ESCAPES + RING_FIELD_ENTRIES:
            row = cursor.execute('SELECT id,cleaned_tex FROM math_concepts WHERE slug=?', (slug,)).fetchone()
            if not row:
                raise ValueError(f'Missing reviewed entry: {slug}')
            old = row['cleaned_tex']
            text = old
            if slug in FIELD_ESCAPES:
                for word in ['field', 'fields']:
                    macro = r'\PMlinkescapeword{' + word + '}'
                    if macro not in text:
                        text = macro + '\n' + text
            else:
                # These escapes originally guarded against the relation-theory
                # meaning. The new exact title now wins for these ring/field uses.
                text = re.sub(r'\\PMlinkescapeword\{field\}\s*', '', text)
                text = text.replace('https://math.ucla.edu/~', r'https://math.ucla.edu/\%7E')
            if text != old:
                rendered = render_tex_reusing_existing_diagrams(row['id'], text, cursor)
                cursor.execute('UPDATE math_concepts SET cleaned_tex=?,rendered_tex=?,updated_at=? WHERE id=?',
                               (text, rendered, now, row['id']))

        for e in ENTRIES:
            d = fetch_public_math_concept_detail(cursor, e['slug'])
            assert d and d['owner'] == 'CWoo'
            assert set(d['types']) == set(types(e))
            assert set(d['synonyms']) == set(e['synonyms'])
            assert set(d['definitions']) == set(e['definitions'])
            assert {r['code'] for r in d['classifications']} == set(e['classifications'])
            assert 'math-env-definition' in d['display_tex'] and 'math-env-example' in d['display_tex']
            assert r'\PMlink' not in d['display_tex']
        for origin, target in [('group-extension','group'), ('division-ring','ring'), ('division-ring','field'),
                               ('module-homomorphism','module'), ('nonassociative-algebra','algebra')]:
            d = fetch_public_math_concept_detail(cursor, origin)
            parser = Links(); parser.feed(d['display_tex'])
            assert any(a.get('href') == 'concept.html?slug='+target and a.get('class') == 'math-autolink'
                       for a, label in parser.links), (origin,target)
        for slug in FIELD_ESCAPES:
            parser = Links(); parser.feed(fetch_public_math_concept_detail(cursor,slug)['display_tex'])
            assert not any(a.get('href')=='concept.html?slug=field' for a,label in parser.links), slug
    return created


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path, default=SRC.parent/'portfolio.db')
    print('Created:', apply(parser.parse_args().db))
