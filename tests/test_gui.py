from pathlib import Path

from PySide6.QtCore import Qt
from pypdf import PdfWriter

from pdfpick.app import MainWindow, load_app_icon


def test_initial_controls(qtbot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)
    assert window.zoom_slider.minimum() == 25
    assert window.zoom_slider.maximum() == 200
    assert window.zoom_slider.value() == 100
    assert not window.export_button.isEnabled()
    assert not window.odd_checkbox.isEnabled()
    assert not load_app_icon().isNull()


def test_page_selection_updates_bulk_states(qtbot, monkeypatch, tmp_path: Path) -> None:
    source = tmp_path / "sample.pdf"
    writer = PdfWriter()
    for _ in range(4):
        writer.add_blank_page(width=300, height=420)
    with source.open("wb") as stream:
        writer.write(stream)

    window = MainWindow()
    qtbot.addWidget(window)
    monkeypatch.setattr(window, "_queue_all_renders", lambda: None)
    window.session_id = 1
    window._pdf_loaded(1, source, 4)

    window.page_cards[0].checkbox.click()
    assert window.selected_pages == {0}
    assert window.odd_checkbox.checkState() == Qt.CheckState.PartiallyChecked
    assert window.export_button.isEnabled()

    window.odd_checkbox.click()
    assert {0, 2} <= window.selected_pages
    assert window.odd_checkbox.checkState() == Qt.CheckState.Checked


def test_zoom_is_debounced(qtbot, monkeypatch) -> None:
    window = MainWindow()
    qtbot.addWidget(window)
    calls = []
    monkeypatch.setattr(window, "_queue_all_renders", lambda: calls.append(True))
    window.source_path = Path("sample.pdf")
    window.page_count = 1
    window._create_page_cards()

    window.zoom_slider.setValue(120)
    window.zoom_slider.setValue(140)
    qtbot.wait(300)
    assert calls == [True]
    assert window.zoom_label.text() == "140%"


def test_pdf_loads_and_renders_page_previews(qtbot, tmp_path: Path) -> None:
    source = tmp_path / "preview.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=300, height=420)
    writer.add_blank_page(width=420, height=300)
    with source.open("wb") as stream:
        writer.write(stream)

    window = MainWindow()
    qtbot.addWidget(window)
    window.load_pdf(source)

    qtbot.waitUntil(lambda: len(window.page_cards) == 2, timeout=5_000)
    qtbot.waitUntil(
        lambda: all(not card.preview.pixmap().isNull() for card in window.page_cards),
        timeout=10_000,
    )
    assert window.path_label.text() == str(source.resolve())
    assert window.page_cards[0].preview.pixmap().width() == 400
