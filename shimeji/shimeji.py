import sys
import os
from PyQt6.QtCore import Qt, QPoint, QTimer
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication, QLabel, QWidget

class Shimeji(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)

        # Cargar frames de animación
        self.frames = []
        for i in range(12):
            frame_path = os.path.join("frames", f"frame ({i+1}).png")
            self.frames.append(QPixmap(frame_path))

        # Imagen inicial
        self.current_frame = 0
        self.label = QLabel(self)
        self.label.setPixmap(self.frames[self.current_frame])
        self.resize(self.frames[0].size())

        # Animación con timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(50)

        # Posición para arrastrar
        self.old_pos = QPoint()

    def update_frame(self):
        self.current_frame = (self.current_frame + 1) % len(self.frames)
        self.label.setPixmap(self.frames[self.current_frame])

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    shimeji = Shimeji()
    shimeji.show()
    sys.exit(app.exec())
