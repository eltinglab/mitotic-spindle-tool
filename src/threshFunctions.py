import numpy as np

# applies a threshold to an image array
def applyThreshToArr(arr, thresh, gOLI, gOLF):

    # game of life factor and number of iterations
    gOLFactor = gOLF
    gOLIterations = gOLI

    # apply the initial threshold
    output = arr > thresh

    # set the outsides of the image to False
    output[0, :] = False
    output[:, 0] = False
    output[len(output) - 1, :] = False
    output[:, len(output[0]) - 1] = False

    # play game of life with the thresholded image
    for i in range(0, gOLIterations):
        for r in range(1, len(output) - 1):
            for c in range(1, len(output[r]) - 1):
                if (np.sum(output[r-1:r+2, c-1:c+2]) < gOLFactor):
                    output[r][c] = False

    return output