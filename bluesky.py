import os, json, requests, keyring, sys
from PyQt5.QtWidgets import (
    QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox, QDialog, QApplication
)
from PyQt5.QtCore import Qt
from appdirs import user_data_dir

CONFIG_FILE = os.path.join(user_data_dir("RedSocial", "IARA"), "config.json")
SERVICE_NAME = "Bluesky"

class LoginDialog(QDialog):
    def __init__(self, on_success):
        super().__init__()
        self.setWindowTitle("Iniciar sesión en Bluesky")
        self.on_success = on_success
        self.service_name = SERVICE_NAME
        self.resize(300, 150)

        self.user_input = QLineEdit()
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.Password)

        self.toggle_button = QPushButton("👁️")
        self.toggle_button.setCheckable(True)
        self.toggle_button.setFixedWidth(30)
        self.toggle_button.clicked.connect(self.toggle_password)

        self.login_button = QPushButton("Iniciar sesión")
        self.login_button.clicked.connect(self.try_login)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Usuario:"))
        layout.addWidget(self.user_input)
        layout.addWidget(QLabel("Contraseña:"))
        pass_layout = QHBoxLayout()
        pass_layout.addWidget(self.pass_input)
        pass_layout.addWidget(self.toggle_button)
        layout.addLayout(pass_layout)
        layout.addWidget(self.login_button)
        self.setLayout(layout)

        self.load_saved_user()

    def load_saved_user(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.user_input.setText(data.get("username", ""))
            except:
                pass

    def toggle_password(self):
        self.pass_input.setEchoMode(
            QLineEdit.Normal if self.toggle_button.isChecked() else QLineEdit.Password
        )

    def try_login(self):
        user = self.user_input.text().strip()
        pwd = self.pass_input.text()
        if not user or not pwd:
            QMessageBox.warning(self, "Campos vacíos", "Completa usuario y contraseña.")
            return
        self.on_success(user, pwd)
        self.accept()

class BlueskyClient:
    def __init__(self):
        self.handle = None
        self.password = None
        self.session = requests.Session()
        self.access_token = None
        self.refresh_token = None
        self.base_url = "https://bsky.social"

        # Intentar login automático
        if not self._try_load_credentials() or not self.login():
            self._show_login_dialog()

    def _try_load_credentials(self):
        if not os.path.exists(CONFIG_FILE):
            return False
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.handle = data.get("username")
                if self.handle:
                    self.password = keyring.get_password(SERVICE_NAME, self.handle)
                    return bool(self.password)
        except:
            return False
        return False

    def _save_credentials(self):
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"username": self.handle}, f)
        keyring.set_password(SERVICE_NAME, self.handle, self.password)

    def _show_login_dialog(self):
        app = QApplication.instance()
        owns_app = app is None
        if owns_app:
            app = QApplication(sys.argv)

        self.login_dialog = LoginDialog(self._on_login_success)
        self.login_dialog.exec_()

        if owns_app:
            app.quit()

    def _on_login_success(self, username, password):
        self.handle = username
        self.password = password
        if self.login():
            self._save_credentials()
        else:
            keyring.delete_password(SERVICE_NAME, username)
            self._show_login_dialog()

    def login(self):
        url = f"{self.base_url}/xrpc/com.atproto.server.createSession"
        payload = {
            "identifier": self.handle,
            "password": self.password
        }
        response = self.session.post(url, json=payload)
        if response.status_code == 200:
            data = response.json()
            self.access_token = data.get("accessJwt")
            self.refresh_token = data.get("refreshJwt")
            self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})
            return True
        else:
            print(f"[❌] Error al autenticar Bluesky: {response.status_code} - {response.text}")
            return False

    def get_timeline(self, limit=30, cursor=None):
        url = f"{self.base_url}/xrpc/app.bsky.feed.getTimeline"
        params = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        response = self.session.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error al obtener el feed de Bluesky: {response.status_code} - {response.text}")
            return None

    def get_posts_data(self, timeline_json):
        posts = []
        if not timeline_json:
            return posts
        for item in timeline_json.get("feed", []):
            post_data = item.get("post", {})
            author = post_data.get("author", {})
            text = post_data.get("record", {}).get("text", "")
            embed = post_data.get("embed", {})
            images = []
            if embed.get("$type") == "app.bsky.embed.images#view":
                for img in embed.get("images", []):
                    full_url = img.get("thumb")
                    if full_url:
                        images.append(full_url)

            post_url = f"https://bsky.app/profile/{author.get('handle')}/post/{post_data.get('uri').split('/')[-1]}"
            posts.append({
                "user": author.get("displayName") or author.get("handle", "Desconocido"),
                "handle": f"@{author.get('handle')}",
                "text": text,
                "time": post_data.get("indexedAt", "")[:16].replace("T", " "),
                "url": post_url,
                "stats": "",
                "images": images,
                "source": "🌤️ Bluesky"
            })
        return posts