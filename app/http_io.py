"""HTTP I/O for exchanging data with the cycling site API."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request


def upload_start_list(
    site_url: str,
    token: str,
    device_id: str,
    items: list[str],
    client_revision: int,
) -> int:
    """Upload this device's start list (the "save" list) to the cycling site.

    The site stores it keyed by ``device_id``; re-uploading the same ``device_id``
    overwrites the previously stored list, unless this snapshot is older than the one
    already stored (the server rejects a stale revision with HTTP 409).

    Args:
        site_url: Base URL of the site, e.g. "https://example.com".
        token: Upload token (UUID) from the competition detail page.
        device_id: Stable per-machine identifier (see config).
        items: The start-protocol lines (one per competitor).
        client_revision: Strictly-increasing per-device counter (persisted in the
            backup); the server uses it to reject a reordered/stale overwrite.

    Returns:
        The number of items the site stored.

    Raises:
        ValueError: On HTTP error, network error, or invalid JSON response.
    """
    url = site_url.rstrip("/") + "/api/v1/start-list/"
    payload = json.dumps(
        {
            "competition_token": token,
            "device_id": device_id,
            "items": items,
            "client_revision": client_revision,
        }
    ).encode("utf-8")
    req = urllib.request.Request(  # noqa: S310
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise ValueError(f"HTTP {exc.code}: {exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise ValueError(f"Connection error: {exc.reason}") from exc
    except OSError as exc:
        # urllib only wraps failures raised while sending; a socket timeout or a
        # dropped connection while reading the response surfaces as a bare OSError,
        # which would otherwise escape into the caller's Qt slot.
        raise ValueError(f"Connection error: {exc}") from exc
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"Invalid response: {exc}") from exc
    # A body that is not the expected object, or a count that is not a number, must
    # not reach the caller as a TypeError: this runs unattended in auto mode.
    if not isinstance(data, dict):
        raise ValueError("Invalid response: expected a JSON object")
    count = data.get("count", len(items))
    try:
        return int(count)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid response: bad count {count!r}") from exc


def fetch_participants(site_url: str, token: str) -> dict:
    """
    Fetch participants from the cycling site participants API.

    Args:
        site_url: Base URL of the site, e.g. "https://example.com".
        token: Upload token (UUID) from the competition detail page.

    Returns:
        Parsed JSON dict with keys: participants, categories, competition_title, etc.

    Raises:
        ValueError: On HTTP error, network error, or invalid JSON response.
    """
    url = (
        site_url.rstrip("/")
        + "/api/v1/participants/?"
        + urllib.parse.urlencode({"competition_token": token})
    )
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:  # noqa: S310
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise ValueError(f"HTTP {exc.code}: {exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise ValueError(f"Connection error: {exc.reason}") from exc
    except OSError as exc:
        raise ValueError(f"Connection error: {exc}") from exc
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"Invalid response: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("Invalid response: expected a JSON object")
    return data
