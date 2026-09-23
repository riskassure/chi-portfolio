"""Add five foundational gaps, reviewed against titles, aliases and full source.

Existing specialized entries use these notions without defining them generally.
Keep existing entries intact; add reciprocal related links and verify incoming
links through the public renderer. Re-running validates without duplicating.
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
from services.math.public_concept_detail_service import fetch_public_math_concept_detail
from services.math.public_search_service import search_public_math_library
from add_eight_algebra_concepts import source, Links
from add_sylow_theorems import document_types
from add_twenty_concepts_20260922 import ESCAPES


def entry(title, slug, canonical, codes, synonyms, definitions, related, body):
    return dict(title=title, slug=slug, canonical=canonical,
                classifications=codes, synonyms=synonyms, definitions=definitions,
                related=related, body=body,
                reference=('Emily Riehl', 'Category Theory in Context, Chapters 1, 2 and 4',
                           'https://emilyriehl.github.io/files/context.pdf'),
                escapes=list(ESCAPES) + ['arrow', 'object', 'identity', 'normal', 'natural',
                    'component', 'unit', 'element', 'inverse', 'composition', 'domain',
                    'codomain', 'small', 'large', 'class', 'map', 'structure', 'fixed',
                    'isomorphism', 'homomorphism', 'full', 'faithful', 'initial', 'terminal',
                    'zero', 'universal', 'opposite', 'dual', 'free', 'unique', 'relation',
                    'underlying', 'word', 'length', 'empty', 'finite', 'forgetful',
                    'categorical', 'connected', 'injective', 'surjective', 'instance',
                    'compatible', 'square', 'language', 'endomorphism'])


ENTRIES = [
entry('category', 'category', 'Category', ['18A05'], ['categories'],
      ['small category', 'locally small category', 'identity morphism', 'categorical isomorphism'],
      ['functor', 'natural-transformation', 'precategory', 'subcategory', 'dual-category', 'preorder-as-a-category'], r"""
A category records which objects can be connected by morphisms and how those morphisms compose.
\begin{definition}
A \emph{category} \(\mathcal{C}\) has a collection of objects and, for each ordered pair \(A,B\), a collection \(\Hom_{\mathcal{C}}(A,B)\) of morphisms from \(A\) to \(B\). Each morphism has a specified source and target. There are composition operations
\[
\Hom_{\mathcal{C}}(B,C)\times\Hom_{\mathcal{C}}(A,B)\longrightarrow\Hom_{\mathcal{C}}(A,C),\qquad (g,f)\longmapsto g\circ f,
\]
and an \emph{identity morphism} \(1_A:A\to A\) for every object. The axioms are
\[
h\circ(g\circ f)=(h\circ g)\circ f,\qquad 1_B\circ f=f=f\circ1_A
\]
whenever the compositions are defined. In \(g\circ f\), the morphism \(f\) is applied first.

A category is \emph{locally small} if every morphism collection \(\Hom_{\mathcal{C}}(A,B)\) is a set. It is \emph{small} if both its objects and all its morphisms form sets. Unless stated otherwise, the examples here are locally small; the objects may form a proper class. These size conventions distinguish the category of all sets from a small category.

A \emph{categorical isomorphism} is a morphism \(f:A\to B\) with an inverse \(g:B\to A\) satisfying \(g\circ f=1_A\) and \(f\circ g=1_B\).
\end{definition}
\begin{proposition}
An object's identity morphism is unique, and an isomorphism has a unique inverse.
\end{proposition}
\begin{proof}
If \(e,e':A\to A\) both satisfy the identity laws, then \(e=e\circ e'=e'\). If \(g,h\) are inverses of \(f\), then \(g=g\circ(f\circ h)=(g\circ f)\circ h=h\).
\end{proof}
\begin{example}
In \(\mathbf{Set}\), objects are sets and morphisms are functions. In \(\mathbf{Grp}\), objects are groups and morphisms are group homomorphisms. In the category of left modules over a specified ring \(R\), morphisms are \(R\)-linear maps. Ordinary composition and identity maps give the axioms in each case.

A monoid gives a category with one object: its elements are the endomorphisms, its multiplication is composition, and its unit is the identity. A partially ordered set gives a category with one morphism \(a\to b\) exactly when \(a\le b\); transitivity supplies composition. See \PMlinkname{preorder as a category}{PreorderAsACategory}.
\end{example}
\begin{remark}
Objects need not be sets equipped with structure, and morphisms need not be functions. The axioms concern identities and composition. A \PMlinkname{precategory}{Precategory} in this collection supplies objects and arrows before the additional categorical structure is imposed.
\end{remark}
"""),
entry('functor', 'functor', 'Functor', ['18A05','18A25'], ['functors', 'covariant functor'],
      ['contravariant functor', 'forgetful functor'],
      ['category','natural-transformation','identity-functor','constant-functor','dual-category','faithful-functor','full-functor'], r"""
Functors carry objects and morphisms between categories while respecting the rules for composition.
\begin{definition}
A \emph{functor} (or \emph{covariant functor}) \(F:\mathcal{C}\to\mathcal{D}\) assigns an object \(F(A)\) to each object \(A\) and a morphism \(F(f):F(A)\to F(B)\) to each morphism \(f:A\to B\), such that
\[
F(1_A)=1_{F(A)},\qquad F(g\circ f)=F(g)\circ F(f).
\]
A \emph{contravariant functor} from \(\mathcal{C}\) to \(\mathcal{D}\) is a covariant functor \(\mathcal{C}^{\mathrm{op}}\to\mathcal{D}\), using the \PMlinkname{opposite category}{DualCategory}. Viewed on arrows of \(\mathcal{C}\), it sends \(f:A\to B\) to \(F(f):F(B)\to F(A)\) and satisfies \(F(g\circ f)=F(f)\circ F(g)\).
\end{definition}
\begin{example}
A \emph{forgetful functor} discards part of an object's structure and views its morphisms as maps preserving the retained structure. For instance, \(U:\mathbf{Grp}\to\mathbf{Set}\) assigns the underlying set to a group and the underlying function to a homomorphism. Composition and identities are unchanged.

For a locally small category and an object \(A\), the assignment \(X\mapsto\Hom(A,X)\) is covariant: \(f:X\to Y\) acts by \(h\mapsto f\circ h\). The assignment \(X\mapsto\Hom(X,A)\) is contravariant: \(f:X\to Y\) acts by \(h\mapsto h\circ f\). Associativity and the identity laws verify both functor axioms.
\end{example}
\begin{proposition}
A functor preserves \PMlinkname{categorical isomorphisms}{Category}.
\end{proposition}
\begin{proof}
If \(g\circ f=1_A\) and \(f\circ g=1_B\), applying \(F\) gives \(F(g)\circ F(f)=1_{F(A)}\) and \(F(f)\circ F(g)=1_{F(B)}\). Hence \(F(g)\) is the inverse of \(F(f)\).
\end{proof}
\begin{remark}
A functor need not be injective on objects or morphisms. The stronger conditions on morphism maps are treated in \PMlinkname{faithful functor}{FaithfulFunctor} and \PMlinkname{full functor}{FullFunctor}. Identity and constant functors already have their own entries.
\end{remark}
"""),
entry('natural transformation', 'natural-transformation', 'NaturalTransformation', ['18A25'],
      ['natural transformations'], ['natural isomorphism', 'naturality condition'],
      ['category','functor','functor-category','compositions-of-natural-transformations','unit-of-adjunction'], r"""
A natural transformation compares two functors by maps that are compatible with every morphism in their source category.
\begin{definition}
For functors \(F,G:\mathcal{C}\to\mathcal{D}\), a \emph{natural transformation} \(\eta:F\Rightarrow G\) assigns a component \(\eta_A:F(A)\to G(A)\) to every object \(A\). For each \(f:A\to B\), the \emph{naturality condition} is
\[
G(f)\circ\eta_A=\eta_B\circ F(f).
\]
Both sides are morphisms \(F(A)\to G(B)\): the square with vertical sides \(\eta_A,\eta_B\) commutes. A \emph{natural isomorphism} is a natural transformation admitting an inverse natural transformation under componentwise composition.
\end{definition}
\begin{proposition}
A natural transformation is a natural isomorphism if and only if every component is a categorical isomorphism.
\end{proposition}
\begin{proof}
An inverse transformation provides inverse components. Conversely, suppose each \(\eta_A\) is invertible. Multiplying the naturality equation on the left by \(\eta_B^{-1}\) and on the right by \(\eta_A^{-1}\) gives
\[
F(f)\circ\eta_A^{-1}=\eta_B^{-1}\circ G(f).
\]
Thus the inverse components form a natural transformation \(G\Rightarrow F\), and the composites are identity transformations.
\end{proof}
\begin{example}
On \(\mathbf{Set}\), let \(D(X)=X\times X\) and \(D(f)(x,y)=(f(x),f(y))\). The diagonal maps \(\delta_X(x)=(x,x)\) form a natural transformation from the identity functor to \(D\), because \(D(f)(\delta_X(x))=(f(x),f(x))=\delta_Y(f(x))\). This is not a natural isomorphism: if \(X\) has two distinct elements, \(\delta_X\) is not surjective.
\end{example}
\begin{remark}
Having a map, or even an isomorphism, at every object does not by itself establish naturality; the compatibility equation must also hold. The \PMlinkname{functor category}{FunctorCategory} uses natural transformations as morphisms. Their vertical and horizontal compositions are discussed in \PMlinkname{compositions of natural transformations}{CompositionsOfNaturalTransformations}.
\end{remark}
"""),
entry('initial and terminal objects', 'initial-and-terminal-objects', 'InitialAndTerminalObjects', ['18A05','18A30'],
      [], ['initial object','terminal object','zero object'],
      ['category','dual-category','limiting-cone','universal-arrow','preorder-as-a-category'], r"""
Initial and terminal objects are specified by uniqueness of the morphisms leaving or entering them.
\begin{definition}
An \emph{initial object} \(I\) of \(\mathcal{C}\) has exactly one morphism \(I\to X\) for every object \(X\). A \emph{terminal object} \(T\) has exactly one morphism \(X\to T\) for every object \(X\). A \emph{zero object} is both initial and terminal. Reversing arrows exchanges initial and terminal objects.
\end{definition}
\begin{proposition}
Any two initial objects are uniquely isomorphic; the same holds for terminal objects.
\end{proposition}
\begin{proof}
If \(I,J\) are initial, there are unique maps \(u:I\to J\) and \(v:J\to I\). Each initial object has exactly one endomorphism (a morphism from itself to itself), which must be its identity. Hence \(v\circ u=1_I\) and \(u\circ v=1_J\). The isomorphism is unique because the map \(I\to J\) is unique. Reversing all arrows proves the terminal case.
\end{proof}
\begin{example}
In \(\mathbf{Set}\), the empty set is initial and every singleton is terminal. There is no zero object: a set with a map to the empty set must be empty, but the empty set receives no map from a singleton.

In \(\mathbf{Grp}\), the trivial group is a zero object: a homomorphism into it is unique, and a homomorphism out of it must send its identity to the identity. Likewise the zero module is a zero object among modules over a specified ring.

In a partially ordered set viewed as a category, an initial object is a least element and a terminal object is a greatest element. These conditions are stronger than merely being minimal or maximal. A discrete category with two objects has neither: there are no morphisms between its distinct objects.
\end{example}
\begin{remark}
An initial object need not be an empty underlying set, and a terminal object need not be a singleton underlying set: the chosen category and its morphisms determine the property. In the language of \PMlinkname{limiting cones}{LimitingCone}, a terminal object is the limit of the empty diagram; an initial object is its colimit. Indeed, every object carries the unique empty cone, so the universal condition is precisely the one in the definition.
\end{remark}
"""),
entry('universal arrow', 'universal-arrow', 'UniversalArrow', ['18A40'], ['universal arrows'],
      ['universal arrow from an object to a functor','universal arrow from a functor to an object'],
      ['category','functor','initial-and-terminal-objects','comma-category','unit-of-adjunction','equivalent-definition-of-a-representable-functor'], r"""
A universal arrow expresses a factorization problem in which every admissible map factors uniquely through one chosen object.
\begin{definition}
Let \(U:\mathcal{D}\to\mathcal{C}\) be a functor and \(C\) an object of \(\mathcal{C}\). A \emph{universal arrow from an object to a functor}, from \(C\) to \(U\), is a pair \((D,\eta)\) with \(\eta:C\to U(D)\), such that for every \(D'\) and \(f:C\to U(D')\), there is exactly one \(g:D\to D'\) satisfying
\[
U(g)\circ\eta=f.
\]
Dually, a \emph{universal arrow from a functor to an object}, from \(U\) to \(C\), is a pair \((D,\epsilon)\) with \(\epsilon:U(D)\to C\), such that every \(f:U(D')\to C\) is uniquely of the form
\[
\epsilon\circ U(g)=f,\qquad g:D'\to D.
\]
The direction of the structure map is part of the definition.
\end{definition}
\begin{proposition}
Two universal arrows \((D,\eta)\) and \((E,\theta)\) from the same object \(C\) to the same functor \(U\) are uniquely isomorphic compatibly with their structure maps.
\end{proposition}
\begin{proof}
Universality gives unique \(g:D\to E\) and \(h:E\to D\) with \(U(g)\circ\eta=\theta\) and \(U(h)\circ\theta=\eta\). Then \(U(h\circ g)\circ\eta=\eta\). Since \(1_D\) has this property too, uniqueness gives \(h\circ g=1_D\). Similarly \(g\circ h=1_E\). The required compatibility already determines \(g\) uniquely.
\end{proof}
\begin{example}
Let \(U:\mathbf{Grp}\to\mathbf{Set}\) forget the group operation, let \(C=\{*\}\), and let \(\eta(*)=1\) in the additive group \(\mathbb{Z}\). A function \(f:\{*\}\to U(G)\) chooses an element \(a\in G\). There is a unique group homomorphism \(g:\mathbb{Z}\to G\) with \(g(1)=a\), namely \(g(n)=a^n\). The exponent laws prove it is a homomorphism, and any such homomorphism is determined by the image of \(1\). Thus \((\mathbb{Z},\eta)\) is universal from the singleton to \(U\).
\end{example}
\begin{remark}
The first definition says that \((D,\eta)\) is an initial object in the \PMlinkname{comma category}{CommaCategory} \((C\downarrow U)\): its morphisms are exactly the maps \(g\) with the stated equation. The dual definition gives a terminal object in \((U\downarrow C)\). Equivalently, the first universal arrow supplies bijections \(\Hom_{\mathcal{D}}(D,D')\to\Hom_{\mathcal{C}}(C,U(D'))\), sending \(g\) to \(U(g)\circ\eta\). These are natural in \(D'\) by functoriality. This connects with \PMlinkname{representable functors}{EquivalentDefinitionOfARepresentableFunctor} and the existing \PMlinkname{unit of adjunction}{UnitOfAdjunction} entry.
\end{remark}
"""),
]

ORIGINS = [('identity-functor','functor'),
           ('functor-category','natural-transformation'),
           ('connected-category','initial-and-terminal-objects'),
           ('unit-of-adjunction','universal-arrow'),
           ('subcategory','category')]


def links(html):
    parser = Links(); parser.feed(html)
    return {attrs['href'].split('slug=',1)[1] for attrs,_ in parser.links
            if attrs.get('href','').startswith('concept.html?slug=')}


def relate(c, origin, target):
    a = c.execute('SELECT id FROM math_concepts WHERE slug=?',(origin,)).fetchone()[0]
    b = c.execute('SELECT id,canonical_name FROM math_concepts WHERE slug=?',(target,)).fetchone()
    assert b, target
    if not c.execute('SELECT 1 FROM math_related_concepts WHERE concept_id=? AND related_canonical_name=?',(a,b[1])).fetchone():
        c.execute('INSERT INTO math_related_concepts(concept_id,related_canonical_name,related_concept_id) VALUES(?,?,?)',(a,b[1],b[0]))


def verify(c):
    for e in ENTRIES:
        d = fetch_public_math_concept_detail(c.cursor(),e['slug'])
        assert d and d['owner']=='CWoo' and d['cleaned_tex']==source(e),e['slug']
        for key in ['synonyms','definitions']: assert set(d[key])==set(e[key])
        assert set(d['types'])==set(document_types(e))
        assert {r['code'] for r in d['classifications']}==set(e['classifications'])
        html=d['display_tex']; assert r'\PMlink' not in html
        assert e['slug'] not in links(html)
        for env in ['definition','proof','example','remark','proposition']:
            assert html.count('class="math-env math-env-'+env+'"')==e['body'].count(r'\begin{'+env+'}'),(e['slug'],env)
        pattern=r'\\\(.*?\\\)|\\\[.*?\\\]'
        assert re.findall(pattern,source(e),re.S)==re.findall(pattern,html,re.S),e['slug']
        for target in links(html):
            assert c.execute('SELECT 1 FROM math_concepts WHERE slug=?',(target,)).fetchone(),target
        for label,target in re.findall(r'\\PMlinkname\{([^{}]*)\}\{([^{}]*)\}',e['body']):
            row=c.execute('SELECT slug FROM math_concepts WHERE canonical_name=?',(target,)).fetchone()
            assert row and row[0] in links(html),(label,target)
        assert any(r['slug']==e['slug'] for r in search_public_math_library(c.cursor(),e['title'])['data'])
        related=c.execute('SELECT related_concept_id FROM math_related_concepts WHERE concept_id=?',(d['id'],)).fetchall()
        assert len(related)>=len(e['related']) and all(r[0] for r in related)
        print('Verified',d['id'],e['slug'])
    for origin,target in ORIGINS:
        assert target in links(fetch_public_math_concept_detail(c.cursor(),origin)['display_tex']),(origin,target)
    assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    assert not c.execute('PRAGMA foreign_key_check').fetchall()


def apply(path):
    if not path.is_file(): raise FileNotFoundError(path)
    with sqlite3.connect(path) as c:
        c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON')
        now=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for e in ENTRIES:
            if c.execute('SELECT 1 FROM math_concepts WHERE slug=?',(e['slug'],)).fetchone(): continue
            for term in [e['title'],*e['synonyms'],*e['definitions']]:
                assert not c.execute('''SELECT title FROM math_concepts WHERE lower(title)=lower(?)
                    UNION SELECT synonym_text FROM math_synonyms WHERE lower(synonym_text)=lower(?)
                    UNION SELECT defined_term FROM math_definitions WHERE lower(defined_term)=lower(?)''',(term,term,term)).fetchone(),term
            for code in e['classifications']:
                assert c.execute('SELECT id FROM math_classifications WHERE code=?',(code,)).fetchone(),code
            create_math_concept(c.cursor(),e['canonical'],e['slug'],e['title'],now,'CWoo',source(e),1,
                                e['classifications'],document_types(e),e['synonyms'],e['definitions'],[])
        for e in ENTRIES:
            for target in e['related']: relate(c,e['slug'],target)
        for origin,target in ORIGINS: relate(c,origin,target)
        verify(c)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db',type=Path,default=SRC.parent/'portfolio.db')
    apply(parser.parse_args().db)
