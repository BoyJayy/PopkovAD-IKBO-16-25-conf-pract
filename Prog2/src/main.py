"""Command-line entry point of the dependency visualizer."""

import argparse
import sys
from pathlib import Path

from apt_index import download_index, exact_package
from config import load_config


def main():
    """Show the mandatory direct dependencies of the exact package version."""
    parser = argparse.ArgumentParser(description="Граф зависимостей Ubuntu")
    parser.add_argument("config", type=Path, help="файл конфигурации YAML")
    args = parser.parse_args()
    try:
        config = load_config(args.config)
        if config.test_mode:
            raise ValueError("Тестовый репозиторий появится на этапе 3")
        packages = download_index(config.repository)
        root = exact_package(packages, config.package, config.version)
        print(f"{root.name}={root.version}")
        for line in root.direct_lines():
            print(line)
        if not (root.pre_depends or root.depends):
            print("Нет обязательных зависимостей")
    except (OSError, ValueError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
