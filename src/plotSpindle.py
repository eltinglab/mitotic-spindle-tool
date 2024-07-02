from PySide6.QtGui import QPainter, QPainterPath, QColorConstants, QPen
from PySide6.QtCore import QPoint, QPointF
import tiffFunctions as tiffF
import numpy as np

# used for plotting the results of the curve fit onto the preview pixmap
def plotSpindle(fitResults, doesSpindleExist):
    spindleArray = fitResults[0]
    leftPole = fitResults[1]
    rightPole = fitResults[2]
    centerPoint = fitResults[3]

    # scale up the pixmap for smoother overlaid drawings
    # sf: scale factor (higher value = slower preview)
    sF = 2

    # skip all of this code if I decide to set the scale back to 1
    if sF > 1:
        height, width = spindleArray.shape
        bigSpindleArray = np.zeros((height * sF, width * sF))
        for y in range(height):
            for x in range(width):
                bigSpindleArray[sF * y : sF * y + sF,
                                sF * x : sF * x + sF] = spindleArray[y, x]
        
        # scale up coordinate values
        leftPole = (leftPole[0] * sF, leftPole[1] * sF)
        rightPole = (rightPole[0] * sF, rightPole[1] * sF)
        centerPoint = (centerPoint[0] * sF, centerPoint[1] * sF)

    controlPoint = calculateBezierPoint(leftPole, centerPoint, rightPole)

    if sF > 1:
        spindlePix = tiffF.pixFromArr(bigSpindleArray)
    else:
        spindlePix = tiffF.pixFromArr(spindleArray)

    # if there is no spindle, don't try to plot
    if not doesSpindleExist:
        return spindlePix

    # draw the fit line
    painter = QPainter()
    painter.begin(spindlePix)
    painter.setOpacity(0.5)
    path = QPainterPath(QPointF(leftPole[0], leftPole[1]))
    path.quadTo(controlPoint[0], controlPoint[1], rightPole[0], rightPole[1])
    pen = QPen(QColorConstants.Red)
    pen.setWidth(2 * sF)
    painter.setPen(pen)
    painter.drawPath(path)
    painter.end()

    # draw the poles
    painter = QPainter()
    painter.begin(spindlePix)
    pointRadius = 3 * sF
    painter.setPen(QColorConstants.Red)
    painter.setBrush(QColorConstants.Red)
    painter.drawEllipse(QPoint(int(leftPole[0]), int(leftPole[1])),
                        pointRadius, pointRadius)
    painter.drawEllipse(QPoint(int(rightPole[0]), int(rightPole[1])),
                        pointRadius, pointRadius)
    painter.end()

    return spindlePix

def calculateBezierPoint(lP, cP, rP):

    # Math for a 3 point Bezier Curve
    # vector formula: P = (1-t)^2 * P1 + 2(1-t)t * P2 + t^2 * P3
    # we have P, P1, and P3, and we want to know P2, so
    # P2 = ( P - (1-t)^2 * P1 - t^2 * P3 ) / ( 2(1-t)t )
    # where t is 1/2 when you have the center point P of a quadratic
    # P2 = 2 * P - (P1 + P2) / 2
    # lP is left (P1), cP is center (P), rP is right (P3)

    x = 2 * cP[0] - (lP[0] + rP[0]) / 2
    y = 2 * cP[1] - (lP[1] + rP[1]) / 2

    return (x, y)
