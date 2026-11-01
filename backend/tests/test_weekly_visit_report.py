from contextlib import closing
from datetime import date, datetime, timezone
import gzip
import io
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from zoneinfo import ZoneInfo

SRC = Path(__file__).resolve().parents[1] / 'src'
sys.path.insert(0, str(SRC))
from database import nightly_backup
import hosting_secrets
from services import access_log_archive as archive
import weekly_visit_report as weekly

PHONE = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1'
PC = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0 Safari/537.36'
LA = ZoneInfo('America/Los_Angeles')


def line(ip, when, request, status=200, agent=PC, referrer='-'):
    return (f'{ip} - - [{when} +0000] "{request} HTTP/1.1" {status} 512 "{referrer}" "{agent}" '
            f'"{ip}" response-time=0.010\n')


def visit(ip, when, page='/', agent=PC, referrer='-'):
    """A page view by a real browser: the page, then its data a second later."""
    hh, mm, ss = when[-8:].split(':')
    return [line(ip, when, f'GET {page}', agent=agent, referrer=referrer),
            line(ip, f'{when[:-8]}{hh}:{mm}:{int(ss) + 1:02d}', 'GET /api/session-check', agent=agent)]


class Folder(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.logs = self.root / 'var-log'
        self.logs.mkdir()
        self.log = self.logs / 'www.cwoo.me.access.log'
        self.saved = self.root / 'backups' / 'access-logs'

    def write(self, name, lines, packed=False):
        data = ''.join(lines).encode()
        path = self.logs / name
        path.write_bytes(gzip.compress(data) if packed else data)
        return path


class ArchiveTests(Folder):
    def test_saves_rotated_copies_once_even_after_they_are_renamed(self):
        day1 = [line('8.8.8.8', '25/Oct/2026:10:17:00', 'GET /'), line('8.8.8.8', '26/Oct/2026:10:16:59', 'GET /a')]
        day2 = [line('7.7.7.7', '26/Oct/2026:10:17:00', 'GET /b')]
        self.write('www.cwoo.me.access.log', [line('1.1.1.1', '27/Oct/2026:01:00:00', 'GET /now')])
        self.write('www.cwoo.me.access.log.1', day1)
        report = archive.save_rotated(self.log, self.saved)
        self.assertEqual(len(report['saved']), 1)
        name = report['saved'][0]
        self.assertTrue(name.startswith('www.cwoo.me.access-20261025T101700Z-20261026T101659Z-'), name)
        self.assertEqual(gzip.decompress((self.saved / name).read_bytes()), ''.join(day1).encode())
        # The next rotation: .1 becomes .2.gz with the same text, a new .1 appears.
        (self.logs / 'www.cwoo.me.access.log.1').unlink()
        self.write('www.cwoo.me.access.log.2.gz', day1, packed=True)
        self.write('www.cwoo.me.access.log.1', day2)
        report = archive.save_rotated(self.log, self.saved)
        self.assertEqual((len(report['saved']), report['already_saved']), (1, 1))
        self.assertEqual(len(archive.archived(self.saved)), 2)
        # The current log is never saved; nothing temporary is left behind.
        self.assertEqual(len(list(self.saved.iterdir())), 2)

    def test_a_longer_copy_of_the_same_log_replaces_the_shorter(self):
        start = [line('8.8.8.8', '25/Oct/2026:10:17:00', 'GET /')]
        more = start + [line('8.8.8.8', '25/Oct/2026:10:17:05', 'GET /late')]
        self.write('www.cwoo.me.access.log.1', start)
        archive.save_rotated(self.log, self.saved)
        self.write('www.cwoo.me.access.log.1', more)
        report = archive.save_rotated(self.log, self.saved)
        self.assertEqual(len(report['replaced']), 1)
        [kept] = archive.archived(self.saved)
        self.assertEqual(gzip.decompress(kept['path'].read_bytes()), ''.join(more).encode())
        # The shorter one coming back later is not saved again.
        self.write('www.cwoo.me.access.log.1', start)
        self.assertEqual(archive.save_rotated(self.log, self.saved)['already_saved'], 1)

    def test_lines_between_reads_overlapping_saved_logs_then_the_current_log(self):
        self.write('www.cwoo.me.access.log.2.gz', [line('1.1.1.1', '01/Oct/2026:00:00:00', 'GET /old')], packed=True)
        self.write('www.cwoo.me.access.log.1', [line('2.2.2.2', '26/Oct/2026:12:00:00', 'GET /week')])
        self.write('www.cwoo.me.access.log', [line('3.3.3.3', '27/Oct/2026:12:00:00', 'GET /now')])
        archive.save_rotated(self.log, self.saved)
        start = datetime(2026, 10, 26, tzinfo=timezone.utc)
        found = list(archive.lines_between(self.log, self.saved, start, datetime(2026, 11, 2, tzinfo=timezone.utc)))
        self.assertEqual([text.split()[0] for text in found], ['2.2.2.2', '3.3.3.3'])

    def test_nightly_backup_also_saves_the_logs(self):
        db = self.root / 'portfolio.db'
        with closing(sqlite3.connect(db)) as connection:
            connection.execute('CREATE TABLE math_concepts(id INTEGER PRIMARY KEY)')
            connection.commit()
        self.write('www.cwoo.me.access.log.1', [line('8.8.8.8', '25/Oct/2026:10:17:00', 'GET /')])
        out = io.StringIO()
        with redirect_stdout(out):
            code = nightly_backup.main(['backup', '--database', str(db), '--backups', str(self.root / 'nightly'),
                                        '--access-log', str(self.log), '--log-archive', str(self.saved)])
        self.assertEqual(code, 0)
        report = json.loads(out.getvalue())
        self.assertEqual((report['status'], report['access_logs']['status']), ('ok', 'ok'))
        self.assertEqual(len(report['access_logs']['saved']), 1)

    def test_a_log_problem_does_not_stop_the_database_backup(self):
        db = self.root / 'portfolio.db'
        with closing(sqlite3.connect(db)) as connection:
            connection.execute('CREATE TABLE math_concepts(id INTEGER PRIMARY KEY)')
            connection.commit()
        blocker = self.root / 'not-a-folder'
        blocker.write_text('x')
        self.write('www.cwoo.me.access.log.1', [line('8.8.8.8', '25/Oct/2026:10:17:00', 'GET /')])
        out = io.StringIO()
        with redirect_stdout(out):
            code = nightly_backup.main(['backup', '--database', str(db), '--backups', str(self.root / 'nightly'),
                                        '--access-log', str(self.log), '--log-archive', str(blocker / 'logs')])
        self.assertEqual(code, 1)
        report = json.loads(out.getvalue())
        self.assertEqual((report['status'], report['access_logs']['status']), ('ok', 'failed'))
        self.assertEqual(len(list((self.root / 'nightly').glob('*.db.gz'))), 1)


class FakeSmtp:
    sent, fail = [], False

    def __init__(self, host, port, timeout):
        self.host = (host, port)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def starttls(self, context):
        pass

    def login(self, user, password):
        self.user = (user, password)

    def send_message(self, message):
        if FakeSmtp.fail:
            raise OSError('network down')
        FakeSmtp.sent.append(message)


class ReportTests(Folder):
    def setUp(self):
        super().setUp()
        # Week of Monday 26 Oct 2026 (Pacific daylight time, UTC-7).
        lines = []
        lines += visit('8.8.8.8', '26/Oct/2026:17:00:00', '/math/concept.html?slug=group', agent=PHONE,
                       referrer='https://www.google.com/search')
        lines += visit('8.8.8.8', '27/Oct/2026:17:00:00', '/music/', agent=PHONE)
        # One page, no referrer: likely a robot even though it loaded the parts.
        lines += visit('5.5.5.5', '28/Oct/2026:18:00:00', '/')
        # Visitor text that would be a formula, on a page that robots skip.
        lines.append(line('6.6.6.6', '29/Oct/2026:18:00:00', 'GET /', referrer='=HYPERLINK(x)'))
        # Before the week starts in Pacific time (Monday 00:00 PDT is 07:00 UTC).
        lines += visit('4.4.4.4', '26/Oct/2026:06:59:00', '/travel/')
        # Chi's admin work leaves that address out for the day.
        lines += visit('9.9.9.9', '30/Oct/2026:20:00:00', '/photos/')
        lines.append(line('9.9.9.9', '30/Oct/2026:20:05:00', 'POST /api/login'))
        self.write('www.cwoo.me.access.log.1', lines[:6])
        self.write('www.cwoo.me.access.log', lines[6:])
        self.monday = date(2026, 10, 26)

    def test_week_and_last_full_week(self):
        start, end = weekly.week_bounds(self.monday, LA)
        self.assertEqual(start.astimezone(timezone.utc), datetime(2026, 10, 26, 7, tzinfo=timezone.utc))
        # Sunday 1 Nov is the day clocks fall back, so the week ends at 00:00 PST = 08:00 UTC.
        self.assertEqual(end.astimezone(timezone.utc), datetime(2026, 11, 2, 8, tzinfo=timezone.utc))
        self.assertEqual(weekly.last_full_week(date(2026, 11, 2)), self.monday)   # a Monday
        self.assertEqual(weekly.last_full_week(date(2026, 11, 8)), self.monday)   # the Sunday after
        self.assertEqual(weekly.last_full_week(date(2026, 11, 9)), date(2026, 11, 2))

    def test_workbook_counts_real_visitors_and_keeps_the_robot_formula(self):
        from openpyxl import load_workbook
        out = self.root / 'report.xlsx'
        summary = weekly.make_report(self.monday, out, self.log, self.saved, 'America/Los_Angeles')
        self.assertEqual((summary['page_views'], summary['real_visits'], summary['real_visitors']), (4, 2, 1))
        self.assertEqual((summary['likely_bot'], summary['not_real_browser'], summary['cloud']), (1, 1, 0))
        self.assertEqual(summary['devices'], [('phone', 2, 1)])
        self.assertEqual(summary['pages'][0][0], '/math/concept.html (group)')
        self.assertIn(('google.com', 1, 1), summary['sources'])
        self.assertEqual(summary['days'][0][1:], (1, 1))
        book = load_workbook(out)
        self.assertEqual(book.sheetnames, ['Summary', 'Places', 'Devices', 'Times', 'Pages', 'All visits'])
        raw = book['All visits']
        self.assertEqual([c.value for c in raw[1]][-2:], ['likely_bot', 'counted'])
        self.assertEqual(raw['U2'].value, '=AND(COUNTIF(E:E,E2)=1,S2="")')
        self.assertEqual(raw['V2'].value, '=AND(N2="",O2="yes",NOT(U2))')
        self.assertEqual(raw.auto_filter.ref, 'A1:V5')
        referrers = [raw.cell(r, 19) for r in range(2, 6)]
        evil = [c for c in referrers if c.value and c.value.startswith('=')]
        self.assertEqual(len(evil), 1)
        self.assertEqual(evil[0].data_type, 's')   # plain text, never run as a formula
        # Nothing from before the week or from Chi's admin day.
        self.assertNotIn('4.4.4.4', [raw.cell(r, 6).value for r in range(2, 6)])
        self.assertNotIn('9.9.9.9', [raw.cell(r, 6).value for r in range(2, 6)])

    def settings(self, **values):
        path = self.root / 'hosting.json'
        path.write_text(json.dumps(dict(REPORT_EMAIL_FROM='me@gmail.com', REPORT_EMAIL_TO='me@gmail.com',
                                        REPORT_EMAIL_PASSWORD='abcdefghijklmnop', **values)))
        return path

    def test_send_emails_each_week_once(self):
        FakeSmtp.sent, FakeSmtp.fail = [], False
        reports = self.root / 'reports'
        args = dict(log=self.log, archive=self.saved, reports=reports, zone_name='America/Los_Angeles',
                    settings_path=self.settings(), today=date(2026, 11, 2), smtp=FakeSmtp)
        message = weekly.send_weekly(**args)
        self.assertIn('Sent', message)
        [email] = FakeSmtp.sent
        self.assertIn('2 real visits from 1 visitors', email['Subject'])
        [attachment] = list(email.iter_attachments())
        self.assertEqual(attachment.get_filename(), 'visits-2026-10-26-to-2026-11-01.xlsx')
        self.assertIn('Top countries', email.get_body().get_content())
        self.assertEqual([p.name for p in reports.iterdir()], ['visits-2026-10-26-to-2026-11-01.xlsx'])
        self.assertIn('Already sent', weekly.send_weekly(**dict(args, today=date(2026, 11, 3))))
        self.assertEqual(len(FakeSmtp.sent), 1)

    def test_a_failed_send_keeps_no_copy_so_the_next_day_tries_again(self):
        FakeSmtp.sent, FakeSmtp.fail = [], True
        reports = self.root / 'reports'
        with self.assertRaises(OSError):
            weekly.send_weekly(self.log, self.saved, reports, 'America/Los_Angeles',
                               settings_path=self.settings(), today=date(2026, 11, 2), smtp=FakeSmtp)
        self.assertEqual(list(reports.iterdir()), [])
        FakeSmtp.fail = False

    def test_missing_email_settings_say_how_to_fix(self):
        path = self.root / 'hosting.json'
        path.write_text('{}')
        with self.assertRaises(SystemExit) as stop:
            weekly.email_settings(path)
        self.assertIn('hosting_secrets.py email', str(stop.exception))


class EmailSettingsTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name) / 'hosting.json'
        self.path.write_text(json.dumps({'ADMIN_PASSWORD': 'keep'}))

    def answers(self, *replies):
        replies = iter(replies)
        return lambda prompt: next(replies)

    def test_saves_address_recipient_and_app_password_without_spaces(self):
        message = hosting_secrets.change_email(self.path, ask=self.answers('abcd efgh ijkl mnop'),
                                               answer=self.answers('me@gmail.com', ''))
        self.assertNotIn('abcd', message)
        self.assertEqual(json.loads(self.path.read_text()), dict(
            ADMIN_PASSWORD='keep', REPORT_EMAIL_FROM='me@gmail.com', REPORT_EMAIL_TO='me@gmail.com',
            REPORT_EMAIL_PASSWORD='abcdefghijklmnop'))
        if os.name == 'posix':
            self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)

    def test_refuses_something_that_is_not_an_app_password(self):
        with self.assertRaises(SystemExit):
            hosting_secrets.change_email(self.path, ask=self.answers('hunter2'),
                                         answer=self.answers('me@gmail.com', ''))
        self.assertEqual(json.loads(self.path.read_text()), {'ADMIN_PASSWORD': 'keep'})


if __name__ == '__main__':
    unittest.main()
