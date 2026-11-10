from __future__ import annotations

from pathlib import Path


def pdf_to_text(path: Path) -> str:
    """Layout-preserving text, equivalent to `pdftotext -layout`."""
    import pdfplumber

    with pdfplumber.open(path) as pdf:
        return "\n".join((page.extract_text(layout=True) or "") for page in pdf.pages)
