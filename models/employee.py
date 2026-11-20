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
            "status": (self.status or "VALID").upper(),
            "error_message": self.error_message,
            "validation_errors": list(self.validation_errors),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Employee":
        """Erstellt eine Employee-Instanz aus einem Dictionary."""
        raw_id = data.get("id")
        if raw_id is None or raw_id == "":
            emp_id: Optional[int] = None
        else:
            emp_id = int(raw_id)

        raw_errors = data.get("validation_errors")
        errors = [str(err) for err in raw_errors] if isinstance(raw_errors, list) else []

        raw_status = str(data.get("status") or "VALID").strip().upper() or "VALID"

        return cls(
            id=emp_id,
            first_name=str(data.get("first_name") or "").strip(),
            last_name=str(data.get("last_name") or "").strip(),
            email=str(data.get("email") or "").strip(),
            phone=str(data.get("phone") or "").strip(),
            department=str(data.get("department") or "").strip(),
            birth_date=str(data.get("birth_date") or "").strip(),
            hire_date=str(data.get("hire_date") or "").strip(),
            status=raw_status,
            error_message=str(data.get("error_message") or ""),
            validation_errors=errors,
        )