import pandas as pd
from models.employee import Employee

def import_csv(file_path: str) -> list[Employee]:
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        employees = []
        for _, row in df.iterrows():
            employees.append(
                Employee(
                    id=None,
                    name=row.get("name", ""),
                    email=row.get("email", ""),
                    phone=row.get("phone", ""),
                    department=row.get("department", ""),
                    hire_date=row.get("hire_date", "")
                )
            )
        return employees
    except Exception as e:
        print(f"Fehler beim Import: {e}")
        return []
