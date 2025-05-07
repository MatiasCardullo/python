import re
import os
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QProgressBar, QScrollArea,QPushButton,QDialog
from PyQt5.QtWebEngineWidgets import QWebEngineView,QWebEnginePage
from PyQt5.QtCore import QUrl, QTimer, pyqtSignal
from bs4 import BeautifulSoup
import file_downloader
from settings_dialog import SettingsDialog, load_config

#Mucho ruido en consola, shhhh
class SilentPage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        pass

#Navegador Web
class MediafireDownloader(QWebEngineView):
    direct_links_ready = pyqtSignal(list)

    def __init__(self, urls):
        super().__init__()
        self.setPage(SilentPage(self))
        self.urls = [(url, "") for url in urls]  # Url,path
        self.current_index = 0
        self.results = []
        self.setWindowTitle("Mediafire Downloader")
        self.loadFinished.connect(self.on_load_finished)
        self.load(QUrl(self.urls[self.current_index][0]))

    def start(self):
        self.show()

    def on_load_finished(self):
        print(f"[{self.current_index+1}/{len(self.urls)}] Páginas cargadas...")
        QTimer.singleShot(1000, self.route_url_handling)

    def route_url_handling(self):
        url, path = self.urls[self.current_index]
        if "/folder/" in url:
            self.page().toHtml(lambda html: self.handle_folder_html(html, path))
        elif "/file/" in url or "/download/" in url:
            self.page().toHtml(lambda html: self.handle_file_html(html, path))
        else:
            print("❌ URL no reconocida como archivo o carpeta.")
            self.results.append(None)
            self.proceed_to_next()

    def handle_folder_html(self, html, base_path):
        soup = BeautifulSoup(html, "html.parser")
        aux = []
        title_tag = soup.find(id="folder_name")
        folder_name = "Subcarpeta"  # Fallback
        if title_tag and title_tag.has_attr("title"):
            folder_name = title_tag["title"]

        subfolder_path = os.path.join(base_path, folder_name)
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if re.match(r"^https?://www\.mediafire\.com/file/", href):
                aux.append(href)
            elif re.match(r"^#\w+", href):
                folder_id = href.lstrip("#")
                span = a.find("span", class_="item-name")
                if span:
                    span_name = span.text.strip().replace(" ", "_")
                    full_url = f"https://www.mediafire.com/folder/{folder_id}/{span_name}"
                    aux.append(full_url)

        file_links = list(set(aux))
        if file_links:
            print(f"📁 {len(file_links)} archivos encontrados en carpeta '{folder_name}'.")
            insert_position = self.current_index + 1
            for link in reversed(file_links):
                self.urls.insert(insert_position, (link, subfolder_path))
        else:
            print("❌ No se encontraron archivos en la carpeta.")
        self.proceed_to_next()

    def handle_file_html(self, html, current_path):
        soup = BeautifulSoup(html, "html.parser")
        button = soup.find("a", {"id": "downloadButton"})
        filename_tag = soup.find("div", class_="filename")
        if button and button.has_attr("href"):
            direct_link = button["href"]
            filename = filename_tag.text.strip() if filename_tag else os.path.basename(direct_link)
            full_path = os.path.join(current_path, filename)
            print(f"✅ Enlace directo: {direct_link}")
            print(f"💾 Guardar como: {full_path}")
            self.results.append((full_path, direct_link))
        else:
            print("❌ No se encontró el enlace de descarga.")
            self.results.append((None,None))
        self.proceed_to_next()

    def proceed_to_next(self):
        self.current_index += 1
        if self.current_index < len(self.urls):
            self.load(QUrl(self.urls[self.current_index][0]))
        else:
            self.direct_links_ready.emit(self.results)
            self.close()

#Main - Ventana de descargas
class DownloadWindow(QWidget):
    def __init__(self, urls):
        super().__init__()
        self.setWindowTitle("Descargas MediaFire")
        self.layout = QVBoxLayout(self)

        self.config = load_config()
        self.max_parallel_downloads = self.config.get("max_parallel_downloads")
        self.open_on_finish = self.config.get("open_on_finish")

        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.inner_widget = QWidget()
        self.inner_layout = QVBoxLayout(self.inner_widget)
        self.scroll.setWidget(self.inner_widget)
        self.layout.addWidget(self.scroll)
        self.settings_button = QPushButton("⚙ Opciones")
        self.settings_button.clicked.connect(self.open_settings_dialog)
        self.layout.addWidget(self.settings_button)

        self.progress_bars = []
        self.labels = []
        self.downloader = MediafireDownloader(urls)
        self.downloader.direct_links_ready.connect(self.start_downloads)
        self.downloader.start()

    def open_settings_dialog(self):
        dialog = SettingsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            # Recargar config desde el archivo
            self.config = load_config()
            # Aplicar nueva configuración de descargas paralelas
            self.max_parallel_downloads=self.config.get("max_parallel_downloads")
            file_downloader.set_max_parallel_downloads(self.max_parallel_downloads)
            # Si tenés más settings, los podés aplicar aquí también
            self.open_on_finish = self.config.get("open_on_finish")
            print(f"✅ Configuración actualizada: {self.config}")

    def start_downloads(self, direct_links):
        self.completed_downloads = 0
        for index, (relative_path, link) in enumerate(direct_links):
            if not link:
                continue
            
            dir_path = os.path.dirname(relative_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)

            label = QLabel(f"Descargando: {relative_path}")
            bar = QProgressBar()
            bar.setValue(0)

            self.inner_layout.addWidget(label)
            self.inner_layout.addWidget(bar)

            self.labels.append(label)
            self.progress_bars.append(bar)

            signals = file_downloader.DownloadSignals()
            signals.progress.connect(self.update_progress)
            signals.finished.connect(self.mark_finished)

            thread = file_downloader.FileDownloader(link, relative_path, index, signals)
            thread.start()
        self.total_downloads = len(self.progress_bars)
        self.show()

    def update_progress(self, index, percent):
        self.progress_bars[index].setValue(percent)

    def mark_finished(self, index):
        done=f"✅ Completado: {self.labels[index].text()[12:]}"
        print(done)
        self.labels[index].setText(done)
        self.inner_layout.removeWidget(self.progress_bars[index])
        self.progress_bars[index].deleteLater()
        self.completed_downloads += 1
        if self.completed_downloads == self.total_downloads:
            QTimer.singleShot(10000, self.close)            

if __name__ == '__main__':
    os.system("title Descargas")
    app = QApplication(sys.argv)
    window = DownloadWindow(sys.argv[1:])
    sys.exit(app.exec_())
