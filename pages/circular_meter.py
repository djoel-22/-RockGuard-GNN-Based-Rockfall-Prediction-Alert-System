# circular_meter.py
# Advanced compact circular risk meter widget for PyQt6

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRectF, QSize
from PyQt6.QtGui import QPainter, QPen, QFont, QColor


class CircularMeter(QWidget):
    """
    A compact circular risk meter widget.
    Displays a percentage (0–100%) with a colored arc.
    Colors:
        - Green for low (<40%)
        - Orange for medium (40–70%)
        - Red for high (>70%)
    """

    def __init__(self, parent=None, diameter: int = 100):
        super().__init__(parent)
        self._value = 0.0  # 0.0 to 1.0 normalized
        self._diameter = diameter
        self.setFixedSize(diameter, diameter)

    def sizeHint(self) -> QSize:
        return QSize(self._diameter, self._diameter)

    def setValue(self, value: float):
        """
        Set the risk value (normalized between 0.0 and 1.0).
        Automatically repaints the widget.
        """
        self._value = max(0.0, min(1.0, float(value)))
        self.update()

    def paintEvent(self, event):
        d = self._diameter
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # ---------- Background Arc ----------
        pen_bg = QPen(QColor(200, 200, 200), int(d * 0.10))
        painter.setPen(pen_bg)
        painter.drawArc(QRectF(5, 5, d - 10, d - 10), 0, 360 * 16)

        # ---------- Foreground Arc ----------
        pen_fg = QPen(self._get_color(), int(d * 0.10))
        painter.setPen(pen_fg)

        span_angle_degrees = int(self._value * 360)
        start_angle = -90 * 16  # start at top
        span = -span_angle_degrees * 16  # clockwise
        painter.drawArc(QRectF(5, 5, d - 10, d - 10), start_angle, span)

        # ---------- Percentage Text ----------
        painter.setPen(QColor(255, 255, 255))   # white
        font = QFont()
        font.setPointSize(int(d * 0.22))
        font.setBold(True)
        painter.setFont(font)

        pct_text = f"{int(round(self._value * 100))}%"
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, pct_text)

    # helper: risk color
    def _get_color(self) -> QColor:
        if self._value >= 0.7:
            return QColor(220, 50, 47)   # red
        elif self._value >= 0.4:
            return QColor(203, 152, 0)   # orange
        else:
            return QColor(38, 139, 34)   # green
