"""Module versions of the five and snake lemmas, with proofs and Xy diagrams.

Full-source review found neither lemma. General categorical kernels/cokernels
and quotient modules already exist. 'Exact sequence' is registered to a regular
category's exact fork, so use qualified module terminology and explicit links.
"""
import argparse
from datetime import datetime
from pathlib import Path
import re
import sqlite3
import sys
SRC=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(SRC))
from services.math.concept_create_service import create_math_concept
from services.math.public_concept_detail_service import fetch_public_math_concept_detail
from services.math.public_search_service import search_public_math_library
from add_eight_algebra_concepts import source, Links
from add_sylow_theorems import document_types
from add_twenty_concepts_20260922 import ESCAPES
from add_category_foundations import relate, links


def entry(title,slug,canonical,aliases,definitions,related,body,reference):
    return dict(title=title,slug=slug,canonical=canonical,classifications=['16D10','18G99'],
                synonyms=aliases,definitions=definitions,related=related,body=body,reference=reference,
                escapes=list(ESCAPES)+['exact sequence','kernel','cokernel','image','map','homomorphism',
                  'isomorphism','injective','surjective','inverse','identity','natural','square','row',
                  'lift','left','right','zero','class','representative','well-defined','sequence',
                  'diagram','commutative','commutes','linear','element','module','short','long',
                  'associated','boundary','connecting','factor','normal','split','independent',
                  'categorical','measure','projection'])


FIVE_DIAGRAM=r"""\[
\xymatrix{
A_1\ar[r]^{f_1}\ar[d]_{u_1} & A_2\ar[r]^{f_2}\ar[d]_{u_2} & A_3\ar[r]^{f_3}\ar[d]_{u_3} & A_4\ar[r]^{f_4}\ar[d]_{u_4} & A_5\ar[d]_{u_5} \\
B_1\ar[r]_{g_1} & B_2\ar[r]_{g_2} & B_3\ar[r]_{g_3} & B_4\ar[r]_{g_4} & B_5
}
\]"""
SNAKE_DIAGRAM=r"""\[
\xymatrix{
0\ar[r] & A\ar[r]^{i}\ar[d]_{\alpha} & B\ar[r]^{p}\ar[d]_{\beta} & C\ar[r]\ar[d]_{\gamma} & 0 \\
0\ar[r] & A'\ar[r]_{i'} & B'\ar[r]_{p'} & C'\ar[r] & 0
}
\]"""
SNAKE_SEQUENCE=r"""\[
\xymatrix{
0\ar[r] & \ker\alpha\ar[r]^{i_*} & \ker\beta\ar[r]^{p_*} & \ker\gamma\ar[dll]^{\delta} & \\
 & \operatorname{coker}\alpha\ar[r]_{\overline{i'}} & \operatorname{coker}\beta\ar[r]_{\overline{p'}} & \operatorname{coker}\gamma\ar[r] & 0
}
\]"""
EXAMPLE_DIAGRAM=r"""\[
\xymatrix{
0\ar[r] & \mathbb{Z}\ar[r]^{2}\ar[d]_{2} & \mathbb{Z}\ar[r]^{q}\ar[d]_{1} & \mathbb{Z}/2\mathbb{Z}\ar[r]\ar[d]_{0} & 0 \\
0\ar[r] & \mathbb{Z}\ar[r]_{1} & \mathbb{Z}\ar[r] & 0\ar[r] & 0
}
\]"""
MODULE_REF=('Romyar Sharifi','Abstract Algebra, Chapter 5: Modules over rings','https://www.math.ucla.edu/~sharifi/notes/algebra-ch05.html')
FIVE_REF=('University of Pennsylvania, CIS 610 course notes','Rings and Modules, section on the five lemma and snake lemma','https://www.cis.upenn.edu/~cis6100/alg2.pdf')
SNAKE_REF=('The Stacks Project','Snake lemma, Section 10.4','https://stacks.math.columbia.edu/tag/07JV')

ENTRIES=[
entry('kernels and cokernels of module homomorphisms','module-kernels-and-cokernels','ModuleKernelsAndCokernels',[],
      ['kernel of a module homomorphism','cokernel of a module homomorphism','image of a module homomorphism'],
      ['module','module-homomorphism','quotient-module','kernel-of-a-morphism','exact-sequences-of-modules','snake-lemma'],r"""
Kernels measure failure of injectivity, while cokernels measure failure of surjectivity. All modules here are unital left modules over an associative unital ring \(R\).
\begin{definition}
A \PMlinkname{module homomorphism}{ModuleHomomorphism} \(f:M\to N\) satisfies \(f(x+y)=f(x)+f(y)\) and \(f(rx)=rf(x)\). Its kernel, image and cokernel are
\[
\ker f=\{x\in M:f(x)=0\},\qquad \im f=\{f(x):x\in M\},\qquad \operatorname{coker}f=N/\im f.
\]
These are, respectively, the \emph{kernel of a module homomorphism}, the \emph{image of a module homomorphism}, and the \emph{cokernel of a module homomorphism}. The first two sets are submodules by linearity; the last is a \PMlinkname{quotient module}{QuotientModule}. We include the kernel by \(k:\ker f\to M\), and project to the cokernel by \(q:N\to N/\im f\).
\end{definition}
\begin{proposition}
If \(t:X\to M\) satisfies \(ft=0\), it factors uniquely through \(k\). If \(s:N\to Y\) satisfies \(sf=0\), it factors uniquely through \(q\). Also, \(f\) is injective exactly when \(\ker f=0\), and surjective exactly when \(\operatorname{coker}f=0\).
\end{proposition}
\begin{proof}
For the kernel factorization, \(t(x)\in\ker f\), so regard \(t\) as a map to that submodule. Inclusion is injective, forcing uniqueness. For the cokernel factorization set \(\overline{s}(n+\im f)=s(n)\). Changing representatives adds \(f(m)\), which \(s\) kills. Thus the formula is well-defined and linear; surjectivity of \(q\) forces uniqueness. Finally \(f(x)=f(y)\) exactly when \(x-y\in\ker f\), and \(N/\im f=0\) exactly when \(N=\im f\).
\end{proof}
\begin{example}
Multiplication by \(n\ge2\) on the \(\mathbb{Z}\)-module \(\mathbb{Z}\) has zero kernel and cokernel \(\mathbb{Z}/n\mathbb{Z}\). It is injective but not surjective.
\end{example}
\begin{remark}
The factorization properties identify these concrete constructions with the categorical \PMlinkname{kernel and cokernel}{KernelOfAMorphism}. A bijective module homomorphism has a linear inverse: apply the original map to the proposed additive and scalar identities for its inverse, then use injectivity. Thus bijective module homomorphisms are module isomorphisms.
\end{remark}
""",MODULE_REF),
entry('exact sequences of modules','exact-sequences-of-modules','ExactSequencesOfModules',['exact sequence of modules'],
      ['short exact sequence','short exact sequence of modules','commutative diagram','morphism of exact sequences'],
      ['module-kernels-and-cokernels','quotient-module','five-lemma','snake-lemma','example-of-exact-functor'],r"""
Exactness says that the elements killed by one map are precisely those supplied by the preceding map. Work with unital left modules over one associative unital ring \(R\).
\begin{definition}
A sequence of module homomorphisms is \emph{exact at} \(B\) in \(A\xrightarrow{f}B\xrightarrow{g}C\) when \(\im f=\ker g\). An \emph{exact sequence of modules} is exact at every position with both an incoming and an outgoing map. Kernels and images have the meanings in \PMlinkname{module kernels and cokernels}{ModuleKernelsAndCokernels}.
A \emph{short exact sequence} is an exact sequence
\[
\xymatrix{0\ar[r] & A\ar[r]^{i} & B\ar[r]^{p} & C\ar[r] & 0}.
\]
It says that \(i\) is injective, \(p\) is surjective, and \(\im i=\ker p\). A \emph{commutative diagram} means that the directed paths being compared with the same source and target have equal composites. A \emph{morphism of exact sequences} is a collection of maps between corresponding modules for which the squares commute.
\end{definition}
\begin{proposition}
In a short exact sequence, the map \(B/\im i\to C\), \(b+\im i\mapsto p(b)\), is an isomorphism.
\end{proposition}
\begin{proof}
The formula is well-defined because \(p\) kills \(\im i\), and it is linear. It is onto because \(p\) is onto. If its value is zero, then \(b\in\ker p=\im i\), so its argument is the zero coset. It is therefore bijective and hence a module isomorphism.
\end{proof}
\begin{example}
For every submodule \(N\subseteq M\), inclusion and projection give a short exact sequence \(0\to N\to M\to M/N\to0\). In particular, \(0\to\mathbb{Z}\xrightarrow{n}\mathbb{Z}\to\mathbb{Z}/n\mathbb{Z}\to0\) is short exact for \(n\ge2\).
\end{example}
\begin{remark}
The equation \(gf=0\) alone gives only \(\im f\subseteq\ker g\), not equality. Endpoint zeros encode injectivity and surjectivity and must not be omitted from hypotheses that need them. This entry concerns sequences of modules, rather than the exact forks discussed in regular categories.
\end{remark}
""",MODULE_REF),
entry('five lemma','five-lemma','FiveLemma',['five-lemma'],['short five lemma'],
      ['exact-sequences-of-modules','module-kernels-and-cokernels','snake-lemma'],r"""
The five lemma recovers the middle isomorphism in a ladder of exact sequences. Here all objects are unital left modules over the same associative unital ring \(R\); abelian groups are the case \(R=\mathbb{Z}\).
\begin{theorem}
Suppose the following diagram commutes and both rows are \PMlinkname{exact}{ExactSequencesOfModules} at their three interior modules:
"""+FIVE_DIAGRAM+r"""
If \(u_1\) is surjective, \(u_2,u_4\) are isomorphisms, and \(u_5\) is injective, then \(u_3\) is an isomorphism. Thus in particular it suffices that the other four vertical maps be isomorphisms.
\end{theorem}
\begin{proof}
First prove injectivity. Let \(x\in A_3\) satisfy \(u_3(x)=0\). Commutativity gives \(u_4(f_3(x))=g_3(u_3(x))=0\). Since \(u_4\) is injective, \(f_3(x)=0\), so exactness supplies \(y\in A_2\) with \(f_2(y)=x\). Then \(g_2(u_2(y))=0\), and exactness in the lower row gives \(z\in B_1\) with \(g_1(z)=u_2(y)\). Surjectivity of \(u_1\) gives \(w\in A_1\) with \(u_1(w)=z\). Hence \(u_2(y-f_1(w))=0\). Injectivity of \(u_2\) yields \(y=f_1(w)\), and \(x=f_2f_1(w)=0\).

For surjectivity, take \(z\in B_3\). Choose \(w\in A_4\) with \(u_4(w)=g_3(z)\). Then \(u_5(f_4(w))=g_4g_3(z)=0\), so \(f_4(w)=0\) by injectivity of \(u_5\). Exactness gives \(x_0\in A_3\) with \(f_3(x_0)=w\). Now \(g_3(z-u_3(x_0))=0\), so \(z-u_3(x_0)=g_2(v)\) for some \(v\in B_2\). Choose \(y\in A_2\) with \(u_2(y)=v\). Then \(u_3(x_0+f_2(y))=z\). The middle map is bijective, hence an isomorphism by \PMlinkname{the module-homomorphism criterion}{ModuleKernelsAndCokernels}.
\end{proof}
\begin{corollary}
The \emph{short five lemma}: in a commutative diagram of short exact sequences, if the maps on the first and last nonzero modules are isomorphisms, then the map on the middle modules is an isomorphism.
\end{corollary}
\begin{proof}
Include the zero modules at both ends as the first and fifth terms of the five-term rows. Their unique vertical maps are isomorphisms. Apply the five lemma to the three remaining modules.
\end{proof}
\begin{remark}
The two parts of the proof use different hypotheses: injectivity uses surjectivity of \(u_1\) and injectivity of \(u_2,u_4\); surjectivity uses surjectivity of \(u_2,u_4\) and injectivity of \(u_5\). These are the diagram chases often packaged as versions of the four lemma. This entry proves the module version directly, without treating arbitrary categorical objects as sets of elements.
\end{remark}
""",FIVE_REF),
entry('snake lemma','snake-lemma','SnakeLemma',['snake-lemma'],['connecting homomorphism of the snake lemma'],
      ['exact-sequences-of-modules','module-kernels-and-cokernels','five-lemma','kernel-of-a-morphism'],r"""
The snake lemma links the kernels and cokernels of a morphism of short exact sequences. Work with unital left modules over an associative unital ring \(R\). The proof also applies to abelian groups, viewed as \(\mathbb{Z}\)-modules.
\begin{theorem}
Let the following diagram commute, with both rows \PMlinkname{short exact}{ExactSequencesOfModules}:
"""+SNAKE_DIAGRAM+r"""
There is a canonical linear map \(\delta:\ker\gamma\to\operatorname{coker}\alpha\), the \emph{connecting homomorphism of the snake lemma}, making the following sequence exact. Read the upper row from left to right, follow \(\delta\) down to the lower-left term, then continue right:
"""+SNAKE_SEQUENCE+r"""
Here \(i_*,p_*\) are restrictions of \(i,p\), while \(\overline{i'},\overline{p'}\) are induced on the quotient modules defining the cokernels.
\end{theorem}
\section*{Constructing the connecting map}
For \(c\in\ker\gamma\), choose \(b\in B\) with \(p(b)=c\). Then \(p'(\beta(b))=\gamma(c)=0\), so there is a unique \(a'\in A'\) with \(i'(a')=\beta(b)\). Define
\[
\delta(c)=a'+\alpha(A)\in A'/\alpha(A)=\operatorname{coker}\alpha.
\]
This is the diagram chase: lift left along \(p\), move down along \(\beta\), lift left along \(i'\), and take the coset modulo \(\alpha(A)\).
\begin{proof}
We first justify the construction. Another lift of \(c\) is \(b+i(a)\) for some \(a\in A\). Its image under \(\beta\) is \(i'(a'+\alpha(a))\), so its resulting coset is unchanged. The lift through \(i'\) is unique because \(i'\) is injective. Sums and scalar multiples of chosen lifts are lifts of the corresponding sums and scalar multiples of \(c\); the formula therefore defines an \(R\)-linear map. Commutativity ensures that restrictions to the kernels and induced maps on the cokernels are well-defined.

At \(\ker\alpha\) and \(\ker\beta\): the map \(i_*\) is injective since \(i\) is. If \(b\in\ker\beta\) has \(p(b)=0\), write \(b=i(a)\). Then \(i'(\alpha(a))=\beta(b)=0\), hence \(a\in\ker\alpha\). Conversely, \(p(i(a))=0\). This proves exactness at these terms, including the initial zero.

At \(\ker\gamma\): a lift \(b\in\ker\beta\) gives \(a'=0\), so \(\delta(p(b))=0\). Conversely, if \(\delta(c)=0\), then the chosen \(a'\) equals \(\alpha(a)\) for some \(a\). The element \(b-i(a)\) still maps to \(c\), but its image under \(\beta\) is zero. Thus \(\ker\delta=\im p_*\).

At \(\operatorname{coker}\alpha\): if \(\delta(c)=[a']\), then \(i'(a')=\beta(b)\), so \(\overline{i'}([a'])=0\). Conversely, if this quotient class maps to zero, choose \(b\) with \(i'(a')=\beta(b)\). Then \(\gamma(p(b))=p'(i'(a'))=0\), and the construction gives \(\delta(p(b))=[a']\).

At \(\operatorname{coker}\beta\): the composite with \(\overline{i'}\) is zero because \(p'i'=0\). If \(\overline{p'}([b'])=0\), then \(p'(b')=\gamma(c)\) for some \(c\in C\). Lift \(c\) to \(b\in B\). Now \(p'(b'-\beta(b))=0\), so \(b'-\beta(b)=i'(a')\) for some \(a'\). Therefore \([b']=\overline{i'}([a'])\).

Finally, \(p'\) is surjective, so every class in \(\operatorname{coker}\gamma\) has a preimage in \(\operatorname{coker}\beta\). This proves exactness at the last term and the final zero, completing the proof.
\end{proof}
\begin{example}
The following diagram has short exact rows; \(q\) is reduction modulo two, and labels \(1,2\) denote multiplication by those integers:
"""+EXAMPLE_DIAGRAM+r"""
Here \(\ker\gamma=\mathbb{Z}/2\mathbb{Z}\), \(\operatorname{coker}\alpha=\mathbb{Z}/2\mathbb{Z}\), and the other four kernel/cokernel terms vanish. To compute \(\delta([m])\), lift to \(m\in\mathbb{Z}\); both \(\beta\) and \(i'\) are identities, so \(a'=m\). Thus \(\delta([m])=[m]\): the connecting map is nonzero and is an isomorphism.
\end{example}
\begin{remark}
The short-exact-row hypotheses give the endpoint zeros displayed here. More general versions assume only right exactness of the upper row and left exactness of the lower row; endpoint injectivity and surjectivity must then be stated separately. Different sign conventions may replace \(\delta\) by \(-\delta\); exactness is unchanged. The formula above fixes the convention used throughout this entry.
\end{remark}
""",SNAKE_REF),
]


def verify(c):
    for e in ENTRIES:
        d=fetch_public_math_concept_detail(c.cursor(),e['slug'])
        assert d and d['owner']=='CWoo' and d['cleaned_tex']==source(e),e['slug']
        for key in ['synonyms','definitions']:assert set(d[key])==set(e[key])
        assert set(d['types'])==set(document_types(e))
        assert {r['code'] for r in d['classifications']}==set(e['classifications'])
        html=d['display_tex'];assert r'\PMlink' not in html
        assert e['slug'] not in links(html)
        for env in ['definition','proof','theorem','corollary','example','remark','proposition']:
            assert html.count('class="math-env math-env-'+env+'"')==e['body'].count(r'\begin{'+env+'}'),(e['slug'],env)
        pattern=r'\\\(.*?\\\)|\\\[.*?\\\]'
        assert re.findall(pattern,source(e),re.S)==re.findall(pattern,html,re.S),e['slug']
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
    if not path.is_file():raise FileNotFoundError(path)
    with sqlite3.connect(path) as c:
        c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON')
        now=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for e in ENTRIES:
            if c.execute('SELECT 1 FROM math_concepts WHERE slug=?',(e['slug'],)).fetchone():continue
            for term in [e['title'],*e['synonyms'],*e['definitions']]:
                assert not c.execute('''SELECT title FROM math_concepts WHERE lower(title)=lower(?)
                    UNION SELECT synonym_text FROM math_synonyms WHERE lower(synonym_text)=lower(?)
                    UNION SELECT defined_term FROM math_definitions WHERE lower(defined_term)=lower(?)''',(term,term,term)).fetchone(),term
            for code in e['classifications']:
                assert c.execute('SELECT id FROM math_classifications WHERE code=?',(code,)).fetchone(),code
            create_math_concept(c.cursor(),e['canonical'],e['slug'],e['title'],now,'CWoo',source(e),1,e['classifications'],document_types(e),e['synonyms'],e['definitions'],[])
        for e in ENTRIES:
            for target in e['related']:relate(c,e['slug'],target)
        for origin,target in [('kernel-of-a-morphism','module-kernels-and-cokernels'),('example-of-exact-functor','exact-sequences-of-modules'),('quotient-module','module-kernels-and-cokernels')]:relate(c,origin,target)
        verify(c)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db',type=Path,default=SRC.parent/'portfolio.db')
    apply(parser.parse_args().db)
