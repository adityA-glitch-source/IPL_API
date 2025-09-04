# IPL_API
A REST API for IPL statistics built with Flask &amp; Pandas (2008–2022 dataset)
📌 Project Overview

IPL_API is a Flask-based REST API that serves cricket statistics from the Indian Premier League (IPL).
The dataset includes detailed match data such as teams, venues, winners, scores, man of the match awards, and player performances.

Using Pandas, data analysis functions were created to extract insights, and Flask was used to expose them as API endpoints.
Users can query endpoints to fetch structured results like team records, head-to-head stats, batting stats, and bowling stats.

⚡ Features / Endpoints

/teams → Returns all IPL teams.

/teamVsteam?team1=<teamA>&team2=<teamB> → Head-to-head record between two teams.

/team_record?team=<teamName> → Overall performance record of a team.

/batting_record?team=<teamName> → Batting statistics for a team/players.

/bowling_record?team=<teamName> → Bowling statistics for a team/players.

🛠️ Tech Stack

Python – Data analysis with Pandas

Flask – REST API framework

Dataset – All IPL matches (2008–2022)
