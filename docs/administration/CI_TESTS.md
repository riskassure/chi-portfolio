# Automatic tests on GitHub (CI)

Every pull request (PR) and every push to `main` now runs the Python test suite
on GitHub's own computers. This is called **continuous integration (CI)**. It is
the same `pytest backend/tests` you run on the laptop, done for you each time code
changes, so a PR can't quietly break something that a test would have caught.

CI only runs tests. It never publishes to the website, never touches the live or
working databases, and never needs any password or key. Publishing is still
options 14/15 then 3, 4, 5 on the laptop.

## How it works

- The instructions live in [`.github/workflows/tests.yml`](../../.github/workflows/tests.yml).
  GitHub reads any file in `.github/workflows/` as a "workflow": a list of steps
  plus the events that start it. Ours starts on a PR, on a push to `main`, and on
  demand (see below).
- For each run GitHub starts two fresh, empty virtual machines (called **runners**):
  one Linux (like PythonAnywhere) and one Windows (like the laptop). On each it
  checks out the commit, installs Python 3.13 and `backend/requirements.txt` plus
  pytest, and runs `python -m pytest backend/tests -ra`. The machines are thrown
  away afterwards.
- A run takes a few minutes. Public repositories get these runners free.
- If you push again to the same branch while a run is going, the older run is
  cancelled; only the newest commit matters.

The runners start from a clean checkout, so they only see what is in git. No
`working.db`, no `dist/`, no `.env`, no credentials. The tests already build their
own small temporary databases, so this is fine.

### Tests that skip on GitHub

`-ra` makes pytest print a line for each skipped test and why. Expected skips:

| Test | Skips where | Why |
| --- | --- | --- |
| `test_diagram_sync.py` (one render test) | both runners | Needs LaTeX and `dvisvgm`, which only the laptop has |
| `test_local_admin_password.py` (two DPAPI tests) | Linux | Windows-only password storage; they do run on the Windows runner |

A skip is not a failure. A new test that needs something only the laptop has
should skip the same way (`unittest.skipUnless(...)` or `pytest.mark.skipif`), with
a reason.

## Reading the result on a PR

At the bottom of a PR's **Conversation** tab, GitHub shows a box of **checks**:

- **Yellow dot**: still running.
- **Green tick**: all tests passed on that system.
- **Red cross**: something failed. Click **Details** next to it, then the
  **Run tests** step. The end of the log has pytest's usual summary: which test
  failed and the assertion. Fix it on the branch and push; the checks run again.

The same tick or cross appears next to each commit on the repository's front page
and under the **Actions** tab, which lists every run.

A red check does not stop you from pressing **Merge**; it is a warning. If you
want GitHub to refuse merges while tests fail, see [Optional: require green
checks](#optional-require-green-checks).

## Running it by hand

**Actions** tab, **Tests** on the left, **Run workflow**, pick a branch, **Run
workflow**. Useful to re-check `main` after a GitHub outage, or to re-run after a
flaky failure (or use **Re-run jobs** on a finished run).

## When it fails

1. Open the failing run (PR checks, **Details**) and read the pytest summary.
2. Reproduce on the laptop: `.\.venv313\Scripts\python.exe -m pytest backend/tests`
   (or just the named test file).
3. If it fails only on one runner, it is usually a system difference: file paths
   (`\` vs `/`), line endings, or a tool the laptop has but GitHub doesn't. Fix
   the code or make the test skip with a reason; never delete or disable a real
   test to get green.
4. If **Install dependencies** fails, a version in `backend/requirements.txt` may
   no longer install on Python 3.13; that is worth knowing before PythonAnywhere
   hits it too.

## Changing it

- **Python version:** `python-version` in the workflow. Keep it the same as the
  laptop's `.venv313` and PythonAnywhere's.
- **New dependency:** add it to `backend/requirements.txt`; CI picks it up.
- **pytest version:** pinned in the workflow's install step.
- Edit the workflow on a branch and open a PR like any code change; the PR runs
  the edited workflow, so you see the effect before merging.

## Optional: require green checks

GitHub can block the **Merge** button until the checks pass (a "branch
protection rule"). Not turned on. To turn it on: repository **Settings**,
**Branches** (or **Rules**, **Rulesets**), add a rule for `main`, tick **Require
status checks to pass**, and choose both `pytest (ubuntu-latest)` and
`pytest (windows-latest)`. Admins can still override it.
