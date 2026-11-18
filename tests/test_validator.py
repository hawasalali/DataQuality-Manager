from services.data_validator import validate_email, validate_phone, validate_date, validate_employee
from models.employee import Employee

def test_validate_email():
    assert validate_email("max@test.de") == True
    assert validate_email("max@test") == False

def test_validate_phone():
    assert validate_phone("0123456789") == True
    assert validate_phone("abc") == False

def test_validate_date():
    assert validate_date("2020-01-01") == True
    assert validate_date("2020-13-01") == False

def test_validate_employee():
    emp1 = Employee(id=None, name="Max", email="max@test.de", phone="0123456789", department="IT", hire_date="2020-01-01")
    emp2 = Employee(id=None, name="", email="invalid", phone="abc", department="IT", hire_date="2020-13-01")

    result1 = validate_employee(emp1)
    assert result1.is_valid == True
    assert result1.errors == []

    result2 = validate_employee(emp2)
    assert result2.is_valid == False
    assert len(result2.errors) > 0
