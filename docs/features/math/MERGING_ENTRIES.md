# Merging and retiring math entries (helper option 21)

When two entries are really the same page, one of them (the **absorbed entry A**)
is retired into the other (the **survivor S**). An entry that should simply go away,
such as a test leftover, can be retired with no survivor. Nothing is ever deleted.
The approved design is design v3 of 2026-10-25 (`/mnt/project-files/entry-merging/`).
Use [Merge candidates](MERGE_CANDIDATES.md) to find pairs; you decide every pair.

## What a merge does

- **A stays intact.** Its text, metadata, diagrams, name and URL are unchanged. Only
  three columns are set: `retired_at` (NULL means active), `retired_into_id` (S) and
  `retirement_reason`.
- **S gains copies** of what A has and S lacks (case-insensitive): A's title as a
  synonym (unless you opt out), A's synonyms and defined terms, A's MSC
  classifications, and A's related links (no duplicates, never S to itself).
- **Entries already retired into A** are repointed to S, so redirects never chain.
- **No other entry changes.** Links to A, both `\PMlinkname` and related links, lead
  to S when a page is viewed. A's old URL shows S with a note that A was merged into it.
  Search, the catalog, classification pages and the autolinker show only active entries.
- **The log** (`math_concept_merges`) keeps the time, reason, both versions of S (as
  frozen at the session start and as approved) and every row added or repointed.
- **A plain retirement** sets only A's three columns and logs it. A's old URL shows
  "This entry has been retired" with the reason. Links to it show as plain text.
  It is refused while any entry is retired into A: merge A into a survivor instead.

S's text is never changed by the merge itself. You publish it first, as a normal text
edit, so a failure at any point leaves both entries active and both pages working.

## One-time rollout

1. **Laptop:** merge the PR and `git pull`.
2. **Schema:** option **21 → 1**, then 3 (stage), 4 (check live), 5 (publish). This
   adds the three columns, a case-insensitive unique index on slugs, the log table and
   `math_schema_meta`. The live site behaves exactly as before.
3. **Website code:** option **15** with the retirement-aware readers (`backend/src`
   services and routes, `frontend/math/math_concept.js`, `frontend/math/math_editor.js`).
   Check a few pages, search and the catalog: nothing should look different.
4. **Option 8.** It recognises this one known schema difference, upgrades temporary
   copies of your baseline and working copy to compare them, and installs new copies
   from live. Your old databases are not edited.

Run the migration `add_math_retirement_columns.py --db <db> --apply` only on a
database rebuilt from the migrations; option 8 already gives your working copy the
upgrade.

## Merging two entries

1. **Start the session first**, before editing anything: option **21 → 2**, choose
   `merge`, then the canonical names of A and S (as option 1 shows them in brackets)
   and a reason. The helper reads both entries from live over SSH (read-only) and
   checks that your working copy has the same versions. It stops if either has
   unpublished local edits. It then freezes both in
   `dist/merge-sessions/<id>/session.json`.
2. **Edit S** in your working copy: fold in A's content (render any diagrams with
   option 19). Leave A as it is.
3. **Publish S's text** with options 2, 3, 4, 5 as usual and check its page. Stopping
   here is safe: both entries are active and S is already improved.
4. **Prepare the merge:** option **21 → 3**, pick the session. Answer whether A's title
   becomes S's synonym (normally yes) and whether this is a metadata-only merge (S's
   text unchanged; normally no). The review shows S's text change, what will be
   copied, the entries linking to A, and a check against your working copy.
5. **Stage, check live, publish:** 3, 4, 5. The live check (and the publish again,
   under the database write lock) requires that:
   - the live website code declares retirement contract 1;
   - S on live is exactly the version you prepared from (text, metadata and diagrams);
   - A on live is unchanged since step 1 and still active;
   - no copied term would newly clash with another active entry's title, synonym
     or defined term (overlaps A already had are kept and listed).

   Anything else stops it with `CONFLICT` or `BLOCKED`, and nothing changes.
6. **Verify live:** S's page, A's old URL, a search for A's title, and one page that
   linked to A.
7. **Option 8.** The publish saved a receipt in the session folder and marked it
   *waiting for option 8*. Option 21 prepares nothing more until then. Option 8 first
   confirms the receipt against the live snapshot (the log row, A's retirement, the
   copied rows and repointed redirects). It then applies exactly that change to
   temporary copies of your baseline and working copy before comparing. Any other
   unpublished local edit still stops the refresh, as always. If live no longer
   matches the receipt, option 8 refuses and says what differs.
8. **Record it in git:** write a migration from the receipt and open a PR:

   ```powershell
   .\.venv313\Scripts\python.exe backend/src/database/math/migrations/math_entry_merge.py --write backend/src/database/math/migrations/merge_entries_<date>.py dist/merge-sessions/<id>/receipt.json
   ```

   The migration gives S its approved text and synonyms, then replays the same change
   with the publisher's own code. It skips anything already recorded.

## Retiring an entry with no survivor

Option **21 → 2**, choose `retire`, give A and the reason. Then **21 → 3** prepares
the package. Its review lists every entry that links to A; fix those first with
options 2–5 if you want. Then 3, 4, 5, verify, and option 8, as above.

## Undo

Option **21 → 4** lists published merges and retirements and prepares an undo
package for 3, 4, 5. The live check allows it only while the recorded state holds:

- A is still retired as recorded and S is still active;
- every row the merge added to S is still there;
- every repointed redirect still points at S;
- no later merge or retirement involving A or S is still in effect (undo that one first);
- making A active again creates no new alias clash with entries that gained one of
  A's terms meanwhile.

The undo deletes the added rows, points the repointed redirects back at A, clears A's
three columns and marks the log row undone. S's text is not changed. Its earlier
version is in the session file (`frozen.survivor`); restoring it is a normal text
edit with options 2–5. Run option 8 afterwards, and record the undo receipt
(`undo-receipt.json`) in the same kind of migration.

## Compatibility rules

- `read_snapshot` output is unchanged; retirement is read separately (`read_status`).
- Text patches and diagram packages refuse a retired entry. New entries may not use a
  retired entry as related concept; the message names its survivor. Names and slugs of
  retired entries stay reserved; their titles may be reused.
- `backend/src/services/math/retirement.py` declares `RETIREMENT_CONTRACT = 1`.
  `backend/tests/test_retirement_readers.py` defines what that means for every reader.
  **A PR that touches math readers merges only with that suite passing.**
- Once anything is retired, live records contract 1 and option 15 refuses website code
  that does not declare it. Going back to older code means undoing every merge and
  retirement first.
- Last resort: every publish takes a verified backup in the server's `backups`
  folder. Restoring one is manual and only safe if nothing was published since.

## Code

| File | Role |
|---|---|
| `backend/math_schema.py` | the one-time schema upgrade (package, migration and option 8) |
| `backend/merge_sync.py` | checks, change sets, `replay` and `verify`; runs on the server and in option 8 |
| `backend/merge_workflow.py` | option 21 menu, sessions, packages, receipts |
| `backend/bring_changes_home.py` | option 8: confirms receipts and replays them onto temporary copies |
| `backend/src/services/math/retirement.py` | how website readers treat retired entries |
| `backend/src/database/math/migrations/math_entry_merge.py` | git record of published merges |
| `backend/tests/test_merge_publishing.py` | end-to-end: publish S, merge, option 8, undo, plain retirement |
