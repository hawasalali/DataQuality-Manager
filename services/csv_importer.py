import csv
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

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

    def _encodings_to_try(self) -> List[str]:
        """Liefert die Kodierungsliste mit default_encoding zuerst (ohne Duplikate)."""
        ordered = [self.default_encoding] + list(self.SUPPORTED_ENCODINGS)
        seen = set()
        result: List[str] = []
        for enc in ordered:
            if enc and enc not in seen:
                seen.add(enc)
                result.append(enc)
        return result

    @staticmethod
    def _is_empty_row(row: Dict[str, str]) -> bool:
        """Prüft, ob eine Zeile komplett leer ist."""
        return all(not (val or "").strip() for val in row.values())

    @staticmethod
    def _detect_delimiter(sample: str) -> str:
        """Ermittelt das wahrscheinlichste Trennzeichen (; , oder Tab)."""
        counts = {
            ";": sample.count(";"),
            ",": sample.count(","),
            "\t": sample.count("\t"),
        }
        best = max(counts, key=lambda k: counts[k])
        return best if counts[best] > 0 else ","

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

        if path.is_dir():
            msg = f"Der angegebene Pfad ist ein Verzeichnis, keine CSV-Datei: {path}"
            logger.error(msg)
            return None, [], msg

        for encoding in self._encodings_to_try():
            try:
                with open(path, mode="r", encoding=encoding, newline="") as f:
                    sample = f.read(2048)
                    f.seek(0)
                    delimiter = self._detect_delimiter(sample)
                    reader = csv.DictReader(f, delimiter=delimiter)

                    if not reader.fieldnames:
                        return None, [], "Die CSV-Datei ist leer oder hat keine Kopfzeile."

                    headers = [
                        h.strip()
                        for h in reader.fieldnames
                        if h is not None and h.strip()
                    ]
                    if not headers:
                        return None, [], "Die Kopfzeile der CSV-Datei ist leer."

                    rows: List[Dict[str, str]] = []
                    for row in reader:
                        cleaned_row: Dict[str, str] = {}
                        for k, v in row.items():
                            if k is None:
                                continue
                            key = k.strip()
                            if not key:
                                continue
                            if isinstance(v, list):
                                val = ", ".join(
                                    str(item).strip()
                                    for item in v
                                    if item is not None
                                )
                            else:
                                val = v.strip() if v is not None else ""
                            cleaned_row[key] = val

                        if not self._is_empty_row(cleaned_row):
                            rows.append(cleaned_row)

                logger.info(
                    "Datei erfolgreich mit Kodierung '%s' geladen: %s (%d Zeilen)",
                    encoding,
                    path,
                    len(rows),
                )
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
            return list(self.REQUIRED_COLUMNS)
        normalized_headers = {h.strip().lower() for h in headers if h}
        return [
            col
            for col in self.REQUIRED_COLUMNS
            if col.lower() not in normalized_headers
        ]

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
        safe_limit = max(0, limit)
        return headers or [], rows[:safe_limit], None

    def import_employees(self, filepath: Union[str, Path]) -> List[Employee]:
        """Importiert Mitarbeiterdaten aus einer CSV-Datei als Liste von Employee-Objekten."""
        headers, rows, error = self.load_rows(filepath)
        if error:
            logger.error(error)
            return []

        missing_columns = self.validate_headers(headers)
        if missing_columns:
            logger.error("Fehlende Spalten in der CSV-Datei: %s", missing_columns)
            return []

        employees: List[Employee] = []
        for row in rows:
            lower_row = {k.strip().lower(): v for k, v in row.items()}
            employee = Employee(
                first_name=lower_row.get("first_name", ""),
                last_name=lower_row.get("last_name", ""),
                email=lower_row.get("email", ""),
                phone=lower_row.get("phone", ""),
                department=lower_row.get("department", ""),
                birth_date=lower_row.get("birth_date", ""),
                hire_date=lower_row.get("hire_date", ""),
            )
            employees.append(employee)

        logger.info(
            "Erfolgreich %d Mitarbeiter aus %s eingelesen.", len(employees), filepath
        )
        return employees