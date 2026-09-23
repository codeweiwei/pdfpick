# PDF 選頁重組工具

使用 PySide6 製作的 Windows 桌面工具，可預覽 PDF、勾選指定頁面，並依原始順序輸出成新的 PDF。預覽縮圖不會影響輸出品質。

## 安裝與啟動

需要 Python 3.11 以上版本及 [uv](https://docs.astral.sh/uv/)。

```powershell
uv sync
uv run pdfpick
```

## 操作方式

1. 按「選取 PDF」開啟來源檔案。
2. 點選各頁左上角的核取方塊，或使用「單數頁」「雙數頁」批次選取。
3. 使用左下角滑桿調整 25%–200% 預覽比例；100% 對應 Windows 的 96 DPI 顯示尺度。
4. 按「輸出選取頁面」並指定新 PDF 的儲存位置。

密碼保護的 PDF 暫不支援。輸出頁面固定依來源文件順序排列。

## 測試

```powershell
uv run pytest
```

## 開發與維護

目前架構、背景預覽協定、縮放定義、輸出安全機制與修改入口整理於 [實作與維護指南](docs/IMPLEMENTATION.md)。
