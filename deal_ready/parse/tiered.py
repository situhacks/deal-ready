"""Cheap model reads the page; the strong model re-reads the exhibit.

The capability boundary between a 1B and a 4B vision model, measured on this corpus,
is not "bigger is better". It is specific:

    minicpm-v4.6 (1B)   labelled charts  9-10/10   unlabelled charts  0/10   ~19s/page
    qwen3.5:4b  (4B)    labelled charts  10/10     unlabelled charts  reads  ~150s/page

Reading a printed data label is recognition. Reading a value off an axis is spatial
reasoning about where a point sits between gridlines - a different task, and the small
model cannot do it at all. It does not guess badly; it returns no numbers.

**Why every exhibit page escalates now, when this file used to gate on loud failure.**
The v1 trigger escalated a page only when its transcription mentioned a chart AND
contained no numbers, because escalation cost 119-171s per page (thinking model, full
page render) and an unmeasured trigger spends the budget the tiering was meant to
save - the first version fired on 16 of 20 pages and two thirds of that bought
nothing. That gate had a blind spot it took a reviewer to find: a page can carry
numbers and still be misread, because the cheap model silently drops annotations
inside the chart raster (T05 p6: three bar labels transcribed, the "Top 5 customers:
28% of ARR" callout box omitted). No ground-truth-free trigger can see a missing
value on a page full of them.

The gate made sense while escalation was expensive. Then two fixes landed - the
`think` parameter at the model door, and exhibit-level reads of the PDF's native
embedded images instead of a 120 DPI page render - and the escalated step fell from
~150s to 6-17s per exhibit. A gate that costs exactness to save seconds that no
longer need saving is the wrong shape, so the trigger loosened: every page whose
transcription mentions an exhibit is re-read at exhibit level. The cheap page text is
kept and the exhibit transcription is appended - prose from the cheap pass, exact
chart values from the strong one.

What did NOT change: the axis/label classification stays ground-truth-free, derived
from the cheap transcription (exhibit mentioned but no values = unlabelled chart).
That signal rides out as `chart_kind` in the page meta, and the memo layer uses it to
decide which values ship flagged.
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

_CROP_MARKER = "[Exhibit re-read at native resolution]"


def needs_escalation(text: str) -> tuple[bool, str, str]:
    """Should the strong model re-read this page's exhibits?

    Returns (escalate, why, chart_kind). Ground-truth free by design: we ask what the
    transcription says about itself, not whether it matches an answer key. The
    history of this trigger is a measurement story - see the module docstring. The
    first version fired on any page containing the word "unreadable" (16 of 20 pages,
    two thirds buying nothing); the second required "no numbers at all", which was
    quiet about charts the cheap model half-read. This version re-reads every exhibit
    page because the re-read got cheap.

    `chart_kind` is the part downstream consumers care about: "unlabelled" means the
    cheap pass saw an exhibit and no values - the axis-read signature - and values
    recovered from such a page ship flagged. "labelled" means numbers were present;
    the re-read is for completeness, and its values are label reads.
    """
    if not text.strip():
        return True, "empty transcription", "unlabelled"
    has_exhibit = bool(_EXHIBIT.search(text))
    has_numbers = bool(_NUMERIC.search(text))
    if has_exhibit:
        if has_numbers:
            return (True, "mentions an exhibit - re-reading it at exhibit level",
                    "labelled")
        return (True, "mentions an exhibit but reported no values - unlabelled chart",
                "unlabelled")
    if "unreadable" in text.lower() and not has_numbers:
        return (True, "reported a value unreadable and produced no numbers",
                "unlabelled")
    return False, "", ""


def parse(pdf_path: Path, pages: list[int] | None = None,
          cheap: str = CHEAP_MODEL, strong: str = STRONG_MODEL,
          use_cache: bool = True) -> ParsedDocument:
    """Cheap model first; strong model re-reads every exhibit, losslessly."""
    base = vision.parse(pdf_path, pages=pages, model=cheap, use_cache=use_cache)
    if not base.pages:
        return base

    out: list[ParsedPage] = []
    escalated: list[int] = []
    for p in base.pages:
        need, why, kind = needs_escalation(p.text)
        if not need:
            p.meta["tier"] = "cheap"
            out.append(p)
            continue

        # Exhibit-level read: the page's own embedded images, lossless. This is the
        # path that recovers axis values and dropped callout boxes; it is also the
        # cheap one (6-17s at think=False), which is why every exhibit gets it.
        crop_text, crop_meta = vision.read_crops(pdf_path, p.page_number, strong,
                                                 use_cache=use_cache)
        if crop_text:
            cheap_secs = p.meta.get("seconds", 0) or 0
            merged = p.text.rstrip() + "\n\n" + _CROP_MARKER + "\n" + crop_text
            measured = None
            if kind == "unlabelled":
                # The transcription's axis values are estimates; on an unlabelled
                # chart they can be measured instead. Model read the tick glyphs
                # once (cached); code does the rest, offline, forever.
                measured = vision.measure_exhibit(pdf_path, p.page_number, strong,
                                                  crop_text, use_cache=use_cache)
                if measured:
                    merged += "\n\n" + measured
            p.text = merged
            p.meta.update({
                "tier": "escalated", "escalated_because": why,
                "chart_kind": kind, "cheap_model": cheap, "strong_model": strong,
                "crop": True, "measured": bool(measured),
                "crop_seconds": (crop_meta or {}).get("seconds"),
                "seconds": round(cheap_secs + (crop_meta or {}).get("seconds", 0) or 0, 2),
            })
            escalated.append(p.page_number)
            out.append(p)
            continue

        # Fallback for pages without embedded images (vector exhibits) or an
        # unavailable crop read: the v1 path, a full-page render at the strong tier.
        up = vision.parse(pdf_path, pages=[p.page_number], model=strong,
                          use_cache=use_cache, think=False)
        got = up.page(p.page_number)
        if got and got.text.strip():
            got.meta.update({"tier": "escalated", "escalated_because": why,
                             "chart_kind": kind, "cheap_model": cheap})
            out.append(got)
            escalated.append(p.page_number)
        else:
            p.meta.update({"tier": "cheap", "escalation_attempted": True,
                           "escalated_because": why})
            out.append(p)

    return ParsedDocument(
        source=Path(pdf_path), pages=out, backend=f"tiered:{cheap}->{strong}",
        notes=(f"Cheap-first vision. {len(out) - len(escalated)} page(s) answered by "
               f"{cheap}; {len(escalated)} re-read at exhibit level by {strong} "
               f"{escalated if escalated else ''}."))
