import numpy as np

# using thresholded image, return the desired parameters
def curveFitData(arr):

    # create identical array for manipulation
    threshArr = np.array(shape=arr.shape)
    for i in range(0, len(arr)):
        for j in range(0, len(arr[i])):
            threshArr[i,j] = arr[i,j]
    
    # count the number of points and preallocate vectors
    numPoints = np.sum(threshArr)
    c2 = np.zeros(numPoints)
    r2 = np.zeros(numPoints)
    count = 0

    # list of all x's and y's
    for r in range(0, len(threshArr)):
        for c in range(0, len(threshArr[r])):
            if threshArr(c,r) == 1:
                r2[count] = r
                c2[count] = c
                count += 1
    
    # CHECK EACH POINT AND SORT INTO OBJECTS

    # start object list with one object
    tObjects = [thresholdObject(c2[0], r2[0])]

    # go through each image point
    for i in range(1, len(c2)):
        noMatch = True

        # go through each existing object
        o = 1
        while noMatch and o <= len(tObjects):

            # check each point in the object until it finds a neighbor
            # or goes through all of them
            j = len(tObjects[o].xCoords)
            while noMatch and j > 0:

                # if it finds a neighbor, add it to the object
                if abs(tObjects[o].xCoords[j] - c2[i]) <= 2 and abs(tObjects[o].yCoords[j] - r2[i]) <= 2:
                    tObjects[o].addPoint(c2[i], r2[i])
                    noMatch = False
                else:
                    # go to next point
                    j -= 1
            
            o += 1
        
        # if it goes through all objects without a match,
        # make a new object
        if noMatch:
            tObjects.append(thresholdObject(c2[i], r2[i]))

    # CONSOLIDATE OBJECTS

    # this needs to compare every point on an object with every other
    # point on other objects (not really EVERY point)

    # sort the objects array from most points to least
    # TODO: sort tObjects in reverse order of numPoints


# a class to represent threshold objects
class thresholdObject():

    def __init__(self, x0, y0):

        self.xCoords = [x0]
        self.yCoords = [y0]
        self.numPoints = 1

    def addPoint(self, xCoord, yCoord):
        self.xCoords.append(xCoord)
        self.yCoords.append(yCoord)
        self.numPoints += 1
