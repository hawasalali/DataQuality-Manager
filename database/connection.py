import sqlite3
import logging
from pathlib import Path
from typing import Optional, List, Tuple, Any, Union

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Eine Klasse zur Verwaltung der Datenbankverbindung."""

    def __init__(self, db_path: str = "data/dataquality.db", db_type: str = "sqlite"):
        self.db_type = db_type
        self.db_path = db_path
        self.conn: Optional[Union[sqlite3.Connection, Any]] = None

        try:
            if self.db_type == "sqlite":
                self._initialize_sqlite()
            elif self.db_type == "mysql":
                raise NotImplementedError("MySQL-Unterstützung ist noch nicht implementiert.")
            else:
                raise ValueError(f"Unsupported database type: {self.db_type}")

            logger.info(f"Erfolgreich mit {self.db_type.upper()}-Datenbank verbunden.")
        except Exception as e:
            logger.error(f"Fehler bei der Initialisierung der Datenbank: {e}")
            raise

    def _initialize_sqlite(self) -> None:
        """Initialisiert die SQLite-Datenbankverbindung und erstellt das Datenverzeichnis."""
        try:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            self.conn = sqlite3.connect(self.db_path)
            self.conn.execute("PRAGMA foreign_keys = ON;")
            self.conn.row_factory = sqlite3.Row
        except sqlite3.Error as e:
            logger.error(f"Fehler bei der SQLite-Verbindung: {e}")
            raise RuntimeError(f"Konnte keine SQLite-Verbindung herstellen: {e}")

    def execute_query(
        self,
        query: str,
        params: Union[Tuple, List, None] = None,
        fetch: bool = False
    ) -> Optional[List[Any]]:
        """Führt eine SQL-Abfrage aus und gibt die Ergebnisse zurück (falls fetch=True)."""
        if not self.conn:
            raise RuntimeError("Keine aktive Datenbankverbindung.")

        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params or ())

            if fetch:
                result = cursor.fetchall()
                logger.debug(f"Abfrage erfolgreich: {query[:50]}... (Ergebnisse: {len(result)})")
                return result
            else:
                self.conn.commit()
                logger.debug(f"Abfrage erfolgreich: {query[:50]}...")
                return None

        except sqlite3.Error as e:
            self.conn.rollback()
            logger.error(f"Fehler bei der Abfrage: {query[:50]}... Fehler: {e}")
            raise RuntimeError(f"Datenbankfehler: {e}")

    def close(self) -> None:
        """Schließt die Datenbankverbindung."""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("Datenbankverbindung erfolgreich geschlossen.")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        if hasattr(self, "conn") and self.conn:
            self.close()

    def create_tables(self, schema_path: str = "database/schema.sql") -> None:
        """Erstellt die Tabellen basierend auf einem SQL-Schema."""
        if not self.conn:
            raise RuntimeError("Keine aktive Datenbankverbindung.")

        try:
            with open(schema_path, "r", encoding="utf-8") as file:
                schema = file.read()

            self.conn.executescript(schema)
            self.conn.commit()
            logger.info(f"Tabellen erfolgreich aus {schema_path} erstellt.")

        except FileNotFoundError:
            logger.error(f"Schema-Datei nicht gefunden: {schema_path}")
            raise FileNotFoundError(f"Die Datei {schema_path} wurde nicht gefunden.")
        except Exception as e:
            logger.error(f"Fehler beim Erstellen der Tabellen: {e}")
            raise RuntimeError(f"Fehler beim Ausführen des SQL-Schemas: {e}")
