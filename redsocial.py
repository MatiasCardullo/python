from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QListWidget, QListWidgetItem, QScrollArea, QTextEdit
)
import sys

class PostWidget(QWidget):
    def __init__(self, user, text):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"<b>{user}</b>"))
        layout.addWidget(QLabel(text))
        self.setLayout(layout)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mini Red Social")
        self.resize(1000, 600)

        main_layout = QHBoxLayout(self)

        menu_izquierdo = QVBoxLayout()
        menu_izquierdo.addWidget(QLabel("🏠 Inicio"))
        menu_izquierdo.addWidget(QLabel("👤 Perfil"))
        menu_izquierdo.addWidget(QLabel("⚙ Config"))
        left_widget = QWidget()
        left_widget.setLayout(menu_izquierdo)

        feed_layout = QVBoxLayout()
        for i in range(20):
            post = PostWidget(f"Usuario {i}", "Este es un post de ejemplo.")
            feed_layout.addWidget(post)

        feed_widget = QWidget()
        feed_widget.setLayout(feed_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidget(feed_widget)
        scroll_area.setWidgetResizable(True)

        info_derecha = QVBoxLayout()
        info_derecha.addWidget(QLabel("🔔 Notificaciones"))
        info_derecha.addWidget(QLabel("💬 Mensajes"))
        right_widget = QWidget()
        right_widget.setLayout(info_derecha)

        main_layout.addWidget(left_widget, 2)
        main_layout.addWidget(scroll_area, 5)
        main_layout.addWidget(right_widget, 2)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
