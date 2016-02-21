import json
import matplotlib.pyplot as plt
import os
from pprint import pprint

import numpy as np
import matplotlib.pyplot as plt
from scipy.misc import imread
import matplotlib.cbook as cbook

def replay():


    for root, dirs, files in os.walk("/Users/David/Desktop/nflhackathon/game1plays/"):

        for file in files:

            filename = "/Users/David/Desktop/nflhackathon/game1plays/" + file

            print(file)

            if file.endswith(".json"):
                with open(filename) as data_file:
                    data = json.load(data_file)

                teamData = ['homeTrackingData', 'awayTrackingData']


                play = data['play']
                print(play)

                schedule = data['schedule']

                possession = play['possessionTeamId']
                home_team = schedule['homeTeamId']
                visitor_team = schedule['visitorTeamId']

                print(possession)
                print(home_team)
                

                plt.figure()
                plt.ion()

                teamLocations = []

                for i in range(2):
                    team = teamData[i]
                    playerLocationData = data[team]

                    playerLocations = []

                    for playerData in playerLocationData:
                        trackingData = playerData['playerTrackingData']
                        playerLocation = []

                        for locationData in trackingData:
                            playerLocation.append((locationData['x'], locationData['y']))
                        playerLocations.append(playerLocation)

                    teamLocations.append(playerLocations)
                # print(teamLocations)
                index = 0
                timeLength = len(teamLocations[i][0])
                for time in [x for x in range(timeLength) if x % 3 == 0]:
                    for teamInd in range(2):
                        if int(possession) - home_team == 0:
                            opp = 1
                        else:
                            opp = 0
                        for playerInd in range(len(teamLocations[i])):
                            if time < len(teamLocations[teamInd][playerInd]):
                                x,y = teamLocations[teamInd][playerInd][time]
                                color = 'b' if teamInd == 0 else 'r'
                                
                                # to see if they are open
                                diff_list = []
                                for playerInd in range(len(teamLocations[opp])):
                                    if time < len(teamLocations[opp][playerInd]):
                                        xOpp, yOpp = teamLocations[opp][playerInd][time]
                                        difference = abs(x-xOpp) + abs(y-yOpp)
                                        diff_list.append(difference)
                                if min(diff_list) > 5:
                                    color = 'y'

                                # plot points
                                plt.scatter(x, y, c=color, s=100)

                    # if you want to show paths, set this to true
                    showPaths = False

                    if showPaths:
                        for i in range(2):
                            for player in teamLocations[i]:
                                xData = []
                                yData = []

                                for x,y in player:
                                    xData.append(x)
                                    yData.append(y)

                                if i == 1:
                                    plt.plot(xData, yData, c='r')
                                else:
                                    plt.plot(xData, yData, c='b')

                    xmin = 10
                    xmax = 110
                    ymin = 0
                    ymax = 53.3
                    axes = plt.gca()
                    axes.set_xlim([xmin,xmax])
                    axes.set_ylim([ymin,ymax])

                    im = plt.imread('/Users/David/Desktop/nflhackathon/game1plays/football_field.png')
                    implot = plt.imshow(im, extent=[5, 115, 0, 53.3])

                    #heat map
                    # heatmap, xedges, yedges = np.histogram2d(yData, xData, bins=50)
                    # extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]
                    # plt.imshow(heatmap, extent=[5,115,0,53.3])

                    #draw dots and animate 
                    plt.draw()
                    plt.pause(0.01)
                    plt.clf()
                   
            plt.close()


replay()









