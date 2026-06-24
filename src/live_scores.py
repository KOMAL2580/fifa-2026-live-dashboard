from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd
import requests


DEFAULT_BASE_URL = "https://v3.football.api-sports.io"
DEFAULT_TIMEOUT_SECONDS = 15

LIVE_STATUS_CODES = {"1H", "HT", "2H", "ET", "BT", "P", "LIVE", "INT"}
UPCOMING_STATUS_CODES = {"TBD", "NS"}
FINISHED_STATUS_CODES = {"FT", "AET", "PEN"}


class LiveScoreError(RuntimeError):
    """Raised when the live-score API cannot return usable match data."""


def _normalize_status(api_status: str | None) -> str:
    # Convert provider-specific status codes into the dashboard's three statuses.
    if api_status in LIVE_STATUS_CODES:
        return "Live"
    if api_status in UPCOMING_STATUS_CODES:
        return "Upcoming"
    if api_status in FINISHED_STATUS_CODES:
        return "Finished"
    return "Upcoming"


def _safe_number(value: Any, default: int | float = 0) -> int | float:
    # API fields can be null before a match starts, so normalize them safely.
    return default if value is None else value


def _fixture_to_dashboard_row(fixture: dict[str, Any]) -> dict[str, Any]:
    # Map the API-Football fixture shape into the same columns as sample_matches.csv.
    fixture_info = fixture.get("fixture", {})
    status_info = fixture_info.get("status", {})
    league_info = fixture.get("league", {})
    teams_info = fixture.get("teams", {})
    goals_info = fixture.get("goals", {})

    api_status = status_info.get("short")
    dashboard_status = _normalize_status(api_status)
    elapsed = status_info.get("elapsed")

    return {
        "match_id": f"API-{fixture_info.get('id', 'unknown')}",
        "competition": league_info.get("name", "Unknown competition"),
        "status": dashboard_status,
        "minute": 90 if dashboard_status == "Finished" else _safe_number(elapsed, 0),
        "home_team": teams_info.get("home", {}).get("name", "Home team"),
        "away_team": teams_info.get("away", {}).get("name", "Away team"),
        "home_goals": _safe_number(goals_info.get("home"), 0),
        "away_goals": _safe_number(goals_info.get("away"), 0),
        "home_possession": 50,
        "away_possession": 50,
        "home_shots": 0,
        "away_shots": 0,
        "home_xg": 0.0,
        "away_xg": 0.0,
        "home_form_points": 0,
        "away_form_points": 0,
        "data_source": "API-Football",
    }


def fetch_matches_from_api(
    api_key: str,
    mode: str = "today",
    match_date: str | None = None,
    timezone: str = "Asia/Kolkata",
    base_url: str = DEFAULT_BASE_URL,
) -> pd.DataFrame:
    """Fetch live or today's football fixtures from API-Football."""
    if not api_key:
        raise LiveScoreError("FOOTBALL_API_KEY is not set.")

    params = {"timezone": timezone}
    if mode == "live":
        params["live"] = "all"
    else:
        params["date"] = match_date or date.today().isoformat()

    try:
        response = requests.get(
            f"{base_url.rstrip('/')}/fixtures",
            headers={"x-apisports-key": api_key},
            params=params,
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise LiveScoreError(f"Live-score request failed: {exc}") from exc

    payload = response.json()
    errors = payload.get("errors")
    if errors:
        raise LiveScoreError(f"Live-score API returned an error: {errors}")

    fixtures = payload.get("response", [])
    rows = [_fixture_to_dashboard_row(fixture) for fixture in fixtures]
    return pd.DataFrame(rows)
