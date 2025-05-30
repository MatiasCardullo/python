from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QTableWidget, QTableWidgetItem, QComboBox, QSpinBox,
    QDoubleSpinBox, QListWidget, QFileDialog, QTabWidget, QMessageBox, QFormLayout
)
import sys
import json
import os

class RecipeManager:
    def __init__(self):
        self.recipes = {}

    def add_recipe(self, name, time, amount, materials):
        self.recipes[name] = {
            "time": time,
            "amount": amount,
            "materials": materials
        }

    def save_to_file(self, filepath):
        with open(filepath, "w") as f:
            json.dump(self.recipes, f, indent=2)

    def load_from_file(self, filepath):
        with open(filepath, "r") as f:
            self.recipes = json.load(f)

    def calculate_requirements(self, product, desired_rate_per_min):
        requirements = {}

        def helper(prod, rate_needed, final_call=False):
            if prod not in self.recipes:
                requirements[prod] = {
                    "type": "base",
                    "qty": requirements.get(prod, {}).get("qty", 0.0) + rate_needed,
                    "prod_per_machine": 0,
                    "machines_needed": 0
                }
                return

            recipe = self.recipes[prod]
            time = recipe["time"]
            amount = recipe.get("amount", 1)
            prod_per_machine = (60 / time) * amount
            if prod not in requirements:
                requirements[prod] = {
                    "type": "final" if final_call else "intermedio",
                    "qty": 0.0,
                    "prod_per_machine": prod_per_machine,
                    "machines_needed": 0
                }

            requirements[prod]["qty"] += rate_needed
            requirements[prod]["machines_needed"] = requirements[prod]["qty"] / prod_per_machine

            multiplier = rate_needed / amount
            for mat, qty in recipe["materials"].items():
                helper(mat, qty * multiplier)

        helper(product, desired_rate_per_min, final_call=True)
        return requirements

class RecipeEditorTab(QWidget):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        form = QFormLayout()
        self.name_input = QLineEdit()
        self.time_input = QDoubleSpinBox()
        self.time_input.setDecimals(2)
        self.time_input.setMaximum(9999)
        self.time_unit_selector = QComboBox()
        self.time_unit_selector.addItems(["segundos", "minutos", "horas"])
        self.amount_input = QSpinBox()
        self.amount_input.setMinimum(1)
        self.amount_input.setMaximum(9999)

        time_row = QHBoxLayout()
        time_row.addWidget(self.time_input)
        time_row.addWidget(self.time_unit_selector)
        form.addRow("Producto:", self.name_input)
        form.addRow("Tiempo de fabricación:", time_row)
        form.addRow("Cantidad producida:", self.amount_input)
        layout.addLayout(form)

        self.materials_layout = QVBoxLayout()
        self.material_inputs = []

        layout.addWidget(QLabel("Materiales:"))
        layout.addLayout(self.materials_layout)

        add_mat_button = QPushButton("Agregar material")
        add_mat_button.clicked.connect(lambda: self.add_material_row())
        layout.addWidget(add_mat_button)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Agregar receta")
        edit_btn = QPushButton("Modificar receta")
        delete_btn = QPushButton("Eliminar receta")
        save_btn = QPushButton("Guardar JSON")
        load_btn = QPushButton("Cargar JSON")
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(load_btn)
        add_btn.clicked.connect(self.save_recipe)
        edit_btn.clicked.connect(self.load_selected_recipe)
        delete_btn.clicked.connect(self.delete_selected_recipe)
        save_btn.clicked.connect(self.save_json)
        load_btn.clicked.connect(self.load_json)


        layout.addLayout(btn_layout)

        self.recipe_list = QListWidget()
        layout.addWidget(QLabel("Recetas existentes:"))
        layout.addWidget(self.recipe_list)

        self.setLayout(layout)

    def add_material_row(self, mat_name="", qty=0):
        row = QHBoxLayout()
        mat_input = QLineEdit()
        qty_input = QDoubleSpinBox()
        qty_input.setMaximum(9999)
        mat_input.setText(mat_name)
        qty_input.setValue(qty)

        remove_btn = QPushButton("🗑")
        remove_btn.setFixedWidth(30)

        def remove():
            for i in range(self.materials_layout.count()):
                if self.materials_layout.itemAt(i).layout() == row:
                    for j in reversed(range(row.count())):
                        widget = row.itemAt(j).widget()
                        if widget:
                            widget.deleteLater()
                    self.materials_layout.removeItem(row)
                    self.material_inputs.pop(i)
                    break

        remove_btn.clicked.connect(remove)

        row.addWidget(QLabel("Material:"))
        row.addWidget(mat_input)
        row.addWidget(QLabel("Cantidad:"))
        row.addWidget(qty_input)
        row.addWidget(remove_btn)

        self.materials_layout.addLayout(row)
        self.material_inputs.append((mat_input, qty_input, remove_btn))
    
    def save_recipe(self):
        name = self.name_input.text().strip()
        time = self.time_input.value()
        unit = self.time_unit_selector.currentText()
        if unit == "minutos":
            time *= 60
        elif unit == "horas":
            time *= 3600
        amount = self.amount_input.value()

        if not name:
            QMessageBox.warning(self, "Error", "El nombre del producto no puede estar vacío.")
            return

        materials = {}
        for mat_input, qty_input, _ in self.material_inputs:
            mat = mat_input.text().strip()
            qty = qty_input.value()
            if mat:
                materials[mat] = qty

        self.manager.add_recipe(name, time, amount, materials)
        self.refresh_recipe_list()
        self.clear_inputs()

    def load_selected_recipe(self):
        selected = self.recipe_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "Error", "Seleccioná una receta de la lista.")
            return

        name = selected.text()
        recipe = self.manager.recipes.get(name)
        if not recipe:
            return

        self.name_input.setText(name)
        total_seconds = recipe["time"]
        if total_seconds % 3600 == 0:
            self.time_input.setValue(total_seconds / 3600)
            self.time_unit_selector.setCurrentText("horas")
        elif total_seconds % 60 == 0:
            self.time_input.setValue(total_seconds / 60)
            self.time_unit_selector.setCurrentText("minutos")
        else:
            self.time_input.setValue(total_seconds)
            self.time_unit_selector.setCurrentText("segundos")
        self.amount_input.setValue(recipe.get("amount", 1))

        for i in reversed(range(self.materials_layout.count())):
            child = self.materials_layout.takeAt(i)
            while child.count():
                widget = child.takeAt(0).widget()
                if widget:
                    widget.deleteLater()

        self.material_inputs.clear()

        for mat, qty in recipe["materials"].items():
            self.add_material_row(mat, qty)
    
    def delete_selected_recipe(self):
        selected = self.recipe_list.currentItem()
        if not selected:
            return
        name = selected.text()
        confirm = QMessageBox.question(self, "Confirmar", f"¿Eliminar receta '{name}'?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            del self.manager.recipes[name]
            self.refresh_recipe_list()

    def save_json(self):
        path, _ = QFileDialog.getSaveFileName(self, "Guardar archivo de recetas", "", "JSON files (*.json)")
        if path:
            self.manager.save_to_file(path)

    def load_json(self):
        path, _ = QFileDialog.getOpenFileName(self, "Cargar archivo de recetas", "", "JSON files (*.json)")
        if path:
            self.manager.load_from_file(path)
            self.refresh_recipe_list()

    def clear_inputs(self):
        self.name_input.clear()
        self.time_input.setValue(0)
        self.amount_input.setValue(1)
        for layout in self.materials_layout.children():
            if isinstance(layout, QHBoxLayout):
                while layout.count():
                    w = layout.takeAt(0).widget()
                    if w:
                        w.deleteLater()
        self.material_inputs.clear()
    
    def refresh_recipe_list(self):
        self.recipe_list.clear()
        for r in self.manager.recipes:
            self.recipe_list.addItem(r)

class CalculatorTab(QWidget):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.unit_index = 1
        self.unit_labels = ["seg", "min", "hora"]
        self.unit_multipliers = [1/60, 1, 60]
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        input_layout = QHBoxLayout()

        self.product_selector = QComboBox()
        self.rate_input = QDoubleSpinBox()
        self.rate_input.setDecimals(2)
        self.rate_input.setMaximum(999999)
        self.rate_unit_selector = QComboBox()
        self.rate_unit_selector.addItems(["/seg", "/min", "/hora"])

        rate_layout = QHBoxLayout()
        rate_layout.addWidget(self.rate_input)
        rate_layout.addWidget(self.rate_unit_selector)
        input_layout.addWidget(QLabel("Producto final:"))
        input_layout.addWidget(self.product_selector)
        input_layout.addWidget(QLabel("Tasa deseada:"))
        input_layout.addLayout(rate_layout)

        calc_btn = QPushButton("Calcular")
        calc_btn.clicked.connect(self.calculate)

        layout.addLayout(input_layout)
        layout.addWidget(calc_btn)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.update_headers()
        self.table.horizontalHeader().sectionClicked.connect(self.header_clicked)
        layout.addWidget(self.table)

        self.setLayout(layout)

    def refresh_product_list(self):
        self.product_selector.clear()
        if not self.manager.recipes:
            self.product_selector.setEnabled(False)
        else:
            self.product_selector.addItems(self.manager.recipes.keys())
            self.product_selector.setEnabled(True)

    def update_headers(self):
        labels = ["Producto", "Tipo",
                f"Cantidad/{self.unit_labels[self.unit_index]}",
                "Prod/Máquina", "Máquinas"]
        self.table.setHorizontalHeaderLabels(labels)
    
    def header_clicked(self, index):
        if index == 2:
            self.unit_index = (self.unit_index + 1) % 3
            self.update_headers()
            self.calculate()

    def calculate(self):
        product = self.product_selector.currentText()
        rate = self.rate_input.value()
        unit = self.rate_unit_selector.currentText()
        if unit == "/seg":
            rate *= 60
        elif unit == "/hora":
            rate /= 60

        if not product:
            QMessageBox.warning(self, "Error", "Seleccione un producto y una tasa válida.")
            return

        results = self.manager.calculate_requirements(product, rate)

        self.table.setRowCount(len(results))
        for row, (name, info) in enumerate(results.items()):
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(info["type"]))
            mult = self.unit_multipliers[self.unit_index]
            adjusted_qty = info['qty'] * mult
            self.table.setItem(row, 2, QTableWidgetItem(f"{adjusted_qty:.2f}"))
            self.table.setItem(row, 3, QTableWidgetItem(f"{info['prod_per_machine']:.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"{info['machines_needed']:.2f}"))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🧱 Calculadora de crafteo universal")
        self.resize(800, 600)

        self.manager = RecipeManager()

        self.tabs = QTabWidget()
        self.tab_editor = RecipeEditorTab(self.manager)
        self.tab_calculator = CalculatorTab(self.manager)

        self.tabs.addTab(self.tab_editor, "📦 Recetas")
        self.tabs.addTab(self.tab_calculator, "🧮 Calculadora")

        self.setCentralWidget(self.tabs)
        self.tabs.currentChanged.connect(self.on_tab_changed)

    def on_tab_changed(self, index):
        if self.tabs.widget(index) == self.tab_calculator:
            self.tab_calculator.refresh_product_list()

    def closeEvent(self, event):
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
