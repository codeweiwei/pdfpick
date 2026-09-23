from __future__ import annotations

from PySide6.QtCore import QMimeData, Qt, Signal
from PySide6.QtGui import QDrag, QDragEnterEvent, QDragMoveEvent, QDropEvent, QImage, QMouseEvent, QPixmap
from PySide6.QtWidgets import QApplication, QCheckBox, QFrame, QHBoxLayout, QLabel, QVBoxLayout


class DragLabel(QLabel):
    drag_requested = Signal()

    def __init__(self, text: str) -> None:
        super().__init__(text)
        self._press_position = None
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setToolTip("拖曳到另一頁可調整順序")

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_position = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if (
            self._press_position is not None
            and event.buttons() & Qt.MouseButton.LeftButton
            and (event.position().toPoint() - self._press_position).manhattanLength()
            >= QApplication.startDragDistance()
        ):
            self._press_position = None
            self.drag_requested.emit()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._press_position = None
        super().mouseReleaseEvent(event)


class PageCard(QFrame):
    selection_changed = Signal(int, bool)
    reorder_requested = Signal(int, int)
    DRAG_MIME_TYPE = "application/x-pdfpick-page"

    def __init__(self, page_index: int, target_width: int) -> None:
        super().__init__()
        self.page_index = page_index
        self.target_width = target_width
        self.setObjectName("pageCard")
        self.setFixedWidth(target_width + 24)
        self.setAcceptDrops(True)

        self.checkbox = QCheckBox(f"第 {page_index + 1} 頁")
        self.checkbox.clicked.connect(
            lambda checked: self.selection_changed.emit(self.page_index, checked)
        )
        self.drag_handle = DragLabel("☰ 拖曳排序")
        self.drag_handle.drag_requested.connect(self._start_drag)
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.addWidget(self.checkbox)
        header.addStretch()
        header.addWidget(self.drag_handle)

        self.preview = DragLabel("載入中…")
        self.preview.drag_requested.connect(self._start_drag)
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumHeight(max(80, int(target_width * 1.3)))
        self.preview.setFixedWidth(target_width)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(11, 9, 11, 11)
        layout.setSpacing(8)
        layout.addLayout(header)
        layout.addWidget(self.preview, alignment=Qt.AlignmentFlag.AlignHCenter)

    def _start_drag(self) -> None:
        drag = QDrag(self)
        mime = QMimeData()
        mime.setData(self.DRAG_MIME_TYPE, str(self.page_index).encode("ascii"))
        drag.setMimeData(mime)
        drag.exec(Qt.DropAction.MoveAction)

    def _drag_source(self, event: QDragEnterEvent | QDragMoveEvent | QDropEvent) -> PageCard | None:
        source = event.source()
        if (
            isinstance(source, PageCard)
            and source is not self
            and source.window() is self.window()
            and event.mimeData().hasFormat(self.DRAG_MIME_TYPE)
        ):
            return source
        return None

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if self._drag_source(event) is not None:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if self._drag_source(event) is not None:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        source = self._drag_source(event)
        if source is None:
            event.ignore()
            return
        self.reorder_requested.emit(source.page_index, self.page_index)
        event.acceptProposedAction()

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
