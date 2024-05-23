import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel,
                             QSpinBox, QTableWidget, QTabWidget, QWidget, 
                             QVBoxLayout, QHBoxLayout, QGridLayout)
from PyQt6.QtGui import QPixmap

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

        self.imageMap = QPixmap()
        imagePixLabel = QLabel()
        imagePixLabel.setPixmap(self.imageMap)
        self.threshMap = QPixmap()
        threshPixLabel = QLabel()
        threshPixLabel.setPixmap(self.threshMap)
        self.previewMap = QPixmap()
        previewPixLabel = QLabel()
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
        leftImagesWidget = QWidget()
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
        tempGrid.addWidget(self.previewButton, 0, 0)
        tempGrid.addWidget(self.addButton, 0, 1)
        tempGrid.addWidget(self.tossButton, 1, 0)
        tempGrid.addWidget(self.exportButton, 1, 1)
        bottomLeftWidget.setLayout(tempGrid)
        tempVertical.addWidget(bottomLeftWidget)
        tempGrid = QGridLayout()
        leftWidget.setLayout(tempVertical)
        tempVertical = QVBoxLayout()

        tempVertical.addWidget(imagePixLabel)
        tempVertical.addWidget(threshPixLabel)
        leftImagesWidget.setLayout(tempVertical)
        tempVertical = QVBoxLayout()
        tempHorizontal.addWidget(leftImagesWidget)
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

# Create and display the application if this file is being run
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()