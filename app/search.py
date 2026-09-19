"""Transliteration-aware search over the competitor lists.

A rider registered as "Denis Chernykh" is looked up by a Latin fragment one moment and
by a Cyrillic one the next, and plain substring matching finds only one of them. Worse,
one name has several Latin spellings -- Maria and Mariya, Sergey and Sergei, Dmitry and
Dmitriy -- so carrying the query letter by letter into the other script is not enough
either.

Both sides are therefore reduced to one **search key**: a coarse Latin spelling in
which the letters a speller has a choice about land on the same result. The i-like
letters (i, y, j and Cyrillic i, iy, yeru, and the Ukrainian ones) all become ``i``;
"kh" and Cyrillic kha both become ``h``; the iotated vowels become ``ia`` and ``iu``,
which is what "ya" and "yu" reduce to anyway; and a run of the same letter collapses,
so "mariia" and "maria" meet. A line also keeps its text as typed, so an exact
substring still matches exactly as it did before this existed.

Building keys for a whole list is the expensive half, so :class:`SearchIndex` does it
once per change of that list; the query is reduced on every search.

The tables spell their non-ASCII characters as escapes because the repository rejects
non-ASCII bytes in source files (see CLAUDE.md).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import NamedTuple

# Cyrillic letter -> search key. Several letters share a key on purpose: that is what
# lets one Latin spelling of a name find another.
_CYRILLIC_KEY = {
    "\u0430": "a",
    "\u0431": "b",
    "\u0432": "v",
    "\u0433": "g",
    "\u0491": "g",
    "\u0434": "d",
    "\u0435": "e",
    "\u0451": "e",
    "\u0454": "e",
    "\u0436": "zh",
    "\u0437": "z",
    "\u0438": "i",
    "\u0456": "i",
    "\u0457": "i",
    "\u0439": "i",
    "\u044b": "i",
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
    "\u0445": "h",
    "\u0446": "ts",
    "\u0447": "ch",
    "\u0448": "sh",
    "\u0449": "sch",
    "\u044a": "",
    "\u044c": "",
    "\u044d": "e",
    "\u044e": "iu",
    "\u044f": "ia",
}

# Latin sequence -> search key, longest match first, so "shch" wins over "sh" and "kh"
# over both "k" and "h". The iotated vowels need no entry: "ya" falls out as "ia"
# through y -> i, which is exactly where Cyrillic ya lands.
_LATIN_KEY = {
    "shch": "sch",
    "sch": "sch",
    "zh": "zh",
    "kh": "h",
    "ch": "ch",
    "sh": "sh",
    "ts": "ts",
    "ye": "e",
    "je": "e",
    "yo": "e",
    "jo": "e",
    "a": "a",
    "b": "b",
    "c": "k",
    "d": "d",
    "e": "e",
    "f": "f",
    "g": "g",
    "h": "h",
    "i": "i",
    "j": "i",
    "k": "k",
    "l": "l",
    "m": "m",
    "n": "n",
    "o": "o",
    "p": "p",
    "q": "k",
    "r": "r",
    "s": "s",
    "t": "t",
    "u": "u",
    "v": "v",
    "w": "v",
    "x": "ks",
    "y": "i",
    "z": "z",
}

_CHUNK_SIZES = (4, 3, 2, 1)

_CYRILLIC_RANGES = ((0x0400, 0x052F), (0x2DE0, 0x2DFF), (0xA640, 0xA69F))
_LATIN_RANGES = ((0x0041, 0x005A), (0x0061, 0x007A), (0x00C0, 0x024F))


class Forms(NamedTuple):
    """The two comparable shapes of one piece of text."""

    plain: str
    key: str


def _collapse_runs(text: str) -> str:
    """Squeeze runs of the same character, so "mariia" and "maria" agree."""
    out: list[str] = []
    for char in text:
        if not out or out[-1] != char:
            out.append(char)
    return "".join(out)


def search_key(text: str) -> str:
    """Reduce text to the coarse spelling two scripts can be compared in."""
    lowered = text.lower()
    out: list[str] = []
    position = 0
    while position < len(lowered):
        for size in _CHUNK_SIZES:
            replacement = _LATIN_KEY.get(lowered[position : position + size])
            if replacement is not None:
                out.append(replacement)
                position += size
                break
        else:
            char = lowered[position]
            out.append(_CYRILLIC_KEY.get(char, char))
            position += 1
    return _collapse_runs("".join(out))


def search_forms(text: str) -> Forms:
    """Reduce text to the forms a search compares."""
    return Forms(text.lower(), search_key(text))


def forms_match(line: Forms, query: Forms) -> bool:
    """Whether the query appears in the line, as typed or as a search key.

    An empty key (a lone soft sign reduces to nothing) is skipped rather than treated
    as a substring of everything.
    """
    if query.plain and query.plain in line.plain:
        return True
    return bool(query.key and query.key in line.key)


def scripts_in(text: str) -> set[str]:
    """Name the scripts the letters of text belong to, e.g. {"Latin", "Cyrillic"}.

    Only the two the search actually transliterates between are named; any other
    letter is reported as "Other", which is honest about what this can tell apart
    and still shows the referee that something unexpected is in the list.
    """
    found: set[str] = set()
    for char in text:
        if not char.isalpha():
            continue
        code = ord(char)
        if any(low <= code <= high for low, high in _LATIN_RANGES):
            found.add("Latin")
        elif any(low <= code <= high for low, high in _CYRILLIC_RANGES):
            found.add("Cyrillic")
        else:
            found.add("Other")
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
