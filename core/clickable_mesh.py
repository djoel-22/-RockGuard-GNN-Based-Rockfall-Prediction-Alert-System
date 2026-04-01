from PyQt6.QtCore import pyqtSignal, Qt
import pyqtgraph.opengl as gl


class ClickableMeshItem(gl.GLMeshItem):
    clicked = pyqtSignal(object, object)

    def __init__(self, index, **kwargs):
        super().__init__(**kwargs)
        self.index = index
        self.setGLOptions('additive')

    def mouseClickEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.clicked.emit(self, event)
            event.accept()
        else:
            event.ignore()
