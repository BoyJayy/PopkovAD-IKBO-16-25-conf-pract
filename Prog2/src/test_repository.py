"""Load an offline adjacency list with uppercase package names."""

from pathlib import Path

from config import TEST_NAME
from graph import Node

TEST_VERSION = "1.0"
MAX_TEST_BYTES = 1024 * 1024


def parse_graph(source):
    """Parse uppercase names and reject duplicate or undefined vertices."""
    graph = {}
    for number, line in enumerate(source.splitlines(), 1):
        line = line.partition("#")[0].strip()
        if not line:
            continue
        name, separator, targets = line.partition(":")
        name, targets = name.strip(), targets.split()
        if not separator or not TEST_NAME.fullmatch(name):
            raise ValueError(f"Граф, строка {number}: ожидается ИМЯ: ИМЕНА")
        if name in graph or any(not TEST_NAME.fullmatch(t) for t in targets):
            raise ValueError(f"Граф, строка {number}: неверное имя или дубль")
        graph[name] = tuple(dict.fromkeys(targets))
    undefined = {target for values in graph.values() for target in values}
    undefined -= graph.keys()
    if undefined:
        raise ValueError("Граф: не объявлены " + ", ".join(sorted(undefined)))
    return graph


def load_test(config):
    """Read a bounded local graph and select its configured root."""
    with Path(config.repository).open("rb") as stream:
        source = stream.read(MAX_TEST_BYTES + 1)
    if len(source) > MAX_TEST_BYTES:
        raise ValueError("Тестовый граф превышает ограничение 1 МиБ")
    graph = parse_graph(source.decode("utf-8-sig"))
    if config.package not in graph or config.version != TEST_VERSION:
        raise ValueError(f"Граф: не найден {config.package}={config.version}")
    nodes = {name: Node(name, TEST_VERSION) for name in graph}
    records = {
        nodes[name]: tuple(nodes[target] for target in targets)
        for name, targets in graph.items()
    }
    return nodes[config.package], records, records.__getitem__
