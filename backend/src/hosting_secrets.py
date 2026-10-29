"""Change the live site's admin password or session secret; never prints them.

Run on PythonAnywhere in a Bash console, then reload the web app from the Web tab:

    cd ~/chi-portfolio/backend/src
    python3 hosting_secrets.py check           # is the current admin password weak?
    python3 hosting_secrets.py password        # choose a new admin password
    python3 hosting_secrets.py session-secret  # new session secret: signs everyone out

password and session-secret rewrite ~/.config/chi-portfolio/hosting.json in place, keeping its other
settings and its owner-only permissions.
"""
import argparse
import getpass
import json
import os
from pathlib import Path
import re
import secrets

SETTINGS = Path.home() / '.config' / 'chi-portfolio' / 'hosting.json'
MIN_PASSWORD, MIN_SECRET = 16, 32
GOOD_LENGTH = 20
# Words a guesser tries first: generic passwords and names tied to this site.
GUESSABLE = ('password', 'passw0rd', 'admin', 'letmein', 'welcome', 'qwerty', 'asdf',
             'iloveyou', 'monkey', 'dragon', 'secret', 'cwoo', 'woo', 'chi', 'portfolio',
             'python', 'anywhere', 'math')
SEQUENCES = ('abcdefghijklmnopqrstuvwxyz', '0123456789', 'qwertyuiop', 'asdfghjkl', 'zxcvbnm')


def weaknesses(password):
    """Plain-language reasons a password is easier to guess than a random one.

    This catches common patterns only. It can't prove a password is random: a
    password that passes can still be weak if it is reused or based on something
    about you. A password manager's generator is the dependable source.
    """
    found = []
    lowered = password.lower()
    if len(password) < GOOD_LENGTH:
        found.append(f'it is shorter than {GOOD_LENGTH} characters')
    kinds = sum(bool(re.search(pattern, password)) for pattern in
                (r'[a-z]', r'[A-Z]', r'[0-9]', r'[^a-zA-Z0-9]'))
    if kinds < 3:
        found.append('it uses fewer than three kinds of character '
                     '(lowercase, uppercase, digits, symbols)')
    words = [word for word in GUESSABLE if word in lowered]
    if words:
        found.append('it contains an easily guessed word (' + ', '.join(words) + ')')
    if re.search(r'(19|20)[0-9]{2}', password):
        found.append('it contains something that looks like a year')
    if re.search(r'(.)\1\1', password):
        found.append('it repeats one character three or more times in a row')
    runs = [run for run in SEQUENCES for start in range(len(run) - 3)
            if run[start:start + 4] in lowered or run[start:start + 4][::-1] in lowered]
    if runs:
        found.append('it contains a run such as abcd, 1234 or qwer')
    if len(set(password)) < len(password) / 2:
        found.append('more than half of its characters are repeats')
    return found


def report(found):
    return 'Weak: ' + '; '.join(found) + '.' if found else 'No common weaknesses found.'


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


def check_password(path):
    """Look at the current admin password without showing it."""
    found = weaknesses(str(load(path).get('ADMIN_PASSWORD', '')))
    advice = (' Consider a new one from a password manager: python3 hosting_secrets.py password'
              if found else '')
    return report(found) + advice, not found


def change_password(path, ask=getpass.getpass, confirm=input):
    values = load(path)
    password = ask(f'New admin password ({MIN_PASSWORD}+ characters): ')
    if len(password) < MIN_PASSWORD:
        raise SystemExit(f'Password must contain at least {MIN_PASSWORD} characters. Nothing was changed.')
    if password != ask('Confirm new admin password: '):
        raise SystemExit('Passwords do not match. Nothing was changed.')
    if secrets.compare_digest(password.encode(), str(values.get('ADMIN_PASSWORD', '')).encode()):
        raise SystemExit('That is the current password. Nothing was changed.')
    found = weaknesses(password)
    if found:
        print(report(found))
        if confirm('Use it anyway? Type yes to continue: ').strip().lower() != 'yes':
            raise SystemExit('Nothing was changed.')
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
    parser.add_argument('what', choices=['check', 'password', 'session-secret'])
    parser.add_argument('--settings', type=Path, default=SETTINGS, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.what == 'check':
        message, strong = check_password(args.settings)
        print(message)
        raise SystemExit(0 if strong else 1)
    if args.what == 'password':
        print(change_password(args.settings))
    else:
        print(change_session_secret(args.settings))


if __name__ == '__main__':
    main()
