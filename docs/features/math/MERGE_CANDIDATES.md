# Finding entries to merge, cross-link or rename

`backend/find_merge_candidates.py` lists pairs of math entries that might be duplicates or
might need a link or a clearer title. It only reads. It opens the database read-only and writes a
report into a new folder, so it's safe to run at any time, including while the local server runs.

```
python backend/find_merge_candidates.py --db PATH-TO-WORKING-DB
```

The report goes to `dist/merge-candidates/<UTC time>/` (or `--output NEW-FOLDER`):

- `candidates.md`: suggested merges, renames and cross-links, each with both entries' ids, slugs,
  canonical names (what option 21 asks for), MSC codes, content role, text length and how many entries link to them;
- `candidates.csv`: every pair found, including the ones to leave alone, with an empty
  `chi_decision` column to fill in.

## What the suggestions mean

Every suggestion is a **heuristic**. Shared MSC codes, document types and word overlap can't show
that two entries state the same mathematics, so each row is a question for a person, not an answer.

| Suggestion | When the script makes it |
|---|---|
| merge | In the same MSC area (same first three characters) and with comparable content roles, **and** with evidence in the text: a same-title pair needs strong word overlap (60% or more of the shorter entry's four-word sequences), or the shorter entry is at most a quarter as long while sharing 20% or more of its wording (a possible stub). Pairs with different titles need the shorter entry almost all contained in the other (85% or more), or one title used as the other's synonym or defined term together with strong overlap. A matching title, subject and role without shared text is reported as a rename to check, never as a merge. |
| rename | Same title in different subjects (e.g. two "filtration" entries, 03B45 and 03E20). |
| cross-link | Same object with a different role (a definition and a theorem, or a theorem and "proof of …"), sibling definitions with templated wording, or a title used as the other entry's alias, when the two don't already link to each other. |
| leave | Shared terminology or weak overlap only, or the entries already link to each other. |

A synonym or defined term shared by two entries never produces a merge suggestion on its own.
The content role comes from the title ("proof of", "examples of", "characterization", "properties
of") and otherwise from the document types (definition, statement or mixed). The suggested survivor
is the entry more pages link to (related concepts or `\PMlinkname`), then the longer one. It is only a starting point: read both texts, and decide which URL should stay, before choosing.

Nothing in this report changes any entry. To carry out a merge you have decided on, follow
[Merging and retiring entries](MERGING_ENTRIES.md) (helper option 21).
