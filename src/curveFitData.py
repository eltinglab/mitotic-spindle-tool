from numpy import zeros, array, arctan, pi, uint64, cos, sin
from numpy import sum as npsum
from numpy import mean as npmean
from numpy import sqrt as npsqrt
from numpy.linalg import norm, eig
from scipy.ndimage import rotate
from scipy.integrate import quad
from scipy.optimize import curve_fit
import tiffFunctions as tiffF

# define a constant
DATA_NAMES = ("Pole Separation (px)", "Arc Length (px)", "Area Metric (px^2)",
             "Max Curvature (px^-1)", "Avg Curvature (px^-1)")

def transformCoordinatesBackToOriginal(rotatedCoords, transformInfo):
    """
    Transform coordinates from rotated/processed space back to original image space
    
    Args:
        rotatedCoords: tuple of (x, y) coordinates in rotated space
        transformInfo: dictionary containing transformation parameters
    
    Returns:
        tuple of (x, y) coordinates in original image space
    """
    if transformInfo is None:
        return rotatedCoords
    
    rot_x, rot_y = rotatedCoords
    
    # Get transformation parameters
    com = transformInfo['com']  # Center of mass in original image
    rotAngle = transformInfo['rotAngle']  # Rotation angle in degrees
    processed_center_x = transformInfo['processed_center_x']
    processed_center_y = transformInfo['processed_center_y']
    
    # Convert rotation angle to radians
    angle_rad = rotAngle * pi / 180
    
    # Step 1: Translate to center of rotated image
    centered_x = rot_x - processed_center_x
    centered_y = rot_y - processed_center_y
    
    # Step 2: Apply inverse rotation
    cos_angle = cos(-angle_rad)
    sin_angle = sin(-angle_rad)
    
    unrotated_x = centered_x * cos_angle - centered_y * sin_angle
    unrotated_y = centered_x * sin_angle + centered_y * cos_angle
    
    # Step 3: Translate back to original coordinate system
    original_x = unrotated_x + com[0]
    original_y = unrotated_y + com[1]
    
    return (original_x, original_y)

def getSpindleImgWithTransform(imageArr, arr):
    """
    Enhanced version of getSpindleImg that also returns transformation information
    needed to map coordinates back to the original image space
    """

    # create identical array for manipulation
    threshArr = zeros(shape=arr.shape)
    for i in range(0, len(arr)):
        for j in range(0, len(arr[i])):
            threshArr[i,j] = arr[i,j]
    
    # count the number of points and preallocate vectors
    totalPoints = int(npsum(threshArr))

    # make these int type to avoid default double assignment later
    c2 = zeros(totalPoints, dtype=int)
    r2 = zeros(totalPoints, dtype=int)
    count = 0

    # list of all x's and y's
    for r in range(0, len(threshArr)):
        for c in range(0, len(threshArr[r])):
            if threshArr[r,c] == 1:
                r2[count] = r
                c2[count] = c
                count += 1
    
    # Return a white X if there are no points left after thresholding
    if totalPoints == 0:
        doesSpindleExist = False
        return tiffF.threshXArr(), doesSpindleExist, None
    else:
        doesSpindleExist = True
    
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
        mass = uint64(0)
        xsum = uint64(0)
        ysum = uint64(0)
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
        avgObjectSize = npmean(numPointsArr)

        minDist = len(threshArr[0])
        for o in range(0, len(tObjects)):
            if (norm(array([xcen, ycen]) 
                    - array([tObjects[o].com])) < minDist
                    and tObjects[o].numPoints > avgObjectSize):
                minDist = norm(array([xcen, ycen])
                                         - array([tObjects[o].com]))
                centerObj = o
        
        spindle = tObjects[centerObj]
    else:
        spindle = tObjects[0]
    
    # create array with only the spindle object
    spindleArr = zeros(threshArr.shape)
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

    tensorMat = array([[Ixx, Ixy],
                          [Ixy, Iyy]])

    # CALCULATE EIGENVECTORS AND ROTATE THE SPINDLE
    eigenValues, eigenVectors = eig(tensorMat)
    tempIndex = list(eigenValues).index(min(eigenValues))
    mainvector = eigenVectors[:,tempIndex]

    rotAngle = - arctan(mainvector[0]/mainvector[1]) * 180 / pi
    rotImg = rotate(spindleImg, rotAngle, order=1)
    
    transformInfo = {
        'com': spindle.com,
        'rotAngle': rotAngle,
        'processed_center_x': xcen,
        'processed_center_y': ycen
    }
    
    return rotImg, doesSpindleExist, transformInfo

def getSpindleImg(imageArr, arr):

    # create identical array for manipulation
    threshArr = zeros(shape=arr.shape)
    for i in range(0, len(arr)):
        for j in range(0, len(arr[i])):
            threshArr[i,j] = arr[i,j]
    
    # count the number of points and preallocate vectors
    totalPoints = int(npsum(threshArr))

    # make these int type to avoid default double assignment later
    c2 = zeros(totalPoints, dtype=int)
    r2 = zeros(totalPoints, dtype=int)
    count = 0

    # list of all x's and y's
    for r in range(0, len(threshArr)):
        for c in range(0, len(threshArr[r])):
            if threshArr[r,c] == 1:
                r2[count] = r
                c2[count] = c
                count += 1
    
    # Return a white X if there are no points left after thresholding
    if totalPoints == 0:
        doesSpindleExist = False
        return tiffF.threshXArr(), doesSpindleExist
    else:
        doesSpindleExist = True
    
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
        mass = uint64(0)
        xsum = uint64(0)
        ysum = uint64(0)
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
        avgObjectSize = npmean(numPointsArr)

        minDist = len(threshArr[0])
        for o in range(0, len(tObjects)):
            if (norm(array([xcen, ycen]) 
                    - array([tObjects[o].com])) < minDist
                    and tObjects[o].numPoints > avgObjectSize):
                minDist = norm(array([xcen, ycen])
                                         - array([tObjects[o].com]))
                centerObj = o
        
        spindle = tObjects[centerObj]
    else:
        spindle = tObjects[0]
    
    # create array with only the spindle object
    spindleArr = zeros(threshArr.shape)
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

    tensorMat = array([[Ixx, Ixy],
                          [Ixy, Iyy]])

    # CALCULATE EIGENVECTORS AND ROTATE THE SPINDLE
    eigenValues, eigenVectors = eig(tensorMat)
    tempIndex = list(eigenValues).index(min(eigenValues))
    mainvector = eigenVectors[:,tempIndex]

    rotAngle = - arctan(mainvector[0]/mainvector[1]) * 180 / pi
    rotImg = rotate(spindleImg, rotAngle, order=1)
    
    transformInfo = {
        'com': spindle.com,
        'rotAngle': rotAngle,
        'processed_center_x': xcen,
        'processed_center_y': ycen
    }
    
    return rotImg, doesSpindleExist, transformInfo

def spindleMeasurements(imageArr, threshArr):
    spindleArray, doesSpindleExist = getSpindleImg(imageArr, threshArr)

    # if spindle doesn't exist in the threshold, don't do calculations
    if not doesSpindleExist:
        return (0.0, 0.0, 0.0, 0.0, 0.0), doesSpindleExist

    # FIT CURVE AND FIND POLES
    numPoints = int(npsum(spindleArray > 0.0))

    rotX = zeros(numPoints)
    rotY = zeros(numPoints)

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
    poleSeparation = npsqrt(a2**2 + 1) * (maxX - minX)

    # ARC LENGTH
    def arcFunc(t):
        return npsqrt(4 * a**2 * t**2 + 4 * a * b * t + b**2 + 1)
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

    return data, doesSpindleExist

def spindlePlot(imageArr, threshArr):
    spindleArray, doesSpindleExist = getSpindleImg(imageArr, threshArr)

    # FIT CURVE AND FIND POLES
    numPoints = int(npsum(spindleArray > 0.0))

    rotX = zeros(numPoints, dtype=int)
    rotY = zeros(numPoints, dtype=int)

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
    centerX = (maxX - minX) / 2 + minX

    def spindleFunc(x):
        return a * x**2 + b * x + c

    leftPole = (minX, spindleFunc(minX))
    rightPole = (maxX, spindleFunc(maxX))
    centerPoint = (centerX, spindleFunc(centerX))

    return (spindleArray, leftPole, rightPole, centerPoint), doesSpindleExist

def spindleMeasurementsManual(imageArr, threshArr, leftPole, rightPole):
    """
    Calculate spindle measurements using manually specified pole positions
    """
    import numpy as np
    from scipy.integrate import quad
    
    # POLE SEPARATION (Euclidean distance)
    poleSeparation = np.sqrt((rightPole[0] - leftPole[0])**2 + 
                           (rightPole[1] - leftPole[1])**2)
    
    # ARC LENGTH (for manual override, approximate as straight line)
    arcLength = poleSeparation
    
    # For area and curvature, we need to fit a curve through the actual spindle pixels
    # Get the rotated spindle for pixel analysis
    spindleArray, doesSpindleExist = getSpindleImg(imageArr, threshArr)
    
    if not doesSpindleExist:
        return [0.0, 0.0, 0.0, 0.0, 0.0], False
    
    try:
        # Get spindle pixels for analysis
        numPoints = int(npsum(spindleArray > 0.0))
        
        if numPoints == 0:
            return [poleSeparation, arcLength, 0.0, 0.0, 0.0], True
        
        rotX = zeros(numPoints)
        rotY = zeros(numPoints)
        
        rotHeight, rotWidth = spindleArray.shape
        
        count = 0
        for r in range(0, rotHeight):
            for c in range(0, rotWidth):
                if spindleArray[r,c] > 0:
                    rotX[count] = c
                    rotY[count] = r
                    count += 1
        
        # Fit a quadratic curve through the detected pixels
        def quadFunc(x, a, b, c):
            return a * (x ** 2) + b * x + c
        
        params, covariances = curve_fit(quadFunc, rotX, rotY)
        a, b, c = params[0], params[1], params[2]
        
        # Use manual poles for endpoints but automatic curve for area calculation
        minX = min(leftPole[0], rightPole[0])
        maxX = max(leftPole[0], rightPole[0])
        
        # AREA METRIC (difference between manual line and detected curve)
        def spindleFunc(x):
            return a * x**2 + b * x + c
        
        x1 = leftPole[0]
        x2 = rightPole[0]
        y1 = leftPole[1]
        y2 = rightPole[1]
        
        if x2 != x1:  # Avoid division by zero
            m1 = (y2 - y1) / (x2 - x1)
            
            def poleFunc(x):
                return m1 * (x - x1) + y1
            
            try:
                areaCurve = abs(quad(poleFunc, x1, x2)[0] - quad(spindleFunc, x1, x2)[0])
            except:
                areaCurve = 0.0
        else:
            areaCurve = 0.0
        
        # CURVATURE METRICS (based on detected curve, not manual line)
        maxCurve = abs(2*a) if a != 0 else 0.0
        
        def curvatureFunc(x):
            if (4 * a**2 * x**2 + 4 * a * b * x + b**2 + 1) > 0:
                return (2 * a) / ((4 * a**2 * x**2 + 4 * a * b * x + b**2 + 1)**(3/2))
            else:
                return 0.0
        
        try:
            if x2 != x1:
                avgCurve = abs(quad(curvatureFunc, x1, x2)[0] / (x2 - x1))
            else:
                avgCurve = 0.0
        except:
            avgCurve = 0.0
        
        # Output data
        data = [poleSeparation, arcLength, areaCurve, maxCurve, avgCurve]
        
        return data, True
        
    except Exception as e:
        print(f"Warning in manual measurements: {e}")
        # Return basic measurements if detailed analysis fails
        return [poleSeparation, arcLength, 0.0, 0.0, 0.0], True

def spindlePlotManual(imageArr, threshArr, leftPole, rightPole):
    """
    Manual version of spindlePlot that uses manually specified pole positions
    """
    # Get the spindle array using automatic detection for the overall shape
    spindleArray, doesSpindleExist = getSpindleImg(imageArr, threshArr)
    
    # If no spindle exists, still create a plot with manual poles on the image
    if not doesSpindleExist:
        spindleArray = imageArr  # Use the original image instead
        doesSpindleExist = True  # Force to true since we have manual positions
    
    # Use manual pole positions instead of fitted ones
    centerPoint = ((leftPole[0] + rightPole[0]) / 2, (leftPole[1] + rightPole[1]) / 2)
    
    return (spindleArray, leftPole, rightPole, centerPoint), doesSpindleExist

def spindlePlotManualWithOriginalCoords(imageArr, threshArr, leftPole, rightPole):
    """
    Manual version that returns coordinates in original space
    """
    # Since manual coordinates are already in original space, no transformation needed
    centerPoint = ((leftPole[0] + rightPole[0]) / 2, (leftPole[1] + rightPole[1]) / 2)
    
    return (imageArr, leftPole, rightPole, centerPoint), True, None

def spindlePlotWithOriginalCoords(imageArr, threshArr):
    """
    Enhanced version of spindlePlot that returns spindle end coordinates 
    in the original coordinate space
    """
    # Get spindle array and transformation info
    spindleArray, doesSpindleExist, transformInfo = getSpindleImgWithTransform(imageArr, threshArr)
    
    if not doesSpindleExist:
        return (spindleArray, (0, 0), (0, 0), (0, 0)), doesSpindleExist, None
    
    # FIT CURVE AND FIND POLES in rotated space
    numPoints = int(npsum(spindleArray > 0.0))
    
    rotX = zeros(numPoints, dtype=int)
    rotY = zeros(numPoints, dtype=int)
    
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
    
    params, covariances = curve_fit(quadFunc, rotX, rotY)
    a, b, c = params[0], params[1], params[2]
    
    minX = min(rotX)
    maxX = max(rotX)
    centerX = (maxX - minX) / 2 + minX
    
    def spindleFunc(x):
        return a * x**2 + b * x + c
    
    # Get poles in rotated space
    leftPole_rotated = (minX, spindleFunc(minX))
    rightPole_rotated = (maxX, spindleFunc(maxX))
    centerPoint_rotated = (centerX, spindleFunc(centerX))
    
    # Transform coordinates back to original space
    leftPole_original = transformCoordinatesBackToOriginal(leftPole_rotated, transformInfo)
    rightPole_original = transformCoordinatesBackToOriginal(rightPole_rotated, transformInfo)
    centerPoint_original = transformCoordinatesBackToOriginal(centerPoint_rotated, transformInfo)
    
    return (imageArr, leftPole_original, rightPole_original, centerPoint_original), doesSpindleExist, transformInfo

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
