"""Escalate only when the cheap model demonstrably failed.

Measured on this corpus, the capability boundary between a 1B and a 4B vision model
is not "bigger is better". It is specific:

    minicpm-v4.6 (1B)   labelled charts  10/10     unlabelled charts   0/10    ~19s/page
    qwen3.5:4b  (4B)    labelled charts  10/10     unlabelled charts  reads    ~150s/page

Reading a printed data label is recognition. Reading a value off an axis is spatial
reasoning about where a point sits between gridlines - a different task, and the small
model cannot do it at all. It does not guess badly; it returns no numbers.

That failure being *loud* is what makes cheap-first viable. The escalation trigger
needs no ground truth: if a page's transcription mentions a chart and contains no
numeric values, the cheap model has told us it could not read the exhibit, and only
then is the 8x slower model worth waking.

So the default path costs ~19s/page and the expensive model runs on the handful of
pages that actually need it. Same idea as the human escalation ladder elsewhere in
this pipeline: do the cheap thing, detect failure honestly, escalate on evidence.
"""

from __future__ import annotations

import re
from pathlib import Path

from . import vision
from .base import ParsedDocument, ParsedPage

CHEAP_MODEL = "minicpm-v4.6:latest"
STRONG_MODEL = "qwen3.5:4b"

_NUMERIC = re.compile(r"\d+(?:\.\d+)?\s?%|\$\s?\d")
_EXHIBIT = re.compile(r"chart|graph|figure|exhibit|plot|axis", re.I)


def needs_escalation(text: str) -> tuple[bool, str]:
    """Did the cheap model fail in the way that a stronger one would fix?

    Ground-truth free by design. We are asking what the transcription says about
    itself, not comparing it to an answer key - the trigger has to work on documents
    nobody has labelled.
    """
    if not text.strip():
        return True, "empty transcription"
    if _EXHIBIT.search(text) and not _NUMERIC.search(text):
        return True, "mentions an exhibit but reports no values"
    if "unreadable" in text.lower():
        return True, "model reported a value as unreadable"
    return False, ""


def parse(pdf_path: Path, pages: list[int] | None = None,
          cheap: str = CHEAP_MODEL, strong: str = STRONG_MODEL,
          use_cache: bool = True) -> ParsedDocument:
    """Cheap model first; strong model only on pages that failed loudly."""
    base = vision.parse(pdf_path, pages=pages, model=cheap, use_cache=use_cache)
    if not base.pages:
        return base

    out: list[ParsedPage] = []
    escalated: list[int] = []
    for p in base.pages:
        need, why = needs_escalation(p.text)
        if not need:
            p.meta["tier"] = "cheap"
            out.append(p)
            continue
        up = vision.parse(pdf_path, pages=[p.page_number], model=strong,
                          use_cache=use_cache)
        got = up.page(p.page_number)
        if got and got.text.strip():
            got.meta.update({"tier": "escalated", "escalated_because": why,
                             "cheap_model": cheap})
            out.append(got)
            escalated.append(p.page_number)
        else:
            p.meta.update({"tier": "cheap", "escalation_attempted": True,
                           "escalated_because": why})
            out.append(p)

    return ParsedDocument(
        source=Path(pdf_path), pages=out, backend=f"tiered:{cheap}->{strong}",
        notes=(f"Cheap-first vision. {len(out) - len(escalated)} page(s) answered by "
               f"{cheap}; {len(escalated)} escalated to {strong} "
               f"{escalated if escalated else ''}."))
