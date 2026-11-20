from typing import List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QIcon
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from models.employee import Employee


class _SortableIdItem(QTableWidgetItem):
    """Sortierbares Table-Item für numerische IDs."""

    def __lt__(self, other: "QTableWidgetItem") -> bool:
        try:
            return int(self.data(Qt.ItemDataRole.UserRole) or 0) < int(
                other.data(Qt.ItemDataRole.UserRole) or 0
            )
        except (TypeError, ValueError):
            return super().__lt__(other)


class EmployeeFormDialog(QDialog):
    """Dialog zum Hinzufügen oder Bearbeiten eines Mitarbeiters."""

    def __init__(
        self, employee: Optional[Employee] = None, parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.employee = employee or Employee()
        self.setWindowTitle(
            "Mitarbeiter bearbeiten"
            if self.employee.id is not None
            else "Neuer Mitarbeiter"
        )
        self.setMinimumWidth(380)

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

        form.addRow("Vorname*:", self.first_name_input)
        form.addRow("Nachname*:", self.last_name_input)
        form.addRow("E-Mail*:", self.email_input)
        form.addRow("Telefon:", self.phone_input)
        form.addRow("Abteilung:", self.department_combo)
        form.addRow("Geburtsdatum:", self.birth_date_input)
        form.addRow("Einstellungsdatum:", self.hire_date_input)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
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


class EmployeeView(QWidget):
    """Eine View für die Anzeige, Suche, Filterung und Verwaltung von Mitarbeiterdaten."""

    employee_selected = pyqtSignal(int)
    employee_added = pyqtSignal(Employee)
    employee_edited = pyqtSignal(Employee)
    employee_deleted = pyqtSignal(int)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._all_employees: List[Employee] = []
        self._employees_by_id: dict[int, Employee] = {}

        self.setWindowTitle("Mitarbeiterverwaltung")
        self.setWindowIcon(QIcon.fromTheme("view-list-details"))

        main_layout = QVBoxLayout()

        # Such- und Filterleiste
        filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Suche nach Name oder E-Mail...")
        self.department_filter = QComboBox()
        self.department_filter.addItem("Alle Abteilungen")
        self.status_filter = QComboBox()
        self.status_filter.addItems(["Alle Status", "VALID", "WARNING", "INVALID"])

        filter_layout.addWidget(QLabel("Suche:"))
        filter_layout.addWidget(self.search_input)
        filter_layout.addWidget(QLabel("Abteilung:"))
        filter_layout.addWidget(self.department_filter)
        filter_layout.addWidget(QLabel("Status:"))
        filter_layout.addWidget(self.status_filter)

        # Aktions-Buttons
        button_layout = QHBoxLayout()
        self.add_button = self._create_button("Neu", "list-add")
        self.edit_button = self._create_button("Bearbeiten", "document-edit")
        self.delete_button = self._create_button("Löschen", "edit-delete")

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch()

        # Tabelle
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        main_layout.addLayout(filter_layout)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.table)
        self.setLayout(main_layout)

        self._setup_table()
        self._connect_signals()

    def _create_button(self, text: str, icon_name: str) -> QPushButton:
        button = QPushButton(text)
        button.setIcon(QIcon.fromTheme(icon_name))
        button.setToolTip(f"{text} (Klicken für {text.lower()})")
        return button

    def _connect_signals(self) -> None:
        self.add_button.clicked.connect(self._on_add_clicked)
        self.edit_button.clicked.connect(self._on_edit_clicked)
        self.delete_button.clicked.connect(self._on_delete_clicked)
        self.table.cellDoubleClicked.connect(lambda *_: self._on_edit_clicked())
        if self.table.selectionModel() is not None:
            self.table.selectionModel().selectionChanged.connect(
                self._on_table_selection_changed
            )
        self.search_input.textChanged.connect(self._apply_filters)
        self.department_filter.currentTextChanged.connect(self._apply_filters)
        self.status_filter.currentTextChanged.connect(self._apply_filters)

    def _setup_table(self) -> None:
        columns = [
            "ID",
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
        self.table.setColumnHidden(0, True)

    def get_selected_employee_id(self) -> Optional[int]:
        """Gibt die ID des aktuell ausgewählten Mitarbeiters zurück."""
        selected_rows = (
            self.table.selectionModel().selectedRows()
            if self.table.selectionModel()
            else []
        )
        if not selected_rows:
            return None
        row_idx = selected_rows[0].row()
        id_item = self.table.item(row_idx, 0)
        if id_item is None:
            return None
        raw_id = id_item.data(Qt.ItemDataRole.UserRole)
        if raw_id is None:
            return None
        parsed = int(raw_id)
        return parsed if parsed > 0 else None

    def get_selected_employee(self) -> Optional[Employee]:
        """Gibt das aktuell ausgewählte Employee-Objekt zurück."""
        emp_id = self.get_selected_employee_id()
        if emp_id is None:
            return None
        return self._employees_by_id.get(emp_id)

    def _on_add_clicked(self) -> None:
        dialog = EmployeeFormDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.employee_added.emit(dialog.get_employee())

    def _on_edit_clicked(self) -> None:
        emp = self.get_selected_employee()
        if emp is not None:
            dialog = EmployeeFormDialog(employee=emp, parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.employee_edited.emit(dialog.get_employee())
        else:
            QMessageBox.information(
                self,
                "Keine Auswahl",
                "Bitte wählen Sie einen Mitarbeiter aus der Liste aus.",
            )

    def _on_delete_clicked(self) -> None:
        employee_id = self.get_selected_employee_id()
        if employee_id is not None:
            reply = QMessageBox.question(
                self,
                "Mitarbeiter löschen",
                "Möchten Sie diesen Mitarbeiter wirklich löschen?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.employee_deleted.emit(employee_id)
        else:
            QMessageBox.information(
                self,
                "Keine Auswahl",
                "Bitte wählen Sie einen Mitarbeiter aus der Liste aus.",
            )

    def _on_table_selection_changed(self) -> None:
        employee_id = self.get_selected_employee_id()
        if employee_id is not None:
            self.employee_selected.emit(employee_id)

    def set_employees(self, employees: List[Employee]) -> None:
        """Speichert die Mitarbeiterliste, aktualisiert Abteilungsfilter und füllt die Tabelle."""
        self._all_employees = list(employees or [])
        self._employees_by_id = {
            emp.id: emp for emp in self._all_employees if emp.id is not None
        }

        current_dept = self.department_filter.currentText()
        departments = sorted(
            {
                (e.department or "").strip()
                for e in self._all_employees
                if (e.department or "").strip()
            }
        )
        self.department_filter.blockSignals(True)
        self.department_filter.clear()
        self.department_filter.addItem("Alle Abteilungen")
        self.department_filter.addItems(departments)
        idx = self.department_filter.findText(current_dept)
        if idx >= 0:
            self.department_filter.setCurrentIndex(idx)
        self.department_filter.blockSignals(False)

        self._apply_filters()

    def _apply_filters(self) -> None:
        search_text = self.search_input.text().strip().lower()
        selected_dept = self.department_filter.currentText()
        selected_status = self.status_filter.currentText()

        filtered: List[Employee] = []
        for emp in self._all_employees:
            full_name = f"{emp.first_name or ''} {emp.last_name or ''}".lower()
            email = (emp.email or "").lower()
            if (
                search_text
                and search_text not in full_name
                and search_text not in email
            ):
                continue
            if (
                selected_dept != "Alle Abteilungen"
                and (emp.department or "") != selected_dept
            ):
                continue
            if (
                selected_status != "Alle Status"
                and (emp.status or "").upper() != selected_status
            ):
                continue
            filtered.append(emp)

        self._render_table(filtered)

    def _render_table(self, employees: List[Employee]) -> None:
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(employees))

        status_colors = {
            "VALID": QColor("#d4edda"),
            "WARNING": QColor("#fff3cd"),
            "INVALID": QColor("#f8d7da"),
            "ERROR": QColor("#f8d7da"),
        }

        for row_idx, emp in enumerate(employees):
            emp_id_val = emp.id if emp.id is not None else -(row_idx + 1)
            id_item = _SortableIdItem(
                str(emp.id if emp.id is not None else "")
            )
            id_item.setData(Qt.ItemDataRole.UserRole, emp_id_val)

            status_text = (emp.status or "VALID").upper()
            values = [
                id_item,
                QTableWidgetItem(emp.first_name or ""),
                QTableWidgetItem(emp.last_name or ""),
                QTableWidgetItem(emp.email or ""),
                QTableWidgetItem(emp.phone or ""),
                QTableWidgetItem(emp.department or ""),
                QTableWidgetItem(emp.hire_date or ""),
                QTableWidgetItem(status_text),
            ]

            row_bg = status_colors.get(status_text)
            for col_idx, item in enumerate(values):
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if row_bg is not None and col_idx == len(values) - 1:
                    item.setBackground(row_bg)
                    item.setForeground(QColor("#111111"))
                self.table.setItem(row_idx, col_idx, item)

        self.table.setSortingEnabled(True)