"""Explicitly publish one reviewed staged math package after a live preflight."""
import argparse
import json
from pathlib import Path
import shlex
import shutil
import subprocess

from preflight_live_package import build_request

BOOTSTRAP = '''
import sys, json, types, hashlib, os
from pathlib import Path
from datetime import datetime, timezone
os.umask(0o077)
config = json.load(sys.stdin)
for name, source in config['modules']:
    module = types.ModuleType(name)
    module.__file__ = '<trusted-local-publisher>/' + name + '.py'
    sys.modules[name] = module
    exec(compile(source, module.__file__, 'exec'), module.__dict__)
from stage_pythonanywhere_package import read_package
from live_math_publication import publish
data = read_package(Path(config['remote']))
if hashlib.sha256(data).hexdigest() != config['sha256']:
    raise SystemExit('Staged ZIP differs from reviewed package. Nothing applied.')
database = Path(config['database'])
result = publish(data, database, database.parents[2] / 'backups', database.parent / 'src')
result.update(sha256=config['sha256'], completed_utc=datetime.now(timezone.utc).isoformat())
print('PUBLICATION_RESULT=' + json.dumps(result))
'''


def publish_staged(username, remote, local, output):
    if output.exists() or not output.parent.is_dir():
        raise ValueError('Choose a new receipt filename in an existing directory.')
    request = build_request(username, remote, local)
    for name in ('live_math_publication',):
        request['modules'].append((name, Path(__file__).with_name(name + '.py').read_text(encoding='utf-8')))
    if not shutil.which('ssh'):
        raise ValueError('Windows OpenSSH Client is required.')
    # Reserve a receipt before networking. An interrupted attempt retains its digest.
    receipt = dict(status='PENDING', remote=remote, sha256=request['sha256'])
    with output.open('x', encoding='utf-8') as stream:
        json.dump(receipt, stream, indent=2)
    print('Publishing selected math update. SSH may ask for your PythonAnywhere account password.', flush=True)
    executable = f'/home/{username}/.virtualenvs/chi-portfolio/bin/python'
    command = shlex.quote(executable) + ' -I -B -c ' + shlex.quote(BOOTSTRAP)
    try:
        result = subprocess.run(['ssh', username + '@ssh.pythonanywhere.com', command],
                                input=json.dumps(request), stdout=subprocess.PIPE,
                                text=True, encoding='utf-8', check=True)
        lines = [line[len('PUBLICATION_RESULT='):] for line in result.stdout.splitlines()
                 if line.startswith('PUBLICATION_RESULT=')]
        if len(lines) != 1:
            raise ValueError('No unambiguous publication result received.')
        response = json.loads(lines[0])
        if response.get('sha256') != request['sha256'] or response.get('status') not in ('APPLIED', 'ALREADY_PRESENT'):
            raise ValueError('Unexpected publication result.')
        receipt.update(response)
        output.write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    except (OSError, ValueError, subprocess.CalledProcessError, KeyboardInterrupt):
        raise RuntimeError('Publication result is unconfirmed. Keep the pending receipt and run live preflight before retrying; the server may have completed the update.') from None
    print(response['status'] + ': ' + response['canonical'])
    if response.get('backup'):
        print('Verified backup:', response['backup'])
    print('Receipt:', output.resolve())
    return response


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('remote')
    parser.add_argument('--local', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--username', default='cwoo')
    parser.add_argument('--apply', action='store_true', required=True,
                        help='Explicitly apply this reviewed package; existing identical content is skipped')
    args = parser.parse_args()
    try:
        publish_staged(args.username, args.remote, args.local, args.output)
    except (ValueError, RuntimeError, OSError) as error:
        raise SystemExit(str(error))
