# Load Packages
import os
#from IPython.core.display import HTML
#import xlrd as xl
import numpy as np
import pandas as pd
import requests
import json
from io import StringIO
import numpy as np
import requests
#from bs4 import BeautifulSoup
from datetime import datetime

def get_rankings():
    year = datetime.now().year  # Adjust to current or desired season (e.g., 2024 for past data)
    api_key = os.environ.get('CFBD_API_KEY', 'G7EL3wSl1uoDYSQOw1aVQ+yKey9MG1nYqP3pLaW+sPKAzo/NiGJiKLi5fHo38xXa')  # Fallback to hardcoded if not set
    response = requests.get(
        "https://api.collegefootballdata.com/games",
        params={"year": year, "seasonType": "both"},
        headers={"Authorization": f"Bearer {api_key}"}
    )
    data = pd.read_json(StringIO(response.text))
    

    # only include games that have already been played
    data = data[
        (data['homePoints'] == data['homePoints'])
        & (data['awayPoints'] == data['awayPoints'])
        & (pd.notna(data['homeConference']))
        & (pd.notna(data['awayConference']))
    ]

    #create copy for dataset with all teams
    data2 = data
    # only include teams in division one FBS
    data = data[data['homeClassification']== 'fbs']
    # create spread variable
    data['homeSpread'] = data['homePoints'] - data['awayPoints']
    data['awaySpread'] = -data['homeSpread']
    

    # change postseason games from week 1 to week 15
    data['week'] = np.where(data['seasonType'] == 'postseason',15, data['week'])

    # subtract 2.5 points from the home teams spread, keep neutral as is, and add 2.5 to away teams.
    data['homeSpread_adj'] = np.where(data['neutralSite'] == True, data['homeSpread'], (data['homeSpread'] - 2.5))
    data['awaySpread_adj'] = -data['homeSpread_adj']


    # convert each game into two rows, one for each team and remove unwated rows.
    teams = pd.concat([
        data[['homeTeam', 'homeSpread', 'homeSpread_adj', 'awayTeam', ]].rename(columns={'homeTeam': 'team', 'homeSpread': 'spread',  'awayTeam': 'opponent', 'homeSpread_adj' : 'adj_spread'}),
        data[['awayTeam', 'awaySpread', 'awaySpread_adj', 'homeTeam' ,]].rename(columns={'awayTeam': 'team', 'awaySpread': 'spread',  'homeTeam': 'opponent', 'awaySpread_adj' : 'adj_spread'})
    ])



    # set maximum spread for win or loss to 28 and -28 respectively
    teams['adj_spread'] = np.where(teams['adj_spread'] > 28, 28, teams['adj_spread']) # cap the upper bound scoring margin at +28 points
    teams['adj_spread'] = np.where(teams['adj_spread'] < -28, -28, teams['adj_spread']) # cap the lower bound scoring margin at -28 points

    # group rows by team
    spreads = teams.groupby('team').adj_spread.mean()
    return sreads.head(50)
'''


# create empty arrays
ts = []
vics = []
terms = []
solutions = []
loss = []
schedule = pd.DataFrame(columns = ['Team', 'Victories'])

for team in spreads.keys():
    row = []
 # get a list of team opponents
    opps = list(teams[teams['team'] == team]['opponent'])
# list of wins
    win = list(teams[(teams['team'] == team) & (teams['spread'] > 0)]['opponent'])
    losses = list(teams[(teams['team'] == team) & (teams['spread'] < 0)]['opponent'])

    for opp in spreads.keys():
        if opp == team:
    # set opponents coefficient to 1 
            row.append(1)
        elif opp in opps:
            # coefficient for opponents should be 1 over the number of opponents
        	row.append(-1.0/len(opps))
        else:
            # teams not yet played recieve a coefficient of zero
            row.append(0)
    terms.append(row)

    # average game spread on the other side of the equation
    solutions.append(spreads[team])
    
    # save opponents
    loss.append(losses)
    ts.append(team)
    vics.append(win)
    

schedule['Team'] = ts
schedule['Victories'] = vics
schedule['Losses'] = loss
# solve the linear equation    
solutions = np.linalg.solve(np.array(terms), np.array(solutions))


# add team names to solutions and create dataframe
ratings = list(zip( spreads.keys(), solutions ))
PR = pd.DataFrame(ratings, columns=['team', 'adj'])
# create spread variable
data2['home_spread'] = data2['home_points'] - data2['away_points']
data2['away_spread'] = -data2['home_spread']


# convert each game into two rows, one for each team and remove unwated rows.
teams2 = pd.concat([
    data2[['home_team', 'home_spread', 'away_team', ]].rename(columns={'home_team': 'team', 'home_spread': 'spread',  'away_team': 'opponent'}),
    data2[['away_team', 'away_spread', 'home_team' ,]].rename(columns={'away_team': 'team', 'away_spread': 'spread',  'home_team': 'opponent'})
])

#list of teams
teams3 = list(teams2.team)
# create empty arrays
ts2 = []
vics2 = []
loss2 = []
schedule2 = pd.DataFrame(columns = ['Team', 'Victories','Losses'])

for team in teams3:
 # get a list of team opponents
    opps = list(teams2[teams2['team'] == team]['opponent'])
# list of wins
    win = list(teams2[(teams2['team'] == team) & (teams2['spread'] > 0)]['opponent'])
    losses = list(teams2[(teams2['team'] == team) & (teams2['spread'] < 0)]['opponent'])
    
    # save opponents
    loss2.append(losses)
    ts2.append(team)
    vics2.append(win)
# calculations in this cell are to define a teams true record
schedule2['Team'] = ts2
schedule2['Victories'] = vics2
schedule2['Losses'] = loss2


schedule2 = schedule2[schedule2['Team'].isin(schedule['Team'])]
records = []
win_p = []
loss_count = []
for ind,row in schedule2.iterrows():
    lc = len(row['Losses'])
    rec = '(' + str(len(row['Victories'])) + '-' + str(len(row['Losses'])) + ')'
    per = len(row['Victories']) / (len(row['Victories']) + len(row['Losses']))  
    records.append(rec)
    win_p.append(per)
    loss_count.append(lc)
        
schedule2['records'] = records
schedule2['Losses'] = loss_count
schedule2['Win %'] = win_p
schedule2['Win %'] = schedule2['Win %'] * 100
Record = schedule2[['Team','records','Win %']].drop_duplicates()
Record['Team'] = np.where(Record['Team'] == 'Miami (OH)', "Miami_OH", Record['Team'])
# sets mean adj +/- score to zero (added after week 7 2021)
mean = PR.adj.mean()
PR['adj'] = PR['adj'] - mean

# create new data frame for each game containing columns listed below
home_teams = pd.concat([
    data[['home_team', 'home_points', 'away_points', 'away_team' ,'week']].rename(columns={'home_team': 'team', 'home_points': 'offense',  'away_points': 'defense', 'away_team' : 'opponent'})
    ])

away_teams = pd.concat([
    data[['away_team', 'away_points', 'home_points', 'home_team','week' ]].rename(columns={'away_team': 'team', 'away_points': 'offense',  'home_points': 'defense', 'home_team' : 'opponent' })
    ])

stats = home_teams.append(away_teams)

# create a binary win variable
stats['win'] = np.where(stats['offense'] > stats['defense'], 1, 0)

# variable used to help define adj win percentage
win_a_function = ((stats.iloc[0,4] + stats.iloc[-1,4])/50)*2

# create variable used to calculate adjusted win percentage
stats['win_adj'] = np.where(stats['offense'] > stats['defense'], 1, ((stats.iloc[0,4] + stats.iloc[-1,4])/50) -((win_a_function/(stats.iloc[-1,4]-stats.iloc[0,4]))*(stats['week']-1)))

# create variable for true +/- value
stats['margin'] = stats['offense'] - stats['defense']

# create a count variable
stats['game'] = 1

#join stats and PR on opponent column
stats2 = pd.merge(stats, PR, left_on = 'opponent', right_on = 'team', how = 'left')

# create a games played count for each team
total_games = stats.groupby('team').game.sum()

# creates a vector holding average true +/- value of each team
margin = stats.groupby('team').margin.mean()

# creates an average points scored vector 
offense = stats.groupby('team').offense.mean()

# creates an average points allowed vector 
defense = stats.groupby('team').defense.mean()

# creates a true win percentage vector
win_per = stats.groupby('team').win.mean()

# creates an adjusted win percentage vector 
adj_win_per = stats.groupby('team').win_adj.mean()

# creates a strength of schedule vector
SOS = stats2.groupby('team_x').adj.mean()

# appends total games vector to data frame
PR['total_games'] = total_games.values

# appends strength of schedule vector to data frame
PR['SOS'] = SOS.values

# appends avereage points scored vector to data frame
PR['offense'] = offense.values

# appends avereage points allowed vector to data frame
PR['defense'] = defense.values

# appends true win percentage vector to data frame
PR['win %'] = win_per.values

# appends true +/- vector to data frame
PR['avg +/-'] = margin.values

# appends adj win percentage vector to data frame
PR['adj win %'] = adj_win_per.values

# alters adj win percentage of teams with zero wins
PR['adj win %'] = np.where(PR['win %'] == 0, .4 / (PR['total_games']), PR['adj win %'])

# ranks teams offenses
PR['offense'] = PR['offense'].rank(method='min', ascending=False)

# ranks teams defenses
PR['defense'] = PR['defense'].rank(method='min')

# ranks teams strength of schedule
PR['SOS'] = PR['SOS'].rank(method='min', ascending=False)

# creates function used to calculate rating
def square2(x):
    return np.sqrt(np.sqrt(x))

# calculates rating
PR['rating'] = (PR['adj'] + 100) * square2(PR['adj win %'])

# multiplies win % by 100
PR['win %'] = PR['win %']*100

# multiplies adj win % by 100
PR['adj win %'] = PR['adj win %']*100

# rename columns
PR = PR.rename(columns={'team': 'School', 'rating': 'Rating',  'win %' : "Win %", 'adj win %' : 'Adj Win %', 'offense' : 'Offense' , 'defense' : 'Defense', 'avg +/-' : '+/-', 'adj' : 'Adj +/-'}) 

# sorts values by rating
rankings = PR.sort_values('Rating', ascending=False).reset_index()[['School', 'Rating','Adj Win %', 'SOS', 'Offense', 'Defense','+/-','Adj +/-']]

# add rating points for victorie over top 25 teams
# top 25 = 1
# top 10 = 2
# top 5 = 3
top25 = list(rankings.School.head(25))
top10 = list(rankings.School.head(10))
top5 = list(rankings.School.head(5))
ratings = []
for ind,row in rankings.iterrows():
    t = row['School']
    vict = schedule[schedule['Team'] == t].iloc[0,1]
    rating = row['Rating']
    for i in vict:
        if i in top25:
            rating = rating + 1
        if i in top10:
            rating = rating + 1
        if i in top5:
            rating = rating + 1
    ratings.append(rating)
rankings['Rating'] = ratings

# sort by rating
rankings.sort_values('Rating', ascending = False,inplace = True)

rankings = rankings.reset_index()

# create rank columns
r = []
for i in rankings.index:
    r.append(i + 1)
rankings['Rank'] = r

# flip schools who are ranked directly under a team they beat, but has not beat them.
prev = rankings['School'][0]
rank = []
for ind,row in rankings.iterrows():
    t = row['School']
    v = schedule[schedule['Team'] == t].iloc[0,1]
    v2 = schedule[schedule['Team'] == prev].iloc[0,1]
    r = row['Rank']
    for i in v:
        if i == prev:
            r = r - 1
            for i in v2:
                if i == row['School']:
                    r = r + 1
    rank.append(r)
    prev = row['School']
rankings['Rank'] = rank

# Downloading contents from AP Poll
url = "http://www.collegepollarchive.com/football/ap/seasons.cfm?seasonid=" + year
data = requests.get(url).text

# Creating BeautifulSoup object
soup = BeautifulSoup(data, 'html.parser')

# Creating list with all tables
rows = soup.find_all('tr')

# loop to create attach ap rankings to all ranked schools
ap = pd.DataFrame()
rank = []
college = []
for i in range(1,26):
    try:
        rank.append(i)
        college.append(rows[i].find_all('td')[3].text.split(' (')[0])
    except:
        continue
ap['AP'] = rank
ap['School'] = college

# alter names to match internal rankings
ap['School'] = np.where(ap['School'] == 'Mississippi', 'Ole Miss', ap['School'])
ap['School'] = np.where(ap['School'] == 'San Jose State', 'San José State', ap['School'])
ap['School'] = np.where(ap['School'] == 'Southern Miss', 'Southern Mississippi', ap['School'])
ap['School'] = np.where(ap['School'] == "Hawaii", "Hawai'i", ap['School'])

# resort with new ranks
rankings.sort_values('Rank', ascending = True,inplace = True)
rankings = rankings.reset_index()
rankings.drop(columns = 'index', inplace = True)

# merge ap ranking to data
rankings_m = rankings.merge(ap, how = 'outer', on = 'School')

#check to see if all teams merged properly
len(rankings_m) == len(rankings)

rankings_m['School'] = np.where(rankings_m['School'] == 'Miami (OH)', "Miami_OH", rankings_m['School'])

# change null rankings to NR
rankings_m['AP'] = np.where(rankings_m['AP'].isna(), 'NR',rankings_m['AP'])

'''

