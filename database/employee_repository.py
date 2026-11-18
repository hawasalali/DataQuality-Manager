from models.employee import Employee
from database.connection import DatabaseConnection

class EmployeeRepository:
    def __init__(self, db_path: str = "data/employees.db"):
        self.db = DatabaseConnection(db_path)

    def add_employee(self, employee: Employee) -> int:
        cursor = self.db.get_connection().cursor()
        cursor.execute(
            "INSERT INTO employees (name, email, phone, department, hire_date, is_valid) VALUES (?, ?, ?, ?, ?, ?)",
            (employee.name, employee.email, employee.phone, employee.department, employee.hire_date, employee.is_valid)
        )
        self.db.get_connection().commit()
        return cursor.lastrowid

    def get_all_employees(self) -> list[Employee]:
        cursor = self.db.get_connection().cursor()
        cursor.execute("SELECT id, name, email, phone, department, hire_date, is_valid FROM employees")
        rows = cursor.fetchall()
        return [
            Employee(
                id=row[0],
                name=row[1],
                email=row[2],
                phone=row[3],
                department=row[4],
                hire_date=row[5],
                is_valid=bool(row[6])
            )
            for row in rows
        ]

    def update_employee_validity(self, employee_id: int, is_valid: bool):
        cursor = self.db.get_connection().cursor()
        cursor.execute(
            "UPDATE employees SET is_valid = ? WHERE id = ?",
            (is_valid, employee_id)
        )
        self.db.get_connection().commit()

    def close(self):
        self.db.close()
