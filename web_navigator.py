import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, QTimer

def detect_mode(query: str) -> str:
    q = query.lower()
    if q.startswith("definir ") or "significado de" in q:
        return "wikipedia"
    elif "video reciente de" in q or "último video de" in q:
        return "youtube_latest"
    return "default"

# --------- Generar URL de búsqueda según modo ---------
def generate_search_url(query: str, mode: str) -> str:
    if mode == "wikipedia":
        term = query.lower().replace("definir", "").replace("significado de", "").strip()
        return f"https://es.wikipedia.org/wiki/{term.replace(' ', '_')}"
    elif mode == "youtube_latest":
        channel = query.lower().replace("ver el video reciente de", "").replace("último video de", "").strip()
        return f"https://www.youtube.com/results?search_query={channel}"
    return f"https://www.google.com/search?q={query}"

def main(query: str):
    mode = detect_mode(query)
    search_url = generate_search_url(query, mode)

    app = QApplication(sys.argv)
    browser = QWebEngineView()
    browser.setWindowTitle("Assistant Browser")
    browser.resize(1000, 800)
    browser.show()
    print(f"[INFO] Cargando: {search_url}")
    browser.load(QUrl(search_url))

    # Automatización después de cargar la página
    def on_load_finished():
        match mode:
            case "wikipedia":
                print("[INFO] Modo Wikipedia: artículo cargado.")

            case "youtube_latest":
                print("[INFO] Modo YouTube: buscando video más reciente.")
                js = """
                    (function() {
                        let firstResult = document.querySelector('a#video-title');
                        if (firstResult) {
                            firstResult.click();
                        }
                    })();
                """
                QTimer.singleShot(2000, lambda: browser.page().runJavaScript(js))

            case _:

    # Conectar evento de página cargada
    browser.loadFinished.connect(on_load_finished)
    sys.exit(app.exec_())

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python web_navigator.py 'tu consulta'")
        sys.exit(1)
    user_query = " ".join(sys.argv[1:])
    main(user_query)
