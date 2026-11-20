import copy
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from models.employee import Employee
from models.validation_result import Severity, ValidationResult

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Ein Generator für Qualitätsberichte im JSON-Format."""

    def __init__(self, default_filename: str = "quality_report.json"):
        self.default_filename = default_filename
        self.report_template: Dict[str, Any] = {
            "metadata": {
                "generated_at": None,
                "report_version": "1.0",
            },
            "summary": {
                "total_records": 0,
                "valid_records": 0,
                "warnings": 0,
                "errors": 0,
                "duplicate_records": 0,
            },
            "details": {
                "warnings": [],
                "errors": [],
            },
        }

    def _create_report_template(self) -> Dict[str, Any]:
        """Erstellt eine tiefe Kopie der Berichtsvorlage."""
        return copy.deepcopy(self.report_template)

    @staticmethod
    def _serialize_details(items: Optional[List[Any]]) -> List[Dict[str, Any]]:
        """Wandelt Detail-Einträge in serialisierbare Dictionaries um."""
        if not items:
            return []
        serialized: List[Dict[str, Any]] = []
        for item in items:
            if hasattr(item, "to_dict") and callable(item.to_dict):
                serialized.append(item.to_dict())
            elif isinstance(item, dict):
                serialized.append(item)
            else:
                serialized.append({"message": str(item)})
        return serialized

    def generate(
        self,
        total: int,
        valid: int,
        warnings: int = 0,
        errors: int = 0,
        duplicate_records: int = 0,
        warning_details: Optional[list] = None,
        error_details: Optional[list] = None,
        filename: Optional[Union[str, Path]] = None,
        directory: Optional[Union[str, Path]] = None,
    ) -> bool:
        """Generiert einen Qualitätsbericht im JSON-Format."""
        try:
            report = self._create_report_template()
            report["metadata"]["generated_at"] = datetime.now().isoformat()
            report["summary"].update(
                {
                    "total_records": total,
                    "valid_records": valid,
                    "warnings": warnings,
                    "errors": errors,
                    "duplicate_records": duplicate_records,
                }
            )

            report["details"]["warnings"] = self._serialize_details(warning_details)
            report["details"]["errors"] = self._serialize_details(error_details)

            filepath = Path(filename or self.default_filename)
            if directory is not None:
                dir_path = Path(directory)
                dir_path.mkdir(parents=True, exist_ok=True)
                filepath = dir_path / filepath.name
            elif str(filepath.parent) not in ("", "."):
                filepath.parent.mkdir(parents=True, exist_ok=True)

            with open(filepath, "w", encoding="utf-8") as file:
                json.dump(report, file, indent=4, ensure_ascii=False)

            logger.info("Qualitätsbericht erfolgreich generiert: %s", filepath)
            return True

        except Exception as e:
            logger.error("Fehler beim Generieren des Berichts: %s", e)
            return False

    def generate_from_employees(
        self,
        employees: List[Employee],
        results: List[ValidationResult],
        filename: Optional[Union[str, Path]] = None,
        directory: Optional[Union[str, Path]] = "reports",
    ) -> bool:
        """Generiert einen JSON-Bericht direkt aus Mitarbeiter- und Validierungsergebnis-Listen."""
        emp_list = employees or []
        res_list = results or []

        total = len(emp_list)
        valid = sum(1 for emp in emp_list if getattr(emp, "status", "") == "VALID")

        warnings_list: List[Dict[str, Any]] = []
        errors_list: List[Dict[str, Any]] = []
        duplicates = 0

        for r in res_list:
            if getattr(r, "is_valid", False):
                continue
            try:
                sev = Severity.from_value(r.severity)
            except Exception:
                sev = None

            msg_lower = str(getattr(r, "message", "") or "").lower()
            if sev == Severity.WARNING:
                warnings_list.append(r.to_dict() if hasattr(r, "to_dict") else {"message": str(r)})
                if "doppelt" in msg_lower or "duplicate" in msg_lower:
                    duplicates += 1
            elif sev == Severity.ERROR:
                errors_list.append(r.to_dict() if hasattr(r, "to_dict") else {"message": str(r)})

        return self.generate(
            total=total,
            valid=valid,
            warnings=len(warnings_list),
            errors=len(errors_list),
            duplicate_records=duplicates,
            warning_details=warnings_list,
            error_details=errors_list,
            filename=filename,
            directory=directory,
        )

    def generate_from_validation_results(
        self,
        validation_results: Dict[str, Any],
        filename: Optional[Union[str, Path]] = None,
        directory: Optional[Union[str, Path]] = None,
    ) -> bool:
        """Generiert einen Qualitätsbericht basierend auf einem Ergebnis-Dictionary."""
        try:
            data = validation_results or {}
            return self.generate(
                total=int(data.get("total_records", 0)),
                valid=int(data.get("valid_records", 0)),
                warnings=int(data.get("warnings", 0)),
                errors=int(data.get("errors", 0)),
                duplicate_records=int(data.get("duplicate_records", 0)),
                warning_details=data.get("warning_details", []),
                error_details=data.get("error_details", []),
                filename=filename,
                directory=directory,
            )
        except Exception as e:
            logger.error("Fehler beim Generieren des Berichts aus Validierungsergebnissen: %s", e)
            return False