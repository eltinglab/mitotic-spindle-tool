from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QHBoxLayout, QFileDialog
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import numpy as np
import os

try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False

class PlotDialog(QDialog):
    def __init__(self, parent=None, title="Data Plot", image_name=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(800, 500)
        self.column_name = ""  # Store column name for saving files
        self.image_name = image_name  # Store the image filename
        
        # Create matplotlib Figure and Canvas
        self.figure = Figure(figsize=(8, 5), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        
        # Add toolbar for basic matplotlib interactions
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        # Create layout for canvas and toolbar
        plot_layout = QVBoxLayout()
        plot_layout.addWidget(self.toolbar)
        plot_layout.addWidget(self.canvas)
        
        # Create button layout
        button_layout = QHBoxLayout()
        
        # Add save button
        save_button = QPushButton("Save Plot")
        save_button.clicked.connect(self.save_plot)
        button_layout.addWidget(save_button)
        
        # Add close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addLayout(plot_layout)
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
    
    def save_plot(self):
        """
        Save the current plot to a file
        """
        # Get the base image name without path or extension
        if self.image_name:
            base_image_name = os.path.basename(self.image_name)
            base_image_name = os.path.splitext(base_image_name)[0]
            default_filename = f"{base_image_name}_{self.column_name.replace(' ', '_').replace('(', '').replace(')', '')}.png"
        else:
            default_filename = f"spindle_{self.column_name.replace(' ', '_').replace('(', '').replace(')', '')}.png"
        
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save Plot", default_filename, "Images (*.png *.jpg *.pdf);;All Files (*)")
        
        if file_name:
            # Save figure with tight layout
            self.figure.tight_layout()
            self.figure.savefig(file_name, dpi=300, bbox_inches='tight')
            
    def plot_column_data(self, frames, data, column_name):
        """
        Create a line plot of frame number vs. column value
        
        Parameters:
            frames: Array of frame numbers (x-axis)
            data: Array of values for the selected column (y-axis)
            column_name: Name of the column being plotted
        """
        # Store column name for save function
        self.column_name = column_name
        
        # Print debug info
        print(f"Plotting {column_name} with {len(frames)} data points")
        print(f"Frames: {frames}")
        print(f"Values: {data}")
        
        # Convert inputs to numpy arrays for safety
        frames = np.array(frames)
        data = np.array(data)
        
        # Clear any previous plot
        self.figure.clear()
        
        # Create axes
        ax = self.figure.add_subplot(111)
        
        # Check if we have valid data
        if len(frames) > 0 and len(data) > 0:
            # Check if seaborn is available for enhanced visuals
            if HAS_SEABORN:
                sns.set_style("whitegrid")
                sns.lineplot(x=frames, y=data, ax=ax, marker='o')
            else:
                ax.plot(frames, data, marker='o', linestyle='-')
                
            # Set labels
            ax.set_xlabel('Frame Number')
            ax.set_ylabel(column_name)
            ax.set_title(f'{column_name} vs Frame Number')
            
            # Add grid
            ax.grid(True)
        else:
            ax.text(0.5, 0.5, 'No data available for this column', 
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes, fontsize=14)
        
        # Add tight layout
        self.figure.tight_layout()
        
        # Refresh canvas
        self.canvas.draw()
