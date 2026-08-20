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

    Ground-truth free by design. We ask what the transcription says about itself, not
    whether it matches an answer key - the trigger has to work on documents nobody has
    labelled.

    **Tuned after measuring it, and the first version was too loose.** The original
    escalated any page containing the word "unreadable" anywhere. Across the corpus
    that fired on 16 of 20 pages, including prose and table pages the 1B model had
    already transcribed perfectly - it had simply noted one minor item as unreadable
    and dragged the whole page up a tier. Escalation cost 1,183s against 383s for the
    cheap pass alone, and roughly two thirds of that bought nothing.

    The lesson generalises past this repo: an escalation trigger is a classifier, and
    an unmeasured one silently spends the budget the tiering was supposed to save.
    Now a page escalates only when it plausibly carries an exhibit AND yielded no
    numbers at all - the signature of a chart the small model could not read.
    """
    if not text.strip():
        return True, "empty transcription"
    if _EXHIBIT.search(text) and not _NUMERIC.search(text):
        return True, "mentions an exhibit but reports no values"
    # "unreadable" only counts when the page also produced nothing numeric. On its own
    # it is far too eager - see the docstring.
    if "unreadable" in text.lower() and not _NUMERIC.search(text):
        return True, "reported a value unreadable and produced no numbers"
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
