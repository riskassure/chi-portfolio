"""Option 22: install the Python packages pinned in backend/requirements.txt on PythonAnywhere.

Run from the helper (website_workflow.py, option 22) after a dependency PR, such
as a Dependabot update, is merged and pulled. It

1. runs the deploy guard (clean main that matches GitHub), so the list of
   versions comes from reviewed, tested code;
2. reads the packages installed in the site virtualenv over SSH (no changes)
   and shows which ones differ from requirements.txt;
3. after a typed UPDATE, runs pip install -r in that virtualenv, then replaces
   the live copy of backend/requirements.txt with main's;
4. checks every pin is now installed, reloads the website and checks the
   homepage.

A receipt with the versions before and after goes to dist/package-updates/.
To undo an update, revert its PR on main, pull, and run option 22 again: pins
are exact, so pip moves back to the earlier versions.
See docs/administration/deployment/PACKAGE_UPDATES.md.
"""
from importlib import metadata
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess
import time

import deploy_guard
import site_deployment
from pythonanywhere_api import SETTINGS, validate

ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = 'backend/requirements.txt'
RECEIPTS = ROOT / 'dist' / 'package-updates'
VIRTUALENV = 'chi-portfolio'
PREFIX = 'LIVE_PACKAGES='
PIN = re.compile(r'([A-Za-z0-9][A-Za-z0-9._-]*)==([A-Za-z0-9][A-Za-z0-9.+!_-]*)')

# Runs on PythonAnywhere with the system Python. It reads a JSON request on
# stdin and prints one PREFIX line; pip's own progress goes to stderr, which
# the laptop terminal shows as it happens.
REMOTE_SCRIPT = r'''
import hashlib, json, os, subprocess, sys, tempfile
from pathlib import Path
request = json.load(sys.stdin)
home = Path.home()
python = home / '.virtualenvs' / request['virtualenv'] / 'bin' / 'python'
live_copy = home / 'chi-portfolio' / 'backend' / 'requirements.txt'
if not python.is_file():
    raise SystemExit('Site virtualenv not found: ' + str(python))
def installed():
    result = subprocess.run([str(python), '-m', 'pip', 'list', '--format=json', '--disable-pip-version-check'],
                            stdout=subprocess.PIPE, check=True)
    return {item['name']: item['version'] for item in json.loads(result.stdout)}
def copy_digest():
    # Line endings are ignored: a copy uploaded from Windows may have CRLF.
    return hashlib.sha256(live_copy.read_bytes().replace(b'\r\n', b'\n')).hexdigest() if live_copy.is_file() else None
if request['mode'] == 'install':
    data = request['requirements'].encode('utf-8')
    fd, temporary = tempfile.mkstemp(prefix='.requirements-', suffix='.txt', dir=home)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
        result = subprocess.run([str(python), '-m', 'pip', 'install', '--no-cache-dir', '--disable-pip-version-check',
                                 '-r', temporary], stdout=sys.stderr)
        if result.returncode:
            raise SystemExit('pip install failed (exit code %d); the live requirements.txt was left as it was.' % result.returncode)
        # Only after a successful install, so the live copy never names versions that are not installed.
        os.replace(temporary, live_copy)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
print('LIVE_PACKAGES=' + json.dumps(dict(python=str(python), installed=installed(), copy=copy_digest())))
'''


def normalize(name):
    """Package names compare case-insensitively with -, _ and . treated alike (PEP 503)."""
    return re.sub(r'[-_.]+', '-', name).lower()


def parse_requirements(text):
    """Return {name: version} for a requirements file of exact pins only.

    Anything else (ranges, options, URLs) is refused, so a careless edit can't
    make the live install differ from what CI tested.
    """
    pins = {}
    for number, line in enumerate(text.splitlines(), 1):
        line = line.split('#', 1)[0].strip()
        if not line:
            continue
        match = PIN.fullmatch(line)
        if not match:
            raise ValueError(f'{REQUIREMENTS} line {number} is not an exact pin like "Flask==3.1.3": {line}')
        if normalize(match[1]) in {normalize(name) for name in pins}:
            raise ValueError(f'{REQUIREMENTS} line {number} pins {match[1]} a second time.')
        pins[match[1]] = match[2]
    if not pins:
        raise ValueError(f'{REQUIREMENTS} pins no packages.')
    return pins


def differences(wanted, installed):
    """[(name, installed version or None, wanted version)] for each pin not installed exactly."""
    have = {normalize(name): version for name, version in installed.items()}
    return [(name, have.get(normalize(name)), version) for name, version in wanted.items()
            if have.get(normalize(name)) != version]


def table(changes):
    width = max(len(name) for name, _, _ in changes)
    return '\n'.join(f'  {name.ljust(width)}  {old or "(not installed)"} -> {new}' for name, old, new in changes)


def laptop_versions(wanted):
    """Versions installed for the Python running the helper (the laptop's .venv313)."""
    found = {}
    for name in wanted:
        try:
            found[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            pass
    return found


def remote(username, request, timeout):
    """Run REMOTE_SCRIPT over SSH and return its parsed answer."""
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', username):
        raise ValueError('Invalid hosting username.')
    command = ['ssh', '-o', 'ConnectTimeout=15', username + '@ssh.pythonanywhere.com',
               'python3.13 -I -B -c ' + shlex.quote(REMOTE_SCRIPT)]
    try:
        result = subprocess.run(command, input=json.dumps(request), text=True, encoding='utf-8',
                                stdout=subprocess.PIPE, timeout=timeout)
    except FileNotFoundError:
        raise ValueError('ssh was not found. Install the Windows OpenSSH Client.') from None
    except subprocess.TimeoutExpired:
        raise RuntimeError('PythonAnywhere did not answer in time. Run option 22 again; it shows what is installed now.') from None
    lines = [line[len(PREFIX):] for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    if result.returncode or len(lines) != 1:
        raise RuntimeError('The PythonAnywhere step did not finish (see the messages above). '
                           'Run option 22 again; it shows what is installed now.')
    return json.loads(lines[0])


def choose_domain(settings, ask=input):
    domains = site_deployment.domains(settings)
    if not domains:
        raise ValueError('No website found in the selected account.')
    domain = domains[0] if len(domains) == 1 else ask('Website domain to reload (' + ', '.join(domains) + '): ').strip()
    if domain not in domains:
        raise ValueError('Choose a website from the account list.')
    return domain


def laptop_advice(wanted):
    if differences(wanted, laptop_versions(wanted)):
        return ('This laptop\'s Python also differs from requirements.txt. Update it with:\n'
                '  .\\.venv313\\Scripts\\python.exe -m pip install -r backend\\requirements.txt')
    return 'This laptop already has the same versions.'


def run(state, ask=input, guard=deploy_guard.check, call=remote, reload=site_deployment.reload_site,
        verify=site_deployment.verify_site, receipts=RECEIPTS):
    commit = guard(ROOT, [REQUIREMENTS])
    print('Deploy guard passed: requirements.txt from main at', commit[:7], '(clean and matches GitHub).')
    text = (ROOT / REQUIREMENTS).read_text(encoding='utf-8')
    wanted = parse_requirements(text)
    settings = validate(json.loads(SETTINGS.read_text(encoding='utf-8')))
    if settings['username'] != state['username']:
        raise ValueError('API account differs from the selected workflow account.')
    domain = choose_domain(settings, ask)
    print('Reading the packages installed on PythonAnywhere over SSH. SSH may ask for your key passphrase. '
          'Nothing on the server is changed.', flush=True)
    before = call(state['username'], dict(mode='list', virtualenv=VIRTUALENV), 120)
    changes = differences(wanted, before['installed'])
    copy_current = before['copy'] == hashlib.sha256(text.encode('utf-8')).hexdigest()
    if not changes and copy_current:
        print('PythonAnywhere already has every version in requirements.txt. Nothing to do.')
        print(laptop_advice(wanted))
        return
    if changes:
        print(f'{len(changes)} package(s) on PythonAnywhere differ from requirements.txt:')
        print(table(changes))
    else:
        print('Every package already matches; only the live copy of requirements.txt is out of date.')
    print('Typing UPDATE runs pip install in', before['python'].rsplit('/bin/', 1)[0],
          'and copies requirements.txt to the live folder' + (', then reloads https://' + domain if changes else '') + '.')
    if ask('Type UPDATE to continue: ').strip() != 'UPDATE':
        print('Cancelled. Nothing on PythonAnywhere was changed.')
        return
    receipts.mkdir(parents=True, exist_ok=True)
    receipt = receipts / (time.strftime('%Y%m%dT%H%M%S') + '.json')
    record = dict(status='INSTALL_PENDING', commit=commit, domain=domain, requirements=wanted,
                  before=before['installed'], changes=[dict(name=n, before=o, after=v) for n, o, v in changes])
    def save(status, **extra):
        record.update(status=status, **extra)
        receipt.write_text(json.dumps(record, indent=2), encoding='utf-8')
    save('INSTALL_PENDING')
    print('Installing. pip\'s messages follow; this can take a few minutes.', flush=True)
    after = call(state['username'], dict(mode='install', virtualenv=VIRTUALENV, requirements=text), 1200)
    save('INSTALLED', after=after['installed'])
    left = differences(wanted, after['installed'])
    if left:
        save('MISMATCH_AFTER_INSTALL')
        raise RuntimeError('pip finished, but these still differ (receipt ' + str(receipt) + '):\n' + table(left))
    print('Every version in requirements.txt is now installed on PythonAnywhere.')
    if changes:
        save('RELOAD_PENDING')
        reload(settings, domain)
        save('RELOAD_ACKNOWLEDGED')
        verify(domain)
        save('HOMEPAGE_VERIFIED')
        print('Reloaded https://' + domain + '; the homepage answers. Check the admin sign-in and a math page in your browser.')
    else:
        save('COPY_UPDATED')
    print('Receipt:', receipt)
    print(laptop_advice(wanted))
