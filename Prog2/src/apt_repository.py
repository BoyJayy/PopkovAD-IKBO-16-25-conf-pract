"""Resolve declared APT dependencies inside one binary package index."""

import operator
import re
from collections import defaultdict
from dataclasses import dataclass
from functools import cmp_to_key

from apt_index import download_index, exact_package
from apt_version import compare_versions
from config import APT_NAME, valid_version
from graph import Node

RELATION = re.compile(
    rf"({APT_NAME.pattern})(?::([a-z0-9-]+))?"
    r"(?:\s*\((<<|<=|=|>=|>>)\s*([^\s()]+)\))?"
)
COMPARE = {
    "<<": operator.lt, "<=": operator.le, "=": operator.eq,
    ">=": operator.ge, ">>": operator.gt,
}


@dataclass(frozen=True)
class Relation:
    """One alternative, optionally qualified and restricted by version."""

    name: str
    qualifier: str | None
    operator: str | None
    version: str | None

    def accepts(self, version):
        """Check the provided version against this alternative's constraint."""
        if not self.operator:
            return True
        return version is not None and COMPARE[self.operator](
            compare_versions(version, self.version), 0
        )


def alternatives(text):
    """Yield every alternative from a binary relationship field."""
    if not text:
        return
    for term in re.split(r"[,|]", text):
        match = RELATION.fullmatch(term.strip())
        if not match or (match[4] and not valid_version(match[4])):
            raise ValueError(f"Индекс: неверная зависимость {term.strip()!r}")
        yield Relation(*match.groups())


def package_order(left, right):
    """Sort records of a concrete package by Debian version."""
    return compare_versions(left.version, right.version)


def eligible_architecture(package, qualifier, native):
    """Accept an explicit architecture or the current index's architecture."""
    if qualifier in (None, "native", "any"):
        qualifier = native
    return package.architecture in {qualifier, "all", ""}


def index_architecture(packages):
    """Use the single concrete architecture represented in the binary index."""
    architectures = {p.architecture for p in packages} - {"", "all"}
    if len(architectures) > 1:
        raise ValueError("Индекс: ожидается одна архитектура")
    return next(iter(architectures), "")


class AptRepository:
    """Look up concrete versions and providers from the loaded index."""

    def __init__(self, packages):
        self.native = index_architecture(packages)
        self.records = {}
        self.by_name = defaultdict(list)
        self.providers = defaultdict(list)
        for package in packages:
            self.records[Node(package.name, package.version)] = package
            self.by_name[package.name].append(package)
            for capability in alternatives(package.provides):
                self.providers[capability.name].append((package, capability))
        for records in self.by_name.values():
            records.sort(key=cmp_to_key(package_order), reverse=True)
        for providers in self.providers.values():
            key = cmp_to_key(package_order)
            providers.sort(key=lambda entry: key(entry[0]), reverse=True)

    def resolve(self, relation):
        """Return the newest eligible version of each concrete package."""
        matched = {}
        for package in self.by_name.get(relation.name, ()):
            if self.accepts(package, package.version, relation):
                matched[package.name] = Node(package.name, package.version)
                break
        for package, capability in self.providers.get(relation.name, ()):
            if self.accepts(package, capability.version, relation):
                matched.setdefault(
                    package.name, Node(package.name, package.version)
                )
        return tuple(matched.values()) or (Node(relation.name, None),)

    def accepts(self, package, version, relation):
        """Check the architecture and the provided version together."""
        return (eligible_architecture(package, relation.qualifier, self.native)
                and relation.accepts(version))

    def dependencies(self, node):
        """Return distinct targets across Pre-Depends and Depends alternatives."""
        if node.version is None:
            return ()
        package = self.records[node]
        relations = (package.pre_depends, package.depends)
        return tuple(dict.fromkeys(
            target
            for value in relations
            for relation in alternatives(value)
            for target in self.resolve(relation)
        ))


def load_apt(config):
    """Load an APT index, choose the root, and prepare dependency lookup."""
    packages = download_index(config.repository)
    root = exact_package(packages, config.package, config.version)
    repository = AptRepository(packages)
    node = Node(root.name, root.version)
    return node, repository.records, repository.dependencies
