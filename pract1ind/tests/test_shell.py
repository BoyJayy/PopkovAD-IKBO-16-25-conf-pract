"""Проверки парсера, команд и интерактивного диалога."""

import getpass
from pathlib import Path
import socket
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from parser import parse_command
from shell import default_prompt, execute, repl


class ParserTests(unittest.TestCase):
    """Проверить раскрытие переменных и границы аргументов."""

    @patch.dict("os.environ", {"DEMO": "путь с пробелом"})
    def test_expansion(self):
        """Значение переменной остаётся одним аргументом."""
        self.assertEqual(parse_command('cd "${DEMO}"'),
                         ["cd", "путь с пробелом"])
        self.assertEqual(parse_command("ls $DEMO"),
                         ["ls", "путь с пробелом"])

    def test_quotes_and_escape(self):
        """Одинарные кавычки и экранирование сохраняют доллар."""
        self.assertEqual(parse_command("ls '$HOME' \\$HOME ''"),
                         ["ls", "$HOME", "$HOME", ""])
        self.assertEqual(parse_command('cd folder" with space"'),
                         ["cd", "folder with space"])

    @patch.dict("os.environ", {}, clear=True)
    def test_missing_variable(self):
        """Неопределённая переменная раскрывается в пустую строку."""
        self.assertEqual(parse_command("ls $MISSING"), ["ls", ""])

    def test_invalid_syntax(self):
        """Ошибочный синтаксис не выполняется."""
        for line in ['cd "unfinished', "ls \\"]:
            with self.subTest(line=line), self.assertRaises(ValueError):
                parse_command(line)


class ShellTests(unittest.TestCase):
    """Проверить команды и обработку ошибок в REPL."""

    def test_prompt(self):
        """Приглашение содержит реальные данные ОС."""
        expected = f"{getpass.getuser()}@{socket.gethostname()}:~$ "
        self.assertEqual(default_prompt(), expected)

    def test_stubs(self):
        """Заглушки печатают своё имя и аргументы."""
        output = []
        self.assertTrue(execute("ls -a /tmp", output.append))
        self.assertTrue(execute("cd", output.append))
        self.assertEqual(output, ['ls: аргументы = ["-a", "/tmp"]',
                                  "cd: аргументы = []"])

    def test_invalid_commands(self):
        """Неизвестные команды и неверные аргументы дают ошибку."""
        for line in ["pwd", "cd a b", "cd -x", "ls -z", "exit 1"]:
            with self.subTest(line=line), self.assertRaises(ValueError):
                execute(line)

    def test_exit_and_blank(self):
        """Пустая строка продолжает диалог, exit завершает."""
        self.assertTrue(execute("   "))
        self.assertFalse(execute("exit"))

    def test_repl_recovers(self):
        """После ошибки следующий ввод обрабатывается."""
        output = []
        lines = iter(["pwd", "ls", "exit", "cd"])
        repl("demo$ ", lambda prompt: next(lines), output.append)
        self.assertIn("Ошибка:", output[0])
        self.assertEqual(output[1], "ls: аргументы = []")
        self.assertEqual(next(lines), "cd")

    def test_eof(self):
        """Конец потока корректно завершает REPL."""
        def read(prompt):
            """Имитировать EOF."""
            raise EOFError
        repl("demo$ ", read)


if __name__ == "__main__":
    unittest.main()
