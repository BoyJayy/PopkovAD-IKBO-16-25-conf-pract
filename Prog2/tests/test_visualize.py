"""Check visualization formatting and the CLI output modes."""

import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from graph import Node
from visualize import ascii_tree, plantuml


class VisualizeTests(unittest.TestCase):
    def test_cycle_and_shared_node_in_both_formats(self):
        a, b, c = [Node(name, "1.0") for name in "ABC"]
        graph = {a: (b, c), b: (a, c), c: ()}
        self.assertEqual(ascii_tree(graph, a), "\n".join((
            "A=1.0", "+-- B=1.0", "|   +-- A=1.0 [cycle]",
            "|   \\-- C=1.0", "\\-- C=1.0 [seen]",
        )))
        source = plantuml(graph, a)
        self.assertEqual(source.count('rectangle "C=1.0"'), 1)
        self.assertIn("p1 --> p0", source)
        self.assertIn("p0 --> p2", source)

    def test_cli_can_save_puml_without_renderer(self):
        with TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(ROOT / "src/main.py"),
                 str(ROOT / "examples/test.yaml"), "--puml-only",
                 "--output-dir", directory],
                capture_output=True, text=True, check=True, timeout=10,
            )
            path = Path(directory) / "A.puml"
            self.assertTrue(path.read_text().startswith("@startuml\n"))
            self.assertFalse(path.with_suffix(".png").exists())
            self.assertIn("[cycle]", result.stdout)

    def test_cli_reverse_reports_direct_and_transitive(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "src/main.py"),
             str(ROOT / "examples/test.yaml"), "--reverse"],
            capture_output=True, text=True, check=True, timeout=10,
        )
        self.assertIn("Прямые: D=1.0, TOP=1.0", result.stdout)
        self.assertIn("Транзитивные: B=1.0, C=1.0", result.stdout)
