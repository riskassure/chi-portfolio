# Keeping Python packages up to date (Dependabot and option 22)

The website runs on other people's code as well as its own: Flask (the web
framework), Werkzeug and Jinja2 underneath it, Pillow for images, zxcvbn for the
password check, and a few more. They are listed, each with one exact version, in
`backend/requirements.txt`. When one of them fixes a security hole, the site only
gets the fix once that version is installed on PythonAnywhere.

Two pieces handle this:

1. **Dependabot** (a GitHub feature) watches for new versions and opens a pull
   request (PR) that changes `backend/requirements.txt`. The tests run on it like
   on any PR.
2. **Helper option 22** installs the versions from `main`'s
   `backend/requirements.txt` into the live site's virtualenv and reloads the site.

Merging a Dependabot PR changes only the file in git. Nothing on the laptop or the
live site changes until you run option 22 (live) and the laptop pip command below.

## Words used here

| Word | Meaning |
| --- | --- |
| Package | A library of Python code someone else publishes on PyPI (the Python package index), installed with `pip`. |
| Pin | A line like `Flask==3.1.3`: exactly this version, nothing newer. Every line in `requirements.txt` is a pin, so the laptop, GitHub's tests and the live site all run the same versions. |
| Virtualenv | A private folder of installed packages for one program. The live site's is `/home/cwoo/.virtualenvs/chi-portfolio`; the laptop's is `.venv313`. Installing into one doesn't touch the other. |
| Patch / minor / major | Version `3.1.3` is major 3, minor 1, patch 3. Patch and minor updates should not break anything; a major update (3 to 4) may need code changes. |
| Transitive dependency | A package the site doesn't import itself, but Flask does (Werkzeug, Jinja2, click...). Pinned too, so nothing changes by surprise. |

## What Dependabot sends you

Configured in `.github/dependabot.yml`:

- **Python packages, weekly (Mondays):** one PR whose title starts
  "Python packages:" and mentions the `python-packages` group, with all patch and
  minor updates together. A major update comes as its own PR.
- **GitHub Actions steps, monthly:** one PR updating the tools the test workflow
  uses (`actions/checkout`, `actions/setup-python`). These affect only the tests on
  GitHub, never the site: merge them when the checks are green; no option 22.
- **Cooldown of 7 days:** a new release is only proposed once it is a week old.
  Broken or tampered releases are usually found and withdrawn within days.
- At most 5 open package PRs at a time.

GitHub sends you a notification (and email, depending on your GitHub settings)
for each one.

### Security alerts (one-time setting)

Dependabot can also open a PR straight away, ignoring the weekly schedule and the
cooldown, when a pinned version has a published security hole. That part is a
repository setting, not a file: on GitHub open the repository, **Settings**,
**Advanced Security** (older pages: **Code security**), and turn on
**Dependabot alerts** and **Dependabot security updates**. Alerts then also appear
under the repository's **Security** tab.

## Handling a Dependabot PR

1. **Open the PR** and wait for both checks (`pytest (ubuntu-latest)` and
   `pytest (windows-latest)`) to finish.
2. **Red cross:** don't merge. A newer version broke a test. Ask Claude to look
   at it; the fix is either a code change in the same PR or skipping that version.
   Writing `@dependabot ignore this minor version` (or `major version`) as a PR
   comment tells Dependabot to stop proposing it.
3. **Green tick:** read the list of changed versions in the PR description. For a
   major update, or anything touching Flask or Werkzeug, a quick local test is
   worth it before merging (see [Trying it locally first](#trying-it-locally-first)).
4. **Merge** (squash, like every PR).
5. **Install it on the laptop and the live site,** below.

You don't have to handle every PR the week it arrives. If a second weekly PR
comes before you merged the first, Dependabot updates or replaces the older one.

## Installing after a merge (option 22)

In PowerShell in `C:\Development\chi-portfolio`:

1. `git switch main` and `git pull` (the [deploy guard](DEPLOY_GUARD.md) refuses
   anything else).
2. Laptop packages:
   `.\.venv313\Scripts\python.exe -m pip install -r backend\requirements.txt`
3. Start the helper and choose **22**.
4. It runs the deploy guard, then reads the live virtualenv over SSH (no changes)
   and lists each package that differs, for example
   `Flask  3.1.3 -> 3.1.4`. If nothing differs it says so and stops.
5. Type `UPDATE`. pip's messages scroll past (a minute or two). The helper then
   copies `requirements.txt` to the live folder, checks every pin is installed,
   reloads the website and checks that the homepage answers.
6. **Check the site in a private window:** the homepage, a math entry, and the
   admin sign-in (sign in and out). If something is wrong, see
   [Undoing an update](#undoing-an-update).

At the end it says whether the laptop's versions match too, and gives the step 2
command if not.

The receipt, with the versions before and after, is saved as
`dist\package-updates\<date-time>.json`.

### If option 22 stops

| Message | Meaning | What to do |
| --- | --- | --- |
| `Deploy guard: ...` | The laptop isn't on a clean `main` that matches GitHub | The fix is printed; see [Deploy guard](DEPLOY_GUARD.md) |
| `... is not an exact pin like "Flask==3.1.3"` | A line in `requirements.txt` isn't `name==version` | Fix it in a PR; option 22 never installs ranges |
| `pip install failed ...; the live requirements.txt was left as it was` | pip couldn't install a version (PyPI unreachable, a version with no build for PythonAnywhere's Python 3.13) | Read pip's last lines above it. pip may have installed some packages before failing, but the site keeps running the code it had loaded: it wasn't reloaded. Run option 22 again once the cause is fixed, or [undo](#undoing-an-update) |
| `pip finished, but these still differ` | pip reported success yet a version is wrong | Rare; ask Claude with the receipt. No reload happened |
| `The PythonAnywhere step did not finish` | SSH failed, or the server answered nothing usable | Check SSH works (`ssh cwoo@ssh.pythonanywhere.com` then `exit`) and run 22 again; it shows the current state first |
| `Reload result is unconfirmed` / `Public homepage verification failed` | Packages are installed, but the reload or homepage check failed | Open the PythonAnywhere **Web** tab: press **Reload**, then read the error log linked there |

### Trying it locally first

Before merging a big update, check out the PR's branch on the laptop
(`git fetch origin` then `git switch <branch name from the PR>`), run step 2's
pip command, and use option **6** to click through the site locally. Afterwards
`git switch main` and run step 2's pip command again to go back.

## Undoing an update

Every version is pinned, so going back is the same path as going forward:

1. On GitHub, open the merged PR and press **Revert**. GitHub makes a new PR that
   puts the old versions back. Merge it when green.
2. Laptop: `git pull`, then the pip command from step 2.
3. Helper option **22**, `UPDATE`. pip installs the old versions and the site reloads.

If the site is down and you need it back before GitHub: in a PythonAnywhere
**Bash** console run `workon chi-portfolio`, then `pip install Flask==<old version>`
(the old versions are in the receipt's `before` list), then **Reload** on the
**Web** tab. Then do steps 1-3 so git and the live site agree again.

## Adding a new package

1. Add `name==version` to `backend/requirements.txt` in the same PR as the code
   that imports it. Use the exact version you tested with on the laptop
   (`.\.venv313\Scripts\python.exe -m pip show <name>` shows it).
2. Merge, then follow [Installing after a merge](#installing-after-a-merge-option-22),
   **before** publishing the code with option 15. The other order would reload the
   site with code that imports a package that isn't installed yet, and the site
   would show an error until it is.

Removing a package from `requirements.txt` does not uninstall it from the live
virtualenv; an unused package does no harm there.

## What it doesn't do

- It doesn't upgrade pip itself or Python. PythonAnywhere's Python version is set
  in the **Web** tab; changing it means a new virtualenv (see
  [First hosting installation](PYTHONANYWHERE.md)).
- Neither Dependabot nor option 22 covers the JavaScript libraries the pages load
  from other websites: MathJax (`mathjax@3`) and the ArcGIS map (`5.1`). Their
  versions are written in the HTML files under `frontend/`.
- The [live files check](LIVE_DRIFT_CHECK.md) compares the live folder's
  `requirements.txt` with `main`, not the installed packages. Option 22 always
  shows the installed versions first, so running it is the way to check.
