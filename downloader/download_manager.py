import json
import time, re, os, sys, uuid, functools
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QProgressBar, QScrollArea, QPushButton, QDialog, QTextEdit
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtCore import QUrl, QTimer, pyqtSignal, QThreadPool
from bs4 import BeautifulSoup
from workers import DownloadSignals, FileDownloader
from settings_dialog import SettingsDialog, load_config, DEFAULT_CONFIG
from torrent import TorrentUpdater, add_magnet_link, add_torrent_file

from enum import Enum

class DownloadType(Enum):
    NORMAL = 0
    TORRENT = 1
    TEMPORAL = 2

#Mucho ruido en consola, shhhh
class SilentPage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        pass

#Navegador Web
class UniversalDownloader(QWebEngineView):
    direct_links_ready = pyqtSignal(list)

    def __init__(self, items):
        super().__init__()
        self.setPage(SilentPage(self))

        self.items = items  # Lista completa (cada item con 'url', 'password', etc.)
        self.targets = []   # Solo los que necesitan navegador
        self.current_index = 0

        # Expandir los items en sub-items individuales (uno por URL)
        for entry in self.items:
            urls = entry["url"] if isinstance(entry["url"], list) else [entry["url"]]
            pwd_raw = entry.get("password", "")
            passwords = pwd_raw if isinstance(pwd_raw, list) else [pwd_raw]
            for u, p in zip(urls, passwords):
                self.targets.append({
                    "original_entry": entry,
                    "url": u,
                    "password": p,
                    "base_path": entry.get("path") or "",  # puede cambiar después
                })

        if not self.targets:
            QTimer.singleShot(100, lambda: self.direct_links_ready.emit(self.items))
            return

        self.setWindowTitle("Universal Downloader")
        self.loadFinished.connect(self.on_load_finished)
        self.load(QUrl(self.targets[0]["url"]))

    def on_load_finished(self):
        current = self.targets[self.current_index]
        print(f"[{self.current_index + 1}/{len(self.targets)}] Cargando: {current['url']}")
        QTimer.singleShot(1000, self.route_url_handling)

    def route_url_handling(self):
        target = self.targets[self.current_index]
        url = target["url"]
        path = target["base_path"]

        if "mediafire.com" in url:
            self.handle_mediafire(url, path)
        #elif "4shared.com" in url:
        #    self.page().toHtml(lambda html: self.handle_4shared(html, path))
        #elif "drive.google.com" in url:
        #    self.handle_gdrive(url, path)
        else:
            print(f"❌ Sitio no soportado: {url}")
            self.register_result(None, None)
            self.proceed_to_next()

    def handle_mediafire(self, url, path):
        if "/folder/" in url:
            self.page().toHtml(lambda html: self.handle_mediafire_folder(html, path))
        elif "/file/" in url or "/download/" in url:
            self.page().toHtml(lambda html: self.handle_mediafire_file(html, path))
        else:
            print("❌ URL de MediaFire no reconocida.")
            self.register_result(None, None)
            self.proceed_to_next()

    def handle_mediafire_folder(self, html, base_path):
        soup = BeautifulSoup(html, "html.parser")
        aux = []
        folder_name = "Subcarpeta"
        title_tag = soup.find(id="folder_name")
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
            print(f"📁 {len(file_links)} archivos encontrados.")
            insert_position = self.current_index + 1
            for link in reversed(file_links):
                self.targets.insert(insert_position, {
                    "original_entry": self.targets[self.current_index]["original_entry"],
                    "url": link,
                    "password": self.targets[self.current_index]["password"],
                    "base_path": subfolder_path
                })
        else:
            print("❌ No se encontraron archivos en la carpeta.")
        self.proceed_to_next()

    def handle_mediafire_file(self, html, path):
        soup = BeautifulSoup(html, "html.parser")
        button = soup.find("a", {"id": "downloadButton"})
        filename_tag = soup.find("div", class_="filename")
        if button and button.has_attr("href"):
            direct_link = button["href"]
            filename = filename_tag.text.strip() if filename_tag else os.path.basename(direct_link)
            full_path = os.path.join(path, filename)
            self.register_result(full_path, direct_link)
        else:
            print("❌ No se encontró el enlace de descarga.")
            self.register_result(None, None)
        self.proceed_to_next()

    def register_result(self, path, direct_link):
        target = self.targets[self.current_index]
        entry = target["original_entry"]

        # Si fue exitoso, actualizamos
        if path and direct_link:
            entry["direct_link"] = direct_link
            entry["path"] = path
            entry["url"] = target["url"]
            entry["password"] = target["password"]
        else:
            # Eliminamos este mirror de la entrada
            urls = entry["url"] if isinstance(entry["url"], list) else [entry["url"]]
            pwds = entry["password"] if isinstance(entry["password"], list) else [entry["password"]]
            if target["url"] in urls:
                idx = urls.index(target["url"])
                urls.pop(idx)
                if idx < len(pwds):
                    pwds.pop(idx)
            entry["url"] = urls if len(urls) > 1 else (urls[0] if urls else "")
            entry["password"] = pwds if len(pwds) > 1 else (pwds[0] if pwds else "")

    def proceed_to_next(self):
        self.current_index += 1
        if self.current_index < len(self.targets):
            self.load(QUrl(self.targets[self.current_index]["url"]))
        else:
            # Devolver toda la lista original, con actualizaciones
            self.direct_links_ready.emit(self.items)
            self.close()

#Main - Ventana de descargas
class DownloadWindow(QWidget):
    def __init__(self, json_entries):
        super().__init__()
        self.setWindowTitle("Descargador Universal")
        self.setMinimumSize(400, 200)
        self.layout = QVBoxLayout(self)

        self.config = load_config()
        self.folder_path = self.config.get("folder_path",DEFAULT_CONFIG["folder_path"])
        self.open_on_finish = self.config.get("open_on_finish",DEFAULT_CONFIG["open_on_finish"])
        self.max_parallel_downloads = self.config.get("max_parallel_downloads",DEFAULT_CONFIG["max_parallel_downloads"])

        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.inner_widget = QWidget()
        self.inner_layout = QVBoxLayout(self.inner_widget)
        self.scroll.setWidget(self.inner_widget)
        self.layout.addWidget(self.scroll)
        self.settings_button = QPushButton("Configuración ⚙")
        self.settings_button.clicked.connect(self.open_settings_dialog)
        self.layout.addWidget(self.settings_button)

        self.torrent_hashes = {}
        self.torrent_timer = QTimer()
        self.torrent_timer.timeout.connect(self.start_torrent_update)
        self.torrent_timer.start(3000)

        self.progress_bars = []
        self.labels = []
        self.temp_progress_bars = []
        self.temp_labels = []
        self.torrent_progress_bars = []
        self.torrent_labels = []
        self.downloader = UniversalDownloader(json_entries)
        self.downloader.direct_links_ready.connect(self.start_downloads)

    def start_downloads(self, direct_links):
        for index, entry in enumerate(direct_links):
            link = entry.get("direct_link")
            path = entry.get("path","")
            #password = entry.get("password")
            full_path = os.path.join(self.folder_path, path)
            if not link:
                continue

            if link.startswith("magnet:?"):
                torrent_hash = add_magnet_link(link, self.folder_path)
                if torrent_hash:
                    print("Magnet agregado "+torrent_hash)

            elif link.endswith(".torrent"):
                def make_on_finished(idx, path):
                    def check_file(attempt=1):
                        if os.path.exists(path):
                            add_torrent_file(path, self.folder_path)
                            self.mark_finished(idx, DownloadType.TEMPORAL)
                        elif attempt < 10:
                            QTimer.singleShot(200, lambda: check_file(attempt + 1))
                        else:
                            print(f"❌ Archivo .torrent no encontrado: {path}")
                    return lambda: check_file()
                
                label = QLabel(f"Descargando .torrent: {path}")
                bar = QProgressBar()
                bar.setValue(0)
                self.inner_layout.addWidget(label)
                self.inner_layout.addWidget(bar)
                self.temp_labels.append(label)
                self.temp_progress_bars.append(bar)

                signals = DownloadSignals()
                signals.progress.connect(self.update_progress)
                signals.finished.connect(make_on_finished(index, full_path))

                thread = FileDownloader(link, full_path, index, signals)
                QThreadPool.globalInstance().start(thread)

            else:
                # Descarga directa normal
                dir_path = os.path.dirname(full_path)
                if dir_path:
                    os.makedirs(dir_path, exist_ok=True)

                label = QLabel(f"Descargando: {path}")
                bar = QProgressBar()
                bar.setValue(0)
                self.inner_layout.addWidget(label)
                self.inner_layout.addWidget(bar)
                self.labels.append(label)
                self.progress_bars.append(bar)

                signals = DownloadSignals()
                signals.progress.connect(self.update_progress)
                signals.finished.connect(lambda idx=index: self.mark_finished(idx))

                thread = FileDownloader(link, full_path, index, signals)
                QThreadPool.globalInstance().start(thread)
        
        self.show()

    def open_settings_dialog(self):
        dialog = SettingsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.folder_path,
            self.open_on_finish,
            self.max_parallel_downloads = apply_settings()

    def start_torrent_update(self):
        updater = TorrentUpdater()
        updater.signals.result.connect(self.on_torrent_data_received)
        updater.signals.error.connect(self.on_torrent_update_error)
        QThreadPool.globalInstance().start(updater)

    def on_torrent_update_error(self,message):
        if message!="""<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">
            <html><head>
            <title>404 Not Found</title>
            </head><body>
            <h1>Not Found</h1>
            <p>The requested URL was not found on this server.</p>
            </body></html>""":
            print(f"Error al actualizar progreso de torrents: {message}")

    def on_torrent_data_received(self, torrents):
        for t in torrents:
            if t.state in ("pausedDL", "pausedUP", "checkingUP", "checkingDL", "queuedDL"):
                continue
            if t.hash in self.torrent_hashes:
                index, _ = self.torrent_hashes[t.hash]
                percent = int(t.progress * 100)
                self.torrent_progress_bars[index].setValue(percent)
                if percent >= 100:
                    self.mark_finished(index)
                    self.torrent_hashes.pop(t.hash, None)
            else:
                label = QLabel(f"Descargando torrent: {t.name}")
                bar = QProgressBar()
                bar.setValue(int(t.progress * 100))
                self.inner_layout.addWidget(label)
                self.inner_layout.addWidget(bar)
                index = len(self.torrent_labels)
                self.torrent_labels.append(label)
                self.torrent_progress_bars.append(bar)
                self.torrent_hashes[t.hash] = (index, t.name)

    def update_progress(self, index, percent):
        if index >= len(self.progress_bars):
            return
        self.progress_bars[index].setValue(percent)

    def mark_finished(self, index, download_type=DownloadType.NORMAL):
        if download_type == DownloadType.TORRENT:
            lb = self.torrent_labels[index]
            pb = self.torrent_progress_bars[index]
        elif download_type == DownloadType.TEMPORAL:
            lb = self.temp_labels[index]
            pb = self.temp_progress_bars[index]
        else:  # NORMAL
            lb = self.labels[index]
            pb = self.progress_bars[index]

        done = f"✅ Completado: {lb.text()[12:]}"
        print(done)
        lb.setText(done)
        self.inner_layout.removeWidget(pb)
        pb.deleteLater()
        if download_type == DownloadType.TEMPORAL:
            self.inner_layout.removeWidget(lb)
            lb.deleteLater()
         
#Optional - Ventana para ingresar links
class LinkInputWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pegar enlaces de paginas de descarga")
        self.setMinimumSize(400, 200)

        layout = QVBoxLayout()
        self.instructions = QLabel("Pega uno o más enlaces (uno por línea):")
        self.textbox = QTextEdit()
        self.accept_button = QPushButton("Iniciar Descargas")
        self.accept_button.clicked.connect(self.proceed)
        self.settings_button = QPushButton('⚙')
        self.settings_button.clicked.connect(self.open_settings_dialog)
        self.settings_button.setFixedWidth(25) 

        layout.addWidget(self.instructions)
        layout.addWidget(self.textbox)
        buttons = QHBoxLayout()
        buttons.addWidget(self.accept_button)
        buttons.addWidget(self.settings_button)
        layout.addLayout(buttons)
        self.setLayout(layout)

        self.links = []

    def open_settings_dialog(self):
        dialog = SettingsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            apply_settings()
    
    def proceed(self):
        text = self.textbox.toPlainText().strip()
        if text:
            self.links = [line.strip() for line in text.splitlines() if line.strip()]
            self.close()

def apply_settings():
    config = load_config()
    folder_path = config.get("folder_path")
    open_on_finish = config.get("open_on_finish")
    max_parallel_downloads = config.get("max_parallel_downloads")
    print(f"✅ Configuración actualizada: {config}")
    return folder_path, open_on_finish, max_parallel_downloads

if __name__ == '__main__':
    os.system("title Descargas")
    app = QApplication(sys.argv)

    args = sys.argv[1:]

    if args and args[0].endswith(".json") and os.path.exists(args[0]):
        # Leer el JSON desde archivo
        with open(args[0], "r", encoding="utf-8") as f:
            json_data = json.load(f)
        window = DownloadWindow(json_data)
        sys.exit(app.exec_())
    else:
        # Modo interactivo: entrada de enlaces
        link_input = LinkInputWindow()
        link_input.show()
        app.exec_()
        if link_input.links:
            # Convertir a estructura de JSON mínima
            json_data = [{"url": url} for url in link_input.links]
            window = DownloadWindow(json_data)
            sys.exit(app.exec_())
