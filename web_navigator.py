import sys
import webbrowser
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, QTimer
from site_selector import detect_special_site
from datetime import datetime

HISTORY_PATH = "history.txt"

def log_history(entry: str):
    with open(HISTORY_PATH, "a", encoding="utf-8") as f:
        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        f.write(f"{timestamp} {entry}\n")

def open_webpage(url: str):
    app = QApplication(sys.argv)
    browser = QWebEngineView()
    browser.setWindowTitle("Assistant Browser")
    browser.resize(1000, 800)
    browser.show()
    browser.load(QUrl(search_url))

    log_history(f"Opened URL: {url}")
    sys.exit(app.exec_())

def smart_search(query: str):
    special_site = detect_special_site(query)

    if special_site:
        log_history(f"Detected specialized topic: {query} -> {special_site}")
        open_webpage(special_site)
    else:
        search_url = f"https://www.google.com/search?q={query}"
        log_history(f"Performed Google search: {query}")
        open_webpage(search_url)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        search_query = " ".join(sys.argv[1:])
        smart_search(search_query)
    else:
        print("Uso: python web_navigator.py 'tu consulta'")
