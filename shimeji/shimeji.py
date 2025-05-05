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

        # Estado inicial
        self.behaviors = {}  # Diccionario: comportamiento → lista de frames
        self.load_behaviors()
        self.current_behavior = "idle"
        self.current_frame = 0
        self.label = QLabel(self)
        self.label.setPixmap(self.behaviors[self.current_behavior][0])
        self.resize(self.label.pixmap().size())

        # Animación con timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(100)

        # Movimiento manual
        self.old_pos = QPoint()

    def load_behaviors(self):
        sprite_dir = "sprites"
        for behavior_name in os.listdir(sprite_dir):
            behavior_path = os.path.join(sprite_dir, behavior_name)
            if os.path.isdir(behavior_path):
                frames = []
                for file in sorted(os.listdir(behavior_path)):
                    if file.endswith(".png"):
                        print(file)
                        frame_path = os.path.join(behavior_path, file)
                        frames.append(QPixmap(frame_path))
                if frames:
                    self.behaviors[behavior_name] = frames

    def set_behavior(self, behavior_name):
        if behavior_name in self.behaviors:
            self.current_behavior = behavior_name
            self.current_frame = 0
            self.label.setPixmap(self.behaviors[behavior_name][0])
            self.resize(self.label.pixmap().size())

    def update_frame(self):
        frames = self.behaviors[self.current_behavior]
        self.current_frame = (self.current_frame + 1) % len(frames)
        self.label.setPixmap(frames[self.current_frame])

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()
            self.set_behavior("walk")  # Cambia a "walk" al tocarlo

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.set_behavior("idle")  # Vuelve a "idle" al soltar

if __name__ == "__main__":
    app = QApplication(sys.argv)
    shimeji = Shimeji()
    shimeji.show()
    sys.exit(app.exec())
