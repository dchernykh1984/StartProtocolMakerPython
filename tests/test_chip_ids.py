"""The rider's timing chips (field 11), ChronometerPython issue #49: the pure helpers.

The form and the handlers are covered in tests/test_window.py, with the other handlers.
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
    line = _line("e280 1170 0000 020a, E2801170000002AB", refs="r1")
    assert line.endswith("#r1#E28011700000020A,E2801170000002AB#")
    assert parse_competitor_line(line)["chips"] == "E28011700000020A,E2801170000002AB"


def test_ids_split_on_commas_and_semicolons_and_between_long_words():
    assert split_chips("E280 1170 0000 020A") == ["E28011700000020A"]
    assert split_chips("a1;b2 ,, c3") == ["A1", "B2", "C3"]
    assert split_chips("e280-1170.00:0a") == ["E2801170000A"]
    assert split_chips(" , ; ") == []
    # Two whole ids pasted with a space are two ids, not one made-up one.
    assert split_chips("E28011700000020A E2801170000002AB") == [
        "E28011700000020A",
        "E2801170000002AB",
    ]
    assert split_chips("E280 1170 0000 020A E2801170000002AB") == [
        "E28011700000020A",
        "E2801170000002AB",
    ]
    assert split_chips("ABC1234 9 BCD") == ["ABC1234", "9BCD"]


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


def test_invisible_and_full_width_characters_are_plain_ones():
    nbsp, zwsp, bom, fw_comma, fw_a = (
        chr(0xA0),
        chr(0x200B),
        chr(0xFEFF),
        chr(0xFF0C),
        chr(0xFF21),
    )
    typed = f"{bom}E280{nbsp}1170{zwsp} 0000 020{fw_a}{fw_comma}b2"
    assert foreign_chip_tokens(typed) == []
    assert split_chips(typed) == ["E28011700000020A", "B2"]


def test_a_foreign_character_is_named_in_the_message():
    from app.models import describe_foreign_chip

    token = f"{chr(0x415)}280A"
    assert describe_foreign_chip(token) == f"{token}  (CYRILLIC CAPITAL LETTER IE)"


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


# -- the readers of fields 0-10 (FinishProtocolGenerator, the site) -----------------


def _generator_fields(line: str) -> list[str]:
    """FinishProtocolGeneratorPython's StartProtocolElement.from_line: fields 0-9."""
    parts = line.split("#")
    return [parts[i] if i < len(parts) else "" for i in range(10)]


def _site_fields(line: str) -> tuple[str, str, str, bool]:
    """cycling-site event_photos/bindings.py parse_line: bib, stage, refs by index."""
    fields = line.split("#")
    refs_present = line.count("#") >= 11
    return fields[0], fields[4], fields[10] if refs_present else "", refs_present


def test_the_generator_and_the_site_read_a_line_with_chips_as_without():
    plain = _line(refs="r7")
    with_chips = _line("E28011700000020A,E2801170000002AB", refs="r7")
    assert _generator_fields(with_chips) == _generator_fields(plain)
    assert _site_fields(with_chips) == _site_fields(plain)
    assert _site_fields(with_chips) == ("120", "1", "r7", True)


def test_a_0_5_backup_line_loads_and_has_no_chips(tmp_path):
    from app.models import load_backup, save_backup

    path = tmp_path / "spm_backup.txt"
    save_backup(str(path), [OLD], [OLD], [], [], "", "", "", "", False, False)
    loaded = load_backup(str(path))
    assert loaded["open_items"] == [OLD]
    assert loaded["save_items"] == [OLD]
    assert parse_competitor_line(loaded["save_items"][0])["chips"] == ""


# -- copies and merges keep the field (FR-004, FR-005) -------------------------------

# A line from a later version: something after the chips must survive copies too.
LATER = _line("A1,B2", refs="r9") + "future#"


def test_the_backup_and_the_start_protocol_file_keep_the_chips(tmp_path):
    from app.models import load_backup, save_backup, write_start_protocol

    backup = tmp_path / "spm_backup.txt"
    save_backup(str(backup), [LATER], [LATER], [], [], "", "", "", "", False, False)
    assert load_backup(str(backup))["save_items"] == [LATER]
    start = tmp_path / "start.txt"
    write_start_protocol(str(start), [LATER, OLD])
    assert start.read_text(encoding="utf-8").splitlines() == [LATER, OLD]


def _site_line(name: str, ref: str) -> str:
    return build_competitor_line(
        "", name, "M40#3", "1", "1990", "T", "C", "", "0 00:00:00.000", ref
    )


def test_a_merge_from_the_site_keeps_the_chips_of_a_known_line():
    from app.models import merge_open_lines

    mine = build_competitor_line(
        "", "Kim A", "M40#3", "1", "1990", "T", "C", "", "0 00:00:00.000", "r21", "A1"
    )
    merged, added, _ = merge_open_lines([mine], [_site_line("Kim A", "r21")])
    assert (merged, added) == ([mine], 0)


def test_linking_an_old_line_to_its_registration_keeps_its_chips():
    from app.models import merge_open_lines

    old = build_competitor_line(
        "", "Lee B", "M40#3", "1", "1990", "T", "C", "", "0 00:00:00.000", "", "B1,B2"
    )
    merged, added, _ = merge_open_lines([old], [_site_line("Lee B", "r17")])
    assert added == 0
    assert parse_competitor_line(merged[0])["refs"] == "r17"
    assert parse_competitor_line(merged[0])["chips"] == "B1,B2"


# -- teams (FR-006) --------------------------------------------------------------------


def test_merging_chip_text_keeps_order_drops_repeats_and_keeps_foreign_ids():
    from app.models import merge_chip_text

    assert merge_chip_text("a1, B2", "b2;c3") == "A1, B2, C3"
    assert merge_chip_text("", "E280 1170") == "E2801170"
    assert merge_chip_text(", ;", "") == ""
    foreign = f"{chr(0x415)}1"
    assert merge_chip_text(foreign, "A1") == f"{foreign}, A1"


# -- duplicates (FR-007) ---------------------------------------------------------------


def test_a_chip_on_two_protocol_lines_is_found():
    from app.models import duplicate_chip_row

    lines = [_line("A1,B1", number="1"), _line("C1", number="2")]
    assert duplicate_chip_row(lines) == -1
    assert duplicate_chip_row([*lines, _line("d1, b1", number="3")]) == 2
    assert duplicate_chip_row([OLD, OLD]) == -1
