import numpy as np
import json
import matplotlib.pyplot as plt


def load_rosters():
    with open('data/team1.json') as f1:
        team1 = json.load(f1)
    with open('data/team2.json') as f2:
        team2 = json.load(f2)
    with open('data/team3.json') as f1:
        team3 = json.load(f1)
    with open('data/team4.json') as f2:
        team4 = json.load(f2)
    with open('data/team5.json') as f1:
        team5 = json.load(f1)
    with open('data/team6.json') as f2:
        team6 = json.load(f2)
    return [team1, team2, team3, team4, team5, team6] # teams 0 indexed

def load_game_routes(game_filepath):
    with open(game_filepath) as data_file:
        # gameData = json.load(data_file)
        route_vectors = []
        teams = load_rosters()

        for line in data_file:
            data = json.loads(line) 
            playType = data['play']['playType']
            # direction_of_play_left = (data['yardsToGo'] == data['absoluteYardlineNumber'] - 10) # TODO
            if playType == 'play_type_pass':
                teamWithPossessionID = data['play']['possessionTeamId']
                roster = teams[int(teamWithPossessionID) - 1]
                wide_receivers = get_wide_receivers(roster)
                visitorTeamID = data['schedule']['visitorTeam']['teamId']
                playerLocationData = data['homeTrackingData']
                if visitorTeamID == teamWithPossessionID:
                    playerLocationData = data['awayTrackingData']

                for playerData in playerLocationData:
                    if playerData['nflId'] in wide_receivers:
                        trackingData = playerData['playerTrackingData']
                        route_vectors.append(route_vector(trackingData))
        # print(route_vectors)
        return route_vectors

def route_vector(playerLocationData):
    # create route feature vector, should be 40 
    # np.zeros(40*53)
    # run through until event of "snap"
    # end at event of "throw"
    # record x, y position as the player start
    # x being the yardline, 
    # 
    route = [0 for i in range(40*53)]
    record_loc = False
    start_x = start_y = None
    initial_location = playerLocationData[0]
    last_location = playerLocationData[len(playerLocationData) - 1]
    direction_of_play_left = (last_location['x'] < initial_location['x'])
    xData, yData = [], [] # REMOVE

    for location in playerLocationData:
        if 'event' in location.keys():
            if location['event'] == 'snap':
                record_loc = True
                start_x, start_y = int(location['x']), int(location['y'])
                xData.append(location['x']) # REMOVE
                yData.append(location['y']) # REMOVE
                i = convert_location(start_x, start_y, start_x, direction_of_play_left)
                route[i] = 1
            elif location['event'] == 'passForward':
                record_loc = False
                i = convert_location(int(location['x']), int(location['y']), start_x, direction_of_play_left)
                xData.append(location['x']) # REMOVE
                yData.append(location['y']) # REMOVE
                route[i] = 1
        else:
            if record_loc:
                i = convert_location(int(location['x']), int(location['y']), start_x, direction_of_play_left)
                route[i] = 1
                xData.append(location['x']) # REMOVE
                yData.append(location['y']) # REMOVE
    # visualize_route(xData, yData) # REMOVE
    # print(route)
    return route

def convert_location(x, y, start_x, direction_of_play_left):
    if not direction_of_play_left:
        row = y # meaning that higher on the field will be lower in the 2d array vis
        col = x - start_x
    else:
        row = 53 - y
        col = abs(x - start_x)
    index =  row * 40 + col
    return index


def get_wide_receivers(team_roster):
    # returns a set of the nflId's of the wide receivers
    wr_set = set()
    for player in team_roster['teamPlayers']:
        if player['position'] == 'WR':
            wr_set.add(player['nflId'])
    return wr_set

def visualize_route(xData, yData):
    plt.figure()
    plt.plot(xData, yData)
    plt.show()

def visualize_route_vector(vector):
    # plotting 1 player
    xData = []
    yData = []

    plt.figure()

    for i in range(len(vector)):
        if vector[i] > 0:
            print(i)
            y = i//40
            x = i - y * 40
            print(x, y)
            xData.append(x)
            yData.append(y)
    
    plt.plot(xData, yData)

    plt.show()



routes = load_game_routes('data/game-1-q1.json')
for r in routes:
    visualize_route_vector(r)
# visualize_route_vector(routes[0])



