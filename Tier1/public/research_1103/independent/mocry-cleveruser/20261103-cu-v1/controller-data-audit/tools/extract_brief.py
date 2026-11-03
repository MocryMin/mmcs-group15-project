#!/usr/bin/env python3
"""Extract the brief PDF to a page-marked text file for researcher workers."""
from __future__ import annotations

import json
import hashlib
from pathlib import Path

BUNDLE = Path(__file__).resolve().parents[1] / "inputs"
PDF = BUNDLE / "Project_Brief.pdf"
OUT = BUNDLE / "brief_extracted_text.md"


def main() -> int:
    import fitz  # PyMuPDF

    doc = fitz.open(PDF)
    parts = [
        "# Project_Brief.pdf — text extract (pages 1-{} )\n".format(doc.page_count),
        "Derived artefact: produced by `tools/extract_brief.py` with PyMuPDF {}. "
        "The PDF `Project_Brief.pdf` is authoritative; line breaks and table layout in this "
        "text extract are approximate. Page markers below follow the PDF pagination.\n".format(
            fitz.__doc__.strip().splitlines()[0] if fitz.__doc__ else "unknown"
        ),
        f"Source PDF sha256: {hashlib.sha256(PDF.read_bytes()).hexdigest()}\n",
    ]
    for i, page in enumerate(doc, start=1):
        parts.append(f"\n\n---\n\n## Page {i}\n\n" + page.get_text("text").strip() + "\n")
    text = "".join(parts)
    OUT.write_text(text, encoding="utf-8")
    meta = {
        "pdf": PDF.name,
        "pdf_sha256": hashlib.sha256(PDF.read_bytes()).hexdigest(),
        "pages": doc.page_count,
        "extract": OUT.name,
        "extract_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "extract_chars": len(text),
        "extractor": "PyMuPDF",
    }
    (BUNDLE / "brief_extract.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(meta, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
