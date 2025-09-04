from flask import Flask,jsonify,request

import ico
import ipl
app = Flask(__name__)
@app.route('/')
def home():
    return 'Hello World!'
@app.route('/api/teams')
def teams():
    teams = ipl.teams_api()
    return jsonify(teams)
@app.route('/api/teamVteam')
def teamVteam():
    team1 = request.args.get('team1')
    team2 = request.args.get('team2')
    response = ipl.teamVsteam_api(team1,team2)
    return  jsonify(response)
@app.route('/api/team-record')
def team_record():
    team_name = request.args.get('team')
    response = ico.teamAPI(team_name)
    return response
@app.route('/api/batting-record')
def batting_record():
    batsman_name = request.args.get('batsman')
    response = ico.batsmanAPI(batsman_name)
    return response
@app.route('/api/bowling-record')
def bowling_record():
    bowler_name = request.args.get('bowler')
    response = ico.bowlerAPI(bowler_name)
    return response


if __name__ == '__main__':
    app.run(debug=True)