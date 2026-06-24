from __future__ import annotations

from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = {
    "match_id",
    "competition",
    "status",
    "minute",
    "home_team",
    "away_team",
    "home_goals",
    "away_goals",
    "home_possession",
    "away_possession",
    "home_shots",
    "away_shots",
    "home_xg",
    "away_xg",
    "home_form_points",
    "away_form_points",
}


def load_matches(csv_path: str | Path) -> pd.DataFrame:
    """Load match data and enforce the dashboard's expected schema."""
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Could not find match data: {path}")

    matches = pd.read_csv(path)

    # Validate the CSV early so dashboard errors are easy to understand.
    missing_columns = REQUIRED_COLUMNS.difference(matches.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Match data is missing required columns: {missing}")

    # Convert stat columns to numbers so calculations and charts behave correctly.
    numeric_columns = [
        "minute",
        "home_goals",
        "away_goals",
        "home_possession",
        "away_possession",
        "home_shots",
        "away_shots",
        "home_xg",
        "away_xg",
        "home_form_points",
        "away_form_points",
    ]
    matches[numeric_columns] = matches[numeric_columns].apply(
        pd.to_numeric,
        errors="coerce",
    )

    return matches.fillna(
        {
            "minute": 0,
            "home_goals": 0,
            "away_goals": 0,
            "home_xg": 0.0,
            "away_xg": 0.0,
            "home_form_points": 0,
            "away_form_points": 0,
        }
    )


def get_competitions(matches: pd.DataFrame) -> list[str]:
    # Sidebar filter values come from the current dataset, not hardcoded choices.
    return sorted(matches["competition"].dropna().unique().tolist())


def get_dashboard_metrics(matches: pd.DataFrame) -> dict[str, str | int]:
    # Return safe defaults so the KPI row still renders when filters remove all rows.
    if matches.empty:
        return {
            "matches": 0,
            "live_matches": 0,
            "total_goals": 0,
            "average_xg": "0.00",
        }

    total_goals = int((matches["home_goals"] + matches["away_goals"]).sum())
    total_xg = matches["home_xg"] + matches["away_xg"]

    # These metrics summarize the filtered dataset shown on screen.
    return {
        "matches": int(len(matches)),
        "live_matches": int((matches["status"] == "Live").sum()),
        "total_goals": total_goals,
        "average_xg": f"{total_xg.mean():.2f}",
    }
