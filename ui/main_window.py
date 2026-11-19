from datetime import datetime
from pathlib import Path
from typing import Optional, List
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QMessageBox,
    QFileDialog,
)
from PyQt6.QtGui import QIcon, QAction

from ui.dashboard import Dashboard
from ui.employee_view import EmployeeView
from ui.import_view import ImportView
from ui.validation_view import ValidationView

from database.connection import DatabaseConnection
from database.employee_repository import EmployeeRepository
from models.employee import Employee
from models.validation_result import ValidationResult
from services.csv_importer import CsvImporter
from services.csv_exporter import CsvExporter
from services.data_validator import DataValidator
from services.report_generator import ReportGenerator
from services.statistics_service import StatisticsService


class MainWindow(QMainWindow):
    """Das Hauptfenster der Anwendung 'DataQuality Manager'."""

    def __init__(
        self,
        db: Optional[DatabaseConnection] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)

        self.setWindowTitle("DataQuality Manager")
        self.setWindowIcon(QIcon.fromTheme("applications-development"))
        self.resize(1400, 900)

        if db is None:
            self.db = DatabaseConnection("data/dataquality.db")
            self.db.create_tables("database/schema.sql")
        else:
            self.db = db

        self.repository = EmployeeRepository(self.db)
        self.importer = CsvImporter()
        self.exporter = CsvExporter()
        self.validator = DataValidator()
        self.report_generator = ReportGenerator()
        self.stats_service = StatisticsService()

        self.employees: List[Employee] = []
        self.validation_results: List[ValidationResult] = []

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.tab_widget.setTabShape(QTabWidget.TabShape.Rounded)
        self.tab_widget.setUsesScrollButtons(True)

        self.dashboard = Dashboard(show_duplicates=True)
        self.employee_view = EmployeeView()
        self.import_view = ImportView()
        self.validation_view = ValidationView()

        self.tab_widget.addTab(
            self.dashboard, QIcon.fromTheme("view-statistics"), "Dashboard"
        )
        self.tab_widget.addTab(
            self.employee_view, QIcon.fromTheme("x-office-contact"), "Mitarbeiter"
        )
        self.tab_widget.addTab(
            self.import_view, QIcon.fromTheme("document-import"), "Import"
        )
        self.tab_widget.addTab(
            self.validation_view, QIcon.fromTheme("dialog-information"), "Validierung"
        )

        main_layout.addWidget(self.tab_widget)

        self._create_menu_bar()
        self._connect_signals()
        self.refresh_all_views()

    def _create_menu_bar(self) -> None:
        """Erstellt die Menüleiste für Export-Funktionen."""
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("Datei")

        export_csv_action = QAction("Mitarbeiter als CSV exportieren...", self)
        export_csv_action.triggered.connect(self._on_export_csv)
        file_menu.addAction(export_csv_action)

        export_valid_csv_action = QAction(
            "Nur gültige Mitarbeiter als CSV exportieren...", self
        )
        export_valid_csv_action.triggered.connect(
            lambda: self._on_export_csv(only_valid=True)
        )
        file_menu.addAction(export_valid_csv_action)

        export_json_action = QAction("JSON-Qualitätsbericht exportieren...", self)
        export_json_action.triggered.connect(self._on_export_json_report)
        file_menu.addAction(export_json_action)

        export_errors_action = QAction("Validierungsfehler als CSV exportieren...", self)
        export_errors_action.triggered.connect(self._on_export_validation_errors)
        file_menu.addAction(export_errors_action)

    def _connect_signals(self) -> None:
        """Verbindet die Signale der Views mit den Anwendungs-Slots."""
        self.employee_view.employee_added.connect(self._on_employee_added)
        self.employee_view.employee_edited.connect(self._on_employee_edited)
        self.employee_view.employee_deleted.connect(self._on_employee_deleted)
        self.import_view.import_confirmed.connect(self._on_import_confirmed)

    def refresh_all_views(self) -> None:
        """Lädt Daten aus der Datenbank, validiert sie und aktualisiert alle Views."""
        try:
            self.employees = self.repository.get_all()
            self.validation_results = self.validator.validate_all(self.employees)

            for emp in self.employees:
                if emp.id is not None:
                    self.repository.update(emp)

            self.employee_view.set_employees(self.employees)
            self.validation_view.set_validation_results(
                self.validation_results, self.employees
            )

            stats = self.stats_service.get_statistics_as_dict(employees=self.employees)
            self.dashboard.update_stats(
                total=stats["total"],
                valid=stats["valid"],
                warnings=stats["warnings"],
                errors=stats["errors"],
                duplicates=stats["duplicates"],
            )
        except Exception as e:
            self.show_error(f"Fehler beim Laden der Daten:\n{e}")

    def _on_import_confirmed(self, file_path: str) -> None:
        """Importiert die CSV-Datei, validiert Datensätze und speichert sie in SQLite."""
        try:
            imported_employees = self.importer.import_employees(file_path)
            if not imported_employees:
                self.show_error("Keine gültigen Datensätze zum Importieren gefunden.")
                return

            combined = self.employees + imported_employees
            self.validator.validate_all(combined)

            imported_count = 0
            rejected_count = 0

            for emp in imported_employees:
                emp_id = self.repository.add(emp)
                emp.id = emp_id
                if emp.status == "INVALID":
                    rejected_count += 1
                else:
                    imported_count += 1

            all_results = self.validator.validate_all(self.repository.get_all())
            imported_ids = {e.id for e in imported_employees}
            for res in all_results:
                if res.employee_id in imported_ids:
                    self.repository.add_validation_result(res)

            self.repository.add_import_history(
                filename=Path(file_path).name,
                import_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                records_imported=imported_count,
                records_rejected=rejected_count,
            )

            self.refresh_all_views()
            self.tab_widget.setCurrentWidget(self.employee_view)
            self.show_info(
                f"Import abgeschlossen:\n"
                f"- Gesamt verarbeitet: {len(imported_employees)}\n"
                f"- Gültig / Warnung: {imported_count}\n"
                f"- Mit Fehlern: {rejected_count}"
            )
        except Exception as e:
            self.show_error(f"Fehler beim Importieren:\n{e}")

    def _on_employee_added(self, employee: Employee) -> None:
        """Speichert einen neu angelegten Mitarbeiter in der Datenbank."""
        try:
            self.repository.add(employee)
            self.refresh_all_views()
            self.show_info(
                f"Neuer Mitarbeiter '{employee.first_name} {employee.last_name}' hinzugefügt."
            )
        except Exception as e:
            self.show_error(f"Fehler beim Hinzufügen:\n{e}")

    def _on_employee_edited(self, employee: Employee) -> None:
        """Aktualisiert einen bearbeiteten Mitarbeiter in der Datenbank."""
        try:
            self.repository.update(employee)
            self.refresh_all_views()
            self.show_info(
                f"Mitarbeiter '{employee.first_name} {employee.last_name}' aktualisiert."
            )
        except Exception as e:
            self.show_error(f"Fehler beim Aktualisieren:\n{e}")

    def _on_employee_deleted(self, employee_id: int) -> None:
        """Löscht einen Mitarbeiter aus der Datenbank."""
        try:
            self.repository.delete(employee_id)
            self.refresh_all_views()
            self.show_info("Mitarbeiter wurde gelöscht.")
        except Exception as e:
            self.show_error(f"Fehler beim Löschen:\n{e}")

    def _on_export_csv(self, only_valid: bool = False) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Mitarbeiter als CSV speichern",
            "reports/employees_export.csv",
            "CSV-Dateien (*.csv)",
        )
        if not file_path:
            return

        data = (
            [e for e in self.employees if e.status == "VALID"]
            if only_valid
            else self.employees
        )
        if self.exporter.export(data, filename=file_path):
            self.show_info(f"CSV-Export erfolgreich gespeichert unter:\n{file_path}")
        else:
            self.show_error("CSV-Export ist fehlgeschlagen.")

    def _on_export_json_report(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "JSON-Qualitätsbericht speichern",
            "reports/quality_report.json",
            "JSON-Dateien (*.json)",
        )
        if not file_path:
            return

        if self.report_generator.generate_from_employees(
            self.employees, self.validation_results, filename=file_path, directory=None
        )    def _on_export_validation_errors(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Validierungsfehler als CSV speichern",
            "reports/validation_errors.csv",
            "CSV-Dateien (*.csv)",
        )
        if not file_path:
            return

        if self.exporter.export_validation_errors(
            self.validation_results, filename=file_path
        ):
            self.show_info(f"Validierungsfehler gespeichert unter:\n{file_path}")
        else:
            self.show_error("Fehler beim Exportieren der Validierungsfehler.")

    def show_error(self, message: str) -> None:
        QMessageBox.critical(self, "Fehler", message)

    def show_info(self, message: str) -> None:
        QMessageBox.information(self, "Information", message)

    def closeEvent(self, event) -> None:
        """Schließt die Datenbankverbindung sauber beim Beenden."""
        if self.db:
            self.db.close()
        super().closeEvent(event)
