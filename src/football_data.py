from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd
import requests


BASE_URL = "https://api.football-data.org/v4"
TIMEOUT_SECONDS = 20

LIVE_STATUSES = {"IN_PLAY", "PAUSED"}
UPCOMING_STATUSES = {"SCHEDULED", "TIMED"}
FINISHED_STATUSES = {"FINISHED"}


class FootballDataError(RuntimeError):
    """Raised when football-data.org cannot return usable data."""


def _request(
    api_key: str,
    path: str,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    # football-data.org authenticates with X-Auth-Token.
    if not api_key:
        raise FootballDataError("FOOTBALL_DATA_API_KEY is not set.")

    headers = {
        "X-Auth-Token": api_key,
        "X-Unfold-Goals": "true",
        "X-Unfold-Lineups": "true",
    }
    try:
        response = requests.get(
            f"{BASE_URL}{path}",
            headers=headers,
            params={k: v for k, v in (params or {}).items() if v not in (None, "")},
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.HTTPError as exc:
        message = response.text.strip() if "response" in locals() else str(exc)
        raise FootballDataError(f"football-data.org request failed: {message}") from exc
    except requests.RequestException as exc:
        raise FootballDataError(f"football-data.org request failed: {exc}") from exc

    return response.json()


def _display_status(raw_status: str | None) -> str:
    # Collapse API status values into the dashboard's core states.
    if raw_status in LIVE_STATUSES:
        return "Live"
    if raw_status in FINISHED_STATUSES:
        return "Finished"
    if raw_status in UPCOMING_STATUSES:
        return "Upcoming"
    return raw_status or "Unknown"


def _score_value(score: dict[str, Any], side: str) -> int:
    # football-data.org stores score components under score.fullTime.
    full_time = score.get("fullTime") or {}
    regular_time = score.get("regularTime") or {}
    half_time = score.get("halfTime") or {}
    legacy_side = "homeTeam" if side == "home" else "awayTeam"
    value = full_time.get(side)
    if value is None:
        value = full_time.get(legacy_side)
    if value is None:
        value = regular_time.get(side)
    if value is None:
        value = regular_time.get(legacy_side)
    if value is None:
        value = half_time.get(side)
    if value is None:
        value = half_time.get(legacy_side)
    return 0 if value is None else int(value)


def _team_name(team: dict[str, Any]) -> str:
    return team.get("shortName") or team.get("name") or "TBD"


def normalize_matches(matches: list[dict[str, Any]]) -> pd.DataFrame:
    """Map football-data.org match JSON into dashboard-friendly columns."""
    rows: list[dict[str, Any]] = []
    for match in matches:
        score = match.get("score") or {}
        home_team = match.get("homeTeam") or {}
        away_team = match.get("awayTeam") or {}
        competition = match.get("competition") or {}
        utc_date = match.get("utcDate")

        rows.append(
            {
                "match_id": str(match.get("id")),
                "utc_date": utc_date,
                "status_raw": match.get("status"),
                "status": _display_status(match.get("status")),
                "minute": int(match.get("minute") or (90 if match.get("status") == "FINISHED" else 0)),
                "competition_id": competition.get("id"),
                "competition_code": competition.get("code") or "",
                "competition": competition.get("name") or "Competition",
                "stage": match.get("stage") or "",
                "group": match.get("group") or "",
                "matchday": match.get("matchday") or "",
                "venue": match.get("venue") or "",
                "home_team_id": home_team.get("id"),
                "home_team": _team_name(home_team),
                "home_team_full": home_team.get("name") or _team_name(home_team),
                "home_tla": home_team.get("tla") or "",
                "home_crest": home_team.get("crest") or "",
                "home_lineup": home_team.get("lineup") or [],
                "home_bench": home_team.get("bench") or [],
                "home_coach": home_team.get("coach") or {},
                "home_captain": home_team.get("captain") or {},
                "away_team_id": away_team.get("id"),
                "away_team": _team_name(away_team),
                "away_team_full": away_team.get("name") or _team_name(away_team),
                "away_tla": away_team.get("tla") or "",
                "away_crest": away_team.get("crest") or "",
                "away_lineup": away_team.get("lineup") or [],
                "away_bench": away_team.get("bench") or [],
                "away_coach": away_team.get("coach") or {},
                "away_captain": away_team.get("captain") or {},
                "home_goals": _score_value(score, "home"),
                "away_goals": _score_value(score, "away"),
                "winner": score.get("winner") or "",
                "duration": score.get("duration") or "",
                "last_updated": match.get("lastUpdated") or "",
                "goals": match.get("goals") or [],
                "bookings": match.get("bookings") or [],
                "substitutions": match.get("substitutions") or [],
            }
        )

    frame = pd.DataFrame(rows)
    if frame.empty:
        return pd.DataFrame(
            columns=[
                "match_id",
                "utc_date",
                "status_raw",
                "status",
                "minute",
                "competition_id",
                "competition_code",
                "competition",
                "stage",
                "group",
                "matchday",
                "venue",
                "home_team_id",
                "home_team",
                "home_team_full",
                "home_tla",
                "home_crest",
                "home_lineup",
                "home_bench",
                "home_coach",
                "home_captain",
                "away_team_id",
                "away_team",
                "away_team_full",
                "away_tla",
                "away_crest",
                "away_lineup",
                "away_bench",
                "away_coach",
                "away_captain",
                "home_goals",
                "away_goals",
                "winner",
                "duration",
                "last_updated",
                "goals",
                "bookings",
                "substitutions",
                "kickoff",
            ]
        )

    frame["kickoff"] = pd.to_datetime(frame["utc_date"], errors="coerce", utc=True)
    return frame


def fetch_matches(
    api_key: str,
    date_from: date | str | None = None,
    date_to: date | str | None = None,
    status: str | None = None,
    competitions: str | None = None,
) -> pd.DataFrame:
    """Fetch matches across subscribed competitions."""
    params = {
        "dateFrom": str(date_from) if date_from else None,
        "dateTo": str(date_to) if date_to else None,
        "status": status,
        "competitions": competitions,
    }
    payload = _request(api_key, "/matches", params)
    return normalize_matches(payload.get("matches", []))


def fetch_competition_matches(
    api_key: str,
    competition: str,
    date_from: date | str | None = None,
    date_to: date | str | None = None,
    status: str | None = None,
    season: int | str | None = None,
) -> pd.DataFrame:
    """Fetch matches for one competition, such as WC or PL."""
    params = {
        "dateFrom": str(date_from) if date_from else None,
        "dateTo": str(date_to) if date_to else None,
        "status": status,
        "season": season,
    }
    payload = _request(api_key, f"/competitions/{competition}/matches", params)
    return normalize_matches(payload.get("matches", []))


def fetch_match(api_key: str, match_id: str | int) -> pd.Series:
    """Fetch one match with richer detail such as lineups and events."""
    payload = _request(api_key, f"/matches/{match_id}")
    match = payload.get("match") or {}
    frame = normalize_matches([match] if match else [])
    if frame.empty:
        raise FootballDataError(f"Match {match_id} was not returned by the API.")
    return frame.iloc[0]


def fetch_standings(api_key: str, competition: str, season: int | str | None = None) -> pd.DataFrame:
    """Fetch the latest standings table for one competition."""
    payload = _request(api_key, f"/competitions/{competition}/standings", {"season": season})
    tables = payload.get("standings", [])
    if not tables:
        return pd.DataFrame()

    rows = []
    for standing in tables:
        group = standing.get("group") or standing.get("stage") or "Table"
        if standing.get("type") != "TOTAL":
            continue
        for row in standing.get("table", []):
            team = row.get("team") or {}
            rows.append(
                {
                    "Group": group,
                    "Position": row.get("position"),
                    "Team": team.get("shortName") or team.get("name"),
                    "Crest": team.get("crest") or "",
                    "P": row.get("playedGames"),
                    "W": row.get("won"),
                    "D": row.get("draw"),
                    "L": row.get("lost"),
                    "GF": row.get("goalsFor"),
                    "GA": row.get("goalsAgainst"),
                    "GD": row.get("goalDifference"),
                    "Pts": row.get("points"),
                }
            )
    return pd.DataFrame(rows)


def fetch_scorers(
    api_key: str,
    competition: str,
    limit: int = 20,
    season: int | str | None = None,
) -> pd.DataFrame:
    """Fetch top scorers for one competition."""
    payload = _request(api_key, f"/competitions/{competition}/scorers", {"limit": limit, "season": season})
    rows = []
    for scorer in payload.get("scorers", []):
        player = scorer.get("player") or {}
        team = scorer.get("team") or {}
        rows.append(
            {
                "Player": player.get("name"),
                "Position": player.get("position") or "",
                "Nationality": player.get("nationality") or "",
                "Team": team.get("shortName") or team.get("name") or "",
                "Team Crest": team.get("crest") or "",
                "Goals": scorer.get("goals") or 0,
                "Assists": scorer.get("assists") or 0,
                "Penalties": scorer.get("penalties") or 0,
                "Played": scorer.get("playedMatches") or 0,
            }
        )
    return pd.DataFrame(rows)
