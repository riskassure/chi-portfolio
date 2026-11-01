"""Build last week's site visit report as an Excel file and email it to Chi.

Run on PythonAnywhere (a daily scheduled task runs `send`; see
docs/administration/WEEKLY_VISIT_REPORT.md):

    workon chi-portfolio
    cd ~/chi-portfolio/backend/src
    python weekly_visit_report.py test-email          # check the email settings
    python weekly_visit_report.py send                # email last week's report, if not sent yet
    python weekly_visit_report.py build --out ~/report.xlsx [--week-of 2026-10-26]   # file only

A week runs Monday 00:00 to Sunday 23:59 in Chi's time zone (Pacific). `send` first saves any
rotated access logs into the log archive, so it reads the same history the nightly backup
keeps, plus the current log. A copy of each sent report stays in the reports folder; that copy
is also how `send` knows a week was already emailed, so running it every day sends each week
once (on Monday, or the first day after that it succeeds).

Email goes through Gmail with an app password stored by `python hosting_secrets.py email`
in ~/.config/chi-portfolio/hosting.json. Nothing here changes the site.
"""
import argparse
from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta
from email.message import EmailMessage
import json
import os
from pathlib import Path
import smtplib
import ssl
import sys
from urllib.parse import parse_qs, urlsplit
import uuid
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from services import access_log_archive, visitor_log  # noqa: E402

HOME = Path.home()
SETTINGS = HOME / '.config' / 'chi-portfolio' / 'hosting.json'
LOG = Path('/var/log/www.cwoo.me.access.log')
ARCHIVE = HOME / 'backups' / 'access-logs'
REPORTS = HOME / 'backups' / 'weekly-reports'
ZONE = 'America/Los_Angeles'
SMTP_HOST, SMTP_PORT = 'smtp.gmail.com', 587
SITE = 'cwoo.me'
WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
# Column letters on the "All visits" sheet, as in docs/administration/VISITOR_LOG.md.
COL = {name: chr(ord('A') + i) for i, name in enumerate(visitor_log.COLUMNS)}
LIKELY_BOT = f'=AND(COUNTIF({COL["visitor"]}:{COL["visitor"]},{COL["visitor"]}{{r}})=1,{COL["referrer"]}{{r}}="")'
COUNTED = f'=AND({COL["cloud"]}{{r}}="",{COL["real_browser"]}{{r}}="yes",NOT(U{{r}}))'
TOP = 30


def week_bounds(monday, zone):
    """[start, end) of the Monday-to-Sunday week starting on monday, as aware datetimes."""
    start = datetime.combine(monday, time(), zone)
    return start, datetime.combine(monday + timedelta(days=7), time(), zone)


def last_full_week(today):
    """The Monday of the last week that has fully ended by today."""
    return today - timedelta(days=today.weekday() + 7)


def week_rows(log, archive, start, end, zone, ignore=(), locate=None):
    """Page-view rows (lists of visitor_log.COLUMNS values) in [start, end), plus counts."""
    margin = timedelta(days=1)
    lines = access_log_archive.lines_between(log, archive, start - margin, end + margin)
    return visitor_log.build_rows(lines, ignore=ignore, locate=locate, pages_only=True, zone=zone,
                                  start=start, end=end)


def as_dicts(rows):
    return [dict(zip(visitor_log.COLUMNS, values)) for values in rows]


def mark_robots(visits):
    """Add likely_bot and counted to each visit, the same rule as the workbook's formulas."""
    seen = Counter(visit['visitor'] for visit in visits)
    for visit in visits:
        visit['likely_bot'] = seen[visit['visitor']] == 1 and not visit['referrer']
        visit['counted'] = not visit['cloud'] and visit['real_browser'] == 'yes' and not visit['likely_bot']
    return visits


def page_name(page):
    """A readable name for a page address: math entries by their slug."""
    parts = urlsplit(page)
    slug = parse_qs(parts.query).get('slug', [''])[0]
    path = parts.path or '/'
    return f'{path} ({slug})' if slug else path


def came_from(referrer):
    if not referrer:
        return '(typed in, bookmark or app)'
    host = (urlsplit(referrer).hostname or referrer).removeprefix('www.')
    return '(this site)' if host == SITE else host


def tally(visits, key):
    """(name, visits, distinct visitors), most visits first."""
    count, people = Counter(), defaultdict(set)
    for visit in visits:
        name = key(visit)
        count[name] += 1
        people[name].add(visit['visitor'])
    return [(name, number, len(people[name])) for name, number in
            sorted(count.items(), key=lambda item: (-item[1], str(item[0])))]


def summarize(visits, start, end, counts):
    real = [visit for visit in visits if visit['counted']]
    days = [(start + timedelta(days=i)).date() for i in range((end - start).days)]
    by_day = {day: [0, set()] for day in days}
    for visit in real:
        day = date.fromisoformat(visit['local_time'][:10])
        if day in by_day:
            by_day[day][0] += 1
            by_day[day][1].add(visit['visitor'])
    return dict(
        start=start, end=end, page_views=len(visits), real_visits=len(real),
        real_visitors=len({visit['visitor'] for visit in real}),
        cloud=sum(1 for visit in visits if visit['cloud']),
        not_real_browser=sum(1 for visit in visits if not visit['cloud'] and visit['real_browser'] != 'yes'),
        likely_bot=sum(1 for visit in visits if not visit['cloud'] and visit['real_browser'] == 'yes'
                       and visit['likely_bot']),
        declared_bots=counts.get('bots', 0), yours=counts.get('you', 0),
        days=[(day, by_day[day][0], len(by_day[day][1])) for day in days],
        countries=tally(real, lambda visit: visit['country'] or '(unknown)'),
        cities=tally(real, lambda visit: ', '.join(p for p in (visit['city'], visit['country']) if p) or '(unknown)'),
        devices=tally(real, lambda visit: visit['device']),
        systems=tally(real, lambda visit: visit['os'] or '(unknown)'),
        browsers=tally(real, lambda visit: visit['browser'] or '(unknown)'),
        weekdays=sorted(tally(real, lambda visit: visit['weekday']), key=lambda row: WEEKDAYS.index(row[0])),
        hours=sorted(tally(real, lambda visit: int(visit['hour'])), key=lambda row: row[0]),
        pages=tally(real, lambda visit: page_name(visit['page'])),
        sources=tally(real, lambda visit: came_from(visit['referrer'])),
    )


def text_cell(cell, value):
    """Put visitor-supplied text in a cell as plain text, never as a formula."""
    from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
    if isinstance(value, str):
        value = ILLEGAL_CHARACTERS_RE.sub('', value)
        cell.value = value or None
        if value:
            cell.data_type = 's'
    else:
        cell.value = value


def build_workbook(visits, summary, zone_name):
    """An openpyxl Workbook: Summary, Places, Devices, Times, Pages, All visits."""
    from openpyxl import Workbook
    from openpyxl.chart import BarChart, Reference
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    bold, head_fill = Font(bold=True), PatternFill('solid', fgColor='DDEBF7')
    wrap = Alignment(wrap_text=True, vertical='top')
    book = Workbook()

    def table(sheet, row, column, title, headers, data):
        """Write a small titled table; returns the row after it."""
        sheet.cell(row, column, title).font = Font(bold=True, size=12)
        for i, header in enumerate(headers):
            cell = sheet.cell(row + 1, column + i, header)
            cell.font, cell.fill = bold, head_fill
        for r, values in enumerate(data, start=row + 2):
            for i, value in enumerate(values):
                text_cell(sheet.cell(r, column + i), value)
        if not data:
            sheet.cell(row + 2, column, '(none)')
        return row + 3 + max(len(data), 1)

    def widths(sheet, sizes):
        for i, size in enumerate(sizes, start=1):
            sheet.column_dimensions[get_column_letter(i)].width = size

    start, end = summary['start'], summary['end']
    last = (end - timedelta(days=1)).date()
    sheet = book.active
    sheet.title = 'Summary'
    sheet['A1'] = f'{SITE} visits, {start:%a %b} {start.day} to {last:%a %b} {last.day}, {last.year}'
    sheet['A1'].font = Font(bold=True, size=14)
    zone_label = f'Pacific time ({zone_name})' if zone_name == ZONE else zone_name
    sheet['A2'] = f'Times are {zone_label}. Made {datetime.now(start.tzinfo):%Y-%m-%d %H:%M}.'
    facts = [
        ('Real visits (pages opened by real people)', summary['real_visits']),
        ('Real visitors (distinct address + browser)', summary['real_visitors']),
        ('All page views after removing you and admitted robots', summary['page_views']),
        ('  removed: from a cloud or hosting network', summary['cloud']),
        ('  removed: did not load the page\'s parts (real_browser not yes)', summary['not_real_browser']),
        ('  removed: likely robot (one page, no referrer)', summary['likely_bot']),
        ('Admitted robots left out before counting (any request)', summary['declared_bots']),
        ('Your own requests left out (any request)', summary['yours']),
    ]
    row = table(sheet, 4, 1, 'This week', ['What', 'Count'], facts)
    sheet.cell(row, 1, 'Every count on these sheets uses real visits only: cloud blank, real_browser yes, '
                       'likely_bot FALSE. The "All visits" sheet has every page view with filters, '
                       'so you can count differently.').alignment = wrap
    sheet.merge_cells(start_row=row, start_column=1, end_row=row, end_column=3)
    sheet.row_dimensions[row].height = 45
    day_row = row + 2
    days = [(f'{day:%a} {day:%Y-%m-%d}', number, people) for day, number, people in summary['days']]
    table(sheet, day_row, 1, 'Real visits per day', ['Day', 'Visits', 'Visitors'], days)
    chart = BarChart()
    chart.title, chart.y_axis.title, chart.legend = 'Real visits per day', 'Visits', None
    chart.add_data(Reference(sheet, min_col=2, min_row=day_row + 1, max_row=day_row + 1 + len(days)),
                   titles_from_data=True)
    chart.set_categories(Reference(sheet, min_col=1, min_row=day_row + 2, max_row=day_row + 1 + len(days)))
    chart.height, chart.width = 7, 14
    sheet.add_chart(chart, f'E{day_row}')
    widths(sheet, [58, 10, 10])

    sheet = book.create_sheet('Places')
    row = table(sheet, 1, 1, 'Countries', ['Country', 'Visits', 'Visitors'], summary['countries'])
    table(sheet, row, 1, f'Cities (top {TOP})', ['City', 'Visits', 'Visitors'], summary['cities'][:TOP])
    widths(sheet, [40, 10, 10])

    sheet = book.create_sheet('Devices')
    row = table(sheet, 1, 1, 'Phone or computer', ['Device', 'Visits', 'Visitors'], summary['devices'])
    row = table(sheet, row, 1, 'Operating system', ['System', 'Visits', 'Visitors'], summary['systems'])
    table(sheet, row, 1, 'Browser', ['Browser', 'Visits', 'Visitors'], summary['browsers'])
    widths(sheet, [28, 10, 10])

    sheet = book.create_sheet('Times')
    row = table(sheet, 1, 1, 'By weekday', ['Weekday', 'Visits', 'Visitors'], summary['weekdays'])
    hours = [(f'{hour:02d}:00-{hour:02d}:59', number, people) for hour, number, people in summary['hours']]
    table(sheet, row, 1, 'By hour of day', ['Hour', 'Visits', 'Visitors'], hours)
    widths(sheet, [20, 10, 10])

    sheet = book.create_sheet('Pages')
    row = table(sheet, 1, 1, f'Top pages (top {TOP})', ['Page', 'Visits', 'Visitors'], summary['pages'][:TOP])
    table(sheet, row, 1, 'Came from', ['Site', 'Visits', 'Visitors'], summary['sources'][:TOP])
    widths(sheet, [70, 10, 10])

    sheet = book.create_sheet('All visits')
    headers = visitor_log.COLUMNS + ['likely_bot', 'counted']
    for i, header in enumerate(headers, start=1):
        cell = sheet.cell(1, i, header)
        cell.font, cell.fill = bold, head_fill
    for r, visit in enumerate(visits, start=2):
        for i, name in enumerate(visitor_log.COLUMNS, start=1):
            text_cell(sheet.cell(r, i), visit[name])
        sheet.cell(r, len(headers) - 1, LIKELY_BOT.format(r=r))
        sheet.cell(r, len(headers), COUNTED.format(r=r))
    sheet.freeze_panes = 'A2'
    sheet.auto_filter.ref = f'A1:{get_column_letter(len(headers))}{max(len(visits) + 1, 2)}'
    widths(sheet, [19, 19, 11, 6, 8, 16, 10, 10, 10, 16, 16, 16, 28, 7, 12, 8, 50, 7, 30, 50, 11, 10])
    return book


def subject_and_body(summary):
    start, last = summary['start'], (summary['end'] - timedelta(days=1)).date()
    span = f'{start:%b} {start.day} to {last:%b} {last.day}'
    subject = (f'{SITE} weekly visits, {span}: {summary["real_visits"]} real visits '
               f'from {summary["real_visitors"]} visitors')
    lines = [f'{SITE} visits, {start:%A %b} {start.day} to {last:%A %b} {last.day} {last.year} (Pacific time).', '',
             f'Real visits: {summary["real_visits"]} from {summary["real_visitors"]} visitors.',
             f'Left out as robots: {summary["cloud"]} from cloud networks, '
             f'{summary["not_real_browser"]} that did not load the page like a browser, '
             f'{summary["likely_bot"]} one-page visits with no referrer.', '']
    for title, rows in (('Top countries', summary['countries']), ('Top pages', summary['pages']),
                        ('Phone or computer', summary['devices']), ('Came from', summary['sources'])):
        lines.append(f'{title}:')
        lines.extend(f'  {name}: {number}' for name, number, _ in rows[:5])
        if not rows:
            lines.append('  (none)')
        lines.append('')
    lines.append('The attached Excel file has the details and every page view, with the robot filter.')
    return subject, '\n'.join(lines) + '\n'


def email_settings(path=SETTINGS):
    try:
        values = json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError) as error:
        raise SystemExit(f'Could not read {path}: {error}')
    found = {key: values.get(key) for key in ('REPORT_EMAIL_FROM', 'REPORT_EMAIL_PASSWORD', 'REPORT_EMAIL_TO')}
    missing = [key for key, value in found.items() if not isinstance(value, str) or not value]
    if missing:
        raise SystemExit(f'Email is not set up ({", ".join(missing)} missing). '
                         'Run: python hosting_secrets.py email')
    return found


def send_email(settings, subject, body, attachment=None, smtp=smtplib.SMTP):
    message = EmailMessage()
    message['From'], message['To'], message['Subject'] = (settings['REPORT_EMAIL_FROM'],
                                                          settings['REPORT_EMAIL_TO'], subject)
    message.set_content(body)
    if attachment:
        attachment = Path(attachment)
        message.add_attachment(attachment.read_bytes(), maintype='application',
                               subtype='vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                               filename=attachment.name)
    try:
        with smtp(SMTP_HOST, SMTP_PORT, timeout=60) as server:
            server.starttls(context=ssl.create_default_context())
            server.login(settings['REPORT_EMAIL_FROM'], settings['REPORT_EMAIL_PASSWORD'])
            server.send_message(message)
    except smtplib.SMTPAuthenticationError:
        raise SystemExit('Gmail refused the sign-in. Check the address and app password: '
                         'python hosting_secrets.py email')


def report_name(monday):
    return f'visits-{monday:%Y-%m-%d}-to-{monday + timedelta(days=6):%Y-%m-%d}.xlsx'


def make_report(monday, out, log, archive, zone_name):
    """Save rotated logs, then write the week's workbook to out. Returns the summary."""
    zone = ZoneInfo(zone_name)
    start, end = week_bounds(monday, zone)
    access_log_archive.save_rotated(log, archive)
    rows, counts = week_rows(log, archive, start, end, zone, ignore=visitor_log.ignored_addresses(),
                             locate=visitor_log.open_locator())
    visits = mark_robots(as_dicts(rows))
    summary = summarize(visits, start, end, counts)
    build_workbook(visits, summary, zone_name).save(out)
    return summary


def send_weekly(log, archive, reports, zone_name, settings_path=SETTINGS, today=None, smtp=smtplib.SMTP):
    """Email the last full week's report unless it was already sent. Returns a message."""
    today = today or datetime.now(ZoneInfo(zone_name)).date()
    monday = last_full_week(today)
    reports = Path(reports)
    final = reports / report_name(monday)
    if final.exists():
        return f'Already sent: {final}'
    settings = email_settings(settings_path)
    # Built in a private subfolder under its final name (the attachment's name), and moved
    # next to the others only once Gmail has accepted it.
    sending = reports / f'.sending-{uuid.uuid4().hex[:8]}'
    sending.mkdir(parents=True)
    draft = sending / final.name
    try:
        summary = make_report(monday, draft, log, archive, zone_name)
        subject, body = subject_and_body(summary)
        send_email(settings, subject, body, draft, smtp=smtp)
        os.replace(draft, final)
    finally:
        draft.unlink(missing_ok=True)
        sending.rmdir()
    return f'Sent "{subject}" to {settings["REPORT_EMAIL_TO"]}. Copy kept at {final}'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--log', type=Path, default=LOG, help='current access log')
    parser.add_argument('--archive', type=Path, default=ARCHIVE, help='saved rotated logs')
    parser.add_argument('--zone', default=ZONE, help='time zone for days and hours')
    commands = parser.add_subparsers(dest='command', required=True)
    send = commands.add_parser('send', help="email last week's report unless already sent")
    send.add_argument('--reports', type=Path, default=REPORTS, help='where sent reports are kept')
    build = commands.add_parser('build', help='write one week\'s report to a file, no email')
    build.add_argument('--out', type=Path, required=True)
    build.add_argument('--week-of', type=date.fromisoformat, help='any date in the week (default: last full week)')
    commands.add_parser('test-email', help='send a short test email')
    args = parser.parse_args(argv)
    os.umask(0o077)  # Reports and logs hold visitors' addresses: owner-only files.
    if args.command == 'send':
        print(send_weekly(args.log, args.archive, args.reports, args.zone))
    elif args.command == 'build':
        day = args.week_of or last_full_week(datetime.now(ZoneInfo(args.zone)).date())
        monday = day - timedelta(days=day.weekday())
        summary = make_report(monday, args.out, args.log, args.archive, args.zone)
        print(f'Wrote {args.out}: {summary["real_visits"]} real visits from {summary["real_visitors"]} visitors.')
    else:
        settings = email_settings()
        send_email(settings, f'{SITE} weekly report: test',
                   'This is a test from weekly_visit_report.py on PythonAnywhere. Email works.\n')
        print(f'Test email sent to {settings["REPORT_EMAIL_TO"]}.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
