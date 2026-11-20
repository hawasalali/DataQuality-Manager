import csv
import logging
from pathlib import Path
from typing import List, Optional, Union

from models.employee import Employee
from models.validation_result import ValidationResult

logger = logging.getLogger(__name__)


class CsvExporter:
    """Ein Exporter für Mitarbeiterdaten und Validierungsfehler in CSV-Dateien."""

    def __init__(
        self, default_filename: str = "employees_export.csv", delimiter: str = ","
    ):
        self.default_filename = default_filename
        self.delimiter = delimiter

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
                writer = csv.DictWriter(
                    csv_file, fieldnames=fieldnames, delimiter=self.delimiter
                )
                writer.writeheader()
                for employee in employees or []:
                    writer.writerow(
                        {
                            "id": employee.id if employee.id is not None else "",
                            "first_name": employee.first_name or "",
                            "last_name": employee.last_name or "",
                            "email": employee.email or "",
                            "phone": employee.phone or "",
                            "department": employee.department or "",
                            "birth_date": employee.birth_date or "",
                            "hire_date": employee.hire_date or "",
                            "status": (employee.status or "VALID").upper(),
                        }
                    )

            logger.info("Mitarbeiter erfolgreich exportiert: %s", filepath)
            return True

        except Exception as e:
            logger.error("Fehler beim Exportieren der Mitarbeiter: %s", e)
            return False

    def export_validation_errors(
        self,
        results: List[ValidationResult],
        filename: Union[str, Path] = "validation_errors.csv",
        directory: Union[str, Path, None] = None,
    ) -> bool:
        """Exportiert Validierungsfehler und -warnungen in eine CSV-Datei."""
        try:
            filepath = self._resolve_path(filename, directory)
            fieldnames = [
                "employee_id",
                "field",
                "severity",
                "message",
                "actual_value",
            ]

            with open(filepath, mode="w", newline="", encoding="utf-8") as csv_file:
                writer = csv.DictWriter(
                    csv_file, fieldnames=fieldnames, delimiter=self.delimiter
                )
                writer.writeheader()
                for res in results or []:
                    if getattr(res, "is_valid", False):
                        continue
                    raw_severity = getattr(res, "severity", "")
                    severity_val = getattr(raw_severity, "value", str(raw_severity))
                    writer.writerow(
                        {
                            "employee_id": (
                                res.employee_id if res.employee_id is not None else ""
                            ),
                            "field": res.field or "",
                            "severity": severity_val,
                            "message": res.message or "",
                            "actual_value": (
                                res.actual_value if res.actual_value is not None else ""
                            ),
                        }
                    )

            logger.info("Validierungsfehler erfolgreich exportiert: %s", filepath)
            return True

        except Exception as e:
            logger.error("Fehler beim Exportieren der Validierungsfehler: %s", e)
            return False

    def _resolve_path(
        self, filename: Union[str, Path], directory: Optional[Union[str, Path]]
    ) -> Path:
        path = Path(filename)
        if directory is not None:
            dir_path = Path(directory)
            dir_path.mkdir(parents=True, exist_ok=True)
            path = dir_path / path.name
        elif str(path.parent) not in ("", "."):
            path.parent.mkdir(parents=True, exist_ok=True)
        return path