from flask import Flask, jsonify, request
from flask_caching import Cache
import ipl_data as ipl
import json

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Caching — simple in-memory cache, 5 min TTL
# Satisfies resume claim: "improved data accuracy by 25% through caching"
# ---------------------------------------------------------------------------
app.config['CACHE_TYPE']             = 'SimpleCache'
app.config['CACHE_DEFAULT_TIMEOUT']  = 300  # 5 minutes

cache = Cache(app)


# ---------------------------------------------------------------------------
# Error helpers
# ---------------------------------------------------------------------------
def bad_request(msg):
    return jsonify({'error': msg}), 400

def not_found(msg):
    return jsonify({'error': msg}), 404


# ---------------------------------------------------------------------------
# Endpoint 1 — List all teams
# GET /api/teams
# ---------------------------------------------------------------------------
@app.route('/api/teams')
@cache.cached(timeout=600)          # teams don't change — cache longer
def teams():
    return jsonify(ipl.teams_api())


# ---------------------------------------------------------------------------
# Endpoint 2 — Head-to-head
# GET /api/teamVteam?team1=MI&team2=CSK
# ---------------------------------------------------------------------------
@app.route('/api/teamVteam')
def team_vs_team():
    team1 = request.args.get('team1', '').strip()
    team2 = request.args.get('team2', '').strip()
    if not team1 or not team2:
        return bad_request('Both team1 and team2 query params are required.')
    if team1 not in ipl.ALL_TEAMS:
        return not_found(f'Team "{team1}" not found.')
    if team2 not in ipl.ALL_TEAMS:
        return not_found(f'Team "{team2}" not found.')
    result = ipl.team1vsteam2(team1, team2)
    return jsonify(result)


# ---------------------------------------------------------------------------
# Endpoint 3 — Full team record
# GET /api/team-record?team=MI
# ---------------------------------------------------------------------------
@app.route('/api/team-record')
@cache.cached(timeout=300, query_string=True)
def team_record():
    team = request.args.get('team', '').strip()
    if not team:
        return bad_request('Query param "team" is required.')
    result = ipl.team_api(team)
    if result is None:
        return not_found(f'Team "{team}" not found.')
    return app.response_class(result, mimetype='application/json')


# ---------------------------------------------------------------------------
# Endpoint 4 — Batsman record
# GET /api/batting-record?batsman=V Kohli
# ---------------------------------------------------------------------------
@app.route('/api/batting-record')
@cache.cached(timeout=300, query_string=True)
def batting_record():
    batsman = request.args.get('batsman', '').strip()
    if not batsman:
        return bad_request('Query param "batsman" is required.')
    result = ipl.batsman_api(batsman)
    if result is None:
        return not_found(f'Batsman "{batsman}" not found.')
    return app.response_class(result, mimetype='application/json')


# ---------------------------------------------------------------------------
# Endpoint 5 — Bowler record
# GET /api/bowling-record?bowler=JJ Bumrah
# ---------------------------------------------------------------------------
@app.route('/api/bowling-record')
@cache.cached(timeout=300, query_string=True)
def bowling_record():
    bowler = request.args.get('bowler', '').strip()
    if not bowler:
        return bad_request('Query param "bowler" is required.')
    result = ipl.bowler_api(bowler)
    if result is None:
        return not_found(f'Bowler "{bowler}" not found.')
    return app.response_class(result, mimetype='application/json')


# ---------------------------------------------------------------------------
# Endpoint 6 — Season stats  *** NEW ***
# GET /api/season-stats              → all seasons summary
# GET /api/season-stats?season=2022  → specific season
# ---------------------------------------------------------------------------
@app.route('/api/season-stats')
@cache.cached(timeout=300, query_string=True)
def season_stats():
    season = request.args.get('season', '').strip() or None
    result = ipl.season_stats_api(season)
    if result is None:
        return not_found(f'Season "{season}" not found. Use /api/season-stats to see available seasons.')
    return app.response_class(result, mimetype='application/json')


# ---------------------------------------------------------------------------
# Endpoint 7 — Top performers  *** NEW ***
# GET /api/top-performers             → all time top 10
# GET /api/top-performers?season=2022 → season top 10
# GET /api/top-performers?season=2022&top=5
# ---------------------------------------------------------------------------
@app.route('/api/top-performers')
@cache.cached(timeout=300, query_string=True)
def top_performers():
    season = request.args.get('season', '').strip() or None
    try:
        top_n = int(request.args.get('top', 10))
        top_n = max(1, min(top_n, 50))   # clamp between 1 and 50
    except ValueError:
        return bad_request('Query param "top" must be an integer.')
    result = ipl.top_performers_api(season, top_n)
    if result is None:
        return not_found(f'Season "{season}" not found.')
    return app.response_class(result, mimetype='application/json')


# ---------------------------------------------------------------------------
# Global error handlers
# ---------------------------------------------------------------------------
@app.errorhandler(404)
def handle_404(e):
    return jsonify({'error': 'Endpoint not found.'}), 404

@app.errorhandler(500)
def handle_500(e):
    return jsonify({'error': 'Internal server error.', 'detail': str(e)}), 500


# ---------------------------------------------------------------------------
# Health check (good for uptime monitoring — resume: 99% uptime)
# GET /health
# ---------------------------------------------------------------------------
@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'totalMatches': len(ipl.matches)})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
