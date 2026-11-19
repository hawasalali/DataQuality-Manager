import csv
import logging
from pathlib import Path
from typing import List, Union
from models.employee import Employee
from models.validation_result import ValidationResult

logger = logging.getLogger(__name__)


class CsvExporter:
    """Ein Exporter für Mitarbeiterdaten und Validierungsfehler in CSV-Dateien."""

    def __init__(self, default_filename: str = "employees_export.csv"):
        self.default_filename = default_filename

    def export(
        self,
        employees: List[Employee],
        filename: Union[str, Path, None] = None,
        directory: Union[str, Path, None] = None,
    ) -> bool:
        """Exportiert eine Liste von Mitarbeitern in eine CSV-Datei."""
        try:
            filepath = self._resolve_path(filename or self.default_filename, directory)
            fieldnames = [
                "id",
                "first_name",
                "last_name",
                "email",
                "phone",
                "department",
                "birth_date",
                "hire_date",
                "status",
            ]

            with open(filepath, mode="w", newline="", encoding="utf-8") as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                writer.writeheader()
                for employee in employees:
                    writer.writerow(
                        {
                            "id": employee.id if employee.id is not None else "",
                            "first_name": employee.first_name,
                            "last_name": employee.last_name,
                            "email": employee.email,
                            "phone": employee.phone,
                            "department": employee.department,
                            "birth_date": employee.birth_date,
                            "hire_date": employee.hire_date,
                            "status": employee.status,
                        }
                    )

            logger.info(f"Mitarbeiter erfolgreich exportiert: {filepath}")
            return True

        except Exception as e:
            logger.error(f"Fehler beim Exportieren der Mitarbeiter: {e}")
            return False

    def export_validation_errors(
        self,
        results: List[ValidationResult],
        filename: Union[str, Path] = "validation_errors.csv",
        directory: Union[str, Path, None] = None,
    ) -> bool:
        """Exportiert Validierungsfehler in eine CSV-Datei."""
        try:
            filepath = self._resolve_path(filename, directory)
            fieldnames = ["employee_id", "field", "severity", "message", "actual_value"]

            with open(filepath, mode="w", newline="", encoding="utf-8") as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                writer.writeheader()
                for res in results:
                    writer.writerow(
                        {
                            "employee_id": res.employee_id if res.employee_id is not None else "",
                            "field": res.field,
                            "severity": str(res.severity),
                            "message": res.message,
                            "actual_value": res.actual_value or "",
                        }
                    )

            logger.info(f"Validierungsfehler erfolgreich exportiert: {filepath}")
            return True

        except Exception as e:
            logger.error(f"Fehler beim Exportieren der Validierungsfehler: {e}")
            return False

    def _resolve_path(
        self, filename: Union[str, Path], directory: Union[str, Path, None]
    ) -> Path:
        path = Path(filename)
        if directory is not None:
            dir_path = Path(directory)
            dir_path.mkdir(parents=True, exist_ok=True)
            path = dir_path / path.name
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
        return path
