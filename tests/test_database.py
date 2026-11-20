from pathlib import Path

import pytest

from database.connection import DatabaseConnection
from database.employee_repository import EmployeeRepository
from models.employee import Employee
from models.validation_result import Severity, ValidationResult

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "database" / "schema.sql"


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    """Fixture für den Pfad zu einer isolierten temporären Testdatenbank."""
    return str(tmp_path / "test_employees.db")


@pytest.fixture
def employee_repository(db_path: str):
    """Fixture für das EmployeeRepository mit einer frischen Testdatenbank."""
    db = DatabaseConnection(db_path=db_path)
    db.create_tables(str(SCHEMA_PATH))
    repo = EmployeeRepository(db)

    try:
        yield repo
    finally:
        db.close()


def test_add_employee(employee_repository):
    """Testet das Hinzufügen eines Mitarbeiters."""
    emp = Employee(
        id=None,
        first_name="Max",
        last_name="Mustermann",
        email="max@mustermann.de",
        phone="123456789",
        department="IT",
        birth_date="1990-05-14",
        hire_date="2020-01-01",
    )

    emp_id = employee_repository.add(emp)
    assert emp_id is not None
    assert isinstance(emp_id, int)
    assert emp_id > 0

    employees = employee_repository.get_all()
    assert len(employees) == 1
    assert employees[0].first_name == "Max"
    assert employees[0].last_name == "Mustermann"
    assert employees[0].email == "max@mustermann.de"
    assert employees[0].phone == "123456789"
    assert employees[0].birth_date == "1990-05-14"


def test_get_employee_by_id(employee_repository):
    """Testet das Abrufen eines Mitarbeiters nach ID."""
    emp = Employee(
        id=None,
        first_name="Anna",
        last_name="Schmidt",
        email="anna@schmidt.de",
        phone="987654321",
        department="HR",
        birth_date="1988-11-23",
        hire_date="2019-05-20",
    )
    emp_id = employee_repository.add(emp)

    retrieved_emp = employee_repository.get_by_id(emp_id)
    assert retrieved_emp is not None
    assert retrieved_emp.first_name == "Anna"
    assert retrieved_emp.last_name == "Schmidt"
    assert retrieved_emp.email == "anna@schmidt.de"


def test_get_employee_by_id_not_found(employee_repository):
    """Testet das Abrufen einer nicht vorhandenen Mitarbeiter-ID."""
    assert employee_repository.get_by_id(99999) is None


def test_update_employee(employee_repository):
    """Testet das Aktualisieren eines Mitarbeiters."""
    emp = Employee(
        id=None,
        first_name="Erika",
        last_name="Müller",
        email="erika@mueller.de",
        phone="456123789",
        department="Finance",
        birth_date="1992-07-08",
        hire_date="2021-03-10",
    )
    emp_id = employee_repository.add(emp)

    updated_emp = Employee(
        id=emp_id,
        first_name="Erika",
        last_name="Meier",
        email="erika@meier.de",
        phone="456123789",
        department="Finance",
        birth_date="1992-07-08",
        hire_date="2021-03-10",
        status="VALID",
    )
    employee_repository.update(updated_emp)

    retrieved_emp = employee_repository.get_by_id(emp_id)
    assert retrieved_emp is not None
    assert retrieved_emp.last_name == "Meier"
    assert retrieved_emp.email == "erika@meier.de"


def test_update_employee_without_id_raises(employee_repository):
    """Testet, dass ein Update ohne ID einen ValueError auslöst."""
    emp = Employee(first_name="Ohne", last_name="ID", email="ohne@id.de")
    with pytest.raises(ValueError):
        employee_repository.update(emp)


def test_delete_employee(employee_repository):
    """Testet das Löschen eines Mitarbeiters."""
    emp = Employee(
        id=None,
        first_name="Test",
        last_name="User",
        email="test@user.de",
        phone="111222333",
        department="Marketing",
        birth_date="1995-02-12",
        hire_date="2022-01-01",
    )
    emp_id = employee_repository.add(emp)

    employee_repository.delete(emp_id)

    employees = employee_repository.get_all()
    assert len(employees) == 0


def test_get_all_employees_empty(employee_repository):
    """Testet das Abrufen aller Mitarbeiter aus einer leeren Datenbank."""
    employees = employee_repository.get_all()
    assert len(employees) == 0
    assert isinstance(employees, list)


def test_validation_results_and_import_history(employee_repository):
    """Testet Speichern/Laden von Validierungsergebnissen und Import-Historie."""
    emp_id = employee_repository.add(
        Employee(first_name="Lukas", last_name="Weber", email="lukas@weber.de")
    )
    employee_repository.add_validation_result(
        ValidationResult(
            employee_id=emp_id,
            field="birth_date",
            message="Ungültiges Geburtsdatum. Format: YYYY-MM-DD.",
            severity=Severity.ERROR,
            is_valid=False,
        )
    )
    results = employee_repository.get_all_validation_results()
    assert len(results) == 1
    assert results[0].employee_id == emp_id
    assert results[0].field == "birth_date"

    employee_repository.clear_validation_results()
    assert employee_repository.get_all_validation_results() == []

    employee_repository.add_import_history(
        filename="mitarbeiter.csv",
        import_date="2026-11-20 11:00:00",
        records_imported=4,
        records_rejected=1,
    )
    history = employee_repository.get_import_history()
    assert len(history) == 1
    assert history[0]["filename"] == "mitarbeiter.csv"
    assert history[0]["records_imported"] == 4
    assert history[0]["records_rejected"] == 1