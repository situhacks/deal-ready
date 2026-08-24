"""Run every parse backend over the corpus and write Layer P.

    python parse_corpus.py              # cached where possible
    python parse_corpus.py --fresh      # ignore the vision cache and re-read

Backends that cannot run report "not run" rather than scoring zero. A missing
Tesseract and a parser that read the page and found nothing are different facts, and
collapsing them would be the kind of quiet dishonesty this repo exists to argue
against.

Vision is the expensive one, so it reads only the pages ground truth says carry a
value. That is not a shortcut, it is the routing argument in miniature: read the pages
that matter. `route_corpus.py` measures what that selection is worth.

Two vision configurations run, both from the same cache: the cheap 1B model alone
(the capability boundary row - what a page-level read can and cannot see), and the
tiered pipeline the tool actually ships (cheap page read, strong exhibit re-read -
see deal_ready/parse/tiered.py).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

from deal_ready.parse import textlayer, tiered, vision
from eval.recoverability import aggregate, load_ground_truth, render_table, score_document

ROOT = Path(__file__).parent
DATA = ROOT / "data"
REPORTS = ROOT / "reports"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fresh", action="store_true", help="ignore the vision cache")
    ap.add_argument("--skip-vision", action="store_true")
    args = ap.parse_args()

    gt = load_ground_truth()
    by_target = defaultdict(list)
    for r in gt:
        by_target[r["target_id"]].append(r)

    pdfs = sorted(DATA.glob("*.pdf"))
    rows: list[dict] = []
    backends: list[str] = []
    runtime: dict = {}

    # --- Backend A: text layer (always available) --------------------------------
    print("textlayer:")
    for pdf in pdfs:
        doc = textlayer.parse(pdf)
        rows += score_document(doc, by_target[pdf.name.split("_")[0]])
        print(f"  {pdf.name:<34} {doc.char_count():>6} chars over {len(doc.pages)} pages")
    backends.append("textlayer")

    # --- Backend C: local vision, two configurations ------------------------------
    def run_vision(label: str, parse_doc) -> None:
        nonlocal rows, backends, runtime
        print(f"\n{label}:  (only pages carrying a ground-truth value)")
        secs = tin = tout = 0
        ran_any = False
        for pdf in pdfs:
            recs = by_target[pdf.name.split("_")[0]]
            pages = sorted({r["page"] for r in recs})
            doc = parse_doc(pdf, pages, use_cache=not args.fresh)
            if not doc.pages:
                print(f"  {pdf.name:<34} not run - {doc.notes}")
                continue
            ran_any = True
            rows += score_document(doc, recs)
            for p in doc.pages:
                secs += p.meta.get("seconds", 0) or 0
                tin += p.meta.get("tokens_in", 0) or 0
                tout += p.meta.get("tokens_out", 0) or 0
            esc = [p.page_number for p in doc.pages if p.meta.get("tier") == "escalated"]
            print(f"  {pdf.name:<34} pages {pages}  "
                  f"{sum(p.meta.get('seconds',0) or 0 for p in doc.pages):>6.1f}s"
                  + (f"  escalated {esc}" if esc else ""))
        if ran_any:
            backends.append(label)
            runtime[label] = {"seconds": round(secs, 1), "tokens_in": tin,
                              "tokens_out": tout, "dpi": vision.RENDER_DPI}

    if not args.skip_vision:
        run_vision(
            f"vision:{vision.DEFAULT_MODEL}",
            lambda pdf, pages, use_cache: vision.parse(
                pdf, pages=pages, model=vision.DEFAULT_MODEL, use_cache=use_cache))
        run_vision(
            f"tiered:{tiered.CHEAP_MODEL}->{tiered.STRONG_MODEL}",
            lambda pdf, pages, use_cache: tiered.parse(
                pdf, pages=pages, use_cache=use_cache))

    # --- Layer P ------------------------------------------------------------------
    agg = aggregate(rows)
    table = render_table(agg, backends)

    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "layer_p.json").write_text(
        json.dumps({"rows": rows, "aggregate": agg, "backends": backends,
                    "runtime": runtime}, indent=2), encoding="utf-8")
    # The chart row hides the finding that matters, so split it out.
    split = defaultdict(lambda: {"n": 0, "att": 0})
    for r in rows:
        if r["carrier"] != "chart":
            continue
        kind = "labels" if r["labelled_in_chart"] else "axis"
        s = split[(r["backend"], kind)]
        s["n"] += 1
        s["att"] += int(r["attributed"])

    def _cell(v):
        return "not run" if not v else f"{100*v['att']/v['n']:.0f}% ({v['att']}/{v['n']})"

    md = [
        "# Layer P - what each parse backend makes available",
        "",
        "Percentage of ground-truth fields recovered **and correctly attributed** to "
        "their metric, on the page the value actually lives on. This grades the parser, "
        "not the extractor: it is a ceiling on what any downstream model could achieve "
        "given what it was handed.",
        "",
        table,
        "",
        "## The chart row, split by whether the chart printed its values",
        "",
        "This is the finding the aggregate hides. Reading a printed data label is "
        "recognition. Reading a value off an axis is spatial reasoning about where a "
        "point sits between gridlines. They are different tasks, and they fail "
        "differently.",
        "",
        "| Backend | Charts with data labels | Charts read off the axis |",
        "|---|---|---|",
    ]
    for b in backends:
        md.append(f"| `{b}` | {_cell(split.get((b, 'labels')))} | "
                  f"{_cell(split.get((b, 'axis')))} |")
    md += [
        "",
        "**A value read off an axis is measured, and still flagged.** The v1 "
        "configuration landed around 70% on the axis column: the strong tier was "
        "burning its budget inside a thinking block and reading a lossy page render. "
        "With reasoning disabled and the exhibit re-read from the PDF's native "
        "embedded image, the tiered row reads the axis column in full on the "
        "committed eval. Every axis-read value still ships flagged - an "
        "interpolated value is not a printed one, and the flag is where the human "
        "signs.",
        "",
    ]
    (REPORTS / "layer_p.md").write_text("\n".join(md), encoding="utf-8")

    print("\n" + table)
    print(f"\n  -> reports/layer_p.md")
    for b, rt in runtime.items():
        print(f"  {b}: {rt['seconds']}s, {rt['tokens_in']} tokens in, "
              f"{rt['tokens_out']} out, {rt['dpi']} DPI")
    return 0


if __name__ == "__main__":
    sys.exit(main())
