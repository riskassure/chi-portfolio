# Deployment preparation

The supported first deployment serves `frontend/` and `/api` from one HTTPS
origin, using Waitress behind a reverse proxy. Hosting, domain, TLS, persistent
storage and a staging browser check still need to be finalized. Nothing here
publishes the site automatically.

## Install and start

Use a dedicated Python 3.14 virtual environment. From the repository root:

```text
python -m venv .venv
# Activate the virtual environment using your platform's activation script.
python -m pip install -r backend/requirements.txt
python -m unittest discover -s backend/tests -q
python backend/serve.py
```

Supply these through the host's secret/environment settings before starting:

| Variable | Value |
|---|---|
| `FLASK_ENV` | `production` (the production launcher sets this by default) |
| `PUBLIC_ORIGIN` | Your exact HTTPS origin, e.g. `https://portfolio.example.com`, without a path |
| `FLASK_SECRET_KEY` | Fresh random secret, at least 32 characters |
| `ADMIN_PASSWORD` | Fresh unique administrator password, at least 16 characters |
| `PORTFOLIO_DB_PATH` | Absolute path to the populated SQLite file on persistent storage |
| `MATH_DIAGRAM_DIR` | Absolute path to the deployed diagrams directory |
| `PORT` | Optional loopback WSGI port; defaults to 8080 |

Generate a secret with `python -c "import secrets; print(secrets.token_urlsafe(48))"`
in your own terminal and store it directly in the hosting secret manager. Do not
commit secrets or reuse the old hardcoded development credentials. Rotate any
credentials that were previously tracked; deleting them from current code does
not delete Git history. Production startup fails if required settings are absent.

Terminate TLS at the reverse proxy, redirect HTTP to HTTPS, preserve the original
Host, and proxy to `127.0.0.1:8080`. Keep that port inaccessible externally. Apply
login rate limits at the proxy as well. The app uses a single-process login limiter;
without trusted proxy IP configuration all proxied clients share a limit. Do not
enable arbitrary forwarded-header trust. Use a service manager for restarts and logs.

## Content and persistent storage

Git contains application code and migration scripts, not the live content database.
Create a consistent snapshot of the current populated database:

```text
python backend/backup_database.py path/to/new-portfolio-snapshot.db
```

Transfer that snapshot privately to `PORTFOLIO_DB_PATH`. Never expose it beneath
the public frontend directory. Do not reconstruct production by running all
migrations alphabetically: these are historical, ordered content changes and some
checks assume the content at that stage. A verified current snapshot is the initial
deployment source. Back up production before subsequent schema/content updates.

Transfer all current `backend/data/math/diagrams/` assets, including ignored
generated files, to `MATH_DIAGRAM_DIR`. Preserve `frontend/images/photography/`
and the other frontend assets at their existing relative URLs. Keep those photos
on durable storage across releases. Stop local imports while taking a coordinated
database/media snapshot. Keep versioned private backups of both; rehearse restoration.

Do not upload raw listening-history exports, account token files, OAuth client
secrets, the local config directory, scratch databases, or the whole backend as
public static files. Only `frontend/` is publicly served by the app.

## Local development and imports

For local editing set `ADMIN_PASSWORD` in the process environment and run
`python backend/src/app.py`. Without it, admin login is disabled. A persistent
local `FLASK_SECRET_KEY` is optional; otherwise sessions expire when the server
restarts. Opt into debug mode with `FLASK_DEBUG=1` locally only.

You may browse at `http://127.0.0.1:5000/`, or keep Live Server on port 5500.
`runtime-config.js` selects the local backend only on those loopback Live Server
pages. Public hosts use relative `/api` requests. OAuth imports for Spotify and
Google Photos remain explicitly laptop-only and disabled in production. Run
imports locally, then publish reviewed data/media through the deployment workflow.
Production does not need your personal OAuth credentials.

## Staging acceptance before launch

- Verify HTTPS, login/logout, wrong-password throttling and cookie flags.
- Browse home, biography, resume and its print preview on desktop and mobile.
- Open music, photography and math search, including pages with diagrams.
- Verify signed-out visitors cannot change content or rotate the shared gallery.
- Verify admin edits and gallery rotation with a staging database, then restore it.
- Confirm Network/Console shows no loopback URLs, mixed content, broken assets or errors.
- Test backup restoration and a rollback to the previous code/database/media snapshot.

Current automated checks do not replace this browser acceptance run or a full
security review. Review public contact information and publication rights before launch.
