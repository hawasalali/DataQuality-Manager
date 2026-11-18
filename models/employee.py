class Employee:
    def __init__(self, id: int, name: str, email: str, phone: str, department: str, hire_date: str, is_valid: bool = False, errors: list[str] = None):
        self.id = id
        self.name = name
        self.email = email
        self.phone = phone
        self.department = department
        self.hire_date = hire_date
        self.is_valid = is_valid
        self.errors = errors if errors is not None else []

    def __str__(self):
        return f"Employee(id={self.id}, name='{self.name}', email='{self.email}', is_valid={self.is_valid})"
