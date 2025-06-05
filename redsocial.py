import os, tempfile, urllib.request, sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QPushButton, QTabWidget, QDialog, QFileDialog
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import Qt, QUrl, QTimer, QThread, QObject, pyqtSignal
from PyQt5.QtGui import QPixmap
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

class PostWidget(QFrame):
    def __init__(self, data):
        super().__init__()
        self.setFrameShape(QFrame.Box)
        #self.setStyleSheet("padding: 5px; margin: 5px;")
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"<b>{data['user']}</b> {data['handle']} - {data['time']} {data.get('source', '')}"))
        layout.addWidget(QLabel(f"{data['text']}\n\n🔗 {data['url']}\n📊 {data['stats']}"))
        if data['images']:
            img_row = QHBoxLayout()
            for img_url in data['images']:
                try:
                    base_name = os.path.basename(img_url.split("?")[0])
                    safe_name = urllib.parse.quote(base_name, safe='')
                    temp_path = os.path.join(tempfile.gettempdir(), safe_name)
                    if not os.path.exists(temp_path):
                        urllib.request.urlretrieve(img_url, temp_path)
                    img_label = ClickableLabel()
                    pixmap = QPixmap(temp_path)
                    img_label.setPixmap(pixmap)
                    img_label.clicked.connect(lambda path=img_url: ImageDialog(path).exec_())
                    img_row.addWidget(img_label)
                except Exception as e:
                    print(f"Error al cargar imagen: {e}")
            layout.addLayout(img_row)
        self.setLayout(layout)

class ClickableLabel(QLabel):
    clicked = pyqtSignal()
    def mousePressEvent(self, event):
        self.clicked.emit()

class ImageLoader(QObject):
    finished = pyqtSignal(QPixmap)
    failed = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            base_name = os.path.basename(self.url.split("?")[0])
            safe_name = urllib.parse.quote(base_name, safe='')
            temp_path = os.path.join(tempfile.gettempdir(), "large_" + safe_name)
            if not os.path.exists(temp_path):
                def mejorar_calidad(url):
                    parsed = urlparse(url)
                    qs = parse_qs(parsed.query)
                    qs["name"] = ["large"]
                    new_query = urlencode(qs, doseq=True)
                    parsed = parsed._replace(query=new_query)
                    return urlunparse(parsed)
                url_mejorado = mejorar_calidad(self.url)
                urllib.request.urlretrieve(url_mejorado, temp_path)
            pixmap = QPixmap(temp_path)
            self.finished.emit(pixmap)
        except Exception as e:
            self.failed.emit(str(e))

class ImageDialog(QDialog):
    def __init__(self, image_url):
        super().__init__()
        self.setWindowTitle("Imagen ampliada")
        self.setMinimumSize(1200, 800)

        self.label = QLabel("Cargando imagen...", alignment=Qt.AlignCenter)
        self.save_button = QPushButton("💾 Guardar imagen")
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.guardar_imagen)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.save_button, alignment=Qt.AlignRight)
        self.setLayout(self.layout)

        self.pixmap = None
        self.thread = QThread()
        self.loader = ImageLoader(image_url)
        self.loader.moveToThread(self.thread)
        self.thread.started.connect(self.loader.run)
        self.loader.finished.connect(self.mostrar_imagen)
        self.loader.failed.connect(self.mostrar_error)
        self.loader.finished.connect(self.thread.quit)
        self.loader.failed.connect(self.thread.quit)
        self.thread.start()

    def mostrar_imagen(self, pixmap):
        self.pixmap = pixmap
        self.label.setPixmap(pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.label.setText("")
        self.save_button.setEnabled(True)

    def mostrar_error(self, msg):
        self.label.setText(f"❌ Error al cargar imagen:\n{msg}")
        self.save_button.setEnabled(False)

    def guardar_imagen(self):
        if not self.pixmap:
            return
        file_path, _ = QFileDialog.getSaveFileName(self, "Guardar imagen", "", "Imagen (*.png *.jpg *.jpeg)")
        if file_path:
            self.pixmap.save(file_path)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mini Red Social")
        self.resize(1200, 700)

        self.tweet_urls = set()
        main_layout = QHBoxLayout(self)

        menu_layout = QVBoxLayout()
        menu_layout.addWidget(QLabel("🏠 Inicio"))
        menu_layout.addWidget(QLabel("🔍 Buscar"))
        menu_layout.addWidget(QLabel("👤 Perfil"))
        menu_layout.addWidget(QLabel("⚙ Config"))
        menu_layout.addStretch()

        menu_widget = QWidget()
        menu_widget.setLayout(menu_layout)
        menu_widget.setFixedWidth(100)

        self.feed_layout = QVBoxLayout()
        self.feed_layout.setSpacing(10)

        self.feed_container = QWidget()
        self.feed_container.setLayout(self.feed_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.feed_container)

        self.refresh_btn = QPushButton("📥 Cargar Tweets")
        self.refresh_btn.clicked.connect(self.scrapear_tweets)

        center_layout = QVBoxLayout()
        center_layout.addWidget(self.refresh_btn)
        center_layout.addWidget(self.scroll_area)

        center_widget = QWidget()
        center_widget.setLayout(center_layout)

        self.tabs = QTabWidget()
        self.tabs.setFixedWidth(400)

        self.browser_twitter = QWebEngineView()
        self.browser_twitter.load(QUrl("https://x.com/i/lists/1894498544729636869"))
        self.browser_twitter.setZoomFactor(0.25)
        self.browser_twitter.loadFinished.connect(self.scrapear_tweets)
        self.tabs.addTab(self.browser_twitter, "🐦 Twitter")

        self.browser_misskey = QWebEngineView()
        self.browser_misskey.load(QUrl("https://misskey.io/"))
        self.browser_misskey.setZoomFactor(0.25)
        self.tabs.addTab(self.browser_misskey, "🌟 Misskey")

        self.browser_bluesky = QWebEngineView()
        self.browser_bluesky.load(QUrl("https://bsky.app/"))
        self.browser_bluesky.setZoomFactor(0.25)
        self.tabs.addTab(self.browser_bluesky, "🌤 Bluesky")

        main_layout.addWidget(menu_widget)
        main_layout.addWidget(center_widget, stretch=1)
        main_layout.addWidget(self.tabs)

    def scrapear_tweets(self):
        QTimer.singleShot(15000, self.obtener_twitter)

    def obtener_twitter(self):
        def mejorar_calidad(url):
            parsed = urlparse(url)
            qs = parse_qs(parsed.query)
            if 'name' in qs:
                qs['name'] = ['360x360']
                new_query = urlencode(qs, doseq=True)
                parsed = parsed._replace(query=new_query)
                return urlunparse(parsed)
            return url

        def handle_html(html):
            soup = BeautifulSoup(html, "html.parser")

            tweets = soup.find_all("article", attrs={"data-testid": "tweet"})
            print(f"Tweets encontrados: {len(tweets)}")

            for tweet in tweets:
                user_block = tweet.find("div", attrs={"data-testid": "User-Name"})
                if not user_block:
                    continue
                spans = user_block.find_all("span")
                user = spans[0].get_text(strip=True) if len(spans) > 0 else "Usuario"
                handle = spans[3].get_text(strip=True) if len(spans) > 3 else "@handle"
                datetime = user_block.find('time')
                time = datetime.text if datetime else "(sin hora)"
                tweet_url = datetime.find_parent('a')['href'] if datetime else "#"

                if tweet_url in self.tweet_urls:
                    continue
                self.tweet_urls.add(tweet_url)

                text_elem = tweet.find("div", {"data-testid": "tweetText"})
                text = text_elem.get_text(" ", strip=True) if text_elem else "(sin texto)"
                images = []
                for img_tag in tweet.find_all("img"):
                    src = img_tag.get("src")
                    if src and "profile_images" not in src and ".svg" not in src:
                        #print(src)
                        images.append(mejorar_calidad(src))
                stats_div = tweet.find("div", attrs={"role": "group"})
                stats = stats_div.get("aria-label", "") if stats_div else ""
                tweet_data = {
                    "source": "Twitter",
                    "user": user,
                    "handle": handle,
                    "text": text,
                    "time": time,
                    "url": tweet_url,
                    "stats": stats,
                    "images": images,
                }
                post = PostWidget(tweet_data)

                self.feed_layout.addWidget(post)

        self.browser_twitter.page().toHtml(handle_html)

    def closeEvent(self, event):
        self.browser_twitter.page().profile().clearHttpCache()
        self.browser_twitter.page().profile().deleteLater()
        self.browser_misskey.page().profile().clearHttpCache()
        self.browser_misskey.page().profile().deleteLater()
        self.browser_bluesky.page().profile().clearHttpCache()
        self.browser_bluesky.page().profile().deleteLater()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
