"""Run candidate page readers over the ground-truth pages and grade them identically.

    python bakeoff.py              # grade every installed candidate
    python bakeoff.py --fresh      # ignore the vision cache

The v3 question this answers: should the tiered pipeline's cheap tier stop being a
general VLM? The 2026 document-parsing literature says specialized parsers win
faithful transcription, but no benchmark can make the swap call - top leaderboard
deltas are smaller than one model's run-to-run spread - so the decision instrument
is this: same pages, same 120 DPI render, same transcription prompt, same grader
as Layer P, per-candidate caches committed like every other read.

References come from reports/layer_p.json without re-running: `vision:minicpm`
is a general-VLM single-pass reference, and the `pipeline` row is the full
production pipeline a candidate must beat.

A model that is not installed reports "not run" - an infrastructure gap must not
dress up as a capability finding. Chart-interior values are graded nowhere here:
no candidate even attempts them (ParseBench 2026: parsers under 6%), which is
exactly why chart measurement stays out of the swap decision.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

from deal_ready.models import ollama
from deal_ready.parse import vision
from eval.recoverability import aggregate, load_ground_truth, score_document

ROOT = Path(__file__).parent
DATA = ROOT / "data"
REPORTS = ROOT / "reports"

# The candidates the 2026 research cleared for this box (16GB AMD, Ollama runtime).
# PaddleOCR-VL-1.6: no Ollama manifest exists (checked 2026-08-24); its community
# GGUF needs a manual llama.cpp install - round 2, reason recorded, not silent.
#
# deepseek-ocr's Ollama port instant-EOSes on any prompt longer than ~50 characters
# (bisected 2026-08-24: 48 chars reads, 83 chars returns one token and stops), so it
# cannot carry the production transcription prompt. It is graded on the longest
# prompt that survives, carrying the one rule that matters most (never invent), and
# the fragility itself is a bake-off finding: a reader that cannot hold the
# pipeline's instruction contract is disqualified for production even if it scores.
DEEPSEEK_PROMPT = "Transcribe exactly. Never invent values."
CANDIDATES = [
    {"model": "glm-ocr"},
    {"model": "deepseek-ocr", "prompt": DEEPSEEK_PROMPT, "system": None,
     "cache_variant": "shortprompt",
     "note": "port rejects prompts over ~50 chars; graded on the 40-char core"},
    {"model": "qwen3.8:27b",
     "note": "newest open general multimodal; the just-use-the-best-reader test"},
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fresh", action="store_true", help="ignore the vision cache")
    args = ap.parse_args()

    gt = load_ground_truth()
    by_target: dict[str, list[dict]] = defaultdict(list)
    for r in gt:
        by_target[r["target_id"]].append(r)

    pdfs = sorted(DATA.glob("*.pdf"))
    rows: list[dict] = []
    ran: list[str] = []
    skipped: list[tuple[str, str]] = []
    timing: dict[str, dict] = {}

    for cand in CANDIDATES:
        model = cand["model"]
        print(f"\n{model}:")
        if not (ollama.available() and ollama.has_model(model)):
            skipped.append((model, "not installed in Ollama"))
            print("  not run - not installed")
            continue
        secs = 0.0
        pages_read = 0
        doc = None
        for pdf in pdfs:
            recs = by_target[pdf.name.split("_")[0]]
            pages = sorted({r["page"] for r in recs})
            doc = vision.parse(pdf, pages=pages, model=model,
                               use_cache=not args.fresh,
                               prompt=cand.get("prompt", vision.PROMPT),
                               system=cand.get("system", vision.SYSTEM),
                               cache_variant=cand.get("cache_variant"))
            if not doc.pages:
                skipped.append((model, doc.notes))
                print(f"  {pdf.name:<34} not run - {doc.notes}")
                doc = None
                break
            rows += score_document(doc, recs)
            for p in doc.pages:
                secs += p.meta.get("seconds", 0) or 0
            pages_read += len(doc.pages)
            print(f"  {pdf.name:<34} {len(doc.pages)} pages  {secs:>7.1f}s cumulative")
        if doc is not None:
            ran.append(model)
            timing[model] = {"seconds": round(secs, 1), "pages": pages_read,
                             "sec_per_page": round(secs / max(pages_read, 1), 1),
                             "note": cand.get("note")}

    if not rows:
        print("\nno candidate ran - nothing to grade")
        return 0

    agg = aggregate(rows)
    rep = json.loads((REPORTS / "layer_p.json").read_text(encoding="utf-8")) \
        if (REPORTS / "layer_p.json").exists() else {"aggregate": {}}

    # The chart split, same as Layer P: recognition vs axis reading.
    split: dict[tuple[str, str], dict[str, int]] = defaultdict(
        lambda: {"n": 0, "att": 0})
    for r in rows:
        if r["carrier"] != "chart":
            continue
        s = split[(r["backend"], "labels" if r["labelled_in_chart"] else "axis")]
        s["n"] += 1
        s["att"] += int(r["attributed"])

    def cell(backend: str, carrier: str) -> str:
        v = agg.get(f"{backend}|{carrier}")
        return "not run" if not v else f"{v['attributed_pct']:.0f}% ({v['attributed']}/{v['n']})"

    lines = [
        "# Reader bake-off - candidates vs the production pipeline, identical grading",
        "",
        f"Graded {len(rows)} field-page pairs. Single-pass candidates: full page at "
        "120 DPI, production transcription prompt, temperature 0, per-model caches "
        "committed. References from reports/layer_p.json: `vision:minicpm` is a "
        "general-VLM single-pass reference; `pipeline` is the full production "
        "pipeline (parser pages, chart specialist, measured geometry).",
        "",
        "| Backend | Prose | Table | Chart (labelled) | Chart (axis) | s/page |",
        "|---|---|---|---|---|---|",
    ]
    fmt_split = lambda s: ("not run" if not s["n"]
                           else f"{100 * s['att'] // s['n']}% ({s['att']}/{s['n']})")
    for backend in [f"vision:{m}" for m in ran]:
        t = timing[backend.removeprefix("vision:")]
        lab = split.get((backend, "labels"), {"n": 0, "att": 0})
        ax = split.get((backend, "axis"), {"n": 0, "att": 0})
        lines.append(f"| `{backend}` | {cell(backend, 'prose')} | {cell(backend, 'table')} "
                     f"| {fmt_split(lab)} | {fmt_split(ax)} | {t['sec_per_page']} |")
    for ref, label in [("vision:minicpm-v4.6:latest", "general VLM, single-pass"),
                       ("pipeline:glm-ocr->[qwen3.8:27b+geometry]",
                        "production pipeline")]:
        v = rep.get("aggregate", {})
        g = lambda c: v.get(f"{ref}|{c}", {}).get("attributed_pct")
        f = lambda c: "n/a" if g(c) is None else f"{g(c):.0f}%"
        lines.append(f"| `{ref}` ({label}) | {f('prose')} | {f('table')} | n/a | n/a | "
                     f"see layer_p |")

    lines += [
        "",
        "Chart columns for single-pass candidates are expected to be weak - no "
        "parser reads chart interiors (ParseBench 2026: most under 6%), and the "
        "production pipeline gets its axis column from code-measured geometry, not "
        "from any single model. The swap question is prose/table fidelity, callout "
        "survival (T05 top-five share), and speed; chart geometry is retained "
        "regardless of which reader wins.",
        "",
    ]
    notes = [(m, timing[m]["note"]) for m in ran if timing[m].get("note")]
    if notes:
        lines += ["## Configuration notes", ""]
        lines += [f"- `{m}`: {note}" for m, note in notes]
        lines += [""]
    lines += ["## Not run", ""]
    lines += [f"- `{m}`: {reason}" for m, reason in skipped] or ["- (none)"]

    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "bakeoff.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n" + "\n".join(lines[6:14]))
    print("\n  -> reports/bakeoff.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
