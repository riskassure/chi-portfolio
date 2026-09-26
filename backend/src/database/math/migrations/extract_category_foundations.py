"""Extract six fundamental category-theory definitions into dedicated entries."""
import argparse
from datetime import datetime
from pathlib import Path
import re
import sqlite3
from add_group_centralizers_and_series import entry, SRC, source, document_types, create_math_concept, fetch_public_math_concept_detail, relate, links
from services.math.concept_render_service import render_tex_reusing_existing_diagrams
from services.math.concept_metadata_service import _attach_types
from services.math.public_search_service import search_public_math_library
from services.math.autolink_service import apply_math_autolinker

ENTRIES=[]
def add(title,slug,canonical,codes,origin,body):
    e=entry(title,slug,canonical,codes,[],[],origin,body)
    e['origin']=origin
    e['reference']=('Emily Riehl','Category Theory in Context, Chapters 1 and 3','https://emilyriehl.github.io/files/context.pdf')
    e['escapes']+=['natural','small','large','locally','component','components','full','faithful','context','theory','injective','surjective','homomorphism','isomorphism','inverse image','pointed','dual','dual space','object','objects','terminal','path','monoid','monoids']
    ENTRIES.append(e)

add('natural isomorphism','natural-isomorphism','NaturalIsomorphism','18A05',
    'natural-transformation',r"""
\begin{definition}
For functors \(F,G:\mathcal C\to\mathcal D\), a \emph{natural isomorphism} \(\eta:F\Rightarrow G\) is a [[natural-transformation|natural transformation]] with an inverse natural transformation \(\theta:G\Rightarrow F\). This means \(\theta_A\circ\eta_A=1_{F(A)}\) and \(\eta_A\circ\theta_A=1_{G(A)}\) at every object. Write \(F\cong G\) when one exists.
\end{definition}
\begin{proposition}
A natural transformation is a natural isomorphism if and only if all its components are isomorphisms.
\end{proposition}
\begin{proof}
An inverse transformation gives inverse components. Conversely, if each \(\eta_A\) is invertible, multiply the naturality equation \(G(f)\circ\eta_A=\eta_B\circ F(f)\) by the inverse components to obtain
\[
F(f)\circ\eta_A^{-1}=\eta_B^{-1}\circ G(f).
\]
Thus the inverse components are themselves natural, and compose with \(\eta\) to give the identity transformations.
\end{proof}
\begin{example}
On sets, put \(F(X)=X\times\{*\}\) and \(F(f)(x,*)=(f(x),*)\). The maps \(\eta_X(x,*)=x\) give a natural isomorphism to the identity functor: their inverses send \(x\) to \((x,*)\), and \(f(\eta_X(x,*))=\eta_Y(F(f)(x,*))\).
\end{example}
\begin{remark}
Objectwise isomorphisms must still satisfy naturality. For example, on sets let \(\eta_X:X\to X\) be the identity except on \(\{0,1\}\), where it swaps the elements. All components are bijective, but the map from a singleton selecting \(0\) violates naturality. Hence this family is not a natural isomorphism of the identity functor.
\end{remark}
""")
add('contravariant functor','contravariant-functor','ContravariantFunctor','18A05',
    'functor',r"""
\begin{definition}
A \emph{contravariant functor} from \(\mathcal C\) to \(\mathcal D\) is a covariant [[functor|functor]] \(\mathcal C^{\mathrm{op}}\to\mathcal D\), using the [[dual-category|opposite category]]. In terms of arrows of \(\mathcal C\), it assigns \(F(f):F(B)\to F(A)\) to \(f:A\to B\), and obeys
\[
F(1_A)=1_{F(A)},\qquad F(g\circ f)=F(f)\circ F(g).
\]
Thus both arrow direction and composition order are reversed.
\end{definition}
\begin{example}
For a [[locally-small-category|locally small category]] and a fixed object \(A\), the assignment \(X\mapsto\Hom(X,A)\) is contravariant with values in sets. A morphism \(f:X\to Y\) sends \(h:Y\to A\) to \(h\circ f:X\to A\). Associativity verifies the reversed composition law, and composing with an identity does nothing.
\end{example}
\begin{example}
Taking inverse images is a contravariant functor from sets to sets: assign the power set \(\mathcal P(X)\) to \(X\), and send \(f:X\to Y\) to \(f^{-1}:\mathcal P(Y)\to\mathcal P(X)\). For \(g:Y\to Z\), membership gives \((g\circ f)^{-1}(S)=f^{-1}(g^{-1}(S))\). No inverse function for \(f\) is assumed.
\end{example}
""")
add('forgetful functor','forgetful-functor','ForgetfulFunctor','18A05',
    'functor',r"""
\begin{definition}
A \emph{forgetful functor} is a [[functor|functor]] that retains less structure on objects and regards each morphism as a morphism of the retained structure. This is a descriptive name for a construction, rather than an additional universal axiom on functors. Its action on morphisms must still preserve identities and composition.
\end{definition}
\begin{example}
The functor \(U:\mathbf{Grp}\to\mathbf{Set}\) sends each group to its underlying set and each homomorphism to its underlying function. The functor from groups to monoids forgets the inverse operation; a group homomorphism still preserves multiplication and the identity. From modules over a fixed ring to abelian groups, one forgets scalar multiplication and retains addition.
\end{example}
\begin{proposition}
The underlying-set functor from groups is faithful but not full.
\end{proposition}
\begin{proof}
Two group homomorphisms with the same underlying function agree on every element and hence are equal, proving faithfulness. The constant function \(\mathbb Z\to\mathbb Z\) with value \(1\) is not an additive homomorphism, since it fails to send \(0\) to \(0\). Thus not every function between underlying sets comes from a group homomorphism, so the functor is not full.
\end{proof}
The precise meanings of these properties are in [[faithful-functor|faithful functor]] and [[full-functor|full functor]]. Forgetting structure need not identify objects having different underlying sets; what is forgotten is the extra structure attached to the objects.
""")
add('zero object','zero-object','ZeroObject','18A05 18A30',
    'initial-and-terminal-objects',r"""
\begin{definition}
A \emph{zero object} in a category is an object \(0\) that is both [[initial-and-terminal-objects|initial and terminal]]. Thus, for every object \(X\), there is exactly one morphism \(0\to X\) and exactly one morphism \(X\to0\).
\end{definition}
\begin{proposition}
Any two zero objects are uniquely isomorphic. The composite \(X\to0\to Y\) is independent of which zero object is chosen.
\end{proposition}
\begin{proof}
For zero objects \(0,0'\), the unique arrows in both directions are inverse: their composites are endomorphisms of initial objects and so are identities. For independence, replace \(X\to0\to Y\) by the path through this isomorphism and its inverse. Uniqueness of arrows to terminal objects and from initial objects identifies the resulting composite with \(X\to0'\to Y\).
\end{proof}
This composite is called a zero morphism; the [[kernel-of-a-morphism|kernel entry]] uses these morphisms in its definition.
\begin{example}
The trivial group is a zero object in groups, and the zero module is one in modules over a fixed ring. In pointed sets with basepoint-preserving maps, a singleton is a zero object. In sets with all functions there is no zero object: an initial set is empty, whereas a terminal set is a singleton.
\end{example}
\begin{remark}
Existence of a zero object does not by itself supply addition of morphisms or make a category additive. Pointed sets already illustrate this distinction.
\end{remark}
""")
add('small category','small-category','SmallCategory','18A05',
    'category',r"""
\begin{definition}
A \emph{small category} is a [[category|category]] whose objects form a set and whose morphisms, taken altogether, form a set. These size statements are relative to the chosen set-theoretic foundation or universe.
\end{definition}
\begin{proposition}
A category with a set of objects is small if and only if it is [[locally-small-category|locally small]].
\end{proposition}
\begin{proof}
In a small category each hom-collection is a subset of the set of all morphisms. Conversely, a set of objects gives a set of ordered pairs of objects. If each corresponding hom-collection is a set, their set-indexed disjoint union is a set and contains precisely all morphisms, with their specified sources and targets.
\end{proof}
\begin{example}
A monoid whose elements form a set gives a small one-object category. A set equipped with a partial order gives a small category, with one arrow \(a\to b\) exactly when \(a\le b\). The empty category is small. Small does not mean finite: the ordered natural numbers give an infinite small category.
\end{example}
\begin{remark}
An essentially small category is one equivalent to a small category; it need not itself have a set of objects. See [[skeleton|skeleton]] for this related notion. The category of all sets is not small in the ordinary ambient set/class convention.
\end{remark}
""")
add('locally small category','locally-small-category','LocallySmallCategory','18A05',
    'category',r"""
\begin{definition}
A category \(\mathcal C\) is \emph{locally small} if, for every pair of objects \(A,B\), its morphism collection \(\Hom_{\mathcal C}(A,B)\) is a set. Its objects are not required to form a set. Size is understood relative to a fixed foundation or universe.
\end{definition}
\begin{example}
The category of all sets is locally small: the functions from \(A\) to \(B\) form a subset of \(\mathcal P(A\times B)\), hence a set. It is not small in the ambient set/class convention because there is no set of all sets. Groups and modules over a fixed ring are also locally small, since their homomorphisms form subsets of the corresponding function sets.
\end{example}
\begin{remark}
Every [[small-category|small category]] is locally small, but the converse fails by the example above. Some authors include local smallness in their convention for the word category. Here it is stated explicitly when needed. In particular, it ensures that the hom assignments \(\Hom(A,-)\) and \(\Hom(-,A)\) take values in sets rather than proper classes; the second is a [[contravariant-functor|contravariant functor]].
\end{remark}
""")

def prepare(c):
    names=dict(c.execute('SELECT slug,canonical_name FROM math_concepts'))
    names.update({e['slug']:e['canonical'] for e in ENTRIES})
    for e in ENTRIES:
        for slug,label in re.findall(r'\[\[([^|]+)\|([^\]]+)\]\]',e['body']):
            e['body']=e['body'].replace('[['+slug+'|'+label+']]',r'\PMlinkname{'+label+'}{'+names[slug]+'}')
            if slug not in e['related']: e['related'].append(slug)
        marker=r'\PMlinkname{original discussion}{'+names[e['origin']]+'}'
        if marker not in e['body']: e['body']+='\nSee also the '+marker+'.\n'

def rewrite(tex,slug):
    if slug=='natural-transformation':
        old=r'A \emph{natural isomorphism} is a natural transformation admitting an inverse natural transformation under componentwise composition.'
        tex=tex.replace(old,r'Invertible natural transformations are treated in \PMlinkname{natural isomorphism}{NaturalIsomorphism}.')
        start=tex.index(r'\begin{proposition}');end=tex.index(r'\end{proof}',start)+len(r'\end{proof}')
        tex=tex[:start]+r'The componentwise criterion and its proof are given in that entry.'+tex[end:]
    elif slug=='functor':
        start=tex.index(r'A \emph{contravariant functor}');end=tex.index(r'\end{definition}',start)
        tex=tex[:start]+r'A \PMlinkname{contravariant functor}{ContravariantFunctor} instead reverses arrows and composition order.'+'\n'+tex[end:]
        start=tex.index(r'A \emph{forgetful functor}');end=tex.index('\n\n',start)
        tex=tex[:start]+r'A \PMlinkname{forgetful functor}{ForgetfulFunctor}, such as the underlying-set functor from groups, is a basic example.'+tex[end:]
    elif slug=='initial-and-terminal-objects':
        tex=tex.replace(r'A \emph{zero object} is both initial and terminal.',r'The related notion of a \PMlinkname{zero object}{ZeroObject} has its own entry.')
    else:
        start=tex.index(r'A category is \emph{locally small}');end=tex.index('\n\n',start)
        tex=tex[:start]+r'See \PMlinkname{small category}{SmallCategory} and \PMlinkname{locally small category}{LocallySmallCategory} for the size conventions. Unless stated otherwise, the examples here are locally small; their objects may form a proper class.'+tex[end:]
    return tex

def apply(path):
    with sqlite3.connect(path) as c:
        c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON');prepare(c)
        now=datetime.now().strftime('%Y-%m-%d %H:%M:%S');origins=set()
        for e in ENTRIES:
            if c.execute('SELECT 1 FROM math_concepts WHERE slug=?',(e['slug'],)).fetchone(): continue
            assert not c.execute('SELECT 1 FROM math_concepts WHERE lower(title)=lower(?)',(e['title'],)).fetchone()
            for code in e['classifications']: assert c.execute('SELECT 1 FROM math_classifications WHERE code=?',(code,)).fetchone()
            create_math_concept(c.cursor(),e['canonical'],e['slug'],e['title'],now,'CWoo',source(e),1,e['classifications'],document_types(e),[],[],[])
            origins.add(e['origin'])
        for slug in origins:
            d=fetch_public_math_concept_detail(c.cursor(),slug)
            tex=rewrite(d['cleaned_tex'],slug);assert tex!=d['cleaned_tex']
            rendered=render_tex_reusing_existing_diagrams(d['id'],tex,c.cursor())
            c.execute('UPDATE math_concepts SET cleaned_tex=?,rendered_tex=?,updated_at=? WHERE id=?',(tex,rendered,now,d['id']))
            c.execute('DELETE FROM math_concept_types WHERE concept_id=?',(d['id'],))
            _attach_types(c.cursor(),d['id'],document_types({'body':tex}))
        for e in ENTRIES:
            origin=c.execute('SELECT id FROM math_concepts WHERE slug=?',(e['origin'],)).fetchone()[0]
            c.execute('DELETE FROM math_definitions WHERE concept_id=? AND lower(defined_term)=lower(?)',(origin,e['title']))
            for target in e['related']: relate(c,e['slug'],target)
            relate(c,e['origin'],e['slug'])
        verify(c)

def verify(c):
    for e in ENTRIES:
        d=fetch_public_math_concept_detail(c.cursor(),e['slug'])
        assert d['owner']=='CWoo' and d['cleaned_tex']==source(e)
        assert {r['code'] for r in d['classifications']}==set(e['classifications'])
        for slug in [e['slug'],e['origin']]:
            r=fetch_public_math_concept_detail(c.cursor(),slug)
            assert set(r['types'])==set(document_types({'body':r['cleaned_tex']}))
            pat=r'\\\(.*?\\\)|\\\[.*?\\\]'
            assert re.findall(pat,r['cleaned_tex'],re.S)==re.findall(pat,r['display_tex'],re.S),slug
            for env in ['definition','proof','proposition','example','remark']:
                assert r['display_tex'].count('class="math-env math-env-'+env+'"')==r['cleaned_tex'].count(r'\begin{'+env+'}'),(slug,env)
            assert (e['origin'] if slug==e['slug'] else e['slug']) in links(r['display_tex']),slug
        assert e['slug'] in links(apply_math_autolinker(-1,'<p>'+e['title']+'</p>',c.cursor()))
        assert any(r['slug']==e['slug'] for r in search_public_math_library(c.cursor(),e['title'])['data'])
        print('Verified',d['id'],e['slug'])
    assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    assert not c.execute('PRAGMA foreign_key_check').fetchall()

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--db',type=Path,default=SRC.parent/'portfolio.db')
    args=p.parse_args()
    if not args.db.is_file(): raise FileNotFoundError(args.db)
    apply(args.db)
