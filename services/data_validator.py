import re
from datetime import datetime
from typing import Dict, List, Set

from models.employee import Employee
from models.validation_result import Severity, ValidationResult


class DataValidator:
    """Ein Validator für Mitarbeiterdaten (Pflichtfelder, Formate und Duplikate)."""

    EMAIL_PATTERN: str = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    PHONE_PATTERN: str = r"^\+?[0-9]+(?:[\s\-/()][0-9]+)*$"
    DATE_PATTERN: str = r"^\d{4}-\d{2}-\d{2}$"

    def validate_email(self, email: str) -> bool:
        """Validiert eine E-Mail-Adresse anhand eines regulären Ausdrucks."""
        if not email:
            return False
        cleaned = str(email).strip()
        if not cleaned or ".." in cleaned:
            return False
        return bool(re.match(self.EMAIL_PATTERN, cleaned))

    def validate_phone(self, phone: str) -> bool:
        """Validiert eine Telefonnummer (erlaubt Ziffern, +, Leerzeichen, -, /, Klammern)."""
        if not phone or not str(phone).strip():
            return True  # Optionales Feld, wird nur geprüft wenn befüllt
        cleaned = str(phone).strip()
        if not re.match(self.PHONE_PATTERN, cleaned):
            return False
        digits = [c for c in cleaned if c.isdigit()]
        return len(digits) >= 6

    def _validate_date(self, date_str: str) -> bool:
        """Validiert ein Datum im strikten Format YYYY-MM-DD."""
        if not date_str or not str(date_str).strip():
            return False
        cleaned = str(date_str).strip()
        if not re.match(self.DATE_PATTERN, cleaned):
            return False
        try:
            datetime.strptime(cleaned, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def validate_employee(self, employee: Employee) -> List[ValidationResult]:
        """Validiert ein einzelnes Employee-Objekt und sammelt alle Validierungsfehler."""
        errors: List[ValidationResult] = []

        first_name = str(employee.first_name or "")
        last_name = str(employee.last_name or "")
        email = str(employee.email or "")
        phone = str(employee.phone or "")
        birth_date = str(employee.birth_date or "")
        hire_date = str(employee.hire_date or "")

        # Vorname (Pflichtfeld)
        if not first_name.strip():
            errors.append(
                ValidationResult(
                    employee_id=employee.id,
                    field="first_name",
                    message="Der Vorname darf nicht leer sein.",
                    severity=Severity.ERROR,
                    is_valid=False,
                    actual_value=employee.first_name,
                )
            )

        # Nachname (Pflichtfeld)
        if not last_name.strip():
            errors.append(
                ValidationResult(
                    employee_id=employee.id,
                    field="last_name",
                    message="Der Nachname darf nicht leer sein.",
                    severity=Severity.ERROR,
                    is_valid=False,
                    actual_value=employee.last_name,
                )
            )

        # E-Mail (Pflichtfeld + Format)
        if not email.strip():
            errors.append(
                ValidationResult(
                    employee_id=employee.id,
                    field="email",
                    message="Die E-Mail-Adresse darf nicht leer sein.",
                    severity=Severity.ERROR,
                    is_valid=False,
                    expected_format="benutzer@domain.de",
                    actual_value=employee.email,
                )
            )
        elif not self.validate_email(email):
            errors.append(
                ValidationResult(
                    employee_id=employee.id,
                    field="email",
                    message="Ungültige E-Mail-Adresse.",
                    severity=Severity.ERROR,
                    is_valid=False,
                    expected_format="benutzer@domain.de",
                    actual_value=employee.email,
                )
            )

        # Telefonnummer (optional, Format prüfen wenn vorhanden)
        if phone.strip() and not self.validate_phone(phone):
            errors.append(
                ValidationResult(
                    employee_id=employee.id,
                    field="phone",
                    message="Ungültige Telefonnummer.",
                    severity=Severity.ERROR,
                    is_valid=False,
                    expected_format="0171234567 oder +49 171 1234567",
                    actual_value=employee.phone,
                )
            )

        # Geburtsdatum (optional, Format prüfen wenn vorhanden)
        if birth_date.strip() and not self._validate_date(birth_date):
            errors.append(
                ValidationResult(
                    employee_id=employee.id,
                    field="birth_date",
                    message="Ungültiges Geburtsdatum. Format: YYYY-MM-DD.",
                    severity=Severity.ERROR,
                    is_valid=False,
                    expected_format="YYYY-MM-DD",
                    actual_value=employee.birth_date,
                )
            )

        # Einstellungsdatum (optional, Format prüfen wenn vorhanden)
        if hire_date.strip() and not self._validate_date(hire_date):
            errors.append(
                ValidationResult(
                    employee_id=employee.id,
                    field="hire_date",
                    message="Ungültiges Einstellungsdatum. Format: YYYY-MM-DD.",
                    severity=Severity.ERROR,
                    is_valid=False,
                    expected_format="YYYY-MM-DD",
                    actual_value=employee.hire_date,
                )
            )

        return errors

    def validate_all(self, employees: List[Employee]) -> List[ValidationResult]:
        """
        Validiert eine Liste von Mitarbeitern inklusive Duplikat-Erkennung.
        Aktualisiert Status und Fehlerliste direkt an jedem Employee-Objekt.
        """
        all_results: List[ValidationResult] = []
        seen_emails: Set[str] = set()

        for employee in employees or []:
            emp_results = self.validate_employee(employee)
            email_key = str(employee.email or "").strip().lower()

            if email_key and self.validate_email(email_key):
                if email_key in seen_emails:
                    emp_results.append(
                        ValidationResult(
                            employee_id=employee.id,
                            field="email",
                            message="Doppelter Mitarbeiterdatensatz (E-Mail bereits vorhanden).",
                            severity=Severity.WARNING,
                            is_valid=False,
                            actual_value=employee.email,
                        )
                    )
                else:
                    seen_emails.add(email_key)

            employee.validation_errors = [r.message for r in emp_results]
            if any(r.severity == Severity.ERROR for r in emp_results):
                employee.status = "INVALID"
                employee.error_message = "; ".join(employee.validation_errors)
            elif any(r.severity == Severity.WARNING for r in emp_results):
                employee.status = "WARNING"
                employee.error_message = "; ".join(employee.validation_errors)
            else:
                employee.status = "VALID"
                employee.error_message = ""

            all_results.extend(emp_results)

        return all_results

    def find_duplicates(self, employees: List[Employee]) -> Dict[str, List[Employee]]:
        """Findet Duplikate in einer Liste von Mitarbeitern basierend auf der E-Mail-Adresse."""
        email_to_employees: Dict[str, List[Employee]] = {}
        for employee in employees or []:
            email = str(employee.email or "").strip().lower()
            if email:
                email_to_employees.setdefault(email, []).append(employee)

        return {
            email: emp_list
            for email, emp_list in email_to_employees.items()
            if len(emp_list) > 1
        }

    def get_duplicate_emails(self, employees: List[Employee]) -> Set[str]:
        """Gibt eine Menge von doppelten E-Mail-Adressen zurück."""
        return set(self.find_duplicates(employees).keys())