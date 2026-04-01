# toolbar.py - Complete COC-style Toolbar with Persistent 3D Dynamite Placement

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QFrame, QScrollArea, QSizePolicy
)
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QBrush, QMouseEvent, QCursor, QPixmap, QPainter, QPainterPath
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty, QSize, pyqtSignal, QEvent, QPointF, QRect, QTimer
from PyQt6.QtWidgets import QApplication
import math


class PersistentDynamiteWidget(QWidget):
    """Persistent dynamite widget that stays in place after dropping"""
    
    def __init__(self, tool_type, range_radius, global_pos, parent=None):
        super().__init__(parent)
        self.tool_type = tool_type
        self.range_radius = range_radius
        self.animation_angle = 0
        self.is_placed = False
        
        # Set size based on range radius
        base_size = 80
        self.visual_radius = min(range_radius * 1.5, 150)  # Scale radius for visualization
        widget_size = base_size + int(self.visual_radius * 2)
        
        self.setFixedSize(widget_size, widget_size)
        
        # Convert QPointF to integers for move() method
        pos_x = int(global_pos.x() - widget_size // 2)
        pos_y = int(global_pos.y() - widget_size // 2)
        self.move(pos_x, pos_y)
        
        # Animation timer for subtle pulsing effect
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.animate)
        self.animation_timer.start(100)  # Slower pulse for placed dynamites
        
    def animate(self):
        """Update animation for subtle pulsing effect"""
        self.animation_angle = (self.animation_angle + 5) % 360
        self.update()
        
    def paintEvent(self, event):
        """Draw a persistent dynamite with subtle radius visualization"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center_x = self.width() // 2
        center_y = self.height() // 2
        
        # Draw subtle radius circle (less prominent than during drag)
        pulse_alpha = 40 + int(20 * math.sin(math.radians(self.animation_angle * 2)))
        radius_color = QColor(255, 215, 0, pulse_alpha)  # Subtle pulsating gold
        
        painter.setPen(QPen(radius_color, 1, Qt.PenStyle.DotLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(center_x - self.visual_radius, center_y - self.visual_radius,
                          self.visual_radius * 2, self.visual_radius * 2)
        
        # Draw static dynamite (no rotation for placed ones)
        self.draw_static_dynamite(painter, center_x, center_y)
        
        # Draw tool type and range text
        painter.setPen(QPen(QColor(255, 255, 255)))
        painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        info_text = f"{self.tool_type} (R:{self.range_radius})"
        text_rect = QRect(center_x - 40, center_y + 30, 80, 20)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, info_text)
        
    def draw_static_dynamite(self, painter, center_x, center_y):
        """Draw a static dynamite stick (no rotation for placed ones)"""
        # Dynamite dimensions
        length = 40
        width = 12
        height = 12
        
        # Draw dynamite body (simple 2D representation)
        body_rect = QRect(center_x - length//2, center_y - width//2, length, width)
        
        # Dynamite body (red)
        painter.setBrush(QBrush(QColor(139, 0, 0)))  # Dark red
        painter.setPen(QPen(QColor(101, 67, 33), 2))  # Brown border
        painter.drawRoundedRect(body_rect, 4, 4)
        
        # Brown ends
        painter.setBrush(QBrush(QColor(101, 67, 33)))  # Brown
        painter.drawRect(center_x - length//2, center_y - width//2, 4, width)  # Left end
        painter.drawRect(center_x + length//2 - 4, center_y - width//2, 4, width)  # Right end
        
        # Static fuse
        fuse_color = QColor(255, 215, 0)  # Gold
        painter.setPen(QPen(fuse_color, 2))
        painter.drawLine(center_x + length//2, center_y, center_x + length//2 + 15, center_y - 10)
        
        # Small spark
        painter.setPen(QPen(QColor(255, 255, 0), 1))
        painter.drawLine(center_x + length//2 + 15, center_y - 10, center_x + length//2 + 18, center_y - 13)
        
    def get_dynamite_info(self):
        """Return dynamite information for simulation"""
        return {
            'type': self.tool_type,
            'range': self.range_radius,
            'position': self.pos(),
            'global_position': self.mapToGlobal(self.rect().center())
        }


class Dynamite3DDragWidget(QWidget):
    """3D Dynamite widget with radius visualization that appears during drag operations"""
    
    def __init__(self, tool_type, range_radius, parent=None):
        super().__init__(parent)
        self.tool_type = tool_type
        self.range_radius = range_radius
        self.animation_angle = 0
        
        # Set size based on range radius
        base_size = 120
        self.visual_radius = min(range_radius * 2, 200)  # Scale radius for visualization
        widget_size = base_size + int(self.visual_radius * 2)
        
        self.setFixedSize(widget_size, widget_size)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | 
                           Qt.WindowType.WindowStaysOnTopHint |
                           Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Animation timer for 3D rotation effect
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.animate)
        self.animation_timer.start(50)  # 20 FPS
        
    def animate(self):
        """Update animation for 3D rotation effect"""
        self.animation_angle = (self.animation_angle + 10) % 360
        self.update()
        
    def paintEvent(self, event):
        """Draw a 3D dynamite stick with animated radius visualization"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center_x = self.width() // 2
        center_y = self.height() // 2
        
        # Draw pulsating radius circle
        pulse_alpha = 80 + int(40 * math.sin(math.radians(self.animation_angle * 4)))
        radius_color = QColor(255, 215, 0, pulse_alpha)  # Pulsating gold
        
        painter.setPen(QPen(radius_color, 2, Qt.PenStyle.DashLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(center_x - self.visual_radius, center_y - self.visual_radius,
                          self.visual_radius * 2, self.visual_radius * 2)
        
        # Draw range text
        painter.setPen(QPen(QColor(255, 255, 255, 180)))
        painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        range_text = f"Range: {self.range_radius}"
        text_rect = QRect(center_x - 40, center_y - self.visual_radius - 25, 80, 20)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, range_text)
        
        # Draw 3D dynamite stick with perspective
        self.draw_3d_dynamite(painter, center_x, center_y)
        
    def draw_3d_dynamite(self, painter, center_x, center_y):
        """Draw a 3D perspective dynamite stick"""
        # Calculate 3D rotation
        rotation = math.radians(self.animation_angle)
        scale = 0.8 + 0.2 * math.sin(math.radians(self.animation_angle * 2))  # Bouncing effect
        
        # Dynamite dimensions
        length = 60 * scale
        width = 20 * scale
        height = 20 * scale
        
        # 3D transformation points
        points_3d = [
            (-length/2, -width/2, -height/2),  # 0: back-left-bottom
            ( length/2, -width/2, -height/2),  # 1: front-left-bottom
            ( length/2,  width/2, -height/2),  # 2: front-right-bottom
            (-length/2,  width/2, -height/2),  # 3: back-right-bottom
            (-length/2, -width/2,  height/2),  # 4: back-left-top
            ( length/2, -width/2,  height/2),  # 5: front-left-top
            ( length/2,  width/2,  height/2),  # 6: front-right-top
            (-length/2,  width/2,  height/2),  # 7: back-right-top
        ]
        
        # Apply 3D rotation and project to 2D
        points_2d = []
        for x, y, z in points_3d:
            # Rotate around Y axis
            x_rot = x * math.cos(rotation) + z * math.sin(rotation)
            y_rot = y
            z_rot = -x * math.sin(rotation) + z * math.cos(rotation)
            
            # Simple perspective projection
            perspective = 1 + z_rot * 0.001
            x_proj = center_x + x_rot * perspective
            y_proj = center_y + y_rot * perspective
            
            points_2d.append((x_proj, y_proj))
        
        # Draw 3D dynamite faces
        self.draw_3d_cube(painter, points_2d)
        
        # Draw fuse with animation
        self.draw_animated_fuse(painter, center_x, center_y, rotation, scale)
        
        # Draw tool type text
        painter.setPen(QPen(QColor(255, 255, 255)))
        painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        text_rect = QRect(center_x - 30, center_y + 40, 60, 20)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self.tool_type)
        
    def draw_3d_cube(self, painter, points):
        """Draw the 3D cube representing the dynamite stick"""
        # Define faces (vertices indices)
        faces = [
            ([0, 1, 2, 3], QColor(139, 0, 0)),    # Bottom - Dark Red
            ([4, 5, 6, 7], QColor(160, 0, 0)),    # Top - Lighter Red
            ([0, 1, 5, 4], QColor(120, 0, 0)),    # Left - Darker Red
            ([2, 3, 7, 6], QColor(120, 0, 0)),    # Right - Darker Red
            ([0, 3, 7, 4], QColor(101, 67, 33)),  # Back - Brown
            ([1, 2, 6, 5], QColor(101, 67, 33)),  # Front - Brown
        ]
        
        # Draw each face
        for vertex_indices, color in faces:
            path = QPainterPath()
            first_point = points[vertex_indices[0]]
            path.moveTo(first_point[0], first_point[1])
            
            for i in vertex_indices[1:]:
                path.lineTo(points[i][0], points[i][1])
            path.closeSubpath()
            
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor(50, 50, 50), 1))
            painter.drawPath(path)
    
    def draw_animated_fuse(self, painter, center_x, center_y, rotation, scale):
        """Draw animated fuse with sparks"""
        # Fuse position (attached to front of dynamite)
        fuse_length = 25 * scale
        fuse_start_x = center_x + 30 * math.cos(rotation) * scale
        fuse_start_y = center_y - 30 * math.sin(rotation) * scale
        
        # Animated fuse end with sparks
        spark_phase = math.sin(math.radians(self.animation_angle * 8))
        fuse_end_x = fuse_start_x + fuse_length * math.cos(rotation + 0.3)
        fuse_end_y = fuse_start_y - fuse_length * math.sin(rotation + 0.3)
        
        # Draw fuse
        fuse_color = QColor(255, 215, 0)  # Gold
        painter.setPen(QPen(fuse_color, 3))
        painter.drawLine(int(fuse_start_x), int(fuse_start_y), 
                        int(fuse_end_x), int(fuse_end_y))
        
        # Draw sparks
        if spark_phase > 0:
            spark_size = 3 + int(2 * spark_phase)
            spark_color = QColor(255, 255, 0, int(200 * spark_phase))
            painter.setPen(QPen(spark_color, 2))
            
            # Multiple spark lines
            for i in range(3):
                angle = rotation + (i * math.pi / 4)
                spark_end_x = fuse_end_x + spark_size * math.cos(angle)
                spark_end_y = fuse_end_y - spark_size * math.sin(angle)
                painter.drawLine(int(fuse_end_x), int(fuse_end_y),
                               int(spark_end_x), int(spark_end_y))
    
    def closeEvent(self, event):
        """Clean up animation timer"""
        self.animation_timer.stop()
        super().closeEvent(event)


class DraggableDynamiteTool(QWidget):
    """Draggable dynamite tool with drag & drop functionality"""
    
    # Signals for drag events
    dragStarted = pyqtSignal(object)  # Emits the tool instance
    dragFinished = pyqtSignal(object, QPointF)  # Emits tool and global position
    
    def __init__(self, tool_type, range_radius, sensor_value, parent=None):
        super().__init__(parent)
        self.tool_type = tool_type
        self.range_radius = range_radius
        self.sensor_value = sensor_value
        self.is_dragging = False
        self.drag_start_pos = None
        self.drag_widget = None
        
        self.setFixedSize(70, 70)  # Slightly larger for better visual
        self.setStyleSheet("""
            DraggableDynamiteTool {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #8B4513, stop:0.4 #A0522D, stop:0.6 #8B4513,
                    stop:1 #654321);
                border: 2px solid #5D4037;
                border-radius: 10px;
            }
            DraggableDynamiteTool:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #9C661F, stop:0.4 #B8860B, stop:0.6 #9C661F,
                    stop:1 #765432);
                border: 2px solid #FFD700;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)
        
        # Tool icon - using 3D-like representation
        icon_label = QLabel("🧨")  # Firecracker emoji as icon
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        icon_label.setStyleSheet("color: #FFD700; background: transparent;")
        layout.addWidget(icon_label)
        
        # Tool name
        name_label = QLabel(tool_type)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        name_label.setStyleSheet("color: #FFFFFF; background: transparent;")
        layout.addWidget(name_label)
        
        # Range indicator with visual bar
        range_layout = QHBoxLayout()
        range_label = QLabel(f"R:{range_radius}")
        range_label.setFont(QFont("Arial", 8))
        range_label.setStyleSheet("color: #CCCCCC; background: transparent;")
        range_layout.addWidget(range_label)
        
        # Visual range indicator bar
        range_bar = QLabel()
        range_bar.setFixedHeight(4)
        bar_width = min(range_radius * 2, 40)  # Scale bar width with range
        range_bar.setFixedWidth(bar_width)
        range_bar.setStyleSheet(f"""
            QLabel {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00FF00, stop:0.5 #FFFF00, stop:1 #FF0000);
                border-radius: 2px;
            }}
        """)
        range_layout.addWidget(range_bar)
        range_layout.addStretch()
        
        layout.addLayout(range_layout)
        
        # Set tooltip
        self.setToolTip(f"💣 {tool_type}\n🎯 Range: {range_radius}m\n⚡ Sensor Effect: {sensor_value}")

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_pos = event.position().toPoint()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() & Qt.MouseButton.LeftButton and self.drag_start_pos:
            if (event.position().toPoint() - self.drag_start_pos).manhattanLength() > QApplication.startDragDistance():
                if not self.is_dragging:
                    self.startDrag()

    def startDrag(self):
        """Start the drag operation with 3D dynamite widget"""
        self.is_dragging = True
        
        # Create 3D dynamite drag widget with radius visualization
        self.drag_widget = Dynamite3DDragWidget(self.tool_type, self.range_radius)
        self.drag_widget.show()
        
        # Change cursor to crosshair for precision dropping
        QApplication.setOverrideCursor(QCursor(Qt.CursorShape.CrossCursor))
        
        # Emit signal
        self.dragStarted.emit(self)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self.is_dragging:
            self.is_dragging = False
            if self.drag_widget:
                self.drag_widget.close()  # This will stop the animation timer
                self.drag_widget.deleteLater()
                self.drag_widget = None
            
            QApplication.restoreOverrideCursor()
            # Emit the global position directly
            self.dragFinished.emit(self, event.globalPosition())
        
        self.drag_start_pos = None

    def updateDragPosition(self, global_pos):
        """Update drag widget position during drag"""
        if self.is_dragging and self.drag_widget:
            # Convert QPointF to integers for move() method
            pos_x = int(global_pos.x() - self.drag_widget.width() // 2)
            pos_y = int(global_pos.y() - self.drag_widget.height() // 2)
            self.drag_widget.move(pos_x, pos_y)


class COCToolbar(QWidget):
    """Collapsible COC-style toolbar that can be shown/hidden"""
    
    # Signal emitted when a tool is dropped and when persistent dynamite is created
    toolDropped = pyqtSignal(object, QPointF)  # tool, global_position
    dynamitePlaced = pyqtSignal(object, QPointF)  # tool, global_position for persistent placement
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setParent(parent)
        
        # Toolbar state
        self.is_expanded = False
        self.animation_duration = 300
        self.current_dragged_tool = None
        self.placed_dynamites = []  # Track all placed dynamites
        
        # Setup UI
        self.setup_ui()
        
        # Create animation for expand/collapse
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(self.animation_duration)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Set initial state (collapsed)
        self.collapse()
        
    def setup_ui(self):
        """Initialize the toolbar UI"""
        # Main layout
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Toggle button (always visible)
        self.toggle_btn = QPushButton("🧨")  # Changed to firecracker emoji
        self.toggle_btn.setFixedSize(40, 60)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4A4A4A, stop:0.3 #2D2D2D, stop:0.7 #1A1A1A,
                    stop:1 #0D0D0D);
                border: 2px solid #8B6914;
                border-right: none;
                border-radius: 8px 0px 0px 8px;
                color: #FFD700;
                font-weight: bold;
                font-size: 18px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5A5A5A, stop:0.3 #3D3D3D, stop:0.7 #2A2A2A,
                    stop:1 #1D1D1D);
                border: 2px solid #FFD700;
                border-right: none;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3A3A3A, stop:0.3 #1D1D1D, stop:0.7 #0A0A0A,
                    stop:1 #000000);
            }
        """)
        self.toggle_btn.clicked.connect(self.toggle)
        self.main_layout.addWidget(self.toggle_btn)
        
        # Tools container (scrollable area for tools)
        self.tools_container = QFrame()
        self.tools_container.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2D2D2D, stop:0.15 #1A1A1A, stop:0.85 #1A1A1A,
                    stop:1 #2D2D2D);
                border: 2px solid #8B6914;
                border-left: none;
                border-radius: 0px 8px 8px 0px;
            }
        """)
        self.tools_container.setFixedHeight(74)  # Increased height for larger tools
        
        # Tools layout
        self.tools_layout = QHBoxLayout(self.tools_container)
        self.tools_layout.setContentsMargins(10, 5, 10, 5)
        self.tools_layout.setSpacing(8)
        self.tools_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # Create demo tools
        self.create_demo_tools()
        
        self.main_layout.addWidget(self.tools_container)
        
        # Install event filter for global mouse tracking
        QApplication.instance().installEventFilter(self)
        
    def create_demo_tools(self):
        """Create demo dynamite tools with different ranges"""
        tools_data = [
            ("TNT", 50, 80),      # Large range
            ("Dyna-S", 30, 60),   # Medium range
            ("Mega-B", 70, 95),   # Very large range
            ("Micro-D", 20, 40),  # Small range
            ("Nano-X", 15, 30),   # Very small range
            ("Thermo", 60, 85),   # Large range
            ("Geo-B", 45, 70),    # Medium-large range
            ("Hydro", 35, 65)     # Medium range
        ]
        
        self.tools = []
        for tool_type, range_radius, sensor_value in tools_data:
            tool = DraggableDynamiteTool(tool_type, range_radius, sensor_value)
            tool.dragStarted.connect(self.on_tool_drag_started)
            tool.dragFinished.connect(self.on_tool_drag_finished)
            self.tools_layout.addWidget(tool)
            self.tools.append(tool)
    
    def on_tool_drag_started(self, tool):
        """Handle tool drag start"""
        self.current_dragged_tool = tool
        print(f"Started dragging: {tool.tool_type} (Range: {tool.range_radius})")
    
    def on_tool_drag_finished(self, tool, global_position):
        """Handle tool drag finish - create persistent dynamite"""
        if self.current_dragged_tool == tool:
            self.current_dragged_tool = None
            
            # Create persistent dynamite that stays in place
            persistent_dynamite = PersistentDynamiteWidget(
                tool.tool_type, tool.range_radius, global_position, self.parent()
            )
            persistent_dynamite.show()
            self.placed_dynamites.append(persistent_dynamite)
            
            # Emit both signals for compatibility
            self.toolDropped.emit(tool, global_position)
            self.dynamitePlaced.emit(tool, global_position)
            
            print(f"Placed persistent {tool.tool_type} at {global_position}")
            print(f"Total dynamites placed: {len(self.placed_dynamites)}")
    
    def clear_all_dynamites(self):
        """Remove all placed dynamites"""
        for dynamite in self.placed_dynamites:
            dynamite.close()
            dynamite.deleteLater()
        self.placed_dynamites.clear()
        print("Cleared all placed dynamites")
    
    def get_placed_dynamites(self):
        """Get information about all placed dynamites"""
        return [dynamite.get_dynamite_info() for dynamite in self.placed_dynamites]
    
    def eventFilter(self, obj, event):
        """Global event filter to track mouse movement during drag"""
        if (event.type() == QEvent.Type.MouseMove and 
            self.current_dragged_tool and 
            self.current_dragged_tool.is_dragging):
            
            self.current_dragged_tool.updateDragPosition(event.globalPosition().toPoint())
        
        return super().eventFilter(obj, event)
    
    def toggle(self):
        """Toggle between expanded and collapsed states"""
        if self.is_expanded:
            self.collapse()
        else:
            self.expand()
    
    def expand(self):
        """Expand the toolbar"""
        if self.is_expanded:
            return
            
        self.is_expanded = True
        
        # Calculate expanded width (tools width + padding)
        expanded_width = 450  # Slightly wider for larger tools
        
        # Get current geometry
        current_geo = self.geometry()
        
        # Animate to expanded state
        self.animation.setStartValue(current_geo)
        self.animation.setEndValue(current_geo.adjusted(0, 0, expanded_width, 0))
        self.animation.start()
        
        # Update toggle button indicator
        self.toggle_btn.setText("◀")
    
    def collapse(self):
        """Collapse the toolbar"""
        if not self.is_expanded:
            return
            
        self.is_expanded = False
        
        # Calculate collapsed width (just toggle button)
        collapsed_width = 40
        
        # Get current geometry
        current_geo = self.geometry()
        
        # Animate to collapsed state
        self.animation.setStartValue(current_geo)
        self.animation.setEndValue(current_geo.adjusted(0, 0, -(current_geo.width() - collapsed_width), 0))
        self.animation.start()
        
        # Update toggle button indicator
        self.toggle_btn.setText("🧨")  # Changed to firecracker emoji
    
    def add_tool(self, tool_type, range_radius, sensor_value):
        """Add a new tool to the toolbar"""
        tool = DraggableDynamiteTool(tool_type, range_radius, sensor_value)
        tool.dragStarted.connect(self.on_tool_drag_started)
        tool.dragFinished.connect(self.on_tool_drag_finished)
        self.tools_layout.addWidget(tool)
        self.tools.append(tool)
        
        # If adding first tool and collapsed, auto-expand
        if len(self.tools) == 1 and not self.is_expanded:
            self.expand()
    
    def remove_tool(self, tool_type):
        """Remove a tool from the toolbar by type"""
        for tool in self.tools:
            if tool.tool_type == tool_type:
                tool.dragStarted.disconnect()
                tool.dragFinished.disconnect()
                self.tools_layout.removeWidget(tool)
                tool.deleteLater()
                self.tools.remove(tool)
                break
    
    def get_tools(self):
        """Get list of available tools"""
        return self.tools
    
    def clear_tools(self):
        """Remove all tools from toolbar"""
        for tool in self.tools[:]:
            self.remove_tool(tool.tool_type)
    
    def paintEvent(self, event):
        """Custom paint event for additional styling"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw subtle glow effect when expanded
        if self.is_expanded:
            pen = QPen(QColor(255, 215, 0, 60))
            pen.setWidth(3)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 8, 8)


class MainToolbar(QWidget):
    """Main toolbar container that can be placed in main window"""
    
    # Forward the toolDropped signal
    toolDropped = pyqtSignal(object, QPointF)
    dynamitePlaced = pyqtSignal(object, QPointF)  # New signal for persistent dynamites
    
    def __init__(self, main_window=None):
        super().__init__(main_window)
        self.main_window = main_window
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the main toolbar layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create the COC-style toolbar
        self.coc_toolbar = COCToolbar(self)
        self.coc_toolbar.toolDropped.connect(self.toolDropped)
        self.coc_toolbar.dynamitePlaced.connect(self.dynamitePlaced)
        layout.addWidget(self.coc_toolbar)
        
        # Add some spacing and info label
        info_label = QLabel("🧨 Drag 3D dynamite to place - Multiple dynamites can be placed")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setFont(QFont("Arial", 9))
        info_label.setStyleSheet("""
            QLabel {
                color: #FFD700;
                background: transparent;
                padding: 5px;
                font-weight: bold;
            }
        """)
        layout.addWidget(info_label)
    
    def get_toolbar(self):
        """Get the COC toolbar instance"""
        return self.coc_toolbar
    
    def add_dynamite_tool(self, tool_type, range_radius, sensor_value):
        """Add a dynamite tool to the toolbar"""
        self.coc_toolbar.add_tool(tool_type, range_radius, sensor_value)
    
    def remove_dynamite_tool(self, tool_type):
        """Remove a dynamite tool from the toolbar"""
        self.coc_toolbar.remove_tool(tool_type)
    
    def toggle_toolbar(self):
        """Toggle toolbar visibility"""
        self.coc_toolbar.toggle()
    
    def expand_toolbar(self):
        """Expand the toolbar"""
        self.coc_toolbar.expand()
    
    def collapse_toolbar(self):
        """Collapse the toolbar"""
        self.coc_toolbar.collapse()
    
    def clear_all_tools(self):
        """Remove all tools from toolbar"""
        self.coc_toolbar.clear_tools()
    
    def clear_all_dynamites(self):
        """Remove all placed dynamites"""
        self.coc_toolbar.clear_all_dynamites()
    
    def get_placed_dynamites(self):
        """Get information about all placed dynamites"""
        return self.coc_toolbar.get_placed_dynamites()
    
    def get_available_tools(self):
        """Get list of all available tools"""
        return self.coc_toolbar.get_tools()