# Merging and retiring math entries: design v3

**Status: implemented as helper option 21** (PR #20, merged as 1d372b0 on
2026-10-26). Rolled out live on 2026-10-26, and the first merge (entry 20 into
entry 19) was published the same day and recorded in PR #21. This is the design
Chi approved on 2026-10-25, kept as the record of *why* option 21 works as it does.
For how to use it, follow [Merging and retiring entries](MERGING_ENTRIES.md); where
the two differ, that guide and the code are current.

Original status line, as approved:

> Status: **merge publication not built; read-only candidate finder approved and being built.**
> v3 revises v2 after Chi's second review (2026-10-25). v1 and v2 are kept alongside. §11 maps both
> reviews' points to where they're answered. Checked against `main` at e924491
> and the working copy `set-theory-entries/relation-fixes/out/working.db` (1,252 entries).

Paths such as `/mnt/project-files/...` and `set-theory-entries/...` refer to the
project's shared files, not to this repository.

## 1. Goal and scope

When two entries are genuinely the same page, they become one. The **survivor S** keeps its id and URL and
gains the useful content of the **absorbed entry A**. A is **retired, not deleted**: its row and its
own metadata stay in the database untouched, its old URL lands on S, and it disappears from the index,
search and the autolinker. Each merge is reviewed and logged. Undo is available while the recorded
post-merge state still matches (§8).

**Closely related is not the same as duplicate.** A definition, a characterization and a theorem
about the same object usually deserve separate pages. Those get cross-links, not a merge. Shared
terminology (a synonym or defined term used by two entries) is never enough on its own to justify a merge (§9).

Retiring an entry with **no survivor** (e.g. the "PStricks Create Test" leftover) uses the same
mechanism.

## 2. Schema change

`math_concepts` has no status today. `canonical_name` is UNIQUE, `slug` has **no** unique constraint
(all 1,252 slugs happen to be distinct), and every reader reads all rows.

Add to `math_concepts` (nullable, no default; existing rows stay active):

| Column | Type | Meaning |
|---|---|---|
| `retired_at` | TEXT (ISO 8601 UTC) | NULL = active. Set = retired. **This is the "is active" flag**; one column can't contradict itself. |
| `retired_into_id` | INTEGER REFERENCES math_concepts(id) | The survivor; NULL for a retirement with no survivor. |
| `retirement_reason` | TEXT | Required when retired. |

Add `CREATE UNIQUE INDEX idx_math_concepts_slug_ci ON math_concepts(lower(slug))` so the database
itself reserves URLs (§4).

Add a log table:

```
math_concept_merges(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  absorbed_id INTEGER NOT NULL REFERENCES math_concepts(id),
  survivor_id INTEGER REFERENCES math_concepts(id),   -- NULL: retirement with no survivor
  applied_at TEXT NOT NULL,
  undone_at TEXT,
  reason TEXT NOT NULL,
  survivor_before_json TEXT,    -- S as frozen when the merge session started (§5 step 2); NULL for plain retirement
  survivor_after_json TEXT,     -- S's full entry + diagram list as approved (required to be live)
  added_rows_json TEXT NOT NULL,-- every row the merge added to S, and every redirect it repointed
  package_sha256 TEXT NOT NULL)
```

Add a one-row-per-key table `math_schema_meta(key TEXT PRIMARY KEY, value TEXT NOT NULL)` holding
`retirement_contract_required` (§10, "Compatibility contract").

Code enforces: `retired_into_id` only with `retired_at`; S must be active; no S = A; reason required.

### The schema upgrade is idempotent *and* checked
The schema package and the migration run the same function, which for each object:
- **missing** → creates it;
- **present** → compares its definition with the expected one (column name, declared type and
  REFERENCES clause from `PRAGMA table_info`/`foreign_key_list`; the exact `sqlite_master.sql` for
  the index and the two tables). Identical: skip. Different: **refuse everything** and report the difference.
  A half-applied or hand-made variant is never accepted silently.

Before creating the unique slug index it runs
`SELECT lower(slug), group_concat(canonical_name) FROM math_concepts GROUP BY lower(slug) HAVING count(*) > 1`
(and the same for `lower(trim(slug))` to catch stray spaces). Any result → refuse and list the
colliding entries. The current working copy has none (1,252 entries, 1,252 distinct slugs). All
statements run in one transaction after a verified backup, followed by `integrity_check` and
`foreign_key_check`.

## 3. What a merge changes, and what stays intact

v1 moved A's rows to S. **v2 copies instead**, so A stays exactly as it was:

**Stays intact on A:** the `math_concepts` row (title, slug, canonical name, text, rendered HTML,
timestamps), its types, classifications, synonyms, defined terms, link exclusions, related links,
diagram rows and SVG files. Retirement only *sets* A's three new columns. Readers ignore A's metadata
because A is retired (§6).

**Added to S** (each listed in `added_rows_json`):
- A's synonyms and defined terms that S doesn't already have (case-insensitive);
- A's **title** as a synonym of S (default on, opt-out per merge);
- A's MSC classifications that S lacks;
- A's outgoing related links, minus duplicates and S→S.

**Repointed redirects:** any entry already retired *into A* gets `retired_into_id = S` (recorded, so
undo can put it back). Redirects never chain.

**Not changed anywhere else:** no other entry's text or metadata. Links *into* A from other entries,
both `\PMlinkname` and related-concept rows, are resolved to S **when the page is viewed** (§6). v1
proposed rewriting other entries' related rows. v2 drops that, which keeps every other entry's
snapshot unchanged and makes undo much simpler.

S's own text change is **not** made by the retirement step. It's published before it (§5), and both
versions of S are captured in the log.

## 4. Identity reservation vs alias collisions (two separate rules)

**Identity (names and URLs), checked across active AND retired rows:** a new entry may not reuse any
existing `canonical_name` or slug, case-insensitively. Today that's enforced in code (`check_target`,
`slug_helper`). v2 adds the unique slug index so it's enforced in the database too. Retired entries
keep their names and URLs forever, and those keep resolving to S.

**Aliases (titles, synonyms, defined terms as link and search text), checked across ACTIVE rows
only:** the existing rule applies (a synonym may repeat another entry's defined term; nothing else may
repeat). For a merge the comparison set is *active entries other than A and S*. So A's title becoming
S's synonym is allowed (A is leaving the active set), while a clash with any unrelated active entry
refuses the package and names the clash. The editor's and new-entry checks are updated to skip retired
rows for alias checks only. A new entry whose title equals a retired title gets a warning naming the
survivor.

## 5. Publication sequence: local authoring, then reviewed production publication

Each merge goes through these steps in order:

1. **Choose** (§9): Chi approves the pair, the survivor, and "merge" as the action.
2. **Start the merge session** (option 21, "start"), **before S is edited.** The helper reads A and
   S (full snapshots and stored diagram lists) **from live** over SSH, read-only, the way option 20
   reads the live catalog. It also checks the working copy's S and A equal those (no unpublished local edits
   to either; otherwise it stops and says so). It freezes them in
   `dist/merge-sessions/<id>/session.json` with a SHA-256. That frozen S is `survivor_before`. It
   doesn't depend on when the baseline was last synchronized, and it's kept unchanged through both
   publications and written into the log. An intervening option 8 or unrelated publish doesn't change it.
   If live S changes for any reason other than this session's step-4 publish, step 6 refuses, and the
   session has to be restarted.
3. **Author locally:** edit S in the working copy (fold in A's content; render any diagrams with
   option 19). Claude drafts, Chi reviews.
4. **Publish S's text** with existing options 2 → 3 → 4 → 5 (text and, if needed, the diagram route).
   Verify S's page. *Intermediate state: A and S both active, S already improved. That's a valid state
   to stop in.*
5. **Prepare the retirement**, option 21 "prepare". It takes `survivor_before` and A from the
   session, and S_after (the approved text and diagrams) from the **working copy**. It refuses if
   S_after equals `survivor_before` (no text change), unless Chi confirms a metadata-only merge.
   It writes a review: rows to add, redirects to repoint, warnings, alias checks.
6. **Stage, check, publish** with 3 → 4 → 5. Under `BEGIN IMMEDIATE`, publish verifies that live S
   **equals S_after, including stored diagrams**, that live A equals the session's frozen A and is active, and
   that the alias rules hold. Then it takes a verified backup, applies §3, reads back, verifies and commits.
   **If anything differs, nothing is applied and both entries remain active**, which is the recoverable
   state from step 4. A successful publish returns a **merge receipt** (§7) that the helper saves
   in the session folder.
7. **Verify live:** S's page, A's old URL, search for A's title, one page that links to A.
8. **Option 8.** This is required before the next merge (§7).

### Plain retirement (no survivor)
A separate, simpler path: option 21 "retire" → review → 3/4/5 → option 8. Rules for the first implementation:
- A must be active, and **no entry may be retired into A**. If any is, the retirement is refused and
  those entries are listed. (Their redirects would have nowhere to go. Merge A into a survivor instead, or undo
  those merges first.)
- No rows are added anywhere. Only A's three columns are set; `survivor_before_json` is NULL.
- The review lists every incoming link to A (`\PMlinkname` targets and related rows) and what will
  happen to it. A PMlinkname to a retired entry with no survivor renders as plain text (the current
  behaviour for an unknown target), and related links to A are hidden. Chi can fix those entries
  first with options 2–5 if wanted.
- A's old URL shows "This entry has been retired" with the reason.
- The same receipt and option 8 rule apply (§7).

## 6. How readers treat a retired entry (production website code)

| Place | After |
|---|---|
| Page by slug or id | A is retired into S: the API returns S plus `merged_from: {title, slug}`. The page switches the address bar to S, sets a canonical link, and shows "*A* has been merged into this entry." No survivor: a "this entry has been retired" notice. This is client-side, since `concept.html` is static, not an HTTP 301. |
| `\PMlinkname{…}{A}` in other entries | The existing view-time lookup (canonical name → slug) maps A to S's slug. No TeX is rewritten. |
| Related list on a page | A related link to A is shown as S, de-duplicated, and S never links to itself. |
| Autolinker, catalog, index, classification hubs/counts, public search | active rows only; A's former aliases reach S through the rows copied onto S |
| Admin search/audit/edit | retired rows listed as "retired → S". The editor refuses to save a retired entry. |
| New-entry checks (option 2, option 20, editor create) | identity across all rows; aliases across active rows (§4). Naming a retired entry as related concept or PMlinkname target gives a message naming S. |

## 7. Fresh state: one merge per sync (v1 of the feature)

After a merge, the baseline and working copy lack its changes until option 8. A second merge started
before then would freeze live state but author against a stale working copy, and its conflict checks and
option 8 reconciliation would have to combine two receipts. **Rule for the first implementation:** after a retirement package is published, the helper
records "merge published, sync pending". Option 21 refuses to prepare another merge or undo until
option 8 completes. Options 2–5 for unrelated entries keep working as today.

Several merges per sync would need a designed refresh of the planning state (e.g. planning from a fresh
live snapshot). That's deferred and out of scope.

### Option 8 reconciliation of a completed merge
**Problem:** after the merge, the working copy has S's new text (published in step 4, so it already
equals live) but not the copied metadata, A's retirement or the log row. Today's comparison would find
`math_concepts`, `math_synonyms` and others differing between working and live while the working copy also
differs from the baseline, and refuse ("Unpublished or divergent local rows need review").

**Rule:** the receipt is the publish result plus the exact row-level change set the package applied
(rows added to S, A's three column values, repointed redirects, the log row). It's stored with its
package SHA-256 in the session folder, and the helper's state lists it as *pending sync*. Option 8 then:
1. confirms the receipt against live: a `math_concept_merges` row with that `package_sha256` exists,
   is not undone, and the live rows named in the change set equal the receipt's after-values. Any
   mismatch → refuse and say which (no guessing);
2. applies **exactly that change set** to the *temporary* upgraded copies of the baseline and working
   database it already compares (§10), and nothing else;
3. runs the normal comparison. The merge's own rows now match on all three sides. **Any other local
   difference is still detected exactly as today.** Unpublished unrelated edits block the refresh and are
   listed, and nothing is overwritten or lost (option 8 never merges unpublished edits into live data;
   that existing behaviour is unchanged);
4. on success, installs the new copies from live as usual and clears *pending sync*.

Undo receipts work the same way, with the inverse change set. Plain retirement receipts have just the
three columns and the log row.

**End-to-end test (required before shipping):** a temp baseline/working/live trio: publish S's text
(options 2–5 path) → publish the merge → option 8 succeeds and the new working copy equals live. Plus
these variants: (a) an unrelated unpublished local edit → option 8 refuses and names it; (b) live
altered after the merge → receipt check refuses; (c) undo → option 8 succeeds; (d) plain retirement →
option 8 succeeds.

## 8. Undo: available when the recorded post-merge state still matches

Option 21 "undo" prepares a package that reverses one merge, applied through 3/4/5 with the same
checks. It's offered only when **all** of these still hold on live:

- A is retired into S with the recorded time and reason;
- S is **active** (S has not since been retired into something else; if it has, undo that later merge first);
- every row the merge added to S is still present and unchanged;
- every redirect the merge repointed (entries once retired into A) still points at S;
- no later, not-undone merge involves A or S (merges undo in reverse order).

- **the alias rules still hold after reactivation.** While A was retired, another active entry
  may have gained a title, synonym or defined term that equals one of A's. So undo computes the
  post-undo state (A active again, the copied rows gone from S) and re-runs the §4 alias check over
  **all** active entries before anything is applied. A clash refuses the undo and names the entry.
  (Identity can't clash, because A's name and slug stayed reserved.)

Otherwise the undo is refused and the review lists exactly what changed. The undo deletes the added rows,
restores repointed redirects to A, clears A's three columns and sets `undone_at`. A is intact (§3),
so nothing has to be put back on A.

**S's text is not reverted by undo.** Its pre-merge version is captured in `survivor_before_json`
(and in git via the migration, §10). Restoring it is a separate, normal text publish (options 2–5).
Option 21 undo can write that text into the working copy for review. If S's text changed again after the
merge, Chi decides by hand.

**Undo of a plain retirement:** offered when A is retired with no survivor at the recorded time and
reason, no later record involves A, no entry has been retired into A since, and the alias re-check above
passes. It clears A's three columns and sets `undone_at`. Nothing else changes, because nothing was added.

Last resort: every publish already takes a verified backup, and restoring the whole database is a
manual step, only when nothing else has been published since.

## 9. Candidate report: merge, cross-link, rename, leave

`find_merge_candidates.py` is read-only, runs on a working copy, and writes
`dist/merge-candidates/<date>/candidates.md` (+ `.csv`). It lists pairs found by any signal, but the
**suggested action** depends on evidence, not on shared words. **Every suggestion is labelled
heuristic.** MSC overlap, document types and text similarity can't establish that two entries say the
same mathematics. The report says so at the top and on every suggested merge.

| Action | When the report proposes it |
|---|---|
| **Merge** | Same subject (MSC overlap) **and** the same content role (both definitions of the same object, or the same statement), **and** strong text overlap or one entry is a strict subset/stub of the other. Never on shared terminology alone. |
| **Cross-link** | Same object, different role: definition vs characterization vs theorem vs examples. Suggests related-concept links or a `\PMlinkname` sentence. |
| **Rename** | Same or near-same title in different subjects. Proposes disambiguated titles; slugs and URLs are unchanged. |
| **Leave** | Shared alias that's legitimate in both places (e.g. "relation" defining "domain"). Shown only in an appendix. |

Each row shows titles, MSC codes, document types (from environments), length, incoming-link count,
the signals, the proposed action and a suggested survivor. Current signal counts: 3 same-title pairs,
20 titles used as another entry's alias, 79 aliases shared by two or more entries, 11 "proof of …" entries.
Of the same-title pairs, "completeness theorem for propositional logic" (ids 19/20, both 03B05) looks
like **merge**, while "filtration" (03B45 vs 03E20) and "Kleene algebra" (06D30 vs 20M35/68Q70) are
**rename**. Chi decides every row. The report is a shortlist, not a verdict.

## 10. Rollout, compatibility and where code lives

### Three places code lives
- **Laptop helper** (`website_workflow.py`, option 21, option 8 rule, snapshot readers, and the
  publisher modules that are **sent over SSH** at publish time): updated by merging the PR and
  `git pull` on the laptop. Option 15 does **not** deploy these.
- **Production readers** (`backend/src` services/routes and `frontend/math`): deployed with option 15.
- **Local server** (option 6): runs the laptop's `backend/src`, so it's also updated by `git pull`.

### Snapshot compatibility (`read_snapshot`)
Eight helper modules call it besides its own (`apply_math_text_patch`, `batch_publish`,
`diagram_sync`, `inspect_staged_package`, `live_math_publication`, `prepare_math_patch`,
`publish_math_entry`, `website_workflow`). Several depend on its exact shape. For example,
`apply_math_text_patch.check_stored_entry` requires the field set to equal `SNAPSHOT_FIELDS`, and
the new-entry, patch and diagram publishers compare `read_snapshot(...) == intended`. Adding fields would make every
already-staged package and every equality check fail. **Rules:**

1. `read_snapshot()` **keeps its exact current output.** No new fields.
2. A new `read_status(db)` returns `{canonical: {retired, retired_into, reason}}`. It's used by
   option 21, option 1 and the guards below. On a database without the columns, it returns "all active".
3. Existing package kinds gain one guard on apply: refuse if the target entry is retired (text patch,
   diagram package). New-entry packages refuse retired related concepts. Package formats are unchanged,
   so packages staged before the upgrade still validate.
4. Option 1 reports a locally edited retirement column as *unsupported: use option 21*.

**Regression tests before rollout:** an old-format text patch, diagram package, new-entry package and
option 20 batch each apply on (a) an old-schema database and (b) an upgraded database with zero
retirements, with identical results. `read_snapshot` output is byte-identical before and after the
upgrade. Option 8 runs old→upgraded and upgraded→upgraded. Readers on an upgraded database with zero
retirements return the same JSON as today.

### Rollout order (one time)
1. **Laptop:** merge the PR, `git pull`.
2. **Schema package** via 3/4/5: adds the columns, the slug index, the log table and
   `math_schema_meta` on live, with the checks in §2. The current live code ignores them.
3. **Production readers** via option 15. Verify pages, search and the catalog are unchanged.
4. **Option 8** with the new rule: if the only schema difference is this known upgrade, it applies it
   to **temporary copies** of the baseline and working database, compares as usual, and installs new
   copies from live. Your originals are never edited. New columns and the log are compared by content,
   with ids mapped to canonical names.
5. Only then the first merge (§5).

### Compatibility contract (replaces v2's source-text guard)
Whether code "has the filter" can't be decided by searching source text. So the guarantee is a
**declared version backed by tests**:

- `backend/src/services/math/retirement.py` declares `RETIREMENT_CONTRACT = 1`, a plain integer
  literal. All readers get the active-row filter and redirect resolution from this module.
- `tests/test_retirement_readers.py` defines contract 1 as behaviour. On a fixture with a merged
  entry, a plain-retired entry and a redirect, every public and admin reader (detail by slug and by id,
  catalog, classification hubs and counts, search, autolinker, PMlinkname resolution, related list,
  admin search, editor save) must behave as §6 says. The test asserts the constant equals the contract
  it checks, so raising or keeping the number without passing tests fails. **Release requirement:** a
  PR that touches math readers merges only with this suite passing, and that's in the PR checklist and
  the runbook.
- Live records `math_schema_meta.retirement_contract_required`. The schema package sets it to 0. The first
  merge or plain retirement raises it to 1 in the same transaction.
- **Option 21** refuses to prepare a merge unless the *deployed* production code declares a contract ≥ 1.
  It reads the literal from the server's `retirement.py` over SSH (parsed with `ast`, nothing executed).
- **Option 15** reads `RETIREMENT_CONTRACT` from the package's `retirement.py` the same way and
  refuses to publish if it's missing or lower than live's `retirement_contract_required`.

So correctness comes from the tests, and the guard only compares two declared numbers.

### Code rollback
While `retirement_contract_required` is 0 (no retirements yet), redeploying earlier code is allowed.
Once it's 1, option 15 refuses code that doesn't declare contract ≥ 1. Going back to pre-retirement
code means undoing every merge and retirement first, then lowering the requirement with a reviewed
schema-meta package.

### Migrations (git record)
`add_math_retirement_columns.py` (same DDL, idempotent, `--db` required, preview by default,
`--apply` backs up first). `math_entry_merge.py` replays a merge from its recorded plan, including
S_after's text. A `merge_entries_<date>.py` per session lists merges in the order they were applied on live,
committed by PR after Chi verifies. `step1_load_relational.py` is unchanged.

## 11. Chi's review points → where answered

| Review point | Answer |
|---|---|
| Related ≠ duplicate; merge/cross-link/rename | §1, §9 |
| 1. Explicit publication sequence; survivor must be live; failure leaves both active | §5 |
| 2. Successive merges and fresh state | §7: one merge per sync in v1 |
| 3. Snapshot changes are a compatibility change | §10: `read_snapshot` unchanged, new `read_status`, regression tests |
| 4. Tighter undo, survivor text, redirect repointing, later retirement of S | §8, log columns in §2 |
| 5. Code rollback claim | §10 "Code rollback" |
| 6. Identity reservation vs alias collisions | §4, slug index in §2 |
| "A's rows stay as they are" contradiction | §3: v2 copies, so A is truly intact |
| Option 15 vs helper | §10 "Three places code lives" |
| **Review 2:** 1. Option 8 reconciliation of a merge + end-to-end test | §7 "Option 8 reconciliation" |
| 2. Freeze S before authoring | §5 step 2, `survivor_before_json` in §2 |
| 3. Plain retirement and its undo; redirects into A | §5 "Plain retirement", §8 |
| 4. Undo re-checks alias collisions | §8 |
| 5. Concrete compatibility guard | §10 "Compatibility contract" |
| Schema upgrade checks definitions and slug collisions | §2 "The schema upgrade is idempotent and checked" |
| Candidate suggestions are heuristic | §9 |

## 12. Build plan (after approval)

1. Candidate finder (read-only). **Approved 2026-10-25; being built.**
2. Schema, `read_status`, readers, guards, option 8 rule, compatibility tests. Rollout per §10.
3. Option 21 (start session, merge, plain retirement, undo), receipts, option 8 reconciliation,
   end-to-end tests, sync-pending lock, migration helper, docs (CONTENT_SYNC,
   ADDING_ENTRIES, ADMIN_RUNBOOK).
4. First real merge, recorded as a migration PR.
