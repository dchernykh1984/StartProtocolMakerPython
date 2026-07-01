"""Tests for StartProtocolMaker models (pure logic, no GUI)."""

from __future__ import annotations

import tempfile
from pathlib import Path

from app.models import (
    auto_shift_time,
    build_competitor_line,
    check_duplicate_fields,
    current_local_seconds,
    get_field,
    get_n_fields,
    get_next_number,
    get_time_from_seconds,
    load_backup,
    parse_competitor_line,
    save_backup,
    write_start_protocol,
)

# ---------------------------------------------------------------------------
# get_time_from_seconds
# ---------------------------------------------------------------------------


class TestGetTimeFromSeconds:
    def test_zero(self) -> None:
        assert get_time_from_seconds(0) == "0 00:00:00.000"

    def test_one_hour(self) -> None:
        assert get_time_from_seconds(3600) == "0 01:00:00.000"

    def test_fractional(self) -> None:
        assert get_time_from_seconds(1.5) == "0 00:00:01.500"

    def test_one_day(self) -> None:
        assert get_time_from_seconds(86400) == "1 00:00:00.000"

    def test_complex(self) -> None:
        t = 86400 + 3600 + 120 + 5.846
        result = get_time_from_seconds(t)
        assert result.startswith("1 01:02:05.")

    def test_near_boundary_no_four_digit_ms(self) -> None:
        # 0.9999 fractional: truncation gives .999, not .1000
        result = get_time_from_seconds(0.9999)
        ms_part = result.split(".")[-1]
        assert len(ms_part) == 3


# ---------------------------------------------------------------------------
# current_local_seconds
# ---------------------------------------------------------------------------


class TestCurrentLocalSeconds:
    def test_applies_timezone_offset(self, monkeypatch) -> None:
        # C++ formula: local = _ftime.time - timezone_minutes*60
        # Python: local = time.time() - time.timezone
        # For UTC+5 (Asia/Almaty): time.timezone = -18000
        import time as _time

        monkeypatch.setattr(_time, "time", lambda: 1_000_000.0)
        monkeypatch.setattr(_time, "timezone", -18_000)  # UTC+5
        assert current_local_seconds() == 1_000_000.0 + 18_000  # 1_018_000.0

    def test_utc_zone_returns_same_as_utc(self, monkeypatch) -> None:
        import time as _time

        monkeypatch.setattr(_time, "time", lambda: 500_000.0)
        monkeypatch.setattr(_time, "timezone", 0)
        assert current_local_seconds() == 500_000.0


# ---------------------------------------------------------------------------
# get_field / get_n_fields
# ---------------------------------------------------------------------------


class TestGetField:
    def test_basic(self) -> None:
        assert get_field("a#b#c", 0) == "a"
        assert get_field("a#b#c", 2) == "c"

    def test_out_of_range(self) -> None:
        assert get_field("a#b", 5) == ""

    def test_n_fields(self) -> None:
        assert get_n_fields("a#b#c#") == 3
        assert get_n_fields("a#b") == 1


# ---------------------------------------------------------------------------
# build_competitor_line / parse_competitor_line
# ---------------------------------------------------------------------------


class TestCompetitorLine:
    _LINE = "42#John Doe#GroupA#3#1#1990#TeamX#CityY#comment#0 00:00:30.000#"

    def test_build(self) -> None:
        line = build_competitor_line(
            number="42",
            name="John Doe",
            group_with_laps="GroupA#3",
            stage="1",
            year_of_birth="1990",
            team="TeamX",
            city="CityY",
            comment="comment",
            time_shift="0 00:00:30.000",
        )
        assert line == self._LINE

    def test_parse(self) -> None:
        d = parse_competitor_line(self._LINE)
        assert d["number"] == "42"
        assert d["name"] == "John Doe"
        assert d["group"] == "GroupA"
        assert d["laps"] == "3"
        assert d["stage"] == "1"
        assert d["year_of_birth"] == "1990"
        assert d["team"] == "TeamX"
        assert d["city"] == "CityY"
        assert d["comment"] == "comment"
        assert d["time_shift"] == "0 00:00:30.000"

    def test_parse_missing_comment(self) -> None:
        line = "1#Alice#G#3#1#1990#T#C#"
        d = parse_competitor_line(line)
        assert d["comment"] == ""
        assert d["time_shift"] == "0 00:00:00.000"


# ---------------------------------------------------------------------------
# auto_shift_time
# ---------------------------------------------------------------------------


class TestAutoShiftTime:
    def test_basic(self) -> None:
        result = auto_shift_time("10", "1", "60")
        # (10-1)*60 = 540 sec = 9 minutes
        assert result == "0 00:09:00.000"

    def test_zero_delay(self) -> None:
        result = auto_shift_time("5", "1", "0")
        assert result == "0 00:00:00.000"

    def test_invalid_input(self) -> None:
        assert auto_shift_time("abc", "1", "60") is None
        assert auto_shift_time("1", "abc", "60") is None
        assert auto_shift_time("1", "1", "abc") is None

    def test_negative_delay(self) -> None:
        assert auto_shift_time("1", "1", "-10") is None

    def test_first_number(self) -> None:
        result = auto_shift_time("1", "1", "30")
        assert result == "0 00:00:00.000"


# ---------------------------------------------------------------------------
# get_next_number
# ---------------------------------------------------------------------------


class TestGetNextNumber:
    def test_first_free(self) -> None:
        result = get_next_number(
            group_index=0,
            open_items=[],
            save_as_items=[],
            numbers_items=["1-5"],
            use_all_numbers=False,
        )
        assert result == "1"

    def test_skips_used_in_save_as(self) -> None:
        result = get_next_number(
            group_index=0,
            open_items=[],
            save_as_items=["1#Alice#G#3#1#..."],
            numbers_items=["1-5"],
            use_all_numbers=False,
        )
        assert result == "2"

    def test_skips_used_in_open_when_not_use_all(self) -> None:
        result = get_next_number(
            group_index=0,
            open_items=["1#Known#G#3#1#..."],
            save_as_items=[],
            numbers_items=["1-5"],
            use_all_numbers=False,
        )
        assert result == "2"

    def test_use_all_ignores_open(self) -> None:
        result = get_next_number(
            group_index=0,
            open_items=["1#Known#G#3#1#..."],
            save_as_items=[],
            numbers_items=["1-5"],
            use_all_numbers=True,
        )
        assert result == "1"

    def test_no_free_numbers(self) -> None:
        result = get_next_number(
            group_index=0,
            open_items=[],
            save_as_items=[f"{i}#X#G#3#1#..." for i in range(1, 4)],
            numbers_items=["1-3"],
            use_all_numbers=False,
        )
        assert result is None

    def test_invalid_group_index(self) -> None:
        assert get_next_number(-1, [], [], ["1-5"], False) is None
        assert get_next_number(5, [], [], ["1-5"], False) is None

    def test_numbers_with_hash_format(self) -> None:
        # "1-10#1#30" -> interval is "1-10"
        result = get_next_number(0, [], [], ["1-10#1#30"], False)
        assert result == "1"


# ---------------------------------------------------------------------------
# check_duplicate_fields
# ---------------------------------------------------------------------------


class TestCheckDuplicateFields:
    def test_no_duplicates(self) -> None:
        items = ["1#Alice#G#3", "2#Bob#G#3"]
        found, _idx = check_duplicate_fields(items, 0, False)
        assert found is False

    def test_duplicate_id(self) -> None:
        items = ["1#Alice#G#3#1", "1#Bob#G#3#1"]
        found, _idx = check_duplicate_fields(items, 0, False)
        assert found is True
        assert _idx == 0

    def test_duplicate_name(self) -> None:
        items = ["1#Alice#G#3#1", "2#Alice#G#3#1"]
        found, _idx = check_duplicate_fields(items, 1, False)
        assert found is True

    def test_split_by_space(self) -> None:
        # "alice smith" vs "alice jones" -> same first word "alice"
        items = ["1#alice smith#G#3#1", "2#alice jones#G#3#1"]
        found, _ = check_duplicate_fields(items, 1, split_by_space=True)
        assert found is True

    def test_start_from_offset(self) -> None:
        # duplicate at indices 0,1 but start_from=1 -> only looks at items[1:]
        items = ["1#Alice#G#3#1", "2#Bob#G#3#1", "2#Carol#G#3#1"]
        found, _ = check_duplicate_fields(items, 0, False, start_from=1)
        assert found is True

    def test_empty(self) -> None:
        found, idx = check_duplicate_fields([], 0, False)
        assert found is False
        assert idx == -1


# ---------------------------------------------------------------------------
# save_backup / load_backup
# ---------------------------------------------------------------------------


class TestBackup:
    def _roundtrip(self, **kwargs) -> dict:
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            path = f.name
        save_backup(path, **kwargs)
        return load_backup(path)

    def _defaults(self, **overrides) -> dict:
        base = {
            "open_items": [],
            "save_items": [],
            "groups": [],
            "numbers": [],
            "regexp_from": "",
            "regexp_to": "",
            "ftp_address": "",
            "start_protocol_file": "",
            "use_all_numbers": False,
            "auto_shift": False,
        }
        base.update(overrides)
        return base

    def test_empty(self) -> None:
        result = self._roundtrip(**self._defaults())
        assert result["open_items"] == []
        assert result["save_items"] == []

    def test_open_items(self) -> None:
        items = [
            "1#Alice#G#3#1#1990#T#C##0 00:00:00.000#",
            "2#Bob#G#3#1#1985#T#C##0 00:00:00.000#",
        ]
        result = self._roundtrip(**self._defaults(open_items=items))
        assert result["open_items"] == items

    def test_save_items(self) -> None:
        items = ["42#Runner#GroupA#3#1#1990#T#C##0 00:01:00.000#"]
        result = self._roundtrip(**self._defaults(save_items=items))
        assert result["save_items"] == items

    def test_groups_and_numbers(self) -> None:
        result = self._roundtrip(
            **self._defaults(
                groups=["GroupA#3", "GroupB#5"],
                numbers=["1-50", "51-100"],
            )
        )
        assert result["groups"] == ["GroupA#3", "GroupB#5"]
        assert result["numbers"] == ["1-50", "51-100"]

    def test_regexp(self) -> None:
        result = self._roundtrip(
            **self._defaults(
                regexp_from="(.+),(.+)",
                regexp_to="$2 $1",
            )
        )
        assert result["regexp_from"] == "(.+),(.+)"
        assert result["regexp_to"] == "$2 $1"

    def test_ftp_address(self) -> None:
        result = self._roundtrip(**self._defaults(ftp_address="ftp://example.com"))
        assert result["ftp_address"] == "ftp://example.com"

    def test_start_protocol_file(self) -> None:
        result = self._roundtrip(
            **self._defaults(start_protocol_file="/path/to/start.txt")
        )
        assert result["start_protocol_file"] == "/path/to/start.txt"

    def test_use_all_numbers(self) -> None:
        result = self._roundtrip(**self._defaults(use_all_numbers=True))
        assert result["use_all_numbers"] is True

    def test_auto_shift(self) -> None:
        result = self._roundtrip(**self._defaults(auto_shift=True))
        assert result["auto_shift"] is True

    def test_auto_shift_false_not_saved(self) -> None:
        result = self._roundtrip(**self._defaults(auto_shift=False))
        assert result["auto_shift"] is False

    def test_first_number(self) -> None:
        result = self._roundtrip(**self._defaults(first_number="5"))
        assert result["first_number"] == "5"

    def test_first_number_empty_by_default(self) -> None:
        result = self._roundtrip(**self._defaults())
        assert result["first_number"] == ""

    def test_delay(self) -> None:
        result = self._roundtrip(**self._defaults(delay="30"))
        assert result["delay"] == "30"

    def test_delay_empty_by_default(self) -> None:
        result = self._roundtrip(**self._defaults())
        assert result["delay"] == ""

    def test_first_number_and_delay_together(self) -> None:
        result = self._roundtrip(**self._defaults(first_number="10", delay="60"))
        assert result["first_number"] == "10"
        assert result["delay"] == "60"

    def test_load_nonexistent_returns_empty(self) -> None:
        result = load_backup("/nonexistent/path/file.txt")
        assert result["open_items"] == []

    def test_load_wrong_format_returns_empty(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("WRONG HEADER\nsome data\n")
            path = f.name
        result = load_backup(path)
        assert result["open_items"] == []


# ---------------------------------------------------------------------------
# write_start_protocol
# ---------------------------------------------------------------------------


class TestWriteStartProtocol:
    def test_writes_lines(self) -> None:
        ivan = "\u0418\u0432\u0430\u043d"  # Ivan
        items = [
            f"1#{ivan}#G#3#1#1990#T#C##0 00:00:00.000#",
            "2#Bob#G#3#1#1985#T#C##0 00:00:00.000#",
        ]
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            path = f.name
        write_start_protocol(path, items)
        content = Path(path).read_text(encoding="utf-8")
        for item in items:
            assert item in content

    def test_empty(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            path = f.name
        write_start_protocol(path, [])
        content = Path(path).read_text(encoding="utf-8")
        assert content.strip() == ""
