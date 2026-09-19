"""Transliteration-aware search over the competitor lists.

A rider registered as "Denis Chernykh" is looked up by a Latin fragment one moment and
by a Cyrillic one the next, and plain substring matching finds only one of them. Worse,
one name has several Latin spellings -- Maria and Mariya, Sergey and Sergei, Dmitry and
Dmitriy -- so carrying the query letter by letter into the other script is not enough
either.

Both sides are therefore reduced to one **search key**: a coarse Latin spelling in
which the letters a speller has a choice about land on the same result. The i-like
letters (i, y, j and the Cyrillic i, short i, yeru and dotted i) all become ``i``;
"kh" and Cyrillic kha both become ``h``; the iotated vowels become ``ia`` and ``iu``,
which is what "ya" and "yu" reduce to anyway; and a run of the same letter collapses,
so "mariia" and "maria" meet. A line also keeps its text as typed, so an exact
substring still matches exactly as it did before this existed.

The alphabets covered are the ones these races are run in: Kazakh, Russian and Latin,
including the Latin alphabet Kazakhstan is moving to. Other Cyrillic alphabets are
deliberately absent -- a letter with no entry still matches itself, and adding one is
a single line when a race needs it.

Building keys for a whole list is the expensive half, so :class:`SearchIndex` does it
once per change of that list; the query is reduced on every search.

The tables spell their non-ASCII characters as escapes because the repository rejects
non-ASCII bytes in source files (see CLAUDE.md).
"""

from __future__ import annotations

import unicodedata
from collections.abc import Sequence
from typing import NamedTuple

# Cyrillic letter -> search key. Several letters share a key on purpose: that is what
# lets one Latin spelling of a name find another.
_CYRILLIC_KEY = {
    "\u0430": "a",
    "\u0431": "b",
    "\u0432": "v",
    "\u0433": "g",
    "\u0434": "d",
    "\u0435": "e",
    "\u0451": "e",
    "\u0436": "zh",
    "\u0437": "z",
    "\u0438": "i",
    "\u0456": "i",
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
    # Kazakh. Each sounds like the Russian letter a speller would reach for, so it
    # shares that letter's key.
    "\u04d9": "a",
    "\u0493": "g",
    "\u049b": "k",
    "\u04a3": "n",
    "\u04e9": "o",
    "\u04b1": "u",
    "\u04af": "u",
    "\u04bb": "h",
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
    # Kazakh and Turkish Latin: dropping the mark would lose the sound, and the
    # Cyrillic letters they stand for are digraphs here.
    "\u015f": "sh",
    "\u00e7": "ch",
    # Latin letters with no combining mark to strip: a bar, a slash or a
    # ligature is part of the letter, so each needs its own entry.
    "\u0131": "i",
    "\u00f8": "o",
    "\u0142": "l",
    "\u0111": "d",
    "\u00f0": "d",
    "\u00e6": "ae",
    "\u0153": "oe",
    "\u00df": "ss",
    "z": "z",
}

_CHUNK_SIZES = (4, 3, 2, 1)

# Only what the tables themselves produce may be collapsed. Everything else -- digits
# above all -- passes through untouched, or bib 11 would reduce to 1 and find bib 1.
_COLLAPSIBLE = {
    char for value in (*_CYRILLIC_KEY.values(), *_LATIN_KEY.values()) for char in value
}

_CYRILLIC_RANGES = ((0x0400, 0x052F), (0x2DE0, 0x2DFF), (0xA640, 0xA69F))


class Forms(NamedTuple):
    """The two comparable shapes of one piece of text."""

    plain: str
    key: str


def _collapse_runs(text: str) -> str:
    """Squeeze runs of the same transliterated letter, so "mariia" and "maria" agree.

    Digits and separators are left alone: they carry no spelling choice, and a bib or
    a year that lost a repeated digit would match the wrong rider.
    """
    out: list[str] = []
    for char in text:
        if out and out[-1] == char and char in _COLLAPSIBLE:
            continue
        out.append(char)
    return "".join(out)


def _strip_marks(text: str) -> str:
    """Drop combining marks, so an accented letter reaches its plain entry.

    The Latin alphabet Kazakhstan moved to writes Gibadat as "Gibadat" with a breve,
    and a Spanish or Turkish name arrives accented too; decomposing and dropping the
    marks lands all of them on the ASCII table. Cyrillic letters that decompose (short
    i and yo) reach the same key this way that their own entries give.
    """
    return "".join(
        char
        for char in unicodedata.normalize("NFD", text)
        if not unicodedata.combining(char)
    )


def _key_for_char(char: str) -> str:
    """The key for one character the tables do not spell out.

    A letter the tables know is used as it is. Otherwise the marks come off and the
    tables are asked again, which is how an accented Latin letter reaches its plain
    entry and how Cyrillic letters that decompose (short i and yo) land on the same key
    their own entries give. Anything still unknown passes through, so
    a script this module cannot read at least keeps matching itself.
    """
    mapped = _CYRILLIC_KEY.get(char)
    if mapped is not None:
        return mapped
    base = _strip_marks(char)
    if base == char:
        return char
    for table in (_LATIN_KEY, _CYRILLIC_KEY):
        mapped = table.get(base)
        if mapped is not None:
            return mapped
    return base


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
            out.append(_key_for_char(lowered[position]))
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

    A letter counts as Latin when the reduction can reach it -- through its own entry
    or by dropping its marks -- rather than by sitting in a fixed block, so an
    accented letter is not reported as unreadable when the search reads it fine.
    """
    found: set[str] = set()
    for char in text:
        if not char.isalpha():
            continue
        code = ord(char)
        if any(low <= code <= high for low, high in _CYRILLIC_RANGES):
            found.add("Cyrillic")
        elif char in _LATIN_KEY or _strip_marks(char).isascii():
            found.add("Latin")
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
        incoming = list(items)
        if incoming == self._items:
            return False
        self._items = incoming
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
