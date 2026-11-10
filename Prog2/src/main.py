"""Command-line entry point of the dependency visualizer."""

import argparse
import sys
from pathlib import Path

from apt_repository import load_apt
from config import load_config
from graph import build_graph, reverse_graph
from test_repository import load_test
from visualize import ascii_tree, write_visualization

DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "out"


def parse_args():
    """Read the config path and choose how to display the result."""
    parser = argparse.ArgumentParser(description="Граф зависимостей Ubuntu")
    parser.add_argument("config", type=Path, help="файл конфигурации YAML")
    parser.add_argument("--reverse", action="store_true",
                        help="показать обратные зависимости")
    parser.add_argument("--puml-only", action="store_true",
                        help="сохранить PlantUML без рендеринга")
    parser.add_argument("--no-open", action="store_true",
                        help="сохранить PNG без открытия просмотрщика")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT,
                        help="папка для .puml и .png (по умолчанию Prog2/out)")
    return parser.parse_args()


def print_reverse(graph, root):
    """Separate immediate dependents from the rest of the reverse DFS."""
    direct = graph[root]
    transitive = [node for node in graph if node != root and node not in direct]
    for title, nodes in (("Прямые", direct), ("Транзитивные", transitive)):
        print(f"{title}: " + (", ".join(n.label() for n in nodes) or "нет"))


def main():
    """Build the requested graph and output the selected representation."""
    args = parse_args()
    try:
        config = load_config(args.config)
        load_repository = load_test if config.test_mode else load_apt
        root, records, dependencies = load_repository(config)
        if args.reverse:
            graph = reverse_graph(
                root, records, dependencies, config.exclude
            )
            print_reverse(graph, root)
        else:
            graph = build_graph(root, dependencies, config.exclude)
            if config.ascii_tree:
                print(ascii_tree(graph, root))
            write_visualization(
                graph, root, args.output_dir, args.puml_only, args.no_open
            )
    except (OSError, ValueError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
