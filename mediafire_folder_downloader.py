import sys
import os
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


def download_file(url, dest_folder):
    filename = url.split("/")[-1].split("?")[0]
    dest_path = os.path.join(dest_folder, filename)
    print(f"⬇️  Downloading: {filename}")
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
    print(f"✅ Saved: {dest_path}")


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
    os.makedirs(output_folder, exist_ok=True)
    print(f"🔍 Getting file links from folder...")
    file_pages = run_scraper(folder_url)
    print(f"📄 Found {len(file_pages)} files. Getting direct links...")
    for i, url in enumerate(file_pages, 1):
        print(f"\n[{i}/{len(file_pages)}] 🧭 Abriendo archivo: {url}")
        direct_link = get_direct_link_via_browser(url)
        if direct_link:
            print(f"✅ Direct link: {direct_link}")
            download_file(direct_link, output_folder)
        else:
            print(f"❌ No se pudo obtener el link directo.")


if __name__ == "__main__":
    folder_url = input("Enter MediaFire folder URL: ").strip()
    main(folder_url)
