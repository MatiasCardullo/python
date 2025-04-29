import sys
import urllib.parse
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLineEdit, QPushButton, QToolBar, QAction, QWidget, QVBoxLayout
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
from bs4 import BeautifulSoup

def detect_automation_mode(query):
    keywords = {
        "define ": "definition",
        "descargar ": "download",
        "download ": "download",
        "convertir ": "convert",
        "traducir ": "translate",
        "weather ": "weather",
        "clima ": "weather",
    }

    for word, mode in keywords.items():
        if word in query.lower():
            if word == "define ":
                cleaned_query = query.lower().replace(word, "", 1).strip()
            return mode, cleaned_query

    return None, query


class SimpleBrowser(QMainWindow):
    def __init__(self, search_query, automation_mode):
        super().__init__()
        self.setWindowTitle("Simple Web Browser")
        self.setGeometry(100, 100, 800, 600)
        self.automation_mode = automation_mode

        self.browser = QWebEngineView()
        self.browser.setZoomFactor(0.75)

        # Crear toolbar
        self.toolbar = QToolBar()
        self.addToolBar(self.toolbar)

        # Botón atrás
        self.back_button = QAction('<', self)
        self.back_button.triggered.connect(self.browser.back)
        self.toolbar.addAction(self.back_button)

        # Botón adelante
        self.forward_button = QAction('>', self)
        self.forward_button.triggered.connect(self.browser.forward)
        self.toolbar.addAction(self.forward_button)

        # Campo de búsqueda
        self.search_bar = QLineEdit()
        self.search_bar.returnPressed.connect(self.perform_search)
        self.toolbar.addWidget(self.search_bar)
        
        # Botón zoom in
        self.zoom_in_button = QAction('🔎+', self)
        self.zoom_in_button.triggered.connect(self.zoom_in)
        self.toolbar.addAction(self.zoom_in_button)

        # Botón zoom out
        self.zoom_out_button = QAction('🔎-', self)
        self.zoom_out_button.triggered.connect(self.zoom_out)
        self.toolbar.addAction(self.zoom_out_button)

        # Botón save
        self.save_button = QAction('💾', self)
        self.save_button.triggered.connect(self.save_html)
        self.toolbar.addAction(self.save_button)

        # Configurar estado
        self.save_button.setEnabled(False)
        if self.automation_mode is not None:
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
        self.browser.loadFinished.connect(self.on_load_finished)
        #self.browser.loadFinished.connect(self.find_specific_div)

    def zoom_in(self):
        current_zoom = self.browser.zoomFactor()
        self.browser.setZoomFactor(current_zoom + 0.1)

    def zoom_out(self):
        current_zoom = self.browser.zoomFactor()
        self.browser.setZoomFactor(current_zoom - 0.1)
        
    def process_html(self,html):
        soup = BeautifulSoup(html, "html.parser")
        div = soup.find("div", {"class": "dURPMd", "id": "rso"})
        if div:
            links = div.find_all("a", href=True)
            print("Enlaces con <h3> dentro:")
            count = 0
            for a in links:
                if a.find("h3"):
                    print(a['href'])
                    count += 1
            print(f"Total: {count} enlaces mostrados.")
        else:
            print("DIV no encontrado.")

    def on_load_finished(self,ok):
        if not ok:
            print("Error: La página no se cargó correctamente.")
            return
        self.browser.page().toHtml(self.process_html)

    def save_html(self):
        def callback(html):
            with open('page_saved.html', 'w', encoding='utf-8') as f:
                f.write(html)
            print("HTML saved to page_saved.html")
        self.browser.page().toHtml(callback)

    def search_in_google(self, query):
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.google.com/search?q={encoded_query}"
        self.browser.load(QUrl(url))

    def perform_search(self):
        query = self.search_bar.text()
        self.search_in_google(query)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    automation_mode, search_query = detect_automation_mode(" ".join(sys.argv[1:]))
    window = SimpleBrowser(search_query, automation_mode=automation_mode)
    window.show()
    sys.exit(app.exec_())
