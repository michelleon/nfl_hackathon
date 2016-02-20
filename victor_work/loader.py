import json
import matplotlib.pyplot as plt

from pprint import pprint


def main():
    with open('sample.json') as data_file:
        data = json.load(data_file)

    playerLocationData = data['homeTrackingData']

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

    plt.figure()

    for player in playerLocations:
        xData = []
        yData = []

        for x,y in player:
            xData.append(x)
            yData.append(y)

        plt.plot(xData, yData)

    plt.show()

main()
