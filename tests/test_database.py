from database.employee_repository import EmployeeRepository
from models.employee import Employee
import os

def test_employee_repository():
    db_path = "data/test_employees.db"
    repo = EmployeeRepository(db_path)

    emp = Employee(id=None, name="Test", email="test@test.de", phone="123", department="IT", hire_date="2020-01-01")
    emp_id = repo.add_employee(emp)
    assert emp_id is not None

    employees = repo.get_all_employees()
    assert len(employees) == 1
    assert employees[0].name == "Test"

    repo.close()
    os.remove(db_path)
