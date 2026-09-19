"""Tests for the transliteration-aware search helpers.

Cyrillic fixtures are spelled as escapes to keep this file ASCII (see CLAUDE.md); the
comment next to each names it.
"""

from __future__ import annotations

from typing import ClassVar

import pytest

from app.search import (
    Forms,
    SearchIndex,
    forms_match,
    scripts_in,
    search_forms,
    search_key,
)

DEN = "\u0414\u0435\u043d"  # Den
CHERNYKH = "\u0427\u0435\u0440\u043d\u044b\u0445"  # Chernykh
# Denis Chernykh
DENIS_CHERNYKH = "\u0414\u0435\u043d\u0438\u0441 \u0427\u0435\u0440\u043d\u044b\u0445"
MARIA = "\u041c\u0430\u0440\u0438\u044f"  # Maria
SERGEY = "\u0421\u0435\u0440\u0433\u0435\u0439"  # Sergey
DMITRY = "\u0414\u043c\u0438\u0442\u0440\u0438\u0439"  # Dmitry
YULIA = "\u042e\u043b\u0438\u044f"  # Yulia
NIKOLAY = "\u041d\u0438\u043a\u043e\u043b\u0430\u0439"  # Nikolay
EVGENY = "\u0415\u0432\u0433\u0435\u043d\u0438\u0439"  # Evgeny
SHCHUKIN = "\u0429\u0443\u043a\u0438\u043d"  # Shchukin
TSVET = "\u0426\u0432\u0435\u0442"  # Tsvet
ZHUK = "\u0416\u0443\u043a"  # Zhuk
IGOR = "\u0418\u0433\u043e\u0440\u044c"  # Igor with a soft sign
SOFT = "\u044c"  # a lone soft sign
ALYONA = "\u0410\u043b\u0451\u043d\u0430"  # Alyona, with yo
ALENA = "\u0410\u043b\u0435\u043d\u0430"  # Alena, with ye
PETROV = "\u041f\u0435\u0442\u0440\u043e\u0432 \u0418\u0432\u0430\u043d"  # Petrov Ivan


class TestSearchKey:
    def test_a_cyrillic_name_reduces_to_latin(self) -> None:
        assert search_key(CHERNYKH) == "chernih"

    def test_the_latin_spelling_reduces_to_the_same_key(self) -> None:
        assert search_key("Chernykh") == search_key(CHERNYKH)

    def test_a_spelling_without_the_k_reduces_to_the_same_key(self) -> None:
        # Both "kh" and a bare "h" stand for the same Cyrillic letter.
        assert search_key("Chernyh") == search_key(CHERNYKH)

    def test_digraphs(self) -> None:
        assert search_key(SHCHUKIN) == "schukin"
        assert search_key("Shchukin") == "schukin"
        assert search_key(TSVET) == "tsvet"
        assert search_key(ZHUK) == "zhuk"

    def test_latin_text_is_reduced_too(self) -> None:
        assert search_key("Denis") == "denis"

    def test_punctuation_and_digits_survive(self) -> None:
        assert search_key("12#Den#5") == "12#den#5"

    def test_soft_sign_disappears(self) -> None:
        assert search_key(IGOR) == "igor"

    def test_yo_and_ye_reduce_together(self) -> None:
        assert search_key(ALYONA) == search_key(ALENA)

    def test_runs_of_one_letter_collapse(self) -> None:
        # What lets "mariia" meet "maria".
        assert search_key("Anna") == "ana"

    def test_repeated_digits_do_not_collapse(self) -> None:
        # A bib that lost a digit would find the wrong rider.
        assert search_key("11") == "11"
        assert search_key("1988") == "1988"
        assert search_key("100") == "100"

    def test_repeated_separators_do_not_collapse(self) -> None:
        assert search_key("1##Elite") == "1##elite"

    def test_empty(self) -> None:
        assert search_key("") == ""


class TestAlternativeSpellings:
    """One name, several Latin spellings: all of them have to meet."""

    @pytest.mark.parametrize(
        ("cyrillic", "spellings"),
        [
            (MARIA, ["Maria", "Mariya", "Mariia"]),
            (SERGEY, ["Sergey", "Sergei", "Sergej"]),
            (DMITRY, ["Dmitry", "Dmitriy", "Dmitrii"]),
            (YULIA, ["Yulia", "Iuliia", "Julia"]),
            (NIKOLAY, ["Nikolay", "Nikolai"]),
            (EVGENY, ["Evgeny", "Yevgeniy", "Evgenii"]),
        ],
    )
    def test_every_spelling_reduces_to_the_cyrillic_key(
        self, cyrillic: str, spellings: list[str]
    ) -> None:
        for spelling in spellings:
            assert search_key(spelling) == search_key(cyrillic), spelling


class TestSearchForms:
    def test_keeps_the_text_as_typed_and_the_key(self) -> None:
        forms = search_forms("Denis")
        assert forms.plain == "denis"
        assert forms.key == search_key("Denis")

    def test_a_cyrillic_line(self) -> None:
        forms = search_forms(DEN)
        assert forms.plain == DEN.lower()
        assert forms.key == "den"


class TestFormsMatch:
    """The example from the field: registered in Latin, looked up in Cyrillic."""

    LINE = search_forms("12#Denis Chernykh#Elite#5#1#1990#Team#City##0 00:00:00.000#")
    CYRILLIC_LINE = search_forms("12#" + DENIS_CHERNYKH + "#Elite#5#1#1990###")

    def test_cyrillic_fragment_finds_a_latin_line(self) -> None:
        assert forms_match(self.LINE, search_forms(DEN)) is True

    def test_latin_fragment_finds_a_latin_line(self) -> None:
        assert forms_match(self.LINE, search_forms("Chern")) is True

    def test_latin_fragment_finds_a_cyrillic_line(self) -> None:
        assert forms_match(self.CYRILLIC_LINE, search_forms("Den")) is True

    def test_cyrillic_fragment_finds_a_cyrillic_line(self) -> None:
        assert forms_match(self.CYRILLIC_LINE, search_forms(CHERNYKH)) is True

    def test_an_alternative_spelling_finds_the_line(self) -> None:
        assert forms_match(self.CYRILLIC_LINE, search_forms("Chernyh")) is True

    def test_case_is_ignored(self) -> None:
        assert forms_match(self.LINE, search_forms("CHERNYKH")) is True

    def test_a_number_still_matches(self) -> None:
        assert forms_match(self.LINE, search_forms("1990")) is True

    def test_a_bib_does_not_match_a_shorter_one(self) -> None:
        assert (
            forms_match(search_forms("1#Ivanov Ivan#Elite#"), search_forms("11"))
            is False
        )
        assert (
            forms_match(search_forms("11#Petrov Ivan#Elite#"), search_forms("11"))
            is True
        )

    def test_a_year_does_not_match_a_shorter_one(self) -> None:
        assert (
            forms_match(search_forms("1#Ivanov#Elite#5#1#1980##"), search_forms("1988"))
            is False
        )

    def test_an_exact_substring_still_matches(self) -> None:
        assert forms_match(self.LINE, search_forms("#Elite#")) is True

    def test_a_stranger_does_not_match(self) -> None:
        assert forms_match(self.LINE, search_forms("Petrov")) is False
        assert forms_match(self.CYRILLIC_LINE, search_forms("Petrov")) is False

    def test_a_query_that_reduces_to_nothing_matches_nothing(self) -> None:
        # The soft sign has no Latin letter, so its key is empty -- and an empty key
        # is a substring of everything.
        assert forms_match(search_forms("Denis"), search_forms(SOFT)) is False

    def test_the_line_it_does_belong_to_still_matches_it(self) -> None:
        assert forms_match(search_forms(IGOR), search_forms(SOFT)) is True


class TestScriptsIn:
    def test_latin_only(self) -> None:
        assert scripts_in("Denis Chernykh") == {"Latin"}

    def test_cyrillic_only(self) -> None:
        assert scripts_in(DENIS_CHERNYKH) == {"Cyrillic"}

    def test_both(self) -> None:
        assert scripts_in("Denis " + CHERNYKH) == {"Cyrillic", "Latin"}

    def test_accented_latin_is_latin(self) -> None:
        assert scripts_in("Jos\u00e9") == {"Latin"}

    def test_digits_and_punctuation_are_not_a_script(self) -> None:
        assert scripts_in("12#5#1990#") == set()

    def test_anything_else_is_reported_as_other(self) -> None:
        # Greek here; the search cannot transliterate it, and says so.
        assert scripts_in("\u03b1\u03b2") == {"Other"}


class TestSearchIndex:
    LINES: ClassVar[list[str]] = [
        "1#Denis Chernykh#Elite#",
        "2#" + DENIS_CHERNYKH + "#Elite#",
        "3#Petrov Ivan#Elite#",
    ]

    def test_matches_across_scripts(self) -> None:
        index = SearchIndex()
        index.refresh(self.LINES)
        query = search_forms(DEN)
        assert index.matches(0, query) is True
        assert index.matches(1, query) is True
        assert index.matches(2, query) is False

    def test_reports_the_scripts_of_the_list(self) -> None:
        index = SearchIndex()
        index.refresh(self.LINES)
        assert index.scripts == ["Cyrillic", "Latin"]

    def test_scripts_of_an_empty_list(self) -> None:
        index = SearchIndex()
        index.refresh([])
        assert index.scripts == []

    def test_rebuilds_only_when_the_list_changed(self) -> None:
        index = SearchIndex()
        assert index.refresh(self.LINES) is True
        assert index.refresh(list(self.LINES)) is False  # same content, new list
        assert index.refresh([*self.LINES, "4#New Rider#Elite#"]) is True

    def test_an_edit_that_keeps_the_length_is_still_a_change(self) -> None:
        index = SearchIndex()
        index.refresh(["1#Denis Chernykh#Elite#"])
        assert index.refresh(["1#Denis Petrov#Elite#"]) is True
        assert index.matches(0, search_forms("Petrov")) is True

    def test_a_row_outside_the_list_matches_nothing(self) -> None:
        # The widget and the index can disagree for a moment; do not raise.
        index = SearchIndex()
        index.refresh(self.LINES)
        assert index.matches(99, search_forms("Denis")) is False
        assert index.matches(-1, search_forms("Denis")) is False

    def test_a_fresh_index_matches_nothing(self) -> None:
        assert SearchIndex().matches(0, search_forms("Denis")) is False


def test_forms_is_a_plain_pair() -> None:
    assert tuple(Forms("a", "b")) == ("a", "b")
