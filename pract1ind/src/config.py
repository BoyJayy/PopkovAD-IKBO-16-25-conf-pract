"""Параметры запуска и отладочный вывод конфигурации."""

import argparse
import json

from shell import default_prompt


def parse_config(argv=None):
    """Прочитать путь VFS, приглашение и путь стартового скрипта."""
    parser = argparse.ArgumentParser(
        description="Эмулятор оболочки: вариант 19, этапы 1 и 2")
    parser.add_argument("--vfs", metavar="PATH",
                        help="путь VFS (на этапе 2 только сохраняется)")
    parser.add_argument("--prompt", metavar="TEXT",
                        help="пользовательское приглашение к вводу")
    parser.add_argument("--startup-script", metavar="PATH",
                        help="путь к стартовому скрипту в UTF-8")
    return parser.parse_args(argv)


def print_config(config, write=print):
    """Показать все заданные параметры и итоговое приглашение."""
    effective_prompt = (default_prompt() if config.prompt is None
                        else config.prompt)
    values = {"vfs": config.vfs, "prompt": config.prompt,
              "startup_script": config.startup_script,
              "effective_prompt": effective_prompt}
    write("[config] " + json.dumps(values, ensure_ascii=False))
    return effective_prompt
