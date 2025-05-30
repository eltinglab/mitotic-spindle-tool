import sys
import os

# Handle PyInstaller frozen executable
if getattr(sys, 'frozen', False):
    # We're running in a PyInstaller bundle
    bundle_dir = sys._MEIPASS
    src_dir = os.path.join(bundle_dir, 'src')
    
    # Add src directory to Python path if it exists
    if os.path.exists(src_dir) and src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    
    # Also add the bundle directory
    if bundle_dir not in sys.path:
        sys.path.insert(0, bundle_dir)

from PySide6.QtWidgets import (QApplication, QCheckBox, QMainWindow, QPushButton, QLabel,
                               QSpinBox, QTableView, QWidget, QVBoxLayout,
                               QHBoxLayout, QGridLayout, QSizePolicy,
                               QFileDialog, QSplitter, QFrame, QSplitterHandle,
                               QAbstractItemView, QDialog)
from PySide6.QtGui import (QPixmap, QFont, QPainter, QBrush, QGradient,
                           QTransform, QKeyEvent, QIcon)
from PySide6.QtCore import Qt, QDir, QAbstractTableModel, QEvent

# Import local modules with error handling
try:
    import tiffFunctions as tiffF
    import threshFunctions as threshF
    import curveFitData as cFD
    import plotSpindle as pS
    import plotDialog as pD
    import manualSpindleDialog as mSD
    import metadataDialog as mdD
    from version import VERSION_DISPLAY
except ImportError as e:
    print(f"[ERROR] Failed to import required module: {e}")
    print(f"[DEBUG] Python path: {sys.path}")
    print(f"[DEBUG] Current working directory: {os.getcwd()}")
    if getattr(sys, 'frozen', False):
        print(f"[DEBUG] PyInstaller bundle directory: {sys._MEIPASS}")
        print(f"[DEBUG] Bundle contents: {os.listdir(sys._MEIPASS)}")
        src_dir = os.path.join(sys._MEIPASS, 'src')
        if os.path.exists(src_dir):
            print(f"[DEBUG] src directory contents: {os.listdir(src_dir)}")
    raise

# Force PyInstaller to include all required modules
# These imports ensure PyInstaller detects and includes these modules
try:
    import keypress_method
    import spindlePreviewDialog
    # Re-import all modules to ensure they're included
    import metadataDialog
    import manualSpindleDialog
    import plotDialog
    import plotSpindle
    import curveFitData
    import threshFunctions
    import tiffFunctions
    import version
except ImportError as e:
    print(f"[WARNING] Could not import module: {e}")

import os
from numpy import zeros, arange
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False

# subclass QMainWindow to create a custom MainWindow
class MainWindow(QMainWindow):

    # set up the MainWindow
    def __init__(self):

        # allow the QMainWindow to initialize
        super().__init__()

        self.setWindowTitle("Mitotic Spindle Image Analysis")
        
        # Set the application icon for window, taskbar, etc.
        self.setApplicationIcon()
        
        # Update the version for new releases
        versionNumber = VERSION_DISPLAY
        
        # keep track of the open file name
        self.fileName = None

        # bad frames reported by the user
        self.tossedFrames = []

        # record whether it is starting in light or dark mode
        self.isDarkMode = self.isComputerDarkMode()   
        
        # keep track of whether the preview is the default or not
        self.isPreviewCleared = True
        
        # Store manual override data
        self.manual_override_active = False
        self.manual_left_pole = None
        self.manual_right_pole = None
        
        # Enable keyboard focus for key events
        self.setFocusPolicy(Qt.StrongFocus)
        
        # Enhanced focus management for AppImage compatibility
        self.activateWindow()
        self.raise_()
        
        # Add a status bar to show keyboard shortcuts
        self.statusBar().showMessage("Keyboard Controls: ← Toss | → Add | ↑/↓ Threshold ±10 | W/S GOL Iterations ±1 | A/D GOL Factor ±1 | Space Preview | M Manual | E Export")

        # create accessible widgets
        self.importLabel = QLabel("Single Z")
        self.tiffButton = QPushButton(".tiff")
        self.metadataButton = QPushButton("Metadata Info")
        self.metadataButton.setEnabled(False)  # Initially disabled until TIFF is loaded

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
        self.threshValue.setSingleStep(50)
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

        self.addButton = QPushButton("Add")
        self.tossButton = QPushButton("Toss")
        self.previewButton = QPushButton("Preview")
        self.manualButton = QPushButton("Manual Override")
        
        self.tossButton.setSizePolicy(QSizePolicy.Maximum,
                                           QSizePolicy.Maximum)
        self.exportButton = QPushButton("Export")
        self.runAllFramesButton = QPushButton("Run All Frames")

        self.dataTableView = QTableView()
        self.dataTableView.setSelectionMode(QAbstractItemView.SingleSelection)
        self.dataTableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.dataTableView.clicked.connect(self.onDataTableClicked)
        self.dataTableView.horizontalHeader().sectionClicked.connect(self.onColumnHeaderClicked)
        self.dataTableArray = None
        
        # Hotkeys information
        self.hotkeysLabel = QLabel("Created by the Elting Lab\n github.com/EltingLab")
        self.hotkeysLabel.setWordWrap(True)
        self.hotkeysLabel.setStyleSheet("color: #777777; font-size: 9pt;")

        self.backShade = self.dataTableView.palette().base().color().value()

        imageLabel = QLabel("Source")
        imageMap = QPixmap(tiffF.defaultPix(self.backShade))
        self.imagePixLabel = PixLabel()
        self.imagePixLabel.setPixmap(imageMap)

        thresholdImageLabel = QLabel("Threshold")
        threshMap = QPixmap(tiffF.defaultPix(self.backShade))
        self.threshPixLabel = PixLabel()
        self.threshPixLabel.setPixmap(threshMap)

        previewImageLabel = QLabel("Preview")
        previewMap = QPixmap(tiffF.defaultPix(self.backShade))
        self.previewPixLabel = PixLabel()
        self.previewPixLabel.setPixmap(previewMap)

        imageLabels = (imageLabel, thresholdImageLabel, previewImageLabel)
        imagePixLabels = (self.imagePixLabel, self.threshPixLabel, 
                          self.previewPixLabel)
        
        imageSplitter = SplitterWithHandles(Qt.Horizontal)
        rightSplitter = SplitterWithHandles(Qt.Vertical)

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

        # version number (could move this up to a menu in the future)
        versionLabel = QLabel(versionNumber)
        versionLabel.setStyleSheet("color:#777777")

        # set default size hint for buttons and spacing
        # based off of QButton with the text "Toss Frame Data"
        defaultSize = QPushButton("Toss Frame Data").sizeHint()

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
        tempGrid.addWidget(self.metadataButton, 1, 0, 1, 2)  # Span across both columns
        importWidget.setLayout(tempGrid)
        tempGrid = QGridLayout()
        tempVertical.addWidget(importWidget)

        tempVertical.addSpacing(defaultSize.height())
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

        tempVertical.addSpacing(defaultSize.height())
        tempVertical.addWidget(dataTitle)
        tempGrid.addWidget(self.addButton, 0, 0)
        tempGrid.addWidget(self.tossButton, 0, 1)
        tempGrid.addWidget(self.previewButton, 1, 0)
        tempGrid.addWidget(self.manualButton, 1, 1)
        tempGrid.addWidget(self.runAllFramesButton, 2, 0)
        tempGrid.addWidget(self.exportButton, 2, 1)
        bottomLeftWidget.setLayout(tempGrid)
        tempVertical.addWidget(bottomLeftWidget)
        tempVertical.addWidget(self.hotkeysLabel)
        tempVertical.addStretch()
        tempVertical.addWidget(versionLabel)
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
        self.tiffButton.setFixedSize(defaultSize)
        self.metadataButton.setFixedSize(defaultSize)
        self.previewButton.setFixedSize(defaultSize)
        self.manualButton.setFixedSize(defaultSize)
        self.addButton.setFixedSize(defaultSize)
        self.tossButton.setFixedSize(defaultSize)
        self.exportButton.setFixedSize(defaultSize)
        self.runAllFramesButton.setFixedSize(defaultSize)

        # connect signals to slots
        self.tiffButton.clicked.connect(self.onInputTiffClicked)
        self.metadataButton.clicked.connect(self.onMetadataClicked)

        self.frameValue.textChanged.connect(self.onFrameUpdate)
        self.threshValue.textChanged.connect(self.applyThreshold)
        self.gOLIterationsValue.textChanged.connect(self.applyThreshold)
        self.gOLFactorValue.textChanged.connect(self.applyThreshold)

        self.previewButton.clicked.connect(self.onPreviewClicked)
        self.manualButton.clicked.connect(self.onManualOverrideClicked)
        self.addButton.clicked.connect(self.onAddDataClicked)
        self.tossButton.clicked.connect(self.onTossDataClicked)
        self.exportButton.clicked.connect(self.onExportDataClicked)
        self.runAllFramesButton.clicked.connect(self.onRunAllFramesClicked)

        # center window on the desktop
        def centerApplication(xSize, ySize):
            self.setGeometry(100, 100, xSize, ySize)
            qFrameRect = self.frameGeometry()
            center_point = QApplication.primaryScreen().geometry().center()
            qFrameRect.moveCenter(center_point)
            self.setGeometry(qFrameRect.topLeft().x(),
                             qFrameRect.topLeft().y(),
                             xSize, ySize)
        centerApplication(770, 450)
    
    def setApplicationIcon(self):
        """Set the application icon for window, taskbar, and dock"""
        try:
            # Determine the correct icon path based on execution environment
            if getattr(sys, 'frozen', False):
                # Running in a PyInstaller bundle
                base_path = sys._MEIPASS
                icon_path = os.path.join(base_path, 'icons', 'EltingLabSpindle.ico')
            else:
                # Running in normal Python environment
                icon_path = 'icons/EltingLabSpindle.ico'
            
            if os.path.exists(icon_path):
                icon = QIcon(icon_path)
                if not icon.isNull():
                    # Set window icon for all platforms (title bar, taskbar, dock)
                    self.setWindowIcon(icon)
                    # Also set the application icon globally
                    QApplication.instance().setWindowIcon(icon)
                    print(f"[SUCCESS] Application icon set successfully: {icon_path}")
                    return
            
            print(f"⚠️ Warning: Could not find application icon file at: {icon_path}")
            
        except Exception as e:
            print(f"⚠️ Warning: Failed to set application icon: {e}")
    
    # handle import .tiff button push
    def onInputTiffClicked(self):

        fileName, filter = QFileDialog.getOpenFileName(
                parent=self, caption='Open .tiff',
                dir=QDir.homePath())
        
        # if the user selected a file successfully
        if fileName:
            self.fileName = fileName
            self.clearThreshAndPreview()
            self.frameValue.setValue(1)
            self.onFrameUpdate()
            numFrames = tiffF.framesInTiff(self.fileName)
            self.frameValue.setMaximum(numFrames)
            self.totalFrameValue.setText(str(numFrames))
            
            # Enable metadata button now that a TIFF is loaded
            self.metadataButton.setEnabled(True)
            
            # create the data array and place it in the QTableView
            self.dataTableArray = zeros((numFrames, len(cFD.DATA_NAMES)))
            self.dataTableModel = (
                    ImageTableModel(cFD.DATA_NAMES, self.dataTableArray))
            self.dataTableView.setModel(self.dataTableModel)
            self.dataTableView.resizeColumnsToContents()

            # reset the tossed frames for the new image
            self.tossedFrames = []

            # reset input values
            self.frameValue.setValue(1)
            self.threshValue.setValue(1000)
            self.gOLIterationsValue.setValue(1)
            self.gOLFactorValue.setValue(4)

    # handle metadata info button press
    def onMetadataClicked(self):
        """Show metadata information for the currently loaded TIFF file"""
        if self.fileName:
            try:
                # Create and show the metadata dialog
                metadata_dialog = mdD.MetadataDialog(self.fileName, self)
                metadata_dialog.exec()
            except Exception as e:
                # Handle any errors in creating the dialog
                self.statusBar().showMessage(f"Error displaying metadata: {str(e)}", 5000)

    # handle update of the frame number scroller
    def onFrameUpdate(self):
        self.clearThreshAndPreview()

        # Store the original image array for use in both display and overlay
        imageArr = tiffF.arrFromTiff(self.fileName, self.frameValue.value() - 1)
        self.imagePixLabel.setPixmap(tiffF.pixFromArr(imageArr))
        self.imagePixLabel.setImageArr(imageArr)
        
        # Automatically apply threshold to show the thresholded image
        self.applyThreshold(cleared=True)
        
        # Automatically generate preview for immediate feedback
        self.onPreviewClicked()

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
            
            # Automatically update the preview when threshold changes
            self.onPreviewClicked()
    
    # handle the preview button press
    def onPreviewClicked(self):
        if self.fileName:
            if self.manual_override_active:
                # Use manual pole positions to create preview
                spindlePlotData, doesSpindleExist = cFD.spindlePlotManual(
                    self.imagePixLabel.imageArr,
                    self.threshPixLabel.imageArr,
                    self.manual_left_pole,
                    self.manual_right_pole
                )
            else:
                # Use automatic detection
                spindlePlotData, doesSpindleExist = (
                        cFD.spindlePlot(self.imagePixLabel.imageArr, 
                                        self.threshPixLabel.imageArr))
            
            # Draw on preview image
            previewPixmap = pS.plotSpindle(spindlePlotData, doesSpindleExist)
            self.previewPixLabel.setPixmap(previewPixmap)
            
            # Also draw same data on original image for comparison
            originalWithOverlay = pS.plotSpindleOnOriginal(self.imagePixLabel.imageArr, 
                                                          spindlePlotData, 
                                                          doesSpindleExist)
            self.imagePixLabel.setPixmap(originalWithOverlay, False)
            
            self.isPreviewCleared = False
    
    # handle manual override button press
    def onManualOverrideClicked(self):
        if self.fileName and hasattr(self, 'imagePixLabel') and hasattr(self, 'threshPixLabel'):
            if self.imagePixLabel.imageArr is not None and self.threshPixLabel.imageArr is not None:
                # Create and show the manual override dialog
                manual_dialog = mSD.ManualSpindleDialog(
                    self, 
                    self.imagePixLabel.imageArr, 
                    self.threshPixLabel.imageArr
                )
                
                # Connect the signal to handle manual position updates
                manual_dialog.manual_positions_changed.connect(self.on_manual_positions_changed)
                
                # Show the dialog
                manual_dialog.exec()
    
    def on_manual_positions_changed(self, left_pole, right_pole):
        """Handle manual pole position updates from the dialog"""
        self.manual_override_active = True
        self.manual_left_pole = left_pole
        self.manual_right_pole = right_pole
        
        # Update the preview with manual positions
        self.onPreviewClicked()
        
        # Update the status bar to indicate manual override is active
        self.statusBar().showMessage("Manual override active - pole positions manually set", 3000)
    
    # handle the add data button press
    def onAddDataClicked(self):

        if self.fileName:
            if self.manual_override_active:
                # Use manual override measurements
                data, doesSpindleExist = cFD.spindleMeasurementsManual(
                    self.imagePixLabel.imageArr,
                    self.threshPixLabel.imageArr,
                    self.manual_left_pole,
                    self.manual_right_pole
                )
            else:
                # Use automatic detection
                data, doesSpindleExist = (cFD.spindleMeasurements(
                                                self.imagePixLabel.imageArr,
                                                self.threshPixLabel.imageArr))

            if doesSpindleExist:
                # add the row of data to the data table
                self.dataTableModel.beginResetModel()
                frameIndex = self.frameValue.value() - 1
                for i in range(len(data)):
                    self.dataTableArray[frameIndex, i] = data[i]
                # update the table view
                self.dataTableModel.endResetModel()

                indexOfData = self.dataTableModel.createIndex(frameIndex, 0)
                self.dataTableView.scrollTo(indexOfData)
                
                # Calculate next frame, but don't exceed total frames
                nextFrame = min(frameIndex + 2, int(self.totalFrameValue.text()))
                self.frameValue.setValue(nextFrame)
                
                # Automatically generate preview for the next image
                self.onPreviewClicked()
    
    # handle the toss data button press
    def onTossDataClicked(self):
        tossedFrame = self.frameValue.value()
        if (tossedFrame not in self.tossedFrames and self.fileName):
            self.tossedFrames.append(tossedFrame)
            self.tossedFrames.sort()
            self.dataTableModel.addTossedRow(tossedFrame)
        elif (tossedFrame in self.tossedFrames and self.fileName):
            # "un-tosses" the frame
            self.tossedFrames.remove(tossedFrame)
            self.dataTableModel.removeTossedRow(tossedFrame)

        if self.fileName:
            # Update the data table view
            indexOfData = self.dataTableModel.createIndex(tossedFrame - 1, 0)
            self.dataTableView.scrollTo(indexOfData)
            
            # Calculate next frame, but don't exceed total frames
            nextFrame = min(tossedFrame + 1, int(self.totalFrameValue.text()))
            self.frameValue.setValue(nextFrame)
            
            # Automatically generate preview for the next image
            self.onPreviewClicked()
    
    # write the data to a textfile, CSV, or Excel file
    def onExportDataClicked(self):
        if self.fileName:
            # Generate default filename based on the imported TIFF file
            import os
            base_name = os.path.splitext(os.path.basename(self.fileName))[0]
            default_name = f"{base_name}_data.txt"
            
            # Use the directory of the TIFF file as the default directory
            default_dir = os.path.dirname(self.fileName)
            default_path = os.path.join(default_dir, default_name)

            # prompt the user for the save location and file name with multiple format options
            fileName, filter = QFileDialog.getSaveFileName(
                    parent=self, caption='Export Image Data',
                    dir=default_path, 
                    filter="Text files (*.txt);;CSV files (*.csv);;Excel files (*.xlsx)")
            if not fileName:
                return None # cancel the export
            
            # Auto-append file extension if not present and update filename for format
            if filter == "CSV files (*.csv)":
                if not fileName.lower().endswith('.csv'):
                    # Replace .txt extension with .csv if present, otherwise just add .csv
                    if fileName.lower().endswith('.txt'):
                        fileName = fileName[:-4] + '.csv'
                    else:
                        fileName += '.csv'
            elif filter == "Excel files (*.xlsx)":
                if not fileName.lower().endswith('.xlsx'):
                    # Replace .txt extension with .xlsx if present, otherwise just add .xlsx
                    if fileName.lower().endswith('.txt'):
                        fileName = fileName[:-4] + '.xlsx'
                    else:
                        fileName += '.xlsx'
            elif filter == "Text files (*.txt)":
                if not fileName.lower().endswith('.txt'):
                    fileName += '.txt'
            
            # Determine the export format based on the selected filter or file extension
            if filter == "CSV files (*.csv)" or fileName.lower().endswith('.csv'):
                self._export_csv(fileName)
            elif filter == "Excel files (*.xlsx)" or fileName.lower().endswith('.xlsx'):
                self._export_excel(fileName)
            else:
                # Default to original text format (unchanged from original implementation)
                self._export_text(fileName)
    
    def _export_text(self, fileName):
        """Export data in the original text format - unchanged from original implementation"""
        with open(fileName, "w", encoding="utf-8") as f:
            for column in range(self.dataTableArray.shape[1]):
                f.write(F"{cFD.DATA_NAMES[column]}\n")
                for row in range(self.dataTableArray.shape[0]):
                    f.write(F"{self.dataTableArray[row, column]:.4f}\n")
            
            f.write("Bad Frames\n")
            for frame in self.tossedFrames:
                f.write(F"{frame}\n")
    
    def _export_csv(self, fileName):
        """Export data in CSV format"""
        try:
            # Create DataFrame with measurement data
            df = pd.DataFrame(self.dataTableArray, columns=cFD.DATA_NAMES)
            
            # Add frame numbers as the first column
            df.insert(0, 'Frame', range(1, len(df) + 1))
            
            # Mark tossed frames
            df['Tossed'] = df['Frame'].isin(self.tossedFrames)
            
            # Save to CSV
            df.to_csv(fileName, index=False, float_format='%.4f')
            
            self.statusBar().showMessage(f"Data exported successfully to {fileName}", 3000)
            
        except Exception as e:
            self.statusBar().showMessage(f"Error exporting CSV: {str(e)}", 5000)
    
    def _export_excel(self, fileName):
        """Export data in Excel format with multiple sheets"""
        try:
            # Create DataFrame with measurement data
            df = pd.DataFrame(self.dataTableArray, columns=cFD.DATA_NAMES)
            
            # Add frame numbers as the first column
            df.insert(0, 'Frame', range(1, len(df) + 1))
            
            # Mark tossed frames
            df['Tossed'] = df['Frame'].isin(self.tossedFrames)
            
            # Create Excel writer object
            with pd.ExcelWriter(fileName, engine='openpyxl') as writer:
                # Write main data to first sheet
                df.to_excel(writer, sheet_name='Measurements', index=False, float_format='%.4f')
                
                # Create a summary sheet with tossed frames
                if self.tossedFrames:
                    tossed_df = pd.DataFrame({'Tossed Frames': self.tossedFrames})
                    tossed_df.to_excel(writer, sheet_name='Tossed Frames', index=False)
                
                # Add metadata sheet if TIFF file info is available
                if hasattr(self, 'fileName') and self.fileName:
                    import os
                    metadata_df = pd.DataFrame({
                        'Property': ['Source File', 'Total Frames', 'File Size (MB)'],
                        'Value': [
                            os.path.basename(self.fileName),
                            self.totalFrameValue.text(),
                            f"{os.path.getsize(self.fileName) / (1024*1024):.2f}" if os.path.exists(self.fileName) else "N/A"
                        ]
                    })
                    metadata_df.to_excel(writer, sheet_name='File Info', index=False)
            
            self.statusBar().showMessage(f"Data exported successfully to {fileName}", 3000)
            
        except Exception as e:
            self.statusBar().showMessage(f"Error exporting Excel: {str(e)}", 5000)
    
    # slot called anytime the inputs are modified
    def clearThreshAndPreview(self):
        if self.fileName:
            # Reset threshold and preview images to default
            self.threshPixLabel.setPixmap(tiffF.defaultPix(self.backShade))
            self.previewPixLabel.setPixmap(tiffF.defaultPix(self.backShade))
            self.isPreviewCleared = True
            
            # Clear manual override when threshold changes
            self.manual_override_active = False
            self.manual_left_pole = None
            self.manual_right_pole = None
            
            # If we have an image loaded, ensure we're showing the original without overlays
            if hasattr(self, 'imagePixLabel') and hasattr(self.imagePixLabel, 'imageArr') and self.imagePixLabel.imageArr is not None:
                self.imagePixLabel.setPixmap(tiffF.pixFromArr(self.imagePixLabel.imageArr))

    # changes default pixmap color when computer switches color mode
    def changeDefaultPixmaps(self):
        self.backShade = QTableView().palette().base().color().value()
        newPix = tiffF.defaultPix(self.backShade)
        if self.fileName and self.isPreviewCleared:
            # image and thresh have images but not preview
            self.previewPixLabel.setPixmap(newPix)
        elif not self.fileName:
            # no image is loaded (all three images are defaults)
            self.imagePixLabel.setPixmap(newPix)
            self.threshPixLabel.setPixmap(newPix)
            self.previewPixLabel.setPixmap(newPix)
    
    # determines if the application is in dark mode
    def isComputerDarkMode(self):
        aLabel = QLabel("a")
        return (aLabel.palette().color(aLabel.backgroundRole()).black() 
              > aLabel.palette().color(aLabel.foregroundRole()).black())

    # detects when the computer switches to dark or light mode
    def changeEvent(self, event):
        if event.type() == QEvent.ThemeChange:
            isComputerDarkMode = self.isComputerDarkMode()
            if isComputerDarkMode != self.isDarkMode:
                self.isDarkMode = isComputerDarkMode
                self.changeDefaultPixmaps()
        super().changeEvent(event)
        
    # handle key events for frame navigation and data addition
    def keyPressEvent(self, event: QKeyEvent):
        # Debug information for AppImage troubleshooting (reduced verbosity)
        is_appimage = os.environ.get('APPIMAGE') is not None
        if is_appimage and event.key() in [Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down]:
            print(f"[DEBUG] Arrow key pressed in AppImage, focus: {self.hasFocus()}")
        
        if not self.fileName:
            super().keyPressEvent(event)
            return

        # Ensure we have focus for keyboard events
        if not self.hasFocus():
            self.setFocus()
            self.activateWindow()

        # Handle key mappings
        if event.key() == Qt.Key_Right:
            # Right arrow - Add data (same as Add button)
            self.onAddDataClicked()
        elif event.key() == Qt.Key_Left:
            # Left arrow - Toss/untoss data (same as Toss button)
            self.onTossDataClicked()
        elif event.key() == Qt.Key_Up:
            # Up arrow - Increase threshold by 10
            self.threshValue.setValue(self.threshValue.value() + 10)
            self.applyThreshold()
            self.onPreviewClicked()
        elif event.key() == Qt.Key_Down:
            # Down arrow - Decrease threshold by 10
            self.threshValue.setValue(self.threshValue.value() - 10)
            self.applyThreshold()
            self.onPreviewClicked()
        elif event.key() == Qt.Key_W:
            # W - Increase GOL iterations by 1
            newValue = min(self.gOLIterationsValue.value() + 1, self.gOLIterationsValue.maximum())
            self.gOLIterationsValue.setValue(newValue)
            self.applyThreshold()
            self.onPreviewClicked()
        elif event.key() == Qt.Key_S:
            # S - Decrease GOL iterations by 1
            newValue = max(self.gOLIterationsValue.value() - 1, self.gOLIterationsValue.minimum())
            self.gOLIterationsValue.setValue(newValue)
            self.applyThreshold()
            self.onPreviewClicked()
        elif event.key() == Qt.Key_D:
            # D - Increase GOL factor by 1
            newValue = min(self.gOLFactorValue.value() + 1, self.gOLFactorValue.maximum())
            self.gOLFactorValue.setValue(newValue)
            self.applyThreshold()
            self.onPreviewClicked()
        elif event.key() == Qt.Key_A:
            # A - Decrease GOL factor by 1
            newValue = max(self.gOLFactorValue.value() - 1, self.gOLFactorValue.minimum())
            self.gOLFactorValue.setValue(newValue)
            self.applyThreshold()
            self.onPreviewClicked()
        elif event.key() == Qt.Key_Space:
            # Space - Preview (same as Preview button)
            self.onPreviewClicked()
        elif event.key() == Qt.Key_M:
            # M - Manual override
            self.onManualOverrideClicked()
        elif event.key() == Qt.Key_E:
            # E - Export data
            self.onExportDataClicked()
            
        super().keyPressEvent(event)

    # process all frames automatically
    def onRunAllFramesClicked(self):
        if self.fileName:
            totalFrames = int(self.totalFrameValue.text())
            currentFrame = self.frameValue.value()
            
            # Start from the current frame
            for frame in range(currentFrame, totalFrames + 1):
                self.frameValue.setValue(frame)
                
                # Apply threshold and preview for this frame
                self.applyThreshold()
                self.onPreviewClicked()
                
                # Process the data
                data, doesSpindleExist = (cFD.spindleMeasurements(
                                            self.imagePixLabel.imageArr,
                                            self.threshPixLabel.imageArr))

                if doesSpindleExist:
                    # add the row of data to the data table
                    self.dataTableModel.beginResetModel()
                    frameIndex = frame - 1
                    for i in range(len(data)):
                        self.dataTableArray[frameIndex, i] = data[i]
                    self.dataTableModel.endResetModel()
                else:
                    # If no spindle exists, mark as tossed
                    if frame not in self.tossedFrames:
                        self.tossedFrames.append(frame)
                        self.tossedFrames.sort()
                        self.dataTableModel.addTossedRow(frame)
            
            # Show a status message when completed
            self.statusBar().showMessage(f"Processed all frames from {currentFrame} to {totalFrames}", 5000)
            
    # Handle clicks on data table
    def onDataTableClicked(self, index):
        # Navigate to that frame regardless of which column was clicked
        frame = index.row() + 1  # Convert from 0-based to 1-based index
        self.frameValue.setValue(frame)
            
    # Handle clicks on column headers in the data table
    def onColumnHeaderClicked(self, column_index):
        if self.fileName and column_index >= 0:  # Allow all columns including index
            # Get column name
            if column_index < len(cFD.DATA_NAMES):
                column_name = cFD.DATA_NAMES[column_index]
                
                # Debug print
                print(f"Column clicked: {column_index}, Name: {column_name}")
                
                # Create arrays of frame numbers and data for the selected column
                valid_frames = []
                valid_data = []
                
                # Debug print to check data array dimensions
                print(f"Data array shape: {self.dataTableArray.shape}")
                
                for i in range(self.dataTableArray.shape[0]):
                    if i < len(self.dataTableArray) and column_index < self.dataTableArray.shape[1]:
                        # Only include frames with valid data (non-zero values)
                        value = self.dataTableArray[i, column_index]
                        if value != 0:
                            valid_frames.append(i + 1)  # 1-indexed frame numbers
                            valid_data.append(value)
                
                # Debug print to check collected data
                print(f"Valid frames found: {len(valid_frames)}")
                
                # Extract just the filename for display purposes
                image_name_only = os.path.basename(self.fileName) if self.fileName else None
                
                # Create and show plot dialog even if no data (will show message)
                plot_dialog = pD.PlotDialog(self, 
                                          title=f"{column_name} vs Frame Number", 
                                          image_name=self.fileName)
                plot_dialog.plot_column_data(valid_frames, valid_data, column_name)
                plot_dialog.exec()

# QLabel for keeping the contained pixmap scaled correctly
class PixLabel(QLabel):

    # set up the PixLabel
    def __init__(self):

        # allow the QLabel to initialize itself
        super().__init__()

        # adjustable side unit length of label
        self.side = 80

        # default size twice its minimum size
        self.setGeometry(0, 0, 2 * self.side, 2 * self.side)

        # define a class pixmap variable
        self.pix = None

        # define a class pixArray variable
        self.imageArr = None

        imgPolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.setSizePolicy(imgPolicy)
        self.setMinimumSize(self.side, self.side)
        self.setFrameStyle(QFrame.Panel | QFrame.Raised)
        self.setLineWidth(2)
    
    # setter method for arr
    def setImageArr(self, arr):
        self.imageArr = arr

    # scale pixmap to label w and h, keeping pixmap aspect ratio
    def setPixmap(self, pix, isNewPix = True):

        # if a new pixmap is applied, adjust the minimum size of the
        # label so that the frame always stays flush with the pixmap
        # goal is for longest dimension to be minimum self.side
        if isNewPix:
            hOverW = pix.size().height() / pix.size().width()
            if hOverW < 1: # wide images
                self.setMinimumSize(self.side, int(self.side * hOverW))
            elif hOverW > 1: # tall images
                self.setMinimumSize(int(self.side / hOverW), self.side)
            else: # square images
                self.setMinimumSize(self.side, self.side)
        self.pix = pix
        scaled = pix.scaled(self.size(), Qt.KeepAspectRatio)
        super().setPixmap(scaled)
    
    # rescale the pixmap when the label is resized
    def resizeEvent(self, event):
        self.setPixmap(self.pix, False)
        self.setAlignment(Qt.AlignCenter)
        super().resizeEvent(event)

# subclassed QSplitter to allow for custom handles
class SplitterWithHandles(QSplitter):
    def __init__(self, orientation):
        super().__init__()
        self.setOrientation(orientation)
        self.setHandleWidth(4)

    def createHandle(self):
        return GradientSplitterHandle(self.orientation(), self)

# the custom splitter handle for a SplitterWithHandles
# subclass idea from PySide6 documentation page for QSplitterHandle
class GradientSplitterHandle(QSplitterHandle):

    def paintEvent(self, event):

        painter = QPainter()
        painter.begin(self)
        # preset gradient:
        gradientBrush = QBrush(QGradient.RiskyConcrete)
        if self.orientation() == Qt.Horizontal:
            gradientBrush.setTransform(QTransform().rotate(-90))

        painter.fillRect(self.rect(), gradientBrush)
        painter.end()

# BOILERPLATE TABLE MODEL
class ImageTableModel(QAbstractTableModel):
    def __init__(self, dataNames, data):
        super().__init__()

        self._dataNames = dataNames
        self._data = data
        self._tossedRows = []

    def addTossedRow(self, row):
        self._tossedRows.append(row)
    
    def removeTossedRow(self, row):
        self._tossedRows.remove(row)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            if self._data[index.row(), index.column()] == 0.0:
                return ""
            else:
                return "%.4f" % self._data[index.row(), index.column()]
        if role == Qt.TextAlignmentRole:
            return Qt.AlignVCenter + Qt.AlignRight
        if role == Qt.BackgroundRole:
            if (index.row() + 1) in self._tossedRows:
                return QBrush(Qt.darkGray)
    
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

    # Override showEvent to ensure proper focus when window is shown
    def showEvent(self, event):
        """Override showEvent to ensure proper focus when window is shown"""
        super().showEvent(event)
        # Enhanced focus management for AppImage compatibility
        self.activateWindow()
        self.raise_()
        self.setFocus()
        # Force focus to main window for keyboard events
        QApplication.instance().setActiveWindow(self)

# main function for entry point
def main():
    """Main entry point for the application"""
    # Support for Windows multiprocessing when packaged with PyInstaller
    import multiprocessing
    multiprocessing.freeze_support()
    
    app = QApplication(sys.argv)
    
    # Enhanced AppImage compatibility settings
    # Set application attributes for better focus handling
    app.setAttribute(Qt.AA_DontUseNativeMenuBar, False)
    app.setAttribute(Qt.AA_DontUseNativeDialogs, False)
    
    # Set application class name for better window manager integration
    app.setApplicationName("Mitotic Spindle Tool")
    app.setApplicationDisplayName("Mitotic Spindle Tool")
    app.setApplicationVersion(VERSION_DISPLAY)
    
    # Detect if running in AppImage environment
    is_appimage = os.environ.get('APPIMAGE') is not None
    if is_appimage:
        print("[INFO] Running in AppImage environment - enabling enhanced focus handling")
        # Set application properties for better desktop integration
        app.setDesktopFileName("mitotic-spindle-tool")
    
    window = MainWindow()
    window.show()
    
    # Enhanced focus management for AppImage
    if is_appimage:
        # Ensure window gets focus in AppImage environment
        window.activateWindow()
        window.raise_()
        app.processEvents()  # Process pending events
    
    sys.exit(app.exec())

# create and display the application if this file is being run
if __name__ == "__main__":
    main()