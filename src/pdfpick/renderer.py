from __future__ import annotations

import json
import subprocess
import sys
import threading
from pathlib import Path
from typing import TextIO

from PySide6.QtCore import QObject, Signal


def start_render_backend() -> subprocess.Popen[str]:
    creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    process = subprocess.Popen(
        [sys.executable, "-m", "pdfpick.render_worker", "--server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        bufsize=1,
        creationflags=creation_flags,
    )
    assert process.stdout is not None
    ready_line = process.stdout.readline()
    try:
        ready = json.loads(ready_line)
    except json.JSONDecodeError as exc:
        process.terminate()
        raise RuntimeError("無法啟動 PDF 預覽後端。") from exc
    if ready.get("type") != "ready":
        process.terminate()
        raise RuntimeError("PDF 預覽後端未正確啟動。")
    return process


class RenderService(QObject):
    message = Signal(object)

    def __init__(self, process: subprocess.Popen[str], parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.process = process
        self._lock = threading.Lock()
        self._busy = False
        self._pending: dict[str, object] | None = None
        self._closed = False
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()

    def request(
        self, source: Path, scale: float, output_dir: Path, generation: int
    ) -> None:
        payload: dict[str, object] = {
            "source": str(source),
            "scale": scale,
            "output_dir": str(output_dir),
            "generation": generation,
        }
        with self._lock:
            if self._busy:
                self._pending = payload
                return
            self._busy = True
            self._write(payload)

    def _write(self, payload: dict[str, object]) -> None:
        stream = self.process.stdin
        if stream is None or self.process.poll() is not None:
            self.message.emit({
                "type": "error", "generation": payload["generation"],
                "message": "PDF 預覽後端已停止。",
            })
            return
        stream.write(json.dumps(payload) + "\n")
        stream.flush()

    def _read_loop(self) -> None:
        stream: TextIO | None = self.process.stdout
        if stream is None:
            return
        for line in stream:
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            self.message.emit(payload)
            if payload.get("type") in {"done", "error"}:
                with self._lock:
                    self._busy = False
                    pending = self._pending
                    self._pending = None
                    if pending is not None and not self._closed:
                        self._busy = True
                        self._write(pending)

    def close(self) -> None:
        with self._lock:
            self._closed = True
            self._pending = None
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
        for stream in (self.process.stdin, self.process.stdout, self.process.stderr):
            if stream is not None:
                stream.close()
