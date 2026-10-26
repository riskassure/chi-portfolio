# Merging and retiring math entries (helper option 21)

When two entries are really the same page, one of them (the **absorbed entry A**)
is retired into the other (the **survivor S**). An entry that should simply go away,
such as a test leftover, can be retired with no survivor. Nothing is ever deleted.
The approved design is [design v3 of 2026-10-25](MERGING_DESIGN.md).
Use [Merge candidates](MERGE_CANDIDATES.md) to find pairs; you decide every pair.
Terms such as *survivor*, *retire*, *session* and *receipt* are defined in the runbook's
[Terms used for math entries](../../ADMIN_RUNBOOK.md#terms-used-for-math-entries).

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

This is the procedure as run for the first merge on 2026-10-26 (entry 20 into
entry 19). Do one merge at a time; option 21 prepares nothing new until the last
one has been brought home with option 8.

0. **Before you start.**
   - `git pull` on the laptop, stop the local server, run option **8**, and check
     that option **1** lists no math changes. The session refuses an entry whose
     working copy differs from live, and any other unpublished edit would stop the
     option 8 at the end.
   - Decide which entry survives. S keeps its URL, title, slug, document types and
     owner; A's URL will lead to S. Read both texts.
   - Find both **canonical names**: the candidate report lists them (title, id,
     slug, canonical name). They are not always the slug's words capitalised
     (`modal-logic-gl` is `ModalLogicGL`), so copy them, don't derive them.
1. **Start the session first**, before editing anything: option **21 → 2**, type
   `merge`, then A's canonical name (the entry to retire), S's canonical name, and a
   reason. The reason is shown on A's old page and kept in the log. The helper reads
   both entries from live over SSH (read-only) and checks that your working copy has
   the same versions. It then freezes both in `dist/merge-sessions/<id>/session.json`.
2. **Edit S** in your working copy: start option **6**, sign in, open
   `http://127.0.0.1:5001/math/edit.html?id=<S's id>`, fold in A's content and save.
   Change only the **body** and, if needed, the **synonyms**: those are the only
   fields options 2 to 5 can publish for an existing entry (option 1 marks anything
   else `[unsupported]`). Render any changed diagrams with option **19**. Leave A as
   it is. Check S's local page.
3. **Publish S's text:** option **1** lists S; **2** prepares it (pick its number);
   then **3**, **4**, **5** and `PUBLISH`. Check S's live page. Stopping here is
   safe: both entries are active and S is already improved. Option 8 is not needed
   between this step and the merge.
4. **Prepare the merge:** option **21 → 3**, pick the session. Two questions:
   - *Keep the title of A as a synonym of the survivor?* Normally **Y**. When both
     entries have the same title nothing is added, because S already has it.
   - *Is this a metadata-only merge, with the survivor text unchanged?* **N**, since
     you published new text in step 3. Answer Y only if you deliberately left S's
     text alone; otherwise the helper refuses an unchanged survivor.

   The review shows S's text change, what will be copied, the entries linking to
   A, and a check against your working copy. Only A's title, synonyms, defined
   terms, MSC classifications and related links are copied. **Document types are
   not copied**: if S needs one of A's types, that is a separate change.
5. **Stage, check live, publish:** 3, 4, 5. The live check (and the publish again,
   under the database write lock) requires that:
   - the live website code declares retirement contract 1;
   - S on live is exactly the version you prepared from (text, metadata and diagrams);
   - A on live is unchanged since step 1 and still active;
   - no copied term would newly clash with another active entry's title, synonym
     or defined term (overlaps A already had are kept and listed).

   Anything else stops it with `CONFLICT` or `BLOCKED`, and nothing changes. A
   conflict on S usually means step 3 was not published, or S was edited again
   after it; publish S and choose 21 → 3 again.
6. **Verify live**, logged out: S's page; A's old URL
   (`https://www.cwoo.me/math/concept.html?slug=<A's slug>`) shows S with the
   note that A was merged into it; a search for A's title shows one entry; and one
   page that linked to A, if any (the review lists them).
7. **Option 8.** Stop the local server and type `STOPPED`. The publish saved a
   receipt in the session folder and marked it *waiting for option 8*. Option 8
   first confirms the receipt against the live snapshot (the log row, A's
   retirement, the copied rows and repointed redirects). It then applies exactly
   that change to temporary copies of your baseline and working copy before
   comparing. Any other unpublished local edit still stops the refresh, as always.
   If live no longer matches the receipt, option 8 refuses and says what differs.
8. **Record it in git:** write a migration from the receipt and open a PR:

   ```powershell
   .\.venv313\Scripts\python.exe backend/src/database/math/migrations/math_entry_merge.py --write backend/src/database/math/migrations/merge_entries_<date>.py dist/merge-sessions/<id>/receipt.json
   ```

   `--write` never overwrites a file, so give a second merge on the same day its
   own name (for example `merge_entries_<date>_2.py`). Several receipts can go in
   one file, listed in the order they were published. The migration gives S its
   approved text and synonyms, then replays the same change with the publisher's
   own code. It skips anything already recorded. Merge the PR, then `git pull` on
   the laptop.

Keep the session folder: undo needs its `session.json` and `receipt.json`.

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
