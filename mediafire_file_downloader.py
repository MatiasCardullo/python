import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, QTimer
from bs4 import BeautifulSoup

file_links = [
    "https://www.mediafire.com/file/y5mtusq0ueih47p/NK_89-98.PDF/file",
    "https://www.mediafire.com/file/gdpjzn8nvdlebfx/NK_99-108.PDF/file"
]

class MediafireDownloader(QWebEngineView):
    def __init__(self, urls):
        super().__init__()
        self.urls = urls
        self.current_index = 0
        self.results = []
        self.setWindowTitle("Mediafire Downloader")
        self.loadFinished.connect(self.on_load_finished)
        self.load(QUrl(self.urls[self.current_index]))
        self.show()

    def on_load_finished(self):
        print(f"[{self.current_index+1}/{len(self.urls)}] Página cargada, esperando...")
        QTimer.singleShot(3000, self.extract_link)

    def extract_link(self):
        self.page().toHtml(self.handle_html)

    def handle_html(self, html):
        soup = BeautifulSoup(html, "html.parser")
        button = soup.find("a", {"id": "downloadButton"})
        if button and button.has_attr("href"):
            direct_link = button["href"]
            print(f"✅ Enlace directo: {direct_link}")
            self.results.append(direct_link)
        else:
            print("❌ No se encontró el enlace de descarga.")
            self.results.append(None)

        self.current_index += 1
        if self.current_index < len(self.urls):
            self.load(QUrl(self.urls[self.current_index]))
        else:
            print("\n🎯 Todos los enlaces directos:")
            for i, link in enumerate(self.results):
                print(f"{i+1}. {link if link else '[ERROR]'}")
            self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = MediafireDownloader(file_links)
    sys.exit(app.exec_())
