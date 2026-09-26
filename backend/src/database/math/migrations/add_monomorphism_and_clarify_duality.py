"""Add categorical monomorphisms and clarify existing epi and duality entries."""
import argparse
from datetime import datetime
from pathlib import Path
import re
import sqlite3
from add_group_centralizers_and_series import entry, SRC, source, document_types, create_math_concept, fetch_public_math_concept_detail, relate, links
from services.math.concept_render_service import render_tex_reusing_existing_diagrams
from services.math.concept_metadata_service import _attach_types
from services.math.autolink_service import apply_math_autolinker

E=entry('monomorphism','monomorphism','Monic','18A20',
    ['mono','monic morphism','monomorphisms'],[],
    'epi examples-of-monics dual-category category',r"""
\begin{definition}
A morphism \(f:A\to B\) in a category is a \emph{monomorphism}, or \emph{monic morphism} (also called a \emph{mono}), if for every object \(X\) and every pair \(g,h:X\to A\),
\[
f\circ g=f\circ h\quad\Longrightarrow\quad g=h.
\]
Thus \(f\) can be cancelled on the left of a composite. This definition depends on the ambient category.
\end{definition}
\begin{proposition}
In the category of sets, monomorphisms are precisely injective functions.
\end{proposition}
\begin{proof}
If \(f\) is injective, equality \(f(g(x))=f(h(x))\) implies \(g(x)=h(x)\) for every \(x\), hence \(g=h\). Conversely, if \(f(a)=f(b)\), use the two maps from a singleton selecting \(a\) and \(b\). Monicity makes these maps equal, so \(a=b\).
\end{proof}
\begin{proposition}
Composites of monomorphisms are monomorphisms. If \(g\circ f\) is monic, then \(f\) is monic.
\end{proposition}
\begin{proof}
If \(gfu=gfv\), cancel \(g\) and then \(f\) to obtain \(u=v\). For the second assertion, \(fu=fv\) implies \(gfu=gfv\), and cancellation of \(gf\) gives \(u=v\).
\end{proof}
\begin{example}
Subgroup inclusions and submodule inclusions are monomorphisms: their underlying functions are injective. Every arrow in a partially ordered set viewed as a category is monic, since there is at most one arrow between any two specified objects. Further examples, including monomorphisms that are not injective in their ambient categories, appear in \PMlinkname{examples of monics}{ExamplesOfMonics}.
\end{example}
\begin{remark}
The dual notion is an \PMlinkname{epimorphism}{Epi}: \(f\) is monic in \(\mathcal C\) exactly when its opposite arrow is epic in \(\mathcal C^{\mathrm{op}}\). A categorical monomorphism is not defined merely as an injective function: a general category need not have underlying functions at all. The adjective monic also describes polynomials with leading coefficient one; that is a different meaning.
\end{remark}
""")
E['reference']=('Emily Riehl','Category Theory in Context, Section 1.2','https://emilyriehl.github.io/files/context.pdf')
E['escapes']+=['object','objects','monic','epic','injective','surjective','ambient','left','right','context','theory','categorical','monomorphism']
PROSE_ESCAPES=''.join(r'\PMlinkescapeword{'+s+'}' for s in [
    'object','objects','context','theory','categorical','identity','inverse','surjective',
    'generalization','order','closure','equivalent','similar','kernel','product','nor','epimorphism'])+'\n'

DUAL=r"""
\section*{The principle of categorical duality}
Reversing arrows interchanges \PMlinkname{initial and terminal objects}{InitialAndTerminalObjects}, \PMlinkname{monomorphisms}{Monic} and \PMlinkname{epimorphisms}{Epi}, products and coproducts, and limits and colimits.
\begin{proposition}
A statement proved for every category using only objects, morphisms, identities, and composition has a dual statement obtained by reversing all arrows and composition order. The dual statement holds in every category as well.
\end{proposition}
\begin{proof}
Apply the original statement to the opposite category. Its identity and associativity laws follow from those of the original category, with composition reversed. Interpreting the resulting statement back in the original category gives exactly the dual statement. Reversing arrows twice restores the original category.
\end{proof}
\begin{example}
The uniqueness of an initial object up to unique isomorphism dualizes to the corresponding uniqueness of a terminal object. Similarly, closure of monomorphisms under composition dualizes to closure of epimorphisms under composition.
\end{example}
\begin{remark}
Hypotheses must also be dualized. Duality does not assert that an arbitrary category is equivalent to its opposite, nor does it let one reverse a theorem about a particular category while keeping that category fixed. For example, initial sets are empty but terminal sets are singletons.
\end{remark}
\begin{thebibliography}{9}
\bibitem{riehl} Emily Riehl, \PMlinkexternal{Category Theory in Context, Section 1.2}{https://emilyriehl.github.io/files/context.pdf}.
\end{thebibliography}
"""
EPI=r"""
\section*{Epimorphisms need not be surjective}
\begin{example}
In the category of commutative unital rings and identity-preserving homomorphisms, the inclusion \(\mathbb Z\to\mathbb Q\) is an epimorphism, although it is not surjective. Indeed, if \(u,v:\mathbb Q\to R\) agree on \(\mathbb Z\), they agree on every integer and on the inverses of nonzero integers, since an inverse is unique. Thus they agree on every rational number. The inclusion is also a monomorphism but is not an isomorphism.
\end{example}
\begin{remark}
An \PMlinkname{algebraic-system convention}{HomomorphismBetweenAlgebraicSystems} sometimes uses epimorphism to mean a surjective homomorphism. The definition in this entry is categorical right cancellation; these conventions are not interchangeable in every category.
\end{remark}
\begin{thebibliography}{9}
\bibitem{riehl} Emily Riehl, \PMlinkexternal{Category Theory in Context, Section 1.2}{https://emilyriehl.github.io/files/context.pdf}.
\end{thebibliography}
"""

def save(c,d,tex,now):
    rendered=render_tex_reusing_existing_diagrams(d['id'],tex,c.cursor())
    c.execute('UPDATE math_concepts SET cleaned_tex=?,rendered_tex=?,updated_at=? WHERE id=?',(tex,rendered,now,d['id']))
    # Keep legacy Definition classification even when its markup is informal.
    types=set(d['types'])|set(document_types({'body':tex}))
    _attach_types(c.cursor(),d['id'],sorted(types))

def apply(path):
    with sqlite3.connect(path) as c:
        c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON')
        now=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if not c.execute("SELECT 1 FROM math_concepts WHERE slug='monomorphism'").fetchone():
            assert not c.execute("SELECT 1 FROM math_concepts WHERE canonical_name='Monic' OR lower(title)='monomorphism'").fetchone()
            create_math_concept(c.cursor(),E['canonical'],E['slug'],E['title'],now,'CWoo',source(E),1,E['classifications'],document_types(E),E['synonyms'],[],[])
        d=fetch_public_math_concept_detail(c.cursor(),'dual-category');tex=d['cleaned_tex']
        if 'The principle of categorical duality' not in tex:
            start=tex.index('If $F$ is a covariant functor');end=tex.index('%%%%%',start)
            tex=tex[:start]+r'''For a covariant functor \(F:\mathcal C\to\mathcal D\), its \emph{opposite functor} is the covariant functor \(F^{\mathrm{op}}:\mathcal C^{\mathrm{op}}\to\mathcal D^{\mathrm{op}}\) defined by \(F^{\mathrm{op}}(A)=F(A)\) and \(F^{\mathrm{op}}(f^{\mathrm{op}})=F(f)^{\mathrm{op}}\). This reverses both categories. By contrast, a \PMlinkname{contravariant functor}{ContravariantFunctor} from \(\mathcal C\) to \(\mathcal D\) is a covariant functor \(\mathcal C^{\mathrm{op}}\to\mathcal D\).

'''+DUAL+tex[end:]
            tex=PROSE_ESCAPES+r'\PMlinkescapeword{terminal}'+'\n'+tex
            save(c,d,tex,now)
        d=fetch_public_math_concept_detail(c.cursor(),'epi')
        if 'Epimorphisms need not be surjective' not in d['cleaned_tex']:
            tex=d['cleaned_tex']+'\n'+EPI
            tex=PROSE_ESCAPES+tex
            save(c,d,tex,now)
        for alias in ['categorical duality','principle of categorical duality']:
            ident=c.execute("SELECT id FROM math_concepts WHERE slug='dual-category'").fetchone()[0]
            if not c.execute('SELECT 1 FROM math_synonyms WHERE concept_id=? AND synonym_text=?',(ident,alias)).fetchone():
                c.execute('INSERT INTO math_synonyms(concept_id,synonym_text) VALUES (?,?)',(ident,alias))
        for slug in E['related']:
            relate(c,'monomorphism',slug);relate(c,slug,'monomorphism')
        relate(c,'dual-category','initial-and-terminal-objects')
        # Avoid making every polynomial occurrence of the adjective monic a category link.
        for slug in ['examples-of-monics','regular-monomorphism','strong-monomorphism']:
            d=fetch_public_math_concept_detail(c.cursor(),slug)
            if not d:continue
            prefix=r'For the categorical definition, see \PMlinkname{monomorphism (monic morphism)}{Monic}.'
            if prefix not in d['cleaned_tex']: save(c,d,prefix+'\n\n'+d['cleaned_tex'],now)
            relate(c,slug,'monomorphism')
        for slug in ['monomorphism','epi','dual-category','initial-and-terminal-objects']:
            d=fetch_public_math_concept_detail(c.cursor(),slug)
            assert d and d['display_tex']
            print('Verified',slug)
        d=fetch_public_math_concept_detail(c.cursor(),'monomorphism')
        assert d['cleaned_tex']==source(E)
        pat=r'\\\(.*?\\\)|\\\[.*?\\\]'
        assert re.findall(pat,d['cleaned_tex'],re.S)==re.findall(pat,d['display_tex'],re.S)
        assert 'monomorphism' in links(fetch_public_math_concept_detail(c.cursor(),'epi')['display_tex'])
        for term,target in [('epimorphism','epi'),('monomorphism','monomorphism'),('initial object','initial-and-terminal-objects'),('terminal object','initial-and-terminal-objects'),('categorical duality','dual-category')]:
            assert target in links(apply_math_autolinker(-1,term,c.cursor())),term
        assert 'monomorphism' not in links(apply_math_autolinker(-1,'a monic polynomial',c.cursor()))
        assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        assert not c.execute('PRAGMA foreign_key_check').fetchall()

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--db',type=Path,default=SRC.parent/'portfolio.db')
    args=p.parse_args()
    if not args.db.is_file():raise FileNotFoundError(args.db)
    apply(args.db)
