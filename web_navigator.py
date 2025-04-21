import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, QTimer

# --------- Modo de automatización basado en el query ---------
def detect_mode(query: str) -> str:
    q = query.lower()
    if q.startswith("definir ") or "significado de" in q:
        return "wikipedia"
    # Aquí se pueden agregar más comandos
    return "default"

# --------- Generar URL de búsqueda según modo ---------
def generate_search_url(query: str, mode: str) -> str:
    if mode == "wikipedia":
        term = query.lower().replace("definir", "").strip()
        return f"https://es.wikipedia.org/wiki/{term.replace(' ', '_')}"
    return f"https://www.google.com/search?q={query}"

# --------- Función principal ---------
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
                # Nada extra, ya cargamos el artículo directamente
                print("[INFO] Modo Wikipedia: artículo cargado.")
            case _:
                print("[INFO] Modo por defecto, no hay automatización.")

    # Conectar evento de página cargada
    browser.loadFinished.connect(on_load_finished)

    sys.exit(app.exec_())

# --------- Entrada por línea de comandos ---------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python web_navigator.py 'tu consulta'")
        sys.exit(1)
    user_query = " ".join(sys.argv[1:])
    main(user_query)
