from PIL import Image, ImageQt, ImageSequence
from PySide6.QtGui import QPixmap
import numpy as np

# returns the number of frames in a tiff image
def framesInTiff(tiffFileName):

    # turn the file into a PIL Image
    tiffImage = Image.open(tiffFileName)

    return getattr(tiffImage, "n_frames", 1)

# takes a .tiff file path and turns the image into an array
def arrFromTiff(tiffFileName, frameNum):

    # turn the file into a PIL Image
    tiffImage = Image.open(tiffFileName)

    # select the frame of the tiff using frameNum
    ims = ImageSequence.Iterator(tiffImage)
    im = ims[frameNum]

    # create the array
    return np.array(im)

# creates a normalized QPixmap from a numpy array
def pixFromArr(arr):
    # normalize the array
    temp = np.zeros(arr.shape, dtype = np.uint8)
    lowest = 100000
    highest = 0
    for i in range(0, arr.shape[0]):
        for j in range(0, arr.shape[1]):
            if arr[i][j] < lowest:
                lowest = arr[i][j]
            if arr[i][j] > highest:
                highest = arr[i][j]

    for i in range(0, arr.shape[0]):
        for j in range(0, arr.shape[1]):        
            temp[i][j] = int(255 *
                    ( (arr[i][j] - lowest) / (highest - lowest) ))

    im = Image.fromarray(temp)
    im = ImageQt.ImageQt(im)
    return QPixmap.fromImage(im)

# same as pixFromArr, but no normalization
def threshPixFromArr(arr):
    im = Image.fromarray(arr)
    im = ImageQt.ImageQt(im)
    return QPixmap.fromImage(im)

# turns a tiff file path directly into a QPixmap
def pixFromTiff(fileName, frameNum):
    return pixFromArr(arrFromTiff(fileName, frameNum))

# returns a grayscale pixmap
def defaultPix():
    array = np.arange(0, 100, 1, np.uint8)
    array = np.reshape(array, (10, 10)) 
    return pixFromArr(array)