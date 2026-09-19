"""Tests for the transliteration-aware search helpers.

Cyrillic fixtures are spelled as escapes to keep this file ASCII (see CLAUDE.md); the
comment next to each names it.
"""

from __future__ import annotations

from typing import ClassVar

from app.search import (
    Forms,
    SearchIndex,
    forms_match,
    scripts_in,
    search_forms,
    transliterate_to_cyrillic,
    transliterate_to_latin,
)

DEN = "\u0414\u0435\u043d"
CHERNYKH = "\u0427\u0435\u0440\u043d\u044b\u0445"
DENIS_CHERNYKH = "\u0414\u0435\u043d\u0438\u0441 \u0427\u0435\u0440\u043d\u044b\u0445"
IGOR = "\u0418\u0433\u043e\u0440\u044c"
ALYONA = "\u0410\u043b\u0451\u043d\u0430"
ALENA = "\u0410\u043b\u0435\u043d\u0430"
SOFT = "\u044c"
SHCHUKIN = "\u0429\u0443\u043a\u0438\u043d"
TSVET = "\u0426\u0432\u0435\u0442"
ZHUK = "\u0416\u0443\u043a"


class TestTransliterateToLatin:
    def test_a_cyrillic_name(self) -> None:
        assert transliterate_to_latin(CHERNYKH) == "chernykh"

    def test_digraphs(self) -> None:
        assert transliterate_to_latin(SHCHUKIN) == "shchukin"
        assert transliterate_to_latin(TSVET) == "tsvet"
        assert transliterate_to_latin(ZHUK) == "zhuk"

    def test_latin_text_is_only_lowercased(self) -> None:
        assert transliterate_to_latin("Denis Chernykh") == "denis chernykh"

    def test_punctuation_and_digits_survive(self) -> None:
        assert transliterate_to_latin("12#" + DEN + "#5") == "12#den#5"

    def test_soft_sign_disappears(self) -> None:
        assert transliterate_to_latin(IGOR) == "igor"

    def test_empty(self) -> None:
        assert transliterate_to_latin("") == ""


class TestTransliterateToCyrillic:
    def test_a_latin_name(self) -> None:
        assert transliterate_to_cyrillic("Chernykh") == CHERNYKH.lower()

    def test_longest_digraph_wins(self) -> None:
        # "kh" must beat "k" then "h", and "shch" must beat "sh".
        assert transliterate_to_cyrillic("Shchukin") == SHCHUKIN.lower()

    def test_cyrillic_text_is_only_lowercased(self) -> None:
        assert transliterate_to_cyrillic(DEN) == DEN.lower()

    def test_yo_and_ye_fold_together(self) -> None:
        # One spelling has to compare equal to the other, or a search for the plain
        # spelling misses the rider entered with the dots.
        assert transliterate_to_cyrillic(ALYONA) == transliterate_to_cyrillic(ALENA)

    def test_punctuation_and_digits_survive(self) -> None:
        assert transliterate_to_cyrillic("12#Den#5") == "12#" + DEN.lower() + "#5"

    def test_empty(self) -> None:
        assert transliterate_to_cyrillic("") == ""


class TestSearchForms:
    def test_three_forms_of_a_latin_line(self) -> None:
        forms = search_forms("Denis")
        assert forms.plain == "denis"
        assert forms.latin == "denis"
        assert forms.cyrillic == transliterate_to_cyrillic("denis")

    def test_three_forms_of_a_cyrillic_line(self) -> None:
        forms = search_forms(DEN)
        assert forms.plain == DEN.lower()
        assert forms.latin == "den"
        assert forms.cyrillic == DEN.lower()


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

    def test_case_is_ignored(self) -> None:
        assert forms_match(self.LINE, search_forms("CHERNYKH")) is True

    def test_a_number_still_matches(self) -> None:
        assert forms_match(self.LINE, search_forms("1990")) is True

    def test_a_stranger_does_not_match(self) -> None:
        assert forms_match(self.LINE, search_forms("Petrov")) is False
        assert forms_match(self.CYRILLIC_LINE, search_forms("Petrov")) is False

    def test_a_query_that_transliterates_to_nothing_matches_nothing(self) -> None:
        # The soft sign has no Latin letter, so its Latin form is empty -- and an
        # empty form is a substring of everything.
        line = search_forms("Denis")
        assert forms_match(line, search_forms(SOFT)) is False

    def test_the_line_it_does_belong_to_still_matches_it(self) -> None:
        assert forms_match(search_forms(IGOR), search_forms(SOFT)) is True


class TestScriptsIn:
    def test_latin_only(self) -> None:
        assert scripts_in("Denis Chernykh") == {"Latin"}

    def test_cyrillic_only(self) -> None:
        assert scripts_in(DENIS_CHERNYKH) == {"Cyrillic"}

    def test_both(self) -> None:
        assert scripts_in("Denis " + CHERNYKH) == {"Cyrillic", "Latin"}

    def test_digits_and_punctuation_are_not_a_script(self) -> None:
        assert scripts_in("12#5#1990#") == set()

    def test_another_script_is_named_too(self) -> None:
        assert scripts_in("\u03b1\u03b2") == {"Greek"}


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

    def test_forms_are_reused_between_searches(self) -> None:
        # The point of the index: reducing the list happens once per change, so a
        # second search must not rebuild it.
        index = SearchIndex()
        index.refresh(self.LINES)
        assert index.refresh(self.LINES) is False
        assert index.matches(1, search_forms("Chernykh")) is True


def test_forms_is_a_plain_triple() -> None:
    assert tuple(Forms("a", "b", "c")) == ("a", "b", "c")
