"""Run on the host to create private configuration; never prints credentials."""
import getpass
import json
import os
from pathlib import Path
import secrets

if __name__ == '__main__':
    username = getpass.getuser()
    directory = Path.home() / '.config' / 'chi-portfolio'
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    target = directory / 'hosting.json'
    if target.exists():
        raise SystemExit('Configuration already exists. It has not been changed.')
    password = getpass.getpass('Choose a NEW portfolio admin password (16+ characters): ')
    if len(password) < 16:
        raise SystemExit('Password must contain at least 16 characters.')
    if password != getpass.getpass('Confirm portfolio admin password: '):
        raise SystemExit('Passwords do not match. No configuration saved.')
    values = dict(PUBLIC_ORIGIN=f'https://{username}.pythonanywhere.com',
                  FLASK_SECRET_KEY=secrets.token_urlsafe(48), ADMIN_PASSWORD=password)
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as stream:
        json.dump(values, stream)
    print('Private configuration created for ' + values['PUBLIC_ORIGIN'])
