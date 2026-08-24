"""Backend C - read the page as a picture.

This is the backend that can see a chart. It rasterises each page and asks a local
vision-language model to transcribe what is on it, including reading values off plots
that carry no text at all.

Two design choices are load-bearing:

**Transcribe, do not interpret.** The prompt asks for a faithful rendering of the
page - text as written, tables as rows, charts as series-and-value pairs. It never
asks for the metrics we happen to want. If the prompt named the fields, the backend
would be answering a quiz rather than reading a document, and Layer P would measure
our prompt instead of the parser. Extraction is a separate, later step for exactly
this reason.

**Attribution is demanded explicitly.** A chart reading of "34%" is useless without
"largest customer". The prompt requires every value to arrive attached to its series
label, which is what makes the `attributed` grade downstream meaningful.

Rasterisation is deterministic (fixed DPI, no sampling), so re-running produces the
same images. The model call is temperature 0. What remains non-deterministic is the
model itself, which is why its raw output is committed rather than regenerated on
demand - see `run_checks.py`.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from ..models import ollama
from .base import ParsedDocument, ParsedPage

# 120 DPI, measured rather than guessed. At 170 a letter page costs ~2,780 input
# tokens and 83s; at 120 it costs ~1,485 and reads the same values correctly, because
# the limiting factor is chart comprehension, not glyph size. Raising it is the first
# thing to try if a chart reads badly - but pay the tokens only when it buys accuracy.
RENDER_DPI = 120

# minicpm-v4.6, a 1B model in a 1.6GB download. Chosen on measurement, not on size.
#
# Three models were tried on the same chart page (T01, true values 6% and 19%):
#
#   minicpm-v4.6  1B    19s   both values, no thinking
#   qwen3.5:4b    4B   162s   both values, after 8,914 characters of thinking
#   qwen3-vl:8b   8B   330s   EMPTY response - thinking consumed the whole budget
#
# The small model is not a compromise here, it is the better engineering choice: 17x
# faster, an order of magnitude smaller to download, and - the part that actually
# matters - reliable, because it does not think and therefore cannot be truncated
# mid-thought into a silent empty answer.
#
# That reliability difference is the real finding. A reader cloning this repo needs a
# 1.6GB pull rather than 6.1GB, which is the difference between trying it and not.
#
# Re-measured 2026-08-24, two variables changed: `think=False` at the API door (the
# `think` parameter in models/ollama.py did not exist during the first bake-off), and
# the model shown the chart's native embedded image instead of a 120 DPI page render.
# On the two chart pages the tiered pipeline had been failing (T02/T05 p7, true
# values 96/103 and 81/86):
#
#   qwen3.5:4b  think=False, native crop    5.7-16.5s   all four values exact
#   qwen3-vl:8b think=False, native crop  140.7s / EMPTY           one exact, one empty
#
# The "capability boundary" of the first bake-off was mostly the thinking budget and
# the lossy re-render. qwen3-vl stays rejected: still erratic with thinking disabled,
# still 10-30x slower. The strong tier remains qwen3.5:4b - it just gets to see the
# exhibit properly now.
#
# Also tried and rejected: gemma4:latest advertises `vision` in `ollama show` and then
# answers "please provide the page you would like me to transcribe" for an image sent
# through either /api/generate or /api/chat - the identical payload the others read
# without complaint.
DEFAULT_MODEL = "minicpm-v4.6:latest"

# Fallbacks, in the order they were measured. Bigger is not better on this task.
ALTERNATE_MODELS = ["qwen3.5:4b", "qwen3-vl:8b"]

# Generous, and only load-bearing for the thinking models kept as alternates. On
# those, num_predict is a trap: cap it below the reasoning and the call returns an
# EMPTY string with done_reason="length" - no error, no warning, and indistinguishable
# from a model that cannot read charts. The chosen default does not think, which is
# most of why it is the default.
NUM_PREDICT = 8000

# 420s. Ample for the 1B default (~19s/page) and a fail-fast ceiling for the
# alternates. 8192 context is sufficient: a page image costs ~1,500 tokens in and a
# transcription ~500 out - context was never the constraint, thinking length was.
PAGE_TIMEOUT = 420

SYSTEM = (
    "You transcribe pages from financial documents. You are precise, you never "
    "invent figures, and you say plainly when something is unreadable."
)

PROMPT = """Transcribe this page from a confidential information memorandum.

Rules:
- Reproduce body text as written.
- Render tables as one line per row: `Label | Value | Notes`.
- For every chart, list each series or category with its value, one per line, as
  `<series or category label>: <value>`. Read values off the axis when the chart has
  no data labels printed on it. State the units.
- If a value genuinely cannot be determined, write `unreadable` for it. Never guess.
- Do not summarise, interpret, or add commentary. Transcribe only.

Begin the transcription now."""


def page_images(pdf_path: Path, pages: list[int] | None = None, dpi: int = RENDER_DPI):
    """Rasterise pages to PNG bytes. `pages` is 1-indexed; None means all."""
    import pymupdf

    doc = pymupdf.open(str(pdf_path))
    zoom = dpi / 72.0
    matrix = pymupdf.Matrix(zoom, zoom)
    out = []
    for i in range(doc.page_count):
        n = i + 1
        if pages is not None and n not in pages:
            continue
        pix = doc.load_page(i).get_pixmap(matrix=matrix)
        out.append((n, pix.tobytes("png")))
    doc.close()
    return out


CACHE = Path(__file__).resolve().parents[2] / "data" / "vision_cache"


def _cache_key(pdf_path: Path, page_no: int, model: str, dpi: int,
               variant: str | None = None) -> Path:
    stem = Path(pdf_path).stem
    safe = model.replace(":", "-").replace("/", "-")
    suffix = "" if not variant else f"__{variant}"
    return CACHE / f"{stem}__p{page_no:02d}__{safe}__dpi{dpi}{suffix}.json"


def parse(
    pdf_path: Path,
    pages: list[int] | None = None,
    model: str = DEFAULT_MODEL,
    use_cache: bool = True,
    think: bool | None = None,
    prompt: str = PROMPT,
    system: str | None = SYSTEM,
    cache_variant: str | None = None,
) -> ParsedDocument:
    """Read `pages` with a local vision model.

    Results are cached to `data/vision_cache/` and the cache is committed. That is
    not an optimisation, it is the reproducibility mechanism: a full pass costs
    roughly 45 minutes of local GPU time, so a reviewer must be able to verify every
    published number from artifacts without owning the hardware or waiting. Delete
    the cache to force a genuine re-read.

    An unreachable model yields an empty document with a note, never an exception.
    "Not run" must be visible in the results table, not disguised as a zero score.
    """
    if not ollama.available():
        return ParsedDocument(
            source=Path(pdf_path), pages=[], backend=f"vision:{model}",
            notes="Ollama not reachable - backend not run.")
    if not ollama.has_model(model):
        return ParsedDocument(
            source=Path(pdf_path), pages=[], backend=f"vision:{model}",
            notes=f"Model {model} not installed - backend not run.")

    wanted = pages
    parsed: list[ParsedPage] = []
    to_read: list[int] = []

    # Cache first, so a re-run costs nothing for pages already read.
    import pymupdf
    doc = pymupdf.open(str(pdf_path))
    all_pages = list(range(1, doc.page_count + 1))
    doc.close()
    for n in (wanted if wanted is not None else all_pages):
        ck = _cache_key(pdf_path, n, model, RENDER_DPI, cache_variant)
        if use_cache and ck.exists():
            rec = json.loads(ck.read_text(encoding="utf-8"))
            parsed.append(ParsedPage(page_number=n, text=rec["text"],
                                     method="vision", meta=rec["meta"]))
        else:
            to_read.append(n)

    if to_read:
        CACHE.mkdir(parents=True, exist_ok=True)
        for page_no, png in page_images(pdf_path, to_read):
            reply = ollama.generate(model, prompt, images=[png], system=system,
                                    num_predict=NUM_PREDICT,
                                    timeout=PAGE_TIMEOUT, think=think)
            meta = {
                "model": model, "ok": reply.ok, "error": reply.error,
                "seconds": round(reply.seconds, 2),
                "tokens_in": reply.tokens_in, "tokens_out": reply.tokens_out,
                "dpi": RENDER_DPI,
            }
            text = reply.text if reply.ok else ""
            # Cache successes only. A timeout cached as a read is indistinguishable
            # downstream from "the model looked and found nothing" - it would publish
            # an infrastructure failure as a capability finding. This bit us during
            # the build: a 300s timeout under GPU contention wrote an empty result
            # that scored as a miss. Failures stay uncached so a re-run retries them.
            if reply.ok and text.strip():
                _cache_key(pdf_path, page_no, model, RENDER_DPI,
                           cache_variant).write_text(
                    json.dumps({"text": text, "meta": meta}, indent=2), encoding="utf-8")
            parsed.append(ParsedPage(page_number=page_no, text=text,
                                     method="vision", meta=meta))

    parsed.sort(key=lambda p: p.page_number)
    return ParsedDocument(
        source=Path(pdf_path), pages=parsed, backend=f"vision:{model}",
        notes=f"Local VLM via Ollama at {RENDER_DPI} DPI, temperature 0, cached.")


def page_embedded_images(pdf_path: Path, page_no: int) -> list[bytes]:
    """A page's embedded raster images at native resolution, in document order.

    Charts in a born-digital PDF are embedded pictures; re-rendering the whole page
    at 120 DPI resamples them. Extracting the stored bytes is lossless and needs no
    rendering step at all. Vector-drawn exhibits have no embedded image - callers
    fall back to the page render for those.
    """
    import pymupdf

    doc = pymupdf.open(str(pdf_path))
    try:
        page = doc.load_page(page_no - 1)
        out = []
        for im in page.get_images(full=True):
            info = doc.extract_image(im[0])
            if info.get("image"):
                out.append(info["image"])
        return out
    finally:
        doc.close()


def read_crops(pdf_path: Path, page_no: int, model: str,
               use_cache: bool = True) -> tuple[str | None, dict | None]:
    """Transcribe a page's embedded exhibits, native resolution, `think=False`.

    The escalation tier's input. Same transcription prompt and rules as the page
    path - the model is still reading, not interpreting - but it sees the chart the
    document actually stored rather than a resampled copy of the page it sits on.
    Multiple images on one page are transcribed in order and joined; the cache holds
    the joined transcription per page, so re-runs cost nothing and the committed
    cache remains the evidence.

    Returns (text, meta). (None, None) means no embedded images or no usable model -
    callers fall back to the full-page read. A failed model call returns (None, meta)
    and stays uncached, same rule as `parse`: an infrastructure failure must not be
    cached as a read.
    """
    ck = CACHE / (f"{Path(pdf_path).stem}__p{page_no:02d}__"
                  f"{model.replace(':', '-').replace('/', '-')}__crop.json")
    if use_cache and ck.exists():
        rec = json.loads(ck.read_text(encoding="utf-8"))
        return rec["text"], rec["meta"]

    images = page_embedded_images(pdf_path, page_no)
    if not images:
        return None, None
    if not (ollama.available() and ollama.has_model(model)):
        return None, None

    ck.parent.mkdir(parents=True, exist_ok=True)
    texts: list[str] = []
    secs = tin = tout = 0.0
    for png in images:
        reply = ollama.generate(model, PROMPT, images=[png], system=SYSTEM,
                                num_predict=NUM_PREDICT, timeout=PAGE_TIMEOUT,
                                think=False)
        secs += reply.seconds
        tin += reply.tokens_in
        tout += reply.tokens_out
        if not reply.ok or not reply.text.strip():
            return None, {"model": model, "ok": reply.ok, "error": reply.error,
                          "seconds": round(secs, 2), "source": "embedded-native"}
        texts.append(reply.text.strip())

    text = "\n\n".join(texts)
    meta = {"model": model, "ok": True, "error": "", "seconds": round(secs, 2),
            "tokens_in": int(tin), "tokens_out": int(tout), "dpi": None,
            "source": "embedded-native"}
    ck.write_text(json.dumps({"text": text, "meta": meta}, indent=2),
                  encoding="utf-8")
    return text, meta


# The one thing measurement needs from the model: the tick-label glyphs. Reading
# printed characters is recognition - the task the vision tier does at 100% - and
# it is the only model input to the measured values. Everything downstream of this
# read is arithmetic in chart_measure.py, re-runnable offline from committed bytes.
TICKS_PROMPT = """Read the y-axis tick labels of this chart. Output one label per
line, topmost first, as a bare number exactly as printed (for example: 75.0).
Output nothing else."""

_TICK_RE = re.compile(r"^-?\d+(?:\.\d+)?$")


def read_ticks(pdf_path: Path, page_no: int, image_index: int, png: bytes,
               model: str, use_cache: bool = True) -> list[float] | None:
    """The chart's y-axis tick values, top to bottom. Cached like every read."""
    safe = model.replace(":", "-").replace("/", "-")
    ck = CACHE / f"{Path(pdf_path).stem}__p{page_no:02d}__{safe}__ticks{image_index}.json"
    if use_cache and ck.exists():
        rec = json.loads(ck.read_text(encoding="utf-8"))
        return rec["ticks"]

    if not (ollama.available() and ollama.has_model(model)):
        return None
    reply = ollama.generate(model, TICKS_PROMPT, images=[png], system=SYSTEM,
                            num_predict=400, timeout=PAGE_TIMEOUT, think=False)
    if not reply.ok or not reply.text.strip():
        return None  # uncached failure - a re-run retries it
    ticks = [float(m.group(0)) for line in reply.text.splitlines()
             if (m := _TICK_RE.match(line.strip()))]
    if len(ticks) < 2:
        return None
    ck.parent.mkdir(parents=True, exist_ok=True)
    ck.write_text(json.dumps(
        {"ticks": ticks, "text": reply.text,
         "meta": {"model": model, "ok": True, "seconds": round(reply.seconds, 2)}},
        indent=2), encoding="utf-8")
    return ticks


READ_PROMPT = (
    "Read this line chart. It has two series. For EACH series, read the value of "
    "the FINAL data point (rightmost marker) off the y axis, interpolating between "
    "gridlines. Also list the y-axis tick labels you can see, topmost first.\n"
    "Answer in exactly this format:\n"
    "ticks: <n1>, <n2>, ...\n"
    "<series label>: <value>"
)


def read_chart_values(pdf_path: Path, page_no: int, image_index: int, png: bytes,
                      model: str, use_cache: bool = True) -> list[tuple[str, float]] | None:
    """An independent model's own read of the chart's endpoint values.

    The cross-check tier's input. The measurement (chart_measure.py) is the number
    the pipeline uses; this read exists so every measured value has an independent
    perception path agreeing or disagreeing with it - agreement builds confidence,
    disagreement flags a human. Cached like every read; the cached reads are what
    makes the agreement claim verifiable offline.
    """
    from . import chart_measure

    safe = model.replace(":", "-").replace("/", "-")
    ck = CACHE / f"{Path(pdf_path).stem}__p{page_no:02d}__{safe}__read{image_index}.json"
    if use_cache and ck.exists():
        rec = json.loads(ck.read_text(encoding="utf-8"))
        return [(r["label"], r["value"]) for r in rec["reads"]]

    if not (ollama.available() and ollama.has_model(model)):
        return None
    reply = ollama.generate(model, READ_PROMPT, images=[png], system=None,
                            num_predict=1000, timeout=PAGE_TIMEOUT, think=False)
    if not reply.ok or not reply.text or not reply.text.strip():
        return None  # uncached failure - a re-run retries it
    reads = chart_measure.parse_model_reads(reply.text)
    if not reads:
        return None
    ck.parent.mkdir(parents=True, exist_ok=True)
    ck.write_text(json.dumps(
        {"reads": [{"label": l, "value": v} for l, v in reads],
         "text": reply.text,
         "meta": {"model": model, "ok": True, "seconds": round(reply.seconds, 2)}},
        indent=2), encoding="utf-8")
    return reads


def measure_exhibit(pdf_path: Path, page_no: int, model: str, crop_text: str,
                    use_cache: bool = True,
                    verify_model: str | None = None
                    ) -> tuple[str | None, dict | None]:
    """Measure a page's exhibits and, optionally, cross-check the measurement.

    For each embedded exhibit: geometry finds the series colours and endpoint rows
    (chart_measure.py), the cached tick read supplies the calibration, and the two
    combine into values code computed. The model's role is bounded to reading
    glyphs - its own estimated values stay in the transcription above, explicitly
    superseded. Any step that does not resolve (no gridlines, tick count mismatch,
    unparseable rows) leaves the transcription standing alone.

    `verify_model` (when installed) independently reads the chart's endpoint
    values - a second, perception-only path over the same pixels. The measurement
    stays the number the pipeline uses; the read exists so every measured value
    carries an agreement record: agree within tolerance builds confidence,
    disagree flags a human. Returns (block, crosscheck) - either may be None.
    """
    from . import chart_measure

    images = page_embedded_images(pdf_path, page_no)
    if not images:
        return None, None
    blocks: list[str] = []
    xcheck: dict | None = None
    for i, png in enumerate(images):
        rgb = chart_measure._rgb(png)
        grid = chart_measure.find_gridlines(rgb)
        series = chart_measure.find_series(rgb)
        if len(grid) < 2 or len(series) < 1:
            continue
        ticks = read_ticks(pdf_path, page_no, i, png, model, use_cache=use_cache)
        if ticks is None or len(ticks) != len(grid):
            continue
        # Order is taken from geometry, not from the model: gridlines run top to
        # bottom and a y axis increases upward, so the top gridline pairs with the
        # largest tick. (Measured reason: qwen3.5 returned one chart's ticks
        # bottom-to-top despite the prompt, which mirrored every value.)
        ticks = sorted(ticks, reverse=True)
        values = []
        for color in series:
            ep = chart_measure.find_endpoint(rgb, color)
            if ep is None:
                break
            # Prefer the line's fitted centerline over the marker's own center:
            # a small disc rasterizes wherever its sub-pixel phase lands, the
            # line averages that noise away (chart_measure.line_fit_y).
            y = chart_measure.line_fit_y(rgb, color, ep[1], ep[0]) or ep[0]
            v = chart_measure.interpolate(y, grid, ticks)
            if v is None:
                break
            values.append(round(v, 1))
        if len(values) != len(series):
            continue
        pairs = chart_measure.measured_pairs(crop_text, values)
        if not pairs:
            continue
        blocks.append(chart_measure.block_from_pairs(pairs))
        if verify_model is None or xcheck is not None:
            continue  # one cross-check per page is enough; first resolved image wins
        model_reads = read_chart_values(pdf_path, page_no, i, png, verify_model,
                                        use_cache=use_cache)
        if model_reads:
            recs = chart_measure.crosscheck(pairs, model_reads)
            if recs:
                xcheck = {"model": verify_model, "pairs": recs,
                          "all_agree": all(r["agree"] for r in recs)}
    return ("\n\n".join(blocks) if blocks else None), xcheck
