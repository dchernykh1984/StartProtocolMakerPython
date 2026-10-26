"""The site registration a line belongs to (field 10, ``r<id>``), cycling-site #349.

Pure helpers here; the form and the handlers are covered at the end with the Qt window.
"""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app import main_window as mw
from app.models import (
    build_competitor_line,
    duplicate_ref_row,
    has_refs_field,
    merge_open_lines,
    parse_competitor_line,
    participant_to_open_line,
    set_refs,
    split_refs,
)

_app = QApplication.instance() or QApplication([])

OLD = "120#Ivanov Ivan#M40#3#1#1984#T#C##0 00:00:00.000#"


def _line(name: str, year: str = "1990", refs: str = "", number: str = "") -> str:
    return build_competitor_line(
        number, name, "M40#3", "1", year, "T", "C", "", "0 00:00:00.000", refs
    )


def test_an_old_line_has_no_field_and_a_new_one_always_has_it():
    assert not has_refs_field(OLD)
    assert parse_competitor_line(OLD)["refs"] == ""
    unlinked = _line("Ann")
    assert unlinked.endswith("0 00:00:00.000##")
    assert has_refs_field(unlinked)
    assert parse_competitor_line(_line("Ann", refs="r7"))["refs"] == "r7"


def test_tokens_are_tidied_and_unknown_ones_kept():
    assert split_refs(" r1, r2;r1  x9 #") == ["r1", "r2", "x9"]


def test_set_refs_touches_only_the_field():
    assert set_refs(OLD, "r5") == OLD + "r5#"
    linked = set_refs(OLD, "r5")
    assert set_refs(linked, "") == OLD + "#"
    assert parse_competitor_line(set_refs(linked, "r6"))["name"] == "Ivanov Ivan"


def test_a_site_participant_brings_its_registration_id():
    line = participant_to_open_line(
        {"id": 1234, "first_name": "Ivan", "last_name": "Ivanov", "birth_year": 1984},
        [],
    )
    assert parse_competitor_line(line)["refs"] == "r1234"
    no_id = participant_to_open_line({"first_name": "A", "last_name": "B"}, [])
    assert parse_competitor_line(no_id)["refs"] == ""


def test_two_registrations_of_one_person_stay_two_lines():
    first = [_line("Ivanov Ivan", refs="r1")]
    merged, added, _ = merge_open_lines(first, [_line("Ivanov Ivan", refs="r2")])
    assert added == 1 and len(merged) == 2
    again, added, _ = merge_open_lines(merged, [_line("Ivanov Ivan", refs="r1")])
    assert added == 0 and len(again) == 2


def test_an_old_unlinked_line_takes_the_reference_when_it_is_the_only_match():
    merged, added, ambiguous = merge_open_lines(
        [OLD], [_line("Ivanov Ivan", year="1984", refs="r9")]
    )
    assert (added, ambiguous, len(merged)) == (0, 0, 1)
    assert parse_competitor_line(merged[0])["refs"] == "r9"


def test_two_unlinked_lines_with_the_same_name_are_not_guessed():
    merged, added, ambiguous = merge_open_lines(
        [OLD, OLD], [_line("Ivanov Ivan", year="1984", refs="r9")]
    )
    assert (added, ambiguous, len(merged)) == (1, 1, 3)


@pytest.mark.parametrize("order", [("r1", "r2"), ("r2", "r1")])
def test_one_old_line_and_two_same_named_registrations_link_neither(order):
    incoming = [_line("Ivanov Ivan", year="1984", refs=r) for r in order]
    merged, added, ambiguous = merge_open_lines([OLD], incoming)
    assert (added, ambiguous) == (2, 2)
    assert merged[0] == OLD  # the bib stays on the unlinked old line
    assert [parse_competitor_line(m)["refs"] for m in merged[1:]] == list(order)


def test_lines_without_references_merge_by_name_as_before():
    merged, added, _ = merge_open_lines([OLD], [OLD, _line("Petrov")])
    assert (added, len(merged)) == (1, 2)


def test_one_reference_on_two_protocol_lines_is_reported():
    lines = [_line("A", refs="r1", number="1"), _line("B", refs="r2", number="2")]
    assert duplicate_ref_row(lines) == -1
    assert duplicate_ref_row([*lines, _line("C", refs="r2,r3", number="3")]) == 2


# -- the window -----------------------------------------------------------------------


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


def _payload(*people):
    return {
        "participants": [
            {
                "id": pid,
                "first_name": first,
                "last_name": last,
                "birth_year": 1990,
                "category_id": 1,
                "category_name": "Elite",
            }
            for pid, last, first in people
        ],
        "categories": [{"id": 1, "name": "Elite", "laps": 3}],
    }


def test_registration_on_the_spot_keeps_the_reference_on_the_protocol_line(
    win, monkeypatch
):
    monkeypatch.setattr(
        win, "_fetch_site_payload", lambda: _payload((41, "Ivanov", "Ivan"))
    )
    win._on_replace_from_site()
    win._list_open.setCurrentRow(0)
    win._on_edit_open()
    assert win._edit_refs.text() == "r41"
    win._edit_number.setText("120")
    win._edit_name.setText("Ivanov Ivan Jr")  # a typo fixed at the desk
    win._on_save_to_file()
    saved = win._save_as_items()[0]
    assert parse_competitor_line(saved)["refs"] == "r41"
    assert win._edit_refs.text() == ""  # the next rider does not inherit it


def test_clearing_the_field_unlinks_the_line(win, monkeypatch):
    monkeypatch.setattr(
        win, "_fetch_site_payload", lambda: _payload((41, "Ivanov", "Ivan"))
    )
    win._on_replace_from_site()
    win._list_open.setCurrentRow(0)
    win._on_edit_open()
    win._edit_number.setText("120")
    win._edit_refs.clear()
    win._on_save_to_file()
    saved = win._save_as_items()[0]
    assert saved.endswith("##")


def test_a_team_carries_every_members_reference(win, monkeypatch):
    monkeypatch.setattr(
        win, "_fetch_site_payload", lambda: _payload((21, "Kim", "A"), (17, "Lee", "B"))
    )
    win._on_replace_from_site()
    win._list_open.setCurrentRow(0)
    win._on_edit_open()
    win._list_open.setCurrentRow(1)
    win._on_add_into_team()
    assert win._edit_refs.text() == "r21,r17"


@pytest.mark.parametrize("auto_shift", [False, True])
def test_joining_a_team_keeps_its_issued_bib(win, auto_shift):
    win._parse_and_fill_form(_line("First Rider", refs="r1", number="120"))
    win._chk_auto_shift.setChecked(auto_shift)
    win._list_open.addItem(_line("Second Rider", refs="r2"))
    win._list_open.setCurrentRow(0)
    win._on_add_into_team()
    assert win._edit_number.text() == "120"
    assert win._edit_refs.text() == "r1,r2"


def test_the_reference_survives_a_restart(win, monkeypatch, tmp_path):
    from app.models import load_backup, save_backup

    line = _line("Ivanov Ivan", refs="r41", number="120")
    path = tmp_path / "spm_backup.txt"
    save_backup(str(path), [], [line], [], [], "", "", "", "", False, False)
    assert load_backup(str(path))["save_items"] == [line]


def test_a_reference_used_twice_lights_the_duplicate_warning(win):
    win._list_save_as.addItems(
        [_line("A", refs="r1", number="1"), _line("B", refs="r1", number="2")]
    )
    win._refresh_duplicate_indicator()
    assert not win._lbl_error.isHidden()
