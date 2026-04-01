# ui/loading_overlay.py
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QProgressBar
from PyQt6.QtCore import Qt

class LoadingOverlay(QWidget):
    """
    Semi-transparent full-parent overlay with centered progress bar.
    """

    def __init__(self, parent=None, text="Loading..."):
        super().__init__(parent)

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(parent.rect() if parent else self.rect())

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(15)

        # Text label
        self.label = QLabel(text, self)
        self.label.setStyleSheet("color: #00f9ff; font-size: 16px; font-weight: bold;")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        # Progress bar
        self.progress = QProgressBar(self)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress.setFixedWidth(300)  # <- limit width
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #1a2a3a;
                border-radius: 10px;
                background-color: #2a3a4a;
                text-align: center;
                color: #00f9ff;
            }
            QProgressBar::chunk {
                background-color: #00f9ff;
                border-radius: 10px;
            }
        """)
        layout.addWidget(self.progress)

        # Semi-transparent background
        self.setStyleSheet("""
            background-color: rgba(20, 30, 48, 180);
            border-radius: 10px;
        """)

    def setText(self, text: str):
        self.label.setText(text)

    def setProgress(self, val: float):
        """Set progress 0-100"""
        self.progress.setValue(int(val))
