"""Run every parse backend over the corpus and write Layer P.

    python parse_corpus.py              # cached where possible
    python parse_corpus.py --fresh      # ignore the vision cache and re-read

Backends that cannot run report "not run" rather than scoring zero. A missing
Tesseract and a parser that read the page and found nothing are different facts, and
collapsing them would be the kind of quiet dishonesty this repo exists to argue
against.

Vision is the expensive one - roughly a minute and a half per page on a local 8B
model - so it reads only the pages ground truth says carry a value. That is not a
shortcut, it is the routing argument in miniature: read the pages that matter.
`route_corpus.py` measures what that selection is worth.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

from deal_ready.parse import textlayer, vision
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

    # --- Backend C: local vision model -------------------------------------------
    if not args.skip_vision:
        model = vision.DEFAULT_MODEL
        label = f"vision:{model}"
        print(f"\n{label}:  (only pages carrying a ground-truth value)")
        secs = tin = tout = 0
        ran_any = False
        for pdf in pdfs:
            recs = by_target[pdf.name.split("_")[0]]
            pages = sorted({r["page"] for r in recs})
            doc = vision.parse(pdf, pages=pages, model=model, use_cache=not args.fresh)
            if not doc.pages:
                print(f"  {pdf.name:<34} not run - {doc.notes}")
                continue
            ran_any = True
            rows += score_document(doc, recs)
            for p in doc.pages:
                secs += p.meta.get("seconds", 0) or 0
                tin += p.meta.get("tokens_in", 0) or 0
                tout += p.meta.get("tokens_out", 0) or 0
            print(f"  {pdf.name:<34} pages {pages}  "
                  f"{sum(p.meta.get('seconds',0) or 0 for p in doc.pages):>6.1f}s")
        if ran_any:
            backends.append(label)
            runtime[label] = {"seconds": round(secs, 1), "tokens_in": tin,
                              "tokens_out": tout, "dpi": vision.RENDER_DPI}

    # --- Layer P ------------------------------------------------------------------
    agg = aggregate(rows)
    table = render_table(agg, backends)

    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "layer_p.json").write_text(
        json.dumps({"rows": rows, "aggregate": agg, "backends": backends,
                    "runtime": runtime}, indent=2), encoding="utf-8")
    (REPORTS / "layer_p.md").write_text(
        "# Layer P - what each parse backend makes available\n\n"
        "Percentage of ground-truth fields recovered **and correctly attributed** to "
        "their metric, on the page the value actually lives on.\n\n"
        + table + "\n", encoding="utf-8")

    print("\n" + table)
    print(f"\n  -> reports/layer_p.md")
    for b, rt in runtime.items():
        print(f"  {b}: {rt['seconds']}s, {rt['tokens_in']} tokens in, "
              f"{rt['tokens_out']} out, {rt['dpi']} DPI")
    return 0


if __name__ == "__main__":
    sys.exit(main())
