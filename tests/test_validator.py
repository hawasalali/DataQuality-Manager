import pytest

from models.employee import Employee
from models.validation_result import Severity
from services.data_validator import DataValidator


@pytest.fixture
def validator() -> DataValidator:
    """Fixture für den DataValidator."""
    return DataValidator()


def test_validate_email_valid(validator: DataValidator):
    """Testet die E-Mail-Validierung mit gültigen Adressen."""
    valid_emails = [
        "max@test.de",
        "anna.schmidt@domain.com",
        "user+tag@example.org",
        "user@sub.domain.co.uk",
    ]
    for email in valid_emails:
        assert validator.validate_email(email) is True, f"E-Mail {email} sollte gültig sein."


def test_validate_email_invalid(validator: DataValidator):
    """Testet die E-Mail-Validierung mit ungültigen Adressen."""
    invalid_emails = [
        "max@test",
        "max@.de",
        "@test.de",
        "max test.de",
        "",
        "max@test..de",
        "max@test.de.",
    ]
    for email in invalid_emails:
        assert validator.validate_email(email) is False, f"E-Mail {email} sollte ungültig sein."


def test_validate_phone_valid(validator: DataValidator):
    """Testet die Telefonnummer-Validierung mit gültigen Nummern."""
    valid_phones = [
        "0123456789",
        "+49123456789",
        "0123/456789",
        "+49 123 456789",
        "0123-456789",
        "123456",
    ]
    for phone in valid_phones:
        assert validator.validate_phone(phone) is True, f"Telefonnummer {phone} sollte gültig sein."


def test_validate_phone_invalid(validator: DataValidator):
    """Testet die Telefonnummer-Validierung mit ungültigen Nummern."""
    invalid_phones = [
        "abc",
        "123-",
        "+-123456789",
        "0123 4",  # Zu kurz (nur 5 Ziffern, mindestens 6 erforderlich)
        "++123456789",
    ]
    for phone in invalid_phones:
        assert validator.validate_phone(phone) is False, f"Telefonnummer {phone} sollte ungültig sein."


def test_validate_date_valid(validator: DataValidator):
    """Testet die Datum-Validierung mit gültigen Daten."""
    valid_dates = [
        "2020-01-01",
        "1999-12-31",
        "2000-02-29",
        "2023-04-30",
    ]
    for date in valid_dates:
        assert validator._validate_date(date) is True, f"Datum {date} sollte gültig sein."


def test_validate_date_invalid(validator: DataValidator):
    """Testet die Datum-Validierung mit ungültigen Daten."""
    invalid_dates = [
        "2020-13-01",
        "2020-02-30",
        "2020-04-31",
        "2020/01/01",
        "01-01-2020",
        "2020-1-1",
        "",
        "not-a-date",
    ]
    for date in invalid_dates:
        assert validator._validate_date(date) is False, f"Datum {date} sollte ungültig sein."


def test_validate_employee_valid(validator: DataValidator):
    """Testet die Validierung eines gültigen Mitarbeiters."""
    employee = Employee(
        id=None,
        first_name="Max",
        last_name="Mustermann",
        email="max@test.de",
        phone="0123456789",
        department="IT",
        hire_date="2020-01-01",
    )
    results = validator.validate_employee(employee)
    assert results == []


def test_validate_employee_invalid(validator: DataValidator):
    """Testet die Validierung eines ungültigen Mitarbeiters."""
    employee = Employee(
        id=None,
        first_name="",
        last_name="",
        email="invalid-email",
        phone="abc",
        department="",
        hire_date="2020-13-01",
    )
    results = validator.validate_employee(employee)
    fields_with_errors = {r.field for r in results}

    assert len(results) >= 5
    assert "first_name" in fields_with_errors
    assert "last_name" in fields_with_errors
    assert "email" in fields_with_errors
    assert "phone" in fields_with_errors
    assert "hire_date" in fields_with_errors


def test_validate_project_sample_csv(validator: DataValidator):
    """Testet die 5 Beispiel-Datensätze aus dem Projektplan."""
    employees = [
        Employee(first_name="Max", last_name="Mustermann", email="max@test.de", phone="0171234567", department="IT"),
        Employee(first_name="Anna", last_name="Schmidt", email="anna@test.de", phone="0171234568", department="HR"),
        Employee(first_name="Peter", last_name="", email="peter@test.de", phone="0171234569", department="IT"),
        Employee(first_name="Max", last_name="Mustermann", email="max@test.de", phone="0171234567", department="IT"),
        Employee(first_name="Lisa", last_name="Meyer", email="invalid-email", phone="0171234560", department="Sales"),
    ]

    results = validator.validate_all(employees)
    errors = [r for r in results if r.severity == Severity.ERROR]
    warnings = [r for r in results if r.severity == Severity.WARNING]

    assert len(errors) == 2  # Peter (Nachname fehlt) + Lisa (ungültige E-Mail)
    assert len(warnings) == 1  # Zweiter Max (Duplikat)
    assert sum(1 for e in employees if e.status == "VALID") == 2
    assert employees[2].status == "INVALID"
    assert employees[3].status == "WARNING"
    assert employees[4].status == "INVALID"