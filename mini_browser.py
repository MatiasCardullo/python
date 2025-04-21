import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWebEngineWidgets import QWebEngineView

def open_browser(query):
    app = QApplication(sys.argv)
    web = QWebEngineView()
    url = f"https://www.google.com/search?q={query}"
    web.load(url)
    web.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("query", help="Search query")
    args = parser.parse_args()
    open_browser(args.query)
