from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Employee:
    """Ein Datensatz für Mitarbeiterdaten."""

    id: Optional[int] = None
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone: str = ""
    department: str = ""
    birth_date: str = ""
    hire_date: str = ""
    status: str = "VALID"
    error_message: str = ""
    validation_errors: List[str] = field(default_factory=list)

    @property
    def full_name(self) -> str:
        """Gibt den vollständigen Namen zurück."""
        return f"{self.first_name} {self.last_name}".strip()

    def to_dict(self) -> dict:
        """Konvertiert die Employee-Instanz in ein Dictionary."""
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone": self.phone,
            "department": self.department,
            "birth_date": self.birth_date,
            "hire_date": self.hire_date,
            "status": self.status,
            "error_message": self.error_message,
            "validation_errors": list(self.validation_errors),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Employee":
        """Erstellt eine Employee-Instanz aus einem Dictionary."""
        raw_errors = data.get("validation_errors")
        errors = [str(err) for err in raw_errors] if isinstance(raw_errors, list) else []

        return cls(
            id=data.get("id"),
            first_name=str(data.get("first_name") or ""),
            last_name=str(data.get("last_name") or ""),
            email=str(data.get("email") or ""),
            phone=str(data.get("phone") or ""),
            department=str(data.get("department") or ""),
            birth_date=str(data.get("birth_date") or ""),
            hire_date=str(data.get("hire_date") or ""),
            status=str(data.get("status") or "VALID"),
            error_message=str(data.get("error_message") or ""),
            validation_errors=errors,
        )