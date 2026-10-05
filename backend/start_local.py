"""Start a local preview with a privately chosen, session-only admin password."""
import argparse
import getpass
import os
from pathlib import Path
import secrets
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=5001)
    args = parser.parse_args()
    password = getpass.getpass('Choose a password for this local session (16+ characters): ')
    if len(password) < 16:
        raise SystemExit('Please choose at least 16 characters and run again.')
    if password != getpass.getpass('Confirm local password: '):
        raise SystemExit('Passwords did not match. No server started.')
    os.environ['FLASK_ENV'] = 'development'
    os.environ['ADMIN_PASSWORD'] = password
    os.environ['FLASK_SECRET_KEY'] = secrets.token_urlsafe(48)
    sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))
    import app as gateway
    # Include the selected loopback origin without weakening production checks.
    gateway.LOCAL_ORIGINS.add(f'http://127.0.0.1:{args.port}')
    print(f'Open http://127.0.0.1:{args.port}/admin_dashboard.html')
    print('Use the password you just chose. Keep this terminal open; Ctrl+C stops it.')
    gateway.app.run(host='127.0.0.1', port=args.port, debug=False, use_reloader=False)


if __name__ == '__main__':
    main()
