import sys
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
from services.xml_service import XmlService

DARK_THEME_QSS = """
QMainWindow, QDialog { background-color: #181c24; color: #e6edf3; }
QWidget { font-family: "Segoe UI", "DejaVu Sans", sans-serif; font-size: 13px; color: #e6edf3; }
QFrame#TopBar { background-color: #202632; border: 1px solid #2f3747; border-radius: 8px; }
QLabel#SectionTitle { font-size: 15px; font-weight: 600; color: #f0f6fc; }
QLineEdit, QComboBox { background-color: #12161f; border: 1px solid #343d4f; border-radius: 6px; padding: 6px 10px; color: #e6edf3; }
QLineEdit:focus, QComboBox:focus { border: 1px solid #58a6ff; }
QPushButton { background-color: #262e3d; border: 1px solid #3b465c; border-radius: 6px; padding: 6px 12px; font-weight: 500; color: #e6edf3; }
QPushButton:hover { background-color: #323d52; border-color: #58a6ff; }
QPushButton#PrimaryButton { background-color: #238636; border: 1px solid #2ea043; color: #ffffff; font-weight: 600; }
QPushButton#DangerButton { background-color: #da3633; border: 1px solid #f85149; color: #ffffff; font-weight: 600; }
QTableWidget { background-color: #12161f; alternate-background-color: #171c27; gridline-color: #262e3d; border: 1px solid #2f3747; border-radius: 8px; selection-background-color: #1f6feb; selection-color: #ffffff; }
QHeaderView::section { background-color: #202632; color: #c9d1d9; font-weight: 600; padding: 7px 8px; border: none; border-right: 1px solid #2f3747; border-bottom: 1px solid #343d4f; }
QSplitter::handle { background-color: #2f3747; height: 3px; margin: 2px 20px; }
QStatusBar { background-color: #202632; color: #8b949e; border-top: 1px solid #2f3747; }
"""


class _SortableIdItem(QTableWidgetItem):
    """Sortierbares Tabellen-Item für numerische IDs."""

    def __lt__(self, other: "QTableWidgetItem") -> bool:
        try:
            return int(self.data(Qt.ItemDataRole.UserRole) or 0) < int(
                other.data(Qt.ItemDataRole.UserRole) or 0
            )
        except (TypeError, ValueError):
            return super().__lt__(other)


class EmployeeEditDialog(QDialog):
    """Dialog zum Anlegen oder Bearbeiten eines Mitarbeiters."""

    def __init__(
        self, employee: Optional[Employee] = None, parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.employee = employee or Employee()
        self.setWindowTitle(
            "Edit Employee" if self.employee.id is not None else "New Employee"
        )
        self.setStyleSheet(DARK_THEME_QSS)
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.first_name_input = QLineEdit(self.employee.first_name or "")
        self.last_name_input = QLineEdit(self.employee.last_name or "")
        self.email_input = QLineEdit(self.employee.email or "")
        self.phone_input = QLineEdit(self.employee.phone or "")

        self.department_combo = QComboBox()
        self.department_combo.setEditable(True)
        departments = ["", "IT", "HR", "Sales", "Finance", "Marketing", "Operations"]
        current_dept = (self.employee.department or "").strip()
        if current_dept and current_dept not in departments:
            departments.insert(1, current_dept)
        self.department_combo.addItems(departments)
        self.department_combo.setCurrentText(current_dept)

        self.birth_date_input = QLineEdit(self.employee.birth_date or "")
        self.birth_date_input.setPlaceholderText("YYYY-MM-DD")
        self.hire_date_input = QLineEdit(self.employee.hire_date or "")
        self.hire_date_input.setPlaceholderText("YYYY-MM-DD")

        for text, widget in [
            ("First Name *:", self.first_name_input),
            ("Last Name *:", self.last_name_input),
            ("Email *:", self.email_input),
            ("Phone:", self.phone_input),
            ("Department:", self.department_combo),
            ("Birth Date:", self.birth_date_input),
            ("Hire Date:", self.hire_date_input),
        ]:
            lbl = QLabel(text)
            lbl.setStyleSheet("color: #e6edf3; font-weight: 500;")
            form.addRow(lbl, widget)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Save
        )
        save_btn = buttons.button(QDialogButtonBox.StandardButton.Save)
        if save_btn:
            save_btn.setObjectName("PrimaryButton")
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
            status=(self.employee.status or "VALID").upper(),
        )


class MainWindow(QMainWindow):
    """Einheitliches Hauptfenster mit SQLite-Ansicht sowie CSV/XML-Vorschau & Validierung."""

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
        self, db: Optional[DatabaseConnection] = None, parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.setWindowTitle("DataQuality Manager")
        self.setWindowIcon(QIcon.fromTheme("applications-development"))
        self.resize(1420, 900)
        self.setStyleSheet(DARK_THEME_QSS)

        if db is None:
            self.db = DatabaseConnection(str(PROJECT_ROOT / "data" / "dataquality.db"))
            self.db.create_tables(str(PROJECT_ROOT / "database" / "schema.sql"))
        else:
            self.db = db

        self.repository = EmployeeRepository(self.db)
        self.importer = CsvImporter()
        self.exporter = CsvExporter()
        self.xml_service = XmlService()
        self.validator = DataValidator()
        self.report_generator = ReportGenerator()
        self.stats_service = StatisticsService()

        self.employees: List[Employee] = []
        self._employees_by_id: Dict[int, Employee] = {}
        self.validation_results: List[ValidationResult] = []
        self.preview_employees: List[Employee] = []
        self.preview_validation_results: List[ValidationResult] = []
        self.current_source_path: Optional[str] = None

        self._build_ui()
        self._connect_signals()
        self.refresh_all_views()

    def _badge(self, text: str, bg: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"background-color: {bg}; color: #ffffff; border-radius: 6px; padding: 5px 11px; font-weight: 600;"
        )
        return lbl

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(12, 12, 12, 8)
        root.setSpacing(10)

        top_frame = QFrame()
        top_frame.setObjectName("TopBar")
        top = QHBoxLayout(top_frame)
        self.db_total_badge = self._badge("DB Gesamt: 0", "#2f3b52")
        self.source_checked_badge = self._badge("Quelle Geprüft: 0", "#37435c")
        self.valid_badge = self._badge("Gültig: 0", "#238636")
        self.warning_badge = self._badge("Warnungen: 0", "#b07219")
        self.error_badge = self._badge("Fehler: 0", "#b62324")
        self.history_combo = QComboBox()
        self.history_combo.setMinimumWidth(350)
        self.history_combo.addItem("Import-Historie: Keine Einträge")

        for w in [
            self.db_total_badge,
            self.source_checked_badge,
            self.valid_badge,
            self.warning_badge,
            self.error_badge,
        ]:
            top.addWidget(w)
        top.addStretch()
        top.addWidget(self.history_combo)
        root.addWidget(top_frame)

        splitter = QSplitter(Qt.Orientation.Vertical)

        # Mitte: SQLite-Datenbank
        db_box = QWidget()
        db_layout = QVBoxLayout(db_box)
        db_title = QLabel("SQLite Datenbank - Mitarbeiter")
        db_title.setObjectName("SectionTitle")
        db_layout.addWidget(db_title)

        db_bar = QHBoxLayout()
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

        for w in [
            self.search_input,
            QLabel("Abteilung:"),
            self.department_filter,
        ]:
            db_bar.addWidget(w)
        db_bar.addStretch()
        for w in [
            self.delete_db_btn,
            self.edit_db_btn,
            self.add_db_btn,
            self.export_csv_btn,
            self.export_xml_btn,
            self.export_json_btn,
        ]:
            db_bar.addWidget(w)
        db_layout.addLayout(db_bar)

        self.db_table = self._make_table(self.DB_COLUMNS, sortable=True)
        db_layout.addWidget(self.db_table)
        splitter.addWidget(db_box)

        # Unten: CSV / XML Import-Vorschau & Validierung
        imp_box = QWidget()
        imp_layout = QVBoxLayout(imp_box)
        imp_title = QLabel("CSV / XML Import-Vorschau & Validierung")
        imp_title.setObjectName("SectionTitle")
        imp_layout.addWidget(imp_title)

        imp_bar = QHBoxLayout()
        self.load_csv_btn = QPushButton("CSV laden")
        self.load_xml_btn = QPushButton("XML laden")
        self.export_preview_json_btn = QPushButton("JSON-Report exportieren")
        self.preview_file_label = QLabel("Keine Datei geladen")
        self.preview_file_label.setStyleSheet("color: #8b949e;")
        self.edit_preview_btn = QPushButton("Bearbeiten")
        self.delete_preview_btn = QPushButton("Löschen")
        self.commit_db_btn = QPushButton("In DB übernehmen")
        self.commit_db_btn.setObjectName("PrimaryButton")

        for w in [
            self.load_csv_btn,
            self.load_xml_btn,
            self.export_preview_json_btn,
            self.preview_file_label,
        ]:
            imp_bar.addWidget(w)
        imp_bar.addStretch()
        for w in [self.edit_preview_btn, self.delete_preview_btn, self.commit_db_btn]:
            imp_bar.addWidget(w)
        imp_layout.addLayout(imp_bar)

        self.preview_table = self._make_table(self.PREVIEW_COLUMNS, sortable=False)
        imp_layout.addWidget(self.preview_table)
        splitter.addWidget(imp_box)
        splitter.setSizes([460, 320])
        root.addWidget(splitter)

        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Bereit — CSV, XML, JSON und SQLite aktiv")

    def _make_table(self, headers: List[str], sortable: bool) -> QTableWidget:
        tbl = QTableWidget()
        tbl.setColumnCount(len(headers))
        tbl.setHorizontalHeaderLabels(headers)
        tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tbl.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tbl.setAlternatingRowColors(True)
        tbl.setSortingEnabled(sortable)
        tbl.verticalHeader().setVisible(False)
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        return tbl

    def _connect_signals(self) -> None:
        self.search_input.textChanged.connect(self._render_db_table)
        self.department_filter.currentTextChanged.connect(self._render_db_table)
        self.add_db_btn.clicked.connect(self._on_add_employee)
        self.edit_db_btn.clicked.connect(self._on_edit_employee)
        self.delete_db_btn.clicked.connect(self._on_delete_employee)
        self.db_table.cellDoubleClicked.connect(lambda *_: self._on_edit_employee())
        self.export_csv_btn.clicked.connect(self._on_export_csv)
        self.export_xml_btn.clicked.connect(self._on_export_xml)
        self.export_json_btn.clicked.connect(self._on_export_db_json_report)
        self.load_csv_btn.clicked.connect(self._on_load_csv)
        self.load_xml_btn.clicked.connect(self._on_load_xml)
        self.export_preview_json_btn.clicked.connect(self._on_export_preview_json_report)
        self.edit_preview_btn.clicked.connect(self._on_edit_preview_row)
        self.delete_preview_btn.clicked.connect(self._on_delete_preview_row)
        self.commit_db_btn.clicked.connect(self._on_commit_preview_to_db)

    def _sync_validation_results_to_db(self) -> None:
        """Synchronisiert aktuelle Validierungsfehler/-warnungen mit validation_results."""
        clear_fn = getattr(self.repository, "clear_validation_results", None)
        add_fn = getattr(self.repository, "add_validation_result", None)
        if callable(clear_fn) and callable(add_fn):
            clear_fn()
            for res in self.validation_results:
                if not getattr(res, "is_valid", False):
                    add_fn(res)

    def refresh_all_views(self) -> None:
        try:
            self.employees = self.repository.get_all()
            self._employees_by_id = {
                e.id: e for e in self.employees if e.id is not None
            }
            self.validation_results = self.validator.validate_all(self.employees)
            for emp in self.employees:
                if emp.id is not None:
                    self.repository.update(emp)
            self._sync_validation_results_to_db()
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
        depts = sorted(
            {
                (e.department or "").strip()
                for e in self.employees
                if (e.department or "").strip()
            }
        )
        self.department_filter.blockSignals(True)
        self.department_filter.clear()
        self.department_filter.addItem("Alle")
        self.department_filter.addItems(depts)
        idx = self.department_filter.findText(current)
        if idx >= 0:
            self.department_filter.setCurrentIndex(idx)
        self.department_filter.blockSignals(False)

    def _refresh_history_combo(self) -> None:
        self.history_combo.clear()
        getter = getattr(self.repository, "get_import_history", None)
        entries = getter() if callable(getter) else []
        if not entries:
            self.history_combo.addItem("Import-Historie: Keine Einträge")
            return
        for item in entries:
            if isinstance(item, dict):
                self.history_combo.addItem(
                    f"Import-Historie: {item.get('filename', 'import.csv')} "
                    f"({item.get('import_date', '')} | {item.get('records_imported', 0)} importiert, "
                    f"{item.get('records_rejected', 0)} abgelehnt)"
                )
            else:
                self.history_combo.addItem(f"Import-Historie: {item}")

    def _update_top_stats(self) -> None:
        stats = self.stats_service.get_statistics_as_dict(employees=self.employees)
        src = (
            self.stats_service.get_statistics_as_dict(employees=self.preview_employees)
            if self.preview_employees
            else stats
        )
        self.db_total_badge.setText(f"DB Gesamt: {stats.get('total', len(self.employees))}")
        self.source_checked_badge.setText(
            f"Quelle Geprüft: {len(self.preview_employees)}"
        )
        self.valid_badge.setText(f"Gültig: {src.get('valid', 0)}")
        self.warning_badge.setText(f"Warnungen: {src.get('warnings', 0)}")
        self.error_badge.setText(f"Fehler: {src.get('errors', 0)}")

    def _status_style(self, status: str) -> tuple[str, str]:
        s = (status or "VALID").upper()
        if s == "VALID":
            return "#d4edda", "#155724"
        if s == "WARNING":
            return "#fff3cd", "#856404"
        return "#f8d7da", "#721c24"

    def _cell(
        self, text: str, bg: Optional[str] = None, fg: str = "#111111"
    ) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        if bg:
            item.setBackground(QBrush(QColor(bg)))
            item.setForeground(QBrush(QColor(fg)))
        return item

    def _render_db_table(self) -> None:
        q = self.search_input.text().strip().lower()
        dept = self.department_filter.currentText()
        rows = [
            e
            for e in self.employees
            if (
                not q
                or q in f"{e.first_name or ''} {e.last_name or ''}".lower()
                or q in (e.email or "").lower()
            )
            and (dept == "Alle" or (e.department or "").strip() == dept)
        ]
        self.db_table.setSortingEnabled(False)
        self.db_table.setRowCount(len(rows))
        for r, emp in enumerate(rows):
            id_item = _SortableIdItem(str(emp.id if emp.id is not None else ""))
            id_item.setData(Qt.ItemDataRole.UserRole, emp.id if emp.id is not None else 0)
            bg, fg = self._status_style(emp.status or "VALID")
            vals = [
                id_item,
                self._cell(emp.first_name or ""),
                self._cell(emp.last_name or ""),
                self._cell(emp.email or ""),
                self._cell(emp.phone or ""),
                self._cell(emp.department or ""),
                self._cell(emp.birth_date or ""),
                self._cell((emp.status or "VALID").upper(), bg, fg),
            ]
            for c, item in enumerate(vals):
                self.db_table.setItem(r, c, item)
        self.db_table.setSortingEnabled(True)

    def _selected_db_employee(self) -> Optional[Employee]:
        row = self.db_table.currentRow()
        if row < 0:
            return None
        id_item = self.db_table.item(row, 0)
        if id_item is None:
            return None
        emp_id = id_item.data(Qt.ItemDataRole.UserRole)
        return self._employees_by_id.get(emp_id) if emp_id is not None else None

    def _on_add_employee(self) -> None:
        dlg = EmployeeEditDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.repository.add(dlg.get_employee())
            self.refresh_all_views()

    def _on_edit_employee(self) -> None:
        emp = self._selected_db_employee()
        if not emp:
            self.show_info("Bitte zuerst einen Mitarbeiter auswählen.")
            return
        dlg = EmployeeEditDialog(employee=emp, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.repository.update(dlg.get_employee())
            self.refresh_all_views()

    def _on_delete_employee(self) -> None:
        emp = self._selected_db_employee()
        if not emp or emp.id is None:
            self.show_info("Bitte zuerst einen Mitarbeiter auswählen.")
            return
        if (
            QMessageBox.question(
                self, "Löschen", f"'{emp.first_name} {emp.last_name}' löschen?"
            )
            == QMessageBox.StandardButton.Yes
        ):
            self.repository.delete(emp.id)
            self.refresh_all_views()

    def _on_load_csv(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "CSV laden",
            str(PROJECT_ROOT),
            "CSV-Dateien (*.csv);;Alle (*)",
        )
        if not path:
            return
        rows = self.importer.import_employees(path)
        if not rows:
            self.show_error("Keine gültigen CSV-Datensätze gefunden.")
            return
        self.current_source_path = path
        self.preview_file_label.setText(f"CSV: {Path(path).name}")
        self.preview_employees = rows
        self._revalidate_preview()

    def _on_load_xml(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "XML laden",
            str(PROJECT_ROOT),
            "XML-Dateien (*.xml);;Alle (*)",
        )
        if not path:
            return
        try:
            rows = self.xml_service.load_employees(path)
        except Exception as e:
            self.show_error(f"Fehler beim XML-Import:\n{e}")
            return
        if not rows:
            self.show_error("Keine <employee>-Einträge in der XML-Datei gefunden.")
            return
        self.current_source_path = path
        self.preview_file_label.setText(f"XML: {Path(path).name}")
        self.preview_employees = rows
        self._revalidate_preview()

    def _revalidate_preview(self) -> None:
        combined = list(self.employees) + list(self.preview_employees)
        all_res = self.validator.validate_all(combined)
        preview_ids = {id(emp) for emp in self.preview_employees}
        self.preview_validation_results = [
            r
            for r in all_res
            if any(
                (r.employee_id is None and emp.id is None)
                and (emp.email or "").strip().lower()
                == (r.actual_value or "").strip().lower()
                for emp in self.preview_employees
            )
            or not self.employees
        ] if False else all_res
        _ = preview_ids

        self.preview_table.setRowCount(len(self.preview_employees))
        for i, emp in enumerate(self.preview_employees):
            bg, fg = self._status_style(emp.status or "VALID")
            err = emp.error_message or "; ".join(emp.validation_errors or [])
            items = [
                self._cell(str(i + 1)),
                self._cell(emp.first_name or ""),
                self._cell(emp.last_name or ""),
                self._cell(emp.email or ""),
                self._cell(emp.phone or ""),
                self._cell(emp.department or ""),
                self._cell(emp.birth_date or ""),
                self._cell((emp.status or "VALID").upper(), bg, fg),
                self._cell(err),
            ]
            for c, item in enumerate(items):
                self.preview_table.setItem(i, c, item)
        self._update_top_stats()

    def _on_edit_preview_row(self) -> None:
        row = self.preview_table.currentRow()
        if 0 <= row < len(self.preview_employees):
            dlg = EmployeeEditDialog(employee=self.preview_employees[row], parent=self)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                self.preview_employees[row] = dlg.get_employee()
                self._revalidate_preview()

    def _on_delete_preview_row(self) -> None:
        row = self.preview_table.currentRow()
        if 0 <= row < len(self.preview_employees):
            del self.preview_employees[row]
            self._revalidate_preview()

    def _on_commit_preview_to_db(self) -> None:
        if not self.preview_employees:
            self.show_info("Keine Vorschaudaten vorhanden.")
            return
        imported = rejected = 0
        for emp in self.preview_employees:
            if (emp.status or "").upper() == "INVALID":
                rejected += 1
                continue
            emp.id = None
            emp.id = self.repository.add(emp)
            imported += 1
        add_hist = getattr(self.repository, "add_import_history", None)
        if callable(add_hist):
            add_hist(
                filename=(
                    Path(self.current_source_path).name
                    if self.current_source_path
                    else "import.data"
                ),
                import_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                records_imported=imported,
                records_rejected=rejected,
            )
        self.preview_employees = []
        self.preview_validation_results = []
        self.current_source_path = None
        self.preview_file_label.setText("Keine Datei geladen")
        self.refresh_all_views()
        self.show_info(f"Importiert: {imported}\nAbgelehnt (INVALID): {rejected}")

    def _on_export_csv(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "CSV exportieren",
            str(PROJECT_ROOT / "reports" / "employees_export.csv"),
            "CSV (*.csv)",
        )
        if path:
            if self.exporter.export(self.employees, filename=path):
                self.show_info("CSV exportiert.")
            else:
                self.show_error("CSV-Export fehlgeschlagen.")

    def _on_export_xml(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "XML exportieren",
            str(PROJECT_ROOT / "reports" / "employees_export.xml"),
            "XML (*.xml)",
        )
        if path:
            if self.xml_service.export_employees(self.employees, filename=path):
                self.show_info("XML exportiert.")
            else:
                self.show_error("XML-Export fehlgeschlagen.")

    def _on_export_db_json_report(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "JSON-Report exportieren",
            str(PROJECT_ROOT / "reports" / "quality_report.json"),
            "JSON (*.json)",
        )
        if path:
            if self.report_generator.generate_from_employees(
                self.employees,
                self.validation_results,
                filename=path,
                directory=None,
            ):
                self.show_info("JSON-Report exportiert.")
            else:
                self.show_error("JSON-Report fehlgeschlagen.")

    def _on_export_preview_json_report(self) -> None:
        if not self.preview_employees:
            self._on_export_db_json_report()
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "JSON-Report (Vorschau) exportieren",
            str(PROJECT_ROOT / "reports" / "preview_quality_report.json"),
            "JSON (*.json)",
        )
        if path:
            preview_results = self.validator.validate_all(self.preview_employees)
            if self.report_generator.generate_from_employees(
                self.preview_employees,
                preview_results,
                filename=path,
                directory=None,
            ):
                self.show_info("Vorschau-JSON-Report exportiert.")
            else:
                self.show_error("JSON-Report fehlgeschlagen.")

    def show_error(self, msg: str) -> None:
        QMessageBox.critical(self, "Fehler", msg)

    def show_info(self, msg: str) -> None:
        QMessageBox.information(self, "Information", msg)

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