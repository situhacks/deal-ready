"""The shared shape every parse backend returns.

One interface, three backends, so the comparison is like-for-like. If each backend
returned its own bespoke structure the eval would be comparing our adapter code as
much as the parsers, and the resulting table would prove nothing.

Every page carries the method that produced it. When a document is parsed by more
than one backend - text layer for the prose, vision for the two chart pages - the
provenance survives into the citation, and a reviewer can see which machinery stands
behind each number.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ParsedPage:
    page_number: int          # 1-indexed, matching what a human sees in a viewer
    text: str
    method: str               # textlayer | ocr | vision
    confidence: float | None = None
    meta: dict = field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.text)


@dataclass
class ParsedDocument:
    source: Path
    pages: list[ParsedPage]
    backend: str
    notes: str = ""

    @property
    def text(self) -> str:
        return "\n\n".join(p.text for p in self.pages)

    def page(self, n: int) -> ParsedPage | None:
        for p in self.pages:
            if p.page_number == n:
                return p
        return None

    def char_count(self) -> int:
        return sum(len(p) for p in self.pages)

    def empty_pages(self) -> list[int]:
        return [p.page_number for p in self.pages if not p.text.strip()]
