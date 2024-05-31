import numpy as np

# applys a threshold to an image array
def applyThreshToArr(arr, thresh):

    # these may be turned into buttons later
    gOLFactor = 4
    gOLIter = 1

    output = arr > thresh

    # TODO fix slicing not working vertically
    # output[0][:] = 0
    # output[:][0] = 0
    # output[len(output) - 1][:] = 0
    # output[:][len(output) - 1] = 0

    return output

    # TODO fix array splicing so that the game of life works
    # play game of life with the thresholded image
    # temp = np.full(output.shape, True)
    # for i in range(0, gOLIter):
    #     for r in range(1, len(output) - 1):
    #         for c in range(1, len(output[r]) - 1):
    #             if np.sum(output[r-1:r+2][c-1:c+2]) < gOLFactor:
    #                 temp[r][c] = False
    # return temp