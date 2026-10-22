"""List diagram publish journals on the server, or clean up after an interrupted diagram publish.

Runs over SSH like the live preflight. Without --apply nothing changes. With
--apply it removes only SVG files the named publish created that no diagram
row references, plus unfinished incoming folders; files that existed before
that publish are never touched.
"""
import argparse
import json
from pathlib import Path
import re
import shlex
import shutil
import subprocess

from preflight_live_package import MODULES

BOOTSTRAP = '''
import sys, json, types
from pathlib import Path
config = json.load(sys.stdin)
for name, source in config['modules']:
    module = types.ModuleType(name)
    module.__file__ = '<trusted-local-recovery>/' + name + '.py'
    sys.modules[name] = module
    exec(compile(source, module.__file__, 'exec'), module.__dict__)
import diagram_sync
database = Path(config['database'])
journals = database.parents[2] / 'backups' / diagram_sync.JOURNALS
diagrams = database.parent / 'data' / 'math' / 'diagrams'
if config['package'] is None:
    result = []
    for path in sorted(journals.glob('*.json')) if journals.is_dir() else []:
        journal = json.loads(path.read_text(encoding='utf-8'))
        result.append({k: journal.get(k) for k in ('package_sha256', 'canonical', 'status', 'started_utc', 'backup')})
else:
    result = diagram_sync.cleanup(journals / (config['package'] + '.json'), database, diagrams, config['apply'])
print('RECOVERY_RESULT=' + json.dumps(result))
'''


def build_request(username, package, apply):
    if not re.fullmatch(r'[A-Za-z0-9_]+', username):
        raise ValueError('Invalid username.')
    if package is not None and not re.fullmatch(r'[0-9a-f]{64}', package):
        raise ValueError('Give the package SHA-256 exactly as the journal list shows it.')
    if apply and package is None:
        raise ValueError('--apply needs --package.')
    modules = [name for name in MODULES if name in ('preview_math_sync', 'publish_math_entry',
                                                     'apply_math_text_patch', 'diagram_sync')]
    return dict(database=f'/home/{username}/chi-portfolio/backend/portfolio.db', package=package, apply=apply,
                modules=[(name, Path(__file__).with_name(name + '.py').read_text(encoding='utf-8'))
                         for name in modules])


def run(username, package=None, apply=False):
    request = build_request(username, package, apply)
    if not shutil.which('ssh'):
        raise ValueError('Windows OpenSSH Client is required.')
    print('Connecting to the server. SSH may ask for your PythonAnywhere account password.', flush=True)
    command = 'python3.13 -I -B -c ' + shlex.quote(BOOTSTRAP)
    result = subprocess.run(['ssh', username + '@ssh.pythonanywhere.com', command],
                            input=json.dumps(request), stdout=subprocess.PIPE,
                            text=True, encoding='utf-8', check=True)
    lines = [line[len('RECOVERY_RESULT='):] for line in result.stdout.splitlines()
             if line.startswith('RECOVERY_RESULT=')]
    if len(lines) != 1:
        raise ValueError('No unambiguous result received.')
    return json.loads(lines[0])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', help='Package SHA-256 of the publish to clean up (omit to list journals)')
    parser.add_argument('--apply', action='store_true', help='Remove the listed leftovers')
    parser.add_argument('--username', default='cwoo')
    args = parser.parse_args()
    try:
        print(json.dumps(run(args.username, args.package, args.apply), indent=2))
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        raise SystemExit('Recovery stopped; nothing changed. ' +
                         (str(error) if isinstance(error, ValueError) else 'Check the connection.'))
