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
| Natural numbers | `\N` | `\mathbb{N}` |
| Integers | `\Z` | `\mathbb{Z}` |
| Rational numbers | `\Q` | `\mathbb{Q}` |
| Real numbers | `\R` | `\mathbb{R}` |
| Complex numbers | `\C` | `\mathbb{C}` |
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

Use standard operator commands where MathJax already supplies them, such as
`\ker`, `\lim`, `\sin`, and `\log`. Named operators not built into LaTeX
should use a shared semantic macro or `\operatorname{...}`.

## Formal sections

- Use `\begin{definition} ... \end{definition}` for a formal definition.
- Use `\begin{theorem} ... \end{theorem}`, and the corresponding `lemma`,
  `proposition`, or `corollary` environment, for formal results.
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
- Retain a primary type such as `Theorem`, `Example`, `Algorithm`, or `Topic`
  when `Definition` or `Proof` is added.
- Do not add `Definition` or `Proof` merely because the prose mentions a
  definition or briefly discusses a proof.

## Prose and layout

- Introduce notation before relying on it, and keep the same notation through
  the entry.
- Use `\emph{...}` for emphasis and defined terms. Avoid using bold text as a
  substitute for a formal section environment.
- Put punctuation after an inline expression when it belongs to the sentence.
- Use semantic lists and aligned equations instead of manual spacing.
- Keep diagrams and tables close to the paragraph that introduces them and
  provide a short label or explanation when their meaning is not immediate.

## Review checklist

Before saving a revised entry:

1. Confirm that shared notation follows the preferred forms above.
2. Confirm that local macros are necessary, unique, and defined at the start.
3. Confirm that formal definitions and proofs use formal structural commands.
4. Confirm that the document types reflect those formal sections.
5. Check the rendered entry for unresolved commands, overflow, missing
   diagrams, and malformed MathJax using the admin MathJax audit page.
