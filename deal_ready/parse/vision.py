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


def _cache_key(pdf_path: Path, page_no: int, model: str, dpi: int) -> Path:
    stem = Path(pdf_path).stem
    safe = model.replace(":", "-").replace("/", "-")
    return CACHE / f"{stem}__p{page_no:02d}__{safe}__dpi{dpi}.json"


def parse(
    pdf_path: Path,
    pages: list[int] | None = None,
    model: str = DEFAULT_MODEL,
    use_cache: bool = True,
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
        ck = _cache_key(pdf_path, n, model, RENDER_DPI)
        if use_cache and ck.exists():
            rec = json.loads(ck.read_text(encoding="utf-8"))
            parsed.append(ParsedPage(page_number=n, text=rec["text"],
                                     method="vision", meta=rec["meta"]))
        else:
            to_read.append(n)

    if to_read:
        CACHE.mkdir(parents=True, exist_ok=True)
        for page_no, png in page_images(pdf_path, to_read):
            reply = ollama.generate(model, PROMPT, images=[png], system=SYSTEM,
                                    num_predict=NUM_PREDICT,
                                    timeout=PAGE_TIMEOUT)
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
                _cache_key(pdf_path, page_no, model, RENDER_DPI).write_text(
                    json.dumps({"text": text, "meta": meta}, indent=2), encoding="utf-8")
            parsed.append(ParsedPage(page_number=page_no, text=text,
                                     method="vision", meta=meta))

    parsed.sort(key=lambda p: p.page_number)
    return ParsedDocument(
        source=Path(pdf_path), pages=parsed, backend=f"vision:{model}",
        notes=f"Local VLM via Ollama at {RENDER_DPI} DPI, temperature 0, cached.")
