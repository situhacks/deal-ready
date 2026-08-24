"""The reading pipeline: the best reader for each job, no ladder.

v3.2 collapsed the escalation ladder that v1-v3.1 ran. Its own bake-off decided
the question the ladder existed to answer (reports/bakeoff.md): measured as
full-page readers on identical pages, the newest open frontier model reads 80% of
prose fields and 80% of axis values at 148s a page, while a 0.9B parser reads
100% of prose, tables and labelled charts at 5s. There is no best single reader -
there is a best reader per job, and the pipeline now assigns each job directly
instead of waiting for a cheap pass to fail first:

    glm-ocr (0.9B parser)       every routed page, ~5s     text, tables, labelled
                                                          charts - including
                                                          chart-internal callouts
    qwen3.8:27b (open frontier) chart pages only, ~20-40s  one call: series labels,
                                                          tick glyphs, and its own
                                                          estimated values
    chart_measure.py (code)     the numbers                pixel geometry calibrated
                                                          by those ticks

Nothing escalates, because nothing is running a cheaper pass first. A routed page
either yields values (done) or yields none - the signature of a chart the parser
dropped, since parser-class readers omit unlabelled chart interiors and the word
"chart" with them - and goes straight to the chart specialist. Vector-drawn charts
with no embedded image are reported as unresolved rather than silently passed.

The chart model's estimated values are never used as numbers. They join the
measured values to their series labels, then serve as the independent
cross-check: agreement within chart_measure.READ_TOLERANCE builds confidence in
the memo call-out, disagreement prints resolve-before-use. The measurement stays
the only number the pipeline produces.
"""

from __future__ import annotations

import re
from pathlib import Path

from . import chart_measure, vision
from .base import ParsedDocument, ParsedPage

READER_MODEL = "glm-ocr"
CHART_MODEL = "qwen3.8:27b"

_NUMERIC = re.compile(r"\d+(?:\.\d+)?\s?%|\$\s?\d")

_MEASURED_MARKER = "[Measured from the chart's pixels - authoritative over the estimates above]"


def parse(pdf_path: Path, pages: list[int] | None = None,
          reader: str = READER_MODEL, chart_model: str = CHART_MODEL,
          use_cache: bool = True) -> ParsedDocument:
    """Read every routed page with the parser; chart pages with the specialist.

    A page whose transcription contains no numeric values goes to the chart path:
    the page's embedded exhibit is read once by the chart model (labels, ticks,
    estimates), geometry measures the endpoint values from the pixels, and the
    measured block - code's numbers, the model's labels - is appended. Everything
    is cached per read, so a re-run costs nothing and the committed caches are the
    evidence.
    """
    base = vision.parse(pdf_path, pages=pages, model=reader, use_cache=use_cache)
    if not base.pages:
        return base

    out: list[ParsedPage] = []
    chart_read: list[int] = []
    for p in base.pages:
        p.meta["reader"] = reader
        if _NUMERIC.search(p.text):
            out.append(p)
            continue

        # Chart path: the parser dropped whatever carried the values.
        images = vision.page_embedded_images(pdf_path, p.page_number)
        if not images:
            p.meta["chart_path"] = "no embedded exhibit image - unresolved"
            out.append(p)
            continue
        read = vision.read_chart_values(pdf_path, p.page_number, 0, images[0],
                                        chart_model, use_cache=use_cache)
        if read is None:
            p.meta["chart_path"] = f"{chart_model} unavailable or read failed"
            out.append(p)
            continue
        values = chart_measure.measure_chart(images[0], read["ticks"])
        if values is None:
            p.meta["chart_path"] = "chart geometry did not resolve"
            out.append(p)
            continue
        pairs = chart_measure.join_by_proximity(read["pairs"], values)
        if pairs is None:
            p.meta["chart_path"] = "series labels did not match measured series"
            out.append(p)
            continue
        p.text = p.text.rstrip() + "\n\n" + _MEASURED_MARKER + "\n" \
            + chart_measure.block_from_pairs(pairs)
        xcheck = chart_measure.crosscheck(pairs, read["pairs"])
        meta = {"chart_kind": "unlabelled", "chart_model": chart_model,
                "measured": True}
        if xcheck:
            meta["crosscheck"] = {"model": chart_model, "pairs": xcheck,
                                  "all_agree": all(r["agree"] for r in xcheck)}
        p.meta.update(meta)
        chart_read.append(p.page_number)
        out.append(p)

    return ParsedDocument(
        source=Path(pdf_path), pages=out,
        backend=f"pipeline:{reader}->[{chart_model}+geometry]",
        notes=(f"{reader} read {len(out) - len(chart_read)} page(s) with values; "
               f"{len(chart_read)} chart page(s) measured from pixels "
               f"{chart_read if chart_read else ''}."))
