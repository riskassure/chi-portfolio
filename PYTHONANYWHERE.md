# First deployment: cwoo.pythonanywhere.com

For subsequent releases, follow [UPDATING_WEBSITE.md](UPDATING_WEBSITE.md).
Do not reuse this first-deployment package to update the live database.

This package contains a private database snapshot. Upload it only inside your
PythonAnywhere account, not to a public file-sharing site. It contains no hosting
password or OAuth credentials. Local import staging rows and unpublished Google
Photos drafts have been removed from the COPY; the laptop database is unchanged.

## 1. Upload and extract

In Files, upload `chi-portfolio-pythonanywhere.zip` to `/home/cwoo/`.
Open a Bash console and run:

```bash
cd /home/cwoo
test ! -e chi-portfolio && unzip chi-portfolio-pythonanywhere.zip
```

This is for a first deployment only. If `chi-portfolio` already exists, stop and
back it up before planning an update; do not overwrite a live database.

## 2. Install dependencies and create private settings

```bash
mkvirtualenv --python=/usr/bin/python3.13 chi-portfolio
cd /home/cwoo/chi-portfolio
pip install --no-cache-dir -r backend/requirements.txt
python backend/setup_pythonanywhere.py
python -m unittest discover -s backend/tests -q
```

The setup script prompts privately for a NEW portfolio administrator password
(16+ characters), separate from your PythonAnywhere login. It generates a session
secret and saves both outside the website in `~/.config/chi-portfolio/hosting.json`.
It refuses to overwrite an existing configuration. No credentials are printed.
Do not paste them into chat or commit that file.

## 3. Configure the Web tab

- Python version: **3.13**, Manual configuration.
- Virtualenv: `/home/cwoo/.virtualenvs/chi-portfolio`
- Source code and working directory: `/home/cwoo/chi-portfolio`
- In the linked WSGI configuration file, replace the example content with:

```python
import sys
sys.path.insert(0, '/home/cwoo/chi-portfolio/backend')
from pythonanywhere_wsgi import application
```

Do not run `app.run()`, `serve.py`, or Waitress on PythonAnywhere. Its WSGI
service loads the application directly. Leave Static files mappings empty for
the first check; Flask serves the frontend. Never map the backend directory or
repository root as a static directory.

Enable **Force HTTPS** in the Web tab, then reload the web app. Setting up WSGI
and reloading publishes the included site and catalog at the supplied address.
Before doing that, confirm you are comfortable making the existing biography,
resume contact details, photographs and catalogs public.

## 4. Check the hosted site

Visit `https://cwoo.pythonanywhere.com/`. Check home, biography, resume, music,
photography, math search and a math entry containing a diagram. Test admin login
and logout. Only test editing after saving a copy of the hosted database.
The browser Network panel should show no calls to `127.0.0.1` or mixed-content errors.
If startup fails, inspect the error log linked in the Web tab; share the error
message, not your private settings.

Google Photos and Spotify connection/import screens intentionally remain local
to your laptop. Existing published photos and music are included. Generating new
LaTeX/PSTricks diagrams may require tools unavailable on the host; pre-generated
diagram assets are included. Editing text mathematics does not require those tools.

The login limiter is process-local; a paid plan with multiple workers would need
a shared rate limiter before relying on it for public administrator protection.
SQLite suitability and concurrent editing should also be rechecked as traffic grows.

Once verified, delete only `/home/cwoo/chi-portfolio-pythonanywhere.zip` through
the Files tab to free quota; keep the extracted site. Keep private database/media
backups outside public paths. The package fits the free tier's disk limit with
room for the Python environment, but monitor the account's actual storage use.

Local verification: Python 3.13 on Windows; the hosted Linux environment still
needs the installation, tests and browser checks above.

Provider reference: https://help.pythonanywhere.com/pages/Flask/
