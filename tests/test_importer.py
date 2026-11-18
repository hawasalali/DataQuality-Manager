from services.csv_importer import import_csv
import os

def test_import_csv():
    test_csv = "data/test_employees.csv"
    with open(test_csv, "w") as f:
        f.write("name,email,phone,department,hire_date\nMax Mustermann,max@test.de,0123456789,IT,2020-01-01\n")

    employees = import_csv(test_csv)
    assert len(employees) == 1
    assert employees[0].name == "Max Mustermann"

    os.remove(test_csv)
