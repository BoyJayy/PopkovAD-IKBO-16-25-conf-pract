"""Точка входа консольного эмулятора."""

from config import parse_config, print_config
from shell import repl
from startup import run_startup


def main(argv=None):
    """Вывести конфигурацию, исполнить скрипт и запустить REPL."""
    config = parse_config(argv)
    prompt = print_config(config)
    if config.startup_script is not None:
        try:
            if not run_startup(config.startup_script, prompt):
                return 0
        except (OSError, UnicodeError) as error:
            print(f"Ошибка чтения скрипта {config.startup_script}: {error}")
            return 1
    repl(prompt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
