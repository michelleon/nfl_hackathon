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
    for x,y in teamLocations[0][0]:
        index += 1
        if index % 3 != 0:
            continue
        plt.scatter(x, y, c='b', s=100)


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
    """
    # plotting 1 player
    xData = []
    yData = []


    for player in playerLocations:
        xData = []
        yData = []

        for x,y in player:
            xData.append(x)
            yData.append(y)

        if i == 0:
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


        plt.draw()
        plt.pause(0.05)
        plt.clf()
        """

    # plt.show()


main()
