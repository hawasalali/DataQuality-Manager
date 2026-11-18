import json
from models.employee import Employee

def generate_validation_report(employees: list[Employee], file_path: str):
    valid_employees = [emp for emp in employees if emp.is_valid]
    invalid_employees = [emp for emp in employees if not emp.is_valid]

    error_types = {}
    for emp in invalid_employees:
        for error in emp.errors:
            error_types[error] = error_types.get(error, 0) + 1

    report = {
        "total_employees": len(employees),
        "valid_employees": len(valid_employees),
        "invalid_employees": len(invalid_employees),
        "valid_percentage": (len(valid_employees) / len(employees)) * 100 if employees else 0,
        "errors": error_types,
        "employees": [
            {
                "name": emp.name,
                "email": emp.email,
                "is_valid": emp.is_valid,
                "errors": emp.errors
            }
            for emp in employees
        ]
    }

    with open(file_path, "w") as f:
        json.dump(report, f, indent=2)
