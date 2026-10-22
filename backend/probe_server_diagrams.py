"""Check, read-only, whether the server can render PSTricks diagrams. Nothing on the site changes.

The check runs over SSH like the live preflight. It renders two fixed samples and
one stored live diagram in a new folder under the server's temporary directory,
then removes that folder. The database is opened read-only, the diagrams folder
is only read, and the site is never reloaded.
"""
import argparse
import json
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))
from database.math.pipeline.step2_build_diagrams import wrap_pstricks_document

PLACEHOLDER = '@@PSTRICKS_BLOCK@@'
PACKAGES = ('pstricks.sty', 'pst-tree.sty', 'pst-plot.sty', 'pst-node.sty', 'multido.sty')
SAMPLES = (
    ('pspicture', '\\psset{unit=1cm}\n\\begin{pspicture}(0,0)(2,2)\n'
                  '\\psline(0,0)(2,2)\n\\pscircle(1,1){0.5}\n\\end{pspicture}'),
    ('pstree', '\\pstree{\\TR{$a$}}{\\TR{$b$} \\TR{$c$}}'),
)

BOOTSTRAP = r'''
import hashlib, json, os, re, shutil, sqlite3, subprocess, sys, tempfile
from pathlib import Path
config = json.load(sys.stdin)
result = {'tools': {}, 'packages': {}, 'samples': [], 'live_comparison': None}

def first_line(command):
    try:
        output = subprocess.run(command, capture_output=True, text=True, timeout=60)
        return (output.stdout or output.stderr).strip().splitlines()[0][:200]
    except (OSError, subprocess.SubprocessError, IndexError):
        return None

for tool in ('latex', 'dvisvgm', 'kpsewhich'):
    path = shutil.which(tool)
    result['tools'][tool] = {'path': path, 'version': first_line([path, '--version']) if path else None}
for package in config['packages']:
    found = first_line([result['tools']['kpsewhich']['path'], package]) if result['tools']['kpsewhich']['path'] else None
    result['packages'][package] = bool(found)

def render(folder, name, source):
    document = config['wrapper'].replace(config['placeholder'], source)
    work = folder / name
    work.mkdir()
    (work / 'diagram.tex').write_text(document, encoding='utf-8')
    for stage, command in (('latex', ['latex', '-interaction=nonstopmode', 'diagram.tex']),
                           ('dvisvgm', ['dvisvgm', 'diagram.dvi', '-o', 'diagram.svg'])):
        if not result['tools'][stage]['path']:
            return {'name': name, 'ok': False, 'stage': stage, 'error': stage + ' is not installed'}
        try:
            output = subprocess.run(command, cwd=work, capture_output=True, text=True, timeout=120)
        except (OSError, subprocess.SubprocessError) as error:
            return {'name': name, 'ok': False, 'stage': stage, 'error': str(error)[-1500:]}
        if output.returncode:
            return {'name': name, 'ok': False, 'stage': stage,
                    'error': ((output.stdout or '') + (output.stderr or ''))[-1500:]}
    svg = (work / 'diagram.svg').read_bytes()
    return {'name': name, 'ok': svg.lstrip().startswith((b'<?xml', b'<svg')) and b'<svg' in svg,
            'stage': 'done', 'bytes': len(svg), 'sha256': hashlib.sha256(svg).hexdigest()}

folder = Path(tempfile.mkdtemp(prefix='chi-diagram-probe-'))
try:
    for name, source in config['samples']:
        result['samples'].append(render(folder, name, source))
    database = Path(config['database'])
    if database.is_file():
        db = sqlite3.connect(database.resolve().as_uri() + '?mode=ro', uri=True)
        try:
            row = db.execute("SELECT source_hash, source_tex, svg_path FROM math_concept_diagrams "
                             "WHERE svg_path LIKE '/api/math/diagrams/%' ORDER BY id LIMIT 1").fetchone()
        except sqlite3.Error:
            row = None
        finally:
            db.close()
        if row:
            filename = row[2].rsplit('/', 1)[-1]
            stored = Path(config['diagrams']) / filename
            comparison = {'source_hash': row[0], 'stored_file': filename}
            if re.fullmatch(r'[0-9a-f]{16}\.svg', filename) and stored.is_file():
                live = stored.read_bytes()
                rendered = render(folder, 'live-sample', row[1])
                comparison.update(rendered=rendered, stored_sha256=hashlib.sha256(live).hexdigest(),
                                  identical=rendered.get('sha256') == hashlib.sha256(live).hexdigest())
            else:
                comparison['error'] = 'Stored SVG not found or has an unexpected name.'
            result['live_comparison'] = comparison
finally:
    shutil.rmtree(folder, ignore_errors=True)
    result['temp_removed'] = not folder.exists()
print('PROBE_RESULT=' + json.dumps(result))
'''


def build_request(username):
    if not re.fullmatch(r'[A-Za-z0-9_]+', username):
        raise ValueError('Invalid username.')
    root = f'/home/{username}/chi-portfolio/backend'
    return dict(wrapper=wrap_pstricks_document(PLACEHOLDER), placeholder=PLACEHOLDER,
                samples=[list(sample) for sample in SAMPLES], packages=list(PACKAGES),
                database=root + '/portfolio.db', diagrams=root + '/data/math/diagrams')


def summarize(result):
    """Return the report text; its first line is the verdict."""
    samples = result['samples']
    can_render = bool(samples) and all(sample['ok'] for sample in samples)
    lines = ['SERVER CAN RENDER PSTRICKS' if can_render else 'SERVER CANNOT RENDER PSTRICKS', '']
    for tool, info in result['tools'].items():
        lines.append(f"{tool}: {info['path'] or 'not found'}" + (f" ({info['version']})" if info['version'] else ''))
    lines += [f"{package}: {'found' if found else 'not found'}" for package, found in result['packages'].items()]
    for sample in samples:
        lines.append(f"Sample {sample['name']}: " + ('rendered, ' + str(sample['bytes']) + ' bytes' if sample['ok']
                                                     else 'failed at ' + sample['stage']))
        if not sample['ok'] and sample.get('error'):
            lines += ['  ' + line for line in sample['error'].splitlines()[-15:]]
    comparison = result.get('live_comparison')
    if comparison is None:
        lines.append('Live comparison: no stored diagram found to compare.')
    elif 'error' in comparison:
        lines.append('Live comparison: ' + comparison['error'])
    elif not comparison['rendered']['ok']:
        lines.append(f"Live comparison: rendering {comparison['stored_file']} failed at {comparison['rendered']['stage']}.")
    else:
        lines.append(f"Live comparison: server rendering of {comparison['stored_file']} is " +
                     ('byte-identical to the stored SVG.' if comparison['identical'] else
                      'a valid SVG but differs in bytes from the stored SVG.'))
    lines += ['', 'Temporary folder removed.' if result.get('temp_removed') else
              'WARNING: the temporary folder under the server temp directory could not be removed.',
              'Read-only: the database, the diagrams folder and the website were not changed.']
    return '\n'.join(lines)


def probe(username, output):
    if output.exists():
        raise ValueError('Report already exists. Choose a new output filename.')
    if not output.parent.is_dir():
        raise ValueError('The report directory must already exist.')
    request = build_request(username)
    if not shutil.which('ssh'):
        raise ValueError('Windows OpenSSH Client is required.')
    print('Checking server diagram rendering. SSH may ask for your PythonAnywhere account password.', flush=True)
    command = 'python3.13 -I -B -c ' + shlex.quote(BOOTSTRAP)
    result = subprocess.run(['ssh', username + '@ssh.pythonanywhere.com', command],
                            input=json.dumps(request), stdout=subprocess.PIPE,
                            text=True, encoding='utf-8', check=True)
    lines = [line[len('PROBE_RESULT='):] for line in result.stdout.splitlines()
             if line.startswith('PROBE_RESULT=')]
    if len(lines) != 1:
        raise ValueError('No unambiguous probe result received.')
    report = summarize(json.loads(lines[0]))
    with output.open('x', encoding='utf-8') as stream:
        stream.write(report + '\n')
    print(report)
    print('Report saved:', output.resolve())
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New report filename')
    parser.add_argument('--username', default='cwoo')
    args = parser.parse_args()
    try:
        probe(args.username, args.output)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        raise SystemExit('Probe failed; nothing changed. ' +
                         (str(error) if isinstance(error, ValueError) else 'Check the connection and path.'))
