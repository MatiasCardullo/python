import sys
import threading
import requests
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QProgressBar, QMessageBox, QScrollArea
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, QTimer, pyqtSignal, QObject
from bs4 import BeautifulSoup
from urllib.parse import unquote, urlparse

# Helper para emitir señales desde hilos
class DownloadSignals(QObject):
    progress = pyqtSignal(int, int)  # index, percentage
    finished = pyqtSignal(int)       # index

class FileDownloader(threading.Thread):
    def __init__(self, url, index, signals):
        super().__init__()
        self.url = url
        self.index = index
        self.signals = signals

    def run(self):
        local_filename = unquote(urlparse(self.url).path.split('/')[-1])
        try:
            with requests.get(self.url, stream=True) as r:
                total_length = int(r.headers.get('content-length', 0))
                with open(local_filename, 'wb') as f:
                    downloaded = 0
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            percent = int((downloaded / total_length) * 100)
                            self.signals.progress.emit(self.index, percent)
            self.signals.finished.emit(self.index)
        except Exception as e:
            print(f"[{self.index}] ❌ Error: {e}")
            self.signals.finished.emit(self.index)

class MediafireDownloader(QWebEngineView):
    direct_links_ready = pyqtSignal(list)

    def __init__(self, urls):
        super().__init__()
        self.urls = urls
        self.current_index = 0
        self.results = []
        self.setWindowTitle("Mediafire Downloader")
        self.loadFinished.connect(self.on_load_finished)
        self.load(QUrl(self.urls[self.current_index]))

    def start(self):
        self.show()

    def on_load_finished(self):
        print(f"[{self.current_index+1}/{len(self.urls)}] Página cargada...")
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
            self.direct_links_ready.emit(self.results)
            self.close()

class DownloadWindow(QWidget):
    def __init__(self, urls):
        super().__init__()
        self.setWindowTitle("Descargas MediaFire")
        self.layout = QVBoxLayout(self)

        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.inner_widget = QWidget()
        self.inner_layout = QVBoxLayout(self.inner_widget)
        self.scroll.setWidget(self.inner_widget)
        self.layout.addWidget(self.scroll)

        self.progress_bars = []
        self.labels = []

        self.downloader = MediafireDownloader(urls)
        self.downloader.direct_links_ready.connect(self.start_downloads)
        self.downloader.start()

    def start_downloads(self, direct_links):
        for index, link in enumerate(direct_links):
            if not link:
                continue

            name = unquote(urlparse(link).path.split('/')[-1])
            label = QLabel(f"Descargando: {name}")
            bar = QProgressBar()
            bar.setValue(0)

            self.inner_layout.addWidget(label)
            self.inner_layout.addWidget(bar)

            self.labels.append(label)
            self.progress_bars.append(bar)

            signals = DownloadSignals()
            signals.progress.connect(self.update_progress)
            signals.finished.connect(self.mark_finished)

            thread = FileDownloader(link, index, signals)
            thread.start()

        self.show()

    def update_progress(self, index, percent):
        self.progress_bars[index].setValue(percent)

    def mark_finished(self, index):
        self.labels[index].setText(f"✅ Completado: {self.labels[index].text()[12:]}")
        if all(bar.value() == 100 for bar in self.progress_bars):
            self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DownloadWindow(sys.argv[1:])
    sys.exit(app.exec_())
