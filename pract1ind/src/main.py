"""Точка входа консольного эмулятора."""

from shell import default_prompt, repl


def main():
    """Запустить интерактивный диалог."""
    repl(default_prompt())


if __name__ == "__main__":
    main()
