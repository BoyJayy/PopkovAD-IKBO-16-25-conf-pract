"""Check validation of every configurable option."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from config import load_config, validate


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.path = Path(__file__).resolve().parents[1] / "examples/mawk.yaml"
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

    def test_invalid_options(self):
        invalid = {
            "package": "Mawk",
            "repository": "file:///tmp/Packages.gz",
            "test_mode": "true",
            "version": 1,
            "ascii_tree": 1,
            "exclude": [],
        }
        for key, value in invalid.items():
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, key):
                validate(self.options | {key: value}, self.path)

    def test_test_file_is_relative_to_yaml(self):
        options = self.options | {
            "test_mode": True, "package": "A", "repository": "mawk.yaml"
        }
        self.assertEqual(validate(options, self.path).repository, str(self.path))
        with self.assertRaisesRegex(ValueError, "repository"):
            validate(options | {"repository": "missing.yaml"}, self.path)
