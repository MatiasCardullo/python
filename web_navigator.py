import sys
import argparse
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl

def open_browser(query: str, engine: str = "google"):
    """Open a mini-browser with the given query in the selected search engine."""
    app = QApplication(sys.argv)
    web = QWebEngineView()

    if engine == "google":
        url = f"https://www.google.com/search?q={query}"
    elif engine == "bing":
        url = f"https://www.bing.com/search?q={query}"
    elif engine == "duckduckgo":
        url = f"https://duckduckgo.com/?q={query}"
    else:
        url = f"https://www.google.com/search?q={query}"

    web.load(QUrl(url))
    web.setWindowTitle(f"Searching: {query}")
    web.resize(1024, 768)
    web.show()

    sys.exit(app.exec_())

def main():
    parser = argparse.ArgumentParser(description="Open a browser window and search the internet.")
    parser.add_argument("query", help="Search query string")
    parser.add_argument("--engine", choices=["google", "bing", "duckduckgo"], default="google", help="Search engine to use")
    args = parser.parse_args()
    open_browser(args.query, args.engine)

if __name__ == "__main__":
    main()
