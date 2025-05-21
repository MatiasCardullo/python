import random
import subprocess
import sys
import os
import win32gui
import win32process
from PyQt6.QtCore import Qt, QPoint, QTimer, QRect
from PyQt6.QtGui import QPixmap, QPainter, QMouseEvent, QCursor, QTransform
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QMenu

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

        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.resize(128, 160)

        self.behaviors = {
            "idle": self.load_frames("idle"),
            "walk": self.load_frames("walk"),
            "sleep": self.load_frames("sleep"),
            "fall": self.load_frames("fall"),
            "grab": self.load_frames("grab")
        }

        self.behavior = "idle"
        self.direction = "right"
        self.current_frame = 0
        self.frame_timer = QTimer()
        self.frame_timer.timeout.connect(self.update_frame)
        self.frame_timer.start(100)

        self.move_timer = QTimer()
        self.move_timer.timeout.connect(self.move_character)
        self.move_timer.start(30)

        self.grabbed = False
        self.mouse_offset = None

        self.gravity = 1.2
        self.velocity_y = 0
        self.on_ground = True

        #self.set_behavior("idle")

    def get_platforms(self):
        def is_real_window(hwnd):
            # Verifica que la ventana sea visible y no sea del sistema
            if not win32gui.IsWindowVisible(hwnd):
                return False
            if win32gui.IsIconic(hwnd):  # Minimizada
                return False
            if win32gui.GetWindowText(hwnd) == "":
                return False
            return True

        def enum_handler(hwnd, result_list):
            if is_real_window(hwnd):
                rect = win32gui.GetWindowRect(hwnd)
                left, top, right, bottom = rect
                result_list.append({
                    "x": left,
                    "y_top": top,
                    "y_bottom": bottom,
                    "width": right - left
                })

        platforms = []
        win32gui.EnumWindows(enum_handler, platforms)
        return platforms

    def load_frames(self, behavior):
        path = os.path.join("sprites", behavior)
        if not os.path.exists(path):
            return []
        frames = []
        for file in sorted(os.listdir(path)):
            if file.endswith(".png"):
                frame = QPixmap(os.path.join(path, file))
                frame = frame.scaled(128, 160, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                frames.append(frame)
        return frames

    def set_behavior(self, behavior):
        if behavior != self.behavior and behavior in self.behaviors:
            self.behavior = behavior
            self.current_frame = 0

    def update_frame(self):
        frames = self.behaviors.get(self.behavior, [])
        if not frames:
            return

        frame = frames[self.current_frame]

        if self.direction == "right":
            transform = QTransform().scale(-1, 1)
            frame = frame.transformed(transform, Qt.TransformationMode.SmoothTransformation)

        self.label.setPixmap(frame)
        self.label.resize(frame.size())
        self.resize(frame.size())

        self.current_frame = (self.current_frame + 1) % len(frames)

    def move_character(self):
        if not self.grabbed:
            if self.behavior == "idle":
                chance = random.random()
                if chance < 0.01:
                    self.set_behavior("walk")
                    self.direction = random.choice(["left", "right"])
                elif chance < 0.001:
                    self.set_behavior("sleep")
            elif self.behavior == "walk":
                dx = 2 if self.direction == "right" else -2
                self.move(self.x() + dx, self.y())
                if random.random() < 0.001:
                    self.set_behavior("idle")
            elif self.behavior == "sleep":
                if random.random() < 0.001:
                    self.set_behavior("idle")
            if self.behavior != "sleep":
                self.apply_gravity()
        self.check_boundaries()

    def apply_gravity(self):
        platforms = self.get_platforms()
        screen_rect = QApplication.primaryScreen().geometry()
        bottom_limit = screen_rect.bottom()

        next_y = self.y() + int(self.velocity_y + self.gravity)
        standing = False

        for platform in platforms:
            within_x_bounds = self.x() + self.width() // 2 >= platform["x"] and \
                            self.x() + self.width() // 2 <= platform["x"] + platform["width"]
            near_top_edge = self.y() + self.height() <= platform["y_top"] + 5 and \
                            next_y + self.height() >= platform["y_top"]

            if within_x_bounds and near_top_edge:
                self.velocity_y = 0
                self.move(self.x(), platform["y_top"] - self.height())
                self.on_ground = True
                if self.behavior == "fall":
                    self.set_behavior("idle")
                standing = True
                break

        if not standing:
            if self.y() + self.height() < bottom_limit:
                self.on_ground = False
                self.velocity_y += self.gravity
                self.move(self.x(), next_y)
                if self.behavior != "fall":
                    self.set_behavior("fall")
            else:
                self.velocity_y = 0
                self.move(self.x(), bottom_limit - self.height())
                self.on_ground = True
                if self.behavior == "fall":
                    self.set_behavior("idle")

    def check_boundaries(self):
        screen_rect = QApplication.primaryScreen().geometry()
        new_x = self.x()

        if self.x() < screen_rect.left():
            new_x = screen_rect.left()
            self.direction = "right"
        elif self.x() + self.width() > screen_rect.right():
            new_x = screen_rect.right() - self.width()
            self.direction = "left"

        self.move(new_x, self.y())

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.mouse_offset = event.globalPosition().toPoint() - self.pos()
            self.grabbed = True
            self.velocity_y = 0  # cancelamos caída mientras está agarrado
            self.set_behavior("grab")

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.mouse_offset:
            self.move(event.globalPosition().toPoint() - self.mouse_offset)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.mouse_offset = None
        self.grabbed = False
    
    def contextMenuEvent(self, event):
        menu = QMenu(self)

        sleep_action = menu.addAction("Dormir")
        walk_action = menu.addAction("Caminar")
        idle_action = menu.addAction("Detenerse")
        dupe_action = menu.addAction("Mitosis")
        download_action = menu.addAction("Descargar...")
        close_action = menu.addAction("Cerrar")

        action = menu.exec(event.globalPos())
        if action == sleep_action:
            self.set_behavior("sleep")
        elif action == walk_action:
            self.set_behavior("walk")
        elif action == idle_action:
            self.set_behavior("idle")
        elif action == dupe_action:
            subprocess.Popen(["python", "shimeji.py"])
        elif action == download_action:
            subprocess.Popen(["python", "../downloader/download_manager.py"])
        elif action == close_action:
            QApplication.quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    shimeji = Shimeji()
    shimeji.show()
    sys.exit(app.exec())
