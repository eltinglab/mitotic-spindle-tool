import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel,
                             QSpinBox, QTableWidget, QTabWidget, QWidget, 
                             QVBoxLayout, QHBoxLayout, QGridLayout, QFrame,
                             QSizePolicy)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
import tiffFunctions as tiffF

# subclass QMainWindow to create a custom MainWindow
class MainWindow(QMainWindow):

    # set up the MainWindow
    def __init__(self):

        # allow the QMainWindow to initialize
        super().__init__()

        self.setWindowTitle("Mitotic Spindle Image Analysis")

        # create accessible widgets
        self.tiffButton = QPushButton("Import .tiff")
        self.threshLabel = QLabel("Threshold")
        self.threshValue = QSpinBox()
        self.frameLabel = QLabel("Frame #")
        self.frameValue = QSpinBox()

        self.previewButton = QPushButton("Preview")
        self.addButton = QPushButton("Add Frame Data")
        self.tossButton = QPushButton("Toss Frame Data")
        self.exportButton = QPushButton("Export Data")

        

        self.imageMap = QPixmap(tiffF.defaultPix())
        imagePixLabel = PixLabel()
        imagePixLabel.setPixmap(self.imageMap)

        self.threshMap = QPixmap(tiffF.defaultPix())
        threshPixLabel = PixLabel()
        threshPixLabel.setPixmap(self.threshMap)

        self.previewMap = QPixmap(tiffF.defaultPix())
        previewPixLabel = PixLabel()
        previewPixLabel.setPixmap(self.previewMap)

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

        tempHorizontal.addWidget(imagePixLabel)
        tempHorizontal.addWidget(threshPixLabel)
        tempHorizontal.addWidget(previewPixLabel)
        imagesWidget.setLayout(tempHorizontal)
        tempHorizontal = QHBoxLayout()
        tabs.addTab(imagesWidget, "Images")
        tabs.addTab(self.dataTable, "Data")

        tempHorizontal.addWidget(leftWidget)
        tempHorizontal.addWidget(tabs)
        centralWidget.setLayout(tempHorizontal)
        tempHorizontal = QHBoxLayout()

        self.setCentralWidget(centralWidget)

# QLabel for keeping the contained pixmap scaled correctly
class PixLabel(QLabel):

    # set up the PixLabel
    def __init__(self):

        # allow the QLabel to initialize itself
        super().__init__()

        # define a class pixmap variable
        self.pix = None

        # TODO find a way to keep the frame tight, not freeze max window
        #self.setFrameStyle(QFrame.Panel | QFrame.Raised)
        imgPolicy = QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.setSizePolicy(imgPolicy)
        self.setMinimumSize(100,100)

    # scale pixmap to label w and h, keeping pixmap aspect ratio
    def setPixmap(self, pix):
        self.pix = pix
        w = self.width()
        h = self.height()
        scaled = pix.scaled(w, 
                            h, 
                            Qt.KeepAspectRatio, 
                            Qt.SmoothTransformation)
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