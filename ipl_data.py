import pandas as pd
import numpy as np
import json

# ---------------------------------------------------------------------------
# JSON encoder — handles numpy types cleanly
# ---------------------------------------------------------------------------
class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


# ---------------------------------------------------------------------------
# Data loading — runs ONCE at startup, not on every request
# ---------------------------------------------------------------------------
_MATCHES_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vRy2DUdUbaKx_Co9F0FSnIlyS-8kp4aKv_I0-qzNeghiZHAI_hw94gKG22XTxNJHMFnFVKsO4xWOdIs"
    "/pub?gid=1655759976&single=true&output=csv"
)
_BALLS_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vRu6cb6Pj8C9elJc5ubswjVTObommsITlNsFy5X0EiBY7S-lsHEUqx3g_M16r50Ytjc0XQCdGDyzE_Y"
    "/pub?output=csv"
)

matches = pd.read_csv(_MATCHES_URL)
balls   = pd.read_csv(_BALLS_URL)

# Build merged ball-level frame with bowling team derived
ball_withmatch = balls.merge(matches, on='ID', how='inner').copy()
ball_withmatch['BowlingTeam'] = (
    ball_withmatch['Team1'] + ball_withmatch['Team2']
)
ball_withmatch['BowlingTeam'] = ball_withmatch[['BowlingTeam', 'BattingTeam']].apply(
    lambda x: x.values[0].replace(x.values[1], ''), axis=1
)

batter_data = ball_withmatch[
    np.append(balls.columns.values, ['BowlingTeam', 'Player_of_Match'])
].copy()

bowler_data = batter_data.copy()

_WICKET_KINDS = {'caught', 'caught and bowled', 'bowled', 'stumped', 'lbw', 'hit wicket'}

def _bowler_run(row):
    if row['extra_type'] in ('penalty', 'legbyes', 'byes'):
        return 0
    return row['total_run']

def _is_bowler_wicket(row):
    if row['kind'] in _WICKET_KINDS:
        return row['isWicketDelivery']
    return 0

bowler_data['bowler_run']       = bowler_data.apply(_bowler_run, axis=1)
bowler_data['isBowlerWicket']   = bowler_data.apply(_is_bowler_wicket, axis=1)

ALL_TEAMS = sorted(matches['Team1'].unique().tolist())


# ---------------------------------------------------------------------------
# Teams
# ---------------------------------------------------------------------------
def teams_api():
    return {'teams': ALL_TEAMS}


# ---------------------------------------------------------------------------
# Head-to-head
# ---------------------------------------------------------------------------
def team1vsteam2(team1, team2):
    mask = (
        ((matches['Team1'] == team1) & (matches['Team2'] == team2)) |
        ((matches['Team1'] == team2) & (matches['Team2'] == team1))
    )
    df = matches[mask]
    mp   = len(df)
    won  = int((df['WinningTeam'] == team1).sum())
    nr   = int(df['WinningTeam'].isna().sum())
    loss = mp - won - nr
    return {
        'matchesPlayed': mp,
        'won':   won,
        'loss':  loss,
        'noResult': nr,
    }


# ---------------------------------------------------------------------------
# Team overall record
# ---------------------------------------------------------------------------
def _all_record(team):
    df  = matches[(matches['Team1'] == team) | (matches['Team2'] == team)]
    mp  = len(df)
    won = int((df['WinningTeam'] == team).sum())
    nr  = int(df['WinningTeam'].isna().sum())
    loss = mp - won - nr
    titles = int(((df['MatchNumber'] == 'Final') & (df['WinningTeam'] == team)).sum())
    return {'matchesPlayed': mp, 'won': won, 'loss': loss, 'noResult': nr, 'titles': titles}

def team_api(team):
    if team not in ALL_TEAMS:
        return None
    overall = _all_record(team)
    against = {t: team1vsteam2(team, t) for t in ALL_TEAMS if t != team}
    return json.dumps({team: {'overall': overall, 'against': against}}, cls=NpEncoder)


# ---------------------------------------------------------------------------
# Batsman
# ---------------------------------------------------------------------------
def _batsman_record(batsman, df):
    if df.empty:
        return {}
    out    = int((df['player_out'] == batsman).sum())
    df_bat = df[df['batter'] == batsman]
    inngs  = int(df_bat['ID'].nunique())
    runs   = int(df_bat['batsman_run'].sum())
    fours  = int(((df_bat['batsman_run'] == 4) & (df_bat['non_boundary'] == 0)).sum())
    sixes  = int(((df_bat['batsman_run'] == 6) & (df_bat['non_boundary'] == 0)).sum())
    avg    = float(runs / out) if out else float('inf')
    nballs = int((~(df_bat['extra_type'] == 'wides')).sum())
    sr     = float(runs / nballs * 100) if nballs else 0.0
    gb     = df_bat.groupby('ID')['batsman_run'].sum()
    fifties  = int(((gb >= 50) & (gb < 100)).sum())
    hundreds = int((gb >= 100).sum())
    not_out  = inngs - out
    mom      = int(df_bat[df_bat['Player_of_Match'] == batsman].drop_duplicates('ID').shape[0])
    try:
        hs_val = gb.sort_values(ascending=False).iloc[0]
        hs_id  = gb.sort_values(ascending=False).index[0]
        hs = str(hs_val) if (df_bat[df_bat['ID'] == hs_id]['player_out'] == batsman).any() else str(hs_val) + '*'
    except Exception:
        hs = str(gb.max()) if not gb.empty else '0'
    return {
        'innings': inngs, 'runs': runs, 'fours': fours, 'sixes': sixes,
        'average': avg, 'strikeRate': sr, 'fifties': fifties,
        'hundreds': hundreds, 'highestScore': hs, 'notOut': not_out, 'mom': mom,
    }

def batsman_api(batsman):
    df = batter_data[batter_data['innings'].isin([1, 2])]
    overall = _batsman_record(batsman, df)
    if not overall:
        return None
    against = {t: _batsman_record(batsman, df[df['BowlingTeam'] == t]) for t in ALL_TEAMS}
    return json.dumps({batsman: {'all': overall, 'against': against}}, cls=NpEncoder)


# ---------------------------------------------------------------------------
# Bowler
# ---------------------------------------------------------------------------
def _bowler_record(bowler, df):
    df = df[df['bowler'] == bowler]
    if df.empty:
        return {}
    inngs   = int(df['ID'].nunique())
    nballs  = int((~df['extra_type'].isin(['wides', 'noballs'])).sum())
    runs    = int(df['bowler_run'].sum())
    eco     = float(runs / nballs * 6) if nballs else 0.0
    fours   = int(((df['batsman_run'] == 4) & (df['non_boundary'] == 0)).sum())
    sixes   = int(((df['batsman_run'] == 6) & (df['non_boundary'] == 0)).sum())
    wickets = int(df['isBowlerWicket'].sum())
    avg     = float(runs / wickets) if wickets else float('inf')
    sr      = float(nballs / wickets * 100) if wickets else float('nan')
    gb      = df.groupby('ID')[['isBowlerWicket', 'bowler_run']].sum()
    w3      = int((gb['isBowlerWicket'] >= 3).sum())
    mom     = int(df[df['Player_of_Match'] == bowler].drop_duplicates('ID').shape[0])
    best_row = gb.sort_values(['isBowlerWicket', 'bowler_run'], ascending=[False, True]).head(1)
    best_fig = f"{int(best_row['isBowlerWicket'].values[0])}/{int(best_row['bowler_run'].values[0])}" if not best_row.empty else 'N/A'
    return {
        'innings': inngs, 'wickets': wickets, 'economy': eco,
        'average': avg, 'strikeRate': sr, 'fours': fours, 'sixes': sixes,
        'bestFigure': best_fig, '3+W': w3, 'mom': mom,
    }

def bowler_api(bowler):
    df = bowler_data[bowler_data['innings'].isin([1, 2])]
    overall = _bowler_record(bowler, df)
    if not overall:
        return None
    against = {t: _bowler_record(bowler, df[df['BattingTeam'] == t]) for t in ALL_TEAMS}
    return json.dumps({bowler: {'all': overall, 'against': against}}, cls=NpEncoder)


# ---------------------------------------------------------------------------
# NEW: Season stats
# ---------------------------------------------------------------------------
def season_stats_api(season=None):
    seasons = sorted(matches['Season'].unique().tolist())
    if season and str(season) not in seasons:
        return None

    df = matches if not season else matches[matches['Season'] == str(season)]

    # Merge with ball data for run/wicket aggregates
    bwm = ball_withmatch[ball_withmatch['ID'].isin(df['ID'])]
    bwm_bowl = bowler_data[bowler_data['ID'].isin(df['ID'])]

    total_runs    = int(bwm['total_run'].sum())
    total_wickets = int(bwm_bowl['isBowlerWicket'].sum())
    total_matches = len(df)
    total_sixes   = int(((bwm['batsman_run'] == 6) & (bwm['non_boundary'] == 0)).sum())
    total_fours   = int(((bwm['batsman_run'] == 4) & (bwm['non_boundary'] == 0)).sum())

    # Season winners (finals only)
    finals = df[df['MatchNumber'] == 'Final'][['Season', 'WinningTeam']]
    champions = {str(row['Season']): row['WinningTeam'] for _, row in finals.iterrows()}

    result = {
        'season': season if season else 'all',
        'totalMatches': total_matches,
        'totalRuns': total_runs,
        'totalWickets': total_wickets,
        'totalSixes': total_sixes,
        'totalFours': total_fours,
        'champions': champions,
        'availableSeasons': seasons,
    }
    return json.dumps(result, cls=NpEncoder)


# ---------------------------------------------------------------------------
# NEW: Top performers
# ---------------------------------------------------------------------------
def top_performers_api(season=None, top_n=10):
    seasons = sorted(matches['Season'].unique().tolist())
    if season and str(season) not in seasons:
        return None

    match_ids = matches['ID'] if not season else matches[matches['Season'] == str(season)]['ID']

    # Batting
    bat_df = batter_data[batter_data['ID'].isin(match_ids) & batter_data['innings'].isin([1, 2])]
    top_bat = (
        bat_df.groupby('batter')['batsman_run'].sum()
        .sort_values(ascending=False).head(top_n)
    )
    top_batsmen = [{'name': k, 'runs': int(v)} for k, v in top_bat.items()]

    # Bowling
    bowl_df = bowler_data[bowler_data['ID'].isin(match_ids) & bowler_data['innings'].isin([1, 2])]
    top_bowl = (
        bowl_df.groupby('bowler')['isBowlerWicket'].sum()
        .sort_values(ascending=False).head(top_n)
    )
    top_bowlers = [{'name': k, 'wickets': int(v)} for k, v in top_bowl.items()]

    # Most MOM
    mom_df = matches[matches['ID'].isin(match_ids)]
    top_mom = (
        mom_df['Player_of_Match'].value_counts().head(top_n)
    )
    top_mom_list = [{'name': k, 'awards': int(v)} for k, v in top_mom.items()]

    result = {
        'season': season if season else 'all',
        'topBatsmen': top_batsmen,
        'topBowlers': top_bowlers,
        'topPlayerOfMatch': top_mom_list,
    }
    return json.dumps(result, cls=NpEncoder)
