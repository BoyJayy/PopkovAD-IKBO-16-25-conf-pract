"""Cover recursive traversal, filtering and Debian dependency resolution."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from apt_index import Package
from apt_repository import AptRepository
from apt_version import compare_versions
from config import load_config
from graph import Node, build_graph
from test_repository import load_test, parse_graph


class GraphTests(unittest.TestCase):
    def test_dfs_preserves_cycle_and_visits_shared_target_once(self):
        config = load_config(ROOT / "examples/test.yaml")
        root, _, dependencies = load_test(config)
        graph = build_graph(root, dependencies, config.exclude)
        self.assertEqual([node.name for node in graph], ["A", "B", "D", "C"])
        by_name = {
            node.name: [target.name for target in children]
            for node, children in graph.items()
        }
        self.assertEqual(by_name, {
            "A": ["B", "C"], "B": ["D"], "D": ["A"], "C": ["D"]
        })

    def test_undefined_and_duplicate_test_vertices(self):
        for text in ("A: B", "A:\nA:"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_graph(text)

    def test_single_isolated_package_and_excluded_root(self):
        root = Node("A", "1.0")
        self.assertEqual(build_graph(root, lambda node: (), ""), {root: ()})
        with self.assertRaisesRegex(ValueError, "exclude"):
            build_graph(root, lambda node: (), "A")

    def test_apt_keeps_eligible_alternatives_and_versioned_providers(self):
        def record(name, version, depends="", provides=""):
            return Package(name, version, "amd64", "", depends, provides)

        repository = AptRepository([
            record("demo", "1.0", "liba (<< 2) | virt (>= 2), foreign:arm64"),
            record("liba", "2.0"), record("liba", "1.8"), record("liba", "1.9"),
            record("provider", "5", provides="virt (= 2)"),
            record("other", "6", provides="virt"),
            record("foreign", "1"),
        ])
        self.assertEqual(repository.dependencies(Node("demo", "1.0")), (
            Node("liba", "1.9"), Node("provider", "5"), Node("foreign", None)
        ))

    def test_debian_versions(self):
        for left, right in (
            ("1.0~rc1", "1.0"), ("1.0", "1.0+git"),
            ("1.09", "1.10"), ("1.0-2", "1.0-10"), ("9.0", "1:1.0"),
        ):
            self.assertLess(compare_versions(left, right), 0)
            self.assertGreater(compare_versions(right, left), 0)
        self.assertEqual(compare_versions("1.0-00", "0:1.0"), 0)
