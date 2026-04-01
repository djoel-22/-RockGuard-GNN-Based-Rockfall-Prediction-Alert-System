import sys
from PyQt6.QtWidgets import QApplication, QStyleFactory
from core.app_window import RockfallApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    window = RockfallApp()
    window.show()
    sys.exit(app.exec())
