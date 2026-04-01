# simulation.py - Full Simulation Page with Draggable Dynamite Toolbar
# Updated: embeds a compact CircularMeter inside NodeInfoPanel so sensor changes update the per-node meter
# Added: Node numbering using vtkFollower
# Integrated: NodeConnection (graph propagation of sensor changes)
# Added: Draggable dynamite toolbar with layered effect spheres
# Note: this file expects `circular_meter.py` and `nodeconnection.py` alongside it.

import numpy as np
import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QPushButton,
    QLabel, QFileDialog, QDialog, QApplication
)
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QBrush, QMouseEvent, QCursor
from PyQt6.QtCore import Qt, QPoint, pyqtSignal

from ui.gauges import FuturisticGauge
import vtk
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from scipy.spatial import cKDTree

from .circular_meter import CircularMeter
from .nodeconnection import Node, NodeConnection
from vtkmodules.vtkRenderingCore import vtkFollower
from vtkmodules.vtkRenderingFreeType import vtkVectorText

import random
import math

# ============================================
# NODE CLASS (for dynamite interaction)
# ============================================
class Node3D:
    """Represents a 3D node with position, sensor value, and visual representation."""
    def __init__(self, position, radius=5, initial_sensor=0):
        self.position = position
        self.radius = radius
        self.sensor_value = initial_sensor
        self.actor = self._create_actor()

    def _create_actor(self):
        sphere = vtk.vtkSphereSource()
        sphere.SetCenter(*self.position)
        sphere.SetRadius(self.radius)
        sphere.SetThetaResolution(16)
        sphere.SetPhiResolution(16)
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(sphere.GetOutputPort())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(0, 1, 0)
        return actor

    def react_to_dynamite(self, dynamite_pos, range_radius, sensor_value):
        dx = self.position[0] - dynamite_pos[0]
        dy = self.position[1] - dynamite_pos[1]
        dz = self.position[2] - dynamite_pos[2]
        dist = math.sqrt(dx*dx + dy*dy + dz*dz)
        if dist <= range_radius:
            self.sensor_value = sensor_value
            self.actor.GetProperty().SetColor(1, 0, 0)
            return True
        return False

    def reset(self):
        self.sensor_value = 0
        self.actor.GetProperty().SetColor(0, 1, 0)

# ============================================
# DRAGGABLE DYNAMITE
# ============================================
class DraggableDynamite(QLabel):
    """Draggable dynamite with type, range, and sensor value."""
    def __init__(self, dynamite_type, range_radius, sensor_value, parent=None):
        super().__init__(parent)
        self.dynamite_type = dynamite_type
        self.range_radius = range_radius
        self.sensor_value = sensor_value
        self.setFixedSize(50, 50)
        self.setStyleSheet("border:1px solid gray; background-color:#555;")
        self.dragging = False
        self.drag_start_pos = None
        self.floating_label = None

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_pos = event.position().toPoint()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() & Qt.MouseButton.LeftButton:
            if (event.position() - self.drag_start_pos).manhattanLength() > QApplication.startDragDistance():
                if not self.dragging:
                    self._start_drag()

    def _start_drag(self):
        self.dragging = True
        self.floating_label = QLabel(self.parent())
        self.floating_label.setFixedSize(self.size())
        self.floating_label.setStyleSheet("border:1px solid gray; background-color:#555;")
        self.floating_label.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.floating_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.floating_label.show()
        QApplication.setOverrideCursor(QCursor(Qt.CursorShape.ClosedHandCursor))

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self.dragging:
            self.dragging = False
            if self.floating_label:
                self.floating_label.hide()
                self.floating_label.deleteLater()
                self.floating_label = None
            QApplication.restoreOverrideCursor()
            if hasattr(self.parent(), "dynamitePlaced"):
                pos = QCursor.pos()
                self.parent().dynamitePlaced.emit(pos, self)

    def updateFloatingPosition(self, global_pos):
        if self.dragging and self.floating_label:
            self.floating_label.move(global_pos.x()-self.width()//2, global_pos.y()-self.height()//2)

# =====================================================================================================
# Animated Risk Meter (global)
# =====================================================================================================
class AnimatedRiskMeter(QWidget):
    def __init__(self, title="Risk Meter"):
        super().__init__()
        self.value = 0
        self.setMinimumSize(180, 180)
        self.title_label = QLabel(title, self)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #00f9ff;")
        self.percent_label = QLabel("0%", self)
        self.percent_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.percent_label.setStyleSheet("color: #ffffff; font-weight: bold;")
        self.percent_label.setFont(QFont("Arial", 16))

    def resizeEvent(self, event):
        rect = self.rect()
        self.title_label.setGeometry(0, 0, rect.width(), 25)
        self.percent_label.setGeometry(0, rect.height() // 2 - 20, rect.width(), 40)

    def setValue(self, val):
        self.value = max(0, min(100, val))
        self.percent_label.setText(f"{int(self.value)}%")
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        size = min(rect.width(), rect.height() - 30) - 20
        center = rect.center()
        center.setY(center.y() + 10)

        painter.setPen(QPen(QColor(50, 50, 80), 6))
        painter.setBrush(QBrush(QColor(10, 10, 30)))
        painter.drawEllipse(center, size // 2, size // 2)

        arc_radius = size // 2 - 8
        angle_span = int(360 * (self.value / 100))
        grad_color = QColor.fromHsv(int(120 - (self.value * 1.2)), 255, 255)
        painter.setPen(QPen(grad_color, 14, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawArc(center.x() - arc_radius, center.y() - arc_radius,
                        arc_radius * 2, arc_radius * 2, 90 * 16, -angle_span * 16)

        painter.setPen(QPen(QColor(0, 249, 255, 80), 3))
        painter.drawEllipse(center, size // 2 + 5, size // 2 + 5)

# =====================================================================================================
# Node Info Panel (now connected to node graph)
# =====================================================================================================
class NodeInfoPanel(QDialog):
    def __init__(self, parent, node_graph: NodeConnection, node_id: int, sensors, update_callback):
        """
        node_graph: NodeConnection instance
        node_id: integer index of node
        sensors: same sensors dict as SimulationPage
        update_callback: function to call after propagation to refresh UI (SimulationPage method)
        """
        super().__init__(parent)
        self.setWindowTitle("Node Info")
        self.setStyleSheet("background-color: rgba(20,30,48,0.9); color: #fff; border-radius: 10px;")
        self.setFixedSize(300, 380)

        self.node_graph = node_graph
        self.node_id = node_id
        self.sensors = sensors
        self.update_callback = update_callback

        # Local snapshot - but UI reads from graph when refreshing for canonical values
        node = self.node_graph.nodes[node_id]
        # Ensure node has keys for all sensors
        for k in self.sensors.keys():
            if k not in node.sensors:
                node.sensors[k] = 0.0

        self.local_sensor_values = dict(node.sensors)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        title_row = QHBoxLayout()
        self.title_label = QLabel(f"Node {node_id+1}")
        self.title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color:#00f9ff;")
        title_row.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignLeft)

        self.local_meter = CircularMeter(diameter=96)
        title_row.addWidget(self.local_meter, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addLayout(title_row)

        self.node_risk_label = QLabel("Node Risk: 0%")
        self.node_risk_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.node_risk_label.setStyleSheet("color:#ffcc00;")
        layout.addWidget(self.node_risk_label, alignment=Qt.AlignmentFlag.AlignCenter)

        sensors_frame = QFrame()
        sensors_frame.setStyleSheet("""
            QFrame { background-color: rgba(30,40,60,0.35); border-radius:8px; border:1px solid #1a2a3a; }
        """)
        sensors_layout = QVBoxLayout(sensors_frame)
        sensors_layout.setContentsMargins(8, 8, 8, 8)
        sensors_layout.setSpacing(6)

        self.sensor_labels = {}
        for key, (gauge, (min_v, max_v)) in self.sensors.items():
            row = QHBoxLayout()
            val = self.node_graph.nodes[self.node_id].get_sensor(key, 0.0)
            lbl = QLabel(f"{key}: {val:.2f}")
            lbl.setFont(QFont("Arial", 10))
            lbl.setStyleSheet("color: #ffffff;")
            self.sensor_labels[key] = lbl

            minus_btn = QPushButton("–")
            minus_btn.setFixedWidth(30)
            plus_btn = QPushButton("+")
            plus_btn.setFixedWidth(30)

            minus_btn.setStyleSheet("QPushButton{background:#2a2a2a;color:#fff;border-radius:4px;} QPushButton:pressed{background:#3a3a3a;}")
            plus_btn.setStyleSheet("QPushButton{background:#2a2a2a;color:#fff;border-radius:4px;} QPushButton:pressed{background:#3a3a3a;}")

            # Use default args to capture key correctly
            minus_btn.clicked.connect(lambda _, k=key: self.adjust_sensor(k, -1))
            plus_btn.clicked.connect(lambda _, k=key: self.adjust_sensor(k, +1))

            row.addWidget(lbl)
            row.addWidget(minus_btn)
            row.addWidget(plus_btn)
            sensors_layout.addLayout(row)

        layout.addWidget(sensors_frame, stretch=1)

        footer_row = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setMinimumHeight(30)
        self.refresh_btn.clicked.connect(self.refresh)
        footer_row.addWidget(self.refresh_btn)

        info_lbl = QLabel("Adjust sensors → propagates to network")
        info_lbl.setFont(QFont("Arial", 9))
        info_lbl.setStyleSheet("color:#cfd8ff;")
        footer_row.addWidget(info_lbl, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addLayout(footer_row)

        self.recalculate_risk()

    # ---------------- Adjust Sensor ----------------
    def adjust_sensor(self, key, step):
        min_v, max_v = self.sensors[key][1]
        old_val = self.node_graph.nodes[self.node_id].get_sensor(key, 0.0)
        new_val = max(min_v, min(max_v, old_val + step))
        delta = new_val - old_val
        if abs(delta) < 1e-9:
            return

        # Apply & propagate through graph
        self.node_graph.propagate_change(self.node_id, key, delta)

        # Refresh the panel (reads fresh from node_graph)
        self.refresh()

        # Notify simulation page to update gauges/visuals
        if callable(self.update_callback):
            self.update_callback()

    # ---------------- Recalculate Risk ----------------
    def recalculate_risk(self):
        normalized_vals = []
        for key, (gauge, (min_v, max_v)) in self.sensors.items():
            val = self.node_graph.nodes[self.node_id].get_sensor(key, 0.0)
            denom = (max_v - min_v) if (max_v - min_v) != 0 else 1.0
            norm = (val - min_v) / denom * 100
            normalized_vals.append(norm)

        avg_norm = sum(normalized_vals) / len(normalized_vals) if normalized_vals else 0.0
        self.local_meter.setValue(max(0.0, min(1.0, avg_norm / 100.0)))
        self.node_risk_label.setText(f"Node Risk: {avg_norm:.1f}%")

    # ---------------- Refresh UI ----------------
    def refresh(self):
        for key, lbl in self.sensor_labels.items():
            val = self.node_graph.nodes[self.node_id].get_sensor(key, 0.0)
            lbl.setText(f"{key}: {val:.2f}")
        self.recalculate_risk()


# =====================================================================================================
# Simulation Page
# =====================================================================================================
class SimulationPage(QWidget):
    dynamitePlaced = pyqtSignal(QPoint, DraggableDynamite)

    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)

        # ---------------- Left Panel ----------------
        left = QVBoxLayout()
        left.setSpacing(15)

        control_frame = QFrame()
        control_frame.setStyleSheet("""
            QFrame { background-color: rgba(20,30,48,0.7); border-radius:10px; border:1px solid #1a2a3a; }
        """)
        control_layout = QVBoxLayout(control_frame)
        control_layout.setContentsMargins(10, 10, 10, 10)

        self.model_btn = QPushButton("Upload 3D Model")
        self.csv_btn = QPushButton("Upload Sensor CSV")
        for btn in [self.model_btn, self.csv_btn]:
            btn.setMinimumHeight(40)
            btn.setStyleSheet("""
                QPushButton {background-color:#1a2a2a;color:#00f9ff;border:none;border-radius:8px;font-weight:bold;}
                QPushButton:hover {background-color:#2a3a4a;}
                QPushButton:pressed {background-color:#3a4a5a;}
            """)
            control_layout.addWidget(btn)
        left.addWidget(control_frame)

        # 3D VTK Widget
        self.vtk_widget = QVTKRenderWindowInteractor(self)
        left.addWidget(self.vtk_widget, stretch=1)
        layout.addLayout(left, 2)

        # ---------------- Right Panel (Risk + Sensors + Timestamp) ----------------
        right = QVBoxLayout()
        right.setSpacing(15)

        risk_frame = QFrame()
        risk_frame.setStyleSheet("""
            QFrame {background-color: rgba(20,30,48,0.7); border-radius:10px; border:1px solid #1a2a3a;}
        """)
        risk_layout = QVBoxLayout(risk_frame)
        self.risk_meter = AnimatedRiskMeter()
        risk_layout.addWidget(self.risk_meter, alignment=Qt.AlignmentFlag.AlignCenter)
        right.addWidget(risk_frame)

        sensors_frame = QFrame()
        sensors_frame.setStyleSheet("""
            QFrame {background-color: rgba(20,30,48,0.7); border-radius:10px; border:1px solid #1a2a3a;}
        """)
        sensors_layout = QVBoxLayout(sensors_frame)
        sensors_layout.setContentsMargins(10, 10, 10, 10)
        self.sensors = {
            "Temperature_C": (FuturisticGauge("Temperature", "°C"), (0, 60)),
            "Humidity_%": (FuturisticGauge("Humidity", "%"), (0, 100)),
            "GroundPressure_kPa": (FuturisticGauge("Ground Pressure", "kPa"), (80, 120)),
            "Vibration_mm_s": (FuturisticGauge("Vibration", "mm/s"), (0, 10)),
            "CrackWidth_mm": (FuturisticGauge("Crack Width", "mm"), (0, 5)),
            "Rainfall_mm": (FuturisticGauge("Rainfall", "mm"), (0, 200))
        }
        for g, _ in self.sensors.values():
            sensors_layout.addWidget(g)
        right.addWidget(sensors_frame)

        timestamp_frame = QFrame()
        timestamp_frame.setStyleSheet("""
            QFrame {background-color: rgba(20,30,48,0.7); border-radius:10px; border:1px solid #1a2a3a;}
        """)
        timestamp_layout = QVBoxLayout(timestamp_frame)
        timestamp_layout.setContentsMargins(10, 10, 10, 10)
        self.timestamp_label = QLabel("Timestamp: --")
        self.timestamp_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.timestamp_label.setStyleSheet("color:#ffcc00; padding:6px;")
        timestamp_layout.addWidget(self.timestamp_label)
        self.node_info_label = QLabel("Right-click on a stress node to view info")
        self.node_info_label.setFont(QFont("Arial", 10))
        self.node_info_label.setStyleSheet("color:#ff9900; padding:6px;")
        timestamp_layout.addWidget(self.node_info_label)
        right.addWidget(timestamp_frame)

        layout.addLayout(right, 1)

        # ---------------- Core Attributes ----------------
        self.model_btn.clicked.connect(self.load_model)
        self.csv_btn.clicked.connect(self.load_csv)
        self.csv_data = None
        self.vertices = None
        self.info_panel = None

        self.renderer = vtk.vtkRenderer()
        self.vtk_widget.GetRenderWindow().AddRenderer(self.renderer)
        self.interactor = self.vtk_widget.GetRenderWindow().GetInteractor()

        self.stress_nodes = []   # list of VTK actors (spheres)
        self.node_labels = []    # list of vtkFollower labels
        self.mesh_actor = None
        self.actor_to_nodeid = {}
        self.node_graph = NodeConnection()
        self.picker = vtk.vtkPropPicker()
        self.interactor.SetPicker(self.picker)
        self.interactor.AddObserver("RightButtonPressEvent", self.on_right_click)

      
    # ---------------- Load Model ----------------
    def load_model(self):
        f, _ = QFileDialog.getOpenFileName(self, "Select 3D Model", "", "3D Models (*.obj *.ply *.stl)")
        if not f:
            return
        try:
            import trimesh
            mesh = trimesh.load(f)
            if not isinstance(mesh, trimesh.Trimesh):
                mesh = mesh.dump(concatenate=True)
            self.vertices = mesh.vertices
            faces = mesh.faces

            points = vtk.vtkPoints()
            for v in self.vertices:
                points.InsertNextPoint(v.tolist())

            poly = vtk.vtkPolyData()
            poly.SetPoints(points)

            triangles = vtk.vtkCellArray()
            for f in faces:
                tri = vtk.vtkTriangle()
                tri.GetPointIds().SetId(0, f[0])
                tri.GetPointIds().SetId(1, f[1])
                tri.GetPointIds().SetId(2, f[2])
                triangles.InsertNextCell(tri)
            poly.SetPolys(triangles)

            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputData(poly)
            self.mesh_actor = vtk.vtkActor()
            self.mesh_actor.SetMapper(mapper)
            self.mesh_actor.GetProperty().SetColor(0.3, 0.8, 0.9)

            # 🔹 Enable edge overlay (like Blender) — must run after actor exists
            self.mesh_actor.GetProperty().EdgeVisibilityOn()
            self.mesh_actor.GetProperty().SetEdgeColor(0.1, 0.1, 0.1)  # dark gray edges
            self.mesh_actor.GetProperty().SetLineWidth(1)

            self.renderer.AddActor(self.mesh_actor)

            self.renderer.ResetCamera()
            self.vtk_widget.GetRenderWindow().Render()
        except Exception as e:
            print("Error loading 3D model:", e)

    # ---------------- Load CSV ----------------
    def load_csv(self):
        f, _ = QFileDialog.getOpenFileName(self, "Select CSV", "", "CSV Files (*.csv)")
        if not f:
            return
        try:
            self.csv_data = pd.read_csv(f)
            if self.csv_data.empty or len(self.csv_data) < 3:
                return
            row = self.csv_data.iloc[2]  # 3rd row only
            self.apply_row_data(row)
            self.add_stress_nodes_from_csv()
        except Exception as e:
            print("Error loading CSV:", e)

    # ---------------- Apply Row Data Once ----------------
    def apply_row_data(self, row):
        if "Timestamp" in row:
            self.timestamp_label.setText(f"Timestamp: {row['Timestamp']}")

        normalized_vals = []
        for key, (gauge, (min_v, max_v)) in self.sensors.items():
            if key in row:
                val = float(row[key])
                try:
                    gauge.update_value(val, min_v, max_v)
                except Exception:
                    pass
                gauge.current_value = val
                denom = (max_v - min_v) if (max_v - min_v) != 0 else 1.0
                norm = (val - min_v) / denom * 100
                normalized_vals.append(norm)

        if normalized_vals:
            avg_norm = sum(normalized_vals) / len(normalized_vals)
            self.risk_meter.setValue(avg_norm)

    # ---------------- Add Stress Nodes ----------------
    def add_stress_nodes_from_csv(self):
        # prerequisites
        if self.mesh_actor is None or self.vertices is None:
            return

        # clear previous actors and graph
        for a in self.stress_nodes + self.node_labels:
            try:
                self.renderer.RemoveActor(a)
            except Exception:
                pass
        self.stress_nodes.clear()
        self.node_labels.clear()
        self.actor_to_nodeid.clear()

        # reset node graph
        self.node_graph = NodeConnection()

        num_nodes = min(200, len(self.vertices))
        mesh_bounds = self.mesh_actor.GetBounds()
        mesh_scale = max(mesh_bounds[1]-mesh_bounds[0],
                         mesh_bounds[3]-mesh_bounds[2],
                         mesh_bounds[5]-mesh_bounds[4])
        radius = mesh_scale * 0.005

        chosen_indices = np.random.choice(len(self.vertices), num_nodes, replace=False)
        node_positions = [self.vertices[idx] for idx in chosen_indices]

        heatmap_colors = [
            (1.0, 1.0, 0.0),
            (1.0, 0.65, 0.0),
            (1.0, 0.0, 0.0)
        ]

        # Create Node objects and VTK spheres/labels
        for idx, pos in enumerate(node_positions):
            # create Node with initial sensor values taken from global gauges' current_value if available
            initial_sensors = {}
            for key, (gauge, (min_v, max_v)) in self.sensors.items():
                initial_sensors[key] = getattr(gauge, "current_value", 0.0)

            node = Node(node_id=idx, position=tuple(pos), sensors=initial_sensors)
            self.node_graph.add_node(node)

            # --- Sphere Node (visual) ---
            sphere = vtk.vtkSphereSource()
            sphere.SetCenter(pos.tolist())
            sphere.SetRadius(radius)
            sphere.SetThetaResolution(6)
            sphere.SetPhiResolution(6)
            sphere.Update()

            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(sphere.GetOutputPort())
            actor = vtk.vtkActor()
            actor.SetMapper(mapper)

            color = heatmap_colors[np.random.randint(0, len(heatmap_colors))]
            actor.GetProperty().SetColor(color)
            actor.GetProperty().SetSpecular(0.2)
            actor.GetProperty().SetSpecularPower(8)
            actor.GetProperty().SetAmbient(0.3)

            self.renderer.AddActor(actor)
            self.stress_nodes.append(actor)
            self.actor_to_nodeid[actor] = idx

            # --- Node Number Label ---
            text = vtkVectorText()
            text.SetText(str(idx + 1))
            text_mapper = vtk.vtkPolyDataMapper()
            text_mapper.SetInputConnection(text.GetOutputPort())
            text_actor = vtkFollower()
            text_actor.SetMapper(text_mapper)
            text_actor.SetScale(radius*0.5, radius*0.5, radius*0.5)
            text_actor.SetPosition(pos.tolist())
            text_actor.GetProperty().SetColor(1.0, 1.0, 1.0)
            text_actor.SetCamera(self.renderer.GetActiveCamera())
            self.renderer.AddActor(text_actor)
            self.node_labels.append(text_actor)

        # Connect nearby nodes both visually and in graph
        adjacency_radius = mesh_scale * 0.03
        tree = cKDTree(node_positions)
        for i, pos in enumerate(node_positions):
            neighbors = tree.query_ball_point(pos, adjacency_radius)
            for j in neighbors:
                if i >= j:
                    continue
                # add visual line
                line = vtk.vtkLineSource()
                line.SetPoint1(pos.tolist())
                line.SetPoint2(node_positions[j].tolist())
                line.Update()

                line_mapper = vtk.vtkPolyDataMapper()
                line_mapper.SetInputConnection(line.GetOutputPort())
                line_actor = vtk.vtkActor()
                line_actor.SetMapper(line_mapper)
                line_actor.GetProperty().SetColor(0.5, 0.5, 1.0)
                line_actor.GetProperty().SetLineWidth(2)
                self.renderer.AddActor(line_actor)

                # add logical connection
                try:
                    self.node_graph.add_connection(i, j)
                except Exception:
                    # if nodes missing - should not happen
                    pass

        # final render
        self.vtk_widget.GetRenderWindow().Render()

        # update the UI gauges to reflect first node / aggregated values if desired
        self.update_gauges_from_graph()

    # ---------------- Update UI after graph changes ----------------
    def update_gauges_from_graph(self):
        """
        Update the right-panel FuturisticGauges and the global risk meter
        by aggregating node_graph values (simple average across nodes).
        """
        if not self.node_graph.nodes:
            return

        # For each sensor, compute average across nodes
        sensor_sums = {k: 0.0 for k in self.sensors.keys()}
        count = len(self.node_graph.nodes)
        for node in self.node_graph.nodes.values():
            for k in sensor_sums.keys():
                sensor_sums[k] += node.get_sensor(k, 0.0)

        # Update gauges
        normalized_vals = []
        for k, (gauge, (min_v, max_v)) in self.sensors.items():
            avg = sensor_sums[k] / count if count else 0.0
            try:
                gauge.update_value(avg, min_v, max_v)
            except Exception:
                pass
            gauge.current_value = avg
            denom = (max_v - min_v) if (max_v - min_v) != 0 else 1.0
            norm = (avg - min_v) / denom * 100
            normalized_vals.append(norm)

        # update global risk meter using average normalized value
        if normalized_vals:
            avg_norm = sum(normalized_vals) / len(normalized_vals)
            self.risk_meter.setValue(avg_norm)

        # optionally recolor nodes by one of the sensors (e.g., Temperature) - simple mapping
        # here we map Temperature to color from blue->yellow->red for visualization
        try:
            temps = [n.get_sensor("Temperature_C", 0.0) for n in self.node_graph.nodes.values()]
            if temps:
                tmin, tmax = min(temps), max(temps)
                rng = tmax - tmin if (tmax - tmin) != 0 else 1.0
                for actor, node_id in self.actor_to_nodeid.items():
                    temp = self.node_graph.nodes[node_id].get_sensor("Temperature_C", 0.0)
                    norm = (temp - tmin) / rng
                    # simple color ramp: 0->(0,0,1) blue; 0.5->(1,1,0) yellow; 1->(1,0,0) red
                    if norm < 0.5:
                        # mix blue to yellow
                        t = norm / 0.5
                        r = t * 1.0 + (1 - t) * 0.0
                        g = t * 1.0 + (1 - t) * 0.0
                        b = t * 0.0 + (1 - t) * 1.0
                    else:
                        t = (norm - 0.5) / 0.5
                        r = t * 1.0 + (1 - t) * 1.0
                        g = t * 0.0 + (1 - t) * 1.0
                        b = 0.0
                    try:
                        actor.GetProperty().SetColor((r, g, b))
                    except Exception:
                        pass
        except Exception:
            pass

        # render update
        self.vtk_widget.GetRenderWindow().Render()

    # ---------------- Right-Click Picker ----------------
    def on_right_click(self, obj, event):
        click_pos = self.interactor.GetEventPosition()
        self.picker.Pick(click_pos[0], click_pos[1], 0, self.renderer)
        actor = self.picker.GetActor()
        if actor in self.stress_nodes:
            node_id = self.actor_to_nodeid.get(actor, None)
            if node_id is None:
                return
                
            # Always create a new panel - this fixes the issue with stale content
            if self.info_panel is not None:
                try:
                    self.info_panel.close()
                    self.info_panel.deleteLater()
                except Exception:
                    pass
                self.info_panel = None
                
            # Create new panel for the selected node
            self.info_panel = NodeInfoPanel(
                self, 
                node_graph=self.node_graph, 
                node_id=node_id,
                sensors=self.sensors, 
                update_callback=self.update_gauges_from_graph
            )
            self.info_panel.show()

    # ---------------- Clean up on page change ----------------
    def cleanup(self):
        """Clean up resources when switching away from this page"""
        if self.info_panel is not None:
            try:
                self.info_panel.close()
                self.info_panel.deleteLater()
            except Exception:
                pass
            self.info_panel = None