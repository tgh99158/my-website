#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Mon Sep 27 13:07:17 2021

@author: tylerhoylman
"""
## import packages needed
import xlrd as xl

import numpy as np
import pandas as pd
import requests
import json
import datetime
from io import StringIO

year = datetime.now().year

# scrape data
response = requests.get(
    "https://api.collegefootballdata.com/games",
    params = {"year": year, "seasonType": "both"},
    headers = {"Authorization": "Bearer G7EL3wSl1uoDYSQOw1aVQ+yKey9MG1nYqP3pLaW+sPKAzo/NiGJiKLi5fHo38xXa"}
)

# read data as simplestring
data = pd.read_json(StringIO(response.text))
data.head()


# remove games against non-FBS opponents
data = data[
    (pd.notna(data['home_conference'])) #
    & (pd.notna(data['away_conference']))
]

# only include games that have already been played
data = data[
    (data['home_points'] == data['home_points'])
    & (data['away_points'] == data['away_points'])
    & (pd.notna(data['home_conference']))
    & (pd.notna(data['away_conference']))
]


# create spread variable
data['home_spread'] = data['home_points'] - data['away_points']
data['away_spread'] = -data['home_spread']


# change postseason games from week 1 to week 15
data['week'] = np.where(data['season_type'] == 'postseason',15, data['week'])

# subtract 2.5 points from the home teams spread, keep neutral as is, and add 2.5 to away teams.
data['home_spread'] = np.where(data['neutral_site'] == True, data['home_spread'], (data['home_spread'] - 2.5))
data['away_spread'] = -data['home_spread']
print(data.head())

# convert each game into two rows, one for each team and remove unwated rows.
teams = pd.concat([
    data[['home_team', 'home_spread', 'away_team', ]].rename(columns={'home_team': 'team', 'home_spread': 'spread',  'away_team': 'opponent'}),
    data[['away_team', 'away_spread', 'home_team' ,]].rename(columns={'away_team': 'team', 'away_spread': 'spread',  'home_team': 'opponent'})
])

print(teams.head())


# set maximum spread for win or loss to 28 and -28 respectively
teams['spread'] = np.where(teams['spread'] > 28, 28, teams['spread']) # cap the upper bound scoring margin at +28 points
teams['spread'] = np.where(teams['spread'] < -28, -28, teams['spread']) # cap the lower bound scoring margin at -28 points

# group rows by team
spreads = teams.groupby('team').spread.mean()
spreads.head()
print(spreads)

# create empty arrays
terms = []
solutions = []

for team in spreads.keys():
    row = []
 # get a list of team opponents
    opps = list(teams[teams['team'] == team]['opponent'])

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

# solve the linear equation    
solutions = np.linalg.solve(np.array(terms), np.array(solutions))
print(solutions)

# add team names to solutions and create dataframe
ratings = list(zip( spreads.keys(), solutions ))
PR = pd.DataFrame(ratings, columns=['team', 'adj'])

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
PR['adj win %'] = np.where(PR['win %'] == 0, .6/(PR['total_games']), PR['adj win %'])

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
PR = PR.rename(columns={'team': 'Team', 'rating': 'Rating',  'win %' : "Win %", 'adj win %' : 'Adj win %', 'offense' : 'Offense' , 'defense' : 'Defense', 'avg +/-' : '+/-', 'adj' : 'Adj +/-'}) 

# sorts values by rating
rankings = PR.sort_values('Rating', ascending=False).reset_index()[['Team', 'Rating','Win %','Adj win %', 'SOS', 'Offense', 'Defense','+/-','Adj +/-']]

def get_rankings():
    return rankings
