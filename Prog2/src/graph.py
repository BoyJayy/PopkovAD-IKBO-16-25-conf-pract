"""Represent package versions and traverse the graph recursively."""

from dataclasses import dataclass

MAX_DEPTH = 200
MAX_NODES = 500
MAX_EDGES = 2500


@dataclass(frozen=True)
class Node:
    """A concrete package version, or an unresolved dependency name."""

    name: str
    version: str | None

    def label(self):
        """Show version or mark that the name is absent from the index."""
        if self.version is None:
            return f"{self.name} [нет в индексе]"
        return f"{self.name}={self.version}"


def excluded(node, substring):
    """Return whether the node's name contains the configured substring."""
    return bool(substring and substring in node.name)


def build_graph(root, dependencies, substring):
    """Visit each reachable node once while retaining cycle edges."""
    graph = {}
    edge_count = 0

    def visit(node, depth):
        nonlocal edge_count
        if node in graph:
            return
        if depth >= MAX_DEPTH or len(graph) >= MAX_NODES:
            raise ValueError("Граф превышает ограничение глубины или вершин")
        children = tuple(
            child for child in dependencies(node)
            if not excluded(child, substring)
        )
        edge_count += len(children)
        if edge_count > MAX_EDGES:
            raise ValueError("Граф превышает ограничение числа рёбер")
        graph[node] = children
        for child in children:
            visit(child, depth + 1)

    if excluded(root, substring):
        raise ValueError("exclude: фильтр исключает анализируемый пакет")
    visit(root, 0)
    return graph


def reverse_graph(root, records, dependencies, substring):
    """Invert dependency edges and apply the same recursive DFS from root."""
    incoming = {}
    for node in records:
        if excluded(node, substring):
            continue
        for target in dependencies(node):
            incoming.setdefault(target, []).append(node)
    return build_graph(root, lambda node: incoming.get(node, ()), substring)
