import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from reconstruct import build_command

class RebuildTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.p=Path(t.name)
        for name in ('Original','Source','Analysis','Reconstructed'):
            (self.p/name).mkdir()
        (self.p/'Original'/'app.exe').write_bytes(b'original')
        self.report=self.p/'Analysis'/'report.json'
        self.report.write_text(json.dumps({'status':'inspection complete; source reconstruction and behavioral validation not performed'}))
    def test_command_uses_preserved_copy_and_separate_project(self):
        with patch('reconstruct.locate',return_value='craft-anything-cli'), patch('reconstruct.tool_command',return_value=['craft-anything-cli']):
            args=build_command(self.p)
        self.assertEqual(args[:4],['craft-anything-cli','--deep','rebuild',str(self.p/'Original'/'app.exe')])
        self.assertEqual(args[args.index('--project-folder')+1],str(self.p/'Reconstructed'/'CraftProject'))
        self.assertNotIn('--unattended',args)
        self.assertIn(str(self.report),args[4])
    def test_reject_partial(self):
        self.report.write_text(json.dumps({'status':'partial'}))
        with self.assertRaises(ValueError):build_command(self.p)
    def test_no_overwrite(self):
        (self.p/'Reconstructed'/'CraftProject').mkdir()
        with self.assertRaises(ValueError):build_command(self.p)
