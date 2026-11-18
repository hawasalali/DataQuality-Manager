import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QTableView,
    QFileDialog, QLabel, QMessageBox, QHBoxLayout, QLineEdit, QComboBox
)
from PyQt6.QtCore import Qt
from models.employee import Employee
from database.employee_repository import EmployeeRepository
from services.csv_importer import import_csv
from services.data_validator import validate_employee
from services.csv_exporter import export_to_csv, export_to_json
from services.report_generator import generate_validation_report
from ui.employee_table_model import EmployeeTableModel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DataQuality Manager")
        self.setGeometry(100, 100, 1000, 600)
        self.db_repo = EmployeeRepository()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Header
        header_layout = QHBoxLayout()
        self.import_button = QPushButton("CSV importieren")
        self.import_button.clicked.connect(self.on_import_csv)
        header_layout.addWidget(self.import_button)

        self.export_csv_button = QPushButton("Als CSV exportieren")
        self.export_csv_button.clicked.connect(self.on_export_csv)
        header_layout.addWidget(self.export_csv_button)

        self.export_json_button = QPushButton("Als JSON exportieren")
        self.export_json_button.clicked.connect(self.on_export_json)
        header_layout.addWidget(self.export_json_button)

        self.report_button = QPushButton("Validierungsbericht generieren")
        self.report_button.clicked.connect(self.on_generate_report)
        header_layout.addWidget(self.report_button)

        layout.addLayout(header_layout)

        # Suche und Filter
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Name oder E-Mail suchen...")
        self.search_input.textChanged.connect(self.on_search)
        search_layout.addWidget(self.search_input)

        self.department_filter = QComboBox()
        self.department_filter.addItems(["Alle", "IT", "HR", "Finanzen", "Marketing"])
        self.department_filter.currentTextChanged.connect(self.on_filter)
        search_layout.addWidget(self.department_filter)

        self.valid_filter = QComboBox()
        self.valid_filter.addItems(["Alle", "Valid", "Invalid"])
        self.valid_filter.currentTextChanged.connect(self.on_filter)
        search_layout.addWidget(self.valid_filter)

        layout.addLayout(search_layout)

        # Tabelle
        self.table_view = QTableView()
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        layout.addWidget(self.table_view)

        # Statuslabel
        self.status_label = QLabel("Bereit")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Tabelle initial laden
        self.load_employees()

    def load_employees(self):
        employees = self.db_repo.get_all_employees()
        self.table_view.setModel(EmployeeTableModel(employees))

    def on_import_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "CSV-Datei auswählen", "", "CSV Files (*.csv)")
        if file_path:
            try:
                employees = import_csv(file_path)
                valid_count = 0
                invalid_count = 0
                for emp in employees:
                    validation_result = validate_employee(emp)
                    emp.is_valid = validation_result.is_valid
                    emp.errors = validation_result.errors
                    self.db_repo.add_employee(emp)
                    if emp.is_valid:
                        valid_count += 1
                    else:
                        invalid_count += 1
                self.load_employees()
                self.status_label.setText(f"Importiert: {len(employees)} Mitarbeiter ({valid_count} gültig, {invalid_count} ungültig)")
            except Exception as e:
                QMessageBox.critical(self, "Fehler", f"Fehler beim Import: {e}")

    def on_export_csv(self):
        employees = self.db_repo.get_all_employees()
        file_path, _ = QFileDialog.getSaveFileName(self, "CSV-Datei speichern", "", "CSV Files (*.csv)")
        if file_path:
            export_to_csv(employees, file_path)
            self.status_label.setText(f"Exportiert nach {file_path}")

    def on_export_json(self):
        employees = self.db_repo.get_all_employees()
        file_path, _ = QFileDialog.getSaveFileName(self, "JSON-Datei speichern", "", "JSON Files (*.json)")
        if file_path:
            export_to_json(employees, file_path)
            self.status_label.setText(f"Exportiert nach {file_path}")

    def on_generate_report(self):
        employees = self.db_repo.get_all_employees()
        file_path, _ = QFileDialog.getSaveFileName(self, "Validierungsbericht speichern", "", "JSON Files (*.json)")
        if file_path:
            generate_validation_report(employees, file_path)
            self.status_label.setText(f"Validierungsbericht generiert: {file_path}")

    def on_search(self, text: str):
        model = self.table_view.model()
        if model:
            for row in range(model.rowCount(None)):
                name = model.data(model.index(row, 0), Qt.ItemDataRole.DisplayRole)
                email = model.data(model.index(row, 1), Qt.ItemDataRole.DisplayRole)
                if text.lower() not in name.lower() and text.lower() not in email.lower():
                    self.table_view.setRowHidden(row, True)
                else:
                    self.table_view.setRowHidden(row, False)

    def on_filter(self):
        model = self.table_view.model()
        if model:
            department = self.department_filter.currentText()
            valid_status = self.valid_filter.currentText()

            for row in range(model.rowCount(None)):
                dept = model.data(model.index(row, 3), Qt.ItemDataRole.DisplayRole)
                is_valid = model.data(model.index(row, 5), Qt.ItemDataRole.DisplayRole) == "Ja"

                dept_match = department == "Alle" or dept == department
                valid_match = valid_status == "Alle" or (valid_status == "Valid" and is_valid) or (valid_status == "Invalid" and not is_valid)

                if not (dept_match and valid_match):
                    self.table_view.setRowHidden(row, True)
                else:
                    self.table_view.setRowHidden(row, False)

    def closeEvent(self, event):
        self.db_repo.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
