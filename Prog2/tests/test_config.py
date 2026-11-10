"""Check validation of every configurable option."""

import re
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from config import load_config, validate


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.path = ROOT / "examples/mawk.yaml"
        self.options = {
            "package": "mawk",
            "repository": "https://example.test/Packages.gz",
            "test_mode": False,
            "version": "1:1.0-2",
            "ascii_tree": True,
            "exclude": "",
        }

    def test_example(self):
        self.assertEqual(load_config(self.path).package, "mawk")

    def test_cli_rejects_each_invalid_option(self):
        invalid = {
            "package": "Mawk",
            "repository": "file:///tmp/Packages.gz",
            "test_mode": '"true"',
            "version": "1",
            "ascii_tree": "1",
            "exclude": "[]",
        }
        valid_yaml = self.path.read_text()
        with TemporaryDirectory() as directory:
            path = Path(directory) / "config.yaml"
            for key, value in invalid.items():
                with self.subTest(key=key):
                    text = re.sub(rf"^{key}: .+$", f"{key}: {value}",
                                  valid_yaml, flags=re.MULTILINE)
                    path.write_text(text)
                    result = subprocess.run(
                        [sys.executable, str(ROOT / "src/main.py"), str(path)],
                        capture_output=True, text=True, check=False, timeout=10,
                    )
                    self.assertEqual(result.returncode, 1)
                    self.assertIn(key, result.stderr)
                    self.assertEqual(result.stdout, "")

    def test_duplicate_yaml_key_is_rejected(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "config.yaml"
            path.write_text(self.path.read_text() + "package: grep\n")
            with self.assertRaisesRegex(ValueError, "повтор ключа package"):
                load_config(path)

    def test_test_file_is_relative_to_yaml(self):
        options = self.options | {
            "test_mode": True, "package": "A", "repository": "mawk.yaml"
        }
        validated = validate(options, self.path)
        self.assertEqual(validated.repository, str(self.path))
        with self.assertRaisesRegex(ValueError, "repository"):
            validate(options | {"repository": "missing.yaml"}, self.path)
