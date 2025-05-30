from PySide6.QtWidgets import (QDialog, QVBoxLayout, QPushButton, QHBoxLayout, 
                               QLabel, QCheckBox)
from PySide6.QtCore import Qt, QPointF, Signal, QTimer
from PySide6.QtGui import QPainter, QPen, QBrush, QColorConstants, QMouseEvent
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
import curveFitData as cFD

class ManualSpindleDialog(QDialog):
    """
    Dialog for manually adjusting spindle pole positions
    """
    # Signal emitted when manual positions are confirmed
    manual_positions_changed = Signal(tuple, tuple)  # left_pole, right_pole
    
    def __init__(self, parent=None, image_arr=None, thresh_arr=None):
        super().__init__(parent)
        self.setWindowTitle("Manual Spindle Adjustment")
        self.resize(800, 600)
        
        # Store the image arrays
        self.image_arr = image_arr
        self.thresh_arr = thresh_arr
        
        # Get initial automatic detection
        self.auto_data, self.spindle_exists = cFD.spindlePlot(image_arr, thresh_arr)
        
        # Initialize manual pole positions with automatic detection
        if self.spindle_exists:
            self.left_pole = list(self.auto_data[1])  # Convert to list for mutability
            self.right_pole = list(self.auto_data[2])
        else:
            # If no spindle detected, use center positions as defaults
            height, width = image_arr.shape
            self.left_pole = [width * 0.3, height * 0.5]
            self.right_pole = [width * 0.7, height * 0.5]
        
        # Track which pole is being dragged
        self.dragging_pole = None
        self.drag_threshold = 15  # Pixels threshold for drag detection
        
        # Performance optimization: throttle plot updates during dragging
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self._do_plot_update)
        self.update_delay_ms = 50  # 50ms delay for smooth updates
        
        # Flag to prevent redundant updates
        self.needs_update = False
        
        # Create matplotlib Figure and Canvas with performance optimizations
        self.figure = Figure(figsize=(8, 6), dpi=100, facecolor='white')
        self.figure.patch.set_facecolor('white')  # Explicit background
        self.canvas = FigureCanvas(self.figure)
        
        # Optimize canvas for interactive use
        self.canvas.setFocusPolicy(Qt.ClickFocus)
        
        # Connect mouse events
        self.canvas.mpl_connect('button_press_event', self.on_mouse_press)
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        self.canvas.mpl_connect('button_release_event', self.on_mouse_release)
        
        # Cache axes to avoid recreation
        self.ax = None
        
        # Setup UI
        self.setup_ui()
        
        # Initial plot
        self.update_plot()
    
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel(
            "Click and drag the red circles to adjust spindle pole positions.\n"
            "The blue line shows the fitted curve between the poles."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Canvas
        layout.addWidget(self.canvas)
        
        # Checkbox for auto-detection overlay
        self.show_auto_checkbox = QCheckBox("Show automatic detection (green)")
        self.show_auto_checkbox.setChecked(True)
        self.show_auto_checkbox.toggled.connect(self._schedule_update)
        layout.addWidget(self.show_auto_checkbox)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        reset_button = QPushButton("Reset to Auto")
        reset_button.clicked.connect(self.reset_to_auto)
        button_layout.addWidget(reset_button)
        
        button_layout.addStretch()
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        apply_button = QPushButton("Apply Manual Adjustment")
        apply_button.clicked.connect(self.apply_manual_adjustment)
        button_layout.addWidget(apply_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def reset_to_auto(self):
        """Reset manual positions to automatic detection"""
        if self.spindle_exists:
            self.left_pole = list(self.auto_data[1])
            self.right_pole = list(self.auto_data[2])
        self._schedule_update()
    
    def apply_manual_adjustment(self):
        """Apply the manual adjustment and close dialog"""
        self.manual_positions_changed.emit(tuple(self.left_pole), tuple(self.right_pole))
        self.accept()
    
    def _schedule_update(self):
        """Schedule a plot update with debouncing to prevent excessive redraws"""
        self.needs_update = True
        if not self.update_timer.isActive():
            self.update_timer.start(self.update_delay_ms)
    
    def _do_plot_update(self):
        """Perform the actual plot update"""
        if self.needs_update:
            self.needs_update = False
            self.update_plot()
    
    def update_plot(self):
        """Update the plot with current pole positions"""
        try:
            # Clear figure but reuse axes if possible for better performance
            if self.ax is None:
                self.figure.clear()
                self.ax = self.figure.add_subplot(111)
            else:
                self.ax.clear()
            
            # Configure axes for better performance
            self.ax.set_aspect('equal')
            
            # Display the original image with optimizations
            im = self.ax.imshow(self.image_arr, cmap='gray', aspect='equal', 
                               interpolation='nearest', origin='upper')
            
            # Pre-calculate coordinates to minimize repeated operations
            all_x_coords = [self.left_pole[0], self.right_pole[0]]
            all_y_coords = [self.left_pole[1], self.right_pole[1]]
            
            # Show automatic detection if enabled and exists
            if self.show_auto_checkbox.isChecked() and self.spindle_exists:
                auto_left = self.auto_data[1]
                auto_right = self.auto_data[2]
                auto_center = self.auto_data[3]
                
                # Add auto coordinates to bounds calculation
                all_x_coords.extend([auto_left[0], auto_right[0], auto_center[0]])
                all_y_coords.extend([auto_left[1], auto_right[1], auto_center[1]])
                
                # Plot automatic detection curve (green) - optimized
                if auto_left[0] != auto_right[0]:  # Avoid division by zero
                    x_auto = np.linspace(auto_left[0], auto_right[0], 50)  # Reduced points for performance
                    try:
                        points_x = [auto_left[0], auto_center[0], auto_right[0]]
                        points_y = [auto_left[1], auto_center[1], auto_right[1]]
                        coeffs = np.polyfit(points_x, points_y, 2)
                        y_auto = np.polyval(coeffs, x_auto)
                        self.ax.plot(x_auto, y_auto, 'g-', linewidth=2, alpha=0.7, label='Auto detection')
                        all_x_coords.extend(x_auto.tolist())
                        all_y_coords.extend(y_auto.tolist())
                    except np.RankWarning:
                        # Fallback to straight line if quadratic fitting fails
                        y_auto = np.linspace(auto_left[1], auto_right[1], 50)
                        self.ax.plot(x_auto, y_auto, 'g-', linewidth=2, alpha=0.7, label='Auto detection')
                        all_x_coords.extend(x_auto.tolist())
                        all_y_coords.extend(y_auto.tolist())
                    except Exception:
                        # Silent fallback for any other errors
                        pass
                
                # Plot automatic poles (green)
                self.ax.plot(auto_left[0], auto_left[1], 'go', markersize=8, alpha=0.7)
                self.ax.plot(auto_right[0], auto_right[1], 'go', markersize=8, alpha=0.7)
            
            # Plot manual curve (blue) - optimized
            if self.left_pole and self.right_pole and self.left_pole[0] != self.right_pole[0]:
                x_manual = np.linspace(self.left_pole[0], self.right_pole[0], 50)  # Reduced points
                y_manual = np.linspace(self.left_pole[1], self.right_pole[1], 50)
                self.ax.plot(x_manual, y_manual, 'b-', linewidth=2, label='Manual adjustment')
                all_x_coords.extend(x_manual.tolist())
                all_y_coords.extend(y_manual.tolist())
            
            # Plot manual poles (red, draggable)
            self.ax.plot(self.left_pole[0], self.left_pole[1], 'ro', markersize=10, 
                        label='Left pole (draggable)')
            self.ax.plot(self.right_pole[0], self.right_pole[1], 'ro', markersize=10, 
                        label='Right pole (draggable)')
            
            # Calculate dynamic padding - optimized
            image_height, image_width = self.image_arr.shape
            
            # Use numpy for faster min/max operations
            all_x_coords = np.array(all_x_coords)
            all_y_coords = np.array(all_y_coords)
            min_x, max_x = np.min(all_x_coords), np.max(all_x_coords)
            min_y, max_y = np.min(all_y_coords), np.max(all_y_coords)
            
            # Calculate overflow and padding
            x_overflow_left = max(0, -min_x)
            x_overflow_right = max(0, max_x - image_width)
            y_overflow_top = max(0, -min_y)
            y_overflow_bottom = max(0, max_y - image_height)
            
            # Calculate minimum required padding (reduced for performance)
            min_padding_x = image_width * 0.1  # Reduced from 0.15
            min_padding_y = image_height * 0.1
            
            # Use larger of overflow or minimum padding
            padding_left = max(x_overflow_left, min_padding_x)
            padding_right = max(x_overflow_right, min_padding_x)
            padding_top = max(y_overflow_top, min_padding_y)
            padding_bottom = max(y_overflow_bottom, min_padding_y)
            
            # Set axis limits with calculated padding
            self.ax.set_xlim(-padding_left, image_width + padding_right)
            self.ax.set_ylim(image_height + padding_bottom, -padding_top)  # Invert Y axis
            
            # Add legend outside the plot area and title
            self.ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize='small')
            self.ax.set_title('Manual Spindle Pole Adjustment')
            
            # Optimize layout and drawing with extra space for legend
            self.figure.tight_layout(pad=1.0, rect=[0, 0, 0.85, 1])
            
            # Force canvas update
            self.canvas.draw_idle()  # Use draw_idle for better performance
            
        except Exception as e:
            print(f"Error updating plot: {e}")
            # Fallback: clear everything and show error
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, f'Plot update error: {str(e)}', 
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes, fontsize=12, color='red')
            self.canvas.draw()
    
    def get_pole_at_position(self, x, y):
        """Check if mouse position is near a pole, return which pole or None"""
        if x is None or y is None:
            return None
            
        try:
            left_dist = np.sqrt((x - self.left_pole[0])**2 + (y - self.left_pole[1])**2)
            right_dist = np.sqrt((x - self.right_pole[0])**2 + (y - self.right_pole[1])**2)
            
            if left_dist <= self.drag_threshold:
                return 'left'
            elif right_dist <= self.drag_threshold:
                return 'right'
            else:
                return None
        except (TypeError, IndexError):
            return None
    
    def on_mouse_press(self, event):
        """Handle mouse press events"""
        if event.inaxes and event.button == 1:  # Left mouse button
            self.dragging_pole = self.get_pole_at_position(event.xdata, event.ydata)
            if self.dragging_pole:
                # Immediate visual feedback
                self._schedule_update()
    
    def on_mouse_move(self, event):
        """Handle mouse move events with throttling for performance"""
        if (self.dragging_pole and event.inaxes and 
            event.xdata is not None and event.ydata is not None):
            
            # Update pole position
            try:
                if self.dragging_pole == 'left':
                    self.left_pole = [float(event.xdata), float(event.ydata)]
                elif self.dragging_pole == 'right':
                    self.right_pole = [float(event.xdata), float(event.ydata)]
                
                # Schedule update instead of immediate update for performance
                self._schedule_update()
                
            except (TypeError, ValueError):
                # Ignore invalid coordinates
                pass
    
    def on_mouse_release(self, event):
        """Handle mouse release events"""
        if self.dragging_pole:
            self.dragging_pole = None
            # Force final update after dragging stops
            self.update_timer.stop()
            self._do_plot_update()

    def get_manual_measurements(self):
        """Calculate measurements using manual pole positions"""
        return self.calculate_manual_measurements(self.left_pole, self.right_pole)
    
    def calculate_manual_measurements(self, left_pole, right_pole):
        """Calculate spindle measurements using manual pole positions"""
        try:
            # POLE SEPARATION (Euclidean distance)
            pole_separation = np.sqrt((right_pole[0] - left_pole[0])**2 + 
                                    (right_pole[1] - left_pole[1])**2)
            
            # ARC LENGTH (approximated as straight line for manual adjustment)
            arc_length = pole_separation
            
            # For area and curvature metrics, use automatic detection if available
            area_metric = 0.0
            max_curvature = 0.0
            avg_curvature = 0.0
            
            if self.spindle_exists:
                try:
                    # Get automatic measurements for comparison
                    auto_measurements, _ = cFD.spindleMeasurements(self.image_arr, self.thresh_arr)
                    if auto_measurements:
                        area_metric = auto_measurements[2]  # Use auto area metric
                        # Set minimal curvature since it's a straight line
                        max_curvature = abs(2 * 0.001)  # Very small curvature
                        avg_curvature = abs(0.001)
                except Exception:
                    pass
            
            return [pole_separation, arc_length, area_metric, max_curvature, avg_curvature]
            
        except Exception as e:
            print(f"Error calculating manual measurements: {e}")
            return [0.0, 0.0, 0.0, 0.0, 0.0]
    
    def closeEvent(self, event):
        """Clean up when dialog is closed"""
        # Stop any running timers
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
        
        # Clear matplotlib figure to free memory
        if hasattr(self, 'figure'):
            self.figure.clear()
            
        super().closeEvent(event)
