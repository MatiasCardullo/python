import sys
import subprocess
import subprocess
import re
import requests
from bs4 import BeautifulSoup
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, QEventLoop, QTimer


class MediafireScraper(QWebEngineView):
    def __init__(self, url, callback):
        super().__init__()
        self.callback = callback
        self.loadFinished.connect(self.on_load_finished)
        self.load(QUrl(url))
        self.show()


    def on_load_finished(self):
        print("[🕒] Página cargada, esperando para permitir carga de JS...")
        QTimer.singleShot(3000, lambda: self.page().toHtml(self.process_html))


    def process_html(self, html):
        print("[📄] HTML capturado, procesando...")
        self.callback(html)
        QApplication.instance().quit()


def get_file_page_links_from_folder_html(html):
    soup = BeautifulSoup(html, "html.parser")
    file_links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if re.match(r"^https?://www\.mediafire\.com/file/", href):
            file_links.append(href)
    return list(set(file_links))


def get_direct_download_link_from_html(html):
    soup = BeautifulSoup(html, "html.parser")
    button = soup.find("a", {"id": "downloadButton"})
    if button:
        return button["href"]
    return None


def run_scraper(url):
    app = QApplication(sys.argv)
    result = []

    def handle_folder_html(html):
        links = get_file_page_links_from_folder_html(html)
        result.extend(links)

    browser = MediafireScraper(url, handle_folder_html)
    app.exec_()
    return result


def get_direct_link_via_browser(url):
    app = QApplication(sys.argv)
    result = []

    def handle_file_html(html):
        direct = get_direct_download_link_from_html(html)
        result.append(direct)

    browser = MediafireScraper(url, handle_file_html)
    app.exec_()
    return result[0] if result else None


def main(folder_url, output_folder="mediafire_downloads"):
    #os.makedirs(output_folder, exist_ok=True)
    print(f"🔍 Getting file links from folder...")
    file_pages = run_scraper(folder_url)
    print(f"📄 Found {len(file_pages)} files. Getting direct links...")
    subprocess.run(["python", "mediafire_file_downloader.py"] + file_pages)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        folder_url = sys.argv[1:]
    else:
        folder_url = input("Enter MediaFire folder URL: ").strip()
    main(folder_url)
