from PyQt6.QtWidgets import QProgressBar, QWidget
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QBrush
from PyQt6.QtCore import Qt, QRect


class FuturisticGauge(QProgressBar):
    def __init__(self, title, unit="", max_val=100):
        super().__init__()
        self.unit = unit
        self.title = title
        self.raw_value = 0
        self.setMaximum(max_val)
        self.setValue(0)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.setStyleSheet("""
            QProgressBar {
                border: 2px solid rgba(0,255,255,0.3);
                border-radius: 12px;
                background: rgba(20,20,40,0.8);
                color: #00f9ff;
                font-weight: bold;
                text-align: center;
                padding: 2px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00f9ff, stop:1 #0066ff
                );
                border-radius: 10px;
            }
        """)

    def update_value(self, raw, min_v, max_v):
        self.raw_value = raw
        norm = int(((raw - min_v) / (max_v - min_v)) * 100)
        norm = max(0, min(100, norm))
        self.setValue(norm)
        self.setFormat(f"{self.title}: {raw:.2f} {self.unit}")


class AnimatedRiskMeter(QWidget):
    def __init__(self, title="Rockfall Risk"):
        super().__init__()
        self.value = 0
        self.title = title
        self.setMinimumSize(180, 180)

    def setValue(self, val):
        self.value = max(0, min(100, val))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        size = min(rect.width(), rect.height()) - 20
        center = rect.center()

        # Background
        painter.setPen(QPen(QColor(50, 50, 80), 4))
        painter.setBrush(QBrush(QColor(10, 10, 30)))
        painter.drawEllipse(center, size // 2, size // 2)

        # Risk arc
        angle_span = int(360 * (self.value / 100))
        grad_color = QColor.fromHsv(int(120 - (self.value * 1.2)), 255, 255)
        painter.setPen(QPen(grad_color, 14))
        painter.drawArc(center.x()-size//2, center.y()-size//2, size, size, 90*16, -angle_span*16)

        # Text
        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        painter.setPen(QColor(200, 200, 255))
        text_rect = QRect(center.x() - size//2, center.y() - size//2, size, size)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, f"{self.title}\n{int(self.value)}%")

        # Glow
        painter.setPen(QPen(QColor(0, 249, 255, 100), 2))
        painter.drawEllipse(center, size//2 + 5, size//2 + 5)
