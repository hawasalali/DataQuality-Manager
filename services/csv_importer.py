import csv
import logging
from pathlib import Path
from typing import List, Optional, Union, Dict, Tuple
from models.employee import Employee

logger = logging.getLogger(__name__)


class CsvImporter:
    """Ein Importer für Mitarbeiterdaten aus CSV-Dateien."""

    REQUIRED_COLUMNS: List[str] = [
        "first_name",
        "last_name",
        "email",
    ]

    OPTIONAL_COLUMNS: List[str] = [
        "phone",
        "department",
        "birth_date",
        "hire_date",
    ]

    SUPPORTED_ENCODINGS: List[str] = ["utf-8-sig", "utf-8", "latin-1", "iso-8859-1"]

    def __init__(self, default_encoding: str = "utf-8"):
        self.default_encoding = default_encoding

    def load_rows(
        self, filepath: Union[str, Path]
    ) -> Tuple[Optional[List[str]], List[Dict[str, str]], Optional[str]]:
        """
        Lädt eine CSV-Datei mit automatischer Kodierungs-Erkennung.

        Returns:
            Tuple aus (Header-Liste, Zeilen als Dict-Liste, Fehlermeldung oder None)
        """
        path = Path(filepath)
        if not path.exists():
            msg = f"Datei nicht gefunden: {path}"
            logger.error(msg)
            return None, [], msg

        for encoding in self.SUPPORTED_ENCODINGS:
            try:
                with open(path, mode="r", encoding=encoding, newline="") as f:
                    sample = f.read(2048)
                    f.seek(0)
                    delimiter = ";" if sample.count(";") > sample.count(",") else ","
                    reader = csv.DictReader(f, delimiter=delimiter)
                    if not reader.fieldnames:
                        return None, [], "Die CSV-Datei ist leer oder hat keine Kopfzeile."

                    headers = [h.strip() for h in reader.fieldnames if h is not None]
                    rows: List[Dict[str, str]] = []
                    for row in reader:
                        cleaned_row = {
                            (k.strip() if k else ""): (v.strip() if v is not None else "")
                            for k, v in row.items()
                        }
                        rows.append(cleaned_row)

                logger.info(f"Datei erfolgreich mit Kodierung '{encoding}' geladen: {path}")
                return headers, rows, None
            except UnicodeDecodeError:
                continue
            except Exception as e:
                msg = f"Fehler beim Lesen der CSV-Datei: {e}"
                logger.error(msg)
                return None, [], msg

        msg = "Konnte die CSV-Datei mit keiner unterstützten Kodierung lesen."
        logger.error(msg)
        return None, [], msg

    def validate_headers(self, headers: Optional[List[str]]) -> List[str]:
        """Prüft, ob alle Pflichtspalten vorhanden sind. Gibt fehlende Spalten zurück."""
        if not headers:
            return self.REQUIRED_COLUMNS.copy()
        return [col for col in self.REQUIRED_COLUMNS if col not in headers]

    def preview_csv(
        self, filepath: Union[str, Path], limit: int = 10
    ) -> Tuple[List[str], List[Dict[str, str]], Optional[str]]:
        """Liefert Kopfzeile und die ersten Zeilen für die Import-Vorschau."""
        headers, rows, error = self.load_rows(filepath)
        if error:
            return [], [], error
        missing = self.validate_headers(headers)
        if missing:
            return headers or [], [], f"Fehlende Pflichtspalten: {', '.join(missing)}"
        return headers or [], rows[:limit], None

    def import_employees(self, filepath: Union[str, Path]) -> List[Employee]:
        """Importiert Mitarbeiterdaten aus einer CSV-Datei als Liste von Employee-Objekten."""
        headers, rows, error = self.load_rows(filepath)
        if error:
            logger.error(error)
            return []

        missing_columns = self.validate_headers(headers)
        if missing_columns:
            logger.error(f"Fehlende Spalten in der CSV-Datei: {missing_columns}")
            return []

        employees: List[Employee] = []
        for row in rows:
            employee = Employee(
                first_name=row.get("first_name", ""),
                last_name=row.get("last_name", ""),
                email=row.get("email", ""),
                phone=row.get("phone", ""),
                department=row.get("department", ""),
                birth_date=row.get("birth_date", ""),
                hire_date=row.get("hire_date", ""),
            )
            employees.append(employee)

        logger.info(f"Erfolgreich {len(employees)} Mitarbeiter aus {filepath} eingelesen.")
        return employees
