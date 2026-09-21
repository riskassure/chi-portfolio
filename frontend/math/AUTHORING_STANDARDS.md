# Mathematics entry authoring standards

This guide defines the preferred style for new entries and for entries being
substantially revised. Historical PlanetMath notation may remain when it is
correct and renders clearly. The compatibility aliases in `mathjax_config.js`
support that older material; their presence does not make every alias a
preferred form.

## Source and rendering

- Write mathematical content in `cleaned_tex`. Do not edit `rendered_tex`
  directly; rebuild it through the normal editor or rendering service.
- Use `\(...\)` for inline mathematics and `\[...\]` for displayed
  mathematics in new or substantially revised text. Existing `$...$` and
  `$$...$$` delimiters remain supported.
- Use standard LaTeX commands when they are clear and concise. Use a shared
  macro when it gives a consistent semantic shorthand used across the
  collection.
- Put a concept-local `\newcommand` prelude at the beginning of `cleaned_tex`
  only when an entry needs repeated notation that is not broadly useful.
- Do not redefine a shared macro locally or create a second spelling for an
  existing shared concept.

## Preferred shared notation

The following commands are defined centrally in `mathjax_config.js` and are
preferred when their meaning matches the entry.

| Purpose | Preferred source | Rendering |
| --- | --- | --- |
| Natural numbers | `\mathbb{N}` | `\mathbb{N}` |
| Integers | `\mathbb{Z}` | `\mathbb{Z}` |
| Rational numbers | `\mathbb{Q}` | `\mathbb{Q}` |
| Real numbers | `\mathbb{R}` | `\mathbb{R}` |
| Complex numbers | `\mathbb{C}` | `\mathbb{C}` |
| Probability | `\Prob` | `\mathbb{P}` |
| Domain | `\dom` | upright `dom` |
| Image | `\im` | upright `im` |
| Hom set | `\Hom` | upright `Hom` |
| Automorphism group | `\Aut` | upright `Aut` |
| Spectrum | `\Spec` | upright `Spec` |
| Span | `\Span` | upright `span` |
| Norm | `\norm{x}` | automatically sized double bars |
| Absolute value | `\abs{x}` | automatically sized bars |
| Inner product | `\ip{x,y}` | automatically sized angle brackets |
| Generated object | `\gen{x}` | automatically sized angle brackets |
| Set builder | `\setOf{x}{P(x)}` | automatically sized braces and divider |
| Partial derivative | `\pdiff{f}{x}` | `\frac{\partial f}{\partial x}` |

Use standard LaTeX directly for familiar relations and arrows, including
`\subseteq`, `\supseteq`, `\rightarrow`, `\leftarrow`, `\Leftrightarrow`,
and `\vdash`. Legacy aliases such as `\sse`, `\spse`, `\ra`, `\from`,
`\Iff`, and `\proves` remain supported for imported entries.

Use the explicit `\mathbb` forms for the standard number systems. Historical
aliases such as `\N`, `\Z`, `\Q`, `\R`, and `\C` remain supported, but short
single-letter commands are easy to redefine locally and can change meaning.

Use standard operator commands where MathJax already supplies them, such as
`\ker`, `\lim`, `\sin`, and `\log`. Named operators not built into LaTeX
should use a shared semantic macro or `\operatorname{...}`.

## Formal sections

- Use `\begin{definition} ... \end{definition}` for a formal definition.
- Use `\begin{theorem} ... \end{theorem}`, and the corresponding `lemma`,
  `proposition`, or `corollary` environment, for formal results.
- Use `\begin{example} ... \end{example}` and
  `\begin{remark} ... \end{remark}` for substantial examples and remarks.
  Ordinary phrases such as “for example” remain part of the surrounding prose.
- Use `\begin{proof} ... \end{proof}` for a standalone proof. The legacy
  standalone shorthand `\proof` is also supported.
- A standalone proof renders with an italicized `Proof.` heading and a
  right-aligned hollow square. Do not type `QED`, `\qed`, `\square`, or
  `\blacksquare` at the end of a formal proof.
- A short proof discussion embedded in an ordinary paragraph remains prose.
  Do not add an automatic heading or ending marker to it. An explicitly
  authored legacy `\qed` in such a discussion renders as a hollow square.

## Document types

Document types describe the kinds of substantial content present in an entry;
an entry may have more than one.

- Add `Definition` when the entry contains a formal definition section.
- Add `Proof` when the entry contains a formal standalone proof section.
- Add `Example` when the entry contains a formal example section.
- Add `Remark` when the entry contains a formal remark section.
- Retain a primary type such as `Theorem`, `Example`, `Algorithm`, or `Topic`
  when `Definition` or `Proof` is added.
- Do not add `Definition` or `Proof` merely because the prose mentions a
  definition or briefly discusses a proof.

Use the remaining types according to the entry's substantive purpose:

- `Algorithm` for an explicit computational procedure.
- `Application` for a substantial application of a mathematical result.
- `Axiom` for an axiom or axiom system presented as subject matter.
- `Bibliography` for a reference-centered entry.
- `Biography` for the life and work of a person.
- `Conjecture` for an open or historically conjectured statement, including
  an entry devoted to its proof or resolution.
- `Data structure` for a mathematical or computational data organization.
- `Derivation` for an entry whose principal content derives a stated result.
- `Feature` for a collection of notable properties, techniques, or reference
  features that is not itself primarily a theorem.
- `Topic` for an overview or hub entry spanning several related concepts.

Use semantic `enumerate`, `itemize`, and `description` environments for lists.
Keep custom `\item[...]` labels when they name conditions or logical cases.
Manual labels such as `(1) implies (2)` may remain in prose when later steps
refer to those exact labels.

## Prose and layout

- Introduce notation before relying on it, and keep the same notation through
  the entry.
- Use `\emph{...}` for emphasis and defined terms. Avoid using bold text as a
  substitute for a formal section environment.
- Emphasize a term at its defining occurrence, normally the first occurrence
  in its formal definition. Later uses should remain unstyled.
- A definition that introduces only notation, a map, or a list of conditions
  does not need an artificially emphasized term.
- Begin with a concise sentence that explains the subject or motivates the
  entry. Avoid merely repeating the page title before the definition.
- Use `\begin{thebibliography} ... \end{thebibliography}` with `\bibitem`
  entries for references. The rendered heading is always `References`.
- Treat a displayed equation as part of its sentence and include the required
  comma or period. Use `align` for related multiline calculations, `equation`
  only when a referenced equation number is needed, and avoid introducing new
  `eqnarray` source.
- Put punctuation after an inline expression when it belongs to the sentence.
- Use semantic lists and aligned equations instead of manual spacing.
- Keep diagrams and tables close to the paragraph that introduces them and
  provide a short label or explanation when their meaning is not immediate.

## Concept links

- Concept titles, synonyms, and defined terms may be linked automatically in
  prose. Because matching is context-free, review ordinary-language homonyms
  and suppress them at the entry level when their mathematical sense is not
  intended.
- Add a catalog synonym for a common plural or inflected form only when it has
  the same mathematical meaning everywhere it is likely to occur. Use an
  explicit concept link for a context-dependent synonym.
- Grammatical words such as `and`, `or`, `not`, `if`, and `then` are never
  autolinked, even if they also name a mathematical operation or concept.
- Use `\PMlinkescapeword{term}` or `\PMlinkescapephrase{multiword term}` when
  an otherwise eligible target has the wrong meaning throughout one entry.
- Use `\PMlinkescapetext{visible passage}` to suppress autolinking only in a
  particular occurrence or short passage.
- Preserve deliberate explicit links. Do not add an explicit link solely to
  maximize link density; it should help a reader understand the present entry.

## Review checklist

Before saving a revised entry:

1. Confirm that shared notation follows the preferred forms above.
2. Confirm that local macros are necessary, unique, and defined at the start.
3. Confirm that formal definitions and proofs use formal structural commands.
4. Confirm that the document types reflect those formal sections.
5. Check the rendered entry for unresolved commands, overflow, missing
   diagrams, and malformed MathJax using the admin MathJax audit page.
