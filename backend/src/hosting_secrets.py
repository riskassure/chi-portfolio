"""Change the live site's admin password or session secret; never prints them.

Run on PythonAnywhere in a Bash console, then reload the web app from the Web tab:

    workon chi-portfolio
    cd ~/chi-portfolio/backend/src
    python hosting_secrets.py check            # is the current admin password weak?
    python hosting_secrets.py password         # choose a new admin password
    python hosting_secrets.py session-secret   # new session secret: signs everyone out

password and session-secret rewrite ~/.config/chi-portfolio/hosting.json in place, keeping its other
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
# zxcvbn's estimate of the guesses needed; 10**15 is beyond any online guessing.
GOOD_GUESSES_LOG10 = 15
# Words tied to this site and its owner, which a guesser would try early.
SITE_WORDS = ['cwoo', 'woo', 'chi', 'portfolio', 'admin', 'pythonanywhere', 'math']


def weaknesses(password):
    """Plain-language reasons a password is easier to guess than a random one.

    Uses zxcvbn, which estimates how many guesses an attacker would need from
    common passwords, words, names, keyboard patterns, dates and repeats. It can't
    see whether a password is reused elsewhere, so a password manager's generator
    is still the dependable source.
    """
    try:
        from zxcvbn import zxcvbn
    except ImportError:
        raise SystemExit('The zxcvbn package is missing. Run this with the site\'s virtualenv '
                         '(workon chi-portfolio), or pip install -r backend/requirements.txt there.')
    result = zxcvbn(password, user_inputs=SITE_WORDS)
    if result['guesses_log10'] >= GOOD_GUESSES_LOG10:
        return []
    feedback = result['feedback']
    found = [f'It could be guessed in about 10^{int(result["guesses_log10"])} tries '
             f'(aim for at least 10^{GOOD_GUESSES_LOG10})']
    if feedback['warning']:
        found.append(feedback['warning'].rstrip('.'))
    found.extend(suggestion.rstrip('.') for suggestion in feedback['suggestions'])
    return found


def report(found):
    if not found:
        return 'No common weaknesses found.'
    return 'Weak:\n' + ''.join(f'  - {line}\n' for line in found)


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
    advice = ('Consider a new one from a password manager: python hosting_secrets.py password'
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
