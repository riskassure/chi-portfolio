"""Change the live site's admin password or session secret; never prints them.

Run on PythonAnywhere in a Bash console, then reload the web app from the Web tab:

    cd ~/chi-portfolio/backend/src
    python3 hosting_secrets.py password        # choose a new admin password
    python3 hosting_secrets.py session-secret  # new session secret: signs everyone out

Both rewrite ~/.config/chi-portfolio/hosting.json in place, keeping its other
settings and its owner-only permissions.
"""
import argparse
import getpass
import json
import os
from pathlib import Path
import secrets

SETTINGS = Path.home() / '.config' / 'chi-portfolio' / 'hosting.json'
MIN_PASSWORD, MIN_SECRET = 16, 32


def load(path):
    if not path.is_file():
        raise SystemExit(f'{path} does not exist. Nothing was changed.')
    values = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(values, dict):
        raise SystemExit(f'{path} is not a settings object. Nothing was changed.')
    return values


def save(path, values):
    """Write a 0600 temporary file beside the original, then swap it in."""
    temporary = path.with_name(path.name + '.new')
    temporary.unlink(missing_ok=True)
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as stream:
        json.dump(values, stream)
    os.replace(temporary, path)


def change_password(path, ask=getpass.getpass):
    values = load(path)
    password = ask(f'New admin password ({MIN_PASSWORD}+ characters): ')
    if len(password) < MIN_PASSWORD:
        raise SystemExit(f'Password must contain at least {MIN_PASSWORD} characters. Nothing was changed.')
    if password != ask('Confirm new admin password: '):
        raise SystemExit('Passwords do not match. Nothing was changed.')
    if secrets.compare_digest(password.encode(), str(values.get('ADMIN_PASSWORD', '')).encode()):
        raise SystemExit('That is the current password. Nothing was changed.')
    values['ADMIN_PASSWORD'] = password
    save(path, values)
    return 'Admin password changed. Reload the web app from the Web tab to use it.'


def change_session_secret(path):
    values = load(path)
    values['FLASK_SECRET_KEY'] = secrets.token_urlsafe(48)
    save(path, values)
    return ('Session secret changed. Reload the web app from the Web tab; '
            'everyone signed in (including you) is then signed out.')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('what', choices=['password', 'session-secret'])
    parser.add_argument('--settings', type=Path, default=SETTINGS, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.what == 'password':
        print(change_password(args.settings))
    else:
        print(change_session_secret(args.settings))


if __name__ == '__main__':
    main()
