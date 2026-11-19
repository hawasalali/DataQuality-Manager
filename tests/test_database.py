import os
import pytest
from database.connection import DatabaseConnection
from database.employee_repository import EmployeeRepository
from models.employee import Employee


@pytest.fixture
def db_path():
    """Fixture für den Pfad zur Testdatenbank."""
    return "data/test_employees.db"


@pytest.fixture
def employee_repository(db_path):
    """Fixture für das EmployeeRepository mit einer frischen Testdatenbank."""
    os.makedirs("data", exist_ok=True)
    if os.path.exists(db_path):
        os.remove(db_path)

    db = DatabaseConnection(db_path=db_path)
    db.create_tables("database/schema.sql")
    repo = EmployeeRepository(db)

    yield repo

    db.close()
    if os.path.exists(db_path):
        os.remove(db_path)


def test_add_employee(employee_repository):
    """Testet das Hinzufügen eines Mitarbeiters."""
    emp = Employee(
        id=None,
        first_name="Max",
        last_name="Mustermann",
        email="max@mustermann.de",
        phone="123456789",
        department="IT",
        hire_date="2020-01-01",
    )

    emp_id = employee_repository.add(emp)
    assert emp_id is not None
    assert isinstance(emp_id, int)

    employees = employee_repository.get_all()
    assert len(employees) == 1
    assert employees[0].first_name == "Max"
    assert employees[0].last_name == "Mustermann"
    assert employees[0].email == "max@mustermann.de"
    assert employees[0].phone == "123456789"


def test_get_employee_by_id(employee_repository):
    """Testet das Abrufen eines Mitarbeiters nach ID."""
    emp = Employee(
        id=None,
        first_name="Anna",
        last_name="Schmidt",
        email="anna@schmidt.de",
        phone="987654321",
        department="HR",
        hire_date="2019-05-20",
    )
    emp_id = employee_repository.add(emp)

    retrieved_emp = employee_repository.get_by_id(emp_id)
    assert retrieved_emp is not None
    assert retrieved_emp.first_name == "Anna"
    assert retrieved_emp.last_name == "Schmidt"
    assert retrieved_emp.email == "anna@schmidt.de"


def test_update_employee(employee_repository):
    """Testet das Aktualisieren eines Mitarbeiters."""
    emp = Employee(
        id=None,
        first_name="Erika",
        last_name="Müller",
        email="erika@mueller.de",
        phone="456123789",
        department="Finance",
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
        hire_date="2021-03-10",
    )
    employee_repository.update(updated_emp)

    retrieved_emp = employee_repository.get_by_id(emp_id)
    assert retrieved_emp is not None
    assert retrieved_emp.last_name == "Meier"
    assert retrieved_emp.email == "erika@meier.de"


def test_delete_employee(employee_repository):
    """Testet das Löschen eines Mitarbeiters."""
    emp = Employee(
        id=None,
        first_name="Test",
        last_name="User",
        email="test@user.de",
        phone="111222333",
        department="Marketing",
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
