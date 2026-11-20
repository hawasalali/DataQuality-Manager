import logging
import sys
from pathlib import Path
from typing import Optional

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMessageBox

from database.connection import DatabaseConnection
from ui.main_window import MainWindow

PROJECT_ROOT = Path(__file__).resolve().parent
logger = logging.getLogger(__name__)


def configure_logging() -> None:
    """Konfiguriert Datei- und Konsolen-Logging für die Anwendung."""
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return

    root_logger.setLevel(logging.INFO)
    log_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    file_handler = logging.FileHandler(
        PROJECT_ROOT / "dataquality_manager.log", encoding="utf-8"
    )
    file_handler.setFormatter(log_format)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(log_format)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)


def setup_application() -> Path:
    """Stellt notwendige Verzeichnisse bereit und liefert den Datenbankpfad."""
    logger.info("Starte DataQuality Manager...")
    data_dir = PROJECT_ROOT / "data"
    reports_dir = PROJECT_ROOT / "reports"
    data_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "dataquality.db"


def handle_exception(exc_type, exc_value, exc_traceback) -> None:
    """Fängt unbehandelte Exceptions sauber ab, protokolliert sie und zeigt einen Dialog."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.error(
        "Unbehandelte Exception aufgetreten!",
        exc_info=(exc_type, exc_value, exc_traceback),
    )
    if QApplication.instance() is not None:
        QMessageBox.critical(None, "Schwerwiegender Fehler", str(exc_value))
    sys.exit(1)


def main() -> None:
    """Haupteinstiegspunkt der Anwendung."""
    configure_logging()
    app: Optional[QApplication] = None
    db: Optional[DatabaseConnection] = None

    try:
        sys.excepthook = handle_exception
        app = QApplication(sys.argv)
        app.setApplicationName("DataQuality Manager")
        app.setApplicationVersion("1.0.0")
        app.setWindowIcon(QIcon.fromTheme("applications-development"))

        db_path = setup_application()
        db = DatabaseConnection(str(db_path))
        db.create_tables(str(PROJECT_ROOT / "database" / "schema.sql"))

        window = MainWindow(db=db)
        window.show()
        logger.info("Anwendung erfolgreich gestartet.")

        exit_code = app.exec()
        db.close()
        sys.exit(exit_code)

    except Exception as exc:
        logger.error("Fehler beim Starten der Anwendung: %s", exc, exc_info=True)
        if db is not None:
            db.close()
        if QApplication.instance() is not None:
            QMessageBox.critical(None, "Startfehler", str(exc))
        sys.exit(1)


if __name__ == "__main__":
    main()