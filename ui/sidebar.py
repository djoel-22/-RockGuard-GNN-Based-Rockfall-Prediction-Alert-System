from PyQt6.QtWidgets import QWidget, QPushButton, QVBoxLayout
from PyQt6.QtCore import Qt


class CollapsibleSidebar(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(220)
        self.setStyleSheet("""
            QWidget {
                background-color: #141e30;
                border-right: 2px solid #1f2f47;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                color: #00f9ff;
                font-size: 14px;
                padding: 12px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: rgba(0, 249, 255, 0.1);
            }
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Sidebar buttons
        self.btn_home = QPushButton("🏠  Home")
        self.btn_dashboard = QPushButton("📊  Dashboard")
        self.btn_stress = QPushButton("📡  Stress Analysis")
        self.btn_simulation = QPushButton("🛰️  Simulation")
        self.btn_employee = QPushButton("👷  Employee Management")  # ✅ Added button

        # Add all buttons
        layout.addWidget(self.btn_home)
        layout.addWidget(self.btn_dashboard)
        layout.addWidget(self.btn_stress)
        layout.addWidget(self.btn_simulation)
        layout.addWidget(self.btn_employee)
        layout.addStretch(1)
