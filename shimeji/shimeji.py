import sys
import os
from PyQt6.QtCore import Qt, QPoint, QTimer, QCoreApplication
from PyQt6.QtGui import QPixmap, QGuiApplication
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
        self.behaviors = {}
        self.load_behaviors()
        self.current_behavior = "walk"
        self.current_frame = 0

        # Movimiento automático
        self.walking = True
        self.direction = -1  # 1 = derecha, -1 = izquierda
        self.speed = 3

        # Imagen
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
            self.walking = (behavior_name == "walk")

    def update_frame(self):
        frames = self.behaviors[self.current_behavior]
        self.current_frame = (self.current_frame + 1) % len(frames)
        self.label.setPixmap(frames[self.current_frame])

        if self.walking:
            self.auto_move()

    def auto_move(self):
        screen = QGuiApplication.primaryScreen().availableGeometry()
        x = self.x() + self.direction * self.speed

        # Detectar bordes
        if x <= 0:
            x = 0
            self.direction = 1
        elif x + self.width() >= screen.width():
            x = screen.width() - self.width()
            self.direction = -1

        self.move(x, self.y())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()
            self.set_behavior("idle")

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.set_behavior("walk")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    shimeji = Shimeji()
    shimeji.show()
    sys.exit(app.exec())
