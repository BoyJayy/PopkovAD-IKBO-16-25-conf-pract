"""Read the flat scalar subset of YAML used by the CLI settings."""

import json
import re

ENTRY = re.compile(r"([a-z_]+):[ \t]+(.*)")
SINGLE = re.compile(r"'((?:[^']|'')*)'(?:\s+#.*)?")
DOUBLE = re.compile(r'("(?:[^"\\]|\\.)*")(?:\s+#.*)?')
PLAIN = re.compile(r"[A-Za-z0-9_./+~%?&=:@ -]+")
NUMBER = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)"
                    r"(?:[eE][+-]?[0-9]+)?")


def scalar(text):
    """Read a string, boolean, or other scalar rejected by the option schema."""
    single = SINGLE.fullmatch(text)
    if single:
        return single[1].replace("''", "'")
    double = DOUBLE.fullmatch(text)
    if double:
        return json.loads(double[1])
    value = re.split(r"\s+#", text, maxsplit=1)[0].rstrip()
    if not PLAIN.fullmatch(value) or ": " in value:
        raise ValueError("ожидается скаляр YAML")
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    if NUMBER.fullmatch(value) or value.lower() in {"null", "~"}:
        return None
    return value


def parse_mapping(source):
    """Read an unindented mapping with distinct keys and optional comments."""
    mapping = {}
    for number, line in enumerate(source.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        entry = ENTRY.fullmatch(line.rstrip())
        if not entry:
            raise ValueError(f"YAML, строка {number}: ожидается ключ: значение")
        key, raw_value = entry.groups()
        if key in mapping:
            raise ValueError(f"YAML, строка {number}: повтор ключа {key}")
        try:
            mapping[key] = scalar(raw_value)
        except ValueError:
            message = f"YAML, строка {number}: неверное значение {key}"
            raise ValueError(message) from None
    return mapping
