from pathlib import Path

import pytest
from pypdf import PdfReader, PdfWriter

from pdfpick.core import (
    InvalidPdfError,
    SelectionState,
    UnsupportedEncryptedPdfError,
    default_output_path,
    export_selected_pages,
    inspect_pdf,
    parity_state,
    set_parity,
)


def make_pdf(path: Path, widths: list[int]) -> None:
    writer = PdfWriter()
    for width in widths:
        writer.add_blank_page(width=width, height=width + 100)
    with path.open("wb") as stream:
        writer.write(stream)


def test_parity_selection_and_state() -> None:
    selected = set_parity(set(), 5, odd=True, enabled=True)
    assert selected == {0, 2, 4}
    assert parity_state(selected, 5, True) is SelectionState.ALL
    assert parity_state(selected, 5, False) is SelectionState.NONE

    selected.remove(2)
    assert parity_state(selected, 5, True) is SelectionState.PARTIAL
    selected = set_parity(selected, 5, odd=True, enabled=False)
    assert selected == set()


def test_default_output_path() -> None:
    assert default_output_path(Path("report.pdf")) == Path("report_selected.pdf")


def test_export_preserves_source_order_and_page_sizes(tmp_path: Path) -> None:
    source = tmp_path / "source.pdf"
    output = tmp_path / "selected.pdf"
    make_pdf(source, [200, 300, 400, 500])

    assert export_selected_pages(source, output, {3, 0, 2}) == 3
    reader = PdfReader(output)
    assert len(reader.pages) == 3
    assert [int(page.mediabox.width) for page in reader.pages] == [200, 400, 500]


def test_export_rejects_empty_selection_and_source_overwrite(tmp_path: Path) -> None:
    source = tmp_path / "source.pdf"
    make_pdf(source, [200])
    with pytest.raises(ValueError, match="至少選取"):
        export_selected_pages(source, tmp_path / "out.pdf", set())
    with pytest.raises(ValueError, match="不可覆蓋"):
        export_selected_pages(source, source, {0})


def test_inspect_rejects_invalid_and_encrypted_pdf(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.pdf"
    invalid.write_text("not a pdf", encoding="utf-8")
    with pytest.raises(InvalidPdfError):
        inspect_pdf(invalid)

    encrypted = tmp_path / "encrypted.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.encrypt("secret")
    with encrypted.open("wb") as stream:
        writer.write(stream)
    with pytest.raises(UnsupportedEncryptedPdfError):
        inspect_pdf(encrypted)


def test_export_preserves_explicit_page_order(tmp_path: Path) -> None:
    source = tmp_path / "source.pdf"
    output = tmp_path / "reordered.pdf"
    make_pdf(source, [200, 300, 400, 500])

    assert export_selected_pages(source, output, [3, 0, 2]) == 3
    reader = PdfReader(output)
    assert [int(page.mediabox.width) for page in reader.pages] == [500, 200, 400]
