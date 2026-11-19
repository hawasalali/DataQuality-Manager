from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Severity(Enum):
    """Schweregrade für Validierungsfehler laut Projektplan."""
    ERROR = "ERROR"
    WARNING = "WARNING"

    def __str__(self) -> str:
        return self.value


@dataclass
class ValidationResult:
    """Repräsentiert ein Validierungsergebnis für ein Feld in einem Datensatz."""

    field: str
    message: str
    severity: Severity = Severity.ERROR
    employee_id: Optional[int] = None
    is_valid: bool = False
    expected_format: Optional[str] = None
    actual_value: Optional[str] = None

    def __post_init__(self):
        if isinstance(self.severity, str):
            self.severity = Severity[self.severity.upper()]
        if not self.is_valid and not self.message:
            raise ValueError("Fehlermeldung muss angegeben werden, wenn is_valid=False.")

    def to_dict(self) -> dict:
        """Konvertiert das ValidationResult-Objekt in ein Dictionary."""
        return {
            "employee_id": self.employee_id,
            "field": self.field,
            "message": self.message,
            "severity": str(self.severity),
            "is_valid": self.is_valid,
            "expected_format": self.expected_format,
            "actual_value": self.actual_value,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ValidationResult":
        """Erstellt ein ValidationResult-Objekt aus einem Dictionary."""
        raw_severity = data.get("severity", "ERROR")
        severity = (
            raw_severity
            if isinstance(raw_severity, Severity)
            else Severity[str(raw_severity).upper()]
        )
        return cls(
            employee_id=data.get("employee_id"),
            field=data.get("field", ""),
            message=data.get("message", ""),
            severity=severity,
            is_valid=data.get("is_valid", False),
            expected_format=data.get("expected_format"),
            actual_value=data.get("actual_value"),
        )
