# Weekly visit report (and keeping every access log)

Added 2026-11-01. Code: `backend/src/weekly_visit_report.py`,
`backend/src/services/access_log_archive.py`, the `--access-log` option of
`backend/src/database/nightly_backup.py`, and the `email` command of
`backend/src/hosting_secrets.py`. Tests: `backend/tests/test_weekly_visit_report.py`.

Every Monday morning you get an email with last week's visits (Monday to Sunday, Pacific
time) and an Excel file attached. It builds on the [Visitor log](VISITOR_LOG.md): same
columns, same way of leaving out your own visits and admitted robots.

## Two parts

1. **Keeping every log.** PythonAnywhere keeps only a few weeks of access logs, then
   deletes the oldest. The nightly backup task now also copies each *rotated* log (the
   older copies PythonAnywhere renamed to `.1`, `.2.gz`, ...) into
   `/home/cwoo/backups/access-logs/`, compressed, once each. They are never deleted, so the
   history goes back to the day this was switched on. The current log, which is still
   being written to, is not copied; it gets copied after PythonAnywhere rotates it.
2. **The weekly email.** A daily scheduled task runs `weekly_visit_report.py send`. If
   last week's report hasn't been sent yet, it builds it from the saved logs plus the
   current log, emails it to you through Gmail, and keeps a copy in
   `/home/cwoo/backups/weekly-reports/`. On every other day of the week it sees that copy
   and does nothing. If Monday's send fails (Gmail down, say), Tuesday's run tries again.

## What the Excel file holds

| Sheet | What's on it |
| --- | --- |
| Summary | Real visits and real visitors for the week, how many page views were left out as robots and why, visits per day with a bar chart |
| Places | Countries, and the top 30 cities |
| Devices | Phone, computer or tablet; operating system; browser |
| Times | Visits by weekday and by hour of day (Pacific time) |
| Pages | Top 30 pages (math entries shown with their slug), and which sites people came from |
| All visits | Every page view of the week, with the same columns as the visitor log CSV, filters already on, and two extra columns |

**"Real" means** a page view that passes all three robot checks from
[Filtering out robots in Excel](VISITOR_LOG.md#filtering-out-robots-in-excel):
`cloud` is blank, `real_browser` is `yes`, and `likely_bot` is `FALSE`. Every count on the
first five sheets uses real visits only. A visitor is one IP address with one browser, as in
the CSV.

The **All visits** sheet keeps the formulas so you can see and change the rule:

- column U `likely_bot` is `=AND(COUNTIF(E:E,E2)=1,S2="")`: this visitor opened exactly one
  page this week and came from nowhere (no referrer);
- column V `counted` is `=AND(N2="",O2="yes",NOT(U2))`: `TRUE` for the rows the summary
  counted.

Excel works these out when you open the file. Gmail's preview and some phone viewers
don't run formulas, so U and V may look empty there; the summary sheets are plain
numbers and show everywhere. Text a visitor controls (page address, referrer, browser
description) is stored as plain text, so a visitor can't make Excel run a formula.

The email itself lists the week's totals and the top 5 countries, pages, devices and
referring sites, so you can read the gist on your phone without opening the file.

## Can PythonAnywhere send email through Gmail?

Yes. Free PythonAnywhere accounts may only reach a list of allowed sites, with an
exception for Gmail's mail servers; paid accounts (yours, since it serves `www.cwoo.me`)
can reach any server. The script uses `smtp.gmail.com` port 587 with encryption
(STARTTLS), which is what PythonAnywhere's own help page uses
([SMTP for free users](https://www.pythonanywhere.com/wiki/SMTPForFreeUsers)).

It signs in to your Gmail account with an **app password**: a separate 16-letter password
Google makes for one program. It can only send and read mail, it can't change your Google
account, and you can cancel it at any time without changing your main password. Google
offers app passwords only when **2-Step Verification** is on for the account.

The email goes from your Gmail address to your Gmail address, so it lands in your inbox
like any message you send yourself.

## Set it up (once)

### 1. Publish the code

After the pull request is merged, on the laptop:

```powershell
git pull
.\.venv313\Scripts\python.exe -m pip install -r backend\requirements.txt   # adds openpyxl for the laptop
```

Then start the helper and do these in order, finishing each before the next (the helper
keeps one prepared package at a time):

1. **15**, and enter
   `backend/src/weekly_visit_report.py,backend/src/services/access_log_archive.py,backend/src/services/visitor_log.py,backend/src/database/nightly_backup.py,backend/src/hosting_secrets.py`
   then **3**, **4**, **5**.
2. **22** (installs `openpyxl`, the package that writes Excel files, on PythonAnywhere;
   see [Package updates](deployment/PACKAGE_UPDATES.md)).

### 2. Make a Gmail app password

1. Open <https://myaccount.google.com/security> signed in as the Gmail account the report
   should come from. Under "How you sign in to Google", check that **2-Step Verification**
   is on (turn it on if not).
2. Open <https://myaccount.google.com/apppasswords>. Type a name such as
   `cwoo.me weekly report` and press **Create**.
3. Google shows 16 letters in four groups. Keep that window open for the next step; Google
   never shows it again (you can always make a new one).

### 3. Store it on PythonAnywhere

Open a PythonAnywhere **Bash console** (Dashboard, then Consoles, then Bash):

```bash
workon chi-portfolio
cd ~/chi-portfolio/backend/src
python hosting_secrets.py email
```

It asks for the Gmail address to send from, the address to send to (press Enter for the
same one), and the app password (typing is hidden; spaces are fine). It saves them in
`~/.config/chi-portfolio/hosting.json` with the site's other secrets, owner-only. No reload
is needed: the website doesn't use them.

Then check it works:

```bash
python weekly_visit_report.py test-email
```

You should get an email titled "cwoo.me weekly report: test" within a minute. If it says
"Gmail refused the sign-in", run `hosting_secrets.py email` again and re-type the app
password.

### 4. Save the logs PythonAnywhere still has, and try a report

Still in the console (this also copies every rotated log that exists right now, so do it
soon, before PythonAnywhere deletes the oldest):

```bash
python weekly_visit_report.py build --out ~/report-test.xlsx
ls ~/backups/access-logs/
```

The first line writes last week's report to a file without emailing it and prints the
count of real visits. The second lists the saved logs. To look at the file, open the
**Files** tab, find `report-test.xlsx` in your home folder and download it. Delete it there
when done.

### 5. Scheduled tasks

On the **Tasks** tab (times are UTC):

**Change** the existing 10:17 nightly backup task's command to (one line):

```
/home/cwoo/.virtualenvs/chi-portfolio/bin/python /home/cwoo/chi-portfolio/backend/src/database/nightly_backup.py backup --database /home/cwoo/chi-portfolio/backend/portfolio.db --backups /home/cwoo/backups/nightly --access-log /var/log/www.cwoo.me.access.log --log-archive /home/cwoo/backups/access-logs
```

**Add** a daily task at **17:05** with the command (one line):

```
/home/cwoo/.virtualenvs/chi-portfolio/bin/python /home/cwoo/chi-portfolio/backend/src/weekly_visit_report.py send
```

17:05 UTC is 9:05 am Pacific in winter and 10:05 am in summer. PythonAnywhere tasks run
daily or hourly, not weekly; running daily is what lets a failed Monday retry on
Tuesday. The first run on or after Monday 2 November emails the week of 26 October to
1 November.

## Checking it

- **Nightly log copy:** the 10:17 task's log (Tasks tab, the log icon next to the task)
  shows `"access_logs": {"saved": [...], "already_saved": N, ... "status": "ok"}`. The
  database backup still runs if the log copy fails; the task then ends with an error and
  the log shows `"status": "failed"` with the reason.
- **Weekly email:** the 17:05 task's log says `Sent "..." to ...` on the day it sends,
  and `Already sent: ...` on the others.

## Disk space

Access logs compress well: expect a few hundred kilobytes a week at today's traffic, and
about 30 KB per weekly report. `/home/cwoo/backups/` is under the same disk quota as the
nightly database backups (see [Site down recovery](backups/SITE_DOWN_RECOVERY.md) for
freeing space). Nothing here deletes old logs or reports automatically; delete old
reports by hand if you ever need room (the logs are the part worth keeping).

## Other commands

```bash
# Any past week's report, to a file (any date in that week):
python weekly_visit_report.py build --week-of 2026-11-09 --out ~/visits-nov-9.xlsx

# Send a week again: delete its copy, then send.
rm ~/backups/weekly-reports/visits-2026-10-26-to-2026-11-01.xlsx
python weekly_visit_report.py send
```

`send` always means the last full week; to re-send an older one, `build` it and email it
yourself.

## Changing or cancelling

- **Stop the emails:** delete the 17:05 task. Logs keep being saved by the nightly task.
- **New app password** (or a different address): make one at
  <https://myaccount.google.com/apppasswords>, run `python hosting_secrets.py email` again,
  then delete the old one on that Google page so it stops working.
- **Suspect the app password leaked:** delete it on the Google page first (that alone
  stops it), then make and store a new one.
