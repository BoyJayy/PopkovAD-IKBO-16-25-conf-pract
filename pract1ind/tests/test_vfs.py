"""Проверки загрузки VFS, изоляции снимка и интеграции с CLI."""

from contextlib import redirect_stdout
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from main import main
from shell import execute, repl
from test_config import launch, PROJECT_DIR
from vfs import VirtualFileSystem


class VfsTests(unittest.TestCase):
    """Проверить виртуальные каталоги и произвольное содержимое файлов."""

    def test_default_and_empty_directory(self):
        """Без источника и с пустой директорией есть только корень."""
        with tempfile.TemporaryDirectory() as directory:
            for vfs in [VirtualFileSystem.load(),
                        VirtualFileSystem.load(directory)]:
                self.assertEqual(vfs.summary(),
                                 {"directories": 1, "files": 0, "bytes": 0})
                self.assertEqual(vfs.describe()["children"], [])

    def test_nested_binary_hidden_and_empty(self):
        """Байты, пустые каталоги и необычные имена сохраняются точно."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            nested = root / "папка с пробелами" / "second" / "third"
            nested.mkdir(parents=True)
            payload = b"\x00\xff\x80\n"
            (nested / "data.bin").write_bytes(payload)
            (root / ".hidden").write_text("hidden", encoding="utf-8")
            (root / "empty").mkdir()
            vfs = VirtualFileSystem.load(root)
        self.assertEqual(vfs.read_file(
            "/папка с пробелами/second/third/data.bin"), payload)
        self.assertIn(".hidden", vfs.describe()["children"])
        self.assertEqual(vfs.describe("empty")["children"], [])
        self.assertEqual(vfs.summary(),
                         {"directories": 5, "files": 2, "bytes": 10})

    def test_snapshot_independent_of_source(self):
        """Изменение и удаление исходного файла не затрагивают снимок."""
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "file.txt"
            source.write_bytes(b"original")
            before = source.stat()
            vfs = VirtualFileSystem.load(directory)
            self.assertEqual(source.read_bytes(), b"original")
            self.assertEqual(source.stat().st_mtime_ns, before.st_mtime_ns)
            source.write_bytes(b"changed")
            self.assertEqual(vfs.read_file("file.txt"), b"original")
            vfs.entries["/file.txt"] = b"memory only"
            self.assertEqual(source.read_bytes(), b"changed")
            source.unlink()
        self.assertEqual(vfs.read_file("file.txt"), b"memory only")

    def test_virtual_paths_and_errors(self):
        """Виртуальные пути не позволяют выйти в реальную ОС."""
        vfs = VirtualFileSystem({"/": None, "/file.txt": b"data"})
        self.assertEqual(vfs.read_file("/../../file.txt"), b"data")
        self.assertEqual(vfs.resolve("./file.txt"), "/file.txt")
        self.assertEqual(vfs.describe("file.txt")["bytes"], 4)
        for operation in [lambda: vfs.read_file("/"),
                          lambda: vfs.resolve("/missing"),
                          lambda: vfs.resolve("/file.txt/child")]:
            with self.assertRaises(ValueError):
                operation()

    def test_memory_only_commands_and_repl(self):
        """После загрузки команды VFS не открывают файлы на диске."""
        vfs = VirtualFileSystem({"/": None, "/file.txt": b"data"})
        output = []
        lines = iter(["vfs-info /file.txt", "exit"])
        with patch.object(Path, "open", side_effect=AssertionError), \
                patch.object(Path, "iterdir", side_effect=AssertionError):
            execute("vfs-info", output.append, vfs)
            repl("> ", lambda prompt: next(lines), output.append, vfs)
        self.assertIn('"children": ["file.txt"]', output[0])
        self.assertIn('"bytes": 4', output[1])

    def test_bad_sources(self):
        """Отсутствующая директория и файл вместо неё отклоняются."""
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "file.txt"
            source.write_text("file", encoding="utf-8")
            for candidate in [source, source / "missing"]:
                with self.assertRaises(ValueError):
                    VirtualFileSystem.load(candidate)

    def test_symlinks_rejected(self):
        """Ссылки, включая циклические и битые, не обходятся."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "link").symlink_to(root, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "ссылки"):
                VirtualFileSystem.load(root)
            with self.assertRaisesRegex(ValueError, "ссылкой"):
                VirtualFileSystem.load(root / "link")
            (root / "link").unlink()
            (root / "broken").symlink_to(root / "missing")
            with self.assertRaisesRegex(ValueError, "ссылки"):
                VirtualFileSystem.load(root)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "нужен POSIX FIFO")
    def test_special_files_rejected(self):
        """Специальные файлы не читаются и не блокируют загрузку."""
        with tempfile.TemporaryDirectory() as directory:
            os.mkfifo(Path(directory) / "pipe")
            with self.assertRaisesRegex(ValueError, "тип файла"):
                VirtualFileSystem.load(directory)


class VfsCliTests(unittest.TestCase):
    """Проверить подключение снимка к запуску приложения."""

    def test_fixtures_and_startup(self):
        """Все три примера загружаются до выполнения команд скрипта."""
        for variant in ["minimal", "several", "deep"]:
            with self.subTest(variant=variant):
                result = launch(
                    "--vfs", str(PROJECT_DIR / "examples/vfs" / variant),
                    "--startup-script",
                    str(PROJECT_DIR / "examples/stage3.txt"),
                    "--prompt", "vfs$ ")
                self.assertEqual(result.returncode, 0)
                self.assertIn("[vfs]", result.stdout)
                self.assertIn('"path": "/hello.txt", "type": "file"',
                              result.stdout)
                self.assertIn("путь не найден в VFS", result.stdout)
                self.assertNotIn("эта-строка-не-исполняется", result.stdout)
                if variant == "deep":
                    self.assertIn('"children": ["data.txt"]', result.stdout)

    def test_vfs_in_repl(self):
        """Интерактивная команда получает тот же загруженный снимок."""
        result = launch("--vfs", str(PROJECT_DIR / "examples/vfs/minimal"),
                        input_text="vfs-info /hello.txt\nexit\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn('"type": "file"', result.stdout)

    def test_bad_vfs_exits_before_script(self):
        """Ошибка источника VFS останавливает запуск с кодом 1."""
        with tempfile.TemporaryDirectory() as directory:
            result = launch("--vfs", str(Path(directory) / "missing"),
                            "--startup-script", "also-missing.txt")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Ошибка загрузки VFS", result.stdout)
        self.assertNotIn("Ошибка чтения скрипта", result.stdout)

    def test_permission_error_reported(self):
        """Отказ чтения файла превращается в понятную ошибку запуска."""
        output = io.StringIO()
        with patch.object(Path, "read_bytes", side_effect=PermissionError), \
                redirect_stdout(output):
            code = main(["--vfs", str(PROJECT_DIR / "examples/vfs/minimal")])
        self.assertEqual(code, 1)
        self.assertIn("Ошибка загрузки VFS", output.getvalue())

    def test_vfs_info_invalid_usage(self):
        """Служебная команда проверяет аргументы и наличие VFS."""
        with self.assertRaisesRegex(ValueError, "не более одного"):
            execute("vfs-info a b", vfs=VirtualFileSystem.load())
        with self.assertRaisesRegex(ValueError, "не загружена"):
            execute("vfs-info")


if __name__ == "__main__":
    unittest.main()
