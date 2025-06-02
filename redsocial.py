import os, tempfile, urllib.request, sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QPushButton, QTabWidget
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, QTimer, pyqtSignal
from PyQt5.QtGui import QPixmap
from bs4 import BeautifulSoup

class PostWidget(QFrame):
    def __init__(self, top, text, images):
        super().__init__()
        self.setFrameShape(QFrame.Box)
        #self.setStyleSheet("padding: 5px; margin: 5px;")
        layout = QVBoxLayout()
        layout.addWidget(QLabel(top))
        layout.addWidget(QLabel(text))
        if images:
            img_row = QHBoxLayout()
            for img_url in images:
                try:
                    base_name = os.path.basename(img_url.split("?")[0])
                    safe_name = urllib.parse.quote(base_name, safe='')
                    temp_path = os.path.join(tempfile.gettempdir(), safe_name)
                    if not os.path.exists(temp_path):
                        urllib.request.urlretrieve(img_url, temp_path)
                    img_label = QLabel()
                    pixmap = QPixmap(temp_path).scaledToWidth(150)
                    img_label.setPixmap(pixmap)
                    img_row.addWidget(img_label)
                except Exception as e:
                    print(f"Error al cargar imagen: {e}")
            layout.addLayout(img_row)
        self.setLayout(layout)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mini Red Social")
        self.resize(1200, 700)

        main_layout = QHBoxLayout(self)

        menu_layout = QVBoxLayout()
        menu_layout.addWidget(QLabel("🏠 Inicio"))
        menu_layout.addWidget(QLabel("🔍 Buscar"))
        menu_layout.addWidget(QLabel("👤 Perfil"))
        menu_layout.addWidget(QLabel("⚙ Config"))
        menu_layout.addStretch()

        menu_widget = QWidget()
        menu_widget.setLayout(menu_layout)

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

        self.browser = QWebEngineView()
        self.browser.load(QUrl("https://x.com/i/lists/1894498544729636869"))

        self.tabs = QTabWidget()
        self.tabs.addTab(center_widget, "📰 Feed")
        self.tabs.addTab(self.browser, "🌐 Navegador")

        main_layout.addWidget(menu_widget, 2)
        main_layout.addWidget(self.tabs, 8)

    def scrapear_tweets(self):
        QTimer.singleShot(5000, self.obtener_html)

    def obtener_html(self):
        def handle_html(html):
            soup = BeautifulSoup(html, "html.parser")

            # Limpiar el feed anterior
            while self.feed_layout.count():
                item = self.feed_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()

            tweets = soup.find_all("article", attrs={"data-testid": "tweet"})
            print(f"Tweets encontrados: {len(tweets)}")

            for tweet in tweets:
                # Usuario
                user_block = tweet.find("div", attrs={"data-testid": "User-Name"})
                if not user_block:
                    continue
                spans = user_block.find_all("span")
                user = spans[0].get_text(strip=True) if len(spans) > 0 else "Usuario"
                handle = spans[3].get_text(strip=True) if len(spans) > 3 else "@handle"
                datetime = user_block.find('time')#['datetime']
                time = datetime.text
                tweet_url = datetime.find_parent('a')['href']
                # Texto del tweet
                text_elem = tweet.find("div", {"data-testid": "tweetText"})
                text = text_elem.get_text(" ", strip=True) if text_elem else "(sin texto)"
                # Imágenes
                images = []
                for img_tag in tweet.find_all("img"):
                    src = img_tag.get("src")
                    if src and "profile_images" not in src and "emoji" not in src:
                        images.append(src)
                # Estadísticas del tweet
                stats_div = tweet.find("div", attrs={"role": "group"})
                stats = stats_div.get("aria-label", "") if stats_div else ""
                full_text = f"{text}\n\n🔗 {tweet_url}\n📊 {stats}"
                post = PostWidget(f"<b>{user}</b> {handle} - {time}", full_text, images)

                self.feed_layout.addWidget(post)
        self.browser.page().toHtml(handle_html)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
