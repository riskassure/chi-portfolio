# Deploy guard: publish code only from a clean, up-to-date main

Helper options **14** and **15** copy files from the laptop folder to the live site.
Without a check, they would publish whatever the folder holds at that moment: a
feature branch, an edit you never committed, or an old `main` you forgot to
`git pull`. The live site would then run code that GitHub's `main` doesn't have,
which is exactly the drift the [live files check](LIVE_DRIFT_CHECK.md) finds after
the fact. The deploy guard stops it before it happens.

## What it checks

When you choose **14** or **15**, before anything is read from the live site, the
helper runs `backend/deploy_guard.py`. It asks git four questions, and refuses to
prepare a package unless all four answers are right:

| Check | Refused when | Fix |
| --- | --- | --- |
| Branch | The folder is not on `main` | `git switch main`, then `git pull` |
| Matches GitHub | It first runs `git fetch` (downloads GitHub's history, changes none of your files). Refused if GitHub has commits you don't (behind), you have commits GitHub doesn't (ahead), or both | Behind: `git pull`. Ahead: `git push`, or move the commits to a PR and merge it, then `git pull`. Both: ask Claude |
| Nothing uncommitted | Any tracked file has an uncommitted change, even one you didn't select | Get the change into `main` through a PR, then `git pull`; or throw it away with `git restore <file>` |
| Selected files are in git | A selected file is new and not committed | Commit it through a PR first |

Untracked files you did **not** select (scratch notes, `dist/`) don't matter: they
are never published.

If GitHub can't be reached (no internet), the guard refuses rather than guess.

When the guard passes it prints the commit, for example
`Deploy guard passed: publishing from main at 3acaff1 (clean and matches GitHub).`
The package remembers that commit.

**Option 5 checks again** just before it asks you to type `PUBLISH`, because time
can pass between preparing and publishing. If `main` moved in the meantime (you
pulled a newer merge, or GitHub has a newer one), it refuses with *main has moved
since this package was prepared*: prepare again with 14 or 15. A package prepared
before the guard existed is also refused once; prepare it again.

## What it doesn't check

Content files are data that the local admin pages write, not code. They are
published first and committed afterwards
([Making a change](../CHANGE_STEPS.md)), so the guard ignores them:

- `frontend/geography/places-data.js` (saved map places, published with **14**)
- `frontend/photography/gallery-settings.js` (gallery display settings, option **18**)
- `frontend/images/photography/...` (gallery images)

A selection made only of these skips the guard completely, on any branch. Their
uncommitted changes also never block a code publish.

Options 2-5 for math entries, 8, 9, 11-13, 20 and 21 publish database rows, not
files, and are not affected. Option **16** (retry reload) only reloads code that
option 5 already uploaded and verified, so it isn't guarded again.

## The normal sequence

1. Merge the PR on GitHub (green checks, see [CI](../CI_TESTS.md)).
2. On the laptop, in PowerShell in `C:\Development\chi-portfolio`:
   `git switch main`, then `git pull`. `git status` should say
   *nothing to commit, working tree clean* (untracked files are fine).
3. Helper: **14** or **15**, then 3, 4, 5.

## Reading a refusal

Every refusal starts with *Deploy guard: website code is published only from a
clean main that matches GitHub.* and then says which check failed, lists up to
ten files, and gives the fix. Nothing has been read from or sent to the live site
at that point, and the previous package (if any) is untouched.
