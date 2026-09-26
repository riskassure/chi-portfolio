"""Add abelian, modular and distributive definitions and repair precategory prerequisites."""
import argparse
from datetime import datetime
from pathlib import Path
import re
import sqlite3
from add_group_centralizers_and_series import entry, SRC, source, document_types, create_math_concept, fetch_public_math_concept_detail, relate, links
from services.math.concept_render_service import render_tex_reusing_existing_diagrams
from services.math.concept_metadata_service import _attach_types
from services.math.autolink_service import apply_math_autolinker

ENTRIES=[]
def add(title,slug,canonical,codes,related,body,reference):
    e=entry(title,slug,canonical,codes,[],[],related,body)
    e['reference']=reference
    e['escapes']+=['object','objects','categorical','context','theory','kernel','cokernel','image','coimage','modular','distributive','normal','identity','inverse','injective','surjective','sum','diamond','pentagon','lattice','lattices','meet','join','vertices','open']
    ENTRIES.append(e)

add('abelian category','abelian-category','AbelianCategory','18E10',
    'additive-category preadditive-category kernel-of-a-morphism image-of-a-morphism five-lemma snake-lemma',r"""
\begin{definition}
An \emph{abelian category} is a locally small additive category in which every morphism has a kernel and a cokernel, and the canonical morphism from its coimage to its image is an isomorphism. Here additive means that hom-sets are abelian groups, composition is bilinear, and a zero object and finite biproducts exist. A biproduct is a finite direct sum serving as both product and coproduct.

For \(f:A\to B\), the relevant objects are
\[
\operatorname{Coim}(f)=\operatorname{coker}(\ker f),\qquad
\operatorname{Im}(f)=\ker(\operatorname{coker}f).
\]
The kernel of the cokernel is taken as a morphism into \(B\), and the cokernel of the kernel as a morphism out of \(A\). Their universal properties factor \(f\) as
\[
A\longrightarrow\operatorname{Coim}(f)\longrightarrow\operatorname{Im}(f)\longrightarrow B.
\]
The axiom requires the middle arrow to be an isomorphism. Merely having kernels and cokernels is not sufficient.
\end{definition}
\begin{example}
The category of left modules over a fixed associative unital ring \(R\) is abelian. Addition of homomorphisms is pointwise, and finite direct sums are biproducts. For \(f:M\to N\), its kernel is the usual submodule, its cokernel is \(N/f(M)\), and its categorical image is \(f(M)\). The map \(M/\ker f\to f(M)\), \(m+\ker f\mapsto f(m)\), is well-defined, injective, surjective, and linear. Hence it supplies the required isomorphism. Abelian groups and vector spaces are special cases.
\end{example}
\begin{proposition}
In an abelian category, a morphism that is both monic and epic is an isomorphism.
\end{proposition}
\begin{proof}
For a monic \(f:A\to B\), any \(g:X\to A\) with \(fg=0\) is zero by cancellation against \(f0\), so \(0\to A\) is a kernel. Dually, for epic \(f\), the morphism \(B\to0\) is a cokernel. Consequently \(\operatorname{Coim}(f)\cong A\) and \(\operatorname{Im}(f)\cong B\), and the canonical middle isomorphism is \(f\) under these identifications.
\end{proof}
\begin{remark}
An abelian category is a setting for homological algebra, not a category whose objects must themselves be abelian groups. The collection's \PMlinkname{five lemma}{FiveLemma} and \PMlinkname{snake lemma}{SnakeLemma} give module versions. The general categorical versions are part of the theory of abelian categories. See also \PMlinkname{additive category}{AdditiveCategory} and \PMlinkname{kernels and cokernels}{KernelOfAMorphism}.
\end{remark}
""",('The Stacks Project','Abelian categories, Section 12.5','https://stacks.math.columbia.edu/tag/00ZX'))

REF=('J. B. Nation','Notes on Lattice Theory','https://math.hawaii.edu/~jb/lattice2017.pdf')
add('modular lattice','modular-lattice','ModularLattice','06C05',
    'distributive-lattice normal-subgroup-lattice-is-modular',r"""
A lattice is a partially ordered set in which each pair has a greatest lower bound (meet, \(x\wedge y\)) and a least upper bound (join, \(x\vee y\)).
\begin{definition}
A lattice \(L\) is \emph{modular} if, for all \(x,y,z\in L\),
\[
x\le z\quad\Longrightarrow\quad x\vee(y\wedge z)=(x\vee y)\wedge z.
\]
The hypothesis \(x\le z\) is essential. No greatest or least element is required by this definition.
\end{definition}
\begin{proposition}
The submodules of a module form a modular lattice, with intersection as meet and submodule sum as join.
\end{proposition}
\begin{proof}
Let \(U\subseteq W\) be submodules and \(V\) another submodule. Every element of \(U+(V\cap W)\) lies in both \(U+V\) and \(W\). Conversely, if \(t=u+v\in(U+V)\cap W\), then \(v=t-u\in W\), because \(t,u\in W\). Hence \(v\in V\cap W\) and \(t\in U+(V\cap W)\). This proves the modular identity.
\end{proof}
\begin{example}
In particular, subspaces of a vector space form a modular lattice. In \(k^2\), take the three distinct lines \(A=k(1,0)\), \(B=k(0,1)\), and \(C=k(1,1)\). Then \(A\cap(B+C)=A\), whereas \((A\cap B)+(A\cap C)=0\), so this lattice is not distributive. The five subspaces \(0,A,B,C,k^2\) form the diamond lattice \(M_3\).
\end{example}
\begin{example}
The pentagon lattice \(N_5\) has elements \(0,a,b,c,1\), with \(0<a<b<1\), \(0<c<1\), and \(c\) incomparable with \(a,b\). It is not modular: \(a\vee(c\wedge b)=a\), but \((a\vee c)\wedge b=b\).
\end{example}
Every \PMlinkname{distributive lattice}{DistributiveLattice} is modular. Normal subgroups provide another important example; see \PMlinkname{normal subgroup lattice is modular}{NormalSubgroupLatticeIsModular}.
""",REF)
add('distributive lattice','distributive-lattice','DistributiveLattice','06D05',
    'modular-lattice representing-a-distributive-lattice-by-ring-of-sets',r"""
For a lattice, write \(\wedge\) for greatest lower bound and \(\vee\) for least upper bound.
\begin{definition}
A \emph{distributive lattice} satisfies both identities
\[
x\wedge(y\vee z)=(x\wedge y)\vee(x\wedge z),
\]
\[
x\vee(y\wedge z)=(x\vee y)\wedge(x\vee z)
\]
for all elements. No boundedness or complements are assumed.
\end{definition}
\begin{example}
The power set \(\mathcal P(S)\), ordered by inclusion, is distributive: meet is intersection and join is union, and the identities follow by testing membership. Every chain is distributive, with minimum and maximum as its operations: after interchanging \(y,z\) if necessary, assume \(y\le z\) and evaluate each side. The open sets of a topological space also form a distributive lattice under finite intersection and union.
\end{example}
\begin{proposition}
Every distributive lattice is modular.
\end{proposition}
\begin{proof}
If \(x\le z\), the second distributive identity gives
\[
x\vee(y\wedge z)=(x\vee y)\wedge(x\vee z)=(x\vee y)\wedge z.
\]
This is the modular law.
\end{proof}
\begin{example}
The converse fails. In the five-element diamond \(M_3\), let \(a,b,c\) be its three incomparable middle elements. Their pairwise meets are \(0\) and pairwise joins are \(1\). Thus \(a\wedge(b\vee c)=a\), but \((a\wedge b)\vee(a\wedge c)=0\). This lattice is modular, as realized by the five subspaces in the \PMlinkname{modular lattice}{ModularLattice} entry.
\end{example}
For a representation theorem and proof, see \PMlinkname{representing a distributive lattice by a ring of sets}{RepresentingADistributiveLatticeByRingOfSets}.
""",REF)

DIAMOND=r"""\[
\xymatrix{
& 1 & \\
a\ar@{-}[ur] & b\ar@{-}[u] & c\ar@{-}[ul] \\
& 0\ar@{-}[ul]\ar@{-}[u]\ar@{-}[ur] &
}
\]"""
PENTAGON=r"""\[
\xymatrix{
& 1 & \\
b\ar@{-}[ur] & & c\ar@{-}[ul] \\
a\ar@{-}[u] & & \\
& 0\ar@{-}[ul]\ar@{-}[uur] &
}
\]"""
BOOLEAN=r"""\[
\xymatrix{
& \{p,q\} & \\
\{p\}\ar@{-}[ur] & & \{q\}\ar@{-}[ul] \\
& \varnothing\ar@{-}[ul]\ar@{-}[ur] &
}
\]"""
for e in ENTRIES:
    if e['slug']=='modular-lattice':
        e['body']+='\n'+r'\section*{Hasse diagrams}'+'\nHigher vertices represent larger elements; edges show covering relations.\n'+r'\textbf{Diamond \(M_3\): modular, not distributive.}'+'\n'+DIAMOND+'\n'+r'\textbf{Pentagon \(N_5\): not modular.}'+'\n'+PENTAGON
    elif e['slug']=='distributive-lattice':
        e['body']+='\n'+r'\section*{Hasse diagrams}'+'\nHigher vertices represent larger elements; edges show covering relations.\n'+r'\textbf{The power set of \(\{p,q\}\): distributive.}'+'\n'+BOOLEAN+'\n'+r'\textbf{Diamond \(M_3\): a nondistributive contrast.}'+'\n'+DIAMOND

def save(c,d,tex,now):
    c.execute('UPDATE math_concepts SET cleaned_tex=?,rendered_tex=?,updated_at=? WHERE id=?',
        (tex,render_tex_reusing_existing_diagrams(d['id'],tex,c.cursor()),now,d['id']))
    _attach_types(c.cursor(),d['id'],document_types({'body':tex}))

def apply(path):
    with sqlite3.connect(path) as c:
        c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON')
        now=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for e in ENTRIES:
            if c.execute('SELECT 1 FROM math_concepts WHERE slug=?',(e['slug'],)).fetchone():continue
            assert not c.execute('SELECT 1 FROM math_concepts WHERE lower(title)=lower(?)',(e['title'],)).fetchone()
            create_math_concept(c.cursor(),e['canonical'],e['slug'],e['title'],now,'CWoo',source(e),1,e['classifications'],document_types(e),[],[],[])
        d=fetch_public_math_concept_detail(c.cursor(),'precategory');tex=d['cleaned_tex']
        tex=tex.replace('then $A=B$ and $C=D$','then $A=C$ and $B=D$')
        marker=r'\subsubsection*{Paths Defined}'
        note=r'''\begin{remark}
For the free-category construction below, assume the precategory is small. Then all finite paths form a set, so each resulting hom-collection is a set. With a proper class of objects, set-sized arrow collections for individual pairs do not alone ensure that the paths between two fixed objects form a set: there may be a proper class of possible intermediate objects. The term precategory here means objects and arrows without composition or identities; terminology varies between authors.
\end{remark}
'''
        if note not in tex:tex=tex.replace(marker,note+'\n'+marker)
        tex=tex.replace('with with domain','with domain')
        if tex!=d['cleaned_tex']:save(c,d,tex,now)
        d=fetch_public_math_concept_detail(c.cursor(),'additive-category');tex=d['cleaned_tex']
        tex=tex.replace(r'\item $\mathcal{C}$ is a preadditive category, and',r'\item $\mathcal{C}$ is a preadditive category under the convention used here: its hom-sets are abelian groups, composition is bilinear, and it has a zero object; and')
        old='This shows that $D$ is also the coproduct of $A$ and $B$ with morphisms $'+r'\alpha'+'$ and $'+r'\beta'+ '$.'
        new=r'For uniqueness, the product property gives $\alpha\pi_A+\beta\pi_B=1_D$, since both sides have projections $\pi_A$ and $\pi_B$. Thus any $t:D\to C$ with $t\alpha=r$ and $t\beta=s$ must satisfy $t=t(\alpha\pi_A+\beta\pi_B)=r\pi_A+s\pi_B$. This proves the coproduct universal property.'
        tex=tex.replace(old,new)
        if tex!=d['cleaned_tex']:save(c,d,tex,now)
        if not c.execute('SELECT 1 FROM math_synonyms WHERE concept_id=? AND synonym_text=?',(d['id'],'pre-category')).fetchone():
            c.execute('INSERT INTO math_synonyms(concept_id,synonym_text) VALUES (?,?)',(d['id'],'pre-category'))
        d=fetch_public_math_concept_detail(c.cursor(),'preadditive-category');tex=d['cleaned_tex']
        tex=tex.replace('the category of chain complexes, and the category of rings (not necessarily containing a multiplicative identity).','the category of chain complexes of modules over a fixed ring.')
        tex=tex.replace('However, the category of rings with 1 is not an ab-category (see below for more detail).',r'The category of rings, with or without a required identity, is not in general an ab-category under pointwise addition of homomorphisms: even the sum of the identity map of $\mathbb{Z}$ with itself, $n\mapsto2n$, is not multiplicative.')
        tex=tex.replace(r'In the category $\mathcal{R}$ of unital rings, $\mathbb{Z}$ is an initial object, but it has no terminal object, therefore $\mathcal{R}$ is not an ab-category.',r'In the category of unital rings including the zero ring, $\mathbb{Z}$ is initial and the zero ring is terminal, but these are not isomorphic, so there is no zero object. In the convention excluding the zero ring, there is no terminal object: maps from fields of distinct positive characteristics cannot both enter a nonzero ring. Either convention fails to give an ab-category.')
        if tex!=d['cleaned_tex']:save(c,d,tex,now)
        for e in ENTRIES:
            for slug in e['related']:relate(c,e['slug'],slug);relate(c,slug,e['slug'])
        for e in ENTRIES:
            d=fetch_public_math_concept_detail(c.cursor(),e['slug'])
            assert d['owner']=='CWoo' and d['cleaned_tex']==source(e)
            assert set(d['types'])==set(document_types(e))
            assert {r['code'] for r in d['classifications']}==set(e['classifications'])
            pat=r'\\\(.*?\\\)|\\\[.*?\\\]'
            assert re.findall(pat,d['cleaned_tex'],re.S)==re.findall(pat,d['display_tex'],re.S)
            for label,target in re.findall(r'\\PMlinkname\{([^{}]*)\}\{([^{}]*)\}',e['body']):
                r=c.execute('SELECT slug FROM math_concepts WHERE canonical_name=?',(target,)).fetchone()
                assert r and r[0] in links(d['display_tex']),(label,target)
            assert e['slug'] in links(apply_math_autolinker(-1,e['title'],c.cursor()))
            print('Verified',d['id'],e['slug'])
        assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        assert not c.execute('PRAGMA foreign_key_check').fetchall()

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--db',type=Path,default=SRC.parent/'portfolio.db')
    args=p.parse_args()
    if not args.db.is_file():raise FileNotFoundError(args.db)
    apply(args.db)
