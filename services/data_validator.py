import re
from datetime import datetime
from models.employee import Employee
from models.validation_result import ValidationResult

def validate_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email) is not None

def validate_phone(phone: str) -> bool:
    pattern = r"^\+?[0-9\s\-]+$"
    return re.match(pattern, phone) is not None

def validate_date(date_str: str) -> bool:
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def validate_employee(employee: Employee) -> ValidationResult:
    errors = []
    if not employee.name.strip():
        errors.append("Name fehlt")
    if not validate_email(employee.email):
        errors.append("Ungültige E-Mail-Adresse")
    if not validate_phone(employee.phone):
        errors.append("Ungültige Telefonnummer")
    if not validate_date(employee.hire_date):
        errors.append("Ungültiges Einstellungsdatum (Format: YYYY-MM-DD)")

    employee.is_valid = len(errors) == 0
    employee.errors = errors
    return ValidationResult(is_valid=len(errors) == 0, errors=errors)
