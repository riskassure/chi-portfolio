# Migration scripts: side-effect review

**Reviewed:** 2026-10-22, from `main` at `4f68a81`. Scope: the 35 scripts in `backend/src/database/math/migrations/`. Nothing was run against a database. The scripts have since been changed to require `--db`, preview by default and back up before `--apply` (see [ADDING_ENTRIES](../../features/math/ADDING_ENTRIES.md#migration-scripts-historical-bulk-route)); the findings below describe what each script writes when applied. I read each script's write path, and imported every script to confirm what the module-level code does.

## Short version

- **Every script writes to `backend/portfolio.db` unless told otherwise.** 32 take `--db` with that file as the default. `add_centralizer_in_a_ring.py` and `add_autolink_inflection_synonyms.py` take **no arguments at all**, so they can only write there. `backfill_local_macro_preludes.py` uses the app's `PORTFOLIO_DB_PATH` setting, which also falls back to `backend/portfolio.db`.
- **29 of the 35 change existing entries, not just new ones.** 17 edit the text of existing entries. 24 add "related" links on existing entries. Several also add or remove synonyms, defined terms or document types on existing entries. Only 6 scripts touch nothing but their own new entries.
- **Importing a script is safe.** The chain imports (for example `add_holomorphic_function` → `add_number_theory_and_geometry_foundations` → `add_group_centralizers_and_series` → …) only load entry data and adjust Python's import path. I imported all 35, and none opened a database or created a file.
- **Most scripts are all-or-nothing.** 31 do all their writing in one transaction and finish with a verification step, so a failed check undoes the whole run. Four are not (see "Partial writes").
- **Only one takes a backup.** That's `backfill_local_macro_preludes.py`, which is also the only one with a dry run.

## Problems that apply to many scripts

| Problem | Scripts | What happens |
|---|---|---|
| Wrong default database | All 35 | Running without `--db` edits the stale `backend/portfolio.db` and reports success |
| No way to choose the database | `add_centralizer_in_a_ring`, `add_autolink_inflection_synonyms` | Always writes to `backend/portfolio.db` |
| Creates an empty database if the path is wrong | `add_centralizer_in_a_ring`, `add_autolink_inflection_synonyms` | SQLite creates a new empty file at a mistyped path, then the script fails on the missing tables. The other 33 check the file exists first |
| Partial writes | `add_affine_and_harmonic_functions`, `add_partial_derivatives_and_cauchy_riemann`, `add_countability_and_function_regularity`, `add_five_topology_foundations` | These write in two or three separate transactions. If a later step fails, the earlier ones stay saved. The first two try to put back the defined term they moved, but nothing undoes the new entries |
| Overwrites later edits on a re-run | `expand_desarguesian_examples` | Replaces the whole text of `desarguesian-lattice` with its own fixed version whenever they differ |
| Resets document types on every run | `extract_algebra_foundations` | Recomputes the types of its 9 origin entries from their text each run, dropping any type set by hand since |
| Creates folders | Every script that creates an entry | The shared create service makes `backend/data/math/diagrams/` and `backend/data/math/temp/` (or the `MATH_DIAGRAM_DIR` setting) if missing. No script adds a diagram |
| Changes links on unrelated pages | Every script that adds a title or synonym | The site adds automatic links when a page is viewed, so a new title or synonym can start linking words on other pages. Nothing is written to those pages, but they look different |

On a re-run against today's database, most single-transaction scripts would probably undo themselves. Their verification compares each new entry's text with the script's copy, and several of those entries have been edited since. That's luck, not a safeguard, and it doesn't apply to the four partial-write scripts.

## One possible data bug

`add_abelian_and_lattice_foundations.py` adds the synonym **"pre-category" to `additive-category`**. The surrounding code is repairing `precategory`, so it was probably meant for that entry. It would be worth checking the live entry. I haven't changed anything.

## Script by script

"Related links" means rows added to `math_related_concepts`. "Two-way" means the existing entry also gets a link back to the new one.

### Only add new entries

| Script | New entries | Effect on existing entries |
|---|---|---|
| `add_characteristic_and_root_bound` | 3 | None |
| `add_collatz_conjecture` | 1 | None |
| `add_eight_algebra_concepts` | 8 | None. It checks that existing entries already autolink to the new ones |
| `add_finite_integral_domain_theorem` | 1 | None |
| `add_sylow_theorems` | 5 | None |
| `add_twenty_concepts_20260922` | 20 | None |

### Add new entries and related links on existing entries

| Script | New entries | Existing entries given related links |
|---|---|---|
| `add_analytic_continuation` | 1 | Two-way links to every related or linked entry (via the number-theory script) |
| `add_holomorphic_function` | 1 | Same as above |
| `add_number_theory_and_geometry_foundations` | 16 | Two-way links to every related or linked entry |
| `add_desarguesian_lattice` | 1 | Two-way links to its related entries |
| `add_category_foundations` | 5 | `identity-functor`, `functor-category`, `connected-category`, `unit-of-adjunction`, `subcategory` |
| `add_diagram_chasing` | 1 | `five-lemma`, `snake-lemma`, `exact-sequences-of-modules` |
| `add_eight_computability_concepts` | 8 | `turing-reducibility`, `many-one-reducibility`, `recursive-set`, `arithmetical-hierarchy` |
| `add_five_and_snake_lemmas` | 4 | `kernel-of-a-morphism`, `example-of-exact-functor`, `quotient-module` |
| `add_group_centralizers_and_series` | 3 | `center-of-a-group`, `normalizer-of-a-subgroup`, `centralizer-in-a-ring`, `locally-finite-group`, `solvable-group` |
| `add_semisimple_characterization` | 6 | `semisimple-module`, `socle` |
| `add_twenty_four_concepts_20260924` | 24 | `free-algebra`, `locally-finite-group`, `gcd-domain`, `reflective-subcategory`, `primary-decomposition-theorem1`, `properties-of-ordinals`, `properties-of-ranks-of-sets` |

### Edit the text or metadata of existing entries

| Script | New entries | What it changes on existing entries |
|---|---|---|
| `add_abel_ruffini` | 12 | Related links on `galois-group`. Adds a "fixed field" link exclusion to the text of `signature` |
| `add_abelian_and_lattice_foundations` | 3 | Rewrites passages in `precategory`, `additive-category` and `preadditive-category` and recomputes their types. Adds "pre-category" to `additive-category` (see above). Two-way links |
| `add_affine_and_harmonic_functions` | 2 | Moves the defined term "harmonic function(s)" off `laplace-equation` and adds two links to its text. Two-way links. **Partial writes** |
| `add_algebra_foundations` | 5 | Edits 12 entries: adds a "field" link exclusion to 4, removes it from 8 ring and field entries, and rewrites UCLA links in those 8 |
| `add_centralizer_in_a_ring` | 1 | Removes explicit links from `matrix-ring` and `matrix-unit`. **No `--db` option** |
| `add_collatz_graph_foundations` | 3 | Inserts a definition and three links into `collatz-conjecture` and adds two defined terms. Adds a note and a Remark type to `path1` |
| `add_countability_and_function_regularity` | 5 | Inserts a definition into `smooth-manifold` and adds two defined terms. Two-way links. **Partial writes** |
| `add_five_topology_foundations` | 5 | Adds three links to the text of `smooth-manifold`. Two-way links. **Partial writes** |
| `add_ideals_and_nilpotence` | 7 | Rewrites a sentence in `upper-nilradical`. Related links on several existing entries |
| `add_monomorphism_and_clarify_duality` | 1 | Rewrites a section of `dual-category` and adds two synonyms. Appends a passage to `epi`. Prepends a line to `examples-of-monics`, `regular-monomorphism` and `strong-monomorphism`. Recomputes their types. Two-way links |
| `add_partial_derivatives_and_cauchy_riemann` | 3 | Moves the defined term "Cauchy-Riemann equations" off `holomorphic-function`, replaces its proposition and proof with a pointer, and resets its types. **Partial writes** |
| `add_requested_algebra_definitions` | 7 | Adds definitions and defined terms to `polyadic-semigroup`, `identity-in-a-class` (also fixes a typo) and the Noetherian-ring entry. Adds links in `operations-on-relations` and `semisimple-ring` |
| `add_simple_group` | 1 | Removes a sentence from `composition-series-of-a-group` and adds a link |
| `extract_algebra_foundations` | 9 | Cuts an embedded definition out of each of 9 entries, deletes the matching defined term and resets their types on every run |
| `extract_category_foundations` | 6 | Cuts embedded definitions out of `category`, `functor`, `natural-transformation` and `initial-and-terminal-objects`, deletes the matching defined terms and resets their types |
| `expand_desarguesian_examples` | 0 | Replaces the whole text of `desarguesian-lattice` (see above). Two-way link with `moulton-plane` |

### Change existing entries only

| Script | What it changes |
|---|---|
| `add_autolink_inflection_synonyms` | Adds about 60 plural synonyms to existing entries. **No `--db` option** |
| `backfill_local_macro_preludes` | Adds missing macro definitions to the start of existing entries listed by the latest audit run. It's the careful one: a dry run unless you pass `--apply`, a verified backup first, and each update is skipped if the entry changed since it was read. It uses `PORTFOLIO_DB_PATH`, not `--db` |

## What this means for the helper

Any script with a related-link or text change to an existing entry produces changes that helper options 2 to 5 can't publish. That's 29 of the 35. So re-running one of these locally leaves the working copy different from the live site in ways the helper can't fix.
