"""Qt-level tests for the load-from-site handlers in MainWindow.

The pure conversion helpers (categories_to_groups, merge_groups) are tested in
test_models; here we verify the handlers wire them to the widgets correctly -- in
particular that Replace still syncs groups when the site has no participants yet.
main_window is excluded from coverage, so these guard against silent handler drift.
"""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from app import main_window as mw

_app = QApplication.instance() or QApplication([])


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


def test_replace_keeps_existing_range_for_kept_group(win, monkeypatch):
    # A group already present keeps its hand-tuned range instead of the site's.
    win._add_group_row("Elite#5", "7-7")
    payload = {
        "participants": [],
        "categories": [
            {"id": 1, "name": "Elite", "laps": 5, "bib_from": 100, "bib_to": 199}
        ],
    }
    monkeypatch.setattr(win, "_fetch_site_payload", lambda: payload)
    win._on_replace_from_site()
    assert _group_rows(win) == [("Elite#5", "7-7")]


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
