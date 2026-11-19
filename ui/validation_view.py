---

### 2. `ui/validation_view.py` (Komplett)
Auch hier einfach alles in `ui/validation_view.py` markieren (`Strg + A`), ersetzen und speichern (`Strg + S`):

```python
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QAbstractItemView,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QBrush, QColor
from typing import List, Optional, Dict
from models.employee import Employee
from models.validation_result import ValidationResult


class ValidationView(QWidget):
    """Eine View zur Anzeige von Validierungsergebnissen für Mitarbeiterdaten."""

    validation_selected = pyqtSignal(int)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.setWindowTitle("Validierungsergebnisse")
        self.setWindowIcon(QIcon.fromTheme("dialog-information"))

        layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)

        layout.addWidget(self.table)
        self.setLayout(layout)

        self._setup_table()
        self._connect_signals()
        self._clear_table()

    def _connect_signals(self) -> None:
        self.table.selectionModel().selectionChanged.connect(
            self._on_validation_selected
        )

    def _setup_table(self) -> None:
        columns = [
            "Employee ID",
            "Betroffener Datensatz",
            "Feld",
            "Nachricht",
            "Schweregrad",
            "Erwartetes Format",
            "Tatsächlicher Wert",
        ]
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.setColumnHidden(0, True)

    def _on_validation_selected(self) -> None:
        selected_id = self.get_selected_validation_id()
        if selected_id is not None:
            self.validation_selected.emit(selected_id)

    def set_validation_results(
        self,
        validation_results: List[ValidationResult],
        employees: Optional[List[Employee]] = None,
    ) -> None:
        """Setzt die Validierungsergebnisse inklusive Mitarbeiternamen in die Tabelle."""
        if not validation_results:
            self._clear_table()
            return

        emp_lookup: Dict[int, str] = {}
        if employees:
            for emp in employees:
                if emp.id is not None:
                    full_name = f"{emp.first_name} {emp.last_name}".strip()
                    emp_lookup[emp.id] = full_name or emp.email or f"ID #{emp.id}"

        self.table.setRowCount(len(validation_results))

        for row, result in enumerate(validation_results):
            emp_id_str = str(result.employee_id) if result.employee_id is not None else ""
            self.table.setItem(row, 0, QTableWidgetItem(emp_id_str))

            record_name = (
                emp_lookup.get(result.employee_id, f"Datensatz #{result.employee_id}")
                if result.employee_id is not None
                else "Unbekannter Datensatz"
            )
            self.table.setItem(row, 1, QTableWidgetItem(record_name))
            self.table.setItem(row, 2, QTableWidgetItem(result.field))

            msg_item = QTableWidgetItem(result.message)
            msg_item.setToolTip(result.message)
            self.table.setItem(row, 3, msg_item)

            sev_name = str(result.severity).upper()
            severity_item = QTableWidgetItem(sev_name)
            if sev_name == "ERROR":
                severity_item.setBackground(QBrush(QColor("#f8d7da")))
            elif sev_name == "WARNING":
                severity_item.setBackground(QBrush(QColor("#fff3cd")))
            else:
                severity_item.setBackground(QBrush(QColor("#d4edda")))
            self.table.setItem(row, 4, severity_item)

            self.table.setItem(row, 5, QTableWidgetItem(result.expected_format or ""))

            actual_value_item = QTableWidgetItem(result.actual_value or "")
            actual_value_item.setToolTip(result.actual_value or "")
            self.table.setItem(row, 6, actual_value_item)

    def _clear_table(self) -> None:
        self.table.setRowCount(1)
        item = QTableWidgetItem("Keine Validierungsergebnisse verfügbar.")
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        self.table.setItem(0, 1, item)
        for col in range(self.table.columnCount()):
            if col != 1:
                self.table.setItem(0, col, QTableWidgetItem(""))

    def get_selected_validation_id(self) -> Optional[int]:
        selected_row = self.table.currentRow()
        if selected_row >= 0 and self.table.item(selected_row, 0):
            text = self.table.item(selected_row, 0).text()
            return int(text) if text.isdigit() else None
        return None

    def clear_selection(self) -> None:
        self.table.clearSelection()

    def show_error(self, message: str) -> None:
        QMessageBox.critical(self, "Fehler", message)

    def show_info(self, message: str) -> None:
        QMessageBox.information(self, "Information", message)
