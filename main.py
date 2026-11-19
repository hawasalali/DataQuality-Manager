import sys
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon
from ui.main_window import MainWindow

# Logging einrichten
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("dataquality_manager.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def setup_application() -> None:
    """Setzt die Anwendung auf und überprüft die Verzeichnisstruktur."""
    logger.info("Starte Anwendung...")

    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    logger.info(f"Datenverzeichnis: {data_dir.absolute()}")

    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    logger.info(f"Berichtsverzeichnis: {reports_dir.absolute()}")

    db_path = data_dir / "dataquality.db"
    if not db_path.exists():
        logger.warning(f"Datenbank nicht gefunden: {db_path}. Wird neu erstellt.")
    else:
        logger.info(f"Datenbank gefunden: {db_path}")


def show_startup_message() -> None:
    """Zeigt eine Willkommensmeldung beim Start an."""
    message = """
    <h2>Willkommen beim DataQuality Manager!</h2>
    <p>Diese Anwendung hilft Ihnen bei der Verwaltung und Validierung von Mitarbeiterdaten.</p>
    <p>Version: 1.0.0</p>
    """
    QMessageBox.information(
        None,
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


def main() -> None:
    """Startet die PyQt6-Anwendung mit erweiterter Fehlerbehandlung und Logging."""
    app = None
    try:
        sys.excepthook = handle_exception

        app = QApplication(sys.argv)
        app.setApplicationName("DataQuality Manager")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("DataQuality Team")
        app.setOrganizationDomain("dataquality.local")
        app.setWindowIcon(QIcon.fromTheme("applications-development"))

        setup_application()

        window = MainWindow()
        show_startup_message()
        window.show()

        logger.info("Anwendung erfolgreich gestartet.")
        sys.exit(app.exec())

    except Exception as e:
        logger.error(f"Fehler beim Starten der Anwendung: {e}", exc_info=True)
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
