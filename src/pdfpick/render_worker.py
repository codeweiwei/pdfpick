from __future__ import annotations

import json
import sys
from pathlib import Path

import pypdfium2 as pdfium


def render_document(source: Path, scale: float, output_dir: Path, generation: int) -> None:
    document = pdfium.PdfDocument(str(source))
    try:
        for page_index in range(len(document)):
            page = document[page_index]
            try:
                bitmap = page.render(scale=max(scale, 0.1))
                try:
                    image = bitmap.to_pil().convert("RGB")
                    output = output_dir / f"g{generation}-p{page_index}.png"
                    image.save(output, "PNG")
                finally:
                    bitmap.close()
            finally:
                page.close()
            print(json.dumps({
                "type": "page", "generation": generation,
                "page": page_index, "path": str(output),
            }), flush=True)
    finally:
        document.close()


def serve() -> int:
    print(json.dumps({"type": "ready"}), flush=True)
    for line in sys.stdin:
        request: dict[str, object] = {}
        try:
            request = json.loads(line)
            render_document(
                Path(request["source"]), float(request["scale"]),
                Path(request["output_dir"]), int(request["generation"]),
            )
            print(json.dumps({
                "type": "done", "generation": int(request["generation"]),
            }), flush=True)
        except Exception as exc:
            print(json.dumps({
                "type": "error",
                "generation": request.get("generation", -1) if isinstance(request, dict) else -1,
                "message": str(exc),
            }), flush=True)
    return 0


def main() -> int:
    if len(sys.argv) == 2 and sys.argv[1] == "--server":
        return serve()
    if len(sys.argv) != 5:
        print("invalid render worker arguments", file=sys.stderr)
        return 2
    try:
        render_document(
            Path(sys.argv[1]), float(sys.argv[2]), Path(sys.argv[3]), int(sys.argv[4])
        )
        return 0
    except Exception as exc:
        print(str(exc), file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
