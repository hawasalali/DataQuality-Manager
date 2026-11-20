from typing import Any, Dict, List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from models.employee import Employee
from services.csv_importer import CsvImporter


class ImportView(QWidget):
    """Eine View für den Import und die Vorschau von Mitarbeiterdaten aus CSV-Dateien."""

    import_requested = pyqtSignal(str)
    import_confirmed = pyqtSignal(str)

    PREVIEW_LIMIT: int = 50

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.current_file_path: Optional[str] = None
        self.preview_employees: List[Employee] = []
        self.importer = CsvImporter()

        self.setWindowTitle("Mitarbeiter-Import")
        self.setWindowIcon(QIcon.fromTheme("document-import"))

        layout = QVBoxLayout()

        top_bar = QHBoxLayout()
        self.load_button = self._create_button("CSV laden", "document-open")
        self.file_label = QLabel("Keine Datei ausgewählt")
        self.import_button = self._create_button("Importieren", "go-down")
        self.import_button.setEnabled(False)

        top_bar.addWidget(self.load_button)
        top_bar.addWidget(self.file_label, stretch=1)
        top_bar.addWidget(self.import_button)

        self.table = QTableWidget()
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.verticalHeader().setVisible(False)

        layout.addLayout(top_bar)
        layout.addWidget(self.table)
        self.setLayout(layout)

        self._setup_table()
        self._connect_signals()
        self._clear_table()

    def _create_button(self, text: str, icon_name: str) -> QPushButton:
        button = QPushButton(text)
        button.setIcon(QIcon.fromTheme(icon_name))
        button.setToolTip(f"Klicken, um {text.lower()} auszuführen")
        return button

    def _connect_signals(self) -> None:
        self.load_button.clicked.connect(self._on_load_csv_clicked)
        self.import_button.clicked.connect(self._on_import_clicked)

    def _setup_table(self) -> None:
        columns = [
            "Vorname",
            "Nachname",
            "E-Mail",
            "Telefon",
            "Abteilung",
            "Einstellungsdatum",
            "Status",
        ]
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)

    @staticmethod
    def _read_only_item(text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        return item

    def _clear_table(self) -> None:
        self.current_file_path = None
        self.preview_employees = []
        self.import_button.setEnabled(False)
        self.file_label.setText("Keine Datei ausgewählt")
        self.table.clearSpans()
        self.table.setRowCount(1)

        item = QTableWidgetItem(
            "Klicken Sie auf 'CSV laden', um eine Datei auszuwählen."
        )
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        self.table.setItem(0, 0, item)
        self.table.setSpan(0, 0, 1, self.table.columnCount())

    def _on_load_csv_clicked(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "CSV-Datei auswählen",
            "",
            "CSV-Dateien (*.csv);;Alle Dateien (*)",
        )
        if file_path:
            self.import_requested.emit(file_path)
            self._load_csv_preview(file_path)

    def _load_csv_preview(self, file_path: str) -> None:
        """Lädt eine Vorschau der CSV-Datei über den CsvImporter in die Tabelle."""
        headers, rows, error = self.importer.load_rows(file_path)
        if error:
            QMessageBox.critical(
                self,
                "Fehler beim Laden der CSV-Datei",
                f"Die Datei konnte nicht geladen werden:\n{error}",
            )
            self._clear_table()
            return

        missing = self.importer.validate_headers(headers)
        if missing:
            QMessageBox.critical(
                self,
                "Fehlende Pflichtspalten",
                f"Die CSV-Datei konnte nicht geladen werden:\nFehlende Pflichtspalten: {', '.join(missing)}",
            )
            self._clear_table()
            return

        preview_rows = rows[: self.PREVIEW_LIMIT]
        employees: List[Employee] = []
        for row in preview_rows:
            lower_row = {k.strip().lower(): v for k, v in row.items()}
            employees.append(
                Employee(
                    first_name=lower_row.get("first_name", ""),
                    last_name=lower_row.get("last_name", ""),
                    email=lower_row.get("email", ""),
                    phone=lower_row.get("phone", ""),
                    department=lower_row.get("department", ""),
                    birth_date=lower_row.get("birth_date", ""),
                    hire_date=lower_row.get("hire_date", ""),
                )
            )

        self.current_file_path = file_path
        self.file_label.setText(file_path)
        self.set_preview_data(employees)
        self.import_button.setEnabled(bool(employees))

    def _on_import_clicked(self) -> None:
        if not self.current_file_path:
            QMessageBox.information(
                self,
                "Keine Daten",
                "Bitte laden Sie zuerst eine CSV-Datei.",
            )
            return

        reply = QMessageBox.question(
            self,
            "Import bestätigen",
            f"Möchten Sie {len(self.preview_employees)} Datensätze wirklich importieren?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.import_confirmed.emit(self.current_file_path)

    def set_preview_data(self, employees: List[Employee]) -> None:
        """Setzt die Vorschau der Mitarbeiterdaten in die Tabelle."""
        self.preview_employees = list(employees or [])
        if not self.preview_employees:
            self._clear_table()
            return

        self.table.clearSpans()
        self.table.setRowCount(len(self.preview_employees))
        for row, employee in enumerate(self.preview_employees):
            self.table.setItem(row, 0, self._read_only_item(employee.first_name or ""))
            self.table.setItem(row, 1, self._read_only_item(employee.last_name or ""))
            self.table.setItem(row, 2, self._read_only_item(employee.email or ""))
            self.table.setItem(row, 3, self._read_only_item(employee.phone or ""))
            self.table.setItem(row, 4, self._read_only_item(employee.department or ""))
            self.table.setItem(row, 5, self._read_only_item(employee.hire_date or ""))
            self.table.setItem(row, 6, self._read_only_item("Vorschau"))

    def get_import_data(self) -> List[Dict[str, Any]]:
        """Gibt die aktuellen Vorschaudaten als Liste von Dictionaries zurück."""
        return [emp.to_dict() for emp in self.preview_employees]