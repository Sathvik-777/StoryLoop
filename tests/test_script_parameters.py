import json
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from script_parameters import load_publish_parameter


class ScriptParametersTests(unittest.TestCase):
    def test_publish_parameter_defaults_safely(self):
        cases = [
            ('{"Publish": true}', True),
            ('{"Publish": false}', False),
            ('{"Publish": "true"}', False),
            ('{"Publish": 1}', False),
            ('{"Other": true}', False),
            ("not json", False),
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "script_parameters.json"
            for contents, expected in cases:
                with self.subTest(contents=contents):
                    path.write_text(contents, encoding="utf-8")
                    self.assertIs(load_publish_parameter(path), expected)

    def test_missing_parameters_file_disables_publishing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            self.assertIs(
                load_publish_parameter(Path(temp_dir) / "missing.json"), False
            )
