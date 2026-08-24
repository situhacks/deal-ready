"""A parsing model reads every page; the strong tier re-reads what it drops.

v3 swapped the cheap tier from a general 1B VLM (minicpm-v4.6) to GLM-OCR, a 0.9B
specialized document parser, on bake-off evidence (reports/bakeoff.md): identical
graded fidelity on prose, tables and labelled charts - including chart-internal
callout boxes the generalist dropped - at roughly a quarter of the latency
(~5s/page vs ~19s). The 2026 research wave predicted exactly this: parsers win
faithful transcription by decomposition, and no benchmark scores chart interiors,
which is why the axis column does not come from any single model at all.

The tier shape is unchanged:

    glm-ocr (0.9B parser)   every page, ~5s   prose/tables/labelled charts 100%
    qwen3.5:4b (think=False) exhibit crops    native-image re-reads + tick glyphs
    chart_measure.py        code             axis values measured from pixels

Two measured behaviors of the parser shape the trigger. GLM-OCR reads labelled
charts perfectly but DROPS unlabelled chart interiors entirely - and its output on
such a page contains no exhibit vocabulary at all (no "chart", no "figure"; just
prose, the axis title, and year labels). The old trigger required an exhibit word,
so a parser-class reader would sail past the very pages that need escalation. The
rule is now symmetric and simpler: **a routed page whose transcription yields no
numeric values escalates, whatever it mentions** - a page that produced no numbers
is a page whose exhibit beat the reader. Pages that mention an exhibit AND produced
numbers still escalate (annotation-drop insurance, ~6-17s).

`chart_kind` stays ground-truth-free: no values in the cheap transcription means
"unlabelled" (axis-read signature; values ship flagged), numbers present means
"labelled". The parser's own y-axis tick numbers cannot be used for calibration -
it drops those too - so tick glyphs remain the strong tier's job, read once and
cached, with geometry doing the rest offline.
"""

from __future__ import annotations

import re
from pathlib import Path

from . import vision
from .base import ParsedDocument, ParsedPage

CHEAP_MODEL = "glm-ocr"
STRONG_MODEL = "qwen3.5:4b"

_NUMERIC = re.compile(r"\d+(?:\.\d+)?\s?%|\$\s?\d")
_EXHIBIT = re.compile(r"chart|graph|figure|exhibit|plot|axis", re.I)

_CROP_MARKER = "[Exhibit re-read at native resolution]"


def needs_escalation(text: str) -> tuple[bool, str, str]:
    """Should the strong tier re-read this page's exhibits?

    Returns (escalate, why, chart_kind). Ground-truth free by design: we ask what
    the transcription says about itself, not whether it matches an answer key.
    Measurement history of this trigger: v1 fired on any page containing
    "unreadable" (16 of 20 pages, two thirds buying nothing); v2 required an
    exhibit word plus no numbers, which was quiet about charts the reader
    half-read, then loosened to every exhibit page once escalation got cheap; v3
    adds the parser-class signature - a specialized reader drops unlabelled chart
    interiors AND the exhibit vocabulary, so *no numbers at all* is itself the
    escalation signal.

    `chart_kind`: "unlabelled" means the cheap transcription carried no values -
    the axis-read signature; values recovered from such a page ship flagged.
    "labelled" means numbers were present; the re-read is annotation-drop
    insurance, and its values are label reads.
    """
    if not text.strip():
        return True, "empty transcription", "unlabelled"
    has_exhibit = bool(_EXHIBIT.search(text))
    has_numbers = bool(_NUMERIC.search(text))
    if has_numbers:
        if has_exhibit:
            return (True, "mentions an exhibit - re-reading it at exhibit level",
                    "labelled")
        return False, "", ""
    if has_exhibit:
        return (True, "mentions an exhibit but reported no values - unlabelled chart",
                "unlabelled")
    return (True, "reported no values at all - the reader dropped whatever "
                  "carried them", "unlabelled")


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
