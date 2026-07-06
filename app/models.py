"""Pure-logic helpers for Start Protocol Maker (no GUI dependencies)."""

from __future__ import annotations

import re
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# time helpers
# ---------------------------------------------------------------------------


def get_time_from_seconds(original_time: float) -> str:
    """Format float seconds as 'D HH:MM:SS.mmm' (port of C++ getTimeFromSeconds)."""
    original_seconds = int(original_time)
    original_ms = original_time - original_seconds
    seconds = original_seconds % 60
    minutes = (original_seconds // 60) % 60
    hours = (original_seconds // 3600) % 24
    days = original_seconds // 86400
    milliseconds = int(original_ms * 1000)
    ms_str = str(milliseconds).zfill(3)
    return f"{days} {hours:02d}:{minutes:02d}:{seconds:02d}.{ms_str}"


def current_local_seconds() -> float:
    """Return current local time as float seconds (matches C++ _ftime - timezone)."""
    return time.time() - time.timezone


# ---------------------------------------------------------------------------
# field parsing
# ---------------------------------------------------------------------------


def get_field(line: str, idx: int, sep: str = "#") -> str:
    """Return idx-th token from a sep-delimited string."""
    parts = line.split(sep)
    return parts[idx] if idx < len(parts) else ""


def get_n_fields(line: str, sep: str = "#") -> int:
    """Number of sep-delimited fields (mirrors C++ getNumberOfFields)."""
    return len(line.split(sep)) - 1


def parse_competitor_line(line: str) -> dict[str, str]:
    """Parse a start-protocol line into a field dict."""
    f = lambda i: get_field(line, i)  # noqa: E731
    return {
        "number": f(0),
        "name": f(1),
        "group_and_laps": f(2) + ("#" + f(3) if f(3) else ""),
        "group": f(2),
        "laps": f(3),
        "stage": f(4),
        "year_of_birth": f(5),
        "team": f(6),
        "city": f(7),
        "comment": f(8) if get_n_fields(line) > 8 else "",
        "time_shift": f(9) if get_n_fields(line) > 9 else "0 00:00:00.000",
    }


def build_competitor_line(
    number: str,
    name: str,
    group_with_laps: str,
    stage: str,
    year_of_birth: str,
    team: str,
    city: str,
    comment: str,
    time_shift: str,
) -> str:
    """Build the #-delimited line stored in listBoxCompetitorsListSaveAs."""
    return (
        f"{number}#{name}#{group_with_laps}#{stage}#"
        f"{year_of_birth}#{team}#{city}#{comment}#{time_shift}#"
    )


# ---------------------------------------------------------------------------
# number management
# ---------------------------------------------------------------------------


def _parse_number_range(numbers_item: str) -> tuple[int, int]:
    """Parse 'min-max[#first#delay]' -> (min, max)."""
    interval = numbers_item.split("#")[0] if "#" in numbers_item else numbers_item
    m = re.match(r"(\d+)-(\d+)", interval.strip())
    if not m:
        return 0, -1
    return int(m.group(1)), int(m.group(2))


def get_next_number(  # noqa: C901
    group_index: int,
    open_items: list[str],
    save_as_items: list[str],
    numbers_items: list[str],
    use_all_numbers: bool,
) -> str | None:
    """
    Find the next free number for the group at group_index.
    Returns the number string or None if no free number exists.
    Port of C++ buttonGetNumber_Click logic.
    """
    if group_index < 0 or group_index >= len(numbers_items):
        return None
    first_n, last_n = _parse_number_range(numbers_items[group_index])
    if first_n > last_n:
        return None

    all_numbers: set[int] = set(range(first_n, last_n + 1))

    def _extract_number(item: str) -> int | None:
        raw = item.split("#")[0] if "#" in item else item
        try:
            return int(raw.strip())
        except ValueError:
            return None

    for item in save_as_items:
        n = _extract_number(item)
        if n is not None:
            all_numbers.discard(n)

    if not use_all_numbers:
        for item in open_items:
            n = _extract_number(item)
            if n is not None:
                all_numbers.discard(n)

    if not all_numbers:
        return None
    return str(min(all_numbers))


def auto_shift_time(
    number_str: str, first_number_str: str, single_time_str: str
) -> str | None:
    """
    Calculate start delay for a competitor.
    Returns formatted time string or None if inputs are invalid.
    Port of C++ buttonAutoUpdateDelayFromStart_Click logic.
    """
    try:
        number = int(number_str.strip())
        first_number = int(first_number_str.strip())
        single_time = int(single_time_str.strip())
    except ValueError, AttributeError:
        return None
    if single_time < 0:
        return None
    delay_sec = (number - first_number) * single_time
    return get_time_from_seconds(max(0.0, float(delay_sec)))


# ---------------------------------------------------------------------------
# duplicate detection
# ---------------------------------------------------------------------------


def check_duplicate_fields(
    items: list[str],
    field_idx: int,
    split_by_space: bool,
    start_from: int = 0,
) -> tuple[bool, int]:
    """
    Check for duplicate values in field_idx across items[start_from:].
    Returns (duplicates_found, first_duplicate_index_in_saveas or -1).
    Port of C++ chechDoubleNumbersInSaveAsList logic.
    """
    values: list[str] = []
    for item in items[start_from:]:
        if get_n_fields(item) >= field_idx + 1:
            val = get_field(item, field_idx).lower()
            if split_by_space:
                val = val.split(" ")[0]
            values.append(val)
        else:
            values.append("")

    # quick check
    if len(set(values)) == len(values) or not values:
        return False, -1

    for i in range(len(values)):
        for j in range(i + 1, len(values)):
            if values[i] and values[i] == values[j]:
                stage_i = get_field(items[start_from + i], 4)
                stage_j = get_field(items[start_from + j], 4)
                if stage_i == stage_j:
                    return True, start_from + i
    return True, -1


# ---------------------------------------------------------------------------
# backup file I/O
# ---------------------------------------------------------------------------

_SECTION_OPEN = "List of opened competitors"
_SECTION_SAVE = "List of competitors to save"
_SECTION_GROUPS = "List of groups"
_SECTION_NUMBERS = "List of numbers"
_SECTION_REGEXP_FROM = "RegExp From"
_SECTION_REGEXP_TO = "RegExp To"
_SECTION_FTP = "FTP Configuration"
_SECTION_HTTP = "HTTP Configuration"
_TAG_START_FILE = "StartProtocolFile"
_TAG_USE_ALL = "UseAllNumbers"
_TAG_AUTO_SHIFT = "AutoShift"
_TAG_FIRST_NUMBER = "FirstNumber"
_TAG_DELAY = "DelayPerNumber"
_TAG_DEVICE_ID = "DeviceId"
_TAG_CLIENT_REVISION = "ClientRevision"


def _read_section(
    lines: list[str], start: int, terminators: set[str]
) -> tuple[list[str], int]:
    """Read lines until a terminator is hit. Returns (section_lines, new_idx)."""
    result: list[str] = []
    i = start
    while i < len(lines) and lines[i] not in terminators:
        result.append(lines[i])
        i += 1
    return result, i


def load_backup(path: str) -> dict:  # noqa: C901
    """
    Load a StartProtocolMaker backup file.
    Returns a dict with keys: open_items, save_items, groups, numbers,
    regexp_from, regexp_to, ftp_address, start_protocol_file,
    use_all_numbers, auto_shift.
    Port of C++ loadBackup logic.
    """
    result: dict = {
        "open_items": [],
        "save_items": [],
        "groups": [],
        "numbers": [],
        "regexp_from": "",
        "regexp_to": "",
        "ftp_address": "",
        "http_site_url": "",
        "http_token": "",
        "device_id": "",
        "client_revision": 0,
        "start_protocol_file": "",
        "use_all_numbers": False,
        "auto_shift": False,
        "first_number": "",
        "delay": "",
    }

    p = Path(path)
    if not p.exists():
        return result

    for enc in ("utf-8", "cp1251", "latin-1"):
        try:
            text = p.read_text(encoding=enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        return result

    lines = text.splitlines()
    if not lines or lines[0] != _SECTION_OPEN:
        return result

    i = 1
    open_items, i = _read_section(lines, i, {_SECTION_SAVE})
    if i >= len(lines):
        return result
    result["open_items"] = open_items
    i += 1  # skip _SECTION_SAVE

    save_items, i = _read_section(lines, i, {_SECTION_GROUPS})
    if i >= len(lines):
        return result
    result["save_items"] = save_items
    i += 1  # skip _SECTION_GROUPS

    all_after_groups = {_SECTION_NUMBERS, _SECTION_FTP, _SECTION_REGEXP_FROM}
    groups, i = _read_section(lines, i, all_after_groups)
    result["groups"] = groups

    if i < len(lines) and lines[i] == _SECTION_NUMBERS:
        i += 1
        numbers, i = _read_section(lines, i, {_SECTION_REGEXP_FROM, _SECTION_FTP})
        # pad numbers to match groups length
        while len(numbers) < len(groups):
            numbers.append("")
        result["numbers"] = numbers
    else:
        result["numbers"] = [""] * len(groups)

    if i < len(lines) and lines[i] == _SECTION_REGEXP_FROM:
        i += 1
        rf_lines, i = _read_section(lines, i, {_SECTION_REGEXP_TO, _SECTION_FTP})
        result["regexp_from"] = "\n".join(rf_lines)

    if i < len(lines) and lines[i] == _SECTION_REGEXP_TO:
        i += 1
        rt_lines, i = _read_section(lines, i, {_SECTION_FTP})
        result["regexp_to"] = "\n".join(rt_lines)

    if i < len(lines) and lines[i] == _SECTION_FTP:
        i += 1
        if i < len(lines):
            result["ftp_address"] = lines[i]
            i += 1

    if i < len(lines) and lines[i] == _SECTION_HTTP:
        i += 1
        if i < len(lines):
            result["http_site_url"] = lines[i]
            i += 1
        if i < len(lines):
            result["http_token"] = lines[i]
            i += 1

    if i < len(lines) and lines[i] == _TAG_START_FILE:
        i += 1
        if i < len(lines):
            result["start_protocol_file"] = lines[i]
            i += 1

    if i < len(lines) and lines[i] == _TAG_USE_ALL:
        result["use_all_numbers"] = True
        i += 1

    if i < len(lines) and lines[i] == _TAG_AUTO_SHIFT:
        result["auto_shift"] = True
        i += 1

    if i < len(lines) and lines[i] == _TAG_FIRST_NUMBER:
        i += 1
        if i < len(lines):
            result["first_number"] = lines[i]
            i += 1

    if i < len(lines) and lines[i] == _TAG_DELAY:
        i += 1
        if i < len(lines):
            result["delay"] = lines[i]
            i += 1

    if i < len(lines) and lines[i] == _TAG_DEVICE_ID:
        i += 1
        if i < len(lines):
            result["device_id"] = lines[i]
            i += 1

    if i < len(lines) and lines[i] == _TAG_CLIENT_REVISION:
        i += 1
        if i < len(lines):
            try:
                result["client_revision"] = int(lines[i])
            except ValueError:
                result["client_revision"] = 0
            i += 1

    return result


def _append_tag_value(lines: list[str], tag: str, value: str | int) -> None:
    """Append tag + value pair only when value is truthy."""
    if value:
        lines.append(tag)
        lines.append(str(value))


def save_backup(
    path: str,
    open_items: list[str],
    save_items: list[str],
    groups: list[str],
    numbers: list[str],
    regexp_from: str,
    regexp_to: str,
    ftp_address: str,
    start_protocol_file: str,
    use_all_numbers: bool,
    auto_shift: bool,
    http_site_url: str = "",
    http_token: str = "",
    device_id: str = "",
    client_revision: int = 0,
    first_number: str = "",
    delay: str = "",
) -> None:
    """Write a backup file. Port of C++ saveBackupFile logic."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append(_SECTION_OPEN)
    lines.extend(open_items)
    lines.append(_SECTION_SAVE)
    lines.extend(save_items)
    lines.append(_SECTION_GROUPS)
    lines.extend(groups)
    lines.append(_SECTION_NUMBERS)
    lines.extend(numbers)
    lines.append(_SECTION_REGEXP_FROM)
    if regexp_from:
        lines.extend(regexp_from.splitlines())
    lines.append(_SECTION_REGEXP_TO)
    if regexp_to:
        lines.extend(regexp_to.splitlines())
    lines.append(_SECTION_FTP)
    lines.append(ftp_address)
    if http_site_url or http_token:
        lines.append(_SECTION_HTTP)
        lines.append(http_site_url)
        lines.append(http_token)
    _append_tag_value(lines, _TAG_START_FILE, start_protocol_file)
    if use_all_numbers:
        lines.append(_TAG_USE_ALL)
    if auto_shift:
        lines.append(_TAG_AUTO_SHIFT)
    _append_tag_value(lines, _TAG_FIRST_NUMBER, first_number)
    _append_tag_value(lines, _TAG_DELAY, delay)
    _append_tag_value(lines, _TAG_DEVICE_ID, device_id)
    _append_tag_value(lines, _TAG_CLIENT_REVISION, client_revision)
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def participant_to_open_line(participant: dict, categories: list[dict]) -> str:
    """Convert an API participant dict to a start-protocol open-list line."""
    cat_id = participant.get("category_id")
    cat_name = participant.get("category_name", "")
    laps = ""
    if cat_id is not None:
        for cat in categories:
            if cat.get("id") == cat_id:
                laps_val = cat.get("laps")
                if laps_val is not None:
                    laps = str(laps_val)
                if not cat_name:
                    cat_name = cat.get("name", "")
                break
    # Always include the # separator so field positions are consistent with
    # parse_competitor_line expectations (group=f(2), laps=f(3), stage=f(4)).
    group_with_laps = f"{cat_name}#{laps}"
    p_names = participant.get("participant_names", "")
    if p_names:
        name = p_names
        year_of_birth = participant.get("participant_birth_years", "") or str(
            participant.get("birth_year", "")
        )
        city = participant.get("participant_cities", "") or participant.get("city", "")
    else:
        last = participant.get("last_name", "")
        first = participant.get("first_name", "")
        name = f"{last} {first}".strip()
        year_of_birth = str(participant.get("birth_year", ""))
        city = participant.get("city", "")
    return build_competitor_line(
        number="",
        name=name,
        group_with_laps=group_with_laps,
        stage="1",
        year_of_birth=year_of_birth,
        team=participant.get("team", ""),
        city=city,
        comment="",
        time_shift="0 00:00:00.000",
    )


DEFAULT_NUMBER_RANGE = "1-200"


def category_number_range(category: dict, default: str = DEFAULT_NUMBER_RANGE) -> str:
    """Return a category's bib range as ``bib_from-bib_to``, or ``default`` if unset.

    The ``get number`` button picks the next free bib from this range, so a group synced
    from the site must carry the site's bib range instead of a made-up default.
    """
    bib_from = category.get("bib_from")
    bib_to = category.get("bib_to")
    if bib_from is None or bib_to is None:
        return default
    return f"{bib_from}-{bib_to}"


def categories_to_group_rows(
    categories: list[dict], default_range: str = DEFAULT_NUMBER_RANGE
) -> list[tuple[str, str]]:
    """Convert API categories to ``(group_text, number_range)`` rows.

    ``group_text`` is ``name#laps`` when the category has a lap count, else just
    ``name`` (mirroring how the UI stores manually added groups); ``number_range`` is
    the category's ``bib_from-bib_to``. Nameless categories are skipped and duplicate
    group texts collapsed, keeping first-seen order.
    """
    rows: list[tuple[str, str]] = []
    seen: set[str] = set()
    for cat in categories:
        name = (cat.get("name") or "").strip()
        if not name:
            continue
        laps_val = cat.get("laps")
        group = f"{name}#{laps_val}" if laps_val is not None else name
        if group not in seen:
            seen.add(group)
            rows.append((group, category_number_range(cat, default_range)))
    return rows


def categories_to_groups(categories: list[dict]) -> list[str]:
    """Group texts (``name#laps`` or ``name``) for the categories, order preserved."""
    return [group for group, _ in categories_to_group_rows(categories)]


def merge_groups(existing: list[str], incoming: list[str]) -> list[str]:
    """Return ``existing`` plus each ``incoming`` group not present (order kept)."""
    result = list(existing)
    present = set(existing)
    for group in incoming:
        if group not in present:
            present.add(group)
            result.append(group)
    return result


def write_start_protocol(path: str, save_items: list[str]) -> None:
    """Write save_items to a start protocol file (one line per competitor)."""
    content = "\n".join(save_items)
    Path(path).write_text(content + "\n" if content else "", encoding="utf-8")
