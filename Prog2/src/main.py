"""Command-line entry point of the dependency visualizer."""

import argparse
import sys
from pathlib import Path

from apt_repository import load_apt
from config import load_config
from graph import build_graph
from test_repository import load_test


def main():
    """Print the transitively reachable adjacency list."""
    parser = argparse.ArgumentParser(description="Граф зависимостей Ubuntu")
    parser.add_argument("config", type=Path, help="файл конфигурации YAML")
    args = parser.parse_args()
    try:
        config = load_config(args.config)
        load_repository = load_test if config.test_mode else load_apt
        root, _, dependencies = load_repository(config)
        graph = build_graph(root, dependencies, config.exclude)
        for node, children in graph.items():
            print(f"{node.label()}: " + ", ".join(c.label() for c in children))
    except (OSError, ValueError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
