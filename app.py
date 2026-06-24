from __future__ import annotations

import os
from datetime import date, datetime, timedelta
from html import escape

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.football_data import (
    FINISHED_STATUSES,
    FootballDataError,
    LIVE_STATUSES,
    UPCOMING_STATUSES,
    fetch_competition_matches,
    fetch_match,
    fetch_scorers,
    fetch_standings,
)


st.set_page_config(
    page_title="FIFA 2026 Live Analytics",
    page_icon="F",
    layout="wide",
    initial_sidebar_state="expanded",
)


REFRESH_SECONDS = 120
DEFAULT_UPCOMING_DAYS = 10
WORLD_CUP_COMPETITION = "WC"
WORLD_CUP_SEASON = 2026
WORLD_CUP_LABEL = "FIFA World Cup 2026"
WORLD_CUP_START_DATE = date(2026, 6, 11)
WORLD_CUP_LOGO_URL = "https://upload.wikimedia.org/wikipedia/en/thumb/1/17/2026_FIFA_World_Cup_emblem.svg/250px-2026_FIFA_World_Cup_emblem.svg.png"
NAV_ITEMS = [
    "Tournament Hub",
    "Match Centre",
    "Previous Matches",
    "Team Deep Dive",
    "Leaderboards",
]

COLOR_ACCENT = "#00d084"
COLOR_BLUE = "#4f8cff"
COLOR_YELLOW = "#ffd400"
COLOR_RED = "#ff4d5d"
PLOT_BG = "#111722"
PAPER_BG = "#0b1018"


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        .stApp { background: #080c12; color: #eef2ff; }
        section[data-testid="stSidebar"] {
            background: #070b12;
            border-right: 1px solid #263247;
            min-height: 100vh;
        }
        section[data-testid="stSidebar"] * { color: #d6deef; }
        section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
            padding: 2rem 1.1rem;
        }
        .block-container {
            padding-top: 1.25rem;
            padding-bottom: 2rem;
            max-width: 1480px;
        }
        .sidebar-brand {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: .55rem;
            padding: 1.25rem 0 2.25rem 0;
            text-align: center;
        }
        .sidebar-brand img {
            width: 68px;
            height: 68px;
            object-fit: contain;
        }
        .sidebar-brand-title {
            color: #f4f7fc;
            font-size: 1.22rem;
            font-weight: 900;
            line-height: 1.05;
        }
        .sidebar-brand-year {
            color: #00d084;
            font-size: 2.05rem;
            font-weight: 950;
            line-height: 1;
            margin-bottom: .15rem;
        }
        .sidebar-brand-sub {
            color: #9aa5ba;
            font-size: .78rem;
            letter-spacing: .14rem;
            text-transform: uppercase;
            margin-top: .35rem;
        }
        section[data-testid="stSidebar"] [data-testid="stRadio"] {
            width: 100%;
        }
        section[data-testid="stSidebar"] [data-testid="stRadio"] > label {
            display: none;
        }
        section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] {
            display: grid;
            gap: .55rem;
            width: 100%;
        }
        section[data-testid="stSidebar"] [data-testid="stRadio"] label {
            justify-content: flex-start;
            min-height: 3.05rem;
            padding: .35rem .7rem;
            border-radius: 8px;
            white-space: nowrap;
        }
        section[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
            background: rgba(0, 208, 132, .08);
        }
        section[data-testid="stSidebar"] [data-testid="stRadio"] p {
            font-size: 1.08rem;
            font-weight: 850;
            text-align: left;
            white-space: nowrap;
        }
        h1, h2, h3 { letter-spacing: 0; color: #f7f8fc; }
        [data-testid="stMetric"] {
            background: #111722;
            border: 1px solid #28354d;
            border-radius: 8px;
            padding: 1rem;
        }
        [data-testid="stMetricValue"] { color: #00d084; }
        .fixture-ticker {
            display: flex;
            gap: 0.75rem;
            overflow-x: auto;
            white-space: nowrap;
            padding: 0.75rem;
            border: 1px solid #263247;
            border-radius: 8px;
            background: #0d121c;
            margin-bottom: 1rem;
        }
        .ticker-item {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            min-width: fit-content;
            color: #dce4f5;
        }
        .pill {
            display: inline-block;
            padding: 0.2rem 0.55rem;
            border-radius: 999px;
            font-size: 0.72rem;
            font-weight: 700;
            color: #081016;
            background: #00d084;
        }
        .pill-blue { background: #2f81f7; color: #f8fbff; }
        .pill-red { background: #ff4d5d; color: #fff; }
        .pill-gray { background: #2b3444; color: #d6deef; }
        .panel {
            border: 1px solid #28354d;
            border-radius: 8px;
            background: #111722;
            padding: 1rem;
            margin-bottom: 1rem;
        }
        .panel-title {
            color: #8994aa;
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.18rem;
            margin-bottom: 0.7rem;
        }
        .section-grid {
            display: grid;
            gap: 1rem;
            margin-bottom: 1rem;
        }
        .section-grid.two {
            grid-template-columns: minmax(0, 1.45fr) minmax(420px, 1fr);
        }
        .section-grid.three {
            grid-template-columns: minmax(320px, 1fr) minmax(320px, 1fr) minmax(320px, 1fr);
        }
        .hero-title {
            font-size: 3.05rem;
            line-height: 1;
            font-weight: 850;
            margin: 0;
            color: #f5f7fb;
        }
        .hub-heading {
            display: flex;
            align-items: baseline;
            gap: 1rem;
            margin-bottom: 1rem;
            flex-wrap: wrap;
        }
        .hub-heading .hero-title { margin-bottom: 0; }
        .hub-phase {
            color: #8f99ad;
            font-size: 1.05rem;
            font-weight: 700;
        }
        .muted { color: #8f99ad; }
        .score-card {
            display: grid;
            grid-template-columns: 1fr auto 1fr;
            gap: 1rem;
            align-items: center;
            border: 1px solid #28354d;
            border-radius: 8px;
            background: #111722;
            padding: 1.25rem;
            margin-bottom: 1rem;
        }
        .team-name {
            color: #f2f5fb;
            font-size: 1.35rem;
            font-weight: 800;
        }
        .score-box {
            border: 1px solid #33425e;
            border-radius: 8px;
            background: #151e2b;
            padding: 0.7rem 1.5rem;
            color: #f7f9ff;
            font-size: 2.55rem;
            font-weight: 900;
            text-align: center;
            min-width: 150px;
        }
        .match-console-card {
            display: grid;
            grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr) auto;
            gap: 1.5rem;
            align-items: center;
            border: 1px solid #28354d;
            border-radius: 8px;
            background: #111722;
            padding: 1.6rem;
            margin-bottom: 1rem;
        }
        .match-console-team {
            min-width: 0;
        }
        .match-console-team.away {
            text-align: right;
        }
        .match-console-name {
            color: #f7f8fc;
            font-size: 2rem;
            font-weight: 900;
            line-height: 1.05;
            display: flex;
            align-items: center;
            gap: .75rem;
        }
        .match-console-team.away .match-console-name {
            justify-content: flex-end;
        }
        .match-console-crest {
            width: 34px;
            height: 34px;
            object-fit: contain;
            flex: 0 0 34px;
        }
        .match-console-score {
            border: 1px solid #33425e;
            border-radius: 8px;
            background: #151e2b;
            padding: .7rem 1.7rem;
            min-width: 170px;
            text-align: center;
            color: #00d084;
            font-size: 3.7rem;
            line-height: 1;
            font-weight: 950;
        }
        .match-console-meta {
            text-align: right;
            color: #8f99ad;
            min-width: 230px;
        }
        .formation-note {
            color: #8f99ad;
            margin: .4rem 0 1rem 0;
        }
        .pitch {
            position: relative;
            aspect-ratio: 1.58 / 1;
            min-height: 500px;
            border: 2px solid #087a47;
            background: #031f12;
            overflow: hidden;
        }
        .pitch::before {
            content: "";
            position: absolute;
            inset: 0;
            background:
                linear-gradient(90deg, transparent 49.85%, #087a47 50%, transparent 50.15%),
                radial-gradient(circle at 50% 50%, transparent 0 10%, #087a47 10.2% 10.5%, transparent 10.8%),
                linear-gradient(#087a47, #087a47) 0 50% / 100% 1px no-repeat;
            opacity: .85;
        }
        .pitch-box {
            position: absolute;
            top: 22%;
            width: 10%;
            height: 56%;
            border: 1px solid #087a47;
        }
        .pitch-box.left { left: 0; border-left: 0; }
        .pitch-box.right { right: 0; border-right: 0; }
        .pitch-dot {
            position: absolute;
            transform: translate(-50%, -50%);
            width: 34px;
            height: 34px;
            border-radius: 999px;
            display: grid;
            place-items: center;
            font-size: .76rem;
            font-weight: 900;
            color: #071017;
            z-index: 2;
        }
        .pitch-dot.home { background: #4f8cff; }
        .pitch-dot.away { background: #00d084; }
        .pitch-label {
            position: absolute;
            transform: translate(-50%, 18px);
            color: #58a2ff;
            font-size: .78rem;
            font-weight: 700;
            max-width: 76px;
            text-align: center;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            z-index: 2;
        }
        .pitch-label.away { color: #00d084; }
        .timeline {
            position: relative;
            padding-left: 2rem;
            margin-top: .5rem;
        }
        .timeline::before {
            content: "";
            position: absolute;
            left: .62rem;
            top: .4rem;
            bottom: .4rem;
            width: 3px;
            background: #009b63;
        }
        .timeline-item {
            position: relative;
            padding: .45rem 0 1rem 0;
        }
        .timeline-icon {
            position: absolute;
            left: -1.83rem;
            top: .45rem;
            width: 1.45rem;
            height: 1.45rem;
            border-radius: 999px;
            background: #00d084;
            color: #071017;
            display: grid;
            place-items: center;
            font-size: .75rem;
            font-weight: 900;
            box-shadow: 0 0 0 4px rgba(0, 208, 132, .18);
        }
        .timeline-minute {
            color: #00d084;
            font-weight: 900;
            margin-right: 1.2rem;
        }
        .timeline-title {
            color: #f4f7fc;
            font-weight: 800;
        }
        .event-row {
            border-left: 3px solid #00d084;
            padding: 0.35rem 0 0.35rem 0.85rem;
            margin-bottom: 0.65rem;
            color: #dce4f5;
        }
        .leader-card {
            border: 1px solid #28354d;
            border-radius: 8px;
            background: #111722;
            padding: 1rem;
            margin-bottom: 0.75rem;
        }
        .big-number {
            font-size: 2.45rem;
            font-weight: 900;
            color: #ffd400;
        }
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 1rem;
            margin-bottom: 1rem;
        }
        .kpi-card {
            min-height: 150px;
            border: 1px solid #28354d;
            border-radius: 8px;
            background: #111722;
            padding: 1.05rem 1.2rem;
        }
        .kpi-label {
            color: #8994aa;
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.18rem;
            margin-bottom: 0.8rem;
        }
        .kpi-value {
            font-size: 2.85rem;
            line-height: 1;
            font-weight: 900;
        }
        .kpi-caption {
            color: #8f99ad;
            font-size: 0.95rem;
            margin-top: 0.5rem;
        }
        .fixture-row {
            display: grid;
            grid-template-columns: minmax(0, 1.25fr) auto minmax(180px, .8fr);
            gap: 1rem;
            align-items: center;
            border: 1px solid #28354d;
            border-radius: 8px;
            background: #111722;
            padding: 0.95rem 1rem;
            margin-bottom: 0.75rem;
            min-height: 76px;
        }
        .fixture-teams {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            min-width: 0;
            font-weight: 800;
        }
        .fixture-meta {
            color: #8f99ad;
            text-align: right;
            white-space: nowrap;
        }
        .team-inline {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            min-width: 0;
        }
        .team-inline span:last-child {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .crest {
            width: 20px;
            height: 20px;
            object-fit: contain;
            vertical-align: middle;
            flex: 0 0 20px;
        }
        .standings-wrap {
            overflow-x: auto;
            min-height: 318px;
        }
        .standings-table {
            width: 100%;
            border-collapse: collapse;
            color: #dce4f5;
            min-width: 560px;
        }
        .standings-table th,
        .standings-table td {
            border-bottom: 1px solid #303848;
            padding: 0.72rem 0.5rem;
            text-align: right;
        }
        .standings-table th:first-child,
        .standings-table td:first-child {
            text-align: left;
        }
        .rank-dot {
            display: inline-block;
            width: 0.65rem;
            height: 0.65rem;
            border-radius: 999px;
            margin-right: 0.65rem;
            background: #00d084;
        }
        .rank-dot.mid { background: #ffd400; }
        .rank-dot.low { background: #ff4d5d; }
        .match-snapshot-card {
            border: 1px solid #28354d;
            border-radius: 8px;
            background: #111722;
            padding: 1rem;
            margin-bottom: 1rem;
        }
        .panel-bottom-fill {
            min-height: 250px;
        }
        .formation-empty {
            min-height: 520px;
            display: flex;
            align-items: flex-start;
        }
        .hub-panel-marker {
            display: none;
        }
        div[data-testid="stVerticalBlock"]:has(.hub-panel-top),
        div[data-testid="stLayoutWrapper"]:has(.hub-panel-top),
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.hub-panel-top) {
            min-height: 560px;
        }
        div[data-testid="stVerticalBlock"]:has(.hub-panel-bottom),
        div[data-testid="stLayoutWrapper"]:has(.hub-panel-bottom),
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.hub-panel-bottom) {
            min-height: 760px;
        }
        .scorer-row {
            display: grid;
            grid-template-columns: 2rem minmax(0, 1fr) auto;
            gap: .75rem;
            align-items: center;
            border-bottom: 1px solid #252d3b;
            padding: .85rem 0;
        }
        .scorer-score {
            color: #ffd400;
            font-size: 2.2rem;
            line-height: 1;
            font-weight: 900;
        }
        .legend-row {
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
            margin-top: 1rem;
            color: #8f99ad;
        }
        div[data-baseweb="popover"] ul {
            max-height: 165px;
            overflow-y: auto;
        }
        @media (max-width: 1100px) {
            .kpi-grid,
            .section-grid.two,
            .section-grid.three {
                grid-template-columns: 1fr;
            }
            .fixture-row {
                grid-template-columns: 1fr;
            }
            .match-console-card {
                grid-template-columns: 1fr;
            }
            .match-console-team.away,
            .match-console-meta {
                text-align: left;
            }
            .match-console-team.away .match-console-name {
                justify-content: flex-start;
            }
            .fixture-meta { text-align: left; white-space: normal; }
        }
        div[data-testid="stDataFrame"] {
            border: 1px solid #28354d;
            border-radius: 8px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_config_value(name: str) -> str:
    if os.getenv(name):
        return os.getenv(name, "")
    try:
        return st.secrets.get(name, "")
    except Exception:
        return ""


def enable_auto_refresh() -> None:
    st.html(
        f"""
        <script>
            setTimeout(function() {{
                const expandButton = window.parent.document.querySelector(
                    '[data-testid="stExpandSidebarButton"], button[data-testid="stExpandSidebarButton"]'
                );
                if (expandButton) {{
                    expandButton.click();
                }}
            }}, 250);
            setTimeout(function() {{
                window.parent.location.reload();
            }}, {REFRESH_SECONDS * 1000});
        </script>
        """,
        unsafe_allow_javascript=True,
    )


def badge(status: str) -> str:
    if status == "Live":
        return "<span class='pill pill-red'>LIVE</span>"
    if status == "Upcoming":
        return "<span class='pill pill-blue'>UP NEXT</span>"
    if status == "Finished":
        return "<span class='pill'>FT</span>"
    return f"<span class='pill pill-gray'>{escape(status.upper())}</span>"


def crest_img(url: object) -> str:
    # football-data.org exposes crest/flag URLs for many national teams.
    if not isinstance(url, str) or not url:
        return ""
    safe_url = escape(url, quote=True)
    return f"<img class='crest' src='{safe_url}' alt='' />"


def team_inline(name: object, crest_url: object = "") -> str:
    # Render a team name with its crest/flag where the API provides one.
    return (
        "<span class='team-inline'>"
        f"{crest_img(crest_url)}"
        f"<span>{escape(str(name))}</span>"
        "</span>"
    )


def is_tbd_team(name: object) -> bool:
    value = str(name or "").strip().upper()
    return value in {"", "TBD", "TO BE DETERMINED"}


def local_time(value: object) -> str:
    if pd.isna(value):
        return "TBD"
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    return timestamp.tz_convert("Asia/Kolkata").strftime("%d %b | %H:%M IST")


def safe_int(value: object, default: int = 0) -> int:
    if pd.isna(value):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def plotly_layout(fig: go.Figure, height: int = 360) -> go.Figure:
    fig.update_layout(
        height=height,
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=dict(color="#d7deed"),
        margin=dict(l=20, r=20, t=55, b=25),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    fig.update_xaxes(gridcolor="#263247", zerolinecolor="#263247")
    fig.update_yaxes(gridcolor="#263247", zerolinecolor="#263247")
    return fig


@st.cache_data(ttl=REFRESH_SECONDS, show_spinner="Loading live football data...")
def load_dashboard_data(
    api_key: str,
    today_text: str,
    upcoming_days: int,
) -> dict[str, pd.DataFrame | str]:
    today = date.fromisoformat(today_text)
    date_from_previous = WORLD_CUP_START_DATE
    date_to_upcoming = today + timedelta(days=upcoming_days)

    all_matches = fetch_competition_matches(
        api_key,
        WORLD_CUP_COMPETITION,
        date_from_previous,
        date_to_upcoming,
        season=WORLD_CUP_SEASON,
    )
    try:
        standings = fetch_standings(api_key, WORLD_CUP_COMPETITION, season=WORLD_CUP_SEASON)
    except FootballDataError:
        standings = pd.DataFrame()
    try:
        scorers = fetch_scorers(api_key, WORLD_CUP_COMPETITION, season=WORLD_CUP_SEASON)
    except FootballDataError:
        scorers = pd.DataFrame()

    live_matches = all_matches[all_matches["status_raw"].isin(LIVE_STATUSES)].copy()
    previous_matches = all_matches[all_matches["status_raw"].isin(FINISHED_STATUSES)].copy()
    upcoming_matches = all_matches[all_matches["status_raw"].isin(UPCOMING_STATUSES)].copy()

    return {
        "all_matches": all_matches,
        "live_matches": live_matches,
        "previous_matches": previous_matches.sort_values("kickoff", ascending=False),
        "upcoming_matches": upcoming_matches.sort_values("kickoff"),
        "standings": standings,
        "scorers": scorers,
        "loaded_at": datetime.now().strftime("%d %b %Y, %H:%M:%S"),
    }


@st.cache_data(ttl=REFRESH_SECONDS, show_spinner="Loading match detail...")
def load_match_detail(api_key: str, match_id: str) -> pd.Series:
    return fetch_match(api_key, match_id)


def render_header(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div style="margin-bottom:1rem;">
            <p class="muted" style="margin:0;text-transform:uppercase;letter-spacing:.2rem;">FIFA 2026</p>
            <h1 class="hero-title">{escape(title)}</h1>
            <p class="muted">{escape(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hub_heading(all_matches: pd.DataFrame) -> None:
    phase = "Group Stage"
    matchdays = pd.to_numeric(all_matches.get("matchday"), errors="coerce") if not all_matches.empty else pd.Series(dtype=float)
    valid_matchdays = matchdays.dropna()
    if not valid_matchdays.empty:
        phase = f"Group Stage - Matchday {int(valid_matchdays.max())}"
    st.markdown(
        f"""
        <div class="hub-heading">
            <h1 class="hero-title">Tournament Hub</h1>
            <div class="hub-phase">{escape(phase)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state(title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="panel">
            <div class="panel-title">{escape(title)}</div>
            <p class="muted">{escape(body)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_ticker(matches: pd.DataFrame) -> None:
    if matches.empty:
        return
    ticker_matches = matches[
        ~(matches["home_team"].map(is_tbd_team) & matches["away_team"].map(is_tbd_team))
    ].sort_values("kickoff")
    if ticker_matches.empty:
        return
    ticker_matches = ticker_matches.head(10)
    items = []
    for _, match in ticker_matches.iterrows():
        score = f"{safe_int(match['home_goals'])}-{safe_int(match['away_goals'])}"
        if match["status"] == "Upcoming":
            score = local_time(match["kickoff"])
        items.append(
            "<div class='ticker-item'>"
            f"{badge(str(match['status']))}"
            f"<strong>{team_inline(match['home_team'], match.get('home_crest', ''))}</strong>"
            "<span>vs</span>"
            f"<strong>{team_inline(match['away_team'], match.get('away_crest', ''))}</strong>"
            f"<span class='muted'>{escape(score)}</span>"
            "</div>"
        )
    st.markdown(f"<div class='fixture-ticker'>{''.join(items)}</div>", unsafe_allow_html=True)


def render_score_card(match: pd.Series) -> None:
    if match["status"] == "Upcoming":
        center = local_time(match["kickoff"])
    else:
        center = f"{safe_int(match['home_goals'])} - {safe_int(match['away_goals'])}"

    detail = " | ".join(
        part
        for part in [
            str(match.get("competition", "")),
            str(match.get("stage", "")).replace("_", " ").title(),
            str(match.get("venue", "")),
        ]
        if part
    )

    st.markdown(
        f"""
        <div class="score-card">
            <div>
                <div class="team-name">{team_inline(match['home_team'], match.get('home_crest', ''))}</div>
                <div class="muted">{escape(str(match.get('home_tla') or match.get('home_team_full') or ''))}</div>
            </div>
            <div>
                <div style="text-align:center;margin-bottom:.4rem;">{badge(str(match['status']))}</div>
                <div class="score-box">{escape(center)}</div>
                <div class="muted" style="text-align:center;margin-top:.4rem;">{escape(detail)}</div>
            </div>
            <div style="text-align:right;">
                <div class="team-name" style="justify-content:flex-end;">{team_inline(match['away_team'], match.get('away_crest', ''))}</div>
                <div class="muted">{escape(str(match.get('away_tla') or match.get('away_team_full') or ''))}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_match_list(matches: pd.DataFrame, title: str, limit: int = 8) -> None:
    st.markdown(f"<div class='panel-title'>{escape(title)}</div>", unsafe_allow_html=True)
    if matches.empty:
        st.caption("No matches available for this window.")
        return

    for _, match in matches.head(limit).iterrows():
        if match["status"] == "Upcoming":
            detail = local_time(match["kickoff"])
        else:
            detail = f"{safe_int(match['home_goals'])}-{safe_int(match['away_goals'])}"
        venue = str(match.get("venue") or "")
        st.markdown(
            f"""
            <div class="fixture-row">
                <div class="fixture-teams">
                    {team_inline(match['home_team'], match.get('home_crest', ''))}
                    <span style="color:#8f99ad;">VS</span>
                    {team_inline(match['away_team'], match.get('away_crest', ''))}
                </div>
                <div>{badge(str(match['status']))}</div>
                <div class="fixture-meta">{escape(detail)}{f" | {escape(venue)}" if venue else ""}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def build_metrics(all_matches: pd.DataFrame, live_matches: pd.DataFrame, previous_matches: pd.DataFrame) -> dict[str, int]:
    if all_matches.empty:
        return {"matches": 0, "live": 0, "previous": 0, "goals": 0}
    goals = (
        safe_int((previous_matches["home_goals"].fillna(0) + previous_matches["away_goals"].fillna(0)).sum())
        if not previous_matches.empty
        else 0
    )
    return {
        "matches": int(len(all_matches)),
        "live": int(len(live_matches)),
        "previous": int(len(previous_matches)),
        "goals": goals,
    }


def render_hub_kpis(metrics: dict[str, int]) -> None:
    goals_per_match = metrics["goals"] / metrics["previous"] if metrics["previous"] else 0
    cards = [
        ("Teams", "48", "Qualified nations", COLOR_ACCENT),
        ("Matches Played", str(metrics["previous"]), "of 104 total", COLOR_BLUE),
        ("Goals Scored", str(metrics["goals"]), f"{goals_per_match:.2f} per match", COLOR_YELLOW),
        ("Live Now", str(metrics["live"]), "Matches in play", COLOR_RED),
    ]
    html_cards = []
    for label, value, caption, color in cards:
        html_cards.append(
            "<div class='kpi-card'>"
            f"<div class='kpi-label'>{escape(label)}</div>"
            f"<div class='kpi-value' style='color:{color};'>{escape(value)}</div>"
            f"<div class='kpi-caption'>{escape(caption)}</div>"
            "</div>"
        )
    st.html(f"<div class='kpi-grid'>{''.join(html_cards)}</div>")


def build_local_standings(previous_matches: pd.DataFrame) -> pd.DataFrame:
    rows: dict[str, dict[str, int | str]] = {}
    for _, match in previous_matches.iterrows():
        home = str(match["home_team"])
        away = str(match["away_team"])
        rows.setdefault(home, {"Team": home, "P": 0, "W": 0, "D": 0, "L": 0, "GF": 0, "GA": 0, "Pts": 0})
        rows.setdefault(away, {"Team": away, "P": 0, "W": 0, "D": 0, "L": 0, "GF": 0, "GA": 0, "Pts": 0})
        home_goals = safe_int(match["home_goals"])
        away_goals = safe_int(match["away_goals"])
        rows[home]["P"] += 1
        rows[away]["P"] += 1
        rows[home]["GF"] += home_goals
        rows[home]["GA"] += away_goals
        rows[away]["GF"] += away_goals
        rows[away]["GA"] += home_goals
        if home_goals > away_goals:
            rows[home]["W"] += 1
            rows[away]["L"] += 1
            rows[home]["Pts"] += 3
        elif home_goals < away_goals:
            rows[away]["W"] += 1
            rows[home]["L"] += 1
            rows[away]["Pts"] += 3
        else:
            rows[home]["D"] += 1
            rows[away]["D"] += 1
            rows[home]["Pts"] += 1
            rows[away]["Pts"] += 1
    table = pd.DataFrame(rows.values())
    if table.empty:
        return table
    table["GD"] = table["GF"] - table["GA"]
    return table.sort_values(["Pts", "GD", "GF"], ascending=[False, False, False])[
        ["Team", "P", "W", "D", "L", "GD", "Pts"]
    ]


def add_crests_to_standings(standings: pd.DataFrame, matches: pd.DataFrame) -> pd.DataFrame:
    table = standings.copy()
    if table.empty or "Team" not in table.columns:
        return table
    crest_map: dict[str, str] = {}
    if not matches.empty:
        for _, match in matches.iterrows():
            crest_map[str(match.get("home_team", ""))] = str(match.get("home_crest", "") or "")
            crest_map[str(match.get("home_team_full", ""))] = str(match.get("home_crest", "") or "")
            crest_map[str(match.get("away_team", ""))] = str(match.get("away_crest", "") or "")
            crest_map[str(match.get("away_team_full", ""))] = str(match.get("away_crest", "") or "")
    if "Crest" not in table.columns:
        table["Crest"] = table["Team"].map(crest_map).fillna("")
    else:
        table["Crest"] = table["Crest"].fillna("")
        missing = table["Crest"].eq("")
        table.loc[missing, "Crest"] = table.loc[missing, "Team"].map(crest_map).fillna("")
    return table


def normalize_group_label(value: object) -> str:
    """Turn API labels such as GROUP_A into readable dashboard labels."""
    text = str(value or "").replace("_", " ").strip()
    upper = text.upper()
    if not text or upper in {"NONE", "NAN", "GROUP STAGE", "GROUPSTAGE"}:
        return ""
    parts = text.split()
    if len(parts) == 1 and len(parts[0]) == 1 and parts[0].isalpha():
        return f"Group {parts[0].upper()}"
    if parts and parts[0].upper() == "GROUP":
        suffix = parts[-1]
        if len(suffix) == 1 and suffix.isalpha():
            return f"Group {suffix.upper()}"
    return text.title()


def group_sort_key(group: object) -> tuple[str, str]:
    text = normalize_group_label(group) or str(group)
    suffix = text.rsplit(" ", 1)[-1]
    if len(suffix) == 1 and suffix.isalpha():
        return (f"{ord(suffix.upper()) - ord('A'):02d}", text)
    return (text, text)


def group_options_from_matches(matches: pd.DataFrame) -> list[str]:
    if matches.empty or "group" not in matches.columns:
        return []
    groups = {normalize_group_label(group) for group in matches["group"].dropna().tolist()}
    return sorted([group for group in groups if group], key=group_sort_key)


def matches_for_group(matches: pd.DataFrame, group_label: str) -> pd.DataFrame:
    if matches.empty or "group" not in matches.columns:
        return matches.iloc[0:0].copy()
    group_labels = matches["group"].map(normalize_group_label)
    return matches[group_labels == group_label].copy()


def build_group_standings(group_label: str, all_matches: pd.DataFrame, previous_matches: pd.DataFrame) -> pd.DataFrame:
    group_matches = matches_for_group(all_matches, group_label)
    group_results = matches_for_group(previous_matches, group_label)
    table = build_local_standings(group_results)

    teams: dict[str, str] = {}
    for _, match in group_matches.iterrows():
        for side in ("home", "away"):
            team = str(match.get(f"{side}_team", "") or "")
            if is_tbd_team(team):
                continue
            teams[team] = str(match.get(f"{side}_crest", "") or "")

    if table.empty:
        table = pd.DataFrame(
            [
                {"Team": team, "P": 0, "W": 0, "D": 0, "L": 0, "GD": 0, "Pts": 0}
                for team in teams
            ]
        )
    else:
        visible_teams = set(table["Team"].astype(str))
        missing_rows = [
            {"Team": team, "P": 0, "W": 0, "D": 0, "L": 0, "GD": 0, "Pts": 0}
            for team in teams
            if team not in visible_teams
        ]
        if missing_rows:
            table = pd.concat([table, pd.DataFrame(missing_rows)], ignore_index=True)

    if table.empty:
        return table
    table["Group"] = group_label
    table["Crest"] = table["Team"].map(teams).fillna("")
    table = table.sort_values(["Pts", "GD", "W", "Team"], ascending=[False, False, False, True]).reset_index(drop=True)
    table["Position"] = table.index + 1
    return table


def render_standings_table(table: pd.DataFrame, limit: int = 5) -> None:
    if table.empty:
        st.caption("Standings will appear once the tournament table is available.")
        return

    rows = []
    visible_table = table.head(limit).reset_index(drop=True)
    for index, (_, row) in enumerate(visible_table.iterrows(), start=1):
        position = safe_int(row.get("Position"), index)
        dot_class = "rank-dot"
        if position == 3:
            dot_class = "rank-dot mid"
        elif position >= 4:
            dot_class = "rank-dot low"
        rows.append(
            "<tr>"
            f"<td><span class='{dot_class}'></span>{team_inline(row.get('Team', ''), row.get('Crest', ''))}</td>"
            f"<td>{safe_int(row.get('P'))}</td>"
            f"<td>{safe_int(row.get('W'))}</td>"
            f"<td>{safe_int(row.get('D'))}</td>"
            f"<td>{safe_int(row.get('L'))}</td>"
            f"<td>{safe_int(row.get('GD'))}</td>"
            f"<td style='color:#00d084;font-weight:900;'>{safe_int(row.get('Pts'))}</td>"
            "</tr>"
        )
    st.markdown(
        f"""
        <div class="standings-wrap">
            <table class="standings-table">
                <thead>
                    <tr><th>Team</th><th>P</th><th>W</th><th>D</th><th>L</th><th>GD</th><th>Pts</th></tr>
                </thead>
                <tbody>{''.join(rows)}</tbody>
            </table>
        </div>
        <div class="legend-row">
            <span><span class="rank-dot"></span>Qualify</span>
            <span><span class="rank-dot mid"></span>Play-off</span>
            <span><span class="rank-dot low"></span>Eliminated</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_standings_panel(standings: pd.DataFrame, previous_matches: pd.DataFrame, all_matches: pd.DataFrame) -> None:
    st.markdown("<div class='panel-title'>Group Standings</div>", unsafe_allow_html=True)
    api_table = pd.DataFrame()
    if isinstance(standings, pd.DataFrame) and not standings.empty:
        api_table = add_crests_to_standings(standings, all_matches)
        api_table["GroupLabel"] = api_table.get("Group", pd.Series(dtype=str)).map(normalize_group_label)

    groups = sorted(
        set(group_options_from_matches(all_matches))
        | {group for group in api_table.get("GroupLabel", pd.Series(dtype=str)).dropna().tolist() if group},
        key=group_sort_key,
    )

    if groups:
        selected_group = st.selectbox("Group", groups, key="hub_group_selector", label_visibility="collapsed")
        table = pd.DataFrame()
        if not api_table.empty:
            table = api_table[api_table["GroupLabel"] == selected_group].copy()
        if table.empty:
            table = build_group_standings(selected_group, all_matches, previous_matches)
        if not table.empty and "Position" not in table.columns:
            table = table.reset_index(drop=True)
            table["Position"] = table.index + 1
        sort_cols = [col for col in ["Position", "Pts", "GD", "GF"] if col in table.columns]
        if "Position" in sort_cols:
            table = table.sort_values("Position")
        elif sort_cols:
            table = table.sort_values(sort_cols, ascending=[False] * len(sort_cols))
        render_standings_table(table)
        return

    if not api_table.empty:
        sort_cols = [col for col in ["Position", "Pts", "GD", "GF"] if col in api_table.columns]
        if "Position" in sort_cols:
            api_table = api_table.sort_values("Position")
        elif sort_cols:
            api_table = api_table.sort_values(sort_cols, ascending=[False] * len(sort_cols))
        render_standings_table(api_table)
        return

    local_table = add_crests_to_standings(build_local_standings(previous_matches), all_matches)
    render_standings_table(local_table)


def render_top_scorers_panel(scorers: pd.DataFrame) -> None:
    st.markdown("<div class='panel-title'>Top Scorers</div>", unsafe_allow_html=True)
    if not isinstance(scorers, pd.DataFrame) or scorers.empty:
        st.caption("Top scorer data will appear when tournament scorer records are available.")
        return
    rows = []
    for place, (_, row) in enumerate(scorers.head(5).iterrows(), start=1):
        rows.append(
            f"""
            <div class="scorer-row">
                <div class="muted">{place}</div>
                <div>
                    <strong>{escape(str(row.get('Player', '')))}</strong>
                    <div class="muted">{team_inline(row.get('Team', ''), row.get('Team Crest', ''))}</div>
                </div>
                <div class="scorer-score">{safe_int(row.get('Goals'))}</div>
            </div>
            """
        )
    st.markdown("".join(rows), unsafe_allow_html=True)


def compact_match_card(match: pd.Series, label: str) -> str:
    if match["status"] == "Upcoming":
        title = (
            f"{team_inline(match['home_team'], match.get('home_crest', ''))} "
            "<span style='color:#8f99ad;'>vs</span> "
            f"{team_inline(match['away_team'], match.get('away_crest', ''))}"
        )
        detail = local_time(match["kickoff"])
        pill_class = "pill pill-blue"
    else:
        title = (
            f"{team_inline(match['home_team'], match.get('home_crest', ''))} "
            f"{safe_int(match['home_goals'])} - {safe_int(match['away_goals'])} "
            f"{team_inline(match['away_team'], match.get('away_crest', ''))}"
        )
        detail = str(match.get("venue") or local_time(match["kickoff"]))
        pill_class = "pill pill-red" if label == "LIVE" else "pill pill-gray"
    return (
        "<div class='match-snapshot-card'>"
        f"<span class='{pill_class}'>{escape(label)}</span>"
        f"<div style='margin-top:.75rem;font-weight:850;color:#f4f7fc;'>{title}</div>"
        f"<div class='muted' style='margin-top:.55rem;'>{escape(detail)}</div>"
        "</div>"
    )


def render_live_snapshot(live_matches: pd.DataFrame, upcoming_matches: pd.DataFrame, previous_matches: pd.DataFrame) -> None:
    st.markdown("<div class='panel-title'>Live Match Snapshot</div>", unsafe_allow_html=True)
    if not live_matches.empty:
        st.markdown(compact_match_card(live_matches.iloc[0], "LIVE"), unsafe_allow_html=True)
    elif not upcoming_matches.empty:
        st.markdown(compact_match_card(upcoming_matches.iloc[0], "NEXT KICKOFF"), unsafe_allow_html=True)
    else:
        st.caption("No live or upcoming fixture is available in the selected window.")

    if not previous_matches.empty:
        st.markdown(compact_match_card(previous_matches.iloc[0], "LATEST RESULT"), unsafe_allow_html=True)

    if st.button("Open Match Centre", key="hub_open_match_centre"):
        st.session_state["pending_nav_view"] = "Match Centre"
        st.rerun()
    st.markdown("<div class='panel-bottom-fill'></div>", unsafe_allow_html=True)


def render_formation_preview(live_matches: pd.DataFrame) -> None:
    st.markdown("<div class='panel-title'>Formation Preview</div>", unsafe_allow_html=True)
    if live_matches.empty:
        st.markdown(
            """
            <div class="match-snapshot-card formation-empty" style="background:#222833;">
                Formation preview appears here once a real live lineup is available.
            </div>
            """,
            unsafe_allow_html=True,
        )
        return
    st.markdown(
        """
        <div class="match-snapshot-card formation-empty" style="background:#222833;">
            Formation preview appears here when live lineup positions are returned.
        </div>
        """,
        unsafe_allow_html=True,
    )


def goals_to_events(match: pd.Series) -> pd.DataFrame:
    rows = []
    for goal in match.get("goals") or []:
        team = goal.get("team") or {}
        scorer = goal.get("scorer") or {}
        assist = goal.get("assist") or {}
        score = goal.get("score") or {}
        detail = f"{score.get('home', '')}-{score.get('away', '')}".strip("-")
        if assist.get("name"):
            detail = f"{detail} | Assist: {assist['name']}"
        rows.append(
            {
                "Minute": goal.get("minute") or "",
                "Team": team.get("name") or "",
                "Player": scorer.get("name") or "",
                "Type": goal.get("type") or "Goal",
                "Score": detail,
            }
        )
    return pd.DataFrame(rows)


def render_events(match: pd.Series) -> None:
    events = goals_to_events(match)
    st.markdown("<div class='panel-title'>Goal Events</div>", unsafe_allow_html=True)
    if events.empty:
        st.caption("No goal-event feed is available for this match yet.")
        return
    for _, event in events.iterrows():
        st.markdown(
            f"""
            <div class="event-row">
                <strong>{escape(str(event['Minute']))}'</strong>
                &nbsp; {escape(str(event['Type']))}
                &nbsp; <strong>{escape(str(event['Player']))}</strong>
                <div class="muted">{escape(str(event['Team']))} | {escape(str(event['Score']))}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_score_chart(matches: pd.DataFrame, key: str) -> None:
    if matches.empty:
        st.caption("No completed matches to chart.")
        return
    chart_data = matches.head(12).copy()
    chart_data["fixture"] = chart_data["home_team"] + " vs " + chart_data["away_team"]
    chart_data["total_goals"] = chart_data["home_goals"] + chart_data["away_goals"]
    fig = px.bar(
        chart_data.sort_values("kickoff"),
        x="fixture",
        y="total_goals",
        color="competition",
        title="Goals In Recent Completed Matches",
    )
    st.plotly_chart(plotly_layout(fig, 360), width="stretch", key=key)


def match_stage_label(match: pd.Series) -> str:
    group = str(match.get("group") or "").replace("_", " ").title()
    stage = str(match.get("stage") or "").replace("_", " ").title()
    return group or stage or "World Cup"


def console_crest(url: object) -> str:
    if not isinstance(url, str) or not url:
        return ""
    return f"<img class='match-console-crest' src='{escape(url, quote=True)}' alt='' />"


def ensure_lineup(value: object) -> list[dict[str, object]]:
    if isinstance(value, list):
        return [player for player in value if isinstance(player, dict)]
    return []


def player_position(player: dict[str, object]) -> str:
    position = str(player.get("position") or "").lower()
    if "keeper" in position:
        return "Goalkeeper"
    if "defend" in position:
        return "Defender"
    if "attack" in position or "forward" in position:
        return "Attacker"
    return "Midfielder"


def infer_formation(lineup: list[dict[str, object]]) -> str:
    if not lineup:
        return "-"
    defenders = sum(1 for player in lineup if player_position(player) == "Defender")
    midfielders = sum(1 for player in lineup if player_position(player) == "Midfielder")
    attackers = sum(1 for player in lineup if player_position(player) == "Attacker")
    if defenders + midfielders + attackers == 0:
        return "-"
    return f"{defenders}-{midfielders}-{attackers}"


def compact_player_name(name: object) -> str:
    parts = str(name or "Player").split()
    if not parts:
        return "Player"
    return parts[0] if len(parts[0]) <= 9 else parts[0][:9]


def spread_y(count: int) -> list[float]:
    if count <= 1:
        return [50]
    top = 18
    bottom = 82
    step = (bottom - top) / (count - 1)
    return [top + step * index for index in range(count)]


def formation_points(lineup: list[dict[str, object]], side: str) -> list[str]:
    if not lineup:
        return []
    columns = {
        "Goalkeeper": 7 if side == "home" else 93,
        "Defender": 22 if side == "home" else 78,
        "Midfielder": 42 if side == "home" else 58,
        "Attacker": 58 if side == "home" else 42,
    }
    grouped: dict[str, list[dict[str, object]]] = {
        "Goalkeeper": [],
        "Defender": [],
        "Midfielder": [],
        "Attacker": [],
    }
    for player in lineup:
        grouped[player_position(player)].append(player)

    html_parts: list[str] = []
    for position, players in grouped.items():
        players = sorted(players, key=lambda item: safe_int(item.get("shirtNumber"), 99))
        for player, y in zip(players, spread_y(len(players))):
            shirt = safe_int(player.get("shirtNumber"), 0)
            label = compact_player_name(player.get("name"))
            x = columns[position]
            html_parts.append(
                f"<div class='pitch-dot {side}' style='left:{x}%;top:{y}%;'>{shirt or ''}</div>"
                f"<div class='pitch-label {side}' style='left:{x}%;top:{y}%;'>{escape(label)}</div>"
            )
    return html_parts


def render_match_console_card(match: pd.Series) -> None:
    home_formation = infer_formation(ensure_lineup(match.get("home_lineup")))
    away_formation = infer_formation(ensure_lineup(match.get("away_lineup")))
    status = str(match.get("status") or "")
    minute = safe_int(match.get("minute"))
    minute_badge = f"<span class='pill pill-gray'>{minute}'</span>" if minute else ""
    venue_line = " | ".join(
        part for part in [match_stage_label(match), str(match.get("venue") or "")] if part
    )

    st.html(
        f"""
        <div class="match-console-card">
            <div class="match-console-team">
                <div class="match-console-name">{console_crest(match.get('home_crest'))}{escape(str(match['home_team']))}</div>
                <div class="muted" style="margin-top:.55rem;">{escape(home_formation)}</div>
            </div>
            <div class="match-console-score">{safe_int(match['home_goals'])} - {safe_int(match['away_goals'])}</div>
            <div class="match-console-team away">
                <div class="match-console-name">{escape(str(match['away_team']))}{console_crest(match.get('away_crest'))}</div>
                <div class="muted" style="margin-top:.55rem;">{escape(away_formation)}</div>
            </div>
            <div class="match-console-meta">
                <div>{badge(status)} {minute_badge}</div>
                <div style="margin-top:1.25rem;">{escape(venue_line)}</div>
            </div>
        </div>
        """
    )


def render_formation_pitch(match: pd.Series) -> None:
    home_lineup = ensure_lineup(match.get("home_lineup"))
    away_lineup = ensure_lineup(match.get("away_lineup"))
    home_formation = infer_formation(home_lineup)
    away_formation = infer_formation(away_lineup)

    st.markdown("<div class='panel-title'>Formation</div>", unsafe_allow_html=True)
    if not home_lineup and not away_lineup:
        st.html(
            """
            <div class="pitch">
                <div class="pitch-box left"></div>
                <div class="pitch-box right"></div>
                <div style="position:absolute;inset:0;display:grid;place-items:center;color:#8f99ad;font-weight:800;z-index:3;">
                    Lineup data is not available for this match yet.
                </div>
            </div>
            """
        )
        return

    st.markdown(
        f"<div class='formation-note'>{escape(str(match['home_team']))} {escape(home_formation)} vs "
        f"{escape(str(match['away_team']))} {escape(away_formation)}</div>",
        unsafe_allow_html=True,
    )
    player_html = "".join(formation_points(home_lineup, "home") + formation_points(away_lineup, "away"))
    st.html(
        f"""
        <div class="pitch">
            <div class="pitch-box left"></div>
            <div class="pitch-box right"></div>
            {player_html}
        </div>
        """
    )


def goal_side(goal: dict[str, object], match: pd.Series) -> str:
    team = goal.get("team") or {}
    team_id = team.get("id") if isinstance(team, dict) else None
    team_name = str(team.get("name") or "") if isinstance(team, dict) else ""
    if team_id and str(team_id) == str(match.get("home_team_id")):
        return "home"
    if team_id and str(team_id) == str(match.get("away_team_id")):
        return "away"
    home_names = {str(match.get("home_team")), str(match.get("home_team_full"))}
    return "home" if team_name in home_names else "away"


def timeline_events(match: pd.Series) -> list[dict[str, str]]:
    events: list[dict[str, str]] = []
    goals = [goal for goal in (match.get("goals") or []) if isinstance(goal, dict)]
    bookings = [booking for booking in (match.get("bookings") or []) if isinstance(booking, dict)]
    substitutions = [sub for sub in (match.get("substitutions") or []) if isinstance(sub, dict)]

    home_score = 0
    away_score = 0
    for goal in sorted(goals, key=lambda item: safe_int(item.get("minute"), 0)):
        side = goal_side(goal, match)
        if side == "home":
            home_score += 1
        else:
            away_score += 1
        scorer = goal.get("scorer") or {}
        player_name = scorer.get("name") if isinstance(scorer, dict) else "Goal"
        team_label = match.get("home_team") if side == "home" else match.get("away_team")
        events.append(
            {
                "minute": f"{safe_int(goal.get('minute'))}'",
                "icon": "G",
                "title": str(player_name or "Goal"),
                "detail": f"{team_label} {home_score}-{away_score}",
                "sort": str(safe_int(goal.get("minute"))).zfill(3),
            }
        )

    for booking in bookings:
        player = booking.get("player") or {}
        team = booking.get("team") or {}
        player_name = player.get("name") if isinstance(player, dict) else "Booking"
        team_name = team.get("name") if isinstance(team, dict) else ""
        events.append(
            {
                "minute": f"{safe_int(booking.get('minute'))}'",
                "icon": "Y",
                "title": str(player_name or "Booking"),
                "detail": f"{team_name} {booking.get('card') or 'Card'}".strip(),
                "sort": str(safe_int(booking.get("minute"))).zfill(3),
            }
        )

    for sub in substitutions:
        player_in = sub.get("playerIn") or {}
        player_out = sub.get("playerOut") or {}
        in_name = player_in.get("name") if isinstance(player_in, dict) else "Player in"
        out_name = player_out.get("name") if isinstance(player_out, dict) else "Player out"
        events.append(
            {
                "minute": f"{safe_int(sub.get('minute'))}'",
                "icon": "S",
                "title": str(in_name or "Substitution"),
                "detail": f"On for {out_name}",
                "sort": str(safe_int(sub.get("minute"))).zfill(3),
            }
        )

    if str(match.get("status")) == "Live":
        minute = safe_int(match.get("minute"))
        events.append(
            {
                "minute": f"{minute}'" if minute else "Live",
                "icon": "L",
                "title": "Live",
                "detail": "Match is currently in progress",
                "sort": str(minute or 999).zfill(3),
            }
        )

    return sorted(events, key=lambda item: item["sort"])


def render_events_timeline(match: pd.Series) -> None:
    st.markdown("<div class='panel-title'>Events Timeline</div>", unsafe_allow_html=True)
    events = timeline_events(match)
    if not events:
        st.caption("No event timeline is available for this match yet.")
        return
    rows = []
    for event in events:
        rows.append(
            "<div class='timeline-item'>"
            f"<div class='timeline-icon'>{escape(event['icon'])}</div>"
            f"<span class='timeline-minute'>{escape(event['minute'])}</span>"
            f"<span class='timeline-title'>{escape(event['title'])}</span>"
            f"<div class='muted' style='margin-top:.45rem;'>{escape(event['detail'])}</div>"
            "</div>"
        )
    st.html(f"<div class='timeline'>{''.join(rows)}</div>")


def render_tournament_hub(data: dict[str, pd.DataFrame | str], competition_label: str) -> None:
    all_matches = data["all_matches"]
    live_matches = data["live_matches"]
    previous_matches = data["previous_matches"]
    upcoming_matches = data["upcoming_matches"]
    standings = data["standings"]
    scorers = data["scorers"]
    metrics = build_metrics(all_matches, live_matches, previous_matches)

    render_hub_heading(all_matches)
    render_hub_kpis(metrics)

    left, right = st.columns([1.35, 1])
    with left:
        with st.container(border=True):
            st.markdown("<span class='hub-panel-marker hub-panel-top'></span>", unsafe_allow_html=True)
            render_match_list(upcoming_matches, "Upcoming Matches", 5)
    with right:
        with st.container(border=True):
            st.markdown("<span class='hub-panel-marker hub-panel-top'></span>", unsafe_allow_html=True)
            render_standings_panel(standings, previous_matches, all_matches)

    bottom_left, bottom_middle, bottom_right = st.columns([1, 1, 1])
    with bottom_left:
        with st.container(border=True):
            st.markdown("<span class='hub-panel-marker hub-panel-bottom'></span>", unsafe_allow_html=True)
            render_top_scorers_panel(scorers)
    with bottom_middle:
        with st.container(border=True):
            st.markdown("<span class='hub-panel-marker hub-panel-bottom'></span>", unsafe_allow_html=True)
            render_live_snapshot(live_matches, upcoming_matches, previous_matches)
    with bottom_right:
        with st.container(border=True):
            st.markdown("<span class='hub-panel-marker hub-panel-bottom'></span>", unsafe_allow_html=True)
            render_formation_preview(live_matches)


def render_match_centre(data: dict[str, pd.DataFrame | str], api_key: str) -> None:
    render_header("Match Centre", "Inspect live, upcoming, and completed World Cup fixtures.")
    matches = data["all_matches"]
    if matches.empty:
        render_empty_state("No matches", "The API returned no fixtures for the selected window.")
        return
    status_order = {"Live": 0, "Upcoming": 1, "Finished": 2}
    ordered_matches = matches.copy()
    ordered_matches["status_order"] = ordered_matches["status"].map(status_order).fillna(9)
    ordered_matches = ordered_matches.sort_values(["status_order", "kickoff"], ascending=[True, True])
    labels = {
        row["match_id"]: f"{row['home_team']} vs {row['away_team']} | {row['status']} | {local_time(row['kickoff'])}"
        for _, row in ordered_matches.iterrows()
    }
    match_id = st.selectbox("Choose match", list(labels.keys()), format_func=lambda value: labels[value])
    selected = matches[matches["match_id"] == match_id].iloc[0]

    try:
        selected = load_match_detail(api_key, str(match_id))
    except FootballDataError:
        st.caption("Detailed match feed is not available yet, showing fixture data.")

    render_match_console_card(selected)

    left, right = st.columns([1.85, 0.9])
    with left:
        with st.container(border=True):
            render_formation_pitch(selected)
    with right:
        with st.container(border=True):
            render_events_timeline(selected)


def render_previous_matches(data: dict[str, pd.DataFrame | str]) -> None:
    render_header("Previous Matches", "Replay completed results with scoreline and goal-event details.")
    previous_matches = data["previous_matches"]
    if previous_matches.empty:
        render_empty_state("No previous matches", "No completed fixtures are available for this competition/date window.")
        return
    labels = {
        row["match_id"]: (
            f"{row['home_team']} {safe_int(row['home_goals'])}-{safe_int(row['away_goals'])} "
            f"{row['away_team']} | {local_time(row['kickoff'])}"
        )
        for _, row in previous_matches.iterrows()
    }
    match_id = st.selectbox("Replay match", list(labels.keys()), format_func=lambda value: labels[value])
    selected = previous_matches[previous_matches["match_id"] == match_id].iloc[0]
    render_score_card(selected)

    left, right = st.columns([1, 1])
    with left:
        render_events(selected)
    with right:
        comparison = pd.DataFrame(
            {
                "Team": [selected["home_team"], selected["away_team"]],
                "Goals": [selected["home_goals"], selected["away_goals"]],
            }
        )
        fig = px.bar(comparison, x="Team", y="Goals", color="Team", title="Final Score")
        st.plotly_chart(plotly_layout(fig, 320), width="stretch", key=f"previous-{match_id}")

    st.dataframe(
        previous_matches[
            [
                "kickoff",
                "competition",
                "stage",
                "home_team",
                "home_goals",
                "away_goals",
                "away_team",
                "venue",
            ]
        ],
        width="stretch",
        hide_index=True,
    )


def render_team_deep_dive(data: dict[str, pd.DataFrame | str]) -> None:
    render_header("Team Deep Dive", "Analyze team form using live API match history and standings.")
    matches = data["all_matches"]
    previous_matches = data["previous_matches"]
    if matches.empty:
        render_empty_state("No team data", "No fixtures are available for the selected window.")
        return
    teams = sorted(set(matches["home_team"]).union(set(matches["away_team"])))
    selected_team = st.selectbox("Choose team", teams)
    team_matches = matches[(matches["home_team"] == selected_team) | (matches["away_team"] == selected_team)]
    team_results = previous_matches[
        (previous_matches["home_team"] == selected_team) | (previous_matches["away_team"] == selected_team)
    ]

    gf = 0
    ga = 0
    wins = draws = losses = 0
    for _, match in team_results.iterrows():
        if match["home_team"] == selected_team:
            team_goals = safe_int(match["home_goals"])
            opp_goals = safe_int(match["away_goals"])
        else:
            team_goals = safe_int(match["away_goals"])
            opp_goals = safe_int(match["home_goals"])
        gf += team_goals
        ga += opp_goals
        if team_goals > opp_goals:
            wins += 1
        elif team_goals < opp_goals:
            losses += 1
        else:
            draws += 1

    cols = st.columns(4)
    cols[0].metric("Team fixtures", len(team_matches))
    cols[1].metric("W-D-L", f"{wins}-{draws}-{losses}")
    cols[2].metric("Goals for", gf)
    cols[3].metric("Goal diff", gf - ga)

    left, right = st.columns([1, 1])
    with left:
        render_match_list(team_matches.sort_values("kickoff", ascending=False), f"{selected_team} Fixtures", 8)
    with right:
        if team_results.empty:
            st.caption("Completed team results are not available in this window.")
        else:
            trend = team_results.sort_values("kickoff").copy()
            trend["fixture"] = trend["home_team"] + " vs " + trend["away_team"]
            trend["team_goals"] = trend.apply(
                lambda row: row["home_goals"] if row["home_team"] == selected_team else row["away_goals"],
                axis=1,
            )
            trend["opponent_goals"] = trend.apply(
                lambda row: row["away_goals"] if row["home_team"] == selected_team else row["home_goals"],
                axis=1,
            )
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=trend["fixture"], y=trend["team_goals"], mode="lines+markers", name=selected_team))
            fig.add_trace(go.Scatter(x=trend["fixture"], y=trend["opponent_goals"], mode="lines+markers", name="Opponent"))
            fig.update_layout(title="Goal Trend")
            st.plotly_chart(plotly_layout(fig, 380), width="stretch", key="team-goal-trend")


def render_leaderboards(data: dict[str, pd.DataFrame | str]) -> None:
    render_header("Leaderboards", "Top scorers from FIFA World Cup 2026 when scorer records are available.")
    scorers = data["scorers"]
    previous_matches = data["previous_matches"]

    if isinstance(scorers, pd.DataFrame) and not scorers.empty:
        left, right = st.columns([1.4, 0.7])
        with left:
            fig = px.bar(
                scorers.sort_values("Goals"),
                x="Goals",
                y="Player",
                color="Goals",
                orientation="h",
                color_continuous_scale=["#00d084", "#ffd400"],
                title="Top Scorers",
            )
            st.plotly_chart(plotly_layout(fig, 540), width="stretch", key="scorers-chart")
        with right:
            st.markdown("<div class='panel-title'>Top 3 Podium</div>", unsafe_allow_html=True)
            for place, (_, row) in enumerate(scorers.head(3).iterrows(), start=1):
                st.markdown(
                    f"""
                    <div class="leader-card">
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <div>
                                <strong>#{place} {escape(str(row['Player']))}</strong>
                                <div class="muted">{escape(str(row['Team']))}</div>
                            </div>
                            <div class="big-number">{safe_int(row['Goals'])}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        st.dataframe(scorers, width="stretch", hide_index=True)
        return

    render_empty_state(
        "Scorers unavailable",
        "World Cup 2026 scorer records are not available for this key/window yet.",
    )
    render_score_chart(previous_matches, "leaderboard-goals-from-results")


apply_theme()

pending_nav_view = st.session_state.pop("pending_nav_view", None)
if pending_nav_view in NAV_ITEMS:
    st.session_state["nav_view"] = pending_nav_view

upcoming_days = DEFAULT_UPCOMING_DAYS
api_key = get_config_value("FOOTBALL_DATA_API_KEY") or get_config_value("FOOTBALL_API_KEY")

with st.sidebar:
    st.markdown(
        f"""
        <div class="sidebar-brand">
            <img src="{WORLD_CUP_LOGO_URL}" alt="FIFA World Cup 2026 logo" />
            <div>
                <div class="sidebar-brand-year">2026</div>
                <div class="sidebar-brand-title">FIFA World Cup</div>
                <div class="sidebar-brand-sub">Live Analytics</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.session_state.get("nav_view") not in NAV_ITEMS:
        st.session_state["nav_view"] = NAV_ITEMS[0]
    selected_view = st.radio("Navigation", NAV_ITEMS, label_visibility="collapsed", key="nav_view")

enable_auto_refresh()

if not api_key:
    render_header(WORLD_CUP_LABEL, "Add your API key to load live and previous World Cup matches.")
    st.info("Set FOOTBALL_DATA_API_KEY in your terminal or Streamlit secrets. No sample data is being displayed.")
    st.stop()

try:
    data = load_dashboard_data(
        api_key=api_key,
        today_text=date.today().isoformat(),
        upcoming_days=upcoming_days,
    )
except FootballDataError as exc:
    render_header("FIFA 2026 Live Analytics", "The live request could not be completed.")
    st.error("The request failed. Check that your API key has World Cup 2026 access, then reload the app.")
    st.stop()

render_ticker(data["all_matches"])

if selected_view == "Tournament Hub":
    render_tournament_hub(data, WORLD_CUP_LABEL)
elif selected_view == "Match Centre":
    render_match_centre(data, api_key)
elif selected_view == "Previous Matches":
    render_previous_matches(data)
elif selected_view == "Team Deep Dive":
    render_team_deep_dive(data)
else:
    render_leaderboards(data)
