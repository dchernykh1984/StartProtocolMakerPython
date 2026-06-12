"""HTTP I/O for fetching participant data from the cycling site API."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request


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
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise ValueError(f"HTTP {exc.code}: {exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise ValueError(f"Connection error: {exc.reason}") from exc
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"Invalid response: {exc}") from exc
