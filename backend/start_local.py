"""Start a local preview with a saved, Windows-encrypted admin password."""
import argparse
import os
from pathlib import Path
import secrets
import sys
from local_admin_password import get_password


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=5001)
    parser.add_argument('--database', type=Path, help='Use a separate working database for local testing.')
    passwords = parser.add_mutually_exclusive_group()
    passwords.add_argument('--reset-password', action='store_true', help='Choose and save a replacement local password.')
    passwords.add_argument('--session-password', action='store_true', help='Choose a temporary password without changing the saved one.')
    args = parser.parse_args()
    if args.database:
        database = args.database.resolve()
        if not database.is_file():
            raise SystemExit(f'Database not found: {database}')
        os.environ['PORTFOLIO_DB_PATH'] = str(database)
        print(f'Local working database: {database}', flush=True)
    try:
        password = get_password(reset=args.reset_password, session=args.session_password)
    except (ValueError, OSError) as error:
        raise SystemExit(str(error))
    os.environ['FLASK_ENV'] = 'development'
    os.environ['ADMIN_PASSWORD'] = password
    os.environ['FLASK_SECRET_KEY'] = secrets.token_urlsafe(48)
    sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))
    import app as gateway
    # Include the selected loopback origin without weakening production checks.
    gateway.LOCAL_ORIGINS.add(f'http://127.0.0.1:{args.port}')
    print(f'Open http://127.0.0.1:{args.port}/admin_dashboard.html')
    print('Use your local admin password. Keep this terminal open; Ctrl+C stops it.')
    gateway.app.run(host='127.0.0.1', port=args.port, debug=False, use_reloader=False)


if __name__ == '__main__':
    main()
