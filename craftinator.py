import sys
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QListWidget, QSpinBox,
    QListWidgetItem, QMessageBox, QFileDialog, QComboBox, QTextEdit
)

class RecipeEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Editor y Calculador de Recetas de Crafteo")
        self.recipes = {}
        self.current_recipe = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Entrada del nombre del producto
        self.product_input = QLineEdit()
        layout.addWidget(QLabel("Producto"))
        layout.addWidget(self.product_input)

        # Tiempo de fabricación
        self.time_input = QSpinBox()
        self.time_input.setRange(1, 100000)
        layout.addWidget(QLabel("Tiempo de fabricación (segundos)"))
        layout.addWidget(self.time_input)

        # Lista de materiales
        self.materials_list = QListWidget()
        layout.addWidget(QLabel("Materiales (doble click para editar/eliminar)"))
        layout.addWidget(self.materials_list)

        # Entrada de material nuevo
        material_layout = QHBoxLayout()
        self.material_name_input = QLineEdit()
        self.material_qty_input = QSpinBox()
        self.material_qty_input.setRange(1, 10000)
        self.add_material_btn = QPushButton("Agregar Material")
        self.add_material_btn.clicked.connect(self.add_material)

        material_layout.addWidget(QLabel("Nombre"))
        material_layout.addWidget(self.material_name_input)
        material_layout.addWidget(QLabel("Cantidad"))
        material_layout.addWidget(self.material_qty_input)
        material_layout.addWidget(self.add_material_btn)

        layout.addLayout(material_layout)

        # Botones de guardar receta
        self.save_recipe_btn = QPushButton("Guardar/Actualizar Receta")
        self.save_recipe_btn.clicked.connect(self.save_recipe)
        layout.addWidget(self.save_recipe_btn)

        # Lista de recetas
        self.recipe_list = QListWidget()
        self.recipe_list.itemClicked.connect(self.load_recipe)
        layout.addWidget(QLabel("Recetas guardadas"))
        layout.addWidget(self.recipe_list)

        # Botones para guardar/cargar JSON
        file_buttons = QHBoxLayout()
        self.load_btn = QPushButton("Cargar JSON")
        self.load_btn.clicked.connect(self.load_from_json)
        self.save_btn = QPushButton("Guardar JSON")
        self.save_btn.clicked.connect(self.save_to_json)
        file_buttons.addWidget(self.load_btn)
        file_buttons.addWidget(self.save_btn)
        layout.addLayout(file_buttons)

        # Calculadora de producción
        layout.addWidget(QLabel("\n📦 Calculadora de Producción"))
        self.calc_product_selector = QComboBox()
        self.calc_rate_input = QSpinBox()
        self.calc_rate_input.setRange(1, 10000)
        self.calc_rate_input.setValue(1)
        self.calc_btn = QPushButton("Calcular materiales base")
        self.calc_btn.clicked.connect(self.calculate_resources)
        self.calc_output = QTextEdit()
        self.calc_output.setReadOnly(True)

        calc_layout = QHBoxLayout()
        calc_layout.addWidget(QLabel("Producto:"))
        calc_layout.addWidget(self.calc_product_selector)
        calc_layout.addWidget(QLabel("/min"))
        calc_layout.addWidget(self.calc_rate_input)
        calc_layout.addWidget(self.calc_btn)

        layout.addLayout(calc_layout)
        layout.addWidget(self.calc_output)

        self.setLayout(layout)

        # Eventos extra
        self.materials_list.itemDoubleClicked.connect(self.remove_material)

    def add_material(self):
        name = self.material_name_input.text().strip()
        qty = self.material_qty_input.value()
        if name:
            self.materials_list.addItem(f"{name} x{qty}")
            self.material_name_input.clear()
            self.material_qty_input.setValue(1)

    def remove_material(self, item):
        reply = QMessageBox.question(self, 'Eliminar Material',
                                     f"¿Eliminar '{item.text()}'?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            row = self.materials_list.row(item)
            self.materials_list.takeItem(row)

    def save_recipe(self):
        product = self.product_input.text().strip()
        time = self.time_input.value()
        if not product:
            QMessageBox.warning(self, "Error", "Nombre de producto vacío.")
            return

        materials = {}
        for i in range(self.materials_list.count()):
            text = self.materials_list.item(i).text()
            name, qty = text.split(" x")
            materials[name.strip()] = int(qty)

        self.recipes[product] = {
            "time": time,
            "materials": materials
        }
        self.refresh_recipe_list()
        QMessageBox.information(self, "Guardado", f"Receta '{product}' guardada correctamente.")

    def load_recipe(self, item):
        product = item.text()
        self.product_input.setText(product)
        self.time_input.setValue(self.recipes[product]["time"])
        self.materials_list.clear()
        for mat, qty in self.recipes[product]["materials"].items():
            self.materials_list.addItem(f"{mat} x{qty}")

    def refresh_recipe_list(self):
        self.recipe_list.clear()
        self.calc_product_selector.clear()
        for recipe in sorted(self.recipes):
            self.recipe_list.addItem(recipe)
            self.calc_product_selector.addItem(recipe)

    def save_to_json(self):
        path, _ = QFileDialog.getSaveFileName(self, "Guardar como", filter="JSON (*.json)")
        if path:
            with open(path, 'w') as f:
                json.dump(self.recipes, f, indent=2)
            QMessageBox.information(self, "Guardado", "Archivo JSON guardado correctamente.")

    def load_from_json(self):
        path, _ = QFileDialog.getOpenFileName(self, "Cargar archivo", filter="JSON (*.json)")
        if path:
            with open(path, 'r') as f:
                self.recipes = json.load(f)
            self.refresh_recipe_list()
            QMessageBox.information(self, "Cargado", "Archivo JSON cargado correctamente.")

    def calculate_resources(self):
        product = self.calc_product_selector.currentText()
        rate_per_minute = self.calc_rate_input.value()

        def resolve_tree(prod, amount_per_min):
            if prod not in self.recipes:
                return {prod: amount_per_min}  # recurso base

            recipe = self.recipes[prod]
            output_per_cycle = 1
            time_per_cycle = recipe["time"] / 60  # a minutos
            cycles_per_min = amount_per_min / output_per_cycle

            total = {}
            for mat, qty in recipe["materials"].items():
                sub_needed = qty * cycles_per_min
                sub_tree = resolve_tree(mat, sub_needed)
                for k, v in sub_tree.items():
                    total[k] = total.get(k, 0) + v
            return total

        result = resolve_tree(product, rate_per_minute)
        output = f"Para producir {rate_per_minute} {product}/min se necesita:\n"
        for mat, qty in sorted(result.items()):
            output += f"- {qty:.2f} {mat}/min\n"
        self.calc_output.setPlainText(output)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = RecipeEditor()
    win.resize(700, 700)
    win.show()
    sys.exit(app.exec_())
