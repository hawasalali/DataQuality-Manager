import os
import pytest
from pathlib import Path
from services.csv_importer import CsvImporter
from services.data_validator import DataValidator
from models.employee import Employee


@pytest.fixture
def importer():
    """Fixture für den CsvImporter."""
    return CsvImporter()


@pytest.fixture
def test_csv_path():
    """Fixture für den Pfad zur Test-CSV-Datei."""
    return Path("data/test_employees.csv")


@pytest.fixture
def test_csv_content():
    """Fixture für den Inhalt der Test-CSV-Datei."""
    return (
        "first_name,last_name,email,phone,department,hire_date\n"
        "Max,Mustermann,max@test.de,0123456789,IT,2020-01-01\n"
        "Anna,Schmidt,anna@test.de,987654321,HR,2019-05-20\n"
    )


@pytest.fixture(autouse=True)
def setup_and_teardown(test_csv_path, test_csv_content):
    """Fixture für das Einrichten und Aufräumen der Test-CSV-Datei."""
    os.makedirs("data", exist_ok=True)
    with open(test_csv_path, "w", encoding="utf-8") as f:
        f.write(test_csv_content)

    yield

    if test_csv_path.exists():
        test_csv_path.unlink()


def test_import_csv_single_employee(importer, test_csv_path):
    """Testet den Import einer CSV-Datei mit einem Mitarbeiter."""
    with open(test_csv_path, "w", encoding="utf-8") as f:
        f.write(
            "first_name,last_name,email,phone,department,hire_date\n"
            "Max,Mustermann,max@test.de,0123456789,IT,2020-01-01\n"
        )

    employees = importer.import_employees(test_csv_path)

    assert len(employees) == 1
    assert isinstance(employees, Employee)
    assert employees.first_name == "Max"
    assert employees.last_name == "Mustermann"
    assert employees.email == "max@test.de"
    assert employees.phone == "0123456789"
    assert employees.department == "IT"
    assert employees.hire_date == "2020-01-01"


def test_import_csv_multiple_employees(importer, test_csv_path):
    """Testet den Import einer CSV-Datei mit mehreren Mitarbeitern."""
    employees = importer.import_employees(test_csv_path)

    assert len(employees) == 2
    assert all(isinstance(emp, Employee) for emp in employees)
    assert employees.first_name == "Max"
    assert employees.first_name == "Anna"


def test_import_csv_empty_file(importer, test_csv_path):
    """Testet den Import einer leeren CSV-Datei."""
    with open(test_csv_path, "w", encoding="utf-8") as f:
        f.write("")

    employees = importer.import_employees(test_csv_path)
    assert len(employees) == 0


def test_import_csv_missing_columns(importer, test_csv_path):
    """Testet den Import einer CSV-Datei mit fehlenden Pflichtspalten."""
    with open(test_csv_path, "w", encoding="utf-8") as f:
        f.write("first_name,last_name\nMax,Mustermann\n")

    employees = importer.import_employees(test_csv_path)
    assert len(employees) == 0


def test_import_csv_invalid_data_detected_by_validator(importer, test_csv_path):
    """Testet, dass ungültige CSV-Zeilen eingelesen und vom Validator als INVALID markiert werden."""
    with open(test_csv_path, "w", encoding="utf-8") as f:
        f.write(
            "first_name,last_name,email,phone,department,hire_date\n"
            ",,invalid-email,,,\n"
        )

    employees = importer.import_employees(test_csv_path)
    assert len(employees) == 1

    validator = DataValidator()
    results = validator.validate_all(employees)
    assert len(results) > 0
    assert employees.status == "INVALID"


def test_import_csv_nonexistent_file(importer):
    """Testet den Import einer nicht existierenden CSV-Datei."""
    nonexistent_file = Path("data/nonexistent.csv")
    employees = importer.import_employees(nonexistent_file)
    assert len(employees) == 0
