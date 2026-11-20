from typing import Any, Dict, List, Optional, Tuple

from models.employee import Employee


class StatisticsService:
    """Ein Service zur Berechnung und optionalen Anzeige von Statistiken für Mitarbeiterdaten."""

    def __init__(
        self,
        total_label: Optional[Any] = None,
        valid_label: Optional[Any] = None,
        warning_label: Optional[Any] = None,
        error_label: Optional[Any] = None,
        duplicate_label: Optional[Any] = None,
    ):
        self.total_label = total_label
        self.valid_label = valid_label
        self.warning_label = warning_label
        self.error_label = error_label
        self.duplicate_label = duplicate_label

    @staticmethod
    def _extract_field(item: Any, key: str, default: Any = None) -> Any:
        """Liest ein Feld sicher aus einem Dictionary oder einem Objekt (z. B. ValidationResult)."""
        if isinstance(item, dict):
            return item.get(key, default)
        if key == "message" and hasattr(item, "message"):
            return getattr(item, "message", default)
        return getattr(item, key, default)

    def calculate(self, employees: List[Employee]) -> Tuple[int, int, int, int]:
        """Berechnet Statistiken (total, valid, warnings, errors) für eine Liste von Mitarbeitern."""
        if not employees:
            return 0, 0, 0, 0

        total = len(employees)
        valid = sum(1 for e in employees if (getattr(e, "status", "") or "").upper() == "VALID")
        warning = sum(1 for e in employees if (getattr(e, "status", "") or "").upper() == "WARNING")
        error = sum(
            1 for e in employees if (getattr(e, "status", "") or "").upper() in ("ERROR", "INVALID")
        )

        return total, valid, warning, error

    def calculate_from_validation_results(
        self, validation_results: List[Any]
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
        valid = sum(1 for r in validation_results if bool(self._extract_field(r, "is_valid", False)))
        warnings = sum(
            1
            for r in validation_results
            if not bool(self._extract_field(r, "is_valid", False))
            and str(
                getattr(self._extract_field(r, "severity", ""), "value", self._extract_field(r, "severity", ""))
            ).upper()
            == "WARNING"
        )
        errors = sum(
            1
            for r in validation_results
            if not bool(self._extract_field(r, "is_valid", False))
            and str(
                getattr(self._extract_field(r, "severity", ""), "value", self._extract_field(r, "severity", ""))
            ).upper()
            == "ERROR"
        )
        duplicates = sum(
            1
            for r in validation_results
            if bool(self._extract_field(r, "is_duplicate", False))
            or "doppelt" in str(self._extract_field(r, "message", "") or "").lower()
            or "duplicate" in str(self._extract_field(r, "message", "") or "").lower()
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
        if self.duplicate_label:
            self.duplicate_label.setText(f"Duplicates: {duplicates}")

    def get_statistics_as_dict(
        self,
        employees: Optional[List[Employee]] = None,
        validation_results: Optional[List[Any]] = None,
    ) -> Dict[str, int]:
        """Gibt die Statistiken als Dictionary zurück."""
        if employees is not None:
            total, valid, warnings, errors = self.calculate(employees)
            duplicates = sum(
                1
                for e in employees
                if "doppelt" in (getattr(e, "error_message", "") or "").lower()
                or any(
                    "doppelt" in str(msg).lower() or "duplicate" in str(msg).lower()
                    for msg in (getattr(e, "validation_errors", None) or [])
                )
            )
            return {
                "total": total,
                "valid": valid,
                "warnings": warnings,
                "errors": errors,
                "duplicates": duplicates,
            }
        if validation_results is not None:
            return self.calculate_from_validation_results(validation_results)

        return {
            "total": 0,
            "valid": 0,
            "warnings": 0,
            "errors": 0,
            "duplicates": 0,
        }