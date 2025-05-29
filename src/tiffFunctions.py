from PIL import Image, ImageQt, ImageSequence
from PySide6.QtGui import QPixmap
from numpy import array, zeros, ones, reshape, uint8

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
    return array(im)

# creates a normalized QPixmap from a numpy array
def pixFromArr(arr):
    # normalize the array
    temp = zeros(arr.shape, dtype = uint8)
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
def defaultPix(backShade):
    array = ones(4, dtype=uint8)
    array = reshape(array, (2, 2))
    array *= backShade
    return threshPixFromArr(array)

# returns a black array with a white X for thresholds with no objects
def threshXArr():
    side = 100
    sM1 = side - 1
    array = zeros((side,side))
    for i in range(1, sM1):
        array[i - 1 : i + 2, i - 1 : i + 2] = 1
        array[sM1 - i - 1 : sM1 - i + 2, i - 1 : i + 2] = 1
    return array

# extracts and returns TIFF metadata as a dictionary
def getTiffMetadata(tiffFileName):
    """
    Extract metadata from a TIFF file.
    Returns a dictionary with available metadata information.
    """
    try:
        tiffImage = Image.open(tiffFileName)
        
        metadata = {}
        
        # Basic image information
        metadata['Filename'] = tiffFileName.split('/')[-1] if '/' in tiffFileName else tiffFileName.split('\\')[-1]
        metadata['Format'] = tiffImage.format
        metadata['Mode'] = tiffImage.mode
        metadata['Size'] = f"{tiffImage.size[0]} x {tiffImage.size[1]} pixels"
        metadata['Number of Frames'] = getattr(tiffImage, "n_frames", 1)
        
        # EXIF data if available
        if hasattr(tiffImage, '_getexif') and tiffImage._getexif() is not None:
            exif_data = tiffImage._getexif()
            for tag, value in exif_data.items():
                metadata[f'EXIF_{tag}'] = str(value)
        
        # TIFF tags
        if hasattr(tiffImage, 'tag') and tiffImage.tag is not None:
            for tag, value in tiffImage.tag.items():
                tag_name = f"Tag_{tag}"
                if isinstance(value, (list, tuple)) and len(value) == 1:
                    metadata[tag_name] = str(value[0])
                else:
                    metadata[tag_name] = str(value)
        
        # ImageJ specific metadata if present
        if hasattr(tiffImage, 'tag_v2'):
            # ImageJ uses tag 270 for ImageDescription
            if 270 in tiffImage.tag_v2:
                imagej_info = tiffImage.tag_v2[270]
                if imagej_info and 'ImageJ' in str(imagej_info):
                    metadata['ImageJ_Info'] = str(imagej_info)
            
            # Software tag (tag 305)
            if 305 in tiffImage.tag_v2:
                metadata['Software'] = str(tiffImage.tag_v2[305])
            
            # Resolution tags
            if 282 in tiffImage.tag_v2:  # X Resolution
                metadata['X_Resolution'] = str(tiffImage.tag_v2[282])
            if 283 in tiffImage.tag_v2:  # Y Resolution  
                metadata['Y_Resolution'] = str(tiffImage.tag_v2[283])
            if 296 in tiffImage.tag_v2:  # Resolution Unit
                res_unit = tiffImage.tag_v2[296]
                unit_names = {1: 'No unit', 2: 'Inch', 3: 'Centimeter'}
                metadata['Resolution_Unit'] = unit_names.get(res_unit, f'Unknown ({res_unit})')
        
        # Check for additional info
        if hasattr(tiffImage, 'info') and tiffImage.info:
            for key, value in tiffImage.info.items():
                metadata[f'Info_{key}'] = str(value)
                
        return metadata
        
    except Exception as e:
        return {'Error': f'Failed to read metadata: {str(e)}'}