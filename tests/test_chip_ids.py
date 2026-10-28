"""The rider's timing chips (field 11), ChronometerPython issue #49.

Pure helpers first; the form and the handlers are covered with the Qt window below.
"""

from __future__ import annotations

from app.models import (
    CHIPS_FIELD,
    build_competitor_line,
    foreign_chip_tokens,
    has_chips_field,
    join_chips,
    parse_competitor_line,
    participant_to_open_line,
    split_chips,
)

# A 0.5.x line: references (field 10) but no chips.
OLD = "120#Ivanov Ivan#M40#3#1#1984#T#C##0 00:00:00.000#r41#"


def _line(chips: str = "", number: str = "120", refs: str = "") -> str:
    return build_competitor_line(
        number,
        "Ivanov Ivan",
        "M40#3",
        "1",
        "1984",
        "T",
        "C",
        "",
        "0 00:00:00.000",
        refs,
        chips,
    )


def test_an_old_line_has_no_chip_field_and_a_built_one_always_has_it():
    assert not has_chips_field(OLD)
    assert parse_competitor_line(OLD)["chips"] == ""
    assert parse_competitor_line(OLD)["refs"] == "r41"
    built = _line()
    assert built.count("#") == CHIPS_FIELD + 1
    assert has_chips_field(built)
    assert built.endswith("0 00:00:00.000###")


def test_chips_go_to_field_11_cleaned_and_in_order():
    line = _line("e2801170 0000020a, E2801170000002AB", refs="r1")
    assert line.endswith("#r1#E28011700000020A,E2801170000002AB#")
    assert parse_competitor_line(line)["chips"] == "E28011700000020A,E2801170000002AB"


def test_ids_split_only_on_commas_and_semicolons():
    assert split_chips("E280 1170 0000 020A") == ["E28011700000020A"]
    assert split_chips("a1;b2 ,, c3") == ["A1", "B2", "C3"]
    assert split_chips("e280-1170.00:0a") == ["E2801170000A"]
    assert split_chips(" , ; ") == []


def test_repeats_are_dropped_and_the_first_keeps_its_place():
    assert split_chips("B2, a1, b2, A1") == ["B2", "A1"]
    assert join_chips(["B2", "A1"]) == "B2,A1"


def test_a_cyrillic_look_alike_is_reported_not_dropped():
    # E and A typed with the Russian layout look Latin but are not ASCII; chr() keeps
    # this file ASCII.
    cyr_e, cyr_a = chr(0x415), chr(0x410)
    typed = f"{cyr_e}280A, E2801170000002AB, 1{cyr_a}"
    assert foreign_chip_tokens(typed) == [f"{cyr_e}280A", f"1{cyr_a}"]
    assert foreign_chip_tokens("E280 1170, b2") == []


def test_fields_0_to_10_are_where_they_were():
    plain = _line(refs="r7")
    with_chips = _line("A1,B2", refs="r7")
    for key in (
        "number",
        "name",
        "group",
        "laps",
        "stage",
        "year_of_birth",
        "team",
        "city",
        "comment",
        "time_shift",
        "refs",
    ):
        assert (
            parse_competitor_line(with_chips)[key] == parse_competitor_line(plain)[key]
        )


def test_a_site_line_arrives_with_an_empty_chip_field():
    line = participant_to_open_line(
        {"id": 7, "last_name": "Rider", "first_name": "A", "birth_year": 1990}, []
    )
    assert has_chips_field(line)
    assert line.endswith("#r7##")
    assert parse_competitor_line(line)["chips"] == ""
