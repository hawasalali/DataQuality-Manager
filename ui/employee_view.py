from PyQt6.QtCore import QAbstractTableModel, Qt
from models.employee import Employee

class EmployeeTableModel(QAbstractTableModel):
    def __init__(self, employees: list[Employee]):
        super().__init__()
        self.employees = employees

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            employee = self.employees[index.row()]
            if index.column() == 0:
                return employee.name
            elif index.column() == 1:
                return employee.email
            elif index.column() == 2:
                return employee.phone
            elif index.column() == 3:
                return employee.department
            elif index.column() == 4:
                return employee.hire_date
            elif index.column() == 5:
                return "Ja" if employee.is_valid else "Nein"
            elif index.column() == 6:
                return "; ".join(employee.errors) if employee.errors else "-"

    def rowCount(self, index):
        return len(self.employees)

    def columnCount(self, index):
        return 7

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            headers = [
                "Name", "E-Mail", "Telefon", "Abteilung",
                "Einstellungsdatum", "Valid", "Fehler"
            ]
            return headers[section]
