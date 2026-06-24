from __future__ import annotations

import math

import pandas as pd


def _softmax(scores: list[float]) -> list[float]:
    # Softmax converts raw model scores into probabilities that add up to 1.
    max_score = max(scores)
    exp_scores = [math.exp(score - max_score) for score in scores]
    total = sum(exp_scores)
    return [score / total for score in exp_scores]


def estimate_probabilities(row: pd.Series) -> tuple[float, float, float]:
    """Estimate home/draw/away probabilities from match stats.

    This is a transparent baseline model for portfolio demos. Replace it with a
    trained scikit-learn model once historical match data is available.
    """
    # Create simple football features from goals, xG, shots, possession, and form.
    goal_delta = row["home_goals"] - row["away_goals"]
    xg_delta = row["home_xg"] - row["away_xg"]
    shot_delta = (row["home_shots"] - row["away_shots"]) / 10
    possession_delta = (row["home_possession"] - row["away_possession"]) / 100
    form_delta = (row["home_form_points"] - row["away_form_points"]) / 15

    # Positive strength favors the home team; negative strength favors the away team.
    home_strength = 0.85 * goal_delta + 0.75 * xg_delta + shot_delta + possession_delta + form_delta
    away_strength = -home_strength

    # Draw probability is higher when the two teams look evenly matched.
    draw_strength = 0.55 - abs(home_strength) * 0.45

    home_probability, draw_probability, away_probability = _softmax(
        [home_strength, draw_strength, away_strength]
    )
    return home_probability, draw_probability, away_probability


def prediction_label(row: pd.Series) -> str:
    # Pick the outcome with the highest estimated probability.
    probabilities = {
        "Home win": row["home_win_probability"],
        "Draw": row["draw_probability"],
        "Away win": row["away_win_probability"],
    }
    return max(probabilities, key=probabilities.get)


def add_match_predictions(matches: pd.DataFrame) -> pd.DataFrame:
    # Add prediction columns without mutating the original dataframe.
    predicted = matches.copy()
    probabilities = predicted.apply(estimate_probabilities, axis=1, result_type="expand")
    probabilities.columns = [
        "home_win_probability",
        "draw_probability",
        "away_win_probability",
    ]
    predicted = pd.concat([predicted, probabilities], axis=1)
    predicted["prediction_label"] = predicted.apply(prediction_label, axis=1)
    return predicted
