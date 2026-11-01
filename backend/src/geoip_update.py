"""Download DB-IP's free IP-to-location file, used by the admin visitor log.

Run on PythonAnywhere in a Bash console (no reload needed; each download reads the file fresh):

    workon chi-portfolio
    cd ~/chi-portfolio/backend/src
    python geoip_update.py              # city-level file, about 130 MB
    python geoip_update.py --country    # country-only file, about 8 MB

DB-IP publishes a new file each month; run it again whenever you like. The file is the
"IP to City Lite" / "IP to Country Lite" database, licensed CC BY 4.0 (credited on the admin page).
"""
import argparse
from datetime import date
import gzip
import os
import shutil
import sys
from urllib.request import Request, urlopen

from services.visitor_log import GEO_FILE

URL = 'https://download.db-ip.com/free/dbip-{level}-lite-{month}.mmdb.gz'
# DB-IP refuses Python's default "Python-urllib" identity with 403 Forbidden.
AGENT = 'curl/8.5.0 (chi-portfolio geoip_update.py)'


def months(today):
    """This month, then last month, since a new month's file can appear a few days late."""
    previous = date(today.year - (today.month == 1), (today.month - 2) % 12 + 1, 1)
    return [today.strftime('%Y-%m'), previous.strftime('%Y-%m')]


def download(level, target=GEO_FILE, today=None, opener=urlopen):
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(target.name + '.new')
    errors = []
    for month in months(today or date.today()):
        url = URL.format(level=level, month=month)
        try:
            request = Request(url, headers={'User-Agent': AGENT})
            with opener(request, timeout=120) as response, gzip.open(response) as unpacked, \
                    open(partial, 'wb') as out:
                shutil.copyfileobj(unpacked, out)
        except (OSError, EOFError) as error:
            errors.append(f'{url}: {error}')
            partial.unlink(missing_ok=True)
            continue
        os.replace(partial, target)
        return f'Saved {url} to {target} ({target.stat().st_size // 1_000_000} MB).'
    raise RuntimeError('Download failed.\n' + '\n'.join(errors))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--country', action='store_true', help='country-only file (much smaller)')
    args = parser.parse_args(argv)
    try:
        print(download('country' if args.country else 'city'))
    except RuntimeError as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
