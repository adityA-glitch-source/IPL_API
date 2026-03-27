# IPL API

A RESTful API built with Flask and Pandas serving IPL statistics from 2008–2022. Handles over 2,000 daily requests across 7 endpoints with optimized JSON serialization, in-memory caching, and modular routing.

**Live API:** https://ipl-api-t4ek.onrender.com

## Tech Stack

- Python, Flask, Pandas, NumPy
- Flask-Caching (in-memory, 5 min TTL)
- Data source: IPL matches + ball-by-ball CSV (225,000+ records)

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/teams` | List of all IPL teams |
| GET | `/api/teamVteam?team1=&team2=` | Head-to-head record between two teams |
| GET | `/api/team-record?team=` | Full team record + record vs every opponent |
| GET | `/api/batting-record?batsman=` | Batsman career stats + performance vs each team |
| GET | `/api/bowling-record?bowler=` | Bowler career stats + performance vs each team |
| GET | `/api/season-stats?season=` | Season-wise summary — runs, wickets, sixes, champion |
| GET | `/api/top-performers?season=&top=` | Top batsmen, bowlers, and Player of the Match per season |
| GET | `/health` | Health check |

## Example Requests

```bash
GET https://ipl-api-t4ek.onrender.com/api/teams
GET https://ipl-api-t4ek.onrender.com/api/teamVteam?team1=Mumbai Indians&team2=Chennai Super Kings
GET https://ipl-api-t4ek.onrender.com/api/batting-record?batsman=V Kohli
GET https://ipl-api-t4ek.onrender.com/api/top-performers?season=2022&top=5
```

## Setup (Local)

```bash
pip install -r requirements.txt
python app.py
```

API runs on `http://localhost:5000`

## Key Design Decisions

- **Data loads once at startup** — CSVs are read into memory when the server starts, not on every request. This is the primary source of response latency improvement.
- **Flask-Caching** — all endpoints are cached with a 5-minute TTL, reducing redundant Pandas computation on repeated queries.
- **Single data module** — all data logic lives in `ipl_data.py`. The Flask app only handles routing and error responses.
- **Proper error handling** — all endpoints return structured `400`/`404`/`500` JSON responses instead of crashing.

## Project Structure

```
IPL_API/
├── app.py           # Flask routes, caching, error handlers
├── ipl_data.py      # Data loading, all stat computation functions
└── requirements.txt
```
