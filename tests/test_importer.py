from pathlib import Path

import pytest

from models.employee import Employee
from services.csv_importer import CsvImporter
from services.data_validator import DataValidator


@pytest.fixture
def importer() -> CsvImporter:
    """Fixture für den CsvImporter."""
    return CsvImporter()


@pytest.fixture
def test_csv_path(tmp_path: Path) -> Path:
    """Fixture für den Pfad zu einer temporären Test-CSV-Datei."""
    return tmp_path / "test_employees.csv"


@pytest.fixture
def test_csv_content() -> str:
    """Fixture für den Inhalt der Test-CSV-Datei."""
    return (
        "first_name,last_name,email,phone,department,birth_date,hire_date\n"
        "Max,Mustermann,max@test.de,0123456789,IT,1990-05-14,2020-01-01\n"
        "Anna,Schmidt,anna@test.de,987654321,HR,1988-11-23,2019-05-20\n"
    )


@pytest.fixture(autouse=True)
def setup_and_teardown(test_csv_path: Path, test_csv_content: str):
    """Fixture für das Einrichten der Test-CSV-Datei im temporären Verzeichnis."""
    test_csv_path.write_text(test_csv_content, encoding="utf-8")
    yield


def test_import_csv_single_employee(importer: CsvImporter, test_csv_path: Path):
    """Testet den Import einer CSV-Datei mit einem Mitarbeiter."""
    test_csv_path.write_text(
        "first_name,last_name,email,phone,department,birth_date,hire_date\n"
        "Max,Mustermann,max@test.de,0123456789,IT,1990-05-14,2020-01-01\n",
        encoding="utf-8",
    )

    employees = importer.import_employees(test_csv_path)

    assert len(employees) == 1
    assert isinstance(employees[0], Employee)
    assert employees[0].first_name == "Max"
    assert employees[0].last_name == "Mustermann"
    assert employees[0].email == "max@test.de"
    assert employees[0].phone == "0123456789"
    assert employees[0].department == "IT"
    assert employees[0].birth_date == "1990-05-14"
    assert employees[0].hire_date == "2020-01-01"


def test_import_csv_multiple_employees(importer: CsvImporter, test_csv_path: Path):
    """Testet den Import einer CSV-Datei mit mehreren Mitarbeitern."""
    employees = importer.import_employees(test_csv_path)

    assert len(employees) == 2
    assert all(isinstance(emp, Employee) for emp in employees)
    assert employees[0].first_name == "Max"
    assert employees[1].first_name == "Anna"


def test_import_csv_semicolon_and_case_insensitive_headers(
    importer: CsvImporter, test_csv_path: Path
):
    """Testet Semikolon-Trennzeichen und abweichende Groß-/Kleinschreibung in Headern."""
    test_csv_path.write_text(
        "First_Name;Last_Name;EMAIL;Birth_Date;Hire_Date\n"
        "Lukas;Weber;lukas@test.de;1992-03-15;2021-07-01\n",
        encoding="utf-8",
    )

    employees = importer.import_employees(test_csv_path)
    assert len(employees) == 1
    assert employees[0].first_name == "Lukas"
    assert employees[0].last_name == "Weber"
    assert employees[0].email == "lukas@test.de"
    assert employees[0].birth_date == "1992-03-15"
    assert employees[0].hire_date == "2021-07-01"


def test_import_csv_empty_file(importer: CsvImporter, test_csv_path: Path):
    """Testet den Import einer leeren CSV-Datei."""
    test_csv_path.write_text("", encoding="utf-8")

    employees = importer.import_employees(test_csv_path)
    assert len(employees) == 0


def test_import_csv_missing_columns(importer: CsvImporter, test_csv_path: Path):
    """Testet den Import einer CSV-Datei mit fehlenden Pflichtspalten."""
    test_csv_path.write_text("first_name,last_name\nMax,Mustermann\n", encoding="utf-8")

    employees = importer.import_employees(test_csv_path)
    assert len(employees) == 0


def test_import_csv_invalid_data_detected_by_validator(
    importer: CsvImporter, test_csv_path: Path
):
    """Testet, dass ungültige CSV-Zeilen eingelesen und vom Validator als INVALID markiert werden."""
    test_csv_path.write_text(
        "first_name,last_name,email,phone,department,birth_date,hire_date\n"
        ",,invalid-email,,,,\n",
        encoding="utf-8",
    )

    employees = importer.import_employees(test_csv_path)
    assert len(employees) == 1

    validator = DataValidator()
    results = validator.validate_all(employees)
    assert len(results) > 0
    assert employees[0].status == "INVALID"


def test_import_csv_nonexistent_file(importer: CsvImporter, tmp_path: Path):
    """Testet den Import einer nicht existierenden CSV-Datei."""
    nonexistent_file = tmp_path / "nonexistent.csv"
    employees = importer.import_employees(nonexistent_file)
    assert len(employees) == 0


def test_preview_csv_limits_rows(importer: CsvImporter, test_csv_path: Path):
    """Testet die Import-Vorschau mit Limit."""
    headers, preview_rows, error = importer.preview_csv(test_csv_path, limit=1)
    assert error is None
    assert "first_name" in headers
    assert len(preview_rows) == 1