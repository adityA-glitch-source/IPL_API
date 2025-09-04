import numpy as np
import pandas as pd
ipl_matches = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRy2DUdUbaKx_Co9F0FSnIlyS-8kp4aKv_I0-qzNeghiZHAI_hw94gKG22XTxNJHMFnFVKsO4xWOdIs/pub?gid=1655759976&single=true&output=csv"
matches = pd.read_csv(ipl_matches)

def teams_api():
    teams = list(set(list(matches['Team1']) + list(matches['Team2'])))
    dict_teams = {
                    'teams':teams

                  }
    return dict_teams
def teamVsteam_api(team1, team2):
    valid_teams = list(set(list(matches['Team1']) + list(matches['Team2'])))
    if team1 in valid_teams and team2 in valid_teams:
        teamdf = matches[(matches['Team1'] == team1) & (matches['Team2'] == team2) | (matches['Team1'] == team2) & (matches['Team2'] == team1)]
        total_matches = teamdf.shape[0]

        matches_won_team1 = teamdf['WinningTeam'].value_counts()[team1]
        matches_won_team2 = teamdf['WinningTeam'].value_counts()[team2]

        draws = total_matches - (matches_won_team1 + matches_won_team2)

        response = {
            'total_matches': str(total_matches),
             team1: str(matches_won_team1),
             team2: str(matches_won_team2),
            'draws': str(draws)
        }
        return response
    else:
           {'message': 'Invalid team'}



