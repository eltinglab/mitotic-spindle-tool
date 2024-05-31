import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel,
                             QSpinBox, QTableWidget, QTabWidget, QWidget, 
                             QVBoxLayout, QHBoxLayout, QGridLayout, QSizePolicy,
                             QFileDialog)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QDir
import tiffFunctions as tiffF
import threshFunctions as threshF

# subclass QMainWindow to create a custom MainWindow
class MainWindow(QMainWindow):

    # set up the MainWindow
    def __init__(self):

        # allow the QMainWindow to initialize
        super().__init__()

        self.setWindowTitle("Mitotic Spindle Image Analysis")
        
        # keep track of the open file name
        self.fileName = None

        # create accessible widgets
        self.tiffButton = QPushButton("Import .tiff")

        self.threshLabel = QLabel("Threshold")
        self.threshValue = QSpinBox()
        self.threshValue.setSingleStep(100)
        self.threshValue.setMinimum(0)
        self.threshValue.setMaximum(65535)

        self.frameLabel = QLabel("Frame #")
        self.frameValue = QSpinBox()
        self.frameValue.setMinimum(1)
        self.frameValue.setMaximum(1)

        self.previewButton = QPushButton("Preview")
        self.addButton = QPushButton("Add Frame Data")
        self.tossButton = QPushButton("Toss Frame Data")
        self.exportButton = QPushButton("Export Data")

        imageMap = QPixmap(tiffF.defaultPix())
        self.imagePixLabel = PixLabel()
        self.imagePixLabel.setPixmap(imageMap)

        threshMap = QPixmap(tiffF.defaultPix())
        self.threshPixLabel = PixLabel()
        self.threshPixLabel.setPixmap(threshMap)

        previewMap = QPixmap(tiffF.defaultPix())
        self.previewPixLabel = PixLabel()
        self.previewPixLabel.setPixmap(previewMap)

        self.dataTable = QTableWidget()

        # create container widgets and layouts
        centralWidget = QWidget()
        leftWidget = QWidget()
        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        threshWidget = QWidget()
        frameWidget = QWidget()
        bottomLeftWidget = QWidget()
        imagesWidget = QWidget()

        tempHorizontal = QHBoxLayout()
        tempVertical = QVBoxLayout()
        tempGrid = QGridLayout()
        
        # place widgets in the app
        tempVertical.addWidget(self.tiffButton)
        tempHorizontal.addWidget(self.threshLabel)
        tempHorizontal.addWidget(self.threshValue)
        threshWidget.setLayout(tempHorizontal)
        tempVertical.addWidget(threshWidget)
        tempHorizontal = QHBoxLayout()
        tempHorizontal.addWidget(self.frameLabel)
        tempHorizontal.addWidget(self.frameValue)
        frameWidget.setLayout(tempHorizontal)
        tempVertical.addWidget(frameWidget)
        tempHorizontal = QHBoxLayout()
        tempGrid.addWidget(self.addButton, 0, 0)
        tempGrid.addWidget(self.previewButton, 0, 1)
        tempGrid.addWidget(self.tossButton, 1, 0)
        tempGrid.addWidget(self.exportButton, 1, 1)
        bottomLeftWidget.setLayout(tempGrid)
        tempVertical.addWidget(bottomLeftWidget)
        tempGrid = QGridLayout()
        leftWidget.setLayout(tempVertical)
        tempVertical = QVBoxLayout()

        tempHorizontal.addWidget(self.imagePixLabel)
        tempHorizontal.addWidget(self.threshPixLabel)
        tempHorizontal.addWidget(self.previewPixLabel)
        imagesWidget.setLayout(tempHorizontal)
        tempHorizontal = QHBoxLayout()
        tabs.addTab(imagesWidget, "Images")
        tabs.addTab(self.dataTable, "Data")

        tempHorizontal.addWidget(leftWidget)
        tempHorizontal.addWidget(tabs)
        centralWidget.setLayout(tempHorizontal)
        tempHorizontal = QHBoxLayout()

        self.setCentralWidget(centralWidget)

        # connect signals to slots
        self.tiffButton.clicked.connect(self.onInputTiffClicked)
        self.threshValue.textChanged.connect(self.onThreshUpdate)
        self.frameValue.textChanged.connect(self.onFrameUpdate)
    
    # handle import .tiff button push
    def onInputTiffClicked(self):

        self.fileName, filter = QFileDialog.getOpenFileName(
                parent=self, caption='Open .tiff',
                dir=QDir.homePath(), filter='*.tiff;*.tif')
        
        # if the user selected a file successfully
        if self.fileName:
            self.onFrameUpdate()
    
    # handle update of the frame number scroller
    def onFrameUpdate(self):
        self.imagePixLabel.setPixmap(
                tiffF.pixFromTiff(self.fileName,
                                    self.frameValue.value() - 1))
        self.imagePixLabel.setImageArr(
                tiffF.arrFromTiff(self.fileName,
                                    self.frameValue.value() - 1))

        # update thresh image and the maximum allowed frame number
        self.onThreshUpdate()
        self.frameValue.setMaximum(tiffF.framesInTiff(self.fileName))
    
    # handle update of the threshold integer scroller
    def onThreshUpdate(self):
        arr = threshF.applyThreshToArr(self.imagePixLabel.imageArr,
                self.threshValue.value())
        self.threshPixLabel.setPixmap(tiffF.threshPixFromArr(arr))
        self.threshPixLabel.setImageArr(arr)
        
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
        self.setMinimumSize(100,100)
    
    # setter method for arr
    def setImageArr(self, arr):
        self.imageArr = arr

    # scale pixmap to label w and h, keeping pixmap aspect ratio
    def setPixmap(self, pix):
        self.pix = pix
        w = self.width()
        h = self.height()
        scaled = pix.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
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