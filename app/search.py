"""Transliteration-aware search over the competitor lists.

A rider registered as "Denis Chernykh" is looked up by a Latin fragment one moment and
by a Cyrillic one the next, and plain substring matching finds only one of them. Every
line and every query is therefore reduced to three comparable forms -- as typed, in
Latin and in Cyrillic -- and a line matches when the query's form is contained in the
line's form of the same kind.

Reducing a whole list is the expensive half, so :class:`SearchIndex` does it once per
change of that list; the query is reduced on every search.

The tables spell their non-ASCII characters as escapes because the repository rejects
non-ASCII bytes in source files (see CLAUDE.md).
"""

from __future__ import annotations

import unicodedata
from collections.abc import Sequence
from typing import NamedTuple

_CYRILLIC_TO_LATIN = {
    "\u0430": "a",
    "\u0431": "b",
    "\u0432": "v",
    "\u0433": "g",
    "\u0491": "g",
    "\u0434": "d",
    "\u0435": "e",
    "\u0451": "e",
    "\u0454": "ye",
    "\u0436": "zh",
    "\u0437": "z",
    "\u0438": "i",
    "\u0456": "i",
    "\u0457": "yi",
    "\u0439": "y",
    "\u043a": "k",
    "\u043b": "l",
    "\u043c": "m",
    "\u043d": "n",
    "\u043e": "o",
    "\u043f": "p",
    "\u0440": "r",
    "\u0441": "s",
    "\u0442": "t",
    "\u0443": "u",
    "\u045e": "u",
    "\u0444": "f",
    "\u0445": "kh",
    "\u0446": "ts",
    "\u0447": "ch",
    "\u0448": "sh",
    "\u0449": "shch",
    "\u044a": "",
    "\u044b": "y",
    "\u044c": "",
    "\u044d": "e",
    "\u044e": "yu",
    "\u044f": "ya",
}

# Longest match first, so "shch" wins over "sh" and "kh" over both "k" and "h".
_LATIN_TO_CYRILLIC = {
    "shch": "\u0449",
    "sch": "\u0449",
    "zh": "\u0436",
    "kh": "\u0445",
    "ch": "\u0447",
    "sh": "\u0448",
    "ts": "\u0446",
    "ya": "\u044f",
    "yu": "\u044e",
    "ye": "\u0435",
    "yo": "\u0435",
    "yi": "\u0438",
    "a": "\u0430",
    "b": "\u0431",
    "c": "\u043a",
    "d": "\u0434",
    "e": "\u0435",
    "f": "\u0444",
    "g": "\u0433",
    "h": "\u0445",
    "i": "\u0438",
    "j": "\u0439",
    "k": "\u043a",
    "l": "\u043b",
    "m": "\u043c",
    "n": "\u043d",
    "o": "\u043e",
    "p": "\u043f",
    "q": "\u043a",
    "r": "\u0440",
    "s": "\u0441",
    "t": "\u0442",
    "u": "\u0443",
    "v": "\u0432",
    "w": "\u0432",
    "x": "\u043a\u0441",
    "y": "\u044b",
    "z": "\u0437",
}

_LATIN_CHUNK_SIZES = (4, 3, 2, 1)

# Variants folded together so one Cyrillic spelling compares equal to another: the
# soft and hard signs carry no sound a Latin speller would write, and the Ukrainian
# and Belarusian letters sit close enough to their Russian neighbours.
_CYRILLIC_FOLD = {
    "\u0451": "\u0435",
    "\u044a": "",
    "\u044c": "",
    "\u0456": "\u0438",
    "\u0457": "\u0438",
    "\u0454": "\u0435",
    "\u0491": "\u0433",
    "\u045e": "\u0443",
}


class Forms(NamedTuple):
    """The three comparable shapes of one piece of text."""

    plain: str
    latin: str
    cyrillic: str


def transliterate_to_latin(text: str) -> str:
    """Rewrite Cyrillic letters as Latin ones, leaving everything else as it is."""
    return "".join(_CYRILLIC_TO_LATIN.get(ch, ch) for ch in text.lower())


def transliterate_to_cyrillic(text: str) -> str:
    """Rewrite Latin letters as Cyrillic ones, folding Cyrillic already present."""
    lowered = text.lower()
    out: list[str] = []
    position = 0
    while position < len(lowered):
        for size in _LATIN_CHUNK_SIZES:
            replacement = _LATIN_TO_CYRILLIC.get(lowered[position : position + size])
            if replacement is not None:
                out.append(replacement)
                position += size
                break
        else:
            char = lowered[position]
            out.append(_CYRILLIC_FOLD.get(char, char))
            position += 1
    return "".join(out)


def search_forms(text: str) -> Forms:
    """Reduce text to the forms a search compares."""
    return Forms(
        text.lower(), transliterate_to_latin(text), transliterate_to_cyrillic(text)
    )


def forms_match(line: Forms, query: Forms) -> bool:
    """Whether the query appears in the line in any of the three forms.

    Each form is compared only against its own kind: a Latin query never matches a
    Cyrillic line by accident, it matches the Latin rendering of it. An empty query
    form (a lone soft sign transliterates to nothing) is skipped rather than treated
    as a substring of everything.
    """
    if query.plain and query.plain in line.plain:
        return True
    if query.latin and query.latin in line.latin:
        return True
    return bool(query.cyrillic and query.cyrillic in line.cyrillic)


def scripts_in(text: str) -> set[str]:
    """Name the scripts the letters of text belong to, e.g. {"Latin", "Cyrillic"}."""
    found: set[str] = set()
    for char in text:
        if not char.isalpha():
            continue
        name = unicodedata.name(char, "")
        if name:
            found.add(name.split()[0].capitalize())
    return found


class SearchIndex:
    """The reduced forms of one list, rebuilt only when that list changes."""

    def __init__(self) -> None:
        self._items: list[str] = []
        self._forms: list[Forms] = []
        self._scripts: list[str] = []

    @property
    def scripts(self) -> list[str]:
        """Scripts present in the indexed list, sorted; for the debug line."""
        return self._scripts

    def refresh(self, items: Sequence[str]) -> bool:
        """Re-reduce the list if it changed; returns whether it did.

        The comparison is against the exact items indexed rather than a hash or a
        counter: a stale index silently stops finding people, which is worse than the
        cost of comparing a few hundred short strings.
        """
        if list(items) == self._items:
            return False
        self._items = list(items)
        self._forms = [search_forms(item) for item in self._items]
        scripts: set[str] = set()
        for item in self._items:
            scripts |= scripts_in(item)
        self._scripts = sorted(scripts)
        return True

    def matches(self, row: int, query: Forms) -> bool:
        """Whether the indexed line at row matches the reduced query."""
        if not 0 <= row < len(self._forms):
            return False
        return forms_match(self._forms[row], query)
