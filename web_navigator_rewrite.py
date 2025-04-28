import sys
import urllib.parse
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLineEdit, QPushButton, QToolBar, QAction, QWidget, QVBoxLayout
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl

class SimpleBrowser(QMainWindow):
    def __init__(self, search_query, automation_mode=False):
        super().__init__()
        self.setWindowTitle("Simple Web Browser")
        self.setGeometry(100, 100, 1200, 800)
        self.automation_mode = automation_mode

        self.browser = QWebEngineView()

        # Crear toolbar
        self.toolbar = QToolBar()
        self.addToolBar(self.toolbar)

        # Botón atrás
        self.back_button = QAction('Back', self)
        self.back_button.triggered.connect(self.browser.back)
        self.toolbar.addAction(self.back_button)

        # Botón adelante
        self.forward_button = QAction('Forward', self)
        self.forward_button.triggered.connect(self.browser.forward)
        self.toolbar.addAction(self.forward_button)

        # Campo de búsqueda
        self.search_bar = QLineEdit()
        self.search_bar.returnPressed.connect(self.perform_search)
        self.toolbar.addWidget(self.search_bar)

        # Configurar estado según modo
        if self.automation_mode:
            self.back_button.setEnabled(False)
            self.forward_button.setEnabled(False)
            self.search_bar.setEnabled(False)

        # Layout principal
        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.browser)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Realizar búsqueda inicial
        self.search_in_google(search_query)

    def search_in_google(self, query):
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.google.com/search?q={encoded_query}"
        self.browser.load(QUrl(url))

    def perform_search(self):
        query = self.search_bar.text()
        self.search_in_google(query)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python browser.py <search_query> [--auto]")
        sys.exit(1)

    # Detectar modo automatizado
    automation_mode = "--auto" in sys.argv
    if automation_mode:
        sys.argv.remove("--auto")

    search_query = " ".join(sys.argv[1:])

    app = QApplication(sys.argv)
    window = SimpleBrowser(search_query, automation_mode=automation_mode)
    window.show()
    sys.exit(app.exec_())
