from dataclasses import dataclass, field
from typing import Optional, List


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
            "validation_errors": self.validation_errors,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Employee":
        """Erstellt eine Employee-Instanz aus einem Dictionary."""
        return cls(
            id=data.get("id"),
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            email=data.get("email", ""),
            phone=data.get("phone", ""),
            department=data.get("department", ""),
            birth_date=data.get("birth_date", ""),
            hire_date=data.get("hire_date", ""),
            status=data.get("status", "VALID"),
            error_message=data.get("error_message", ""),
            validation_errors=data.get("validation_errors", []),
        )
