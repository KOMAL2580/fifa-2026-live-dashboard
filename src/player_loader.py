from __future__ import annotations

from pathlib import Path

import pandas as pd


PLAYER_REQUIRED_COLUMNS = {
    "player_id",
    "player_name",
    "team",
    "country",
    "position",
    "match_id",
    "minutes_played",
    "goals",
    "assists",
    "shots",
    "shots_on_target",
    "xg",
    "xa",
    "passes_completed",
    "passes_attempted",
    "pass_accuracy",
    "key_passes",
    "tackles",
    "interceptions",
    "saves",
    "yellow_cards",
    "red_cards",
    "player_rating",
    "age",
    "shirt_number",
    "formation_x",
    "formation_y",
}

EVENT_REQUIRED_COLUMNS = {
    "match_id",
    "minute",
    "event_type",
    "team",
    "player_name",
    "detail",
}


def _validate_columns(frame: pd.DataFrame, required_columns: set[str], label: str) -> None:
    # Fail fast if a CSV does not match the expected dashboard schema.
    missing = required_columns.difference(frame.columns)
    if missing:
        missing_text = ", ".join(sorted(missing))
        raise ValueError(f"{label} data is missing required columns: {missing_text}")


def load_players(csv_path: str | Path) -> pd.DataFrame:
    """Load player-level match analytics for leaderboards and team views."""
    players = pd.read_csv(csv_path)
    _validate_columns(players, PLAYER_REQUIRED_COLUMNS, "Player")

    numeric_columns = [
        "minutes_played",
        "goals",
        "assists",
        "shots",
        "shots_on_target",
        "xg",
        "xa",
        "passes_completed",
        "passes_attempted",
        "pass_accuracy",
        "key_passes",
        "tackles",
        "interceptions",
        "saves",
        "yellow_cards",
        "red_cards",
        "player_rating",
        "age",
        "shirt_number",
        "formation_x",
        "formation_y",
    ]
    players[numeric_columns] = players[numeric_columns].apply(pd.to_numeric, errors="coerce")
    return players.fillna(0)


def load_events(csv_path: str | Path) -> pd.DataFrame:
    """Load match event timelines used in previous-match replay panels."""
    events = pd.read_csv(csv_path)
    _validate_columns(events, EVENT_REQUIRED_COLUMNS, "Event")
    events["minute"] = pd.to_numeric(events["minute"], errors="coerce").fillna(0)
    return events
