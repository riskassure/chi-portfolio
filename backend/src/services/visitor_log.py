"""Turn PythonAnywhere's access logs into a CSV of who visited the site.

PythonAnywhere writes one line per request to /var/log/<domain>.access.log and keeps a
few older copies beside it (.1, then .2.gz, .3.gz, ...). Each line starts with the
visitor's IP address and ends with the browser's User-Agent text. From those we work
out the device type, and, when DB-IP's files are installed, the rough place and who
owns the network (a cloud company's network almost always means a robot).

Chi's own requests are left out: the address of whoever is downloading, any address
that did admin work (sign-in or a saved change) on the same UTC day, and any address
listed in ~/.config/chi-portfolio/visitor-log-ignore-ips.txt.
"""
from bisect import bisect_left
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import gzip
import io
import ipaddress
import os
from pathlib import Path
import re
from urllib.parse import urlsplit

CONFIG = Path.home() / '.config' / 'chi-portfolio'
IGNORE_FILE = CONFIG / 'visitor-log-ignore-ips.txt'
GEO_FILE = CONFIG / 'geoip' / 'dbip-location.mmdb'
ASN_FILE = CONFIG / 'geoip' / 'dbip-asn.mmdb'

# PythonAnywhere's format is nginx "combined" plus extra fields after the user agent.
LINE = re.compile(r'(?P<ip>\S+) \S+ \S+ \[(?P<time>[^\]]+)\] "(?P<request>[^"]*)" '
                  r'(?P<status>\d{3}) \S+ "(?P<referrer>[^"]*)" "(?P<agent>[^"]*)"')
BOT_WORDS = ('bot', 'crawl', 'spider', 'slurp', 'curl', 'wget', 'python', 'go-http',
             'java/', 'okhttp', 'headless', 'scrapy', 'httpclient', 'monitor', 'uptime',
             'preview', 'facebookexternalhit', 'feedfetcher', 'zgrab', 'masscan')
# Words in a network owner's name that mean a data centre rather than a home or phone line.
CLOUD_WORDS = ('amazon', 'aws', 'google', 'microsoft', 'azure', 'digitalocean', 'linode',
               'akamai', 'ovh', 'hetzner', 'vultr', 'choopa', 'contabo', 'oracle', 'alibaba',
               'tencent', 'huawei cloud', 'cloudflare', 'leaseweb', 'scaleway', 'hosting',
               'datacenter', 'data center', 'server', 'colocation', 'm247', 'fastly', 'facebook',
               'meta platforms', 'censys', 'shodan', 'internet measurement')
COLUMNS = ['time_utc', 'local_time', 'weekday', 'hour', 'visitor', 'ip', 'device', 'os', 'browser', 'city', 'region',
           'country', 'network', 'cloud', 'real_browser', 'method', 'page', 'status', 'referrer', 'user_agent']


def log_files(path):
    """The current log first, then the older rotated copies, newest to oldest."""
    path = Path(path)
    older = []
    for candidate in path.parent.glob(path.name + '.*'):
        suffix = candidate.name[len(path.name) + 1:].removesuffix('.gz')
        if suffix.isdigit():
            older.append((int(suffix), candidate))
    return ([path] if path.exists() else []) + [p for _, p in sorted(older)]


def read_lines(paths):
    for path in paths:
        opener = gzip.open if path.name.endswith('.gz') else open
        with opener(path, 'rt', encoding='utf-8', errors='replace') as handle:
            yield from handle


def parse(line):
    match = LINE.match(line)
    if not match:
        return None
    try:
        when = datetime.strptime(match['time'], '%d/%b/%Y:%H:%M:%S %z')
    except ValueError:
        return None
    method, _, rest = match['request'].partition(' ')
    target = rest.rsplit(' ', 1)[0] if ' HTTP/' in rest else rest
    return {'when': when, 'ip': match['ip'], 'method': method, 'page': target,
            'status': int(match['status']), 'referrer': '' if match['referrer'] == '-' else match['referrer'],
            'user_agent': '' if match['agent'] == '-' else match['agent']}


def device(agent):
    """(device, os, browser) guessed from the User-Agent text the browser sends."""
    text = agent.lower()
    if not text or any(word in text for word in BOT_WORDS):
        return 'bot', '', ''
    if 'ipad' in text or 'tablet' in text or ('android' in text and 'mobile' not in text):
        kind = 'tablet'
    elif 'iphone' in text or 'mobile' in text or 'windows phone' in text:
        kind = 'phone'
    elif any(word in text for word in ('windows nt', 'macintosh', 'cros', 'x11', 'linux')):
        kind = 'computer'
    else:
        kind = 'unknown'
    for word, name in (('windows phone', 'Windows Phone'), ('windows', 'Windows'),
                       ('iphone', 'iOS'), ('ipad', 'iPadOS'), ('android', 'Android'),
                       ('cros', 'ChromeOS'), ('mac os x', 'macOS'), ('linux', 'Linux')):
        if word in text:
            system = name
            break
    else:
        system = ''
    # Order matters: Edge and Opera also say Chrome, and Chrome also says Safari.
    for word, name in (('edg/', 'Edge'), ('opr/', 'Opera'), ('samsungbrowser', 'Samsung Internet'),
                       ('firefox', 'Firefox'), ('fxios', 'Firefox'), ('crios', 'Chrome'),
                       ('chrome', 'Chrome'), ('safari', 'Safari')):
        if word in text:
            return kind, system, name
    return kind, system, ''


def is_admin_work(row):
    """A successful sign-in or saved change; only someone signed in as admin can do these."""
    path = urlsplit(row['page']).path
    if row['status'] >= 400 or not path.startswith('/api/'):
        return False
    return path.startswith('/api/admin/') or row['method'] not in {'GET', 'HEAD', 'OPTIONS'}


def is_page_view(row):
    """A page someone opened, rather than the pictures, scripts and data it loads."""
    path = urlsplit(row['page']).path
    if row['method'] != 'GET' or row['status'] >= 400 or path.startswith(('/api/', '/auth/')):
        return False
    last = path.rsplit('/', 1)[-1]
    return last == '' or last.endswith('.html') or '.' not in last


def ignored_addresses(path=IGNORE_FILE):
    try:
        lines = Path(path).read_text(encoding='utf-8-sig').splitlines()
    except OSError:
        return set()
    found = set()
    for line in lines:
        text = line.split('#', 1)[0].strip()
        try:
            found.add(str(ipaddress.ip_address(text)))
        except ValueError:
            pass
    return found


def open_reader(path):
    try:
        import maxminddb
        return maxminddb.open_database(str(path))
    except (ImportError, OSError, ValueError):
        return None


def is_cloud(network):
    text = network.lower()
    # Google Fiber is a home internet provider, unlike the rest of Google's networks.
    if 'fiber' in text:
        return False
    return any(word in text for word in CLOUD_WORDS)


def open_locator(path=None, asn_path=None):
    """Look up (city, region, country, network) in the DB-IP files; None when neither is installed."""
    places, owners = open_reader(path or GEO_FILE), open_reader(asn_path or ASN_FILE)
    if not places and not owners:
        return None

    def find(reader, ip):
        try:
            return (reader.get(ip) if reader else None) or {}
        except ValueError:
            return {}

    def locate(ip):
        found = find(places, ip)
        name = lambda part: (part or {}).get('names', {}).get('en', '')
        regions = found.get('subdivisions') or [{}]
        owner = find(owners, ip).get('autonomous_system_organization', '')
        return name(found.get('city')), name(regions[0]), name(found.get('country')), owner
    return locate


# Excel and other spreadsheets treat a cell starting with one of these as a formula. The
# referrer, User-Agent, page and method come straight from visitors, so a crafted value such
# as "=HYPERLINK(...)" could run when the file is opened.
FORMULA_STARTS = ('=', '+', '-', '@', '\t', '\r')


def safe_cell(value):
    """Text that a spreadsheet shows as typed: a leading ' stops it being read as a formula."""
    if isinstance(value, str) and value.startswith(FORMULA_STARTS):
        return "'" + value
    return value


# A real browser opening a page fetches its style sheets and scripts, and the page asks the
# server for data (every page checks /api/session-check). Most robots read only the page.
FOLLOW_UP_SECONDS = 60


def follow_up_times(rows):
    """Times of the non-page requests each (address, browser) made, sorted, for real_browser."""
    times = defaultdict(list)
    for row in rows:
        if row['method'] in {'GET', 'HEAD'} and row['status'] < 400 and not is_page_view(row):
            times[(row['ip'], row['user_agent'])].append(row['when'].timestamp())
    return times


def loaded_page_parts(row, times):
    later = times.get((row['ip'], row['user_agent']), [])
    start = row['when'].timestamp()
    i = bisect_left(later, start)
    return i < len(later) and later[i] <= start + FOLLOW_UP_SECONDS


def build_rows(lines, my_address='', ignore=(), locate=None, pages_only=True, zone=timezone.utc,
               start=None, end=None):
    """Rows of COLUMNS values (raw, not spreadsheet-safe), plus counts of what was kept and left out.

    Local columns use zone. With start/end (aware datetimes), only requests in [start, end)
    become rows; requests outside still count for spotting admin days and real browsers.
    """
    rows = [row for row in map(parse, lines) if row]
    rows.sort(key=lambda row: row['when'])
    day = lambda row: row['when'].astimezone(timezone.utc).date()
    mine = {(row['ip'], day(row)) for row in rows if is_admin_work(row)}
    follow_ups = follow_up_times(rows)
    always = set(ignore) | ({my_address} if my_address else set())
    counts = Counter()
    places, visitors, found = {}, {}, []
    for row in rows:
        if (start and row['when'] < start) or (end and row['when'] >= end):
            continue
        kind, system, browser = device(row['user_agent'])
        if row['ip'] in always or (row['ip'], day(row)) in mine:
            counts['you'] += 1
            continue
        if kind == 'bot':
            counts['bots'] += 1
            continue
        if pages_only and not is_page_view(row):
            counts['other requests'] += 1
            continue
        counts['kept'] += 1
        # One "visitor" is one address with one browser; numbered in order of first visit.
        visitor = visitors.setdefault((row['ip'], row['user_agent']), len(visitors) + 1)
        if locate and row['ip'] not in places:
            places[row['ip']] = locate(row['ip'])
        city, region, country, network = places.get(row['ip'], ('', '', '', ''))
        if is_page_view(row):
            real = 'yes' if loaded_page_parts(row, follow_ups) else 'no'
        else:
            real = ''
        utc, local = row['when'].astimezone(timezone.utc), row['when'].astimezone(zone)
        found.append([utc.strftime('%Y-%m-%d %H:%M:%S'), local.strftime('%Y-%m-%d %H:%M:%S'),
                      local.strftime('%A'), local.hour, f'V{visitor}', row['ip'],
                      kind, system, browser, city, region, country, network,
                      'yes' if is_cloud(network) else '', real, row['method'],
                      row['page'], row['status'], row['referrer'], row['user_agent']])
    return found, counts


def build_csv(lines, my_address='', ignore=(), locate=None, pages_only=True, zone=timezone.utc):
    """CSV text, plus counts of what was kept and left out; local columns use zone."""
    found, counts = build_rows(lines, my_address, ignore, locate, pages_only, zone)
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(COLUMNS)
    for values in found:
        writer.writerow(map(safe_cell, values))
    return out.getvalue(), counts


def default_log_path():
    if os.environ.get('VISITOR_LOG_PATH'):
        return Path(os.environ['VISITOR_LOG_PATH'])
    host = urlsplit(os.environ.get('PUBLIC_ORIGIN', '')).hostname
    return Path('/var/log') / f'{host}.access.log' if host else None
