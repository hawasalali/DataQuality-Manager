import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor, QIcon
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from database.connection import DatabaseConnection
from database.employee_repository import EmployeeRepository
from models.employee import Employee
from models.validation_result import ValidationResult
from services.csv_exporter import CsvExporter
from services.csv_importer import CsvImporter
from services.data_validator import DataValidator
from services.report_generator import ReportGenerator
from services.statistics_service import StatisticsService


PROFESSIONAL_QSS = """
QMainWindow {
    background-color: #181c24;
    color: #e6edf3;
}
QWidget {
    font-family: "Segoe UI", "DejaVu Sans", sans-serif;
    font-size: 13px;
    color: #e6edf3;
}
QFrame#TopBar {
    background-color: #202632;
    border: 1px solid #2f3747;
    border-radius: 8px;
}
QLabel#SectionTitle {
    font-size: 15px;
    font-weight: 600;
    color: #f0f6fc;
    padding: 2px 0px;
}
QLineEdit, QComboBox {
    background-color: #12161f;
    border: 1px solid #343d4f;
    border-radius: 6px;
    padding: 6px 10px;
    color: #e6edf3;
    selection-background-color: #2f81f7;
}
QLineEdit:focus, QComboBox:focus {
    border: 1px solid #58a6ff;
}
QPushButton {
    background-color: #262e3d;
    border: 1px solid #3b465c;
    border-radius: 6px;
    padding: 6px 12px;
    font-weight: 500;
    color: #e6edf3;
}
QPushButton:hover {
    background-color: #323d52;
    border-color: #58a6ff;
}
QPushButton:pressed {
    background-color: #1c222e;
}
QPushButton#PrimaryButton {
    background-color: #238636;
    border: 1px solid #2ea043;
    color: #ffffff;
    font-weight: 600;
}
QPushButton#PrimaryButton:hover {
    background-color: #2ea043;
}
QPushButton#DangerButton {
    background-color: #da3633;
    border: 1px solid #f85149;
    color: #ffffff;
    font-weight: 600;
}
QPushButton#DangerButton:hover {
    background-color: #e5534b;
}
QTableWidget {
    background-color: #12161f;
    alternate-background-color: #171c27;
    gridline-color: #262e3d;
    border: 1px solid #2f3747;
    border-radius: 8px;
    selection-background-color: #1f6feb;
    selection-color: #ffffff;
}
QHeaderView::section {
    background-color: #202632;
    color: #c9d1d9;
    font-weight: 600;
    padding: 7px 8px;
    border: none;
    border-right: 1px solid #2f3747;
    border-bottom: 1px solid #343d4f;
}
QSplitter::handle {
    background-color: #2f3747;
    height: 3px;
    margin: 2px 20px;
    border-radius: 1px;
}
QStatusBar {
    background-color: #202632;
    color: #8b949e;
    border-top: 1px solid #2f3747;
}
"""


class EmployeeEditDialog(QDialog):
    """Professioneller Dialog zum Anlegen oder Bearbeiten eines Mitarbeiters."""

    def __init__(
        self, employee: Optional[Employee] = None, parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.employee = employee or Employee()
        self.setWindowTitle(
            "Edit Employee" if self.employee.id is not None else "New Employee"
        )
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(8)

        self.first_name_input = QLineEdit(self.employee.first_name or "")
        self.last_name_input = QLineEdit(self.employee.last_name or "")
        self.email_input = QLineEdit(self.employee.email or "")
        self.phone_input = QLineEdit(self.employee.phone or "")

        self.department_combo = QComboBox()
        self.department_combo.setEditable(True)
        departments = ["", "IT", "HR", "Sales", "Finance", "Marketing", "Operations"]
        current_dept = self.employee.department or ""
        if current_dept and current_dept not in departments:
            departments.insert(1, current_dept)
        self.department_combo.addItems(departments)
        self.department_combo.setCurrentText(current_dept)

        self.birth_date_input = QLineEdit(self.employee.birth_date or "")
        self.birth_date_input.setPlaceholderText("YYYY-MM-DD")

        self.hire_date_input = QLineEdit(self.employee.hire_date or "")
        self.hire_date_input.setPlaceholderText("YYYY-MM-DD")

        form.addRow("First Name *:", self.first_name_input)
        form.addRow("Last Name *:", self.last_name_input)
        form.addRow("Email *:", self.email_input)
        form.addRow("Phone:", self.phone_input)
        form.addRow("Department:", self.department_combo)
        form.addRow("Birth Date:", self.birth_date_input)
        form.addRow("Hire Date:", self.hire_date_input)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Save
        )
        cancel_btn = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        save_btn = buttons.button(QDialogButtonBox.StandardButton.Save)
        if cancel_btn:
            cancel_btn.setText("Cancel")
        if save_btn:
            save_btn.setText("Save")

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_employee(self) -> Employee:
        return Employee(
            id=self.employee.id,
            first_name=self.first_name_input.text().strip(),
            last_name=self.last_name_input.text().strip(),
            email=self.email_input.text().strip(),
            phone=self.phone_input.text().strip(),
            department=self.department_combo.currentText().strip(),
            birth_date=self.birth_date_input.text().strip(),
            hire_date=self.hire_date_input.text().strip(),
            status=self.employee.status or "VALID",
        )


class MainWindow(QMainWindow):
    """Hauptfenster im Single-View-Design mit CSV-, XML- und JSON-Unterstützung[cite: 6]."""

    DB_COLUMNS = [
        "ID",
        "Vorname",
        "Nachname",
        "E-Mail",
        "Telefon",
        "Abteilung",
        "Geburtsdatum",
        "Status",
    ]

    PREVIEW_COLUMNS = [
        "Zeile",
        "Vorname",
        "Nachname",
        "E-Mail",
        "Telefon",
        "Abteilung",
        "Geburtsdatum",
        "Status",
        "Fehlermeldung",
    ]

    def __init__(
        self,
        db: Optional[DatabaseConnection] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)

        self.setWindowTitle("DataQuality Manager")
        self.setWindowIcon(QIcon.fromTheme("applications-development"))
        self.resize(1420, 900)
        self.setStyleSheet(PROFESSIONAL_QSS)

        if db is None:
            self.db = DatabaseConnection(str(PROJECT_ROOT / "data" / "dataquality.db"))
            self.db.create_tables(str(PROJECT_ROOT / "database" / "schema.sql"))
        else:
            self.db = db

        self.repository = EmployeeRepository(self.db)
        self.importer = CsvImporter()
        self.exporter = CsvExporter()
        self.validator = DataValidator()
        self.report_generator = ReportGenerator()
        self.stats_service = StatisticsService()

        self.employees: List[Employee] = []
        self._employees_by_id: Dict[int, Employee] = {}
        self.validation_results: List[ValidationResult] = []
        self.preview_employees: List[Employee] = []
        self.current_source_path: Optional[str] = None

        self._build_ui()
        self._connect_signals()
        self.refresh_all_views()

    def _create_badge(
        self, text: str, bg_color: str, fg_color: str = "#ffffff"
    ) -> QLabel:
        badge = QLabel(text)
        badge.setStyleSheet(
            f"""
            QLabel {{
                background-color: {bg_color};
                color: {fg_color};
                border-radius: 6px;
                padding: 5px 11px;
                font-weight: 600;
            }}
            """
        )
        return badge

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(12, 12, 12, 8)
        root_layout.setSpacing(10)

        # 1. Obere Statistik- & Import-Historien-Leiste[cite: 6]
        top_frame = QFrame()
        top_frame.setObjectName("TopBar")
        top_layout = QHBoxLayout(top_frame)
        top_layout.setContentsMargins(10, 8, 10, 8)
        top_layout.setSpacing(8)

        self.db_total_badge = self._create_badge("DB Gesamt: 0", "#2f3b52")
        self.csv_checked_badge = self._create_badge("Quelle Geprüft: 0", "#37435c")
        self.valid_badge = self._create_badge("Gültig: 0", "#238636")
        self.warning_badge = self._create_badge("Warnungen: 0", "#b07219")
        self.error_badge = self._create_badge("Fehler: 0", "#b62324")

        self.history_combo = QComboBox()
        self.history_combo.setMinimumWidth(360)
        self.history_combo.addItem("Import-Historie: Keine Einträge")

        top_layout.addWidget(self.db_total_badge)
        top_layout.addWidget(self.csv_checked_badge)
        top_layout.addWidget(self.valid_badge)
        top_layout.addWidget(self.warning_badge)
        top_layout.addWidget(self.error_badge)
        top_layout.addStretch()
        top_layout.addWidget(self.history_combo)

        root_layout.addWidget(top_frame)

        splitter = QSplitter(Qt.Orientation.Vertical)

        # 2. Mittlerer Bereich: SQLite Datenbank - Mitarbeiter[cite: 6]
        db_section = QWidget()
        db_layout = QVBoxLayout(db_section)
        db_layout.setContentsMargins(0, 4, 0, 4)
        db_layout.setSpacing(6)

        db_title = QLabel("SQLite Datenbank - Mitarbeiter")
        db_title.setObjectName("SectionTitle")
        db_layout.addWidget(db_title)

        db_toolbar = QHBoxLayout()
        db_toolbar.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Suche nach Name oder E-Mail...")
        self.search_input.setMaximumWidth(250)

        self.department_filter = QComboBox()
        self.department_filter.addItem("Alle")

        self.delete_db_btn = QPushButton("Delete")
        self.delete_db_btn.setObjectName("DangerButton")
        self.edit_db_btn = QPushButton("Edit")
        self.add_db_btn = QPushButton("+ Neu")
        self.export_csv_btn = QPushButton("CSV exportieren")
        self.export_xml_btn = QPushButton("XML exportieren")
        self.export_json_btn = QPushButton("JSON-Report exportieren")

        db_toolbar.addWidget(self.search_input)
        db_toolbar.addWidget(QLabel("Abteilung:"))
        db_toolbar.addWidget(self.department_filter)
        db_toolbar.addStretch()
        db_toolbar.addWidget(self.delete_db_btn)
        db_toolbar.addWidget(self.edit_db_btn)
        db_toolbar.addWidget(self.add_db_btn)
        db_toolbar.addWidget(self.export_csv_btn)
        db_toolbar.addWidget(self.export_xml_btn)
        db_toolbar.addWidget(self.export_json_btn)
        db_layout.addLayout(db_toolbar)

        self.db_table = QTableWidget()
        self.db_table.setColumnCount(len(self.DB_COLUMNS))
        self.db_table.setHorizontalHeaderLabels(self.DB_COLUMNS)
        self.db_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.db_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.db_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.db_table.setAlternatingRowColors(True)
        self.db_table.setSortingEnabled(True)
        self.db_table.verticalHeader().setVisible(False)
        self.db_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        db_layout.addWidget(self.db_table)

        splitter.addWidget(db_section)

        # 3. Unterer Bereich: CSV / XML Import-Vorschau & Validierung[cite: 6]
        import_section = QWidget()
        import_layout = QVBoxLayout(import_section)
        import_layout.setContentsMargins(0, 4, 0, 0)
        import_layout.setSpacing(6)

        import_title = QLabel("CSV / XML Import-Vorschau & Validierung")
        import_title.setObjectName("SectionTitle")
        import_layout.addWidget(import_title)

        import_toolbar = QHBoxLayout()
        import_toolbar.setSpacing(8)

        self.load_csv_btn = QPushButton("CSV laden")
        self.load_xml_btn = QPushButton("XML laden")
        self.preview_file_label = QLabel("Keine Datei geladen")
        self.preview_file_label.setStyleSheet("color: #8b949e;")

        self.edit_preview_btn = QPushButton("Bearbeiten")
        self.delete_preview_btn = QPushButton("Löschen")
        self.commit_db_btn = QPushButton("In DB übernehmen")
        self.commit_db_btn.setObjectName("PrimaryButton")

        import_toolbar.addWidget(self.load_csv_btn)
        import_toolbar.addWidget(self.load_xml_btn)
        import_toolbar.addWidget(self.preview_file_label)
        import_toolbar.addStretch()
        import_toolbar.addWidget(self.edit_preview_btn)
        import_toolbar.addWidget(self.delete_preview_btn)
        import_toolbar.addWidget(self.commit_db_btn)
        import_layout.addLayout(import_toolbar)

        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(len(self.PREVIEW_COLUMNS))
        self.preview_table.setHorizontalHeaderLabels(self.PREVIEW_COLUMNS)
        self.preview_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.preview_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.preview_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.preview_table.setAlternatingRowColors(True)
        self.preview_table.verticalHeader().setVisible(False)
        self.preview_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        import_layout.addWidget(self.preview_table)

        splitter.addWidget(import_section)
        splitter.setSizes([460, 320])

        root_layout.addWidget(splitter)

        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        self.statusBar().showMessage("Bereit — CSV, XML, JSON und SQLite aktiv")

    def _connect_signals(self) -> None:
        self.search_input.textChanged.connect(self._render_db_table)
        self.department_filter.currentTextChanged.connect(self._render_db_table)

        self.add_db_btn.clicked.connect(self._on_add_employee)
        self.edit_db_btn.clicked.connect(self._on_edit_employee)
        self.delete_db_btn.clicked.connect(self._on_delete_employee)
        self.db_table.cellDoubleClicked.connect(lambda *_: self._on_edit_employee())

        self.export_csv_btn.clicked.connect(self._on_export_csv)
        self.export_xml_btn.clicked.connect(self._on_export_xml)
        self.export_json_btn.clicked.connect(self._on_export_json_report)

        self.load_csv_btn.clicked.connect(self._on_load_csv)
        self.load_xml_btn.clicked.connect(self._on_load_xml)
        self.edit_preview_btn.clicked.connect(self._on_edit_preview_row)
        self.delete_preview_btn.clicked.connect(self._on_delete_preview_row)
        self.commit_db_btn.clicked.connect(self._on_commit_preview_to_db)

    def refresh_all_views(self) -> None:
        """Lädt Mitarbeiter aus SQLite, validiert sie und aktualisiert alle Bereiche."""
        try:
            self.employees = self.repository.get_all()
            self._employees_by_id = {
                emp.id: emp for emp in self.employees if emp.id is not None
            }
            self.validation_results = self.validator.validate_all(self.employees)

            for emp in self.employees:
                if emp.id is not None:
                    self.repository.update(emp)

            self._refresh_department_filter()
            self._render_db_table()
            self._refresh_history_combo()
            self._update_top_stats()
            self.statusBar().showMessage(
                f"SQLite synchronisiert: {len(self.employees)} Mitarbeiter geladen"
            )
        except Exception as e:
            self.show_error(f"Fehler beim Laden der Daten:\n{e}")

    def _refresh_department_filter(self) -> None:
        current = self.department_filter.currentText()
        departments = sorted(
            {
                (emp.department or "").strip()
                for emp in self.employees
                if (emp.department or "").strip()
            }
        )
        self.department_filter.blockSignals(True)
        self.department_filter.clear()
        self.department_filter.addItem("Alle")
        self.department_filter.addItems(departments)
        idx = self.department_filter.findText(current)
        if idx >= 0:
            self.department_filter.setCurrentIndex(idx)
        self.department_filter.blockSignals(False)

    def _refresh_history_combo(self) -> None:
        self.history_combo.clear()
        history_getter = getattr(self.repository, "get_import_history", None)
        entries = history_getter() if callable(history_getter) else []
        if not entries:
            self.history_combo.addItem("Import-Historie: Keine Einträge")
            return

        for item in entries:
            if isinstance(item, dict):
                fname = item.get("filename", "import.csv")
                date_str = item.get("import_date", "")
                imp_cnt = item.get("records_imported", 0)
                rej_cnt = item.get("records_rejected", 0)
                self.history_combo.addItem(
                    f"Import-Historie: {fname} ({date_str} | {imp_cnt} importiert, {rej_cnt} abgelehnt)"
                )
            else:
                self.history_combo.addItem(f"Import-Historie: {item}")

    def _update_top_stats(self) -> None:
        stats = self.stats_service.get_statistics_as_dict(employees=self.employees)
        db_total = stats.get("total", len(self.employees))
        checked_cnt = len(self.preview_employees)

        if self.preview_employees:
            p_stats = self.stats_service.get_statistics_as_dict(
                employees=self.preview_employees
            )
            valid_cnt = p_stats.get("valid", 0)
            warn_cnt = p_stats.get("warnings", 0)
            err_cnt = p_stats.get("errors", 0)
        else:
            valid_cnt = stats.get("valid", 0)
            warn_cnt = stats.get("warnings", 0)
            err_cnt = stats.get("errors", 0)

        self.db_total_badge.setText(f"DB Gesamt: {db_total}")
        self.csv_checked_badge.setText(f"Quelle Geprüft: {checked_cnt}")
        self.valid_badge.setText(f"Gültig: {valid_cnt}")
        self.warning_badge.setText(f"Warnungen: {warn_cnt}")
        self.error_badge.setText(f"Fehler: {err_cnt}")

    def _make_item(self, text: str, bg: Optional[str] = None) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        if bg:
            item.setBackground(QBrush(QColor(bg)))
            item.setForeground(QBrush(QColor("#C01A1A")))
        return item

    def _render_db_table(self) -> None:
        query = self.search_input.text().strip().lower()
        dept_filter = self.department_filter.currentText()

        filtered = []
        for emp in self.employees:
            full_name = f"{emp.first_name or ''} {emp.last_name or ''}".lower()
            email = (emp.email or "").lower()
            dept = (emp.department or "").strip()
            if query and query not in full_name and query not in email:
                continue
            if dept_filter != "Alle" and dept != dept_filter:
                continue
            filtered.append(emp)

        self.db_table.setSortingEnabled(False)
        self.db_table.setRowCount(len(filtered))

        for row, emp in enumerate(filtered):
            emp_id_text = str(emp.id if emp.id is not None else "")
            id_item = self._make_item(emp_id_text)
            id_item.setData(Qt.ItemDataRole.UserRole, emp.id)

            status = (emp.status or "VALID").upper()
            status_bg = (
                "#28873f"
                if status == "VALID"
                else "#fff3cd"
                if status == "WARNING"
                else "#f8d7da"
            )

            row_items = [
                id_item,
                self._make_item(emp.first_name or ""),
                self._make_item(emp.last_name or ""),
                self._make_item(emp.email or ""),
                self._make_item(emp.phone or ""),
                self._make_item(emp.department or ""),
                self._make_item(emp.birth_date or ""),
                self._make_item(status, bg=status_bg),
            ]
            for col, item in enumerate(row_items):
                self.db_table.setItem(row, col, item)

        self.db_table.setSortingEnabled(True)

    def _get_selected_db_employee(self) -> Optional[Employee]:
        row = self.db_table.currentRow()
        if row < 0:
            return None
        id_item = self.db_table.item(row, 0)
        if not id_item:
            return None
        emp_id = id_item.data(Qt.ItemDataRole.UserRole)
        return self._employees_by_id.get(emp_id)

    def _on_add_employee(self) -> None:
        dialog = EmployeeEditDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            emp = dialog.get_employee()
            self.repository.add(emp)
            self.refresh_all_views()

    def _on_edit_employee(self) -> None:
        emp = self._get_selected_db_employee()
        if not emp:
            self.show_info("Bitte zuerst einen Mitarbeiter in der Tabelle auswählen.")
            return
        dialog = EmployeeEditDialog(employee=emp, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated = dialog.get_employee()
            self.repository.update(updated)
            self.refresh_all_views()

    def _on_delete_employee(self) -> None:
        emp = self._get_selected_db_employee()
        if not emp or emp.id is None:
            self.show_info("Bitte zuerst einen Mitarbeiter in der Tabelle auswählen.")
            return
        reply = QMessageBox.question(
            self,
            "Löschen bestätigen",
            f"Mitarbeiter '{emp.first_name} {emp.last_name}' wirklich löschen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.repository.delete(emp.id)
            self.refresh_all_views()

    def _on_load_csv(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "CSV-Datei laden",
            str(PROJECT_ROOT),
            "CSV-Dateien (*.csv);;Alle Dateien (*)",
        )
        if not file_path:
            return

        imported = self.importer.import_employees(file_path)
        if not imported:
            self.show_error(
                "Keine gültigen Datensätze geladen. Prüfen Sie Spaltennamen (first_name, last_name, email) und Dateiinhalt."
            )
            return

        self.current_source_path = file_path
        self.preview_file_label.setText(f"CSV: {Path(file_path).name}")
        self.preview_employees = imported
        self._revalidate_preview()

    def _parse_employees_from_xml(self, xml_path: str) -> List[Employee]:
        """Liest <employee>-Einträge aus einer XML-Datei ein."""
        tree = ET.parse(xml_path)
        root = tree.getroot()

        records = root.findall(".//employee")
        if not records and root.tag.lower() == "employee":
            records = [root]

        def _text(node: ET.Element, *names: str) -> str:
            for name in names:
                child = node.find(name)
                if child is not None and child.text:
                    return child.text.strip()
            return ""

        employees: List[Employee] = []
        for elem in records:
            employees.append(
                Employee(
                    first_name=_text(elem, "first_name", "vorname"),
                    last_name=_text(elem, "last_name", "nachname"),
                    email=_text(elem, "email", "e-mail"),
                    phone=_text(elem, "phone", "telefon"),
                    department=_text(elem, "department", "abteilung"),
                    birth_date=_text(elem, "birth_date", "geburtsdatum"),
                    hire_date=_text(elem, "hire_date", "einstellungsdatum"),
                )
            )
        return employees

    def _on_load_xml(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "XML-Datei laden",
            str(PROJECT_ROOT),
            "XML-Dateien (*.xml);;Alle Dateien (*)",
        )
        if not file_path:
            return

        try:
            imported = self._parse_employees_from_xml(file_path)
        except Exception as e:
            self.show_error(f"Fehler beim Parsen der XML-Datei:\n{e}")
            return

        if not imported:
            self.show_error("In der XML-Datei wurden keine <employee>-Datensätze gefunden.")
            return

        self.current_source_path = file_path
        self.preview_file_label.setText(f"XML: {Path(file_path).name}")
        self.preview_employees = imported
        self._revalidate_preview()

    def _revalidate_preview(self) -> None:
        combined = list(self.employees) + list(self.preview_employees)
        self.validator.validate_all(combined)
        self._render_preview_table()
        self._update_top_stats()
        self.statusBar().showMessage(
            f"Vorschau validiert: {len(self.preview_employees)} Datensätze geprüft"
        )

    def _render_preview_table(self) -> None:
        self.preview_table.setRowCount(len(self.preview_employees))
        for idx, emp in enumerate(self.preview_employees):
            status = (emp.status or "VALID").upper()
            bg = (
                "#d4edda"
                if status == "VALID"
                else "#fff3cd"
                if status == "WARNING"
                else "#f8d7da"
            )
            err_text = emp.error_message or "; ".join(emp.validation_errors or [])

            items = [
                self._make_item(str(idx + 1)),
                self._make_item(emp.first_name or ""),
                self._make_item(emp.last_name or ""),
                self._make_item(emp.email or ""),
                self._make_item(emp.phone or ""),
                self._make_item(emp.department or ""),
                self._make_item(emp.birth_date or ""),
                self._make_item(status, bg=bg),
                self._make_item(err_text),
            ]
            for col, item in enumerate(items):
                self.preview_table.setItem(idx, col, item)

    def _on_edit_preview_row(self) -> None:
        row = self.preview_table.currentRow()
        if row < 0 or row >= len(self.preview_employees):
            self.show_info("Bitte zuerst eine Vorschauzeile auswählen.")
            return
        dialog = EmployeeEditDialog(employee=self.preview_employees[row], parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.preview_employees[row] = dialog.get_employee()
            self._revalidate_preview()

    def _on_delete_preview_row(self) -> None:
        row = self.preview_table.currentRow()
        if row < 0 or row >= len(self.preview_employees):
            self.show_info("Bitte zuerst eine Vorschauzeile auswählen.")
            return
        del self.preview_employees[row]
        self._revalidate_preview()

    def _on_commit_preview_to_db(self) -> None:
        if not self.preview_employees:
            self.show_info("Keine Vorschaudaten zum Übernehmen vorhanden.")
            return

        imported_cnt = 0
        rejected_cnt = 0

        for emp in self.preview_employees:
            if (emp.status or "").upper() == "INVALID":
                rejected_cnt += 1
                continue
            emp.id = None
            new_id = self.repository.add(emp)
            emp.id = new_id
            imported_cnt += 1

        add_hist = getattr(self.repository, "add_import_history", None)
        if callable(add_hist):
            add_hist(
                filename=Path(self.current_source_path).name
                if self.current_source_path
                else "import.data",
                import_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                records_imported=imported_cnt,
                records_rejected=rejected_cnt,
            )

        self.preview_employees = []
        self.current_source_path = None
        self.preview_file_label.setText("Keine Datei geladen")
        self.refresh_all_views()
        self.show_info(
            f"Übernahme abgeschlossen:\n- Importiert: {imported_cnt}\n- Abgelehnt (INVALID): {rejected_cnt}"
        )

    def _on_export_csv(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Mitarbeiter als CSV exportieren",
            str(PROJECT_ROOT / "reports" / "employees_export.csv"),
            "CSV-Dateien (*.csv)",
        )
        if not file_path:
            return
        if self.exporter.export(self.employees, filename=file_path):
            self.show_info(f"CSV exportiert nach:\n{file_path}")
        else:
            self.show_error("CSV-Export fehlgeschlagen.")

    def _on_export_xml(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Mitarbeiter als XML exportieren",
            str(PROJECT_ROOT / "reports" / "employees_export.xml"),
            "XML-Dateien (*.xml)",
        )
        if not file_path:
            return

        try:
            root = ET.Element(
                "employees",
                attrib={
                    "exported_at": datetime.now().isoformat(),
                    "total": str(len(self.employees)),
                },
            )
            for emp in self.employees:
                emp_el = ET.SubElement(root, "employee")
                fields = {
                    "id": "" if emp.id is None else str(emp.id),
                    "first_name": emp.first_name or "",
                    "last_name": emp.last_name or "",
                    "email": emp.email or "",
                    "phone": emp.phone or "",
                    "department": emp.department or "",
                    "birth_date": emp.birth_date or "",
                    "hire_date": emp.hire_date or "",
                    "status": emp.status or "VALID",
                }
                for key, val in fields.items():
                    child = ET.SubElement(emp_el, key)
                    child.text = val

            ET.indent(root, space="  ")
            out_path = Path(file_path)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            ET.ElementTree(root).write(out_path, encoding="utf-8", xml_declaration=True)
            self.show_info(f"XML-Export erfolgreich gespeichert unter:\n{out_path}")
        except Exception as e:
            self.show_error(f"XML-Export fehlgeschlagen:\n{e}")

    def _on_export_json_report(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "JSON-Report exportieren",
            str(PROJECT_ROOT / "reports" / "quality_report.json"),
            "JSON-Dateien (*.json)",
        )
        if not file_path:
            return
        if self.report_generator.generate_from_employees(
            self.employees, self.validation_results, filename=file_path, directory=None
        ):
            self.show_info(f"JSON-Report gespeichert unter:\n{file_path}")
        else:
            self.show_error("JSON-Report konnte nicht erstellt werden.")

    def show_error(self, message: str) -> None:
        QMessageBox.critical(self, "Fehler", message)

    def show_info(self, message: str) -> None:
        QMessageBox.information(self, "Information", message)

    def closeEvent(self, event) -> None:
        if self.db:
            self.db.close()
        super().closeEvent(event)


if __name__ == "__main__":
    (PROJECT_ROOT / "data").mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "reports").mkdir(parents=True, exist_ok=True)
    app = QApplication(sys.argv)
    app.setApplicationName("DataQuality Manager")
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec())