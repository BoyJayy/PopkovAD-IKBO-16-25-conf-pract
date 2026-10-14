"""Снимок директории: каталоги и байты файлов хранятся в памяти."""

from dataclasses import dataclass
from pathlib import Path
import posixpath


def load_entries(root):
    """Прочитать обычные файлы и каталоги без изменения источника."""
    entries = {"/": None}
    pending = [(root, "/")]
    while pending:
        physical, virtual = pending.pop()
        for child in sorted(physical.iterdir()):
            name = posixpath.join(virtual, child.name)
            if child.is_symlink():
                raise ValueError(f"символические ссылки не поддерживаются: "
                                 f"{child}")
            if child.is_dir():
                entries[name] = None
                pending.append((child, name))
            elif child.is_file():
                entries[name] = child.read_bytes()
            else:
                raise ValueError(f"неподдерживаемый тип файла: {child}")
    return entries


@dataclass
class VirtualFileSystem:
    """Хранить каталоги как None, а содержимое файлов как bytes."""

    entries: dict

    @classmethod
    def load(cls, source=None):
        """Создать пустую VFS либо загрузить снимок директории с диска."""
        if source is None:
            return cls({"/": None})
        root = Path(source)
        if root.is_symlink():
            raise ValueError("источник VFS не должен быть ссылкой")
        if not root.exists():
            raise ValueError(f"директория VFS не найдена: {source}")
        if not root.is_dir():
            raise ValueError(f"источник VFS должен быть директорией: {source}")
        return cls(load_entries(root))

    def resolve(self, path):
        """Разрешить путь внутри виртуального корня, не обращаясь к ОС."""
        normalized = posixpath.normpath("/" + path.lstrip("/"))
        if normalized not in self.entries:
            raise ValueError(f"путь не найден в VFS: {path}")
        return normalized

    def read_file(self, path):
        """Прочитать байты из памяти; каталоги читать как файл нельзя."""
        normalized = self.resolve(path)
        data = self.entries[normalized]
        if data is None:
            raise ValueError(f"это каталог VFS: {path}")
        return data

    def summary(self):
        """Подсчитать каталоги (включая корень), файлы и байты в памяти."""
        files = [data for data in self.entries.values() if data is not None]
        return {"directories": len(self.entries) - len(files),
                "files": len(files), "bytes": sum(map(len, files))}

    def describe(self, path="/"):
        """Вернуть сведения о файле либо детях каталога из памяти."""
        normalized = self.resolve(path)
        data = self.entries[normalized]
        if data is not None:
            return {"path": normalized, "type": "file", "bytes": len(data)}
        children = [name for name in self.entries
                    if name != normalized
                    and posixpath.dirname(name) == normalized]
        return {"path": normalized, "type": "directory",
                "children": sorted(posixpath.basename(name)
                                   for name in children)}
