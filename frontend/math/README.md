# Math CMS frontend

HTML pages, their JavaScript entry points, styles, and MathJax configuration
live in this directory.

The collection-wide writing and notation rules are in
[`AUTHORING_STANDARDS.md`](AUTHORING_STANDARDS.md).

- `render/math_render_helpers.js` exposes `window.MathCmsRender` and orchestrates
  the rendering pipeline.
- `render/` contains shared TeX/HTML transformations and concept-local macros.
- `render/xy/` contains Xy parsing, layout, cells, tables, conversion, cleanup,
  sequences, and DOM overlays.
- `audit/` contains audit API, rendering checks, result formatting, storage,
  clipboard, and view helpers. `mathjax_audit.js` is the audit page entry point.

Scripts use named `window.MathCms...` exports and ordinary HTML script tags.
Keep dependency order synchronized in `concept.html` and `mathjax_audit.html`:
shared rendering dependencies precede the orchestrator, and audit helpers
precede the audit page entry point. Moving a script requires updating its
script URL while retaining any existing query string.

Rendering transformations must also retain their order within the orchestrator,
especially protection/restoration pairs. Folder grouping does not determine
execution order.

## TeX commands and proof style

The site supports two kinds of macro-like commands:

- Shared MathJax aliases live in `mathjax_config.js`. Use these for notation
  that should mean the same thing throughout the collection.
- Concept-local `\newcommand` definitions remain at the beginning of a
  concept's `cleaned_tex`. `render/math_local_macros.js` expands their supported
  subset before MathJax typesets the entry.

Structural prose commands are handled by the rendering pipeline rather than
MathJax. A standalone proof should be authored with either a LaTeX
`\begin{proof} ... \end{proof}` environment or the PlanetMath `\proof`
command. Both render with an italicized `Proof.` heading and a right-aligned
hollow square at the end. Do not add `QED`, `\qed`, or another square manually.
Informal proof discussion inside an ordinary paragraph does not receive an
automatic heading or ending symbol.
