from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QCheckBox, QFrame, QLabel, QVBoxLayout


class PageCard(QFrame):
    selection_changed = Signal(int, bool)

    def __init__(self, page_index: int, target_width: int) -> None:
        super().__init__()
        self.page_index = page_index
        self.target_width = target_width
        self.setObjectName("pageCard")
        self.setFixedWidth(target_width + 24)

        self.checkbox = QCheckBox(f"第 {page_index + 1} 頁")
        self.checkbox.clicked.connect(
            lambda checked: self.selection_changed.emit(self.page_index, checked)
        )
        self.preview = QLabel("載入中…")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumHeight(max(80, int(target_width * 1.3)))
        self.preview.setFixedWidth(target_width)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(11, 9, 11, 11)
        layout.setSpacing(8)
        layout.addWidget(self.checkbox, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.preview, alignment=Qt.AlignmentFlag.AlignHCenter)

    def set_selected(self, selected: bool) -> None:
        self.checkbox.blockSignals(True)
        self.checkbox.setChecked(selected)
        self.checkbox.blockSignals(False)

    def set_target_width(self, width: int) -> None:
        self.target_width = width
        self.setFixedWidth(width + 24)
        self.preview.setFixedWidth(width)
        self.preview.setMinimumHeight(max(80, int(width * 1.3)))
        self.preview.setText("載入中…")
        self.preview.setPixmap(QPixmap())

    def set_image(self, image: QImage) -> None:
        pixmap = QPixmap.fromImage(image)
        self.target_width = pixmap.width()
        self.setFixedWidth(pixmap.width() + 24)
        self.preview.setMinimumHeight(0)
        self.preview.setFixedSize(pixmap.size())
        self.preview.setPixmap(pixmap)

    def set_render_error(self) -> None:
        self.preview.setMinimumHeight(max(80, int(self.target_width * 1.3)))
        self.preview.setText("無法產生預覽")
