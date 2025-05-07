import json
import os
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QSpinBox, QPushButton

CONFIG_PATH = "config.json"
DEFAULT_CONFIG = {
    "open_on_finish": True,
    "max_parallel_downloads": 2
}
def load_config():
    if not os.path.exists(CONFIG_PATH):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)
def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración de Descargas")
        self.config = load_config()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Check: Abrir carpeta al terminar
        self.open_folder_cb = QCheckBox("Abrir carpeta al finalizar")
        self.open_folder_cb.setChecked(self.config.get("open_on_finish", True))
        layout.addWidget(self.open_folder_cb)

        # SpinBox: Máximo de descargas paralelas
        hbox = QHBoxLayout()
        hbox.addWidget(QLabel("Máx. descargas paralelas:"))
        self.max_downloads_spin = QSpinBox()
        self.max_downloads_spin.setMinimum(1)
        self.max_downloads_spin.setMaximum(20)
        self.max_downloads_spin.setValue(self.config.get("max_parallel_downloads", 2))
        hbox.addWidget(self.max_downloads_spin)
        layout.addLayout(hbox)

        # Botones: Guardar / Cancelar
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Guardar")
        cancel_btn = QPushButton("Cancelar")
        save_btn.clicked.connect(self.save_and_close)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def save_and_close(self):
        self.config["open_on_finish"] = self.open_folder_cb.isChecked()
        self.config["max_parallel_downloads"] = self.max_downloads_spin.value()
        save_config(self.config)
        self.accept()

    def get_config(self):
        return self.config
