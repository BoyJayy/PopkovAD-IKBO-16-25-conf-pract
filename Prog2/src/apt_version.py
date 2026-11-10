"""Compare Debian versions by epoch, upstream version and revision."""

import re
from itertools import zip_longest

PARTS = re.compile(r"([^0-9]*)([0-9]*)")


def split_version(value):
    """Separate the epoch and revision, defaulting each to zero."""
    epoch, colon, remainder = value.partition(":")
    if not colon:
        epoch, remainder = "0", value
    upstream, hyphen, revision = remainder.rpartition("-")
    if not hyphen:
        upstream, revision = remainder, "0"
    return int(epoch), upstream, revision


def character_order(character):
    """Place tilde before empty text, then letters, then punctuation."""
    if character == "~":
        return -1
    if not character:
        return 0
    return ord(character) if character.isalpha() else 256 + ord(character)


def comparison(left, right):
    """Return a comparator result for two ordered values."""
    return (left > right) - (left < right)


def compare_part(left, right):
    """Compare alternating non-digit and digit runs in a version part."""
    left_runs, right_runs = PARTS.findall(left), PARTS.findall(right)
    for left_run, right_run in zip_longest(
        left_runs, right_runs, fillvalue=("", "")
    ):
        for a, b in zip_longest(left_run[0], right_run[0], fillvalue=""):
            order = comparison(character_order(a), character_order(b))
            if order:
                return order
        a, b = left_run[1].lstrip("0"), right_run[1].lstrip("0")
        order = comparison((len(a), a), (len(b), b))
        if order:
            return order
    return 0


def compare_versions(left, right):
    """Return a negative, zero or positive result in Debian version order."""
    left_epoch, left_upstream, left_revision = split_version(left)
    right_epoch, right_upstream, right_revision = split_version(right)
    return (comparison(left_epoch, right_epoch)
            or compare_part(left_upstream, right_upstream)
            or compare_part(left_revision, right_revision))
