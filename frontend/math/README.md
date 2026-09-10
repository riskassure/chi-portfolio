# Math CMS frontend

HTML pages, their JavaScript entry points, styles, and MathJax configuration
live in this directory.

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
