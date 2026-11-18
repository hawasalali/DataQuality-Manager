import csv
import json
from models.employee import Employee

def export_to_csv(employees: list[Employee], file_path: str):
    with open(file_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Name", "E-Mail", "Telefon", "Abteilung",
            "Einstellungsdatum", "Valid", "Fehler"
        ])
        for emp in employees:
            writer.writerow([
                emp.name,
                emp.email,
                emp.phone,
                emp.department,
                emp.hire_date,
                "Ja" if emp.is_valid else "Nein",
                "; ".join(emp.errors) if emp.errors else "-"
            ])

def export_to_json(employees: list[Employee], file_path: str):
    data = [
        {
            "id": emp.id,
            "name": emp.name,
            "email": emp.email,
            "phone": emp.phone,
            "department": emp.department,
            "hire_date": emp.hire_date,
            "is_valid": emp.is_valid,
            "errors": emp.errors
        }
        for emp in employees
    ]
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)
