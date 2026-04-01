from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGridLayout
from PyQt6.QtGui import QFont


class DashboardPage(QWidget):
    def __init__(self, sensors, risk_meter):
        super().__init__()
        layout = QVBoxLayout(self)

        title = QLabel("🤖Insights")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #00f9ff;")
        layout.addWidget(title)

        grid = QGridLayout()
        row, col = 0, 0

        for sensor, (gauge, _) in sensors.items():
            grid.addWidget(gauge, row, col)
            col += 1
            if col > 2:
                col = 0
                row += 1

        layout.addLayout(grid)
        layout.addWidget(risk_meter)
