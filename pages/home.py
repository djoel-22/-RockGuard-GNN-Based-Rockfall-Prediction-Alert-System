# =====================================================================================================
# home.py - Advanced Futuristic Home Page (interactive, glowing, clickable cards)
# =====================================================================================================

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGridLayout, QFrame, QHBoxLayout
)
from PyQt6.QtGui import QFont, QCursor
from PyQt6.QtCore import Qt, pyqtSignal


class FeatureCard(QFrame):
    clicked = pyqtSignal(str)  # emits the title when clicked

    def __init__(self, icon: str, title: str, desc: str, page_key: str):
        super().__init__()
        self.page_key = page_key
        self.setObjectName("featureCard")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.setStyleSheet("""
            QFrame#featureCard {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(0, 30, 40, 0.85),
                    stop:1 rgba(0, 60, 80, 0.85)
                );
                border-radius: 16px;
                border: 1px solid rgba(0, 249, 255, 0.25);
                transition: all 0.3s ease-in-out;
            }
            QFrame#featureCard:hover {
                border: 1px solid #00f9ff;
                background: rgba(0, 50, 70, 0.95);
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # Icon + Title
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 28px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        title_label = QLabel(title)
        title_label.setFont(QFont("Orbitron", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #00f9ff;")

        title_row = QHBoxLayout()
        title_row.addWidget(icon_label)
        title_row.addWidget(title_label)
        title_row.addStretch(1)

        layout.addLayout(title_row)

        # Description
        desc_label = QLabel(desc)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #cfd8dc; font-size: 12px;")
        layout.addWidget(desc_label)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.page_key)


class HomePage(QWidget):
    navigate = pyqtSignal(str)  # signal to navigate to another page

    def __init__(self):
        super().__init__()

        # Global Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 40, 50, 40)
        layout.setSpacing(25)

        # ================= Title Section =================
        title = QLabel("⚡ Futuristic Rockfall Detection System")
        title.setFont(QFont("Orbitron", 26, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            color: #00f9ff;
            letter-spacing: 1px;
        """)

        subtitle = QLabel("AI-powered monitoring • Real-time risk analysis • Immersive 3D simulation")
        subtitle.setFont(QFont("Arial", 14, QFont.Weight.Normal))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #aaa; font-style: italic;")

        layout.addWidget(title)
        layout.addWidget(subtitle)

        # ================= Description Section =================
        desc = QLabel(
            "Our cutting-edge system integrates geological sensors, real-time analytics, and AI-driven "
            "predictive modeling to deliver early warnings of rockfall hazards.\n\n"
            "Navigate through the modules to explore live monitoring, stress analysis, immersive "
            "simulations, and intelligent risk insights."
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("""
            color: #cfd8dc;
            font-size: 13px;
            line-height: 1.6em;
        """)
        layout.addWidget(desc)

        # ================= Features Section =================
        grid = QGridLayout()
        grid.setSpacing(25)

        features = [
            ("📊", "Real-Time Monitoring",
             "Track live geological sensor data with beautiful interactive gauges.", "dashboard"),
            ("⚡", "Stress Analysis",
             "Instantly analyze geological stress and identify weak zones.", "stress"),
            ("🛰️", "Simulation",
             "Run advanced predictive 3D rockfall simulations in real time.", "simulation"),
            ("🤖", "Insights",
             "Access AI-powered insights, anomaly detection, and risk forecasting.", "insights"),
        ]

        row, col = 0, 0
        for icon, title_text, desc_text, key in features:
            card = FeatureCard(icon, title_text, desc_text, key)
            card.clicked.connect(self.navigate.emit)
            grid.addWidget(card, row, col)
            col += 1
            if col > 1:
                col = 0
                row += 1

        layout.addLayout(grid)

        layout.addStretch(1)

        # ================= Footer =================
        footer = QLabel("© 2025 Rockfall AI System • Designed with ❤️ for Futuristic Safety")
        footer.setFont(QFont("Arial", 10))
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("color: #666; margin-top: 20px;")
        layout.addWidget(footer)
