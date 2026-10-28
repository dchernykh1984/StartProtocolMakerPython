"""The rider's timing chips (field 11), ChronometerPython issue #49: the pure helpers.

The form and the handlers are covered in tests/test_window.py, with the other handlers.
"""

from __future__ import annotations

from app.models import (
    CHIPS_FIELD,
    build_competitor_line,
    foreign_chip_tokens,
    format_chips,
    has_chips_field,
    parse_competitor_line,
    participant_to_open_line,
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


def test_ids_split_only_on_commas_and_semicolons():
    assert format_chips("E280 1170 0000 020A") == "E28011700000020A"
    assert format_chips("E2801170 0000020A") == "E28011700000020A"
    assert format_chips("a1, b2 ,, c3") == "A1,B2,C3"
    assert format_chips("e280-1170.00:0a") == "E2801170000A"
    assert format_chips(" , ; ") == ""


def test_a_dropped_character_inside_an_id_asks_for_a_check():
    from app.models import cleaned_chip_text

    assert cleaned_chip_text("a1, b2 ;c3") is None  # case and separators only
    assert cleaned_chip_text("") is None
    assert cleaned_chip_text("e280 1170, B2") == "E2801170, B2"
    # A repeat is dropped, which may leave a relay rider without chips: shown too.
    assert cleaned_chip_text("A1; A1") == "A1; -"
    assert cleaned_chip_text("a1, a1") == "A1"
    # Two whole ids pasted without a comma: shown joined, so the desk sees it.
    assert cleaned_chip_text("E28011700000020A E2801170000002AB") == (
        "E28011700000020AE2801170000002AB"
    )


def test_repeats_are_dropped_and_the_first_keeps_its_place():
    assert format_chips("B2, a1, b2, A1") == "B2,A1"


def test_a_cyrillic_look_alike_is_reported_not_dropped():
    # E and A typed with the Russian layout look Latin but are not ASCII; chr() keeps
    # this file ASCII.
    cyr_e, cyr_a = chr(0x415), chr(0x410)
    typed = f"{cyr_e}280A, E2801170000002AB, 1{cyr_a}"
    assert foreign_chip_tokens(typed) == [f"{cyr_e}280A", f"1{cyr_a}"]
    assert foreign_chip_tokens("E280 1170, b2") == []


def test_typographic_punctuation_is_dropped_like_ascii_punctuation():
    from app.models import cleaned_chip_text

    en_dash, hyphen = chr(0x2013), chr(0x2010)
    typed = f"E280{en_dash}1170{hyphen}0000020A"
    assert foreign_chip_tokens(typed) == []
    assert format_chips(typed) == "E28011700000020A"
    assert cleaned_chip_text(typed) == "E28011700000020A"


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
    assert format_chips(typed) == "E28011700000020A,B2"


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


def test_a_team_members_chips_become_the_next_rider():
    from app.models import merge_chip_text

    assert merge_chip_text("a1, B2", "b2,c3") == "a1, B2; c3"
    # Kept as typed, so the save still asks before it joins the pieces.
    assert merge_chip_text("", "E280 1170") == "-; E280 1170"
    assert merge_chip_text("A1", "") == "A1; -"
    assert merge_chip_text("A1; -", "C1") == "A1; -; C1"
    # A semicolon typed ahead of the next member is no rider of its own.
    assert merge_chip_text("A1;", "B1") == "A1; B1"
    foreign = f"{chr(0x415)}1"
    assert merge_chip_text(foreign, "A1") == f"{foreign}; A1"


def test_riders_of_a_team_are_separated_by_semicolons():
    assert format_chips("a1, a2; b1;; c1;") == "A1,A2;B1;-;C1"
    assert format_chips("A1; -") == "A1;-"
    assert format_chips("a1; a1") == "A1;-"


def _team(stages: str, chips: str, number: str = "15") -> str:
    return build_competitor_line(
        number,
        "Team",
        "Relay#3",
        stages,
        "1990",
        "T",
        "C",
        "",
        "0 00:00:00.000",
        "",
        chips,
    )


def test_a_relay_binds_each_riders_chips_to_their_stage_bib():
    from app.models import chip_bibs

    assert chip_bibs(_team("3", "A1,A2;B1;C1")) == [
        ("A1", "15"),
        ("A2", "15"),
        ("B1", "16"),
        ("C1", "17"),
    ]
    assert chip_bibs(_team("3", "A1;-;C1")) == [("A1", "15"), ("C1", "17")]
    # A rider past the last stage has no bib to bind to.
    assert chip_bibs(_team("2", "A1;B1;C1")) == [("A1", "15"), ("B1", "16")]
    # One stage: the whole team is one bib.
    assert chip_bibs(_team("1", "A1;B1")) == [("A1", "15"), ("B1", "15")]
    # Stages need a numeric bib, as on the site; otherwise one bib for all.
    assert chip_bibs(_team("3", "A1;B1", number="T15")) == [
        ("A1", "T15"),
        ("B1", "T15"),
    ]
    assert chip_bibs(_team("3", "A1", number="")) == []
    assert chip_bibs(OLD) == []


# -- duplicates (FR-007) ---------------------------------------------------------------


def test_a_chip_on_two_protocol_lines_is_found():
    from app.models import duplicate_chip_row

    lines = [_line("A1,B1", number="1"), _line("C1", number="2")]
    assert duplicate_chip_row(lines) == -1
    assert duplicate_chip_row([*lines, _line("d1, b1", number="3")]) == 2
    assert duplicate_chip_row([OLD, OLD]) == -1


def test_a_foreign_id_is_written_as_typed_never_turned_into_another_chip():
    from app.models import chip_problem_row

    cyr_a = chr(0x410)
    line = _line(f"{cyr_a}1, B2")
    assert parse_competitor_line(line)["chips"] == f"{cyr_a}1,B2"
    assert chip_problem_row([line]) == 0


def test_a_line_whose_chips_no_reader_can_use_is_found():
    from app.models import chip_problem_row

    good = [_line("A1", number="1"), _team("2", "B1;C1", number="5")]
    assert chip_problem_row(good) == -1
    foreign = _line(number="2")[:-1] + f"{chr(0x415)}1#"
    assert chip_problem_row([*good, foreign]) == 2
    assert chip_problem_row([*good, _team("2", "D1;E1;F1", number="8")]) == 2
    # A full-width A copied verbatim: the form would make it plain, readers drop it.
    full_width = _line(number="3")[:-1] + f"{chr(0xFF21)}1#"
    assert chip_problem_row([*good, full_width]) == 2
    # One stage: a team timed as one may list any number of riders.
    assert chip_problem_row([_team("1", "D1;E1;F1")]) == -1


def test_two_foreign_ids_are_not_taken_for_one_chip():
    from app.models import duplicate_chip_row

    cyr_a, cyr_v = chr(0x410), chr(0x412)
    first = _line(number="1")[:-1] + f"{cyr_a}B1#"
    second = _line(number="2")[:-1] + f"{cyr_v}B1#"
    assert duplicate_chip_row([first, second]) == -1


def test_a_relay_riders_chip_on_a_line_of_their_own_bib_is_no_duplicate():
    from app.models import duplicate_chip_row

    lines = [_team("2", "A1;B1"), _line("B1", number="16")]
    assert duplicate_chip_row(lines) == -1
    assert duplicate_chip_row([*lines, _line("B1", number="17")]) == 2


def test_a_chip_on_two_lines_of_one_bib_or_without_a_bib_is_no_duplicate():
    from app.models import NOT_PAID, duplicate_chip_row

    one_bib = [_line("A1", number="15"), _line("A1, B1", number="15")]
    assert duplicate_chip_row(one_bib) == -1
    no_bib = [
        _line("A1", number=""),
        _line("A1", number=NOT_PAID),
        _line("A1", number="7"),
    ]
    assert duplicate_chip_row(no_bib) == -1
