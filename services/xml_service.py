import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union

from models.employee import Employee

logger = logging.getLogger(__name__)


class XmlService:
    """Importiert und exportiert Mitarbeiterdaten im XML-Format."""

    def load_employees(self, xml_path: Union[str, Path]) -> List[Employee]:
        """Liest <employee>-Einträge aus einer XML-Datei ein."""
        tree = ET.parse(Path(xml_path))
        root = tree.getroot()

        records = root.findall(".//employee")
        if not records and root.tag.lower() == "employee":
            records = [root]

        employees: List[Employee] = []
        for elem in records:
            raw_id = self._read_text(elem, "id")
            emp_id: Optional[int] = int(raw_id) if raw_id.isdigit() else None

            employees.append(
                Employee(
                    id=emp_id,
                    first_name=self._read_text(elem, "first_name", "vorname"),
                    last_name=self._read_text(elem, "last_name", "nachname"),
                    email=self._read_text(elem, "email", "e-mail"),
                    phone=self._read_text(elem, "phone", "telefon"),
                    department=self._read_text(elem, "department", "abteilung"),
                    birth_date=self._read_text(elem, "birth_date", "geburtsdatum"),
                    hire_date=self._read_text(elem, "hire_date", "einstellungsdatum"),
                )
            )
        logger.info("Erfolgreich %d Mitarbeiter aus XML geladen: %s", len(employees), xml_path)
        return employees

    def export_employees(
        self,
        employees: List[Employee],
        filename: Union[str, Path] = "employees_export.xml",
        directory: Optional[Union[str, Path]] = None,
    ) -> bool:
        """Exportiert Mitarbeiter als formatierte UTF-8-XML-Datei."""
        try:
            emp_list = employees or []
            root = ET.Element(
                "employees",
                attrib={
                    "exported_at": datetime.now().isoformat(),
                    "total": str(len(emp_list)),
                },
            )
            for emp in emp_list:
                emp_el = ET.SubElement(root, "employee")
                fields = {
                    "id": "" if emp.id is None else str(emp.id),
                    "first_name": emp.first_name or "",
                    "last_name": emp.last_name or "",
                    "email": emp.email or "",
                    "phone": emp.phone or "",
                    "department": emp.department or "",
                    "birth_date": emp.birth_date or "",
                    "hire_date": emp.hire_date or "",
                    "status": (emp.status or "VALID").upper(),
                }
                for key, val in fields.items():
                    child = ET.SubElement(emp_el, key)
                    child.text = val

            ET.indent(root, space="  ")
            out_path = Path(filename)
            if directory is not None:
                dir_path = Path(directory)
                dir_path.mkdir(parents=True, exist_ok=True)
                out_path = dir_path / out_path.name
            elif str(out_path.parent) not in ("", "."):
                out_path.parent.mkdir(parents=True, exist_ok=True)

            ET.ElementTree(root).write(out_path, encoding="utf-8", xml_declaration=True)
            logger.info("XML-Export erfolgreich gespeichert: %s", out_path)
            return True
        except Exception as e:
            logger.error("Fehler beim XML-Export: %s", e)
            return False

    @staticmethod
    def _read_text(node: ET.Element, *names: str) -> str:
        for name in names:
            child = node.find(name)
            if child is not None and child.text:
                return child.text.strip()
        return ""