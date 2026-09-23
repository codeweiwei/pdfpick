from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable

from pypdf import PdfReader, PdfWriter


class PdfPickError(Exception):
    """Base error presented to the user."""


class UnsupportedEncryptedPdfError(PdfPickError):
    """Raised when a PDF requires a password."""


class InvalidPdfError(PdfPickError):
    """Raised when a PDF cannot be parsed."""


class SelectionState(Enum):
    NONE = 0
    PARTIAL = 1
    ALL = 2


@dataclass(frozen=True)
class PdfInfo:
    path: Path
    page_count: int


def indices_for_parity(page_count: int, odd: bool) -> set[int]:
    """Return zero-based indices for human-facing odd or even page numbers."""
    start = 0 if odd else 1
    return set(range(start, page_count, 2))


def parity_state(selected: set[int], page_count: int, odd: bool) -> SelectionState:
    group = indices_for_parity(page_count, odd)
    if not group or not (selected & group):
        return SelectionState.NONE
    if group <= selected:
        return SelectionState.ALL
    return SelectionState.PARTIAL


def set_parity(
    selected: set[int], page_count: int, odd: bool, enabled: bool
) -> set[int]:
    result = set(selected)
    group = indices_for_parity(page_count, odd)
    if enabled:
        result.update(group)
    else:
        result.difference_update(group)
    return result


def default_output_path(source: str | Path) -> Path:
    path = Path(source)
    return path.with_name(f"{path.stem}_selected.pdf")


def inspect_pdf(source: str | Path) -> PdfInfo:
    path = Path(source).resolve()
    if not path.is_file():
        raise InvalidPdfError("找不到來源 PDF 檔案。")
    try:
        reader = PdfReader(path)
        if reader.is_encrypted:
            raise UnsupportedEncryptedPdfError("目前不支援密碼保護的 PDF。")
        page_count = len(reader.pages)
    except UnsupportedEncryptedPdfError:
        raise
    except Exception as exc:
        raise InvalidPdfError("無法讀取這個 PDF，檔案可能已損壞或格式不受支援。") from exc
    if page_count == 0:
        raise InvalidPdfError("這個 PDF 沒有可用的頁面。")
    return PdfInfo(path=path, page_count=page_count)


def export_selected_pages(
    source: str | Path, destination: str | Path, selected: Iterable[int]
) -> int:
    source_path = Path(source).resolve()
    destination_path = Path(destination).resolve()
    ordered = (
        sorted(selected) if isinstance(selected, (set, frozenset))
        else list(dict.fromkeys(selected))
    )
    if not ordered:
        raise ValueError("請至少選取一頁。")
    if source_path == destination_path:
        raise ValueError("輸出檔案不可覆蓋來源 PDF。")
    if not source_path.is_file():
        raise FileNotFoundError("找不到來源 PDF 檔案。")

    destination_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        reader = PdfReader(source_path)
        if reader.is_encrypted:
            raise UnsupportedEncryptedPdfError("目前不支援密碼保護的 PDF。")
        page_count = len(reader.pages)
        if any(page < 0 or page >= page_count for page in ordered):
            raise IndexError("選取的頁碼超出來源 PDF 範圍。")

        writer = PdfWriter()
        for page_index in ordered:
            writer.add_page(reader.pages[page_index])
        if reader.metadata:
            metadata = {
                str(key): str(value)
                for key, value in reader.metadata.items()
                if key and value is not None
            }
            if metadata:
                writer.add_metadata(metadata)

        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".pdf", prefix=".pdfpick-", dir=destination_path.parent,
            delete=False,
        ) as stream:
            temp_path = Path(stream.name)
            writer.write(stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_path, destination_path)
        temp_path = None
        return len(ordered)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
