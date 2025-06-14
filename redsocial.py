import os, tempfile, urllib.request, sys
import webbrowser
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QPushButton, QTabWidget, QDialog, QFileDialog
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import Qt, QUrl, QTimer, QThread, QObject, pyqtSignal
from PyQt5.QtGui import QPixmap
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from bluesky import BlueskyClient

def calidad_bluesky(url):
    parsed = urlparse(url)
    new_path = parsed.path.replace("feed_thumbnail", "feed_fullsize")
    return urlunparse(parsed._replace(path=new_path))

def calidad_twitter(url,size):
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    if "name" in qs:
        qs["name"] = [size]
        new_query = urlencode(qs, doseq=True)
        parsed = parsed._replace(query=new_query)
        return urlunparse(parsed)
    return url

class PostWidget(QFrame):
    def __init__(self, data):
        super().__init__()
        source = data.get('source', '')
        self.setFrameShape(QFrame.Box)
        #self.setStyleSheet("padding: 5px; margin: 5px;")
        layout = QVBoxLayout()
        link_button = QPushButton(source + " link")
        link_button.clicked.connect(lambda: webbrowser.open(data['url']))
        layout.addWidget(link_button)
        layout.addWidget(QLabel(f"""<b>{data['user']}</b> 
                                {data['handle']} - 
                                {data['time']} 
                                {source}"""))
        layout.addWidget(QLabel(f"""{data['text']}\n\n📊 {data['stats']}"""))
        if data['images']:
            img_row = QHBoxLayout()
            for img_url in data['images']:
                try:
                    base_name = os.path.basename(img_url.split("?")[0])
                    safe_name = urllib.parse.quote(base_name, safe='')
                    temp_path = os.path.join(tempfile.gettempdir(), safe_name)
                    if not os.path.exists(temp_path):
                        urllib.request.urlretrieve(calidad_twitter(img_url,"360x360"), temp_path)
                    img_label = ClickableLabel()
                    pixmap = QPixmap(temp_path).scaledToHeight(360)
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
                if "cdn.bsky.app" in self.url:
                    url_mejorado = calidad_bluesky(self.url)
                else:
                    url_mejorado = calidad_twitter(self.url,"large")
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

        self.scroll_cooldown = False
        self.posts_urls = set()
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
        self.scroll_area.verticalScrollBar().valueChanged.connect(self.check_scroll_position)

        self.refresh_twt_btn = QPushButton("📥 Cargar Tweets")
        self.refresh_twt_btn.clicked.connect(self.scrapear_tweets)
        self.refresh_bs_btn = QPushButton("🌤️ Cargar Bluesky")
        self.refresh_bs_btn.clicked.connect(self.obtener_posts_bluesky)
        self.bluesky_client = BlueskyClient()

        center_layout = QVBoxLayout()
        buttons = QHBoxLayout()
        buttons.addWidget(self.refresh_twt_btn)
        buttons.addWidget(self.refresh_bs_btn)
        center_layout.addLayout(buttons)
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

        main_layout.addWidget(menu_widget)
        main_layout.addWidget(center_widget, stretch=1)
        main_layout.addWidget(self.tabs)

    def reset_scroll_cooldown(self):
        self.scroll_cooldown = False

    def check_scroll_position(self):
        if self.scroll_cooldown:
            return

        scrollbar = self.scroll_area.verticalScrollBar()
        value = scrollbar.value()
        maximum = scrollbar.maximum()

        threshold = 500
        if value >= maximum - threshold:
            #print("🔻 Scroll cerca del final, cargando más contenido...")
            self.scroll_cooldown = True
            QTimer.singleShot(15000, self.reset_scroll_cooldown)
            js_scroll = f"""
                const current = window.scrollY;
                const visible = window.innerHeight;
                const total = document.body.scrollHeight;

                const remaining = total - current - visible;
                const nextScroll = current + remaining / 3;

                window.scrollTo(0, nextScroll);
            """
            self.browser_twitter.page().runJavaScript(js_scroll)
            self.scroll_depth_ratio += (1 - self.scroll_depth_ratio) / 5
            self.scrapear_tweets()
    
    def scrapear_tweets(self):
        self.obtener_posts_bluesky()
        QTimer.singleShot(15000, self.obtener_twitter)

    def obtener_twitter(self):
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
                tweet_url = "https://x.com"+datetime.find_parent('a')['href'] if datetime else "#"
                if tweet_url in self.posts_urls:
                    continue
                self.posts_urls.add(tweet_url)
                text_elem = tweet.find("div", {"data-testid": "tweetText"})
                text = text_elem.get_text(" ", strip=True) if text_elem else ""
                images = []
                for img_tag in tweet.find_all("img"):
                    src = img_tag.get("src")
                    if src and "profile_images" not in src and ".svg" not in src:
                        images.append(src)
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

    def obtener_posts_bluesky(self):
        timeline = self.bluesky_client.get_timeline()
        posts = self.bluesky_client.get_posts_data(timeline)
        for post_data in posts:
            if post_data["url"] in self.posts_urls:
                continue
            self.posts_urls.add(post_data["url"])
            widget = PostWidget(post_data)
            self.feed_layout.addWidget(widget)
    
    def closeEvent(self, event):
        self.browser_twitter.page().profile().clearHttpCache()
        self.browser_twitter.page().profile().deleteLater()
        self.browser_misskey.page().profile().clearHttpCache()
        self.browser_misskey.page().profile().deleteLater()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
