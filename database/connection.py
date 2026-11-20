import logging
import sqlite3
from pathlib import Path
from typing import Any, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Eine Klasse zur Verwaltung der Datenbankverbindung."""

    def __init__(self, db_path: str = "data/dataquality.db", db_type: str = "sqlite"):
        self.db_type = db_type
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

        if self.db_type == "sqlite":
            self._initialize_sqlite()
        elif self.db_type == "mysql":
            raise NotImplementedError("MySQL-Unterstützung ist noch nicht implementiert.")
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")

        logger.info("Erfolgreich mit %s-Datenbank verbunden.", self.db_type.upper())

    def _initialize_sqlite(self) -> None:
        """Initialisiert die SQLite-Datenbankverbindung und erstellt das Datenverzeichnis."""
        try:
            db_file = Path(self.db_path)
            if str(db_file.parent) not in ("", "."):
                db_file.parent.mkdir(parents=True, exist_ok=True)

            self.conn = sqlite3.connect(str(db_file), check_same_thread=False)
            self.conn.execute("PRAGMA foreign_keys = ON;")
            self.conn.row_factory = sqlite3.Row
        except sqlite3.Error as e:
            logger.error("Fehler bei der SQLite-Verbindung: %s", e)
            raise RuntimeError(f"Konnte keine SQLite-Verbindung herstellen: {e}") from e

    def execute_query(
        self,
        query: str,
        params: Union[Tuple[Any, ...], List[Any], None] = None,
        fetch: bool = False,
        return_lastrowid: bool = False,
    ) -> Optional[Union[List[sqlite3.Row], int]]:
        """
        Führt eine SQL-Abfrage aus.
        - fetch=True: gibt eine Liste von sqlite3.Row-Objekten zurück
        - return_lastrowid=True: führt Commit aus und gibt cursor.lastrowid zurück
        - sonst: führt Commit aus und gibt None zurück
        """
        if not self.conn:
            raise RuntimeError("Keine aktive Datenbankverbindung.")

        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params or ())

            if fetch:
                rows = cursor.fetchall()
                logger.debug(
                    "Abfrage erfolgreich: %s... (Ergebnisse: %d)", query[:50], len(rows)
                )
                return rows

            self.conn.commit()
            logger.debug("Abfrage erfolgreich: %s...", query[:50])
            if return_lastrowid:
                return int(cursor.lastrowid or 0)
            return None

        except sqlite3.Error as e:
            if self.conn:
                self.conn.rollback()
            logger.error("Fehler bei der Abfrage: %s... Fehler: %s", query[:50], e)
            raise RuntimeError(f"Datenbankfehler: {e}") from e

    def close(self) -> None:
        """Schließt die Datenbankverbindung."""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("Datenbankverbindung erfolgreich geschlossen.")

    def __enter__(self) -> "DatabaseConnection":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def create_tables(self, schema_path: Optional[str] = None) -> None:
        """Erstellt die Tabellen basierend auf einem SQL-Schema."""
        if not self.conn:
            raise RuntimeError("Keine aktive Datenbankverbindung.")

        resolved_schema = (
            Path(schema_path)
            if schema_path is not None
            else Path(__file__).resolve().parent / "schema.sql"
        )

        try:
            schema = resolved_schema.read_text(encoding="utf-8")
            self.conn.executescript(schema)
            self.conn.commit()
            logger.info("Tabellen erfolgreich aus %s erstellt.", resolved_schema)

        except FileNotFoundError as e:
            logger.error("Schema-Datei nicht gefunden: %s", resolved_schema)
            raise FileNotFoundError(
                f"Die Datei {resolved_schema} wurde nicht gefunden."
            ) from e
        except sqlite3.Error as e:
            if self.conn:
                self.conn.rollback()
            logger.error("Fehler beim Erstellen der Tabellen: %s", e)
            raise RuntimeError(
                f"Fehler beim Ausführen des SQL-Schemas: {e}"
            ) from e