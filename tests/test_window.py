"""Qt-level tests for the load-from-site handlers in MainWindow.

The pure conversion helper (categories_to_group_rows) is tested in test_models;
here we verify the handlers wire it to the widgets correctly -- in
particular that Replace still syncs groups when the site has no participants yet.
main_window is excluded from coverage, so these guard against silent handler drift.
"""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from app import main_window as mw
from app import search as app_search

_app = QApplication.instance() or QApplication([])

# Captured before the fixture stubs it out, for the tests that check what is saved.
_REAL_WRITE_BACKUP = mw.MainWindow._write_backup


def _empty_backup() -> dict:
    return {
        "open_items": [],
        "save_items": [],
        "groups": [],
        "numbers": [],
        "regexp_from": "",
        "regexp_to": "",
        "ftp_address": "",
        "http_site_url": "https://s",
        "http_token": "tok",
        "device_id": "dev",
        "client_revision": 0,
        "start_protocol_file": "",
        "use_all_numbers": False,
        "auto_shift": False,
        "first_number": "",
        "delay": "",
    }


@pytest.fixture
def win(monkeypatch):
    # Never touch disk: stub the backup/protocol writers and the backup loader.
    monkeypatch.setattr(mw, "load_backup", lambda path: _empty_backup())
    monkeypatch.setattr(
        mw.MainWindow, "_write_backup", lambda self, folder, filename: None
    )
    monkeypatch.setattr(mw, "write_start_protocol", lambda *a, **k: None)
    w = mw.MainWindow()
    monkeypatch.setattr(mw.QMessageBox, "information", lambda *a, **k: None)
    monkeypatch.setattr(mw.QMessageBox, "warning", lambda *a, **k: None)
    yield w
    w.deleteLater()


def _group_rows(win) -> list[tuple[str, str]]:
    rows = []
    for i in range(win._list_groups.count()):
        item = win._list_groups.item(i)
        rows.append((item.text(), item.data(Qt.ItemDataRole.UserRole)))
    return rows


# -- Replace syncs groups even with no participants (review point 1) -------


def test_replace_syncs_groups_when_no_participants(win, monkeypatch):
    win._list_open.addItem("99#Keep Me#G#3#1#1990#T#C#c#0 00:00:00.000#")
    payload = {
        "participants": [],
        "categories": [
            {"id": 1, "name": "Elite", "laps": 5, "bib_from": 1, "bib_to": 50}
        ],
    }
    monkeypatch.setattr(win, "_fetch_site_payload", lambda: payload)
    win._on_replace_from_site()
    # participant list is left untouched when the site returns no participants...
    assert win._list_open.count() == 1
    assert win._list_open.item(0).text().startswith("99#Keep Me")
    # ...but the group is synced.
    assert [t for t, _ in _group_rows(win)] == ["Elite#5"]


def test_replace_clears_groups_on_empty_categories_with_participants(win, monkeypatch):
    # A successful response with no categories must clear groups from a prior start.
    win._add_group_row("Old#3", "1-9")
    payload = {
        "participants": [
            {
                "category_id": None,
                "category_name": "",
                "last_name": "New",
                "first_name": "Rider",
                "birth_year": 1991,
                "team": "",
                "city": "",
            }
        ],
        "categories": [],
    }
    monkeypatch.setattr(win, "_fetch_site_payload", lambda: payload)
    win._on_replace_from_site()
    assert "New Rider" in win._list_open.item(0).text()
    assert _group_rows(win) == []  # stale groups cleared


def test_replace_clears_groups_on_empty_categories_without_participants(
    win, monkeypatch
):
    win._list_open.addItem("99#Keep Me#G#3#1#1990#T#C#c#0 00:00:00.000#")
    win._add_group_row("Old#3", "1-9")
    payload = {"participants": [], "categories": []}
    monkeypatch.setattr(win, "_fetch_site_payload", lambda: payload)
    win._on_replace_from_site()
    # participant list untouched (no participants returned), but stale groups cleared.
    assert win._list_open.count() == 1
    assert _group_rows(win) == []


def test_replace_replaces_participants_when_present(win, monkeypatch):
    win._list_open.addItem("99#Old One#G#3#1#1990#T#C#c#0 00:00:00.000#")
    payload = {
        "participants": [
            {
                "category_id": 1,
                "category_name": "Elite",
                "last_name": "New",
                "first_name": "Rider",
                "birth_year": 1991,
                "team": "",
                "city": "",
            }
        ],
        "categories": [
            {"id": 1, "name": "Elite", "laps": 5, "bib_from": 1, "bib_to": 50}
        ],
    }
    monkeypatch.setattr(win, "_fetch_site_payload", lambda: payload)
    win._on_replace_from_site()
    assert win._list_open.count() == 1
    assert "New Rider" in win._list_open.item(0).text()
    assert [t for t, _ in _group_rows(win)] == ["Elite#5"]


# -- Groups carry the site's bib range into the numbers list (review point 2)


def test_replace_uses_site_bib_range_for_new_groups(win, monkeypatch):
    payload = {
        "participants": [],
        "categories": [
            {"id": 1, "name": "Elite", "laps": 5, "bib_from": 100, "bib_to": 199}
        ],
    }
    monkeypatch.setattr(win, "_fetch_site_payload", lambda: payload)
    win._on_replace_from_site()
    assert _group_rows(win) == [("Elite#5", "100-199")]


def _elite_payload(bib_from=100, bib_to=199) -> dict:
    cat = {"id": 1, "name": "Elite", "laps": 5}
    if bib_from is not None:
        cat["bib_from"] = bib_from
    if bib_to is not None:
        cat["bib_to"] = bib_to
    return {"participants": [], "categories": [cat]}


def test_replace_updates_the_range_of_a_group_already_present(win, monkeypatch):
    # The organizer moved the category's bibs on the site; a re-download has to
    # follow, or "Get number" keeps handing out bibs from the old range.
    win._add_group_row("Elite#5", "1-50")
    monkeypatch.setattr(win, "_fetch_site_payload", lambda: _elite_payload())
    win._on_replace_from_site()
    assert _group_rows(win) == [("Elite#5", "100-199")]


def test_replace_keeps_the_autoshift_override_of_a_kept_group(win, monkeypatch):
    # Only the interval comes from the site; "#first#delay" is the referee's own.
    win._add_group_row("Elite#5", "1-50#10#60")
    monkeypatch.setattr(win, "_fetch_site_payload", lambda: _elite_payload(1, 200))
    win._on_replace_from_site()
    assert _group_rows(win) == [("Elite#5", "1-200#10#60")]


def test_replace_rebases_a_first_bib_left_outside_the_new_range(win, monkeypatch):
    # The category was renumbered; keeping first=10 against 100-199 would start the
    # whole group 90 delay steps late.
    win._add_group_row("Elite#5", "1-50#10#60")
    monkeypatch.setattr(win, "_fetch_site_payload", lambda: _elite_payload())
    win._on_replace_from_site()
    assert _group_rows(win) == [("Elite#5", "100-199#100#60")]


def test_replace_keeps_the_local_range_when_the_site_has_none(win, monkeypatch):
    # A category without bib_from/bib_to says nothing about the range, so a
    # hand-tuned local one must not be replaced by the default.
    win._add_group_row("Elite#5", "7-7")
    monkeypatch.setattr(
        win, "_fetch_site_payload", lambda: _elite_payload(bib_from=None, bib_to=None)
    )
    win._on_replace_from_site()
    assert _group_rows(win) == [("Elite#5", "7-7")]


def test_replace_falls_back_to_the_default_for_a_new_group_without_a_range(
    win, monkeypatch
):
    monkeypatch.setattr(
        win, "_fetch_site_payload", lambda: _elite_payload(bib_from=None, bib_to=None)
    )
    win._on_replace_from_site()
    assert _group_rows(win) == [("Elite#5", mw.DEFAULT_NUMBER_RANGE)]


def test_merge_uses_site_bib_range_for_new_groups(win, monkeypatch):
    win._add_group_row("Old#1", "1-9")
    payload = {
        "participants": [],
        "categories": [
            {"id": 2, "name": "Elite", "laps": 5, "bib_from": 100, "bib_to": 199}
        ],
    }
    monkeypatch.setattr(win, "_fetch_site_payload", lambda: payload)
    win._on_merge_from_site()
    assert _group_rows(win) == [("Old#1", "1-9"), ("Elite#5", "100-199")]


def test_merge_updates_the_range_of_a_group_already_present(win, monkeypatch):
    win._add_group_row("Elite#5", "1-50")
    monkeypatch.setattr(win, "_fetch_site_payload", lambda: _elite_payload())
    win._on_merge_from_site()
    assert _group_rows(win) == [("Elite#5", "100-199")]


def test_merge_keeps_the_autoshift_override_of_an_existing_group(win, monkeypatch):
    win._add_group_row("Elite#5", "1-50#10#60")
    monkeypatch.setattr(win, "_fetch_site_payload", lambda: _elite_payload(1, 200))
    win._on_merge_from_site()
    assert _group_rows(win) == [("Elite#5", "1-200#10#60")]


def test_replace_keeps_a_deliberate_offset_when_the_range_did_not_move(
    win, monkeypatch
):
    win._add_group_row("Elite#5", "101-150#100#60")
    monkeypatch.setattr(win, "_fetch_site_payload", lambda: _elite_payload(101, 150))
    win._on_replace_from_site()
    assert _group_rows(win) == [("Elite#5", "101-150#100#60")]


def test_merge_rebases_a_first_bib_left_outside_the_new_range(win, monkeypatch):
    win._add_group_row("Elite#5", "1-50#10#60")
    monkeypatch.setattr(win, "_fetch_site_payload", lambda: _elite_payload())
    win._on_merge_from_site()
    assert _group_rows(win) == [("Elite#5", "100-199#100#60")]


def test_merge_keeps_the_local_range_when_the_site_has_none(win, monkeypatch):
    win._add_group_row("Elite#5", "7-7")
    monkeypatch.setattr(
        win, "_fetch_site_payload", lambda: _elite_payload(bib_from=None, bib_to=None)
    )
    win._on_merge_from_site()
    assert _group_rows(win) == [("Elite#5", "7-7")]


def test_merge_counts_only_groups_it_added(win, monkeypatch):
    # Refreshing a range is not adding a group; the message must not claim it is.
    win._add_group_row("Elite#5", "1-50")
    messages: list[str] = []
    monkeypatch.setattr(
        mw.QMessageBox, "information", lambda *a, **k: messages.append(a[2])
    )
    monkeypatch.setattr(win, "_fetch_site_payload", lambda: _elite_payload())
    win._on_merge_from_site()
    assert "0 new group(s)" in messages[0]


def test_merge_refreshes_every_row_of_a_duplicated_group(win, monkeypatch):
    # Nothing stops a group text being added twice, and "Get number" resolves it with
    # findItems(...)[0] -- so refreshing only one row leaves the used one stale.
    win._add_group_row("Elite#5", "1-50")
    win._add_group_row("Elite#5", "1-50")
    monkeypatch.setattr(win, "_fetch_site_payload", lambda: _elite_payload())
    win._on_merge_from_site()
    assert _group_rows(win) == [("Elite#5", "100-199"), ("Elite#5", "100-199")]


def test_replace_keeps_the_first_duplicate_override(win, monkeypatch):
    # Same resolution order on the replace path: the row lookups would have used.
    win._add_group_row("Elite#5", "1-50#10#60")
    win._add_group_row("Elite#5", "1-50#20#90")
    monkeypatch.setattr(win, "_fetch_site_payload", lambda: _elite_payload(1, 200))
    win._on_replace_from_site()
    assert _group_rows(win) == [("Elite#5", "1-200#10#60")]


def test_merge_leaves_a_group_the_site_no_longer_has(win, monkeypatch):
    win._add_group_row("Old#1", "1-9#2#30")
    monkeypatch.setattr(win, "_fetch_site_payload", lambda: _elite_payload())
    win._on_merge_from_site()
    assert _group_rows(win) == [("Old#1", "1-9#2#30"), ("Elite#5", "100-199")]


# -- AutoShift keeps the form values a group range does not override ---------


def _type(edit, text: str) -> None:
    """Fill a field the way the referee does, so textEdited fires."""
    edit.clear()
    QTest.keyClicks(edit, text)


def _prepare_auto_shift(win, numbers_range: str, first: str = "", delay: str = ""):
    """Arm the window with one group and AutoShift on, as a referee would."""
    win._add_group_row("Elite#5", numbers_range)
    win._combo_group.setCurrentIndex(win._combo_group.findText("Elite#5"))
    _type(win._edit_first_number, first)
    _type(win._edit_delay, delay)
    win._chk_auto_shift.setChecked(True)


def test_auto_shift_keeps_form_values_without_group_override(win):
    _prepare_auto_shift(win, "1-50", first="1", delay="30")
    win._edit_number.setText("3")
    win._on_auto_shift()
    assert win._edit_first_number.text() == "1"
    assert win._edit_delay.text() == "30"
    assert win._edit_time_shift.text() == "0 00:01:00.000"


def test_auto_shift_uses_group_override(win):
    _prepare_auto_shift(win, "1-50#10#60", first="1", delay="30")
    win._edit_number.setText("12")
    win._on_auto_shift()
    assert win._edit_first_number.text() == "10"
    assert win._edit_delay.text() == "60"
    assert win._edit_time_shift.text() == "0 00:02:00.000"


def test_auto_shift_partial_override_keeps_delay(win):
    # "range#first" sets the first number only; the delay stays as typed.
    _prepare_auto_shift(win, "1-50#10", first="1", delay="30")
    win._edit_number.setText("12")
    win._on_auto_shift()
    assert win._edit_first_number.text() == "10"
    assert win._edit_delay.text() == "30"


def test_auto_shift_ignores_blank_override_fields(win):
    _prepare_auto_shift(win, "1-50##", first="1", delay="30")
    win._on_auto_shift()
    assert win._edit_first_number.text() == "1"
    assert win._edit_delay.text() == "30"


def test_group_override_does_not_leak_into_the_next_group(win):
    # Elite carries its own first/delay; Masters does not and must fall back to the
    # values the referee typed, not to Elite's.
    _prepare_auto_shift(win, "1-50#10#60", first="1", delay="30")
    win._add_group_row("Masters#3", "51-99")
    win._edit_number.setText("12")
    win._on_auto_shift()
    assert (win._edit_first_number.text(), win._edit_delay.text()) == ("10", "60")
    win._combo_group.setCurrentIndex(win._combo_group.findText("Masters#3"))
    win._edit_number.setText("52")
    win._on_auto_shift()
    assert (win._edit_first_number.text(), win._edit_delay.text()) == ("1", "30")
    assert win._edit_time_shift.text() == "0 00:25:30.000"  # (52 - 1) * 30 s


def test_a_group_override_is_not_saved_as_the_referees_own_values(win, monkeypatch):
    # Otherwise the override comes back as the baseline after a restart and leaks
    # into every group that has none.
    saved: dict = {}
    monkeypatch.setattr(mw, "save_backup", lambda **kwargs: saved.update(kwargs))
    _prepare_auto_shift(win, "1-50#10#60", first="1", delay="30")
    win._add_group_row("Masters#3", "51-99")
    win._on_auto_shift()
    assert (win._edit_first_number.text(), win._edit_delay.text()) == ("10", "60")

    _REAL_WRITE_BACKUP(win, "data", "spm_backup.txt")
    assert (saved["first_number"], saved["delay"]) == ("1", "30")

    # Restart: the saved values come back, and Masters still gets them.
    restored = _empty_backup()
    restored["first_number"] = saved["first_number"]
    restored["delay"] = saved["delay"]
    win._fill_from_backup(restored)
    win._combo_group.setCurrentIndex(win._combo_group.findText("Masters#3"))
    win._edit_number.setText("52")
    win._on_auto_shift()
    assert (win._edit_first_number.text(), win._edit_delay.text()) == ("1", "30")
    assert win._edit_time_shift.text() == "0 00:25:30.000"


def test_typing_after_an_override_wins_over_it(win):
    _prepare_auto_shift(win, "1-50#10#60", first="1", delay="30")
    win._on_auto_shift()
    _type(win._edit_delay, "15")
    win._add_group_row("Masters#3", "51-99")
    win._combo_group.setCurrentIndex(win._combo_group.findText("Masters#3"))
    win._on_auto_shift()
    assert win._edit_delay.text() == "15"


# -- Editing a competitor with AutoShift on ---------------------------------


def test_edit_keeps_the_number_the_line_already_has(win):
    _prepare_auto_shift(win, "1-50", first="1", delay="30")
    win._list_save_as.addItem("7#Runner One#Elite#5#1#1990#T#C##0 00:00:00.000#")
    win._list_save_as.setCurrentRow(0)
    win._on_edit_save_as()
    assert win._edit_number.text() == "7"
    assert win._edit_time_shift.text() == "0 00:03:00.000"  # (7 - 1) * 30 s


def test_edit_assigns_a_number_when_the_line_has_none(win):
    _prepare_auto_shift(win, "1-50", first="1", delay="30")
    win._list_open.addItem("#Runner One#Elite#5#1#1990#T#C##0 00:00:00.000#")
    win._list_open.setCurrentRow(0)
    win._on_edit_open()
    assert win._edit_number.text() == "1"


def test_edit_restores_the_line_shift_when_auto_shift_cannot_compute(win):
    # Nothing to compute from (no delay), so the form must show the edited line's
    # own shift rather than the previously edited competitor's.
    _prepare_auto_shift(win, "1-50")
    win._list_save_as.addItem("7#First#Elite#5#1#1990#T#C##0 00:05:00.000#")
    win._list_save_as.addItem("8#Second#Elite#5#1#1990#T#C##0 00:00:00.000#")
    win._list_save_as.setCurrentRow(0)
    win._on_edit_save_as()
    assert win._edit_time_shift.text() == "0 00:05:00.000"
    win._list_save_as.setCurrentRow(1)
    win._on_edit_save_as()
    assert win._edit_time_shift.text() == "0 00:00:00.000"


# -- Auto upload of the start list to the site ------------------------------


class _Recorder:
    """Stand-in for upload_start_list that records calls (and can fail on demand)."""

    def __init__(self, error: str = "") -> None:
        self.calls: list[tuple] = []
        self.error = error

    def __call__(self, site_url, token, device_id, items, client_revision):
        self.calls.append((site_url, token, device_id, list(items), client_revision))
        if self.error:
            raise ValueError(self.error)
        return len(items)


@pytest.fixture
def uploads(monkeypatch):
    recorder = _Recorder()
    monkeypatch.setattr(mw, "upload_start_list", recorder)
    return recorder


def _arm_auto_send(win):
    """Turn auto mode on with one competitor queued, and clear the initial schedule."""
    win._list_save_as.addItem("1#Runner One#Elite#5#1#1990#T#C##0 00:00:00.000#")
    win._chk_auto_send.setChecked(True)
    win._auto_send_timer.stop()
    win._auto_send_pending = False


def test_auto_send_off_does_not_upload(win, uploads):
    win._list_save_as.addItem("1#Runner One#Elite#5#1#1990#T#C##0 00:00:00.000#")
    win._save_all_data()
    assert win._auto_send_timer.isActive() is False
    win._on_auto_send_timeout()
    assert uploads.calls == []


def test_auto_send_uploads_after_an_edit(win, uploads):
    _arm_auto_send(win)
    win._save_all_data()
    assert win._auto_send_timer.isActive() is True  # debounced, not sent yet
    assert uploads.calls == []
    win._on_auto_send_timeout()
    assert len(uploads.calls) == 1
    site_url, token, device_id, items, revision = uploads.calls[0]
    assert (site_url, token, device_id) == ("https://s", "tok", "dev")
    assert items == win._save_as_items()
    assert revision == 1
    assert "Sent 1 competitor(s)" in win._lbl_auto_send_status.text()


def test_auto_send_debounces_a_burst_of_edits(win, uploads):
    _arm_auto_send(win)
    for _ in range(3):
        win._save_all_data()
    win._on_auto_send_timeout()
    assert len(uploads.calls) == 1


def test_auto_send_does_not_reschedule_itself(win, uploads):
    # The upload persists the bumped revision, which must not queue another upload.
    _arm_auto_send(win)
    win._save_all_data()
    win._on_auto_send_timeout()
    assert win._auto_send_pending is False
    assert win._auto_send_timer.isActive() is False
    win._on_auto_send_timeout()
    assert len(uploads.calls) == 1


def test_auto_send_leaves_the_protocol_selection_alone(win, uploads):
    # The duplicate check jumps to the offending row; an upload two seconds after the
    # last edit must not move the selection under the referee's hands.
    line = "1#Runner One#Elite#5#1#1990#T#C##0 00:00:00.000#"
    win._list_save_as.addItem(line)
    win._list_save_as.addItem(line)
    win._list_save_as.addItem("2#Runner Two#Elite#5#1#1991#T#C##0 00:00:00.000#")
    win._chk_auto_send.setChecked(True)
    win._save_all_data()
    win._list_save_as.setCurrentRow(2)
    win._on_auto_send_timeout()
    assert len(uploads.calls) == 1
    assert win._list_save_as.currentRow() == 2


def test_auto_send_retries_after_a_failure(win, uploads):
    _arm_auto_send(win)
    uploads.error = "Connection error: timed out"
    win._save_all_data()
    win._on_auto_send_timeout()
    assert len(uploads.calls) == 1
    assert win._auto_send_pending is True  # still owed to the site
    assert "will retry" in win._lbl_auto_send_status.text()
    uploads.error = ""
    win._save_all_data()
    win._on_auto_send_timeout()
    assert len(uploads.calls) == 2
    assert win._auto_send_pending is False


def test_auto_send_retries_on_its_own_after_a_failure(win, uploads):
    # Waiting for the next edit would leave the site stale once registration goes
    # quiet, which is exactly when the start list has to be right.
    _arm_auto_send(win)
    uploads.error = "Connection error: timed out"
    win._save_all_data()
    win._on_auto_send_timeout()
    assert win._auto_send_timer.isActive() is True
    uploads.error = ""
    win._on_auto_send_timeout()  # the retry, with no edit in between
    assert len(uploads.calls) == 2
    assert win._auto_send_pending is False
    assert win._auto_send_timer.isActive() is False


def test_a_failed_manual_send_is_retried_by_auto_mode(win, uploads):
    _arm_auto_send(win)
    uploads.error = "Connection error: timed out"
    win._on_send_to_site()
    assert win._auto_send_timer.isActive() is True
    uploads.error = ""
    win._on_auto_send_timeout()
    assert len(uploads.calls) == 2


def test_a_failed_manual_send_is_not_retried_with_auto_off(win, uploads):
    win._list_save_as.addItem("1#Runner One#Elite#5#1#1990#T#C##0 00:00:00.000#")
    uploads.error = "Connection error: timed out"
    win._on_send_to_site()
    assert win._auto_send_timer.isActive() is False


def test_auto_send_reports_failures_without_a_dialog(win, uploads, monkeypatch):
    def _fail(*a, **k):
        raise AssertionError("auto mode must not open a dialog")

    monkeypatch.setattr(mw.QMessageBox, "warning", _fail)
    monkeypatch.setattr(mw.QMessageBox, "information", _fail)
    _arm_auto_send(win)
    uploads.error = "HTTP 409: Conflict"
    win._save_all_data()
    win._on_auto_send_timeout()
    assert "HTTP 409: Conflict" in win._lbl_auto_send_status.text()


def test_auto_send_needs_url_and_token(win, uploads):
    _arm_auto_send(win)
    win._edit_http_token.setText("")
    win._save_all_data()
    assert win._auto_send_timer.isActive() is False
    assert win._lbl_auto_send_status.text() == "auto: set Site URL and Token"
    win._on_auto_send_timeout()
    assert uploads.calls == []


def test_auto_send_keeps_edits_made_before_the_site_is_configured(win, uploads):
    _arm_auto_send(win)
    win._edit_http_token.setText("")
    win._save_all_data()
    assert win._auto_send_pending is True  # owed, just not sendable yet
    assert win._auto_send_timer.isActive() is False
    win._edit_http_token.setText("tok")
    win._on_save_config()
    assert win._auto_send_timer.isActive() is True
    win._on_auto_send_timeout()
    assert len(uploads.calls) == 1


def test_turning_auto_send_on_uploads_the_current_list(win, uploads):
    win._list_save_as.addItem("1#Runner One#Elite#5#1#1990#T#C##0 00:00:00.000#")
    win._chk_auto_send.setChecked(True)
    assert win._auto_send_timer.isActive() is True
    win._on_auto_send_timeout()
    assert len(uploads.calls) == 1


def test_turning_auto_send_off_drops_the_queued_upload(win, uploads):
    _arm_auto_send(win)
    win._save_all_data()
    win._chk_auto_send.setChecked(False)
    assert win._auto_send_timer.isActive() is False
    assert win._lbl_auto_send_status.text() == ""
    win._on_auto_send_timeout()
    assert uploads.calls == []


def test_loading_a_backup_does_not_upload(win, uploads, monkeypatch):
    # Restoring a saved list is not an edit: the site already has it.
    data = _empty_backup()
    data["auto_send"] = True
    data["save_items"] = ["1#Runner One#Elite#5#1#1990#T#C##0 00:00:00.000#"]
    monkeypatch.setattr(mw, "load_backup", lambda path: data)
    win._load_backup("/backup.txt")
    assert win._chk_auto_send.isChecked() is True  # the setting is restored...
    assert win._auto_send_timer.isActive() is False  # ...without an upload
    assert win._auto_send_pending is False
    win._on_auto_send_timeout()
    assert uploads.calls == []


def test_loading_a_backup_drops_a_queued_upload(win, uploads, monkeypatch):
    # An upload queued from the previous list must not be sent under the loaded one.
    _arm_auto_send(win)
    win._save_all_data()
    assert win._auto_send_timer.isActive() is True
    data = _empty_backup()
    data["auto_send"] = True
    data["save_items"] = ["9#Other Race#Elite#5#1#1990#T#C##0 00:00:00.000#"]
    monkeypatch.setattr(mw, "load_backup", lambda path: data)
    win._load_backup("/other-backup.txt")
    assert win._auto_send_timer.isActive() is False
    assert win._auto_send_pending is False
    win._on_auto_send_timeout()
    assert uploads.calls == []


def test_loading_a_backup_clears_a_stale_status(win, uploads, monkeypatch):
    _arm_auto_send(win)
    win._save_all_data()
    win._on_auto_send_timeout()
    assert "Sent" in win._lbl_auto_send_status.text()
    data = _empty_backup()
    data["auto_send"] = True  # unchanged, so the checkbox emits no signal
    monkeypatch.setattr(mw, "load_backup", lambda path: data)
    win._load_backup("/other-backup.txt")
    assert win._lbl_auto_send_status.text() == ""


def test_adding_a_competitor_to_the_protocol_triggers_auto_send(win, uploads):
    win._list_open.addItem("1#Runner One#Elite#5#1#1990#T#C##0 00:00:00.000#")
    win._list_open.setCurrentRow(0)
    win._chk_auto_send.setChecked(True)
    win._auto_send_timer.stop()
    win._auto_send_pending = False
    win._on_open_to_protocol()
    assert win._auto_send_timer.isActive() is True
    win._on_auto_send_timeout()
    assert uploads.calls[0][3] == win._save_as_items()


def test_manual_send_still_uploads_and_reports(win, uploads):
    win._list_save_as.addItem("1#Runner One#Elite#5#1#1990#T#C##0 00:00:00.000#")
    win._on_send_to_site()
    assert len(uploads.calls) == 1
    assert uploads.calls[0][4] == 1


def test_manual_send_clears_a_queued_auto_send(win, uploads):
    _arm_auto_send(win)
    win._save_all_data()
    win._on_send_to_site()
    assert win._auto_send_timer.isActive() is False
    assert win._auto_send_pending is False
    win._on_auto_send_timeout()
    assert len(uploads.calls) == 1


def test_closing_flushes_a_queued_auto_send(win, uploads, monkeypatch):
    _arm_auto_send(win)
    win._save_all_data()
    monkeypatch.setattr(
        mw.QMessageBox,
        "question",
        lambda *a, **k: mw.QMessageBox.StandardButton.Yes,
    )

    class _Event:
        def accept(self) -> None:
            self.accepted = True

        def ignore(self) -> None:
            self.accepted = False

    win.closeEvent(_Event())
    assert len(uploads.calls) == 1


# -- Transliteration-aware search ------------------------------------------

# Cyrillic fixtures as escapes, to keep this file ASCII (see CLAUDE.md).
_DEN = "\u0414\u0435\u043d"  # Den
# Denis Chernykh
_DENIS_CHERNYKH = "\u0414\u0435\u043d\u0438\u0441 \u0427\u0435\u0440\u043d\u044b\u0445"
_PETROV = "\u041f\u0435\u0442\u0440\u043e\u0432 \u0418\u0432\u0430\u043d"  # Petrov Ivan


def _line(number: str, name: str) -> str:
    return f"{number}#{name}#Elite#5#1#1990#Team#City##0 00:00:00.000#"


def _fill_open(win, *names: str) -> None:
    win._list_open.clear()
    for i, name in enumerate(names, start=1):
        win._list_open.addItem(_line(str(i), name))
    win._list_open.setCurrentRow(-1)
    win._update_open_scripts()


def test_search_finds_a_latin_rider_by_a_cyrillic_fragment(win):
    # The example from the field: registered as "Denis Chernykh", looked up as "Den"
    # typed in Cyrillic.
    _fill_open(win, "Petrov Ivan", "Denis Chernykh")
    win._edit_search.setText(_DEN)
    win._on_search_open()
    assert win._list_open.currentRow() == 1


def test_search_finds_a_cyrillic_rider_by_a_latin_fragment(win):
    _fill_open(win, "Petrov Ivan", _DENIS_CHERNYKH)
    win._edit_search.setText("Chernykh")
    win._on_search_open()
    assert win._list_open.currentRow() == 1


def test_search_still_finds_a_plain_substring(win):
    _fill_open(win, "Petrov Ivan", "Denis Chernykh")
    win._edit_search.setText("1990")
    win._on_search_open()
    assert win._list_open.currentRow() == 0


def test_search_wraps_around_from_the_current_row(win):
    # Find-next behaviour is unchanged: the search starts below the selection.
    _fill_open(win, "Denis Chernykh", "Petrov Ivan", _DENIS_CHERNYKH)
    win._edit_search.setText(_DEN)
    win._on_search_open()
    assert win._list_open.currentRow() == 0
    win._on_search_open()
    assert win._list_open.currentRow() == 2
    win._on_search_open()
    assert win._list_open.currentRow() == 0


def test_search_reports_no_match_and_keeps_the_selection(win, monkeypatch):
    shown: list[str] = []
    monkeypatch.setattr(
        mw.QMessageBox, "information", lambda *a, **k: shown.append(a[2])
    )
    _fill_open(win, "Denis Chernykh")
    win._list_open.setCurrentRow(0)
    win._edit_search.setText("Sidorov")
    win._on_search_open()
    assert shown == ["No matches found."]
    assert win._list_open.currentRow() == 0


def test_an_empty_query_does_nothing(win, monkeypatch):
    monkeypatch.setattr(
        mw.QMessageBox, "information", lambda *a, **k: pytest.fail("no dialog expected")
    )
    _fill_open(win, "Denis Chernykh")
    win._edit_search.setText("")
    win._on_search_open()
    assert win._list_open.currentRow() == -1


def test_searching_an_empty_list_reports_no_match(win, monkeypatch):
    shown: list[str] = []
    monkeypatch.setattr(
        mw.QMessageBox, "information", lambda *a, **k: shown.append(a[2])
    )
    win._list_open.clear()
    win._edit_search.setText(_DEN)
    win._on_search_open()
    assert shown == ["No matches found."]


def test_the_protocol_search_transliterates_too(win):
    win._list_save_as.addItem(_line("1", "Petrov Ivan"))
    win._list_save_as.addItem(_line("2", "Denis Chernykh"))
    win._list_save_as.setCurrentRow(-1)
    win._edit_search_save_as.setText(_DEN)
    win._on_search_save_as()
    assert win._list_save_as.currentRow() == 1


def test_a_search_after_a_site_load_sees_the_new_riders(win, monkeypatch):
    _fill_open(win, "Petrov Ivan")
    payload = {
        "participants": [
            {
                "category_id": 1,
                "category_name": "Elite",
                "last_name": "Chernykh",
                "first_name": "Denis",
                "birth_year": 1990,
                "team": "",
                "city": "",
            }
        ],
        "categories": [
            {"id": 1, "name": "Elite", "laps": 5, "bib_from": 1, "bib_to": 50}
        ],
    }
    monkeypatch.setattr(win, "_fetch_site_payload", lambda: payload)
    win._on_replace_from_site()
    win._list_open.setCurrentRow(-1)
    win._edit_search.setText(_DEN)
    win._on_search_open()
    assert win._list_open.currentRow() == 0


# -- The list is reduced once per change, the query on every search ---------


def test_the_list_is_reduced_only_when_it_changes(win, monkeypatch):
    calls: list[str] = []
    real = app_search.search_forms

    def counting(text: str):
        calls.append(text)
        return real(text)

    # Patched on the module the index reaches through, not on the name main_window
    # imported -- so this counts list reductions, not query reductions.
    monkeypatch.setattr(app_search, "search_forms", counting)
    _fill_open(win, "Petrov Ivan", "Denis Chernykh")
    assert len(calls) == 2  # indexed once, on the change

    win._edit_search.setText(_DEN)
    win._on_search_open()
    win._on_search_open()
    assert len(calls) == 2  # two more searches, no re-reduction

    win._list_open.addItem(_line("3", "Sidorov Ivan"))
    win._on_search_open()
    assert len(calls) == 5  # the list changed, so all three lines were reduced


# -- The scripts line under the pre-registration list ----------------------


def test_scripts_line_names_both_scripts(win):
    _fill_open(win, "Denis Chernykh", _DENIS_CHERNYKH)
    assert win._lbl_open_scripts.text() == "Scripts in list: Cyrillic, Latin"


def test_scripts_line_names_one_script(win):
    # No Latin anywhere in the line, not even in the group or the team.
    win._list_open.clear()
    win._list_open.addItem(f"1#{_PETROV}#########")
    win._update_open_scripts()
    assert win._lbl_open_scripts.text() == "Scripts in list: Cyrillic"


def test_scripts_line_on_an_empty_list(win):
    _fill_open(win)
    assert win._lbl_open_scripts.text() == "Scripts in list: -"


def test_scripts_line_catches_up_on_the_next_search(win):
    # The search refreshes the index anyway, so the line reports what it found even
    # for a change that did not come through a load path.
    _fill_open(win, "Petrov Ivan")
    assert win._lbl_open_scripts.text() == "Scripts in list: Latin"
    win._list_open.addItem(f"2#{_PETROV}#########")
    win._edit_search.setText("Petrov")
    win._on_search_open()
    assert win._lbl_open_scripts.text() == "Scripts in list: Cyrillic, Latin"


def test_scripts_line_follows_a_backup_load(win):
    data = _empty_backup()
    data["open_items"] = [f"1#{_DENIS_CHERNYKH}#########"]
    win._fill_from_backup(data)
    assert win._lbl_open_scripts.text() == "Scripts in list: Cyrillic"
