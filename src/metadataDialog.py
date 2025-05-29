from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QTextEdit, QLabel, QScrollArea, QWidget, QTableWidget,
                               QTableWidgetItem, QHeaderView, QSizePolicy)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import tiffFunctions as tiffF

class MetadataDialog(QDialog):
    """Dialog to display TIFF metadata information"""
    
    def __init__(self, tiff_filename, parent=None):
        super().__init__(parent)
        self.tiff_filename = tiff_filename
        # Extract filename from path (handle both Unix and Windows paths)
        if '/' in tiff_filename:
            filename = tiff_filename.split('/')[-1]
        else:
            filename = tiff_filename.split('\\')[-1]
        self.setWindowTitle(f"Metadata - {filename}")
        self.resize(600, 500)
        
        self.setupUI()
        self.loadMetadata()
        
    def setupUI(self):
        """Set up the dialog UI"""
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("TIFF Metadata Information")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Create table for metadata
        self.metadata_table = QTableWidget()
        self.metadata_table.setColumnCount(2)
        self.metadata_table.setHorizontalHeaderLabels(["Property", "Value"])
        
        # Configure table appearance
        header = self.metadata_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        
        self.metadata_table.setAlternatingRowColors(True)
        self.metadata_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.metadata_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        layout.addWidget(self.metadata_table)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Refresh button
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.loadMetadata)
        button_layout.addWidget(refresh_button)
        
        button_layout.addStretch()
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def loadMetadata(self):
        """Load and display the TIFF metadata"""
        try:
            metadata = tiffF.getTiffMetadata(self.tiff_filename)
            
            # Clear existing content
            self.metadata_table.setRowCount(0)
            
            # Sort metadata keys for better organization
            sorted_keys = sorted(metadata.keys())
            
            # Populate the table
            for i, key in enumerate(sorted_keys):
                self.metadata_table.insertRow(i)
                
                # Property name
                key_item = QTableWidgetItem(str(key))
                key_item.setFont(QFont())
                self.metadata_table.setItem(i, 0, key_item)
                
                # Property value
                value = metadata[key]
                value_item = QTableWidgetItem(str(value))
                
                # Special formatting for certain types of data
                if key.lower() in ['error']:
                    value_item.setForeground(Qt.red)
                elif key.lower() in ['size', 'format', 'mode', 'number of frames', 'filename']:
                    font = QFont()
                    font.setBold(True)
                    value_item.setFont(font)
                
                self.metadata_table.setItem(i, 1, value_item)
            
            # Resize table to content
            self.metadata_table.resizeRowsToContents()
            
        except Exception as e:
            # Show error in table
            self.metadata_table.setRowCount(1)
            self.metadata_table.setItem(0, 0, QTableWidgetItem("Error"))
            error_item = QTableWidgetItem(f"Failed to load metadata: {str(e)}")
            error_item.setForeground(Qt.red)
            self.metadata_table.setItem(0, 1, error_item)
