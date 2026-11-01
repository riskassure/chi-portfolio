import csv
from datetime import date
import gzip
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SRC = Path(__file__).resolve().parents[1] / 'src'
sys.path.insert(0, str(SRC))
import app as gateway
import geoip_update
from services import visitor_log

PHONE = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1'
PC = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0 Safari/537.36 Edg/141.0'
MAC = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15'
TABLET = 'Mozilla/5.0 (Linux; Android 14; SM-X710) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0 Safari/537.36'
BOT = 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'


def line(ip, when, request, status=200, agent=PC, referrer='-'):
    return (f'{ip} - - [{when} +0000] "{request} HTTP/1.1" {status} 512 "{referrer}" "{agent}" '
            f'"{ip}" response-time=0.010\n')


def rows(text):
    return list(csv.DictReader(io.StringIO(text)))


class DeviceTests(unittest.TestCase):
    def test_device_os_and_browser(self):
        self.assertEqual(visitor_log.device(PHONE), ('phone', 'iOS', 'Safari'))
        self.assertEqual(visitor_log.device(PC), ('computer', 'Windows', 'Edge'))
        self.assertEqual(visitor_log.device(MAC), ('computer', 'macOS', 'Safari'))
        self.assertEqual(visitor_log.device(TABLET), ('tablet', 'Android', 'Chrome'))
        self.assertEqual(visitor_log.device(BOT)[0], 'bot')
        self.assertEqual(visitor_log.device('')[0], 'bot')
        self.assertEqual(visitor_log.device('python-requests/2.32')[0], 'bot')


class BuildCsvTests(unittest.TestCase):
    def test_leaves_out_admin_days_my_address_ignored_ips_bots_and_assets(self):
        lines = [
            line('8.8.8.8', '30/Oct/2026:01:00:00', 'GET /math/concept.html?slug=group', agent=PHONE,
                 referrer='https://www.google.com/'),
            line('8.8.8.8', '30/Oct/2026:01:00:01', 'GET /style.css', agent=PHONE),
            line('8.8.8.8', '30/Oct/2026:01:00:02', 'GET /api/math/concepts', agent=PHONE),
            # Chi signs in from 9.9.9.9: that address is theirs for the whole UTC day.
            line('9.9.9.9', '30/Oct/2026:00:30:00', 'GET /index.html'),
            line('9.9.9.9', '30/Oct/2026:02:00:00', 'POST /api/login'),
            line('9.9.9.9', '31/Oct/2026:02:00:00', 'GET /music/'),
            # A failed sign-in is not proof it was Chi.
            line('4.4.4.4', '30/Oct/2026:03:00:00', 'POST /api/login', status=401),
            line('4.4.4.4', '30/Oct/2026:03:00:01', 'GET /admin_dashboard.html'),
            line('5.5.5.5', '30/Oct/2026:04:00:00', 'GET /'),
            line('6.6.6.6', '30/Oct/2026:04:00:00', 'GET /travel/'),
            line('66.249.66.1', '30/Oct/2026:05:00:00', 'GET /', agent=BOT),
            line('1.1.1.1', '30/Oct/2026:05:00:00', 'GET /missing.html', status=404),
            'garbage line\n',
        ]
        text, counts = visitor_log.build_csv(
            lines, my_address='5.5.5.5', ignore={'6.6.6.6'},
            locate=lambda ip: ('Mountain View', 'California', 'United States'))
        found = rows(text)
        self.assertEqual(list(found[0]), visitor_log.COLUMNS)
        self.assertEqual([(r['ip'], r['page']) for r in found], [
            ('8.8.8.8', '/math/concept.html?slug=group'), ('4.4.4.4', '/admin_dashboard.html'),
            ('9.9.9.9', '/music/')])
        first = found[0]
        self.assertEqual((first['time_utc'], first['visitor'], first['device'], first['os']),
                         ('2026-10-30 01:00:00', 'V1', 'phone', 'iOS'))
        self.assertEqual((first['city'], first['country'], first['referrer']),
                         ('Mountain View', 'United States', 'https://www.google.com/'))
        self.assertEqual(counts['you'], 4)
        self.assertEqual(counts['bots'], 1)
        self.assertEqual(counts['kept'], 3)

    def test_every_request_mode_keeps_assets_but_still_drops_me_and_bots(self):
        lines = [line('8.8.8.8', '30/Oct/2026:01:00:00', 'GET /'),
                 line('8.8.8.8', '30/Oct/2026:01:00:01', 'GET /style.css'),
                 line('66.249.66.1', '30/Oct/2026:01:00:02', 'GET /', agent=BOT),
                 line('9.9.9.9', '30/Oct/2026:01:00:03', 'GET /api/admin/math/types')]
        text, counts = visitor_log.build_csv(lines, pages_only=False)
        self.assertEqual([r['page'] for r in rows(text)], ['/', '/style.css'])
        self.assertEqual(rows(text)[0]['city'], '')

    def test_ignore_file_skips_comments_and_bad_lines(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'ips.txt'
            path.write_text('8.8.8.8  # home\nnot-an-ip\n\n2001:4860::8888\n', encoding='utf-8')
            self.assertEqual(visitor_log.ignored_addresses(path), {'8.8.8.8', '2001:4860::8888'})
            self.assertEqual(visitor_log.ignored_addresses(Path(folder) / 'missing.txt'), set())

    def test_no_location_file_means_no_locator(self):
        self.assertIsNone(visitor_log.open_locator(Path(tempfile.gettempdir()) / 'no-such.mmdb'))


class LogFileTests(unittest.TestCase):
    def test_reads_current_and_rotated_logs(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder) / 'www.example.com.access.log'
            base.write_text(line('8.8.8.8', '30/Oct/2026:01:00:00', 'GET /'))
            Path(f'{base}.1').write_text(line('8.8.8.8', '29/Oct/2026:01:00:00', 'GET /a.html'))
            with gzip.open(f'{base}.2.gz', 'wt') as handle:
                handle.write(line('8.8.8.8', '28/Oct/2026:01:00:00', 'GET /b.html'))
            Path(f'{base}.old').write_text('ignored')
            Path(folder, 'www.example.com.error.log').write_text('ignored')
            files = visitor_log.log_files(base)
            self.assertEqual([p.name for p in files], [base.name, base.name + '.1', base.name + '.2.gz'])
            text, _ = visitor_log.build_csv(visitor_log.read_lines(files))
            self.assertEqual([r['page'] for r in rows(text)], ['/b.html', '/a.html', '/'])

    def test_default_path_follows_public_origin(self):
        with patch.dict(os.environ, {'PUBLIC_ORIGIN': 'https://www.example.com', 'VISITOR_LOG_PATH': ''}):
            self.assertEqual(visitor_log.default_log_path(), Path('/var/log/www.example.com.access.log'))


class RouteTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.log = Path(folder.name) / 'site.access.log'
        self.log.write_text(line('8.8.8.8', '30/Oct/2026:01:00:00', 'GET /', agent=PHONE)
                            + line('8.8.8.8', '30/Oct/2026:01:00:01', 'GET /style.css', agent=PHONE))
        for patcher in (patch.dict(os.environ, {'VISITOR_LOG_PATH': str(self.log)}),
                        patch.object(visitor_log, 'IGNORE_FILE', Path(folder.name) / 'none.txt'),
                        patch.object(visitor_log, 'GEO_FILE', Path(folder.name) / 'none.mmdb')):
            patcher.start()
            self.addCleanup(patcher.stop)
        self.client = gateway.app.test_client()

    def test_requires_admin(self):
        self.assertEqual(self.client.get('/api/admin/visitor-log.csv').status_code, 403)

    def test_admin_downloads_csv(self):
        with self.client.session_transaction() as session:
            session['is_admin'] = True
        response = self.client.get('/api/admin/visitor-log.csv')
        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment; filename="visitors-pages-', response.headers['Content-Disposition'])
        self.assertEqual([r['device'] for r in rows(response.get_data(as_text=True))], ['phone'])
        everything = self.client.get('/api/admin/visitor-log.csv?all=1')
        self.assertEqual(len(rows(everything.get_data(as_text=True))), 2)
        self.log.unlink()
        self.assertEqual(self.client.get('/api/admin/visitor-log.csv').status_code, 404)


class GeoDownloadTests(unittest.TestCase):
    def test_months_wrap_the_year(self):
        self.assertEqual(geoip_update.months(date(2027, 1, 2)), ['2027-01', '2026-12'])

    def test_falls_back_to_last_month_and_replaces_file(self):
        asked = []

        def opener(url, timeout):
            asked.append(url)
            if '2026-11' in url:
                raise OSError('404 Not Found')
            return io.BytesIO(gzip.compress(b'mmdb-bytes'))
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'geo' / 'dbip-location.mmdb'
            message = geoip_update.download('city', target, date(2026, 11, 1), opener)
            self.assertEqual(target.read_bytes(), b'mmdb-bytes')
            self.assertIn('dbip-city-lite-2026-10', message)
            self.assertEqual(len(asked), 2)
            self.assertFalse(target.with_name(target.name + '.new').exists())


if __name__ == '__main__':
    unittest.main()
