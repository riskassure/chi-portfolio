# Batch publishing of new math entries: agreed design (option 20)

**Status: implemented as helper option 20** (PR #15, merged as 39d9e42; Windows
fixes in PR #16, merged as c46b4b5). First used live
for the K_1 batch on 2026-10-24, then for naive set theory on 2026-10-25. This is
the design Chi agreed on 2026-10-23, kept as the record of *why* option 20 works as
it does. For how to use it, follow
[Publish a batch of new entries](../../administration/deployment/CONTENT_SYNC.md#publish-a-batch-of-new-entries)
and the runbook checklist
[Add many new entries at once](../../ADMIN_RUNBOOK.md#add-many-new-entries-at-once-option-20);
where they differ from this design, those guides and the code are current.

The last section, the repository record and git step, was built on 2026-10-30 as
helper option 23 (plan step 8; see
[Record a batch in git](../../administration/deployment/CONTENT_SYNC.md#record-a-batch-in-git)).
It follows Chi's preference below: the record is the batch's reviewed package
payloads, as data, replayed by one shared importer (`math_entry_record.py`) through
the live publishing code; it is checked on scratch copies before a separate
`COMMIT`; and the commit goes on `entries/<date>-<topic>` from an isolated checkout.
The batches before it were recorded by hand with `math_entry_batch.run_batch`.

The text below is the agreed design (originally a PDF dated 2026-10-23), unchanged
except for formatting. Its own status line read: "The design is agreed. Nothing is
built yet, and building starts only when you say go."

---

This version combines Chi's revised plan of October 23 with the decisions from the
discussion the same day. It replaces the first draft.

Option 20 makes publishing several new math entries less repetitive. It keeps every
review, conflict check, backup and verification used for a single entry. It automates
the work around publishing, and never changes mathematical content or links to make
publishing easier.

What changed from the first draft:

- No automatic link changes. Loops of related entries stop and are reported.
- You select the entries and name the batch, rather than it taking every new entry.
- Packages are frozen before you confirm, and working.db is never written.
- Each entry's dependencies are confirmed live just before it publishes.
- Visual checks come before option 8.
- The migration file and git commit are out of the first version and become a later
  feature.

## Standards the tool keeps

These come from Chi's revision. Each one holds in every step below.

1. **Authored content and relationships are preserved.** The tool never reverses,
   removes or invents a related link to get a convenient order. A reciprocal
   relationship is not a duplicate, and publishing constraints never become editorial
   decisions.
2. **Review first, then publish exactly what was reviewed.** Preparation writes only
   local review files, never the working database, baseline, links or production.
   Packages are frozen and checksummed before you confirm, so an edit made during a
   long batch can't slip in.
3. **Check current production, not just a saved baseline.** A read-only batch check
   runs before the first write, and each entry's checks run again right before it
   publishes. Batch approval never authorizes overwriting newer live content.
4. **Per-entry backups and honest partial results.** The existing publishers, with
   their verified backups and conflict checks, do the writing. A batch is not
   all-or-nothing, and the report says exactly which entries applied, were already
   present, failed, are pending or are uncertain. A partial batch is never undone by
   restoring a whole database.
5. **Diagram files and rows stay coordinated.** The existing diagram package workflow
   is used unchanged, including its journal, locks, no-overwrite placement and
   same-source-name policy.
6. **Verify before synchronizing.** Publishing and bringing changes home are separate
   outcomes. If option 8 is blocked by unrelated local edits, the report says
   "publication complete; synchronization blocked", and nothing is forced.
7. **Git is separate from publishing.** The tested tool is committed before it's used.
   Databases, receipts, journals, staging files and credentials never go into git, and
   a batch never commits the whole working tree.

## Decisions

| Question | Decision |
| --- | --- |
| Batch-aware live check | The check code is sent over SSH as now, with no server deployment. The first check may validate against the planned batch order. Right before each entry publishes, its dependencies must really exist on production, so a failed earlier entry blocks everything that depends on it. |
| Mutually related entries and loops | Stop, keep both directions, report the exact loop and block approval of the batch. You may remove those entries and their dependants from the selection and regenerate the review. Two passes work since option 2 publishes related concepts of an existing entry (2026-10-30): publish without one direction, then add it with option 2. |
| `\PMlinkname` targets | Resolved with the site's actual rules. The review shows each resolved destination, and unresolved or ambiguous targets block. A target must be live, or scheduled earlier in the batch and confirmed live before the referring entry publishes. |
| Edits to existing entries | Kept separate in the first version. Later, only edits you explicitly select could be added. |
| Pause between entries | 20 seconds, configurable. Reducing repeated SSH connections is the better speed-up to explore later. |
| Branch name for the later repository record | `entries/<date>-<topic>`, for example `entries/2026-10-23-averages`. The topic is asked for at that step, and a retry reuses the recorded branch. |

## First-version scope

Included:

- New math entries you select. Candidates are shown rather than assuming every local
  draft belongs in the batch.
- Plain text, equations and diagrams the existing publishers already support. Missing
  diagrams are rendered and reviewed with the current workflow (option 19) first.
- Dependencies that can be ordered without changing authored content.
- Sequential publishing with saved progress, safe retry decisions and receipts.
- Option 8 afterwards, once you've checked the live pages.

Not included, initially:

- Edits to existing entries, and deletions. Corrections keep using option 2.
- New asset formats.
- Any automatic link rewriting, and batches with loops.
- Generated migration files and git automation. See the last section.

## The workflow

**A. Select and validate.** Find entries that are in the working copy but not in the
baseline. You pick the batch and give it a descriptive name. The tool shows the drafts
you left out, plus any unrelated local edits that may later block option 8. It then
checks each selected entry against both the batch and current production:

- content eligibility, slug and required metadata;
- diagram readiness;
- duplicate names, using the publisher's own matching rules, including titles that
  clash with synonyms or defined terms.

Every blocker found is reported before anything is written live.

**B. Resolve dependencies without editing content.** Related-concept targets are
required dependencies. `\PMlinkname` targets are resolved separately with the site's
own rules, and any that are unresolved or ambiguous block. The selected entries must
form no loops, and targets publish first. If ordering is impossible, the exact loop is
shown and the batch can't be approved. You may explicitly remove the entries in the
loop, and any entries that depend on them, from the selection, and the review is then
regenerated. A reduced batch is never published silently.

**C. Freeze, check live and review.** Build every package and a batch manifest. The
review shows:

- titles, slugs and canonical names;
- the order, and each entry's dependency targets with their resolved destinations;
- the full content and metadata, not just a one-line summary;
- diagram file checksums, with visual previews.

The batch-aware live check runs against the planned result. If it passes, you type
`PUBLISH ALL` for this exact manifest. Anything else cancels, with no content changes.

**D. Publish with recorded progress.** Stage and publish each frozen package through
the existing mechanisms, pausing 20 seconds between entries. Before each publish, the
entry's live checks run again, and its dependencies must be confirmed on production.
It stops on any conflict or validation failure.

**E. Verify, then optionally bring changes home.** It shows completion totals,
receipts per entry and public URLs, with a checklist that includes every page with
diagrams and some text pages. Your visual check is recorded as a separate step, not
assumed from HTTP success. Option 8 is offered only after you stop the local server
and type `STOPPED`. A blocked refresh stays a separate task you can resume, and
completed entries are never republished.

## Progress, resume and failures

Each batch keeps its own manifest under `dist/math-batches/<batch-id>/`, which git
ignores. The helper's state only points to it, and a lock stops two runs working on
the same batch. Saves are atomic.

The manifest records the batch ID, baseline checksum, selected canonical names,
order, package checksums and reviewed revision. It also holds staging references,
each entry's state and receipts, and separate publication, verification and
synchronization status. It stores no passwords or tokens. Intent is saved before each
remote operation and the result after it.

A resume reloads the manifest, checks package integrity and reconciles any uncertain
operation with production. It never rediscovers a different batch or re-prepares from
the current working copy. Frozen packages and later drafts are kept apart. If a frozen
package changed or went missing, the approval is invalid, and the affected unpublished
entries need a new review, with the old history kept. Later edits to the working
database never enter frozen packages automatically. The tool detects them and explains
the choice: proceed, which publishes the older reviewed version, or stop for a new
review of those entries.

| Situation | What the tool does |
| --- | --- |
| Connection drops while staging or checking | Retries after 30, 60 and 120 seconds, then stops |
| Conflict or validation failure | Stops before that entry. Entries already published stay published |
| An earlier entry failed | Entries that depend on it are blocked, because their targets aren't live |
| Publish not confirmed | Inspects live state first. A full match, as defined below, means done. Matching the expected earlier state may allow a retry. Anything else stops |
| Entry already present | Recorded as already present and skipped, but only on a full match (defined below). A partial match is a conflict and stops |
| Window closed partway | Choosing 20 again resumes from the manifest |
| Option 8 blocked | Reported as "publication complete; synchronization blocked", with the working copy kept |

"Already present" means a full match. The live entry must match the complete intended
entry and all its metadata. For a diagram package, the diagram rows must match too, and
the files must be acceptable under the existing SVG policy. Matching only the title or
canonical name is not enough. The same test decides whether an unconfirmed publish
actually went through.

A lost connection is never treated as a failed transaction, and a partial batch is
never undone automatically. Recovery is a separate, reviewed step.

## What you still do

| Step | Automated | You |
| --- | --- | --- |
| A. Select and validate | Candidate list, all checks | Pick the entries, name the batch, fix anything flagged |
| B. Dependencies | Ordering, link resolution, loop report | If there's a loop, remove those entries and their dependants from the selection, then review again |
| C. Freeze and review | Packages, manifest, batch live check | Review the payloads and previews, type `PUBLISH ALL` |
| D. Publish | Per-entry staging, live checks, publishing, retries | Nothing (the SSH passphrase is already set up) |
| E. Verify and bring home | Totals, receipts, URL checklist, option 8 | Check the live pages and record it, stop the server, type `STOPPED` |

The administrator starts and confirms publication from the laptop.

## Build and acceptance

Delivered as one pull request, following Chi's implementation sequence:

1. Agree the design (this document).
2. Planning, read-only for content: batch selection, frozen packages and manifest,
   dependency and `\PMlinkname` resolution, loop reporting, and the batch-aware live
   check, which extends the check code already sent over SSH.
3. Publishing: sequential orchestration through the existing publishers, live
   dependency confirmation before each entry, bounded retries, reconciliation, lock and
   resume. Option 20 in the menu, plus current docs in `ADMIN_RUNBOOK.md`,
   `CONTENT_SYNC.md` and `ADDING_ENTRIES.md`.
4. Isolated testing before any live trial, covering:
   - entries with and without loops, cross-entry duplicate names, and ambiguous or
     unresolved links;
   - cancellation, changed inputs after review, and two runs at once;
   - lost acknowledgements, partial batches, and a failed entry blocking its dependants;
   - diagram asset conflicts, unsupported edits, and a blocked option 8;
   - the real isolated SSH startup code as well as mocked network failures, since mocks
     alone missed an earlier diagram import-path failure.
5. Commit, then trial: after merging, pull on the laptop and trial two or three
   reviewed new entries with a dependency between them, check the live pages, then run
   option 8. Receipts are kept.
6. Repository record: designed separately, as described below.

Acceptance means:

- authored links are preserved;
- no content database or production changes occur before confirmation, though local
  review artifacts may be written;
- only reviewed package bytes are published;
- partial and uncertain results are reported honestly;
- an interruption can be recovered;
- no unrelated local or production work is lost.

## Later: repository record and git (built as option 23)

A separate feature, to be designed after option 20 is working.

- **Decide the record first.** It could be readable authoring data, a publication
  summary, or a replay tool. Chi's preference is versioned, declarative entry payloads
  with one shared, validated importer, rather than a new standalone migration per
  batch.
- **Replay**, if needed, runs in isolation against a suitable old snapshot. It compares
  only the selected entries, metadata and relationships, by content. Unrelated content,
  Spotify data, IDs, timestamps and generated HTML may differ. How diagram assets are
  kept or reproduced is decided before replay is called working.
- **Git step.** Only after the record is validated and reviewed does a separate
  `COMMIT` action make a focused commit on `entries/<date>-<topic>`, asking for the
  topic then. It handles existing branches, unrelated staged files, interrupted pushes
  and commits already made, without duplicates or overwriting work. A retry reuses the
  recorded branch, and an isolated checkout is preferred.
