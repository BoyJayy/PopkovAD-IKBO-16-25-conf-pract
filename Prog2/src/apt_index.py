"""Read Ubuntu binary Packages indexes without calling APT."""

import gzip
import lzma
from dataclasses import dataclass
from io import BytesIO
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import urlopen

from config import APT_NAME, valid_version

MAX_INDEX_BYTES = 64 * 1024 * 1024
HTTP_TIMEOUT_SECONDS = 20
PACKAGE_FIELDS = {
    "Package", "Version", "Architecture", "Depends", "Pre-Depends", "Provides",
}
RELATION_FIELDS = ("Pre-Depends", "Depends")


@dataclass(frozen=True)
class Package:
    """Fields of one package record relevant to dependency analysis."""

    name: str
    version: str
    architecture: str
    pre_depends: str
    depends: str
    provides: str

    @classmethod
    def from_fields(cls, fields):
        """Validate the identifying fields and retain relationship text."""
        name, version = fields.get("Package", ""), fields.get("Version", "")
        if not APT_NAME.fullmatch(name) or not valid_version(version):
            raise ValueError("Индекс: запись с неверным именем или версией")
        return cls(name, version, fields.get("Architecture", ""),
                   fields.get("Pre-Depends", ""), fields.get("Depends", ""),
                   fields.get("Provides", ""))

    def direct_lines(self):
        """Yield the original mandatory dependency declarations by field."""
        for field, value in zip(RELATION_FIELDS, (self.pre_depends, self.depends)):
            if value:
                yield f"{field}: {value}"


def control_records(lines):
    """Read selected Deb822 fields, preserving continuation lines."""
    fields = {}
    key = ""
    for raw_line in lines:
        line = raw_line.rstrip("\r\n")
        if not line:
            if fields:
                yield fields
            fields, key = {}, ""
        elif line[0] in " \t":
            if key in PACKAGE_FIELDS:
                fields[key] += " " + line.strip()
        else:
            key, separator, value = line.partition(":")
            if not separator:
                raise ValueError("Индекс: ожидается поле формата ключ: значение")
            if key in PACKAGE_FIELDS:
                fields[key] = value.strip()
    if fields:
        yield fields


def bounded_read(stream):
    """Reject an index exceeding the size limit, including after unpacking."""
    payload = stream.read(MAX_INDEX_BYTES + 1)
    if len(payload) > MAX_INDEX_BYTES:
        raise ValueError("Индекс превышает ограничение 64 МиБ")
    return payload


def index_text(payload, filename):
    """Unpack a plain, gzip or xz index and decode it as UTF-8."""
    if filename.endswith(".gz"):
        with gzip.GzipFile(fileobj=BytesIO(payload)) as stream:
            payload = bounded_read(stream)
    elif filename.endswith(".xz"):
        with lzma.LZMAFile(BytesIO(payload)) as stream:
            payload = bounded_read(stream)
    return payload.decode("utf-8")


def download_index(url):
    """Download and parse a single binary package index."""
    try:
        with urlopen(url, timeout=HTTP_TIMEOUT_SECONDS) as response:
            payload = bounded_read(response)
        source = index_text(payload, urlsplit(url).path)
    except URLError as error:
        raise ValueError(f"Индекс недоступен: {error.reason}") from None
    except (OSError, EOFError, lzma.LZMAError, UnicodeError) as error:
        raise ValueError(f"Не удалось прочитать индекс: {error}") from None
    packages = [
        Package.from_fields(fields)
        for fields in control_records(source.splitlines())
    ]
    if not packages:
        raise ValueError("В индексе нет записей пакетов")
    return packages


def exact_package(packages, name, version):
    """Find the requested version and report the versions available otherwise."""
    versions = []
    for package in packages:
        if package.name == name:
            if package.version == version:
                return package
            versions.append(package.version)
    if not versions:
        raise ValueError(f"Пакет {name} отсутствует в индексе")
    available = ", ".join(dict.fromkeys(versions))
    raise ValueError(f"Нет {name}={version}. Доступные версии: {available}")
