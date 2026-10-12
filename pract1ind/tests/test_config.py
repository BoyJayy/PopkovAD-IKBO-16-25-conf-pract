"""Проверки конфигурации и стартовых скриптов через CLI."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from config import parse_config, print_config


PROJECT_DIR = Path(__file__).resolve().parents[1]


def launch(*arguments, input_text=""):
    """Запустить эмулятор в отдельном процессе с заданным вводом."""
    return subprocess.run(
        [sys.executable, str(PROJECT_DIR / "src/main.py"), *arguments],
        input=input_text, capture_output=True, text=True, timeout=5)


class ConfigTests(unittest.TestCase):
    """Параметры сохраняются, выводятся и применяются в REPL."""

    def test_all_parameters(self):
        """Проверить все параметры и их отладочный вывод."""
        config = parse_config(["--vfs", "путь с пробелом", "--prompt", "> ",
                               "--startup-script", "commands.txt"])
        output = []
        self.assertEqual(print_config(config, output.append), "> ")
        data = json.loads(output[0].removeprefix("[config] "))
        self.assertEqual(data, {"vfs": "путь с пробелом", "prompt": "> ",
                               "startup_script": "commands.txt",
                               "effective_prompt": "> "})

    def test_defaults(self):
        """Отсутствующие параметры показываются как null."""
        output = []
        prompt = print_config(parse_config([]), output.append)
        data = json.loads(output[0].removeprefix("[config] "))
        self.assertIsNone(data["vfs"])
        self.assertIsNone(data["prompt"])
        self.assertIsNone(data["startup_script"])
        self.assertIn("@", prompt)

    def test_custom_and_empty_prompt(self):
        """Пользовательское приглашение применяется и может быть пустым."""
        for prompt in ["custom$ ", ""]:
            result = launch("--prompt", prompt, input_text="ls\nexit\n")
            self.assertEqual(result.returncode, 0)
            self.assertIn(prompt + "ls: аргументы = []", result.stdout)

    def test_bad_cli(self):
        """Неизвестный параметр и отсутствие значения дают код 2."""
        for arguments in [("--unknown",), ("--vfs",), ("--prompt",),
                          ("--startup-script",)]:
            result = launch(*arguments)
            self.assertEqual(result.returncode, 2)
            self.assertIn("error:", result.stderr)


class StartupTests(unittest.TestCase):
    """Проверить выполнение скрипта и последующий REPL."""

    def test_errors_continue_and_exit_stops(self):
        """Ошибки пропускаются; после exit команды не выполняются."""
        result = launch("--prompt", "test$ ", "--startup-script",
                        str(PROJECT_DIR / "examples/errors.txt"))
        self.assertEqual(result.returncode, 0)
        self.assertIn("test$ unknown", result.stdout)
        self.assertIn("строка 1:", result.stdout)
        self.assertIn("test$ ls\nls: аргументы = []", result.stdout)
        self.assertIn("строка 7:", result.stdout)
        self.assertIn('ls: аргументы = ["-a"]', result.stdout)
        self.assertNotIn("эта строка", result.stdout)

    def test_script_then_repl(self):
        """После конца скрипта без exit начинается интерактивный ввод."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "команды с пробелами.txt"
            path.write_text("ls\n", encoding="utf-8")
            result = launch("--startup-script", str(path), "--prompt", "> ",
                            input_text="cd\nexit\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("> ls\nls: аргументы = []", result.stdout)
        self.assertIn("> cd: аргументы = []", result.stdout)

    def test_missing_script(self):
        """Ошибка чтения скрипта даёт сообщение и код 1."""
        with tempfile.TemporaryDirectory() as directory:
            result = launch("--startup-script",
                            str(Path(directory) / "missing.txt"))
        self.assertEqual(result.returncode, 1)
        self.assertIn("Ошибка чтения скрипта", result.stdout)

    def test_bad_encoding_and_directory(self):
        """Неверная кодировка и каталог вместо файла дают ошибку."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.txt"
            path.write_bytes(b"\xff")
            for candidate in [str(path), directory]:
                result = launch("--startup-script", candidate)
                self.assertEqual(result.returncode, 1)
                self.assertIn("Ошибка чтения скрипта", result.stdout)


if __name__ == "__main__":
    unittest.main()
