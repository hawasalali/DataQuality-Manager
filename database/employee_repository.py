from typing import List, Optional
from models.employee import Employee
from models.validation_result import ValidationResult


class EmployeeRepository:
    def __init__(self, database):
        self.db = database

    def _row_to_employee(self, row) -> Employee:
        """Wandelt eine Datenbankzeile (Tuple oder sqlite3.Row) in ein Employee-Objekt um."""
        if isinstance(row, dict) or hasattr(row, "keys"):
            return Employee(
                id=row["id"],
                first_name=row["first_name"] or "",
                last_name=row["last_name"] or "",
                email=row["email"] or "",
                phone=row["phone"] or "",
                department=row["department"] or "",
                birth_date=row["birth_date"] or "",
                hire_date=row["hire_date"] or "",
                status=row["status"] or "VALID",
            )
        return Employee(
            id=row[0],
            first_name=row[1] or "",
            last_name=row[2] or "",
            email=row[3] or "",
            phone=row[4] or "",
            department=row[5] or "",
            birth_date=row[6] or "",
            hire_date=row[7] or "",
            status=row[8] or "VALID",
        )

    def add(self, employee: Employee) -> int:
        cursor = self.db.conn.cursor()
        cursor.execute(
            """
            INSERT INTO employees (
                first_name,
                last_name,
                email,
                phone,
                department,
                birth_date,
                hire_date,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                employee.first_name,
                employee.last_name,
                employee.email,
                employee.phone,
                employee.department,
                employee.birth_date,
                employee.hire_date,
                employee.status,
            ),
        )
        self.db.conn.commit()
        employee.id = cursor.lastrowid
        return employee.id

    def get_all(self) -> List[Employee]:
        cursor = self.db.conn.cursor()
        cursor.execute(
            """
            SELECT id, first_name, last_name, email, phone, department, birth_date, hire_date, status
            FROM employees
            """
        )
        rows = cursor.fetchall()
        return [self._row_to_employee(row) for row in rows]

    def get_by_id(self, employee_id: int) -> Optional[Employee]:
        cursor = self.db.conn.cursor()
        cursor.execute(
            """
            SELECT id, first_name, last_name, email, phone, department, birth_date, hire_date, status
            FROM employees
            WHERE id = ?
            """,
            (employee_id,),
        )
        row = cursor.fetchone()
        return self._row_to_employee(row) if row else None

    def update(self, employee: Employee) -> None:
        cursor = self.db.conn.cursor()
        cursor.execute(
            """
            UPDATE employees
            SET
                first_name = ?,
                last_name = ?,
                email = ?,
                phone = ?,
                department = ?,
                birth_date = ?,
                hire_date = ?,
                status = ?
            WHERE id = ?
            """,
            (
                employee.first_name,
                employee.last_name,
                employee.email,
                employee.phone,
                employee.department,
                employee.birth_date,
                employee.hire_date,
                employee.status,
                employee.id,
            ),
        )
        self.db.conn.commit()

    def delete(self, employee_id: int) -> None:
        cursor = self.db.conn.cursor()
        cursor.execute(
            """
            DELETE FROM employees
            WHERE id = ?
            """,
            (employee_id,),
        )
        self.db.conn.commit()

    def add_validation_result(self, result: ValidationResult) -> None:
        cursor = self.db.conn.cursor()
        cursor.execute(
            """
            INSERT INTO validation_results (employee_id, column_name, error_message, severity)
            VALUES (?, ?, ?, ?)
            """,
            (result.employee_id, result.field, result.message, str(result.severity)),
        )
        self.db.conn.commit()

    def get_all_validation_results(self) -> List[ValidationResult]:
        cursor = self.db.conn.cursor()
        cursor.execute(
            """
            SELECT employee_id, column_name, error_message, severity
            FROM validation_results
            """
        )
        rows = cursor.fetchall()
        results = []
        for row in rows:
            emp_id = row["employee_id"] if hasattr(row, "keys") else row[0]
            col = row["column_name"] if hasattr(row, "keys") else row[1]
            msg = row["error_message"] if hasattr(row, "keys") else row[2]
            sev = row["severity"] if hasattr(row, "keys") else row[3]
            results.append(
                ValidationResult(
                    employee_id=emp_id,
                    field=col or "",
                    message=msg or "",
                    severity=sev or "ERROR",
                )
            )
        return results

    def add_import_history(
        self, filename: str, import_date: str, records_imported: int, records_rejected: int
    ) -> None:
        cursor = self.db.conn.cursor()
        cursor.execute(
            """
            INSERT INTO import_history (filename, import_date, records_imported, records_rejected)
            VALUES (?, ?, ?, ?)
            """,
            (filename, import_date, records_imported, records_rejected),
        )
        self.db.conn.commit()
