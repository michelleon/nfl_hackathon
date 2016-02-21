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

            if file.endswith(".json"):
                with open(filename) as data_file:
                    data = json.load(data_file)

                teamData = ['homeTrackingData', 'awayTrackingData']

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

                index = 0
                timeLength = len(teamLocations[i][0])
                for time in [x for x in range(timeLength) if x % 3 == 0]:
                    for teamInd in range(2):
                        for playerInd in range(len(teamLocations[i])):
                            if time < len(teamLocations[teamInd][playerInd]):
                                x,y = teamLocations[teamInd][playerInd][time]
                                color = 'b' if teamInd == 0 else 'r'
                                plt.scatter(x, y, c=color, s=100)

                    # if you want to show paths, set this to true
                    showPaths = True

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


                    plt.draw()
                    plt.pause(0.01)
                    plt.clf()
                   
            plt.close()


replay()









