from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Severity(str, Enum):
    """Schweregrade für Validierungsfehler laut Projektplan."""

    ERROR = "ERROR"
    WARNING = "WARNING"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_value(cls, value: object) -> "Severity":
        """Wandelt einen Wert sicher in Severity um oder wirft ValueError."""
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            normalized = value.strip().upper()
            if normalized == "INFO":
                return cls.WARNING
            for item in cls:
                if item.value == normalized or item.name == normalized:
                    return item
        raise ValueError(f"Ungültiger Schweregrad (Severity): {value!r}")


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

    def __post_init__(self) -> None:
        self.severity = Severity.from_value(self.severity)
        self.field = str(self.field or "").strip()
        self.message = str(self.message or "").strip()

        if not self.is_valid and not self.message:
            raise ValueError("Fehlermeldung muss angegeben werden, wenn is_valid=False.")

    @property
    def is_error(self) -> bool:
        """Gibt True zurück, wenn es sich um einen ERROR handelt."""
        return self.severity == Severity.ERROR

    @property
    def is_warning(self) -> bool:
        """Gibt True zurück, wenn es sich um eine WARNING handelt."""
        return self.severity == Severity.WARNING

    def to_dict(self) -> dict:
        """Konvertiert das ValidationResult-Objekt in ein Dictionary."""
        return {
            "employee_id": self.employee_id,
            "field": self.field,
            "message": self.message,
            "severity": self.severity.value,
            "is_valid": self.is_valid,
            "expected_format": self.expected_format,
            "actual_value": self.actual_value,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ValidationResult":
        """Erstellt ein ValidationResult-Objekt aus einem Dictionary."""
        raw_emp_id = data.get("employee_id")
        if raw_emp_id is None or raw_emp_id == "":
            emp_id: Optional[int] = None
        else:
            emp_id = int(raw_emp_id)

        return cls(
            employee_id=emp_id,
            field=str(data.get("field") or ""),
            message=str(data.get("message") or ""),
            severity=Severity.from_value(data.get("severity", Severity.ERROR)),
            is_valid=bool(data.get("is_valid", False)),
            expected_format=data.get("expected_format"),
            actual_value=data.get("actual_value"),
        )