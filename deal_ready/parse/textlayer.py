"""Backend A - the born-digital text layer.

The cheapest correct thing, and the one most pipelines skip straight past on their
way to something impressive. Where a PDF carries real text, extracting it is lossless,
costs nothing, needs no model, and yields exact character offsets - which is what a
citation actually is.

Its ceiling is equally worth knowing: it returns the characters a page contains and
nothing about what the page *shows*. A value that exists only as pixels in a chart is
not merely hard for this backend, it is absent. That is not a bug to tune around; it
is the boundary that decides when a heavier parser earns its cost.
"""

from __future__ import annotations

from pathlib import Path

from .base import ParsedDocument, ParsedPage


def parse(pdf_path: Path) -> ParsedDocument:
    from pypdf import PdfReader

    reader = PdfReader(str(pdf_path))
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append(ParsedPage(page_number=i, text=text, method="textlayer"))
    return ParsedDocument(
        source=Path(pdf_path),
        pages=pages,
        backend="textlayer",
        notes=(
            "Born-digital extraction via pypdf. Lossless for text, blind to raster "
            "content by construction."
        ),
    )
