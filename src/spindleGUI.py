import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel,
                             QSpinBox, QTableView, QWidget, QVBoxLayout,
                             QHBoxLayout, QGridLayout, QSizePolicy,
                             QFileDialog, QSplitter, QFrame, QSpacerItem)
from PySide6.QtGui import QPixmap, QColor, QFont
from PySide6.QtCore import Qt, QDir, QAbstractTableModel
import tiffFunctions as tiffF
import threshFunctions as threshF
import curveFitData as cFD
import numpy as np

# subclass QMainWindow to create a custom MainWindow
class MainWindow(QMainWindow):

    # set up the MainWindow
    def __init__(self):

        # allow the QMainWindow to initialize
        super().__init__()

        self.setWindowTitle("Mitotic Spindle Image Analysis")
        
        # keep track of the open file name
        self.fileName = None

        # bad frames reported by the user
        self.tossedFrames = []

        # create accessible widgets
        self.importLabel = QLabel("Single Z")
        self.tiffButton = QPushButton(".tiff")

        self.totalFrameLabel = QLabel("# of Frames")
        self.totalFrameValue = QLabel("0")
        self.totalFrameValue.setAlignment(Qt.AlignRight)
        self.frameLabel = QLabel("Frame #")
        self.frameValue = QSpinBox()
        self.frameValue.setAlignment(Qt.AlignRight)
        self.frameValue.setMinimum(1)
        self.frameValue.setMaximum(1)

        self.threshLabel = QLabel("Threshold")
        self.threshValue = QSpinBox()
        self.threshValue.setAlignment(Qt.AlignRight)
        self.threshValue.setSingleStep(100)
        self.threshValue.setMinimum(0)
        self.threshValue.setMaximum(65535)
        self.threshValue.setValue(1000)

        self.gOLIterationsLabel = QLabel("GOL Iterations")
        self.gOLIterationsValue = QSpinBox()
        self.gOLIterationsValue.setAlignment(Qt.AlignRight)
        self.gOLIterationsValue.setMinimum(1)
        self.gOLIterationsValue.setMaximum(5)

        self.gOLFactorLabel = QLabel("GOL Factor")
        self.gOLFactorValue = QSpinBox()
        self.gOLFactorValue.setAlignment(Qt.AlignRight)
        self.gOLFactorValue.setMinimum(0)
        self.gOLFactorValue.setMaximum(8)
        self.gOLFactorValue.setValue(4)

        self.previewButton = QPushButton("Preview")
        self.addButton = QPushButton("Add Frame Data")
        self.tossButton = QPushButton("Toss Frame Data")
        self.tossButton.setSizePolicy(QSizePolicy.Maximum,
                                           QSizePolicy.Maximum)
        self.exportButton = QPushButton("Export Data")

        imageLabel = QLabel("Source")
        imageMap = QPixmap(tiffF.defaultPix())
        self.imagePixLabel = PixLabel()
        self.imagePixLabel.setPixmap(imageMap)

        thresholdImageLabel = QLabel("Threshold")
        threshMap = QPixmap(tiffF.defaultPix())
        self.threshPixLabel = PixLabel()
        self.threshPixLabel.setPixmap(threshMap)

        previewImageLabel = QLabel("Preview")
        previewMap = QPixmap(tiffF.defaultPix())
        self.previewPixLabel = PixLabel()
        self.previewPixLabel.setPixmap(previewMap)

        self.dataTableView = QTableView()
        self.dataTableArray = None

        imageLabels = (imageLabel, thresholdImageLabel, previewImageLabel)
        imagePixLabels = (self.imagePixLabel, self.threshPixLabel, 
                          self.previewPixLabel)
        
        imageSplitter = QSplitter()
        rightSplitter = QSplitter()
        rightSplitter.setOrientation(Qt.Vertical)

        # create section titles with modified font
        importTitle = QLabel("Import")
        thresholdTitle = QLabel("Threshold")
        dataTitle = QLabel("Record")
        imagesTitle = QLabel("Images")
        tableTitle = QLabel("Data")

        sectionTitles = (importTitle, thresholdTitle, dataTitle,
                  imagesTitle, tableTitle)

        titleFont = importTitle.font()
        titleFont.setCapitalization(QFont.AllUppercase)

        for title in sectionTitles:
            # change the font and look of the titles
            title.setStyleSheet("color:#777777")
            title.setFont(titleFont)

        # create container widgets and layouts
        centralWidget = QWidget()
        leftWidget = QWidget()
        importWidget = QWidget()
        thresholdWidget = QWidget()
        bottomLeftWidget = QWidget()
        imageWidget = QWidget()
        thresholdImageWidget = QWidget()
        previewImageWidget = QWidget()
        dataTableWidget = QWidget()

        titleSpacer = QSpacerItem(self.tossButton.sizeHint().width(),
                                  self.tossButton.sizeHint().height())

        dividingLine = QFrame()
        dividingLine.setFrameStyle(QFrame.VLine | QFrame.Raised)

        imageWidgets = (imageWidget, thresholdImageWidget, previewImageWidget)

        tempImageWidget = QWidget()
        tempHorizontal = QHBoxLayout()
        tempVertical = QVBoxLayout()
        tempGrid = QGridLayout()
        
        # place widgets in the app
        tempVertical.addWidget(importTitle)
        tempGrid.addWidget(self.importLabel, 0, 0)
        tempGrid.addWidget(self.tiffButton, 0, 1)
        importWidget.setLayout(tempGrid)
        tempGrid = QGridLayout()
        tempVertical.addWidget(importWidget)

        tempVertical.addItem(titleSpacer)
        tempVertical.addWidget(thresholdTitle)
        tempGrid.addWidget(self.totalFrameLabel, 0, 0)
        tempGrid.addWidget(self.totalFrameValue, 0, 1, Qt.AlignRight)
        tempGrid.addWidget(self.frameLabel, 1, 0)
        tempGrid.addWidget(self.frameValue, 1, 1)
        tempGrid.addWidget(self.threshLabel, 2, 0)
        tempGrid.addWidget(self.threshValue, 2, 1)
        tempGrid.addWidget(self.gOLIterationsLabel, 3, 0)
        tempGrid.addWidget(self.gOLIterationsValue, 3, 1)
        tempGrid.addWidget(self.gOLFactorLabel, 4, 0)
        tempGrid.addWidget(self.gOLFactorValue, 4, 1)
        thresholdWidget.setLayout(tempGrid)
        tempGrid = QGridLayout()
        tempVertical.addWidget(thresholdWidget)

        tempVertical.addItem(titleSpacer)
        tempVertical.addWidget(dataTitle)
        tempGrid.addWidget(self.addButton, 0, 0)
        tempGrid.addWidget(self.previewButton, 0, 1)
        tempGrid.addWidget(self.tossButton, 1, 0)
        tempGrid.addWidget(self.exportButton, 1, 1)
        bottomLeftWidget.setLayout(tempGrid)
        tempVertical.addWidget(bottomLeftWidget)
        tempVertical.addStretch()
        tempGrid = QGridLayout()
        leftWidget.setLayout(tempVertical)
        tempVertical = QVBoxLayout()

        for i in range(len(imageLabels)):
            tempVertical.addWidget(imageLabels[i],
                               alignment=Qt.AlignLeft | Qt.AlignBottom)
            tempHorizontal.setContentsMargins(0,0,0,0)
            tempHorizontal.addWidget(imagePixLabels[i], alignment=Qt.AlignLeft)
            tempImageWidget.setLayout(tempHorizontal)
            tempHorizontal = QHBoxLayout()
            tempVertical.addWidget(tempImageWidget)
            tempImageWidget = QWidget()
            tempVertical.addStretch()
            imageWidgets[i].setLayout(tempVertical)
            tempVertical = QVBoxLayout()
            imageSplitter.addWidget(imageWidgets[i])
        
        imageSplitterWidget = QWidget()
        tempVertical.addWidget(imagesTitle)
        tempVertical.addWidget(imageSplitter)
        tempVertical.addStretch()
        imageSplitterWidget.setLayout(tempVertical)
        tempVertical = QVBoxLayout()
        tempVertical.addWidget(tableTitle)
        tempVertical.addWidget(self.dataTableView)
        dataTableWidget.setLayout(tempVertical)
        tempVertical = QVBoxLayout()

        rightSplitter.addWidget(imageSplitterWidget)
        rightSplitter.addWidget(dataTableWidget)

        tempHorizontal.addWidget(leftWidget)
        tempHorizontal.addWidget(dividingLine)
        tempHorizontal.addWidget(rightSplitter, stretch=1)
        centralWidget.setLayout(tempHorizontal)
        tempHorizontal = QHBoxLayout()

        self.setCentralWidget(centralWidget)

        # set fixed button sizes
        self.tiffButton.setFixedSize(self.tossButton.sizeHint())
        self.previewButton.setFixedSize(self.tossButton.sizeHint())
        self.addButton.setFixedSize(self.tossButton.sizeHint())
        self.tossButton.setFixedSize(self.tossButton.sizeHint())
        self.exportButton.setFixedSize(self.tossButton.sizeHint())
        
        # connect signals to slots
        self.tiffButton.clicked.connect(self.onInputTiffClicked)

        self.frameValue.textChanged.connect(self.onFrameUpdate)
        self.threshValue.textChanged.connect(self.applyThreshold)
        self.gOLIterationsValue.textChanged.connect(self.applyThreshold)
        self.gOLFactorValue.textChanged.connect(self.applyThreshold)

        self.previewButton.clicked.connect(self.onPreviewClicked)
        self.addButton.clicked.connect(self.onAddDataClicked)
        self.tossButton.clicked.connect(self.onTossDataClicked)
        self.exportButton.clicked.connect(self.onExportDataClicked)

        # center window on the desktop
        def centerApplication(xSize, ySize):
            self.setGeometry(100, 100, xSize, ySize)
            qFrameRect = self.frameGeometry()
            center_point = QApplication.primaryScreen().geometry().center()
            qFrameRect.moveCenter(center_point)
            self.setGeometry(qFrameRect.topLeft().x(),
                             qFrameRect.topLeft().y(),
                             xSize, ySize)
        centerApplication(880, 450)
    
    # handle import .tiff button push
    def onInputTiffClicked(self):

        fileName, filter = QFileDialog.getOpenFileName(
                parent=self, caption='Open .tiff',
                dir=QDir.homePath(), filter='*.tiff;*.tif')
        
        # if the user selected a file successfully
        if fileName:
            self.fileName = fileName
            self.clearThreshAndPreview()
            self.frameValue.setValue(1)
            self.onFrameUpdate()
            numFrames = tiffF.framesInTiff(self.fileName)
            self.frameValue.setMaximum(numFrames)
            self.totalFrameValue.setText(str(numFrames))
            
            # create the data array and place it in the QTableView
            self.dataTableArray = np.zeros((numFrames, len(cFD.DATA_NAMES)))
            self.dataTableModel = (
                    imageTableModel(cFD.DATA_NAMES, self.dataTableArray))
            self.dataTableView.setModel(self.dataTableModel)
            self.dataTableView.resizeColumnsToContents()

            # reset input values
            self.frameValue.setValue(1)
            self.threshValue.setValue(1000)
            self.gOLIterationsValue.setValue(1)
            self.gOLFactorValue.setValue(4)

    # handle update of the frame number scroller
    def onFrameUpdate(self):
        self.clearThreshAndPreview()

        self.imagePixLabel.setPixmap(
                tiffF.pixFromTiff(self.fileName,
                                    self.frameValue.value() - 1))
        self.imagePixLabel.setImageArr(
                tiffF.arrFromTiff(self.fileName,
                                    self.frameValue.value() - 1))
        self.applyThreshold(cleared=True)

    # handle applying the threshold
    def applyThreshold(self, text="", cleared=False):
        if not cleared:
            self.clearThreshAndPreview()

        if self.fileName:
            arr = threshF.applyThreshToArr(self.imagePixLabel.imageArr,
                                            self.threshValue.value(),
                                            self.gOLIterationsValue.value(),
                                            self.gOLFactorValue.value())
            self.threshPixLabel.setPixmap(tiffF.threshPixFromArr(arr))
            self.threshPixLabel.setImageArr(arr)
    
    # handle the preview button press
    def onPreviewClicked(self):
        if self.fileName:
            self.previewPixLabel.setPixmap(tiffF.pixFromArr(
                    cFD.curveFitData(self.imagePixLabel.imageArr, 
                                 self.threshPixLabel.imageArr)))
    
    # handle the add data button press
    def onAddDataClicked(self):
        if self.fileName:
            data = (cFD.curveFitData(self.imagePixLabel.imageArr,
                                     self.threshPixLabel.imageArr,
                                     False))
        
            # add the row of data to the data table
            self.dataTableModel.beginResetModel()
            frameIndex = self.frameValue.value() - 1
            for i in range(len(data)):
                self.dataTableArray[frameIndex, i] = data[i]
            # update the table view
            self.dataTableModel.endResetModel()

            indexOfData = self.dataTableModel.createIndex(frameIndex, 0)
            self.dataTableView.scrollTo(indexOfData)

            self.frameValue.setValue(frameIndex + 2)
    
    # handle the toss data button press
    def onTossDataClicked(self):
        tossedFrame = self.frameValue.value()
        if (tossedFrame not in self.tossedFrames and self.fileName):
            self.tossedFrames.append(tossedFrame)
            self.tossedFrames.sort()
            self.dataTableModel.addTossedRow(tossedFrame)
            self.onAddDataClicked() # this follows previous lab standard

        if self.fileName:
            self.frameValue.setValue(tossedFrame + 1)

            indexOfData = self.dataTableModel.createIndex(tossedFrame - 1, 0)
            self.dataTableView.scrollTo(indexOfData)
    
    # write the data to a textfile
    def onExportDataClicked(self):
        if self.fileName:

            # prompt the user for the save location and file name
            fileName, filter = QFileDialog.getSaveFileName(
                    parent=self, caption='Export Image Data',
                    dir=QDir.homePath(), filter="*.txt")
            if not fileName:
                return None # cancel the export
            
            with open(fileName, "w", encoding="utf-8") as f:

                for column in range(self.dataTableArray.shape[1]):
                    f.write(F"{cFD.DATA_NAMES[column]}\n")

                    for row in range(self.dataTableArray.shape[0]):
                        f.write(F"{self.dataTableArray[row, column]:.4f}\n")
                
                f.write("Bad Frames\n")
                for frame in self.tossedFrames:
                    f.write(F"{frame}\n")
    
    # slot called anytime the inputs are modified
    def clearThreshAndPreview(self):
        if self.fileName:
            self.threshPixLabel.setPixmap(tiffF.defaultPix())
            self.previewPixLabel.setPixmap(tiffF.defaultPix())
        
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

        imgPolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.setSizePolicy(imgPolicy)
        self.setMinimumSize(75, 75)
        self.setFrameStyle(QFrame.Panel | QFrame.Raised)
        self.setLineWidth(2)
    
    # setter method for arr
    def setImageArr(self, arr):
        self.imageArr = arr

    # scale pixmap to label w and h, keeping pixmap aspect ratio
    def setPixmap(self, pix):
        self.pix = pix
        scaled = pix.scaled(self.size(), Qt.KeepAspectRatio)
        super().setPixmap(scaled)
    
    # rescale the pixmap when the label is resized
    def resizeEvent(self, event):
        self.setPixmap(self.pix)
        self.setAlignment(Qt.AlignCenter)
        super().resizeEvent(event)

# BOILERPLATE TABLE MODEL
class imageTableModel(QAbstractTableModel):
    def __init__(self, dataNames, data):
        super().__init__()

        self._dataNames = dataNames
        self._data = data
        self._tossedRows = []

    def addTossedRow(self, row):
        self._tossedRows.append(row)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            if self._data[index.row(), index.column()] == 0.0:
                return ""
            else:
                return "%.4f" % self._data[index.row(), index.column()]
        if role == Qt.TextAlignmentRole:
            return Qt.AlignVCenter + Qt.AlignRight
        if role == Qt.ForegroundRole:
            if (index.row() + 1) in self._tossedRows:
                return QColor("red")
    
    def rowCount(self, index):
        return self._data.shape[0]
    
    def columnCount(self, index):
        return self._data.shape[1]

    def headerData(self, section, orientation, role):
        # section is the index of the column/row.
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._dataNames[section])

            if orientation == Qt.Vertical:
                return str(section + 1)

# create and display the application if this file is being run
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()