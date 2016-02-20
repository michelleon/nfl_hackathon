import json
import matplotlib.pyplot as plt
import time

from pprint import pprint


def main():
    with open('110.json') as data_file:
        data = json.load(data_file)

    teamData = ['homeTrackingData', 'awayTrackingData']

    plt.figure()
    plt.ion()

    teamLocations = []

    for i in range(2):
        team = teamData[i]
        playerLocationData = data[team]

        # print playerLocationData

        playerLocations = []

        for playerData in playerLocationData:
            trackingData = playerData['playerTrackingData']
            playerLocation = []

            for locationData in trackingData:
                playerLocation.append((locationData['x'], locationData['y']))
            playerLocations.append(playerLocation)

        teamLocations.append(playerLocations)

    index = 0
    for time in range(len(teamLocations[i][0])):
        for teamInd in range(2):
            for playerInd in range(len(teamLocations[i])):
                x,y = teamLocations[teamInd][playerInd][time]
                color = 'b' if teamInd == 0 else 'r'
                plt.scatter(x, y, c=color, s=100)

        xmin = 10
        xmax = 110
        ymin = 0
        ymax = 53.3
        axes = plt.gca()
        axes.set_xlim([xmin,xmax])
        axes.set_ylim([ymin,ymax])

        plt.draw()
        plt.pause(0.01)
        plt.clf()


    return


main()
