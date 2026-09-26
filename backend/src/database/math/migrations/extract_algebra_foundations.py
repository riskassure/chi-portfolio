"""Extract nine embedded algebra definitions, preserving the surrounding arguments."""
import argparse
from datetime import datetime
from pathlib import Path
import re
import sqlite3
from add_group_centralizers_and_series import entry, SRC, source, document_types, create_math_concept, fetch_public_math_concept_detail, relate, links
from services.math.concept_render_service import render_tex_reusing_existing_diagrams
from services.math.public_search_service import search_public_math_library
from services.math.concept_metadata_service import _attach_types

ENTRIES=[]
def add(title,slug,canonical,codes,aliases,origin,term,body):
    e=entry(title,slug,canonical,codes,aliases,[],origin,body)
    e.update(origin=origin,term=term)
    e['escapes']+=['injective','surjective','homomorphism','isomorphism','reflexive','transitive','information','context','theory']
    ENTRIES.append(e)

add('subgroup','subgroup','Subgroup','20A05 20E07',['subgroups'],
    'lagranges-theorem-for-finite-groups','subgroup',r"""
\begin{definition}
A \emph{subgroup} of a group \(G\) is a subset \(H\) containing the identity and closed under multiplication and inverses. Write \(H\le G\). With the inherited operation it is a group; associativity is inherited from \(G\). A proper subgroup is one different from \(G\).
\end{definition}
\begin{proposition}
A nonempty subset \(H\subseteq G\) is a subgroup if and only if \(ab^{-1}\in H\) for all \(a,b\in H\).
\end{proposition}
\begin{proof}
A subgroup satisfies the condition by closure. Conversely, choose \(h\in H\). Then \(hh^{-1}=1\in H\), and \(1b^{-1}\in H\) gives inverses. Applying the condition to \(a\) and \(b^{-1}\) now gives \(ab\in H\).
\end{proof}
\begin{example}
The even integers form a subgroup \(2\mathbb{Z}\le(\mathbb{Z},+)\). The nonnegative integers do not, because they do not contain the additive inverse of \(1\). In \(S_3\), \(\{1,(12)\}\) is a subgroup, but is not a [[normal-subgroup|normal subgroup]].
\end{example}
The order and index of a subgroup are discussed with [[lagranges-theorem-for-finite-groups|Lagrange's theorem]].
""")
add('normal subgroup','normal-subgroup','NormalSubgroup','20E07',['normal subgroups'],
    'normalizer-of-a-subgroup','normal subgroup',r"""
\begin{definition}
A [[subgroup|subgroup]] \(N\le G\) is a \emph{normal subgroup} if \(gNg^{-1}=N\) for every \(g\in G\). Write \(N\trianglelefteq G\).
\end{definition}
\begin{proposition}
Normality is equivalent to \(gN=Ng\) for every \(g\in G\). Every kernel of a group homomorphism is normal.
\end{proposition}
\begin{proof}
Multiplying the set equality \(gNg^{-1}=N\) on the right by \(g\) proves the first equivalence. If \(n\in\ker f\), then \(f(gng^{-1})=f(g)1f(g)^{-1}=1\), giving one inclusion for the kernel; use \(g^{-1}\) for the reverse inclusion.
\end{proof}
\begin{example}
Every subgroup of an abelian group is normal. In \(S_3\), the subgroup \(A_3\) is normal as the kernel of the sign homomorphism. The subgroup \(\{1,(12)\}\) is not normal: conjugation by \((123)\) sends \((12)\) to \((23)\).
\end{example}
Every normal subgroup is the kernel of the canonical map to its [[quotient-group|quotient group]]. Normality in a subgroup need not imply normality in the whole group; see [[normal-series-of-groups|normal and subnormal series]].
""")
add('quotient group','quotient-group','QuotientGroup','20A05 20E15',['factor group','quotient groups'],
    'solvable-group','quotient group',r"""
\begin{definition}
For a [[normal-subgroup|normal subgroup]] \(N\trianglelefteq G\), the \emph{quotient group} (or \emph{factor group}) \(G/N\) consists of left cosets \(gN\), with
\[
(gN)(hN)=ghN.
\]
Its identity is \(N\), and \((gN)^{-1}=g^{-1}N\).
\end{definition}
\begin{proposition}
This operation is well-defined and makes the map \(\pi:G\to G/N\), \(g\mapsto gN\), a surjective homomorphism with kernel \(N\).
\end{proposition}
\begin{proof}
Replacing \(g,h\) by \(gn,hm\), with \(n,m\in N\), changes the product to \(gh(h^{-1}nh)m\). Normality puts the last two factors in \(N\), so the coset is unchanged. Associativity descends from \(G\), and the stated identity and inverses follow immediately. Every coset has a representative, and \(gN=N\) exactly when \(g\in N\), proving the claims about \(\pi\).
\end{proof}
\begin{example}
The quotient \(\mathbb{Z}/n\mathbb{Z}\) is the additive group of residues modulo \(n\). Also \(S_3/A_3\) has two cosets and is cyclic of order two. A coset space \(G/H\) for a nonnormal subgroup generally has no multiplication induced in this way.
\end{example}
""")
add('quotient ring','quotient-ring','QuotientRing','16D25',['factor ring','quotient rings'],
    'ideal-of-a-ring','quotient ring',r"""
\begin{definition}
For an associative ring \(R\) and a two-sided [[ideal-of-a-ring|ideal]] \(I\), the \emph{quotient ring} \(R/I\) has additive cosets as elements, with
\[
(r+I)+(s+I)=(r+s)+I,\qquad (r+I)(s+I)=rs+I.
\]
Its zero is \(I\). If \(R\) is unital, its identity is \(1+I\); the quotient is allowed to be the zero ring.
\end{definition}
\begin{proposition}
The operations are well-defined, and \(r\mapsto r+I\) is a surjective ring homomorphism with kernel \(I\).
\end{proposition}
\begin{proof}
Changing representatives to \(r+i,s+j\) changes their sum by \(i+j\in I\) and their product by \(rj+is+ij\in I\). The ring laws therefore descend from \(R\). The coset of \(r\) is zero exactly when \(r\in I\), and every coset has a representative.
\end{proof}
\begin{example}
In \(\mathbb{Z}/6\mathbb{Z}\), the nonzero classes of \(2\) and \(3\) multiply to zero. The ring \(\mathbb{R}[x]/(x^2+1)\) is isomorphic to \(\mathbb{C}\): evaluate at \(i\); division by \(x^2+1\) leaves a unique remainder \(a+bx\), which maps to \(a+bi\).
\end{example}
A one-sided ideal alone does not in general permit this multiplication. For commutative unital rings, a proper ideal gives a field quotient exactly when it is [[maximal-ideal-of-a-commutative-ring|maximal]].
""")
add('principal ideal of a commutative ring','principal-ideal-of-a-commutative-ring','PrincipalIdealOfACommutativeRing','13A15',[],
    'principal-ideal-domain','principal ideal of a commutative ring',r"""
\begin{definition}
In a commutative unital ring \(R\), an ideal is \emph{principal} if it is generated by a single element \(a\). Explicitly,
\[
(a)=aR=\{ar:r\in R\}.
\]
This is the smallest ideal containing \(a\). The zero ideal is \((0)\), and \(R=(1)\).
\end{definition}
\begin{proposition}
For \(a,b\in R\), we have \((a)\subseteq(b)\) if and only if \(a=br\) for some \(r\in R\).
\end{proposition}
\begin{proof}
Containment puts \(a\) in \((b)\), giving the equation. Conversely, \(as=b(rs)\) for every \(s\in R\), so every element of \((a)\) lies in \((b)\).
\end{proof}
\begin{example}
In \(\mathbb{Z}\), \((6)\subseteq(2)\). In \(k[x,y]\), where \(k\) is a field, \((x,y)\) is not principal. A generator would divide both \(x\) and \(y\). Total degree shows a common divisor of positive degree would have degree one and be a scalar multiple of both, which is impossible. A constant nonzero generator would be a unit, but every member of \((x,y)\) vanishes at \((0,0)\), so this ideal is proper.
\end{example}
A [[principal-ideal-domain|principal ideal domain]] requires every ideal to be principal and also requires the ring to be an integral domain. Noncommutative rings distinguish principal left, right, and two-sided ideals; this entry uses the commutative convention.
""")
add('maximal ideal of a commutative ring','maximal-ideal-of-a-commutative-ring','MaximalIdealOfACommutativeRing','13A15',[],
    'local-ring','maximal ideal of a commutative ring',r"""
\begin{definition}
In a commutative unital ring \(R\), a \emph{maximal ideal} is a proper ideal \(\mathfrak m\) such that no ideal lies strictly between \(\mathfrak m\) and \(R\). The requirement that it be proper excludes \(R\) itself.
\end{definition}
\begin{proposition}
An ideal \(\mathfrak m\) is maximal if and only if the [[quotient-ring|quotient ring]] \(R/\mathfrak m\) is a field.
\end{proposition}
\begin{proof}
For a maximal ideal and \(a\notin\mathfrak m\), the ideal \(\mathfrak m+(a)\) must be \(R\). Write \(1=u+ra\), with \(u\in\mathfrak m\); the class of \(r\) inverts the class of \(a\). Properness ensures the quotient is nonzero. Conversely, if the quotient is a field and an ideal \(J\) strictly contains \(\mathfrak m\), choose \(a\in J\setminus\mathfrak m\). An inverse modulo \(\mathfrak m\) gives \(1-ra\in\mathfrak m\subseteq J\), hence \(1\in J\) and \(J=R\).
\end{proof}
\begin{example}
For a prime \(p\), \(p\mathbb{Z}\) is maximal because its quotient is the field of residues modulo \(p\). The ideal \((x)\) in \(k[x]\) is maximal, since evaluation at zero identifies its quotient with \(k\). The zero ideal of \(\mathbb{Z}\) is not maximal.
\end{example}
Maximal ring ideals should not be confused with maximal ideals of partially ordered sets. A commutative [[local-ring|local ring]] has exactly one maximal ideal; its quotient is the residue field.
""")
add('finite field','finite-field','FiniteField','12E20',['finite fields'],
    'every-finite-integral-domain-is-a-field','finite field',r"""
\begin{definition}
A \emph{finite field} is a field with finitely many elements. Its order is its cardinality. The notation \(\mathbb{F}_q\) denotes a field with \(q\) elements when one exists.
\end{definition}
\begin{proposition}
Every finite field has order \(p^n\), where \(p\) is prime and \(n\ge1\).
\end{proposition}
\begin{proof}
The characteristic cannot be zero, since the integer multiples of \(1\) would then be infinitely many distinct elements. By the [[characteristic-of-a-field-is-zero-or-prime|characteristic theorem]], it is a prime \(p\). The multiples of \(1\) form a copy of \(\mathbb{F}_p\). The given field is a vector space over this subfield. A maximal linearly independent subset exists because the field is finite, and is a finite basis of some size \(n\ge1\). Its coordinate vectors have \(p\) choices in each position, giving \(p^n\) elements.
\end{proof}
\begin{example}
The residues \(\mathbb{Z}/p\mathbb{Z}\) form a field for prime \(p\). A field of four elements is \(\mathbb{F}_2[x]/(x^2+x+1)\). Writing \(a\) for the class of \(x\), its elements are \(0,1,a,a+1\), with \(a^2=a+1\) and \(a(a+1)=1\); thus every nonzero element is invertible. In contrast, \(\mathbb{Z}/4\mathbb{Z}\) is not a field.
\end{example}
\begin{remark}
The classification theorem for finite fields asserts existence and uniqueness up to isomorphism for every prime-power order. See Milne, Fields and Galois Theory, Chapter 4, for a proof. A finite field is different from a finite field extension: for example, \(\mathbb{Q}(\sqrt2)/\mathbb{Q}\) has degree two but both fields are infinite.
\end{remark}
""")
add('minimal polynomial of an algebraic element','minimal-polynomial-of-an-algebraic-element','MinimalPolynomialOfAnAlgebraicElement','12F05',[],
    'separable-field-extension','minimal polynomial of an algebraic element',r"""
\begin{definition}
Let \(L/K\) be a field extension and \(\alpha\in L\) algebraic over \(K\). Its \emph{minimal polynomial over} \(K\), denoted \(m_{\alpha,K}\), is the monic polynomial in \(K[x]\) of least positive degree vanishing at \(\alpha\). Monic means leading coefficient one. The base field is part of the definition.
\end{definition}
\begin{proposition}
The minimal polynomial exists, is unique and irreducible. Every polynomial in \(K[x]\) vanishing at \(\alpha\) is divisible by it.
\end{proposition}
\begin{proof}
Algebraicity supplies a nonzero vanishing polynomial. Choose one of least degree and divide by its leading coefficient; no nonzero constant vanishes. A factorization into two positive-degree polynomials would force one factor to vanish in the extension field, contradicting minimality. Division of any vanishing polynomial by the chosen monic polynomial leaves a remainder of smaller degree that also vanishes, so that remainder is zero. This proves divisibility and, by applying it to another monic polynomial of the same degree, uniqueness.
\end{proof}
\begin{example}
Over \(\mathbb{Q}\), the minimal polynomial of \(\sqrt2\) is \(x^2-2\), since \(\sqrt2\) is irrational. Over \(\mathbb{Q}(\sqrt2)\), it is \(x-\sqrt2\). A transcendental element has no minimal polynomial over the base field.
\end{example}
This entry concerns algebraic elements of field extensions. Minimal polynomials of linear operators are a related but different context. [[separable-field-extension|Separability]] of an algebraic element asks whether this polynomial has repeated roots.
""")
add('Galois extension','galois-extension','GaloisExtension','12F10',['Galois field extension'],
    'galois-group','Galois extension',r"""
\begin{definition}
A \emph{Galois extension} \(L/K\) is an algebraic field extension that is both [[normal-field-extension|normal]] and [[separable-field-extension|separable]]. It need not have finite degree. Its [[galois-group|Galois group]] consists of field automorphisms of \(L\) fixing every element of \(K\).
\end{definition}
\begin{example}
The extension \(\mathbb{Q}(\sqrt2)/\mathbb{Q}\) is Galois: it is the splitting field of the separable polynomial \(x^2-2\). In contrast, \(\mathbb{Q}(\sqrt[3]{2})/\mathbb{Q}\) is separable but not normal. The irreducible polynomial \(x^3-2\) has one root there, but its two nonreal roots cannot lie in this real field; irreducibility follows from the rational-root test for a cubic.
\end{example}
\begin{remark}
A finite extension is Galois exactly when it is the splitting field of a separable polynomial over the base field; equivalently its group of base-field automorphisms has size equal to its degree. These standard characterizations are proved in the reference below. Separability alone or normality alone does not replace the two hypotheses in the definition.
\end{remark}
The [[galois-group|Galois group entry]] explains the convention for naming automorphism groups of extensions that are not Galois.
""")

for i,e in enumerate(ENTRIES):
    e['reference']=(('J. S. Milne','Group Theory, Chapter 1','https://www.jmilne.org/math/CourseNotes/GT.pdf') if i<3 else
        ('Romyar Sharifi','Abstract Algebra, Chapter 3','https://www.math.ucla.edu/~sharifi/notes/algebra-ch03.html') if i<6 else
        ('J. S. Milne','Fields and Galois Theory, Chapters 1, 3 and 4','https://www.jmilne.org/math/CourseNotes/FT.pdf'))

def prepare(c):
    names=dict(c.execute('SELECT slug,canonical_name FROM math_concepts'))
    names.update({e['slug']:e['canonical'] for e in ENTRIES})
    for e in ENTRIES:
        origin_name=c.execute('SELECT title FROM math_concepts WHERE slug=?',(e['origin'],)).fetchone()[0]
        origin_link=r'\PMlinkname{'+origin_name+'}{'+names[e['origin']]+'}'
        if origin_link not in e['body']:
            e['body']+='\nSee also '+origin_link+'.\n'
        targets=re.findall(r'\[\[([^|]+)\|([^\]]+)\]\]',e['body'])
        for slug,label in targets:
            e['body']=e['body'].replace('[['+slug+'|'+label+']]',r'\PMlinkname{'+label+'}{'+names[slug]+'}')
            if slug not in e['related']: e['related'].append(slug)

def rewrite_origin(e,tex):
    link=r'\PMlinkname{'+e['term']+'}{'+e['canonical']+'}'
    # Exact semantic spans: retain other definitions and all surrounding proofs.
    if e['slug']=='subgroup':
        start=tex.index(r'A \emph{subgroup}')
        end=tex.index(' The '+r'\emph{order of a group}',start)
        old=tex[start:end];new='For a '+link+r' \(H\le G\), we use the following terminology.'
    elif e['slug']=='normal-subgroup':
        start=tex.index(r'A \emph{normal subgroup}')
        end=tex.index('\n'+r'\end{definition}',start)
        old=tex[start:end];new=r'The condition \(N_G(H)=G\) says precisely that \(H\) is a '+link+'.'
    elif e['slug']=='quotient-group':
        start=tex.index('For a normal subgroup');end=tex.index('\n'+r'\end{definition}',start)
        old=tex[start:end];new='We use the '+link+r' \(G/N\) whenever \(N\) is normal in \(G\).'
    elif e['slug']=='quotient-ring':
        old=r'The \emph{quotient ring} \(R/I\) has additive cosets as elements, with \((r+I)(s+I)=rs+I\).'
        new='The associated '+link+r' \(R/I\) is defined in its own entry; the following verifies why two-sidedness is required.'
    elif e['slug']=='principal-ideal-of-a-commutative-ring':
        start=tex.index('For a commutative unital ring');end=tex.index(r'A \emph{principal ideal domain}',start)
        old=tex[start:end];new='Use '+r'\((a)\)'+' for the '+link+' generated by '+r'\(a\). '
    elif e['slug']=='maximal-ideal-of-a-commutative-ring':
        old=r'A \emph{maximal ideal of a commutative ring} is a proper ideal contained in no larger proper ideal, so a commutative ring is local precisely when it has exactly one maximal ideal \(\mathfrak m\).'
        new='A commutative ring is local precisely when it has exactly one '+link+r' \(\mathfrak m\).'
    elif e['slug']=='finite-field':
        old=r'A \emph{finite field} is a field whose underlying set has finitely many elements.'
        new='The resulting object is a '+link+'.'
    elif e['slug']=='minimal-polynomial-of-an-algebraic-element':
        start=tex.index(r'For an algebraic element');end=tex.index(r'\begin{definition}',start)
        old=tex[start:end];new=r'For an algebraic element \(\alpha\), write \(m_\alpha\) for its '+link+r'. Its existence, uniqueness, and irreducibility are proved there.'+'\n'+r'\end{definition}'+'\n'
    else:
        old=r'A \emph{Galois extension} is an algebraic extension that is both \PMlinkname{normal}{NormalFieldExtension} and \PMlinkname{separable}{SeparableFieldExtension}. Its \emph{Galois group}'
        new='For a '+link+r', its \emph{Galois group}'
    assert old in tex,(e['slug'],'source changed')
    return tex.replace(old,new,1)

def apply(path):
    with sqlite3.connect(path) as c:
        c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON');prepare(c)
        now=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for e in ENTRIES:
            existing=c.execute('SELECT id FROM math_concepts WHERE slug=?',(e['slug'],)).fetchone()
            if existing: continue
            # A matching embedded definition is expected; a standalone title is not.
            assert not c.execute('SELECT id FROM math_concepts WHERE lower(title)=lower(?)',(e['title'],)).fetchone()
            for code in e['classifications']: assert c.execute('SELECT 1 FROM math_classifications WHERE code=?',(code,)).fetchone(),code
            create_math_concept(c.cursor(),e['canonical'],e['slug'],e['title'],now,'CWoo',source(e),1,e['classifications'],document_types(e),e['synonyms'],[],[])
            d=fetch_public_math_concept_detail(c.cursor(),e['origin'])
            tex=rewrite_origin(e,d['cleaned_tex'])
            rendered=render_tex_reusing_existing_diagrams(d['id'],tex,c.cursor())
            c.execute('UPDATE math_concepts SET cleaned_tex=?,rendered_tex=?,updated_at=? WHERE id=?',(tex,rendered,now,d['id']))
            # The title now registers this concept; remove its old embedded registration.
            c.execute('DELETE FROM math_definitions WHERE concept_id=? AND lower(defined_term)=lower(?)',(d['id'],e['term']))
        for e in ENTRIES:
            origin=fetch_public_math_concept_detail(c.cursor(),e['origin'])
            c.execute('DELETE FROM math_concept_types WHERE concept_id=?',(origin['id'],))
            _attach_types(c.cursor(),origin['id'],document_types({'body':origin['cleaned_tex']}))
            for target in e['related']: relate(c,e['slug'],target)
            relate(c,e['origin'],e['slug'])
        verify(c)

def verify(c):
    for e in ENTRIES:
        d=fetch_public_math_concept_detail(c.cursor(),e['slug'])
        assert d['cleaned_tex']==source(e) and d['owner']=='CWoo'
        assert set(d['types'])==set(document_types(e))
        assert {r['code'] for r in d['classifications']}==set(e['classifications'])
        for slug in [e['slug'],e['origin']]:
            r=fetch_public_math_concept_detail(c.cursor(),slug)
            assert set(r['types'])==set(document_types({'body':r['cleaned_tex']})),slug
            pat=r'\\\(.*?\\\)|\\\[.*?\\\]'
            assert re.findall(pat,r['cleaned_tex'],re.S)==re.findall(pat,r['display_tex'],re.S),slug
            for env in ['definition','proof','proposition','example','remark']:
                assert r['display_tex'].count('class="math-env math-env-'+env+'"')==r['cleaned_tex'].count(r'\begin{'+env+'}'),(slug,env)
            assert (e['origin'] if slug==e['slug'] else e['slug']) in links(r['display_tex']),slug
        assert any(r['slug']==e['slug'] for r in search_public_math_library(c.cursor(),e['title'])['data'])
        print('Verified',d['id'],e['slug'],'from',e['origin'])
    assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    assert not c.execute('PRAGMA foreign_key_check').fetchall()

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--db',type=Path,default=SRC.parent/'portfolio.db')
    args=p.parse_args()
    if not args.db.is_file(): raise FileNotFoundError(args.db)
    apply(args.db)
