# FIFA World Cup 2026 Live Analytics

A Streamlit dashboard for FIFA World Cup 2026 match monitoring and analytics
using the football-data.org API.

## Features

- FIFA World Cup 2026 tournament navigation
- Live, upcoming, finished, and previous-match replay views
- Scoreline, match status, kickoff time, competition, stage, and venue
- Dashboard KPIs for loaded matches, live matches, previous results, and goals
- Previous match replay with final score and goal-event details when available
- Team deep dives using API match history
- Leaderboards using football-data.org competition scorers when available
- Previous match comparison and event timeline when the API includes goal data
- API key support through environment variables or Streamlit secrets
- Automatic 2-minute dashboard refresh
- Clean project structure for a data analyst or data scientist portfolio

## Project Structure

```text
.
├── app.py
├── src/
│   ├── __init__.py
│   └── football_data.py
├── .env.example
├── requirements.txt
└── README.md
```

## Run Locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Live Scores Setup

The live connector is built for football-data.org. Create an API key, then
expose it as an environment variable before running Streamlit:

```bash
export FOOTBALL_DATA_API_KEY="your_football_data_org_key_here"
streamlit run app.py
```

The dashboard requests football-data.org competition `WC` with `season=2026`.
It does not display sample data. If the key is missing or an API request fails,
the app shows an instruction/error state instead of fake results.

For Streamlit Cloud, add this secret instead:

```toml
FOOTBALL_DATA_API_KEY = "your_football_data_org_key_here"
```

## GitHub Publishing

Create an empty repository on GitHub named `fifa-match-analytics-dashboard`,
then run:

```bash
git init
git add .
git commit -m "Initial FIFA match analytics dashboard"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/fifa-match-analytics-dashboard.git
git push -u origin main
```

## Next Improvements

- Add a richer historical match dataset
- Connect richer player statistics from a paid sports data API
- Train a real scikit-learn winner prediction model
- Add downloadable CSV exports and model feature importance
