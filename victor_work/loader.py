import json
import matplotlib.pyplot as plt

from pprint import pprint


def main():
    with open('sample.json') as data_file:
        data = json.load(data_file)

    teamData = ['homeTrackingData', 'awayTrackingData']

    plt.figure()

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

    plt.show()

main()
