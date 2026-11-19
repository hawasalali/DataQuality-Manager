import copy
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from models.employee import Employee
from models.validation_result import ValidationResult, Severity

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

            if warning_details:
                report["details"]["warnings"] = warning_details
            if error_details:
                report["details"]["errors"] = error_details

            filepath = Path(filename or self.default_filename)
            if directory is not None:
                dir_path = Path(directory)
                dir_path.mkdir(parents=True, exist_ok=True)
                filepath = dir_path / filepath.name
            else:
                filepath.parent.mkdir(parents=True, exist_ok=True)

            with open(filepath, "w", encoding="utf-8") as file:
                json.dump(report, file, indent=4, ensure_ascii=False)

            logger.info(f"Qualitätsbericht erfolgreich generiert: {filepath}")
            return True

        except Exception as e:
            logger.error(f"Fehler beim Generieren des Berichts: {e}")
            return False

    def _create_report_template(self) -> Dict[str, Any]:
        """Erstellt eine tiefe Kopie der Berichtsvorlage."""
        return copy.deepcopy(self.report_template)

    def generate_from_employees(
        self,
        employees: List[Employee],
        results: List[ValidationResult],
        filename: Optional[Union[str, Path]] = None,
        directory: Optional[Union[str, Path]] = "reports",
    ) -> bool:
        """Generiert einen JSON-Bericht direkt aus Mitarbeiter- und Validierungsergebnis-Listen."""
        total = len(employees)
        valid = sum(1 for emp in employees if emp.status == "VALID")
        warnings_list = [r.to_dict() for r in results if r.severity == Severity.WARNING]
        errors_list = [r.to_dict() for r in results if r.severity == Severity.ERROR]
        duplicates = sum(
            1
            for r in results
            if r.severity == Severity.WARNING and "doppelt" in r.message.lower()
        )

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
            return self.generate(
                total=validation_results.get("total_records", 0),
                valid=validation_results.get("valid_records", 0),
                warnings=validation_results.get("warnings", 0),
                errors=validation_results.get("errors", 0),
                duplicate_records=validation_results.get("duplicate_records", 0),
                warning_details=validation_results.get("warning_details", []),
                error_details=validation_results.get("error_details", []),
                filename=filename,
                directory=directory,
            )
        except Exception as e:
            logger.error(f"Fehler beim Generieren des Berichts aus Validierungsergebnissen: {e}")
            return False
