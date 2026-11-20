from typing import List, Optional
from models.employee import Employee
from models.validation_result import ValidationResult


class EmployeeRepository:
    """Repository für CRUD-Operationen auf employees, validation_results und import_history."""

    def __init__(self, database):
        self.db = database

    @staticmethod
    def _get_col(row, key: str, index: int, default=None):
        """Liest einen Wert sicher aus einem sqlite3.Row-/Mapping- oder Tuple-Objekt."""
        if isinstance(row, dict) or hasattr(row, "keys"):
            keys = row.keys()
            if key in keys:
                return row[key]
            return default
        if index < len(row):
            return row[index]
        return default

    def _row_to_employee(self, row) -> Employee:
        """Wandelt eine Datenbankzeile (Tuple oder sqlite3.Row) in ein Employee-Objekt um."""
        return Employee(
            id=self._get_col(row, "id", 0),
            first_name=self._get_col(row, "first_name", 1, "") or "",
            last_name=self._get_col(row, "last_name", 2, "") or "",
            email=self._get_col(row, "email", 3, "") or "",
            phone=self._get_col(row, "phone", 4, "") or "",
            department=self._get_col(row, "department", 5, "") or "",
            birth_date=self._get_col(row, "birth_date", 6, "") or "",
            hire_date=self._get_col(row, "hire_date", 7, "") or "",
            status=self._get_col(row, "status", 8, "VALID") or "VALID",
        )

    def add(self, employee: Employee) -> int:
        """Fügt einen neuen Mitarbeiter ein und gibt die neue ID zurück."""
        new_id = self.db.execute_query(
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
            return_lastrowid=True,
        )
        employee.id = new_id
        return new_id if new_id is not None else 0

    def get_all(self) -> List[Employee]:
        """Gibt alle gespeicherten Mitarbeiter zurück."""
        rows = self.db.execute_query(
            """
            SELECT id, first_name, last_name, email, phone, department, birth_date, hire_date, status
            FROM employees
            ORDER BY id ASC
            """,
            fetch=True,
        ) or []
        return [self._row_to_employee(row) for row in rows]

    def get_by_id(self, employee_id: int) -> Optional[Employee]:
        """Sucht einen Mitarbeiter anhand seiner ID."""
        rows = self.db.execute_query(
            """
            SELECT id, first_name, last_name, email, phone, department, birth_date, hire_date, status
            FROM employees
            WHERE id = ?
            """,
            (employee_id,),
            fetch=True,
        ) or []
        return self._row_to_employee(rows[0]) if rows else None

    def update(self, employee: Employee) -> None:
        """Aktualisiert einen bestehenden Mitarbeiter anhand seiner ID."""
        if employee.id is None:
            raise ValueError("Mitarbeiter ohne ID kann nicht aktualisiert werden.")

        self.db.execute_query(
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

    def delete(self, employee_id: int) -> None:
        """Löscht einen Mitarbeiter anhand seiner ID."""
        self.db.execute_query(
            """
            DELETE FROM employees
            WHERE id = ?
            """,
            (employee_id,),
        )

    def add_validation_result(self, result: ValidationResult) -> None:
        """Speichert ein Validierungsergebnis in der Datenbank."""
        severity_value = getattr(result.severity, "value", result.severity)
        self.db.execute_query(
            """
            INSERT INTO validation_results (employee_id, column_name, error_message, severity)
            VALUES (?, ?, ?, ?)
            """,
            (result.employee_id, result.field, result.message, str(severity_value)),
        )

    def get_all_validation_results(self) -> List[ValidationResult]:
        """Lädt alle gespeicherten Validierungsergebnisse."""
        rows = self.db.execute_query(
            """
            SELECT employee_id, column_name, error_message, severity
            FROM validation_results
            ORDER BY id ASC
            """,
            fetch=True,
        ) or []
        results: List[ValidationResult] = []
        for row in rows:
            results.append(
                ValidationResult(
                    employee_id=self._get_col(row, "employee_id", 0),
                    field=self._get_col(row, "column_name", 1, "") or "",
                    message=self._get_col(row, "error_message", 2, "") or "",
                    severity=self._get_col(row, "severity", 3, "ERROR") or "ERROR",
                )
            )
        return results

    def clear_validation_results(self) -> None:
        """Löscht alle bisherigen Validierungsergebnisse (z. B. vor einem neuen Lauf)."""
        self.db.execute_query("DELETE FROM validation_results")

    def add_import_history(
        self, filename: str, import_date: str, records_imported: int, records_rejected: int
    ) -> None:
        """Speichert einen Eintrag in der Import-Historie."""
        self.db.execute_query(
            """
            INSERT INTO import_history (filename, import_date, records_imported, records_rejected)
            VALUES (?, ?, ?, ?)
            """,
            (filename, import_date, records_imported, records_rejected),
        )

    def get_import_history(self) -> List[dict]:
        """Gibt alle Einträge der Import-Historie zurück."""
        rows = self.db.execute_query(
            """
            SELECT id, filename, import_date, records_imported, records_rejected
            FROM import_history
            ORDER BY id DESC
            """,
            fetch=True,
        ) or []
        return [
            {
                "id": self._get_col(row, "id", 0),
                "filename": self._get_col(row, "filename", 1, "") or "",
                "import_date": self._get_col(row, "import_date", 2, "") or "",
                "records_imported": self._get_col(row, "records_imported", 3, 0) or 0,
                "records_rejected": self._get_col(row, "records_rejected", 4, 0) or 0,
            }
            for row in rows
        ]