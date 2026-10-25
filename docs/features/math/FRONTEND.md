# Math CMS frontend

Source context: `frontend/math`. Bare filenames and
relative implementation paths below refer to that source directory.

HTML pages, their JavaScript entry points, styles, and MathJax configuration
live in this directory.

The collection-wide writing and notation rules are in
[`AUTHORING_STANDARDS.md`](AUTHORING_STANDARDS.md).
For the administrator's local create, preview, save and publish workflow, see
[`ADDING_ENTRIES.md`](ADDING_ENTRIES.md).

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

## Public math search

The directory's quick-search dropdown and `search.html` both use
`/api/math/search`, implemented in
`backend/src/services/math/public_search_service.py` (repository-relative path).

- Words can appear in any order: `theorem Sylow` finds `Sylow theorems`.
- Matching ignores case, extra spaces, accents, and punctuation. Apostrophes
  are removed, so `Euler's` and `Eulers` match. Partial words still work.
- Every query word must occur in one searchable name. Titles rank first:
  exact title, phrase at the start, phrase elsewhere, then words in any order.
  Slug/canonical-name matches follow, then synonyms and defined terms.
- Each concept appears once, using its best match, before result limits apply.
  MSC codes, names, and descriptions also support words in any order;
  classification results retain their separate section and limits.
- This searches names and defined terms, not article bodies. Spelling correction
  and automatic stemming are not implemented. A punctuation-only query returns
  no results.

No database migration or index rebuild is needed. Restart the local server to
test backend changes. To enable them in production, publish the changed Python
file through helper option 15 and the reviewed staging/check/publication steps;
Git push alone does not update the site. Verify both the dropdown and the full
results page after publication.

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
