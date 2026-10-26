# How the website works

An orientation for someone who knows Python and SQLite well but hasn't done much
web programming. It explains what runs where, why the helper's steps are shaped as
they are, and where to look when something breaks. The procedures themselves are in
the [admin runbook](../ADMIN_RUNBOOK.md). Checked against `backend/src/app.py`, the
WSGI and local start scripts and the math concept page on 2026-10-26.

## The big picture

The whole site is **one Flask application** (`backend/src/app.py`) and **one SQLite
database** (`portfolio.db`). A visitor's browser talks only to that application. It
makes two kinds of requests:

| Request | Example | Who answers | What comes back |
| --- | --- | --- | --- |
| A page file | `/math/concept.html`, `/math/math_concept.js`, `/style.css` | `frontend_file` in `app.py`, which reads the file from `frontend/` | The file, unchanged |
| An API call | `/api/math/concepts/function` | A route function in `backend/src/routes/*.py` | JSON built from the database by `backend/src/services/` |

The HTML files are mostly empty shells. Their JavaScript runs **in the visitor's
browser**, calls the API, and builds the page from the JSON it gets back. So a page
is assembled in two places: the server picks the data, and the browser lays it out.

What happens when someone opens `https://www.cwoo.me/math/concept.html?slug=function`:

1. The browser asks for `concept.html`. Flask sends the file from `frontend/math/`.
2. The HTML tells the browser to load `runtime-config.js` (which tells the page's
   scripts that the API lives at `/api`), the shared `navbar.js`, the math scripts,
   stylesheets, and MathJax from `cdn.jsdelivr.net` (a public
   content delivery network, not this site).
3. `math_concept.js` reads `slug=function` from the address and calls
   `/api/math/concepts/function`.
4. The route `get_math_concept_detail` in `routes/admin_math.py` opens the database,
   asks `fetch_public_math_concept_detail` for the entry, and returns JSON. A missing
   entry gives HTTP status 404.
5. Back in the browser, `math_concept.js` repairs and inserts the stored HTML
   (autolinks, retired-entry redirects, diagram images), and MathJax turns the TeX
   into typeset formulas.

Consequence: the text stored in `rendered_tex` is not what the visitor sees. Step 5
changes it a lot: `concept.html` loads about 45 small repair scripts from
`frontend/math/render/` before `math_concept.js`. Only a real browser shows whether a page renders correctly.

Other parts work the same way: the music page calls `/api/music/...`, photography
`/api/photography/...`, the travel map `/api/travel/...` plus Esri's map library
from `js.arcgis.com`.

## Local preview and the live site run the same code

| | Local preview (helper option 6) | Live site |
| --- | --- | --- |
| Address | `http://127.0.0.1:5001` (only your laptop can reach it) | `https://www.cwoo.me` |
| Started by | `backend/start_local.py` | PythonAnywhere, through `backend/pythonanywhere_wsgi.py` |
| Database | The helper's working copy (`PORTFOLIO_DB_PATH`) | `/home/cwoo/chi-portfolio/backend/portfolio.db` |
| Admin password | Your local one (saved with Windows encryption) | The production one, in `hosting.json` on the server |
| Errors appear in | The terminal running option 6 | The **error log** on PythonAnywhere's Web tab |

Because the code is the same, a change that works locally will usually work live,
as long as the live files and database match what you tested. That is what the
helper's "check live" step (option 4) checks.

## What a "reload" is, and when it's needed

PythonAnywhere keeps the Flask application running in the background and imports the
Python code once when it starts. Its WSGI file (a small Python file PythonAnywhere
calls; ours just imports `pythonanywhere_wsgi.py`) is how it finds the app.

| What changed | Needs a reload? | Why | Helper option |
| --- | --- | --- | --- |
| Python under `backend/src` | **Yes** | The running process still has the old code imported | **15** (it reloads and checks the homepage; **16** retries) |
| HTML, CSS or JavaScript under `frontend/` | No | Flask reads the file from disk on every request | **14** |
| Database content | No | Every API call opens the database fresh | options 2-5, 9, 12, 20, 21, ... |
| A new Python package (`pip install`) | Yes, after installing | Not handled by the helper | By hand in a PythonAnywhere Bash console, in `/home/cwoo/.virtualenvs/chi-portfolio`, then reload from the Web tab |

Locally it is the same: the option 6 server does not notice Python edits. Stop it
with Ctrl+C and start option 6 again. Frontend edits show up on the next page load.

Python and frontend files that depend on each other (a new JavaScript call to a new
route) must go out together with option 15, or the live page will call a route the
live server doesn't have.

## Browser caching: why a page can look unchanged

Browsers keep copies of files they have downloaded and may reuse them instead of
asking again. API answers are marked `no-store` (never reuse), but page files can be
reused. So after publishing a JavaScript or CSS change you may still see the old one.

- **Ctrl+F5** reloads the page and its files, ignoring the browser's copies.
- A **private/incognito window** shows the page with no stored files and logged out,
  which is how visitors see it.
- Script tags carry a version tag, for example
  `<script src="math_concept.js?v=title-mathjax-v1">`. The part after `?` doesn't
  change which file is served, but it makes the browser treat it as a new address.
  When you change a JavaScript or CSS file that visitors already have, change its
  `?v=` tag in the HTML that loads it and publish both, so returning visitors get
  the new version without pressing Ctrl+F5.

## Logging in

Signing in on `admin_dashboard.html` sends the password to `/api/login`. If it is
correct, Flask gives the browser a signed **session cookie** (a small token the
browser sends back with every request for 8 hours). Admin routes, such as
`/api/admin/math/...`, check that cookie and answer 403 without it. The pages
themselves are public files; only the API calls behind the edit buttons are
protected. Being signed in can change what a page shows, so check pages logged out
(a private window) before calling a publication verified.

Local and live logins are separate: each has its own password and its own cookie.

## Seeing what the browser sees (developer tools)

Press **F12** in Chrome or Edge.

- **Console** tab: JavaScript errors in red. A page that stays blank or half-built
  usually has one here.
- **Network** tab: every request the page made, with its status code. Click one to
  see the JSON the API returned. Reload the page with the tab open to fill it.

Status codes you'll meet:

| Code | Meaning | Where to look next |
| --- | --- | --- |
| 200 | OK | If the page is still wrong, the problem is in the data or the browser-side JavaScript |
| 304 | "Use your stored copy" | Normal; Ctrl+F5 if you suspect a stale file |
| 403 | Refused: not signed in, or the request came from an unexpected address | Sign in again; use the exact address `http://127.0.0.1:5001` locally |
| 404 | Not found: no such file, route or entry | Check the address and slug; a new file may not be published |
| 429 | Too many login attempts | Wait a minute |
| 500 | The Python code raised an error | The option 6 terminal, or PythonAnywhere's error log |

## When something breaks

| Symptom | First check |
| --- | --- |
| Whole site down or "Something went wrong" | PythonAnywhere Web tab: error log, then server log. A failed reload after option 15 shows here; see option 16 |
| One page blank or half-built | F12 Console for a JavaScript error; Network for a failing API call |
| Formulas show as raw TeX | MathJax didn't load (Network tab, `cdn.jsdelivr.net`) or rejected the TeX (red text in the formula) |
| Change published but not visible | Ctrl+F5 or a private window; then confirm with the helper receipt that it was published |
| Works locally, not live | Was the matching Python published with option 15? Is the live database content the same (option 8 compares)? |
| Edit button does nothing | Session expired: sign in again |

## Map of the repository

| Folder | What it is | Runs where |
| --- | --- | --- |
| `frontend/` | The website's pages, JavaScript, CSS and images | Visitors' browsers |
| `backend/src/app.py` | The Flask app: file serving, login, security headers, route registration | Server (live and local) |
| `backend/src/routes/` | API routes, one file per area | Server |
| `backend/src/services/` | The logic behind the routes: database queries, rendering, autolinks | Server |
| `backend/src/database/` | Database setup and the math migrations (git records) | Your laptop, by hand |
| `backend/*.py` | The helper (`website_workflow.py`) and its tools: packaging, SSH checks, publishing, option 8 | Your laptop; some pieces are sent to the server over SSH to check or publish |
| `backend/tests/` | Automated tests (`pytest backend/tests`) | Your laptop |
| `dist/` | Helper state: working copies, packages, receipts, batches, merge sessions. Not in git | Your laptop |
| `docs/` | These guides | |

Git records code history only. Pushing to GitHub does not change the website; the
helper does, and the database is never in git.
