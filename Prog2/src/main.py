"""Command-line entry point of the dependency visualizer."""

import argparse
import sys
from dataclasses import asdict
from pathlib import Path

from config import load_config


def main():
    """Validate settings and show them in key-value format."""
    parser = argparse.ArgumentParser(description="Граф зависимостей Ubuntu")
    parser.add_argument("config", type=Path, help="файл конфигурации YAML")
    args = parser.parse_args()
    try:
        config = load_config(args.config)
        for key, value in asdict(config).items():
            print(f"{key}: {value}")
    except (OSError, ValueError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
