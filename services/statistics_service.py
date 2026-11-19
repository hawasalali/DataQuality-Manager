from typing import List, Tuple, Optional, Dict, Any
from models.employee import Employee


class StatisticsService:
    """Ein Service zur Berechnung und optionalen Anzeige von Statistiken für Mitarbeiterdaten."""

    def __init__(
        self,
        total_label: Optional[Any] = None,
        valid_label: Optional[Any] = None,
        warning_label: Optional[Any] = None,
        error_label: Optional[Any] = None,
    ):
        self.total_label = total_label
        self.valid_label = valid_label
        self.warning_label = warning_label
        self.error_label = error_label

    def calculate(self, employees: List[Employee]) -> Tuple[int, int, int, int]:
        """Berechnet Statistiken (total, valid, warnings, errors) für eine Liste von Mitarbeitern."""
        if not employees:
            return 0, 0, 0, 0

        total = len(employees)
        valid = sum(1 for e in employees if (e.status or "").upper() == "VALID")
        warning = sum(1 for e in employees if (e.status or "").upper() == "WARNING")
        error = sum(1 for e in employees if (e.status or "").upper() in ("ERROR", "INVALID"))

        return total, valid, warning, error

    def calculate_from_validation_results(
        self, validation_results: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Berechnet Statistiken basierend auf einer Liste von Validierungsergebnissen."""
        if not validation_results:
            return {
                "total": 0,
                "valid": 0,
                "warnings": 0,
                "errors": 0,
                "duplicates": 0,
            }

        total = len(validation_results)
        valid = sum(1 for r in validation_results if r.get("is_valid", False))
        warnings = sum(
            1
            for r in validation_results
            if not r.get("is_valid", False)
            and str(r.get("severity", "")).upper() == "WARNING"
        )
        errors = sum(
            1
            for r in validation_results
            if not r.get("is_valid", False)
            and str(r.get("severity", "")).upper() == "ERROR"
        )
        duplicates = sum(
            1
            for r in validation_results
            if r.get("is_duplicate", False)
            or "doppelt" in str(r.get("message", "")).lower()
        )

        return {
            "total": total,
            "valid": valid,
            "warnings": warnings,
            "errors": errors,
            "duplicates": duplicates,
        }

    def update_stats(
        self,
        total: int,
        valid: int,
        warnings: int = 0,
        errors: int = 0,
        duplicates: int = 0,
    ) -> None:
        """Aktualisiert optional übergebene UI-Labels mit den neuen Werten."""
        if self.total_label:
            self.total_label.setText(f"Total: {total}")
        if self.valid_label:
            self.valid_label.setText(f"Valid: {valid}")
        if self.warning_label:
            self.warning_label.setText(f"Warnings: {warnings}")
        if self.error_label:
            self.error_label.setText(f"Errors: {errors}")

        if hasattr(self, "duplicate_label") and self.duplicate_label:
            self.duplicate_label.setText(f"Duplicates: {duplicates}")

    def get_statistics_as_dict(
        self,
        employees: Optional[List[Employee]] = None,
        validation_results: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, int]:
        """Gibt die Statistiken als Dictionary zurück."""
        if employees is not None:
            total, valid, warnings, errors = self.calculate(employees)
            duplicates = sum(
                1
                for e in employees
                if (e.status or "").upper() == "WARNING"
                and "doppelt" in (e.error_message or "").lower()
            )
            return {
                "total": total,
                "valid": valid,
                "warnings": warnings,
                "errors": errors,
                "duplicates": duplicates,
            }
        elif validation_results is not None:
            return self.calculate_from_validation_results(validation_results)
        else:
            return {
                "total": 0,
                "valid": 0,
                "warnings": 0,
                "errors": 0,
                "duplicates": 0,
            }
