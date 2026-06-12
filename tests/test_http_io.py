"""Tests for HTTP I/O and participant_to_open_line."""

from __future__ import annotations

import json
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.http_io import fetch_participants
from app.models import (
    load_backup,
    parse_competitor_line,
    participant_to_open_line,
    save_backup,
)

# ---------------------------------------------------------------------------
# fetch_participants
# ---------------------------------------------------------------------------


def _make_response(data: dict, status: int = 200) -> MagicMock:
    mock = MagicMock()
    mock.__enter__ = lambda s: s
    mock.__exit__ = MagicMock(return_value=False)
    mock.read.return_value = json.dumps(data).encode("utf-8")
    mock.status = status
    return mock


class TestFetchParticipants:
    def test_success_returns_dict(self) -> None:
        payload = {"participants": [], "categories": [], "competition_title": "Test"}
        with patch("urllib.request.urlopen", return_value=_make_response(payload)):
            result = fetch_participants("https://example.com", "abc-token")
        assert result["competition_title"] == "Test"

    def test_http_error_raises_value_error(self) -> None:
        exc = urllib.error.HTTPError(
            url="",
            code=401,
            msg="Unauthorized",
            hdrs=None,  # type: ignore[arg-type]
            fp=None,
        )
        with patch("urllib.request.urlopen", side_effect=exc):
            with pytest.raises(ValueError, match="HTTP 401"):
                fetch_participants("https://example.com", "bad-token")

    def test_url_error_raises_value_error(self) -> None:
        exc = urllib.error.URLError(reason="Name or service not known")
        with patch("urllib.request.urlopen", side_effect=exc):
            with pytest.raises(ValueError, match="Connection error"):
                fetch_participants("https://no-such-host.invalid", "tok")

    def test_invalid_json_raises_value_error(self) -> None:
        mock = MagicMock()
        mock.__enter__ = lambda s: s
        mock.__exit__ = MagicMock(return_value=False)
        mock.read.return_value = b"not json"
        with patch("urllib.request.urlopen", return_value=mock):
            with pytest.raises(ValueError):
                fetch_participants("https://example.com", "tok")

    def test_url_includes_token(self) -> None:
        payload: dict[str, list] = {"participants": [], "categories": []}
        calls: list[str] = []

        def fake_urlopen(url, timeout):
            calls.append(url)
            return _make_response(payload)

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            fetch_participants("https://site.com", "my-token")
        assert "my-token" in calls[0]
        assert calls[0].startswith("https://site.com/api/v1/participants/")

    def test_competition_token_param_name(self) -> None:
        payload: dict[str, list] = {"participants": [], "categories": []}
        calls: list[str] = []

        def fake_urlopen(url, timeout):
            calls.append(url)
            return _make_response(payload)

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            fetch_participants("https://site.com", "abc-uuid")
        assert "competition_token=abc-uuid" in calls[0]


# ---------------------------------------------------------------------------
# participant_to_open_line
# ---------------------------------------------------------------------------


class TestParticipantToOpenLine:
    def _make_participant(self, **kwargs) -> dict:
        defaults = {
            "id": 1,
            "first_name": "Ivan",
            "last_name": "Petrov",
            "birth_date": "1990-06-15",
            "birth_year": 1990,
            "gender": "M",
            "category_id": None,
            "category_name": "",
            "team": "Team A",
            "city": "Moscow",
            "additional_info": "",
            "is_approved": True,
            "is_paid": True,
        }
        defaults.update(kwargs)
        return defaults

    def test_name_is_last_first(self) -> None:
        line = participant_to_open_line(self._make_participant(), [])
        parts = line.split("#")
        assert parts[1] == "Petrov Ivan"

    def test_year_of_birth_parsed(self) -> None:
        line = participant_to_open_line(self._make_participant(), [])
        parsed = parse_competitor_line(line)
        assert parsed["year_of_birth"] == "1990"

    def test_team_and_city_parsed(self) -> None:
        line = participant_to_open_line(self._make_participant(), [])
        parsed = parse_competitor_line(line)
        assert parsed["team"] == "Team A"
        assert parsed["city"] == "Moscow"

    def test_category_with_laps(self) -> None:
        p = self._make_participant(category_id=10, category_name="Elite")
        cats = [{"id": 10, "name": "Elite", "laps": 3}]
        line = participant_to_open_line(p, cats)
        parsed = parse_competitor_line(line)
        assert parsed["group"] == "Elite"
        assert parsed["laps"] == "3"

    def test_category_without_laps(self) -> None:
        p = self._make_participant(category_id=10, category_name="Junior")
        cats = [{"id": 10, "name": "Junior", "laps": None}]
        line = participant_to_open_line(p, cats)
        parsed = parse_competitor_line(line)
        assert parsed["group"] == "Junior"
        assert parsed["laps"] == ""

    def test_no_category(self) -> None:
        p = self._make_participant(category_id=None, category_name="")
        line = participant_to_open_line(p, [])
        parsed = parse_competitor_line(line)
        assert parsed["group"] == ""

    def test_relay_uses_participant_names(self) -> None:
        p = self._make_participant(
            first_name="",
            last_name="",
            participant_names="Ivanov Ivan<BR>Petrov Vasya",
            participant_birth_years="1990<BR>1995",
            participant_cities="Moscow<BR>Almaty",
        )
        line = participant_to_open_line(p, [])
        parts = line.split("#")
        assert parts[1] == "Ivanov Ivan<BR>Petrov Vasya"

    def test_relay_uses_participant_birth_years(self) -> None:
        p = self._make_participant(
            first_name="",
            last_name="",
            participant_names="Ivanov Ivan<BR>Petrov Vasya",
            participant_birth_years="1990<BR>1995",
            participant_cities="Moscow<BR>Almaty",
        )
        line = participant_to_open_line(p, [])
        parsed = parse_competitor_line(line)
        assert parsed["year_of_birth"] == "1990<BR>1995"

    def test_relay_uses_participant_cities(self) -> None:
        p = self._make_participant(
            first_name="",
            last_name="",
            participant_names="Ivanov Ivan<BR>Petrov Vasya",
            participant_birth_years="1990<BR>1995",
            participant_cities="Moscow<BR>Almaty",
        )
        line = participant_to_open_line(p, [])
        parsed = parse_competitor_line(line)
        assert parsed["city"] == "Moscow<BR>Almaty"

    def test_individual_ignores_participant_names_field(self) -> None:
        p = self._make_participant(
            participant_names="", participant_birth_years="", participant_cities=""
        )
        line = participant_to_open_line(p, [])
        parts = line.split("#")
        assert parts[1] == "Petrov Ivan"


# ---------------------------------------------------------------------------
# backup round-trip with HTTP fields
# ---------------------------------------------------------------------------


class TestBackupHTTPRoundTrip:
    def test_http_fields_saved_and_loaded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "backup.txt")
            save_backup(
                path=path,
                open_items=["Alice#1"],
                save_items=[],
                groups=["Group#2"],
                numbers=["1-100"],
                regexp_from="",
                regexp_to="",
                ftp_address="",
                start_protocol_file="",
                use_all_numbers=False,
                auto_shift=False,
                http_site_url="https://my-site.com",
                http_token="test-token-uuid",
            )
            result = load_backup(path)
        assert result["http_site_url"] == "https://my-site.com"
        assert result["http_token"] == "test-token-uuid"

    def test_http_fields_default_to_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "backup.txt")
            save_backup(
                path=path,
                open_items=[],
                save_items=[],
                groups=[],
                numbers=[],
                regexp_from="",
                regexp_to="",
                ftp_address="",
                start_protocol_file="",
                use_all_numbers=False,
                auto_shift=False,
            )
            result = load_backup(path)
        assert result["http_site_url"] == ""
        assert result["http_token"] == ""
