import numpy as np
from scipy.ndimage import rotate
from scipy.integrate import quad
from scipy.optimize import curve_fit

# define a constant
DATA_NAMES = ("Pole Separation (px)", "Arc Length (px)", "Area Metric (px^2)",
             "Max Curvature (px^-1)", "Avg Curvature (px^-1)")

# using thresholded image, return the desired parameters
def curveFitData(imageArr, arr, preview=True):

    # create identical array for manipulation
    threshArr = np.zeros(shape=arr.shape)
    for i in range(0, len(arr)):
        for j in range(0, len(arr[i])):
            threshArr[i,j] = arr[i,j]
    
    # count the number of points and preallocate vectors
    totalPoints = int(np.sum(threshArr))

    # make these int type to avoid default double assignment later
    c2 = np.zeros(totalPoints, dtype=int)
    r2 = np.zeros(totalPoints, dtype=int)
    count = 0

    # list of all x's and y's
    for r in range(0, len(threshArr)):
        for c in range(0, len(threshArr[r])):
            if threshArr[r,c] == 1:
                r2[count] = r
                c2[count] = c
                count += 1
    
    # FIXME - totalPoints is zero when image is completely dark
    # which results in c2[0] being an invalid call
    
    # CHECK EACH POINT AND SORT INTO OBJECTS

    # start object list with one object
    tObjects = [thresholdObject(c2[0], r2[0])]

    # go through each image point
    for i in range(0, len(c2)):
        noMatch = True

        # go through each existing object
        o = 0
        while noMatch and o < len(tObjects):

            # check each point in the object until it finds a neighbor
            # or goes through all of them
            j = len(tObjects[o].xCoords) - 1
            while noMatch and j >= 0:

                # if it finds a neighbor, add it to the object
                if (abs(tObjects[o].xCoords[j] - c2[i]) <= 2
                        and abs(tObjects[o].yCoords[j] - r2[i]) <= 2):
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
    tObjects.sort(reverse=True)

    # set startLength != len(tObjects) to enter the loop
    startLength = len(tObjects) + 1

    while startLength != len(tObjects):

        startLength = len(tObjects)

        o1 = 0
        while o1 < len(tObjects): # going through objects
            o2 = o1 + 1
            
            while o2 < len(tObjects): # comparing with other objects
                noMatch = True
                i = len(tObjects[o1].xCoords) - 1 # every point in o1

                while noMatch and i >= 0:
                    temp1 = tObjects[o2].xCoords
                    temp2 = tObjects[o2].yCoords
                    coordTrunc = ((abs(temp1-tObjects[o1].xCoords[i]) < 10)
                                * (abs(temp2-tObjects[o1].yCoords[i]) < 10))

                    if sum(coordTrunc) > 0:
                        # if any o1 points are within a radius of 10 of
                        # any o2 points, consolidate objects
                        # remove o2 from tObjects
                        noMatch = False
                        tObjects[o1].addPoints(temp1, temp2)
                        tObjects.pop(o2)
                    
                    i -= 1
                o2 += 1
            o1 += 1
    
    # CENTER OF MASS OF EACH OBJECT
    for o in range(0, len(tObjects)):
        mass = np.uint64(0)
        xsum = np.uint64(0)
        ysum = np.uint64(0)
        for i in range(0, tObjects[o].numPoints):
            yC = tObjects[o].yCoords[i]
            xC = tObjects[o].xCoords[i]
            mass += imageArr[yC, xC]
            ysum += imageArr[yC, xC] * tObjects[o].yCoords[i]
            xsum += imageArr[yC, xC] * tObjects[o].xCoords[i]
        tObjects[o].com = [xsum/mass, ysum/mass]
    
    # FIND SPINDLE AUTOMATICALLY
    xcen = len(threshArr[0]) / 2
    ycen = len(threshArr) / 2

    if len(tObjects) > 1:
        numPointsArr = [getattr(o, "numPoints") for o in tObjects]
        avgObjectSize = np.mean(numPointsArr)

        minDist = len(threshArr[0])
        for o in range(0, len(tObjects)):
            if np.linalg.norm(np.array([xcen, ycen]) - np.array([tObjects[o].com])) < minDist and tObjects[o].numPoints > avgObjectSize:
                minDist = np.linalg.norm(np.array([xcen, ycen]) - np.array([tObjects[o].com]))
                centerObj = o
        
        spindle = tObjects[centerObj]
    else:
        spindle = tObjects[0]
    
    # create array with only the spindle object
    spindleArr = np.zeros(threshArr.shape)
    for i in range(0, spindle.numPoints):
        spindleArr[spindle.yCoords[i], spindle.xCoords[i]] = 1
    
    # multiply original image by the one we just made
    spindleImg = imageArr * spindleArr

    # FIND MOMENT OF INERTIA VECTORS
    Ixx = 0
    Iyy = 0
    Ixy = 0

    for y in range(0, len(spindleArr)):
        for x in range(0, len(spindleArr[y])):
            Ixx += spindleArr[y,x] * ((x - spindle.com[0]) ** 2)
            Iyy += spindleArr[y,x] * ((y - spindle.com[1]) ** 2)
            Ixy += spindleArr[y,x] * (x - spindle.com[0]) * (y - spindle.com[1])

    tensorMat = np.array([[Ixx, Ixy],
                          [Ixy, Iyy]])

    # CALCULATE EIGENVECTORS AND ROTATE THE SPINDLE
    eigenValues, eigenVectors = np.linalg.eig(tensorMat)
    tempIndex = list(eigenValues).index(min(eigenValues))
    mainvector = eigenVectors[:,tempIndex]

    rotAngle = - np.arctan(mainvector[0]/mainvector[1]) * 180 / np.pi
    rotImg = rotate(spindleImg, rotAngle, order=1)
    
    if not preview:
        return calculateMeasurements(rotImg)
    else:
        return plotOnSpindle(rotImg)

def calculateMeasurements(spindleArray):

    # FIT CURVE AND FIND POLES
    numPoints = int(np.sum(spindleArray > 0.0))

    rotX = np.zeros(numPoints)
    rotY = np.zeros(numPoints)

    rotHeight, rotWidth = spindleArray.shape

    count = 0
    for r in range(0, rotHeight):
        for c in range(0, rotWidth):
            if spindleArray[r,c] > 0:
                rotX[count] = c
                rotY[count] = r
                count += 1
    
    def quadFunc(x, a, b, c):
        return a * (x ** 2) + b * x + c

    params, covariances  = curve_fit(quadFunc, rotX, rotY)
    a, b, c = params[0], params[1], params[2]

    minX = min(rotX)
    maxX = max(rotX)

    leftPole = [minX, quadFunc(minX, a, b, c)]
    rightPole = [maxX, quadFunc(maxX, a, b, c)]

    # POLE SEPARATION
    params, covariances = curve_fit(lambda x, a, b: a * x + b, rotX, rotY)
    a2 = params[0]
    poleSeparation = np.sqrt(a2**2 + 1) * (maxX - minX)

    # ARC LENGTH
    def arcFunc(t):
        return np.sqrt(4 * a**2 * t**2 + 4 * a * b * t + b**2 + 1)
    arcLength = quad(arcFunc, minX, maxX)[0]
    
    # CURVATURE

    # area metric
    def spindleFunc(x):
        return a * x**2 + b * x + c
    
    x1 = leftPole[0]
    x2 = rightPole[0]
    y1 = leftPole[1]
    y2 = rightPole[1]
    m1 = (y2 - y1) / (x2 - x1)
    
    def poleFunc(x):
        return m1 * (x - x1) + y1
    
    areaCurve = abs(quad(poleFunc, x1, x2)[0] - quad(spindleFunc, x1, x2)[0])

    # maximum and average curvature metrics
    maxCurve = abs(2*a)
    
    def curvatureFunc(x):
        return (2 * a) / ((4 * a**2 * x**2 + 4 * a * b * x + b**2 + 1)**(3/2))
    
    avgCurve = abs(quad(curvatureFunc, x1, x2)[0] / (x2 - x1))

    # output data
    data = [poleSeparation, arcLength, areaCurve, maxCurve, avgCurve]

    return data

def plotOnSpindle(spindleArray):

    # FIT CURVE AND FIND POLES
    numPoints = int(np.sum(spindleArray > 0.0))

    rotX = np.zeros(numPoints, dtype=int)
    rotY = np.zeros(numPoints, dtype=int)

    rotHeight, rotWidth = spindleArray.shape

    count = 0
    for r in range(0, rotHeight):
        for c in range(0, rotWidth):
            if spindleArray[r,c] > 0:
                rotX[count] = c
                rotY[count] = r
                count += 1
    
    def quadFunc(x, a, b, c):
        return a * (x ** 2) + b * x + c

    params, covariances  = curve_fit(quadFunc, rotX, rotY)
    a, b, c = params[0], params[1], params[2]

    minX = min(rotX)
    maxX = max(rotX)

    leftPole = [minX, int(quadFunc(minX, a, b, c))]
    rightPole = [maxX, int(quadFunc(maxX, a, b, c))]

    def spindleFunc(x):
        return a * x**2 + b * x + c

    fitXValues = np.linspace(minX, maxX, maxX - minX + 1, dtype=int)
    fitYValues = np.zeros(fitXValues.shape, dtype=int)
    for i, x in enumerate(fitXValues):
        fitYValues[i] = int(spindleFunc(x))
    
    # use plotValue for plotting white (once the array is normalized)
    plotValue = np.max(spindleArray)

    # ~ half of the line thickness in pixels
    hL = 0

    for i in range(len(fitXValues)):
        x = fitXValues[i]
        y = fitYValues[i]
        if int(i / 3) % 2 == 0:
            spindleArray[y - hL : y + hL + 1, x - hL : x + hL + 1] = 0
        else:
            spindleArray[y - hL : y + hL + 1, x - hL : x + hL + 1] = plotValue

    # half of the plotted square edge in pixels
    hS = 2

    spindleArray[leftPole[1] - hS : leftPole[1] + hS + 1,
                 leftPole[0] - hS : leftPole[0] + hS + 1] = plotValue
    spindleArray[rightPole[1] - hS : rightPole[1] + hS + 1,
                 rightPole[0] - hS : rightPole[0] + hS + 1] = plotValue

    return spindleArray

# a class to represent threshold objects
class thresholdObject():

    def __init__(self, x0, y0):

        self.xCoords = [x0]
        self.yCoords = [y0]
        self.numPoints = 1
        self.com = []
    
    def __lt__(self, other):
        return self.numPoints < other.numPoints

    def addPoint(self, xCoord, yCoord):
        self.xCoords.append(xCoord)
        self.yCoords.append(yCoord)
        self.numPoints += 1
    
    def addPoints(self, x2s, y2s):
        for i in range(0, len(x2s)):
            self.addPoint(x2s[i], y2s[i])
