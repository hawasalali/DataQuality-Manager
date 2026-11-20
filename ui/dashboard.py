from typing import Dict, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class Dashboard(QWidget):
    """Ein Dashboard zur Anzeige von Statistiken für Mitarbeiterdaten."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        show_duplicates: bool = False,
    ):
        super().__init__(parent)

        self.stats: Dict[str, int] = {
            "total": 0,
            "valid": 0,
            "warnings": 0,
            "errors": 0,
            "duplicates": 0,
        }

        main_layout = QVBoxLayout()
        stats_layout = QHBoxLayout()

        self.total_label = self._create_label("DB Total: 0")
        self.valid_label = self._create_label("Valid: 0")
        self.warning_label = self._create_label("Warnings: 0")
        self.error_label = self._create_label("Errors: 0")
        self.duplicate_label: Optional[QLabel] = (
            self._create_label("Duplicates: 0") if show_duplicates else None
        )

        stats_layout.addWidget(self.total_label)
        stats_layout.addWidget(self.valid_label)
        stats_layout.addWidget(self.warning_label)
        stats_layout.addWidget(self.error_label)

        if self.duplicate_label is not None:
            stats_layout.addWidget(self.duplicate_label)

        stats_frame = QFrame()
        stats_frame.setLayout(stats_layout)
        stats_frame.setFrameShape(QFrame.Shape.Panel)
        stats_frame.setFrameShadow(QFrame.Shadow.Raised)
        stats_frame.setLineWidth(1)
        main_layout.addWidget(stats_frame)

        self.setLayout(main_layout)
        self.setWindowTitle("Mitarbeiter-Dashboard")
        self.adjustSize()

    def _create_label(self, text: str) -> QLabel:
        """Erstellt ein QLabel mit einheitlichem Stil."""
        label = QLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        label.setStyleSheet(
            """
            QLabel {
                background-color: #f0f0f0;
                color: #111111;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
            }
            """
        )
        return label

    def update_stats(
        self,
        total: int = 0,
        valid: int = 0,
        warnings: int = 0,
        errors: int = 0,
        duplicates: int = 0,
    ) -> None:
        """Aktualisiert die Statistiken im Dashboard."""
        total_val = int(total or 0)
        valid_val = int(valid or 0)
        warnings_val = int(warnings or 0)
        errors_val = int(errors or 0)
        duplicates_val = int(duplicates or 0)

        self.stats["total"] = total_val
        self.stats["valid"] = valid_val
        self.stats["warnings"] = warnings_val
        self.stats["errors"] = errors_val
        self.stats["duplicates"] = duplicates_val

        self.total_label.setText(f"DB Total: {total_val}")
        self.valid_label.setText(f"Valid: {valid_val}")
        self.warning_label.setText(f"Warnings: {warnings_val}")
        self.error_label.setText(f"Errors: {errors_val}")

        if self.duplicate_label is not None:
            self.duplicate_label.setText(f"Duplicates: {duplicates_val}")

    def update_from_dict(self, stats_dict: Optional[Dict[str, int]]) -> None:
        """Aktualisiert das Dashboard anhand eines Statistik-Dictionaries."""
        data = stats_dict or {}
        self.update_stats(
            total=data.get("total", 0),
            valid=data.get("valid", 0),
            warnings=data.get("warnings", 0),
            errors=data.get("errors", 0),
            duplicates=data.get("duplicates", 0),
        )

    def get_stats(self) -> Dict[str, int]:
        """Gibt die aktuellen Statistiken zurück."""
        return self.stats.copy()

    def clear(self) -> None:
        """Setzt alle Statistiken auf 0 zurück."""
        self.update_stats(0, 0, 0, 0, 0)