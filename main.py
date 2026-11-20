import logging
import sys
from pathlib import Path
from typing import Optional

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMessageBox

from ui.main_window import MainWindow

PROJECT_ROOT = Path(__file__).resolve().parent
logger = logging.getLogger(__name__)


def configure_logging() -> None:
    """Richtet das Logging einmalig mit Datei- und Konsolenausgabe ein."""
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return

    log_file = PROJECT_ROOT / "dataquality_manager.log"
    root_logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)


def setup_application() -> Path:
    """Setzt die Anwendung auf und überprüft die Verzeichnisstruktur."""
    logger.info("Starte Anwendung...")

    data_dir = PROJECT_ROOT / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Datenverzeichnis: %s", data_dir)

    reports_dir = PROJECT_ROOT / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Berichtsverzeichnis: %s", reports_dir)

    db_path = data_dir / "dataquality.db"
    if not db_path.exists():
        logger.warning("Datenbank nicht gefunden: %s. Wird neu erstellt.", db_path)
    else:
        logger.info("Datenbank gefunden: %s", db_path)

    return db_path


def show_startup_message(parent=None) -> None:
    """Zeigt eine Willkommensmeldung beim Start an."""
    message = """
    <h2>Willkommen beim DataQuality Manager!</h2>
    <p>Diese Anwendung hilft Ihnen bei der Verwaltung und Validierung von Mitarbeiterdaten.</p>
    <p>Version: 1.0.0</p>
    """
    QMessageBox.information(
        parent,
        "DataQuality Manager - Willkommen",
        message,
        QMessageBox.StandardButton.Ok,
    )


def handle_exception(exc_type, exc_value, exc_traceback) -> None:
    """Behandelt nicht abgefangene Exceptions und zeigt eine Fehlermeldung an."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.error(
        "Nicht abgefangene Exception aufgetreten!",
        exc_info=(exc_type, exc_value, exc_traceback),
    )

    if QApplication.instance() is not None:
        error_message = f"""
        <h2>Ein schwerwiegender Fehler ist aufgetreten!</h2>
        <p>Die Anwendung wird beendet.</p>
        <p><b>Details:</b></p>
        <pre>{exc_value}</pre>
        """
        QMessageBox.critical(
            None,
            "Schwerwiegender Fehler",
            error_message,
            QMessageBox.StandardButton.Ok,
        )

    sys.exit(1)


def main(show_welcome: bool = False) -> None:
    """Startet die PyQt6-Anwendung mit erweiterter Fehlerbehandlung und Logging."""
    configure_logging()
    app: Optional[QApplication] = None

    try:
        sys.excepthook = handle_exception

        app = QApplication(sys.argv)
        app.setApplicationName("DataQuality Manager")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("DataQuality Team")
        app.setOrganizationDomain("dataquality.local")
        app.setWindowIcon(QIcon.fromTheme("applications-development"))

        db_path = setup_application()

        from database.connection import DatabaseConnection

        db = DatabaseConnection(str(db_path))
        db.create_tables(str(PROJECT_ROOT / "database" / "schema.sql"))

        window = MainWindow(db=db)
        window.show()

        if show_welcome:
            show_startup_message(parent=window)

        logger.info("Anwendung erfolgreich gestartet.")
        sys.exit(app.exec())

    except Exception as e:
        logger.error("Fehler beim Starten der Anwendung: %s", e, exc_info=True)
        if QApplication.instance() is not None:
            QMessageBox.critical(
                None,
                "Startfehler",
                f"Die Anwendung konnte nicht gestartet werden:\n{e}",
                QMessageBox.StandardButton.Ok,
            )
        sys.exit(1)


if __name__ == "__main__":
    main()