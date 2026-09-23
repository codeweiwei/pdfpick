from __future__ import annotations

from PySide6.QtCore import QObject, Qt, Slot
from PySide6.QtGui import QColor, QGuiApplication, QPalette
from PySide6.QtWidgets import QApplication


class ThemeController(QObject):
    def __init__(self, app: QApplication) -> None:
        super().__init__(app)
        self.app = app
        hints = QGuiApplication.styleHints()
        if hasattr(hints, "colorSchemeChanged"):
            hints.colorSchemeChanged.connect(self.apply)
        self.apply()

    @Slot()
    def apply(self, *_args: object) -> None:
        scheme = QGuiApplication.styleHints().colorScheme()
        dark = scheme == Qt.ColorScheme.Dark
        palette = QPalette()
        colors = (
            {
                QPalette.ColorRole.Window: "#202124",
                QPalette.ColorRole.WindowText: "#f1f3f4",
                QPalette.ColorRole.Base: "#17181a",
                QPalette.ColorRole.AlternateBase: "#292a2d",
                QPalette.ColorRole.Text: "#f1f3f4",
                QPalette.ColorRole.Button: "#303134",
                QPalette.ColorRole.ButtonText: "#f1f3f4",
                QPalette.ColorRole.Highlight: "#8ab4f8",
                QPalette.ColorRole.HighlightedText: "#202124",
                QPalette.ColorRole.PlaceholderText: "#9aa0a6",
            }
            if dark
            else {
                QPalette.ColorRole.Window: "#f5f6f8",
                QPalette.ColorRole.WindowText: "#202124",
                QPalette.ColorRole.Base: "#ffffff",
                QPalette.ColorRole.AlternateBase: "#eef0f3",
                QPalette.ColorRole.Text: "#202124",
                QPalette.ColorRole.Button: "#ffffff",
                QPalette.ColorRole.ButtonText: "#202124",
                QPalette.ColorRole.Highlight: "#0b57d0",
                QPalette.ColorRole.HighlightedText: "#ffffff",
                QPalette.ColorRole.PlaceholderText: "#6f7378",
            }
        )
        for role, color in colors.items():
            palette.setColor(role, QColor(color))
        palette.setColor(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.ButtonText,
            QColor("#777b80" if dark else "#9aa0a6"),
        )
        self.app.setPalette(palette)
        border = "#4a4d51" if dark else "#d5d8dc"
        card = "#292a2d" if dark else "#ffffff"
        slider_track = "#5f6368" if dark else "#c4c7c5"
        slider_fill = "#8ab4f8" if dark else "#0b57d0"
        slider_handle = "#aecbfa" if dark else "#0b57d0"
        self.app.setStyleSheet(
            f"""
            QFrame#pageCard {{ background: {card}; border: 1px solid {border};
                               border-radius: 8px; }}
            QFrame#pageCard QLabel, QFrame#pageCard QCheckBox {{ border: none; }}
            QPushButton {{ min-height: 30px; padding: 2px 12px; }}
            QScrollArea {{ border: 1px solid {border}; border-radius: 6px; }}
            QSlider::groove:horizontal {{ height: 6px; background: {slider_track};
                                          border-radius: 3px; }}
            QSlider::sub-page:horizontal {{ background: {slider_fill};
                                            border-radius: 3px; }}
            QSlider::add-page:horizontal {{ background: {slider_track};
                                            border-radius: 3px; }}
            QSlider::handle:horizontal {{ background: {slider_handle};
                                          border: 1px solid {slider_fill};
                                          border-radius: 9px; width: 18px;
                                          margin: -6px 0; }}
            """
        )
