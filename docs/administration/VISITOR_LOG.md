# Visitor log

The admin page has two buttons that download a CSV file (open it in Excel, or load it into
SQLite) listing who visited the site, with your own visits and search-engine robots left out.

- **Visitor log (pages, CSV)**: one row per page someone opened. This is the one you normally want.
- **Visitor log (every request, CSV)**: one row per file the browser fetched. Opening one page
  makes a browser fetch many files (the page, its style sheets, scripts, pictures and the data
  the page asks the server for), so this is much longer. Useful when you want to see, for
  example, which photo files were loaded.

The buttons only read the logs. Nothing on the site changes.

## Where the data comes from

Every time a browser asks the server for anything, PythonAnywhere writes one line to the
**access log**, `/var/log/www.cwoo.me.access.log`. You can see the same file on the
PythonAnywhere **Web** tab under **Log files**. A line looks like this:

```
8.8.8.8 - - [30/Oct/2026:01:00:00 +0000] "GET /math/concept.html?slug=group HTTP/1.1" 200 512 "https://www.google.com/" "Mozilla/5.0 (iPhone; ...) Safari/604.1" ...
```

In order, that is: the visitor's **IP address**, the time (UTC), what was asked for, the
**status code** (200 means it worked, 404 means not found), the **referrer** (the page the
visitor came from, when their browser says so) and the **User-Agent** (a description the
browser sends of itself).

PythonAnywhere **rotates** the log: it renames the file to `.1`, then compresses older copies
as `.2.gz`, `.3.gz` and so on, and eventually deletes the oldest. The download reads all of
them, so the CSV goes back only as far as PythonAnywhere keeps them, typically a few weeks.
If you want a longer history, download the CSV every couple of weeks and keep the files.

## The CSV columns

| Column | Meaning |
| --- | --- |
| `time_utc` | When the request arrived, in UTC (Coordinated Universal Time, not your local time) |
| `local_time` | The same moment in your own time zone (the admin page tells the server which time zone your browser is set to; daylight saving is handled) |
| `weekday` | Day of the week in your time zone, e.g. `Friday` |
| `hour` | Hour of the day in your time zone, 0 to 23 (`18` means 6:00 to 6:59 pm), handy for a pivot table of busy times |
| `visitor` | `V1`, `V2`, ... One number per IP address plus browser, in order of first visit. A rough way to count people; see the limits below |
| `ip` | The visitor's IP address |
| `device` | `phone`, `tablet`, `computer` or `unknown`, guessed from the User-Agent |
| `os`, `browser` | Operating system and browser, also from the User-Agent |
| `city`, `region`, `country` | Approximate place, from the IP address (blank until the location file is installed, see below) |
| `network` | Who owns the IP address: a home or phone provider such as "Comcast Cable" or "Verizon", or a company such as "Amazon.com" (blank until the network file is installed) |
| `cloud` | `yes` when `network` is a cloud or hosting company (Amazon, Microsoft, DigitalOcean, Hetzner, ...). Real people rarely browse from those, so these rows are almost always robots pretending to be browsers. Filter on this column in Excel to hide them |
| `real_browser` | `yes` when, within a minute of opening the page, the same address and browser also fetched the page's parts (style sheets, scripts, or the data every page asks the server for). Real browsers always do; most robots read only the page itself, so `no` usually means a robot even when `network` is a home provider. Can say `no` for a real person who closed the page instantly. Blank on non-page rows of the every-request file |
| `method` | `GET` means "fetch this"; other methods send data to the server |
| `page` | The address asked for. For math entries the `slug=` part says which entry |
| `status` | 200 = worked, 304 = browser already had it, 404 = not found |
| `referrer` | The page they came from, such as a Google search, when the browser says so |
| `user_agent` | The raw browser description, in case you want to look closer |

## What can and can't be known

**Device type: yes, mostly.** Every browser sends a User-Agent text, for example
"iPhone ... Mobile Safari" or "Windows NT 10.0 ... Chrome". That is reliable enough for phone vs
computer. Two catches: iPads now say "Macintosh", so they show as `computer`; and a
browser can be set to lie, though few people do.

**Location: approximately.** An IP address is handed out by the visitor's internet provider,
and there are public databases of which provider uses which addresses where. That gives the
country reliably and the city often, but it is the provider's location, not the person's:
phone networks may place someone in a city hundreds of miles away, and anyone using a VPN or
iCloud Private Relay shows the VPN's location. The site uses DB-IP's free database, which
asks to be credited; the credit is on the admin page.

**Name: no.** Nothing a browser sends includes the person's name or email. The only ways to
know who someone is are that they sign in (the site has no visitor accounts) or that they tell
you. The IP address alone does not identify a person; the internet provider knows which
customer had it, but only gives that out to the police with a court order.

**Counting people is rough.** One person on a phone and a laptop counts as two visitors. A whole
office or a family behind one router can share one IP address. Phone networks change a phone's
address often, so one person can show as several visitors over a day.

## Opening the file in Excel

The file starts with an invisible marker (a UTF-8 "byte-order mark") that tells Excel which
alphabet the text uses, so names like "São Paulo" or "Zürich" show correctly. Without it Excel
shows them garbled, like "SÃ£o Paulo". If you load the file into SQLite or Python instead, read it
as `utf-8-sig`, which skips the marker.

## How your own visits are left out

A row is treated as yours, and left out, when its IP address:

1. is the address you are downloading from right now; or
2. did admin work on the same UTC day: a successful sign-in, a saved change, or any admin
   page request (anything under `/api/admin/`). Only you can do these, so this catches your
   phone and laptop, at home or travelling, on any day you signed in; or
3. is listed in `~/.config/chi-portfolio/visitor-log-ignore-ips.txt` on PythonAnywhere.

A day when you only browsed the site, without signing in, from an address other than the one
you download from, will still show up. If you have a home address that rarely changes, put it in
the ignore file, one address per line; anything after `#` is a note:

```
203.0.113.25   # home
```

To find your current address, search "what is my IP" in a browser at home. Home addresses can
change when the router restarts, so check now and then.

**Robots** are left out too: anything whose User-Agent mentions bot, crawler, spider, curl and
similar, or sends no User-Agent at all. Robots that pretend to be ordinary browsers can't be
told apart and will appear as visitors.

## One-time setup on PythonAnywhere

After the code is published (option 15 with `backend/src/services/visitor_log.py,
backend/src/routes/admin_visitors.py, backend/src/geoip_update.py, backend/src/app.py,
frontend/admin_app.js`, then
option 14 with `admin_dashboard.html,admin_style.css` (option 14 paths are relative to `frontend/`), then options 3, 4, 5),
open a **Bash console** on PythonAnywhere and run:

```
workon chi-portfolio
pip install maxminddb==3.2.0
cd ~/chi-portfolio/backend/src
python geoip_update.py
```

Then **Reload** the web app on the Web tab. The download works without the location file, just
with blank location columns.

`geoip_update.py` downloads the city-level file (about 130 MB of your disk space) and the network-owner file (about 10 MB). If disk is
tight, use `python geoip_update.py --country` instead (about 8 MB, country only; the network file still comes too). DB-IP
publishes a new file every month; addresses move slowly, so re-running it every few months is
plenty. No reload is needed after an update.

## If the button gives an error

- **"No access log found"**: the server looked for `/var/log/www.cwoo.me.access.log` and it
  wasn't there. Check the exact file name on the Web tab under Log files. If it differs, set the
  environment variable `VISITOR_LOG_PATH` to the right path in the WSGI file and reload.
- **"Could not read the access log"**: the web app wasn't allowed to read the file. Download it
  by hand from the Web tab instead and tell Claude, so the download can be moved to the laptop
  helper (which reads the log through the PythonAnywhere API).
- **403 / "Unauthorized"**: you are signed out. Sign in on the admin page and try again.
