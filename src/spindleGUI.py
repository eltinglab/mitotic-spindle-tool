import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel,
                             QSpinBox, QTableWidget, QTabWidget, QWidget, 
                             QVBoxLayout, QHBoxLayout, QGridLayout, QSizePolicy,
                             QFileDialog)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QDir
import tiffFunctions as tiffF
import threshFunctions as threshF
from curveFitData import curveFitData

# subclass QMainWindow to create a custom MainWindow
class MainWindow(QMainWindow):

    # set up the MainWindow
    def __init__(self):

        # allow the QMainWindow to initialize
        super().__init__()

        self.setWindowTitle("Mitotic Spindle Image Analysis")
        
        # keep track of the open file name
        self.fileName = None

        # keep track of whether the thresholded image has been cleared
        self.threshCleared = True

        # create accessible widgets
        self.importLabel = QLabel("Import")
        self.tiffButton = QPushButton("Import .tiff")
        self.tiffButton.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        self.totalFrameLabel = QLabel("# of Frames")
        self.totalFrameValue = QLabel("0")
        self.frameLabel = QLabel("Frame #")
        self.frameValue = QSpinBox()
        self.frameValue.setMinimum(1)
        self.frameValue.setMaximum(1)

        self.threshLabel = QLabel("Threshold")
        self.threshValue = QSpinBox()
        self.threshValue.setSingleStep(100)
        self.threshValue.setMinimum(0)
        self.threshValue.setMaximum(65535)

        self.gOLIterationsLabel = QLabel("GOL Iterations")
        self.gOLIterationsValue = QSpinBox()
        self.gOLIterationsValue.setMinimum(1)
        self.gOLIterationsValue.setMaximum(5)

        self.gOLFactorLabel = QLabel("GOL Factor")
        self.gOLFactorValue = QSpinBox()
        self.gOLFactorValue.setMinimum(0)
        self.gOLFactorValue.setMaximum(8)
        self.gOLFactorValue.setValue(4)

        self.thresholdButton = QPushButton("Apply Threshold")
        self.thresholdButton.setSizePolicy(QSizePolicy.Maximum,
                                           QSizePolicy.Maximum)

        self.previewButton = QPushButton("Preview")
        self.addButton = QPushButton("Add Frame Data")
        self.tossButton = QPushButton("Toss Frame Data")
        self.exportButton = QPushButton("Export Data")

        imageLabel = QLabel("Image")
        imageMap = QPixmap(tiffF.defaultPix())
        self.imagePixLabel = PixLabel()
        self.imagePixLabel.setPixmap(imageMap)

        thresholdImageLabel = QLabel("Thresholded Image")
        threshMap = QPixmap(tiffF.defaultPix())
        self.threshPixLabel = PixLabel()
        self.threshPixLabel.setPixmap(threshMap)

        previewImageLabel = QLabel("Preview")
        previewMap = QPixmap(tiffF.defaultPix())
        self.previewPixLabel = PixLabel()
        self.previewPixLabel.setPixmap(previewMap)

        self.dataTable = QTableWidget()

        # create container widgets and layouts
        centralWidget = QWidget()
        leftWidget = QWidget()
        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        importWidget = QWidget()
        thresholdWidget = QWidget()
        bottomLeftWidget = QWidget()
        imageWidget = QWidget()
        thresholdImageWidget = QWidget()
        previewImageWidget = QWidget()
        imagesWidget = QWidget()

        tempHorizontal = QHBoxLayout()
        tempVertical = QVBoxLayout()
        tempGrid = QGridLayout()
        
        # place widgets in the app
        tempGrid.addWidget(self.importLabel, 0, 0)
        tempGrid.addWidget(self.tiffButton, 0, 1)
        importWidget.setLayout(tempGrid)
        tempGrid = QGridLayout()
        tempVertical.addWidget(importWidget)
        tempVertical.addStretch() # add stretch spacer
        tempGrid.addWidget(self.totalFrameLabel, 0, 0)
        tempGrid.addWidget(self.totalFrameValue, 0, 1, Qt.AlignLeft)
        tempGrid.addWidget(self.frameLabel, 1, 0)
        tempGrid.addWidget(self.frameValue, 1, 1)
        tempGrid.addWidget(self.threshLabel, 2, 0)
        tempGrid.addWidget(self.threshValue, 2, 1)
        tempGrid.addWidget(self.gOLIterationsLabel, 3, 0)
        tempGrid.addWidget(self.gOLIterationsValue, 3, 1)
        tempGrid.addWidget(self.gOLFactorLabel, 4, 0)
        tempGrid.addWidget(self.gOLFactorValue, 4, 1)
        tempGrid.addWidget(self.thresholdButton, 5, 1)
        thresholdWidget.setLayout(tempGrid)
        tempGrid = QGridLayout()
        tempVertical.addWidget(thresholdWidget)
        tempVertical.addStretch() # add stretch spacer
        tempGrid.addWidget(self.addButton, 0, 0)
        tempGrid.addWidget(self.previewButton, 0, 1)
        tempGrid.addWidget(self.tossButton, 1, 0)
        tempGrid.addWidget(self.exportButton, 1, 1)
        bottomLeftWidget.setLayout(tempGrid)
        tempVertical.addWidget(bottomLeftWidget)
        tempGrid = QGridLayout()
        leftWidget.setLayout(tempVertical)
        tempVertical = QVBoxLayout()

        tempVertical.addWidget(imageLabel, 10, Qt.AlignHCenter)
        tempVertical.addWidget(self.imagePixLabel, 90)
        imageWidget.setLayout(tempVertical)
        tempVertical = QVBoxLayout()
        tempVertical.addWidget(thresholdImageLabel, 10, Qt.AlignHCenter)
        tempVertical.addWidget(self.threshPixLabel, 90)
        thresholdImageWidget.setLayout(tempVertical)
        tempVertical = QVBoxLayout()
        tempVertical.addWidget(previewImageLabel, 10, Qt.AlignHCenter)
        tempVertical.addWidget(self.previewPixLabel, 90)
        previewImageWidget.setLayout(tempVertical)
        tempVertical = QVBoxLayout()
        tempHorizontal.addWidget(imageWidget)
        tempHorizontal.addWidget(thresholdImageWidget)
        tempHorizontal.addWidget(previewImageWidget)
        imagesWidget.setLayout(tempHorizontal)
        tempHorizontal = QHBoxLayout()
        
        tabs.addTab(imagesWidget, "Images")
        tabs.addTab(self.dataTable, "Data")

        tempHorizontal.addWidget(leftWidget)
        tempHorizontal.addWidget(tabs)
        centralWidget.setLayout(tempHorizontal)
        tempHorizontal = QHBoxLayout()

        self.setCentralWidget(centralWidget)

        # set fixed button sizes
        self.tiffButton.setFixedSize(self.thresholdButton.sizeHint())
        self.previewButton.setFixedSize(self.thresholdButton.sizeHint())
        self.addButton.setFixedSize(self.thresholdButton.sizeHint())
        self.tossButton.setFixedSize(self.thresholdButton.sizeHint())
        self.exportButton.setFixedSize(self.thresholdButton.sizeHint())
        
        # connect signals to slots
        self.tiffButton.clicked.connect(self.onInputTiffClicked)
        self.thresholdButton.clicked.connect(self.applyThreshold)
        self.frameValue.textChanged.connect(self.onFrameUpdate)
        self.previewButton.clicked.connect(self.onPreviewClicked)

        self.frameValue.textChanged.connect(self.clearThreshImage)
        self.threshValue.textChanged.connect(self.clearThreshImage)
        self.gOLIterationsValue.textChanged.connect(self.clearThreshImage)
        self.gOLFactorValue.textChanged.connect(self.clearThreshImage)
    
    # handle import .tiff button push
    def onInputTiffClicked(self):

        self.fileName, filter = QFileDialog.getOpenFileName(
                parent=self, caption='Open .tiff',
                dir=QDir.homePath(), filter='*.tiff;*.tif')
        
        # if the user selected a file successfully
        if self.fileName:
            self.onFrameUpdate()
            numFrames = tiffF.framesInTiff(self.fileName)
            self.frameValue.setMaximum(numFrames)
            self.totalFrameValue.setText(str(numFrames))

            # reset input values and clear thresholded image
            self.frameValue.setValue(1)
            self.threshValue.setValue(0)
            self.gOLIterationsValue.setValue(1)
            self.gOLFactorValue.setValue(4)
            if not self.threshCleared:
                self.threshPixLabel.setPixmap(tiffF.defaultPix())
                self.threshCleared = True

    # handle update of the frame number scroller
    def onFrameUpdate(self):

        self.imagePixLabel.setPixmap(
                tiffF.pixFromTiff(self.fileName,
                                    self.frameValue.value() - 1))
        self.imagePixLabel.setImageArr(
                tiffF.arrFromTiff(self.fileName,
                                    self.frameValue.value() - 1))

    # handle applying the threshold
    def applyThreshold(self):
        if self.imagePixLabel.imageArr is not None:

            arr = threshF.applyThreshToArr(self.imagePixLabel.imageArr,
                                           self.threshValue.value(),
                                           self.gOLIterationsValue.value(),
                                           self.gOLFactorValue.value())
            self.threshPixLabel.setPixmap(tiffF.threshPixFromArr(arr))
            self.threshPixLabel.setImageArr(arr)

            self.threshCleared = False

        # take focus away from the text fields
        self.setFocus()
    
    # handle the preview button press
    def onPreviewClicked(self):
        if not self.threshCleared:
            self.previewPixLabel.setPixmap(tiffF.threshPixFromArr(
                    curveFitData(self.imagePixLabel.imageArr, 
                                 self.threshPixLabel.imageArr)))
    
    # slot called anytime the inputs are modified
    def clearThreshImage(self):
        if not self.threshCleared:
            self.threshPixLabel.setPixmap(tiffF.defaultPix())
            self.threshCleared = True
        
# QLabel for keeping the contained pixmap scaled correctly
class PixLabel(QLabel):

    # set up the PixLabel
    def __init__(self):

        # allow the QLabel to initialize itself
        super().__init__()

        # define a class pixmap variable
        self.pix = None

        # define a class pixArray variable
        self.imageArr = None

        imgPolicy = QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.setSizePolicy(imgPolicy)
        self.setMinimumSize(150, 150)
    
    # setter method for arr
    def setImageArr(self, arr):
        self.imageArr = arr

    # scale pixmap to label w and h, keeping pixmap aspect ratio
    def setPixmap(self, pix):
        self.pix = pix
        w = self.width()
        h = self.height()
        scaled = pix.scaled(w, h, Qt.KeepAspectRatio)
        super().setPixmap(scaled)
    
    # rescale the pixmap when the label is resized
    def resizeEvent(self, event):
        self.setPixmap(self.pix)
        self.setAlignment(Qt.AlignCenter)
        super().resizeEvent(event)

# create and display the application if this file is being run
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()