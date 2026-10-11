"""Relative paths restored from a backup stay inside the portable app folder."""

from __future__ import annotations

from pathlib import Path

import pytest

from app import paths
from app.models import load_backup, save_backup, write_start_protocol


@pytest.fixture
def race_dir(tmp_path, monkeypatch):
    race = tmp_path / "race"
    race.mkdir()
    unrelated = tmp_path / "working"
    unrelated.mkdir()
    monkeypatch.chdir(unrelated)
    monkeypatch.setattr(paths.sys, "frozen", True, raising=False)
    monkeypatch.setattr(
        paths.sys,
        "executable",
        str(race / "StartProtocolMaker.app/Contents/MacOS/StartProtocolMaker"),
    )
    return race


def test_relative_start_protocol_is_written_next_to_app(race_dir):
    write_start_protocol("start.txt", ["12#Rider#GroupA#"])
    assert (race_dir / "start.txt").read_text(encoding="utf-8") == (
        "12#Rider#GroupA#\n"
    )
    assert not (Path.cwd() / "start.txt").exists()


def test_relative_backup_round_trip_preserves_protocol_path(race_dir):
    save_backup(
        path="temp/backup.txt",
        open_items=[],
        save_items=[],
        groups=[],
        numbers=[],
        regexp_from="",
        regexp_to="",
        ftp_address="",
        start_protocol_file="start.txt",
        use_all_numbers=False,
        auto_shift=False,
    )
    assert (race_dir / "temp/backup.txt").exists()
    assert load_backup("temp/backup.txt")["start_protocol_file"] == "start.txt"
    assert not (Path.cwd() / "temp").exists()
