from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import plotSpindle as pS
import tiffFunctions as tiffF

class SpindlePreviewDialog(QDialog):
    """
    Dialog for displaying spindle detection results on the original image
    with coordinates in original space
    """
    
    def __init__(self, parent, originalImageArr, spindlePlotData, doesSpindleExist, transformInfo=None):
        super().__init__(parent)
        self.setWindowTitle("Spindle Preview - Original Coordinates")
        self.setModal(True)
        
        # Store data
        self.originalImageArr = originalImageArr
        self.spindlePlotData = spindlePlotData
        self.doesSpindleExist = doesSpindleExist
        self.transformInfo = transformInfo
        
        # Setup UI
        self.setupUI()
        self.updatePreview()
        
    def setupUI(self):
        layout = QVBoxLayout()
        
        # Title label
        title_label = QLabel("Spindle Detection Results in Original Coordinate Space")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Image display
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(400, 400)
        layout.addWidget(self.image_label)
        
        # Coordinate information
        self.coord_info_label = QLabel()
        self.coord_info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.coord_info_label)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def updatePreview(self):
        """Update the preview image with spindle overlay"""
        if self.doesSpindleExist and self.spindlePlotData:
            # Create overlay on original image
            overlayPixmap = pS.plotSpindleOnOriginal(
                self.originalImageArr, 
                self.spindlePlotData, 
                self.doesSpindleExist
            )
            self.image_label.setPixmap(overlayPixmap)
            
            # Display coordinate information
            leftPole = self.spindlePlotData[1]
            rightPole = self.spindlePlotData[2]
            centerPoint = self.spindlePlotData[3]
            
            coord_text = f"""Spindle Coordinates (Original Image Space):
Left Pole: ({leftPole[0]:.1f}, {leftPole[1]:.1f})
Right Pole: ({rightPole[0]:.1f}, {rightPole[1]:.1f})
Center Point: ({centerPoint[0]:.1f}, {centerPoint[1]:.1f})"""
            
            self.coord_info_label.setText(coord_text)
        else:
            # No spindle detected
            originalPixmap = tiffF.pixFromArr(self.originalImageArr)
            self.image_label.setPixmap(originalPixmap)
            self.coord_info_label.setText("No spindle detected in this frame.")
