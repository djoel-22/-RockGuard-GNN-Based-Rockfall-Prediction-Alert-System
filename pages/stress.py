# =====================================================================================================
# stress.py - Full Functional Stress Analysis Page (VTK + Clickable Heatmap Nodes + Info Panel + Connectivity)
# Updated: Integrated GNN for intelligent point selection instead of random
# =====================================================================================================

import numpy as np
import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QPushButton,
    QLabel, QFileDialog, QDialog, QMessageBox
)
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QBrush
from PyQt6.QtCore import Qt, QTimer
import pyrebase
import time
import atexit
import os

from ui.gauges import FuturisticGauge  # adjust import as needed

# VTK imports
import vtk
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkRenderingCore import vtkFollower
from vtkmodules.vtkRenderingFreeType import vtkVectorText

# KDTree for nearest neighbor search
from scipy.spatial import cKDTree

# GNN Analyzer import
from core.stressinference import GNNAnalyzer

# Firebase configuration
FIREBASE_CONFIG = {
    "apiKey": "your-api-key",
    "authDomain": "ai-rockfall-alert-system.firebaseapp.com",
    "databaseURL": "https://ai-rockfall-alert-system-default-rtdb.firebaseio.com/",
    "projectId": "ai-rockfall-alert-system",
    "storageBucket": "ai-rockfall-alert-system.appspot.com",
    "messagingSenderId": "your-sender-id",
    "appId": "your-app-id"
}

# =====================================================================================================
# Firebase Manager
# =====================================================================================================
class FirebaseManager:
    def __init__(self):
        try:
            self.firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
            self.db = self.firebase.database()
            print("Firebase connected")
            
            # Clear existing data on startup
            self.clear_all_region_data()
        except Exception as e:
            print(f"Firebase error: {e}")
            self.db = None
    
    def clear_all_region_data(self):
        """Clear all region data from Firebase on startup"""
        if not self.db:
            return
            
        try:
            self.db.child("regions").remove()
            print("Cleared all existing region data from Firebase")
        except Exception as e:
            print(f"Error clearing region data: {e}")
    
    def save_region_data(self, region, risk_percentage, node_count, representative_node_id=None):
        """Save ONE representative node data per region to Firebase"""
        if not self.db:
            return
            
        try:
            region_data = {
                "risk_percentage": risk_percentage,
                "node_count": node_count,
                "representative_node_id": representative_node_id,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self.db.child("regions").child(region).set(region_data)
            print(f"Updated {region}: {risk_percentage}% risk")
        except Exception as e:
            print(f"Error saving region data: {e}")

# =====================================================================================================
# Region Manager
# =====================================================================================================
class RegionManager:
    def __init__(self):
        self.regions = ["North", "South", "East", "West", "Central", 
                       "Northeast", "Northwest", "Southeast", "Southwest"]
    
    def get_region_for_point(self, point, mesh_bounds):
        """Simple region assignment based on position"""
        if mesh_bounds is None:
            return "Central"
            
        x_center = (point[0] - mesh_bounds[0]) / (mesh_bounds[1] - mesh_bounds[0])
        y_center = (point[1] - mesh_bounds[2]) / (mesh_bounds[3] - mesh_bounds[2])
        
        if x_center > 0.66:
            if y_center > 0.66: return "Northeast"
            elif y_center < 0.33: return "Northwest"
            else: return "North"
        elif x_center < 0.33:
            if y_center > 0.66: return "Southeast" 
            elif y_center < 0.33: return "Southwest"
            else: return "South"
        else:
            if y_center > 0.66: return "East"
            elif y_center < 0.33: return "West" 
            else: return "Central"

# =====================================================================================================
# Animated Risk Meter with title and circular progress
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
# Info Panel for Right-Click (Real-Time Updating)
# =====================================================================================================
class NodeInfoPanel(QDialog):
    def __init__(self, parent, risk_meter, sensors, num_nodes, node_id=None):
        super().__init__(parent)
        self.setWindowTitle("Node Info")
        self.setStyleSheet("background-color: rgba(20,30,48,0.9); color: #fff; border-radius: 10px;")
        self.setFixedSize(260, 320)

        self.risk_meter = risk_meter
        self.sensors = sensors
        self.num_nodes = num_nodes
        self.node_id = node_id

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Node ID display
        if self.node_id is not None:
            node_id_label = QLabel(f"Node ID: {self.node_id}")
            node_id_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            node_id_label.setStyleSheet("color: #00ff99;")
            layout.addWidget(node_id_label)

        # Node-specific risk = overall risk / number of nodes
        node_risk_value = self.risk_meter.value / self.num_nodes if self.num_nodes > 0 else 0
        self.node_risk_label = QLabel(f"Node Risk Score: {node_risk_value:.3f}%")
        self.node_risk_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(self.node_risk_label)

        # Add all sensor readings
        self.sensor_labels = {}
        for key, (gauge, _) in sensors.items():
            lbl = QLabel(f"{key}: {getattr(gauge, 'current_value', 0):.2f}")
            lbl.setFont(QFont("Arial", 11))
            layout.addWidget(lbl)
            self.sensor_labels[key] = lbl

    def refresh(self):
        # Update node risk dynamically
        node_risk_value = self.risk_meter.value / self.num_nodes if self.num_nodes > 0 else 0
        self.node_risk_label.setText(f"Node Risk Score: {node_risk_value:.3f}%")

        # Update all sensor readings dynamically
        for key, lbl in self.sensor_labels.items():
            val = getattr(self.sensors[key][0], "current_value", 0)
            lbl.setText(f"{key}: {val:.2f}")

# =====================================================================================================
# Stress Analysis Page (VTK version)
# =====================================================================================================
class StressAnalysisPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)

        # ---------------- Left panel ----------------
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
        self.analyze_btn = QPushButton("Analyze Stress Points")
        
        for btn in [self.model_btn, self.csv_btn, self.analyze_btn]:
            btn.setMinimumHeight(40)
            btn.setStyleSheet("""
                QPushButton {background-color:#1a2a3a;color:#00f9ff;border:none;border-radius:8px;font-weight:bold;}
                QPushButton:hover {background-color:#2a3a4a;}
                QPushButton:pressed {background-color:#3a4a5a;}
            """)
            control_layout.addWidget(btn)
            
        # Set specific color for analyze button
        self.analyze_btn.setStyleSheet("""
            QPushButton {background-color:#2a4a3a;color:#00ff99;border:none;border-radius:8px;font-weight:bold;}
            QPushButton:hover {background-color:#3a5a4a;}
            QPushButton:pressed {background-color:#4a6a5a;}
        """)
            
        left.addWidget(control_frame)

        self.vtk_widget = QVTKRenderWindowInteractor(self)
        left.addWidget(self.vtk_widget, stretch=1)
        layout.addLayout(left, 2)

        # ---------------- Right panel ----------------
        right = QVBoxLayout()
        right.setSpacing(15)

        # Risk Meter
        risk_frame = QFrame()
        risk_frame.setStyleSheet("""
            QFrame {background-color: rgba(20,30,48,0.7); border-radius:10px; border:1px solid #1a2a3a;}
        """)
        risk_layout = QVBoxLayout(risk_frame)
        self.risk_meter = AnimatedRiskMeter()
        risk_layout.addWidget(self.risk_meter, alignment=Qt.AlignmentFlag.AlignCenter)
        right.addWidget(risk_frame)

        # Sensors
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

        # Timestamp
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

        # ---------------- Core attributes ----------------
        self.model_btn.clicked.connect(self.load_model)
        self.csv_btn.clicked.connect(self.load_csv)
        self.analyze_btn.clicked.connect(self.analyze_stress_points)
        self.csv_data = None
        self.csv_index = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_sensors)

        self.renderer = vtk.vtkRenderer()
        self.vtk_widget.GetRenderWindow().AddRenderer(self.renderer)
        self.interactor = self.vtk_widget.GetRenderWindow().GetInteractor()

        self.stress_nodes = []        # list of vtkActor spheres
        self.node_labels = []         # list of vtkFollower text actors
        self.line_actors = []         # list of line vtkActors
        self.mesh_actor = None
        self.vertices = None
        self.faces = None
        self.info_panel = None
        
        # Connectivity: adjacency list for logical connections
        self.node_adjacency = {}
        # mapping actor -> node id
        self.node_id_map = {}

        # NEW: Firebase and region management
        self.region_manager = RegionManager()
        self.firebase_manager = FirebaseManager()
        self.node_regions = {}  # node_id: region_name
        self.region_representatives = {}  # region: representative_node_id

        # NEW: GNN Analyzer - LAZY LOADING
        self.gnn_analyzer = None
        self.model_path = r"D:\New folder (18)\pages\stability_gnn.pth"  # Your exact path
        self.current_mesh_path = None
        self.gnn_top_points = None
        self.gnn_top_indices = None

        self.picker = vtk.vtkPropPicker()
        self.interactor.SetPicker(self.picker)
        self.interactor.AddObserver("RightButtonPressEvent", self.on_right_click)
        self.interactor.Initialize()

        # Register cleanup function to clear Firebase data on application exit
        atexit.register(self.cleanup_on_exit)

    def cleanup_on_exit(self):
        """Clear Firebase data when application exits"""
        print("Cleaning up Firebase data on application exit...")
        if hasattr(self, 'firebase_manager') and self.firebase_manager.db:
            try:
                self.firebase_manager.clear_all_region_data()
            except Exception as e:
                print(f"Error during cleanup: {e}")

    def closeEvent(self, event):
        """Override close event to cleanup before closing"""
        self.cleanup_on_exit()
        event.accept()

    # ---------------- DEBUG METHODS ----------------
    def debug_node_placement(self, node_positions, label="Node Placement"):
        """Debug method to check node distribution"""
        if node_positions is None or len(node_positions) == 0:
            print(f"❌ {label}: No node positions to debug")
            return
        
        # Convert to numpy for analysis
        positions = np.array(node_positions)
        
        print(f"🔍 {label} Debug:")
        print(f"   Total nodes: {len(positions)}")
        print(f"   X range: {positions[:, 0].min():.3f} to {positions[:, 0].max():.3f}")
        print(f"   Y range: {positions[:, 1].min():.3f} to {positions[:, 1].max():.3f}")
        print(f"   Z range: {positions[:, 2].min():.3f} to {positions[:, 2].max():.3f}")
        
        # Check if nodes are clustered
        x_span = positions[:, 0].max() - positions[:, 0].min()
        y_span = positions[:, 1].max() - positions[:, 1].min()
        z_span = positions[:, 2].max() - positions[:, 2].min()
        
        print(f"   Spatial spans - X: {x_span:.3f}, Y: {y_span:.3f}, Z: {z_span:.3f}")
        
        # Check if nodes are clustered in one area
        if x_span < 0.1 or y_span < 0.1 or z_span < 0.1:
            print("⚠️  WARNING: Nodes appear to be clustered in a small area!")
        
        # Check mesh bounds for comparison
        if self.mesh_actor:
            mesh_bounds = self.mesh_actor.GetBounds()
            print(f"📐 Mesh bounds:")
            print(f"   X: {mesh_bounds[0]:.3f} to {mesh_bounds[1]:.3f}")
            print(f"   Y: {mesh_bounds[2]:.3f} to {mesh_bounds[3]:.3f}")
            print(f"   Z: {mesh_bounds[4]:.3f} to {mesh_bounds[5]:.3f}")

    def compare_point_distributions(self):
        """Compare GNN points vs random points distribution"""
        if self.vertices is None:
            return
        
        # Get random points for comparison
        random_indices = np.random.choice(len(self.vertices), 200, replace=False)
        random_points = [self.vertices[idx] for idx in random_indices]
        
        print("🎲 RANDOM POINTS DISTRIBUTION:")
        self.debug_node_placement(random_points, "Random Points")
        
        if self.gnn_top_points is not None:
            print("🧠 GNN POINTS DISTRIBUTION:")
            self.debug_node_placement(self.gnn_top_points, "GNN Points")

    # ---------------- GNN DISTRIBUTION FIX ----------------
    def get_better_distributed_gnn_points(self, vertices, faces, target_points=200):
        """Run GNN multiple times with different parameters to get better distribution"""
        if self.gnn_analyzer is None or self.gnn_analyzer.model is None:
            return None, None, None, "GNN model not loaded"
        
        try:
            print("🔄 Running enhanced GNN analysis for better distribution...")
            
            # Run GNN with larger top_k to get more candidate points
            all_candidates = []
            all_scores = []
            all_indices = []
            
            # Get more candidate points (3x our target)
            top_points, top_scores, top_indices, message = self.gnn_analyzer.analyze_vertices(
                vertices, faces, top_k=600
            )
            
            if top_points is None:
                return None, None, None, message
            
            # Filter and distribute points across the mesh
            distributed_points = self.distribute_points_across_mesh(top_points, top_scores, target_points)
            
            return distributed_points, top_scores[:len(distributed_points)], top_indices[:len(distributed_points)], "Success"
            
        except Exception as e:
            return None, None, None, f"Enhanced analysis failed: {str(e)}"

    def distribute_points_across_mesh(self, points, scores, target_count):
        """Distribute GNN points more evenly across the mesh while maintaining high scores"""
        if len(points) <= target_count:
            return points[:target_count]
        
        # Get mesh bounds
        mesh_bounds = self.mesh_actor.GetBounds() if self.mesh_actor else None
        if mesh_bounds is None:
            return points[:target_count]
        
        x_min, x_max = mesh_bounds[0], mesh_bounds[1]
        y_min, y_max = mesh_bounds[2], mesh_bounds[3]
        z_min, z_max = mesh_bounds[4], mesh_bounds[5]
        
        # Create spatial bins (regions)
        num_x_bins = 3
        num_y_bins = 3
        num_z_bins = 2
        total_bins = num_x_bins * num_y_bins * num_z_bins
        
        # Initialize bins
        bins = [[] for _ in range(total_bins)]
        bin_scores = [[] for _ in range(total_bins)]
        
        # Assign points to bins
        for i, (point, score) in enumerate(zip(points, scores)):
            x, y, z = point
            
            # Calculate bin indices
            x_bin = int((x - x_min) / (x_max - x_min) * num_x_bins)
            y_bin = int((y - y_min) / (y_max - y_min) * num_y_bins)
            z_bin = int((z - z_min) / (z_max - z_min) * num_z_bins)
            
            # Clamp to valid range
            x_bin = max(0, min(num_x_bins - 1, x_bin))
            y_bin = max(0, min(num_y_bins - 1, y_bin))
            z_bin = max(0, min(num_z_bins - 1, z_bin))
            
            bin_index = x_bin + y_bin * num_x_bins + z_bin * num_x_bins * num_y_bins
            bins[bin_index].append(point)
            bin_scores[bin_index].append(score)
        
        # Distribute target points across bins
        distributed_points = []
        points_per_bin = max(1, target_count // total_bins)
        
        for bin_points, bin_scores_list in zip(bins, bin_scores):
            if bin_points:
                # Sort by score (descending) and take top points from each bin
                sorted_indices = np.argsort(bin_scores_list)[::-1]
                selected_points = [bin_points[i] for i in sorted_indices[:points_per_bin]]
                distributed_points.extend(selected_points)
        
        # If we need more points, take highest remaining scores
        if len(distributed_points) < target_count:
            remaining_points = []
            remaining_scores = []
            
            for bin_points, bin_scores_list in zip(bins, bin_scores):
                if bin_points:
                    sorted_indices = np.argsort(bin_scores_list)[::-1]
                    # Take points beyond what we already selected
                    start_index = min(points_per_bin, len(bin_points))
                    remaining_points.extend([bin_points[i] for i in sorted_indices[start_index:]])
                    remaining_scores.extend([bin_scores_list[i] for i in sorted_indices[start_index:]])
            
            # Sort remaining by score and take best ones
            if remaining_points:
                sorted_indices = np.argsort(remaining_scores)[::-1]
                needed = target_count - len(distributed_points)
                additional_points = [remaining_points[i] for i in sorted_indices[:needed]]
                distributed_points.extend(additional_points)
        
        print(f"📊 Distributed {len(distributed_points)} points across {total_bins} spatial regions")
        return distributed_points[:target_count]

    # ---------------- REGION-BASED ANALYSIS ----------------
    def force_full_mesh_coverage(self, vertices, faces, target_points=200):
        """Force GNN to analyze all regions of the mesh by splitting it into sections"""
        if self.gnn_analyzer is None or self.gnn_analyzer.model is None:
            return None, None, None, "GNN model not loaded"
        
        try:
            print("🔄 Running region-based GNN analysis for full coverage...")
            
            # Get mesh bounds
            mesh_bounds = self.mesh_actor.GetBounds() if self.mesh_actor else None
            if mesh_bounds is None:
                return None, None, None, "Mesh bounds not available"
            
            x_min, x_max = mesh_bounds[0], mesh_bounds[1]
            y_min, y_max = mesh_bounds[2], mesh_bounds[3]
            z_min, z_max = mesh_bounds[4], mesh_bounds[5]
            
            # Define regions based on your mesh analysis
            regions = [
                # Left side (currently missing) - negative X
                {"x_range": (x_min, 0), "y_range": (y_min, y_max), "z_range": (z_min, z_max), "name": "Left Side"},
                # Right side (where GNN currently finds points) - positive X
                {"x_range": (0, x_max), "y_range": (y_min, y_max), "z_range": (z_min, z_max), "name": "Right Side"},
                # Top region (currently missing) - high Y
                {"x_range": (x_min, x_max), "y_range": (80, y_max), "z_range": (z_min, z_max), "name": "Top"},
                # Bottom region - low Y
                {"x_range": (x_min, x_max), "y_range": (y_min, 80), "z_range": (z_min, z_max), "name": "Bottom"}
            ]
            
            all_region_points = []
            all_region_scores = []
            all_region_indices = []
            
            # Analyze each region separately
            for region in regions:
                region_name = region["name"]
                x_rmin, x_rmax = region["x_range"]
                y_rmin, y_rmax = region["y_range"]
                z_rmin, z_rmax = region["z_range"]
                
                # Find vertices in this region
                region_vertex_indices = []
                
                for i, vertex in enumerate(vertices):
                    x, y, z = vertex
                    if (x_rmin <= x <= x_rmax and 
                        y_rmin <= y <= y_rmax and 
                        z_rmin <= z <= z_rmax):
                        region_vertex_indices.append(i)
                
                if len(region_vertex_indices) == 0:
                    print(f"   ⚠️  No vertices found in {region_name} region")
                    continue
                
                print(f"   🔍 Analyzing {region_name} region: {len(region_vertex_indices)} vertices")
                
                # Use the new region-based analysis method
                try:
                    region_points, region_scores, region_indices, region_msg = self.gnn_analyzer.analyze_vertices_region(
                        vertices, region_vertex_indices, faces, top_k=50  # Get top 50 from each region
                    )
                    
                    if region_points is not None and len(region_points) > 0:
                        print(f"   ✅ {region_name}: Found {len(region_points)} critical points")
                        all_region_points.extend(region_points)
                        all_region_indices.extend(region_indices)
                        all_region_scores.extend(region_scores)
                    else:
                        print(f"   ❌ {region_name}: No critical points found - {region_msg}")
                        
                except Exception as e:
                    print(f"   ❌ {region_name} analysis failed: {e}")
            
            if len(all_region_points) == 0:
                return None, None, None, "No critical points found in any region"
            
            # If we have too many points, select top ones by score
            if len(all_region_points) > target_points:
                # Sort by score and take top ones
                sorted_indices = np.argsort(all_region_scores)[::-1]
                final_points = [all_region_points[i] for i in sorted_indices[:target_points]]
                final_scores = [all_region_scores[i] for i in sorted_indices[:target_points]]
                final_indices = [all_region_indices[i] for i in sorted_indices[:target_points]]
            else:
                final_points = all_region_points
                final_scores = all_region_scores
                final_indices = all_region_indices
            
            print(f"📊 Region-based analysis: Found {len(final_points)} points across {len(regions)} regions")
            return final_points, final_scores, final_indices, "Success"
            
        except Exception as e:
            return None, None, None, f"Region-based analysis failed: {str(e)}"

    # ---------------- Load 3D Model ----------------
    def load_model(self):
        f, _ = QFileDialog.getOpenFileName(self, "Select 3D Model", "", "3D Models (*.obj *.ply *.stl)")
        if not f:
            return
        try:
            self.current_mesh_path = f  # Store for GNN analysis
            
            import trimesh
            mesh = trimesh.load(f)
            if not isinstance(mesh, trimesh.Trimesh):
                mesh = mesh.dump(concatenate=True)
            self.vertices = mesh.vertices
            self.faces = mesh.faces

            # DEBUG: Check mesh properties
            print(f"📊 Mesh Analysis:")
            print(f"   Total vertices: {len(self.vertices)}")
            print(f"   Total faces: {len(self.faces) if self.faces is not None else 0}")
            print(f"   Vertex range - X: {self.vertices[:, 0].min():.3f} to {self.vertices[:, 0].max():.3f}")
            print(f"   Vertex range - Y: {self.vertices[:, 1].min():.3f} to {self.vertices[:, 1].max():.3f}")
            print(f"   Vertex range - Z: {self.vertices[:, 2].min():.3f} to {self.vertices[:, 2].max():.3f}")

            points = vtk.vtkPoints()
            for v in self.vertices:
                points.InsertNextPoint(v.tolist())

            poly = vtk.vtkPolyData()
            poly.SetPoints(points)

            # if faces exist add them; otherwise keep points-only poly to visualize as vertices/points
            if self.faces is not None and len(self.faces) > 0:
                triangles = vtk.vtkCellArray()
                for fidx in self.faces:
                    if len(fidx) >= 3:
                        tri = vtk.vtkTriangle()
                        tri.GetPointIds().SetId(0, int(fidx[0]))
                        tri.GetPointIds().SetId(1, int(fidx[1]))
                        tri.GetPointIds().SetId(2, int(fidx[2]))
                        triangles.InsertNextCell(tri)
                poly.SetPolys(triangles)

            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputData(poly)
            self.mesh_actor = vtk.vtkActor()
            self.mesh_actor.SetMapper(mapper)
            self.mesh_actor.GetProperty().SetColor(0.3, 0.8, 0.9)
            self.mesh_actor.GetProperty().SetOpacity(1.0)

            # 🔹 Enable edge overlay (like Blender)
            self.mesh_actor.GetProperty().EdgeVisibilityOn()
            self.mesh_actor.GetProperty().SetEdgeColor(0.1, 0.1, 0.1)  # dark gray
            self.mesh_actor.GetProperty().SetLineWidth(1)

            # Add mesh if not already added
            if self.mesh_actor not in self.renderer.GetActors():
                self.renderer.AddActor(self.mesh_actor)

            # Ensure camera frames to include mesh
            self.renderer.ResetCamera()
            self.vtk_widget.GetRenderWindow().Render()
            
            # Reset GNN points when new model is loaded
            self.gnn_top_points = None
            self.gnn_top_indices = None
            
            print(f"✅ Model loaded: {len(self.vertices)} vertices, {len(self.faces) if self.faces is not None else 0} faces")
            
        except Exception as e:
            print("Error loading 3D model:", e)

    # ---------------- GNN Analysis ----------------
    def analyze_stress_points(self):
        """Analyze mesh using GNN to find top 200 stress points"""
        if not hasattr(self, 'current_mesh_path') or not self.current_mesh_path:
            QMessageBox.warning(self, "Warning", "Please load a 3D model first.")
            return
        
        # LAZY LOADING: Load GNN model only when needed
        if self.gnn_analyzer is None:
            print("🔄 Loading GNN model...")
            self.gnn_analyzer = GNNAnalyzer(self.model_path)
        
        if self.gnn_analyzer.model is None:
            QMessageBox.warning(self, "Warning", "GNN model failed to load. Using random points.")
            self.add_stress_nodes_from_csv()  # Fallback to random
            return
        
        # Show processing message
        self.node_info_label.setText("🔄 Analyzing stress points with GNN...")
        self.node_info_label.setStyleSheet("color:#ffcc00; padding:6px;")
        
        # Process in a way that doesn't freeze UI
        QTimer.singleShot(100, self._perform_gnn_analysis)

    def _perform_gnn_analysis(self):
        """Perform GNN analysis using already loaded vertices"""
        try:
            # Check if we have vertices loaded
            if self.vertices is None:
                self.node_info_label.setText("❌ No vertices loaded from model")
                self.node_info_label.setStyleSheet("color:#ff4444; padding:6px;")
                self.add_stress_nodes_from_csv()
                return
            
            print(f"🔄 Running GNN analysis on {len(self.vertices)} vertices...")
            
            # FIRST: Try region-based analysis for full coverage
            print("🎯 Attempting region-based analysis for full mesh coverage...")
            top_points, top_scores, top_indices, message = self.force_full_mesh_coverage(
                self.vertices, self.faces, target_points=200
            )
            
            # SECOND: If region-based fails, try enhanced distribution
            if top_points is None:
                print("🔄 Region-based failed, trying enhanced distribution...")
                top_points, top_scores, top_indices, message = self.get_better_distributed_gnn_points(
                    self.vertices, self.faces, target_points=200
                )
            
            # THIRD: If enhanced distribution fails, try basic GNN
            if top_points is None:
                print("🔄 Enhanced distribution failed, trying basic GNN...")
                top_points, top_scores, top_indices, message = self.gnn_analyzer.analyze_vertices(
                    self.vertices, self.faces, top_k=200
                )
            
            if top_points is not None:
                # DEBUG: Check what points we're getting
                self.debug_node_placement(top_points, "Final GNN Analysis Result")
                
                # Store the GNN-selected points
                self.gnn_top_points = top_points
                self.gnn_top_indices = top_indices
                
                # Update visualization with GNN points
                self.visualize_gnn_points(top_points)
                
                self.node_info_label.setText(f"✅ GNN analysis complete: {len(top_points)} critical points found")
                self.node_info_label.setStyleSheet("color:#00ff99; padding:6px;")
                
                print(f"GNN Analysis: Found {len(top_points)} critical points")
                
                # Compare distributions
                self.compare_point_distributions()
                
            else:
                self.node_info_label.setText(f"❌ GNN analysis failed: {message}")
                self.node_info_label.setStyleSheet("color:#ff4444; padding:6px;")
                print(f"GNN analysis failed: {message}")
                # Fallback to basic GNN analysis
                self._fallback_gnn_analysis()
                
        except Exception as e:
            self.node_info_label.setText(f"❌ GNN analysis error: {str(e)}")
            self.node_info_label.setStyleSheet("color:#ff4444; padding:6px;")
            print(f"GNN analysis error: {e}")
            # Fallback to basic GNN analysis
            self._fallback_gnn_analysis()

    def _fallback_gnn_analysis(self):
        """Fallback to basic GNN analysis if enhanced method fails"""
        try:
            top_points, top_scores, top_indices, message = self.gnn_analyzer.analyze_vertices(
                self.vertices, self.faces, top_k=200
            )
            
            if top_points is not None:
                self.gnn_top_points = top_points
                self.gnn_top_indices = top_indices
                self.visualize_gnn_points(top_points)
                self.node_info_label.setText(f"✅ Basic GNN analysis: {len(top_points)} points found")
                print(f"Fallback GNN Analysis: Found {len(top_points)} critical points")
            else:
                self.add_stress_nodes_from_csv()
        except Exception as e:
            self.add_stress_nodes_from_csv()

    def visualize_gnn_points(self, points):
        """Visualize the GNN-selected points on the mesh"""
        # Clear existing nodes
        self.clear_previous_visualization()
        
        # Use GNN points
        node_positions = points
        
        # Your existing visualization code, but with GNN points
        mesh_bounds = self.mesh_actor.GetBounds() if self.mesh_actor else None
        mesh_scale = self.calculate_mesh_scale(mesh_bounds)
        
        # Create stress nodes at GNN-predicted locations
        self.create_stress_nodes(node_positions, list(range(len(node_positions))), mesh_scale)
        self.create_connectivity(node_positions, mesh_scale)
        
        self.renderer.ResetCamera()
        self.vtk_widget.GetRenderWindow().Render()

    def calculate_mesh_scale(self, mesh_bounds):
        """Calculate mesh scale for proper visualization"""
        if mesh_bounds is None:
            return 1.0
        return max(mesh_bounds[1]-mesh_bounds[0],
                   mesh_bounds[3]-mesh_bounds[2],
                   mesh_bounds[5]-mesh_bounds[4])

    # ---------------- Load CSV ----------------
    def load_csv(self):
        f, _ = QFileDialog.getOpenFileName(self, "Select CSV", "", "CSV Files (*.csv)")
        if not f:
            return
        try:
            self.csv_data = pd.read_csv(f)
            if self.csv_data.empty:
                return
            self.csv_index = 0
            self.timer.start(500)
            
            # Use GNN points if available, otherwise use random
            if self.gnn_top_points is not None:
                self.visualize_gnn_points(self.gnn_top_points)
            else:
                self.add_stress_nodes_from_csv()
                
        except Exception as e:
            print("Error loading CSV:", e)

    # ---------------- Add Heatmap Stress Nodes + Connectivity ----------------
    def add_stress_nodes_from_csv(self):
        if self.mesh_actor is None or self.vertices is None:
            # mesh must be loaded first to place nodes on model
            return

        # Clear previous nodes/labels/lines from renderer
        self.clear_previous_visualization()

        num_nodes = min(200, len(self.vertices))
        mesh_bounds = self.mesh_actor.GetBounds()
        mesh_scale = self.calculate_mesh_scale(mesh_bounds)
        radius = mesh_scale * 0.005

        # Use GNN points if available, otherwise use random
        if self.gnn_top_points is not None:
            node_positions = self.gnn_top_points
            num_nodes = len(node_positions)
            print(f"Using GNN points: {num_nodes} points")
        else:
            chosen_indices = np.random.choice(len(self.vertices), num_nodes, replace=False)
            node_positions = [self.vertices[idx] for idx in chosen_indices]
            print(f"Using random points: {num_nodes} points")

        # DEBUG: Check the distribution of points we're about to visualize
        if self.gnn_top_points is not None:
            self.debug_node_placement(node_positions, "Visualizing GNN Points")
        else:
            self.debug_node_placement(node_positions, "Visualizing Random Points")

        heatmap_colors = [
            (1.0, 1.0, 0.0),
            (1.0, 0.65, 0.0),
            (1.0, 0.0, 0.0)
        ]

        # Create nodes
        for idx, pos in enumerate(node_positions):
            sphere = vtk.vtkSphereSource()
            sphere.SetCenter(float(pos[0]), float(pos[1]), float(pos[2]))
            sphere.SetRadius(radius)
            sphere.SetThetaResolution(8)
            sphere.SetPhiResolution(8)
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
            self.node_adjacency[idx] = []
            self.node_id_map[actor] = idx

            # NEW: Assign region to node and select representative
            region = self.region_manager.get_region_for_point(pos, mesh_bounds)
            self.node_regions[idx] = region
            
            # Select first node in each region as representative
            if region not in self.region_representatives:
                self.region_representatives[region] = idx

            # --- Node Number Label (vtkFollower so it faces camera) ---
            try:
                text = vtkVectorText()
                text.SetText(str(idx + 1))
                text_mapper = vtk.vtkPolyDataMapper()
                text_mapper.SetInputConnection(text.GetOutputPort())
                text_actor = vtkFollower()
                text_actor.SetMapper(text_mapper)
                # scale label relative to node radius
                text_scale = radius * 0.8
                text_actor.SetScale(text_scale, text_scale, text_scale)
                # offset label slightly above the node to avoid z-fighting
                label_offset = np.array(pos) + np.array([0.0, 0.0, radius * 1.5])
                text_actor.SetPosition(float(label_offset[0]), float(label_offset[1]), float(label_offset[2]))
                text_actor.GetProperty().SetColor(1.0, 1.0, 1.0)
                # ensure follower uses renderer camera
                text_actor.SetCamera(self.renderer.GetActiveCamera())
                self.renderer.AddActor(text_actor)
                self.node_labels.append(text_actor)
            except Exception:
                # if any issue with text, continue without label
                pass

        # Connect very near nodes (visual + logical)
        adjacency_radius = mesh_scale * 0.03
        if adjacency_radius <= 0:
            adjacency_radius = 0.1  # fallback

        tree = cKDTree(node_positions)
        for i, pos in enumerate(node_positions):
            neighbors = tree.query_ball_point(pos, adjacency_radius)
            for j in neighbors:
                if i >= j:
                    continue
                # Logical connection
                self.node_adjacency[i].append(j)
                self.node_adjacency[j].append(i)

                # Visual connection
                line = vtk.vtkLineSource()
                line.SetPoint1(float(pos[0]), float(pos[1]), float(pos[2]))
                line.SetPoint2(float(node_positions[j][0]), float(node_positions[j][1]), float(node_positions[j][2]))
                line.Update()

                line_mapper = vtk.vtkPolyDataMapper()
                line_mapper.SetInputConnection(line.GetOutputPort())
                line_actor = vtk.vtkActor()
                line_actor.SetMapper(line_mapper)
                line_actor.GetProperty().SetColor(0.5, 0.5, 1.0)
                line_actor.GetProperty().SetLineWidth(2)
                # make lines slightly transparent so nodes + mesh remain readable
                line_actor.GetProperty().SetOpacity(0.9)

                self.renderer.AddActor(line_actor)
                self.line_actors.append(line_actor)

        # keep mesh + nodes visible and frame camera
        self.renderer.ResetCamera()
        self.vtk_widget.GetRenderWindow().Render()

    def clear_previous_visualization(self):
        """Clear previous nodes, labels, and lines from renderer"""
        try:
            for a in self.stress_nodes:
                try:
                    self.renderer.RemoveActor(a)
                except Exception:
                    pass
            for lab in self.node_labels:
                try:
                    self.renderer.RemoveActor(lab)
                except Exception:
                    pass
            for la in self.line_actors:
                try:
                    self.renderer.RemoveActor(la)
                except Exception:
                    pass
        except Exception:
            pass

        self.stress_nodes = []
        self.node_labels = []
        self.line_actors = []
        self.node_adjacency = {}
        self.node_id_map = {}
        self.node_regions = {}  # Clear previous regions
        self.region_representatives = {}  # Clear previous representatives

    def create_stress_nodes(self, node_positions, indices, mesh_scale):
        """Create stress nodes at specified positions"""
        radius = mesh_scale * 0.005
        mesh_bounds = self.mesh_actor.GetBounds() if self.mesh_actor else None
        
        heatmap_colors = [
            (1.0, 1.0, 0.0),
            (1.0, 0.65, 0.0),
            (1.0, 0.0, 0.0)
        ]

        for idx, pos in enumerate(node_positions):
            sphere = vtk.vtkSphereSource()
            sphere.SetCenter(float(pos[0]), float(pos[1]), float(pos[2]))
            sphere.SetRadius(radius)
            sphere.SetThetaResolution(8)
            sphere.SetPhiResolution(8)
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
            self.node_adjacency[idx] = []
            self.node_id_map[actor] = idx

            # Assign region to node and select representative
            region = self.region_manager.get_region_for_point(pos, mesh_bounds)
            self.node_regions[idx] = region
            
            if region not in self.region_representatives:
                self.region_representatives[region] = idx

            # Node Number Label
            try:
                text = vtkVectorText()
                text.SetText(str(idx + 1))
                text_mapper = vtk.vtkPolyDataMapper()
                text_mapper.SetInputConnection(text.GetOutputPort())
                text_actor = vtkFollower()
                text_actor.SetMapper(text_mapper)
                text_scale = radius * 0.8
                text_actor.SetScale(text_scale, text_scale, text_scale)
                label_offset = np.array(pos) + np.array([0.0, 0.0, radius * 1.5])
                text_actor.SetPosition(float(label_offset[0]), float(label_offset[1]), float(label_offset[2]))
                text_actor.GetProperty().SetColor(1.0, 1.0, 1.0)
                text_actor.SetCamera(self.renderer.GetActiveCamera())
                self.renderer.AddActor(text_actor)
                self.node_labels.append(text_actor)
            except Exception:
                pass

    def create_connectivity(self, node_positions, mesh_scale):
        """Create connectivity between nearby nodes"""
        adjacency_radius = mesh_scale * 0.03
        if adjacency_radius <= 0:
            adjacency_radius = 0.1

        tree = cKDTree(node_positions)
        for i, pos in enumerate(node_positions):
            neighbors = tree.query_ball_point(pos, adjacency_radius)
            for j in neighbors:
                if i >= j:
                    continue
                self.node_adjacency[i].append(j)
                self.node_adjacency[j].append(i)

                line = vtk.vtkLineSource()
                line.SetPoint1(float(pos[0]), float(pos[1]), float(pos[2]))
                line.SetPoint2(float(node_positions[j][0]), float(node_positions[j][1]), float(node_positions[j][2]))
                line.Update()

                line_mapper = vtk.vtkPolyDataMapper()
                line_mapper.SetInputConnection(line.GetOutputPort())
                line_actor = vtk.vtkActor()
                line_actor.SetMapper(line_mapper)
                line_actor.GetProperty().SetColor(0.5, 0.5, 1.0)
                line_actor.GetProperty().SetLineWidth(2)
                line_actor.GetProperty().SetOpacity(0.9)

                self.renderer.AddActor(line_actor)
                self.line_actors.append(line_actor)

    # ---------------- Right-Click Picker ----------------
    def on_right_click(self, obj, event):
        click_pos = self.interactor.GetEventPosition()
        # pick using prop picker
        self.picker.Pick(click_pos[0], click_pos[1], 0, self.renderer)
        actor = self.picker.GetActor()
        if actor in self.stress_nodes:
            node_id = self.node_id_map.get(actor, None)
            if self.info_panel is None or not self.info_panel.isVisible():
                self.info_panel = NodeInfoPanel(self, self.risk_meter, self.sensors, num_nodes=len(self.stress_nodes), node_id=node_id)
                self.info_panel.show()
            else:
                # if different node, reopen with new id
                if getattr(self.info_panel, "node_id", None) != node_id:
                    try:
                        self.info_panel.close()
                    except Exception:
                        pass
                    self.info_panel = NodeInfoPanel(self, self.risk_meter, self.sensors, num_nodes=len(self.stress_nodes), node_id=node_id)
                    self.info_panel.show()
                else:
                    self.info_panel.raise_()
                    self.info_panel.activateWindow()

    # ---------------- Update Sensors ----------------
    def update_sensors(self):
        if self.csv_data is None or self.csv_data.empty:
            return

        row = self.csv_data.iloc[self.csv_index % len(self.csv_data)]
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

            # NEW: Save ONLY ONE representative node per region to Firebase
            # This runs on EVERY sensor update and saves data permanently to Firebase
            for region, rep_node_id in self.region_representatives.items():
                # Count nodes in this region
                region_nodes = [node_id for node_id, node_region in self.node_regions.items() if node_region == region]
                node_count = len(region_nodes)
                
                # Calculate region risk (simple variation from overall risk)
                region_risk = max(0, min(100, avg_norm + (hash(region) % 20 - 10)))
                
                # Save only the representative node data for this region
                # This will overwrite previous data for this region in Firebase
                self.firebase_manager.save_region_data(region, region_risk, node_count, rep_node_id)

        if self.info_panel is not None and self.info_panel.isVisible():
            try:
                self.info_panel.refresh()
            except Exception:
                pass

        self.csv_index += 1