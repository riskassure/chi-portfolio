from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import math_workflow as workflow


class WorkflowTests(unittest.TestCase):
    def test_stale_package_or_local_edit_blocks(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp) / 'base.db'
            package = Path(temp) / 'package.zip'
            base.write_bytes(b'baseline')
            package.write_bytes(b'package')
            proposed = {'cleaned_tex': 'reviewed'}
            state = dict(base=str(base), base_sha256=workflow.digest(base), working='working.db',
                         job=dict(canonical='Test', package=str(package), sha256=workflow.digest(package), proposed=proposed))
            with patch.object(workflow, 'read_snapshot', return_value={'Test': proposed}):
                self.assertEqual(workflow.current_job(state), state['job'])
            with patch.object(workflow, 'read_snapshot', return_value={'Test': {'cleaned_tex': 'new edit'}}):
                with self.assertRaisesRegex(ValueError, 'Local entry changed'):
                    workflow.current_job(state)
            package.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'package changed'):
                workflow.current_job(state)

    def test_publish_requires_check_and_explicit_confirmation(self):
        job = dict(canonical='Test', remote='remote', checked=False, package='package.zip')
        state = dict(username='cwoo')
        with patch.object(workflow, 'current_job', return_value=job), \
             patch.object(workflow, 'publish_staged') as publish, \
             patch.object(workflow, 'save'):
            with self.assertRaises(ValueError):
                workflow.publish_reviewed(state)
            job['checked'] = True
            with patch('builtins.input', return_value='cancel'):
                workflow.publish_reviewed(state)
            publish.assert_not_called()
            publish.side_effect = RuntimeError('connection lost')
            with patch('builtins.input', return_value='PUBLISH'):
                with self.assertRaises(RuntimeError):
                    workflow.publish_reviewed(state)
            self.assertFalse(job['checked'])

    def test_preflight_conflict_clears_previous_success(self):
        job = dict(remote='remote', checked=True, package='package.zip')
        with patch.object(workflow, 'current_job', return_value=job), \
             patch.object(workflow, 'save'), \
             patch.object(workflow, 'preflight', return_value={'report': 'header\nCONFLICT - newer edit\nnotice\nfooter'}):
            workflow.check_live(dict(username='cwoo'))
        self.assertFalse(job['checked'])

    def test_same_file_cannot_be_baseline_and_working(self):
        with tempfile.TemporaryDirectory() as temp:
            database = Path(temp) / 'test.db'
            database.touch()
            with self.assertRaises(ValueError):
                workflow.configure(database, database)
