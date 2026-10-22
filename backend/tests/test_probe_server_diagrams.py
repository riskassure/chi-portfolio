import hashlib
import json
import os
from pathlib import Path
import sqlite3
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from probe_server_diagrams import BOOTSTRAP, build_request, probe, summarize

FAKE_SVG = '<?xml version="1.0"?>\n<svg xmlns="http://www.w3.org/2000/svg"></svg>\n'
# Stand-ins for the TeX tools: latex writes a .dvi, dvisvgm writes FAKE_SVG to its -o target.
FAKE_LATEX = '#!/bin/sh\n[ "$1" = --version ] && { echo "pdfTeX 3.14 (fake)"; exit 0; }\nprintf dvi > diagram.dvi\n'
FAKE_DVISVGM = ('#!/bin/sh\n[ "$1" = --version ] && { echo "dvisvgm 3.0 (fake)"; exit 0; }\n'
                'printf \'' + FAKE_SVG.replace('\n', '\\n') + '\' > "$3"\n')
FAILING_LATEX = '#!/bin/sh\n[ "$1" = --version ] && { echo "pdfTeX (fake)"; exit 0; }\necho "! LaTeX Error: File pstricks.sty not found."\nexit 1\n'
FAKE_KPSEWHICH = '#!/bin/sh\n[ "$1" = --version ] && { echo "kpathsea (fake)"; exit 0; }\n[ "$1" = multido.sty ] && exit 1\necho /texmf/$1\n'


class ServerProbeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.server_tmp = self.root / 'server-tmp'
        self.server_tmp.mkdir()
        self.diagrams = self.root / 'diagrams'
        self.diagrams.mkdir()
        self.database = self.root / 'portfolio.db'
        with sqlite3.connect(self.database) as db:
            db.execute('CREATE TABLE math_concept_diagrams(id INTEGER PRIMARY KEY, concept_id INTEGER, block_index INTEGER, '
                       'source_hash TEXT, source_tex TEXT, svg_path TEXT, created_at TEXT)')
            db.execute("INSERT INTO math_concept_diagrams VALUES(1,1,1,'0123456789abcdef',"
                       "'\\begin{pspicture}(1,1)\\end{pspicture}','/api/math/diagrams/0123456789abcdef.svg','now')")
        db.close()
        (self.diagrams / '0123456789abcdef.svg').write_text(FAKE_SVG)

    def tearDown(self):
        self.temp.cleanup()

    def tool(self, name, script):
        path = self.bin / name
        path.write_text(script)
        path.chmod(path.stat().st_mode | stat.S_IEXEC)

    def run_probe(self):
        request = build_request('cwoo')
        request.update(database=str(self.database), diagrams=str(self.diagrams))
        before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in (self.database, *self.diagrams.iterdir())}
        environment = dict(os.environ, PATH=str(self.bin) + ':/usr/bin:/bin', TMPDIR=str(self.server_tmp))
        result = subprocess.run([sys.executable, '-I', '-B', '-c', BOOTSTRAP], input=json.dumps(request),
                                capture_output=True, text=True, env=environment)
        self.assertEqual(result.returncode, 0, result.stderr)
        # Read-only: database and diagrams unchanged, and the throwaway folder is gone.
        self.assertEqual(before, {p: hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in (self.database, *self.diagrams.iterdir())})
        self.assertEqual(list(self.server_tmp.iterdir()), [])
        return json.loads(result.stdout.split('PROBE_RESULT=')[1])

    @unittest.skipIf(sys.platform == 'win32', 'shell stand-ins for TeX tools')
    def test_missing_tools_reported_as_cannot_render(self):
        result = self.run_probe()
        self.assertIsNone(result['tools']['latex']['path'])
        self.assertFalse(any(sample['ok'] for sample in result['samples']))
        report = summarize(result)
        self.assertTrue(report.startswith('SERVER CANNOT RENDER PSTRICKS'))
        self.assertIn('latex: not found', report)

    @unittest.skipIf(sys.platform == 'win32', 'shell stand-ins for TeX tools')
    def test_working_tools_render_samples_and_compare_live_file(self):
        self.tool('latex', FAKE_LATEX)
        self.tool('dvisvgm', FAKE_DVISVGM)
        self.tool('kpsewhich', FAKE_KPSEWHICH)
        result = self.run_probe()
        self.assertEqual([s['name'] for s in result['samples']], ['pspicture', 'pstree'])
        self.assertTrue(all(sample['ok'] for sample in result['samples']))
        self.assertTrue(result['packages']['pstricks.sty'])
        self.assertFalse(result['packages']['multido.sty'])
        self.assertTrue(result['live_comparison']['identical'])
        report = summarize(result)
        self.assertTrue(report.startswith('SERVER CAN RENDER PSTRICKS'))
        self.assertIn('multido.sty: not found', report)
        self.assertIn('byte-identical', report)

    @unittest.skipIf(sys.platform == 'win32', 'shell stand-ins for TeX tools')
    def test_different_bytes_and_latex_errors_reported(self):
        self.tool('latex', FAKE_LATEX)
        self.tool('dvisvgm', FAKE_DVISVGM)
        (self.diagrams / '0123456789abcdef.svg').write_text(FAKE_SVG.replace('<svg ', '<svg width="1" '))
        self.assertIn('differs in bytes', summarize(self.run_probe()))
        self.tool('latex', FAILING_LATEX)
        result = self.run_probe()
        self.assertEqual(result['samples'][0]['stage'], 'latex')
        report = summarize(result)
        self.assertTrue(report.startswith('SERVER CANNOT RENDER PSTRICKS'))
        self.assertIn('pstricks.sty not found', report)

    @unittest.skipIf(sys.platform == 'win32', 'shell stand-ins for TeX tools')
    def test_unexpected_stored_filename_is_never_read(self):
        with sqlite3.connect(self.database) as db:
            db.execute("UPDATE math_concept_diagrams SET svg_path='/api/math/diagrams/../../portfolio.db'")
        db.close()
        self.assertIn('unexpected name', summarize(self.run_probe()))

    def test_request_uses_site_wrapper_and_live_paths(self):
        request = build_request('cwoo')
        self.assertIn('\\usepackage{pst-tree}', request['wrapper'])
        self.assertEqual(request['wrapper'].count(request['placeholder']), 1)
        self.assertEqual(request['database'], '/home/cwoo/chi-portfolio/backend/portfolio.db')
        self.assertEqual(request['diagrams'], '/home/cwoo/chi-portfolio/backend/data/math/diagrams')
        with self.assertRaises(ValueError):
            build_request('cwoo; rm -rf ~')

    def test_existing_report_refused_before_ssh(self):
        output = self.root / 'report.txt'
        output.write_text('Keep this report')
        with patch('probe_server_diagrams.subprocess.run') as run:
            with self.assertRaises(ValueError):
                probe('cwoo', output)
            run.assert_not_called()
        self.assertEqual(output.read_text(), 'Keep this report')

    def test_probe_saves_report_from_single_result_line(self):
        output = self.root / 'report.txt'
        result = dict(tools={'latex': {'path': None, 'version': None}}, packages={}, samples=[],
                      live_comparison=None, temp_removed=True)
        completed = subprocess.CompletedProcess([], 0, stdout='banner\nPROBE_RESULT=' + json.dumps(result) + '\n')
        with patch('probe_server_diagrams.shutil.which', return_value='/usr/bin/ssh'), \
             patch('probe_server_diagrams.subprocess.run', return_value=completed):
            probe('cwoo', output)
        self.assertTrue(output.read_text().startswith('SERVER CANNOT RENDER PSTRICKS'))
        completed.stdout = ''
        with patch('probe_server_diagrams.shutil.which', return_value='/usr/bin/ssh'), \
             patch('probe_server_diagrams.subprocess.run', return_value=completed):
            with self.assertRaises(ValueError):
                probe('cwoo', self.root / 'second.txt')
        self.assertFalse((self.root / 'second.txt').exists())


if __name__ == '__main__':
    unittest.main()
