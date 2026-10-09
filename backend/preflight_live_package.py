"""Check a staged package against the live database via SSH, without applying it."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shlex
import shutil
import subprocess

from stage_pythonanywhere_package import read_package

# Only these local, reviewed modules are sent. Scripts inside the ZIP are never run.
MODULES = ('pythonanywhere_api', 'stage_pythonanywhere_package', 'preview_math_sync',
           'publish_math_entry', 'apply_math_text_patch', 'inspect_staged_package')
BOOTSTRAP = '''
import sys, json, types, hashlib
from pathlib import Path
from datetime import datetime, timezone
config = json.load(sys.stdin)
for name, source in config['modules']:
    module = types.ModuleType(name)
    module.__file__ = '<trusted-local-preflight>/' + name + '.py'
    sys.modules[name] = module
    exec(compile(source, module.__file__, 'exec'), module.__dict__)
from stage_pythonanywhere_package import read_package
from inspect_staged_package import preview
data = read_package(Path(config['remote']))
if hashlib.sha256(data).hexdigest() != config['sha256']:
    raise SystemExit('Staged ZIP differs from the reviewed local ZIP. Preflight stopped.')
report = preview(data, Path(config['database']), live=True)
print('PREFLIGHT_RESULT=' + json.dumps({
    'checked_utc': datetime.now(timezone.utc).isoformat(),
    'sha256': config['sha256'], 'report': report
}))
'''


def build_request(username, remote, local):
    if not re.fullmatch(r'[A-Za-z0-9_]+', username):
        raise ValueError('Invalid username.')
    if not re.fullmatch(re.escape(f'/home/{username}/chi-portfolio-staging/') +
                        r'[0-9a-f]{32}/package\.zip', remote):
        raise ValueError('Use the exact private staging path from the uploader.')
    data = read_package(local)
    return dict(remote=remote, sha256=hashlib.sha256(data).hexdigest(),
                database=f'/home/{username}/chi-portfolio/backend/portfolio.db',
                modules=[(name, Path(__file__).with_name(name + '.py').read_text(encoding='utf-8'))
                         for name in MODULES])


def preflight(username, remote, local, output):
    if output.exists():
        raise ValueError('Report already exists. Choose a new output filename.')
    if not output.parent.is_dir():
        raise ValueError('The report directory must already exist.')
    request = build_request(username, remote, local)
    if not shutil.which('ssh'):
        raise ValueError('Windows OpenSSH Client is required.')
    print('Checking the live database read-only. SSH may ask for your PythonAnywhere account password.', flush=True)
    # -I avoids imports from the host working directory; -B prevents bytecode files.
    command = 'python3.13 -I -B -c ' + shlex.quote(BOOTSTRAP)
    result = subprocess.run(['ssh', username + '@ssh.pythonanywhere.com', command],
                            input=json.dumps(request), stdout=subprocess.PIPE,
                            text=True, encoding='utf-8', check=True)
    lines = [line[len('PREFLIGHT_RESULT='):] for line in result.stdout.splitlines()
             if line.startswith('PREFLIGHT_RESULT=')]
    if len(lines) != 1:
        raise ValueError('No unambiguous preflight result received; nothing approved.')
    response = json.loads(lines[0])
    if response.get('sha256') != request['sha256'] or not isinstance(response.get('report'), str):
        raise ValueError('Invalid preflight response; nothing approved.')
    with output.open('x', encoding='utf-8') as stream:
        stream.write('Live preflight at ' + response['checked_utc'] + '\n' + response['report'] + '\n')
    print('Live preflight complete. Read:', output.resolve())
    print('No package code executed and no database updates or reloads performed.')
    return response


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('remote')
    parser.add_argument('--local', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--username', default='cwoo')
    args = parser.parse_args()
    try:
        preflight(args.username, args.remote, args.local, args.output)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        raise SystemExit('Preflight failed; nothing approved. ' +
                         (str(error) if isinstance(error, ValueError) else 'Check the connection and file paths.'))
