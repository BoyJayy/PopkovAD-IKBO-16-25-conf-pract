"""Load and validate the six options of the YAML configuration."""

import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from flat_yaml import parse_mapping

APT_NAME = re.compile(r"[a-z0-9][a-z0-9+.-]+")
TEST_NAME = re.compile(r"[A-Z]+")
VERSION = re.compile(r"(?:[0-9]+:)?[0-9][a-zA-Z0-9.+~-]*(?<!-)")
MAX_CONFIG_BYTES = 16 * 1024
MAX_VERSION_LENGTH = 256


@dataclass(frozen=True)
class Config:
    """Validated user options with the test path resolved."""

    package: str
    repository: str
    test_mode: bool
    version: str
    ascii_tree: bool
    exclude: str


def repository_source(value, test_mode, config_path):
    """Resolve a local file or validate an absolute HTTP(S) URL."""
    if test_mode:
        path = config_path.parent / value
        if not path.is_file():
            raise ValueError("repository: укажите существующий файл графа")
        return str(path.resolve())
    try:
        url = urlsplit(value)
        url.port
    except ValueError:
        raise ValueError("repository: некорректный URL") from None
    if url.scheme not in {"http", "https"} or not url.hostname:
        raise ValueError("repository: ожидается абсолютный HTTP(S) URL")
    if url.username is not None or url.fragment or not url.path.strip("/"):
        raise ValueError("repository: нужен URL файла без логина и фрагмента")
    if any(char.isspace() for char in value):
        raise ValueError("repository: пробелы в URL нужно экранировать")
    return value


def string_option(options, key, allow_empty=False):
    """Accept only single-line strings without control characters."""
    value = options.get(key)
    if not isinstance(value, str) or (not value and not allow_empty):
        raise ValueError(f"{key}: ожидается строка")
    if value and not value.isprintable():
        raise ValueError(f"{key}: недопустимые управляющие символы")
    return value


def valid_version(value):
    """Check the shape of an APT version before using or comparing it."""
    return len(value) <= MAX_VERSION_LENGTH and VERSION.fullmatch(value)


def validate(options, config_path):
    """Check types, names and source location before accessing a repository."""
    keys = Config.__dataclass_fields__.keys()
    if not isinstance(options, dict) or options.keys() != keys:
        raise ValueError("YAML: ожидаются ключи " + ", ".join(keys))
    for key in ("test_mode", "ascii_tree"):
        if type(options[key]) is not bool:
            raise ValueError(f"{key}: ожидается true или false")

    test_mode = options["test_mode"]
    package = string_option(options, "package")
    pattern = TEST_NAME if test_mode else APT_NAME
    if not pattern.fullmatch(package):
        raise ValueError("package: неверное имя пакета для выбранного режима")
    version = string_option(options, "version")
    if not valid_version(version):
        raise ValueError("version: ожидается версия в формате APT")
    repository = string_option(options, "repository")
    repository = repository_source(repository, test_mode, config_path)
    exclude = string_option(options, "exclude", allow_empty=True)
    if exclude and exclude != exclude.strip():
        raise ValueError("exclude: уберите пробелы по краям подстроки")
    return Config(package, repository, test_mode, version,
                  options["ascii_tree"], exclude)


def load_config(path):
    """Read one bounded YAML document without allowing Python objects."""
    with path.open("rb") as stream:
        source = stream.read(MAX_CONFIG_BYTES + 1)
    if len(source) > MAX_CONFIG_BYTES:
        raise ValueError("YAML: конфигурация превышает 16 КиБ")
    return validate(parse_mapping(source.decode("utf-8-sig")), path)
