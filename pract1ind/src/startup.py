"""Последовательное выполнение стартового скрипта."""

from pathlib import Path

from shell import execute


def run_startup(path, prompt, write=print):
    """Показать диалог; пропустить ошибочные строки; учесть exit."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    for number, line in enumerate(lines, start=1):
        write(prompt + line)
        try:
            if not execute(line, write):
                return False
        except ValueError as error:
            write(f"Ошибка в скрипте {path}, строка {number}: {error}")
    return True
