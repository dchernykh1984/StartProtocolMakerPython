"""The rider's timing chips (field 11), ChronometerPython issue #49.

Pure helpers first; the form and the handlers are covered with the Qt window below.
"""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app import main_window as mw
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

_app = QApplication.instance() or QApplication([])

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


# -- the form ------------------------------------------------------------------------


@pytest.fixture
def win(monkeypatch):
    from tests.test_window import _empty_backup

    monkeypatch.setattr(mw, "load_backup", lambda path: _empty_backup())
    monkeypatch.setattr(mw.MainWindow, "_write_backup", lambda self, f, n: None)
    monkeypatch.setattr(mw, "write_start_protocol", lambda *a, **k: None)
    w = mw.MainWindow()
    monkeypatch.setattr(mw.QMessageBox, "information", lambda *a, **k: None)
    monkeypatch.setattr(mw.QMessageBox, "warning", lambda *a, **k: None)
    yield w
    w.deleteLater()


def _fill(win, number="120", chips=""):
    win._parse_and_fill_form(_line(number=number))
    win._edit_chips.setText(chips)


def test_saving_writes_the_chips_and_clears_the_field(win):
    _fill(win, chips="e2801170 0000020a, E2801170000002AB")
    win._on_save_to_file()
    saved = win._save_as_items()[0]
    assert saved.endswith("#E28011700000020A,E2801170000002AB#")
    assert win._edit_chips.text() == ""


def test_opening_a_line_fills_the_chip_field(win):
    win._parse_and_fill_form(_line("A1,B2"))
    assert win._edit_chips.text() == "A1,B2"


def test_changing_the_bib_keeps_the_chips(win):
    win._parse_and_fill_form(_line("A1,B2", number="120"))
    win._edit_number.setText("121")
    win._on_save_to_file()
    line = win._save_as_items()[0]
    assert parse_competitor_line(line)["number"] == "121"
    assert parse_competitor_line(line)["chips"] == "A1,B2"


@pytest.mark.parametrize(
    ("typed", "after"),
    [("A1", "A1, "), ("A1, ", "A1, "), ("A1;", "A1;"), ("", "")],
)
def test_enter_in_the_chip_field_adds_one_separator(win, typed, after):
    win._edit_chips.setText(typed)
    win._edit_chips.returnPressed.emit()
    assert win._edit_chips.text() == after
