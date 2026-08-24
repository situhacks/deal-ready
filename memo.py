"""Draft screening memos for screened CIMs. The stage after screen.py.

    python memo.py data/T05_Ashgrove_CIM.pdf
    python memo.py data/                    # the whole inbox
    python memo.py data/ --no-model         # value flags only, no narrative pass

Writes reports/memo_<target>.md and reports/callouts_<target>.json. The memo is the
artifact a reviewer edits; capture.py turns that edit into correction records.

The narrative pass runs a local model through the same door as everything else and
fails soft: an unavailable model means the section is skipped with a note, never
faked. Value-level call-outs are mechanical and survive --no-model.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from deal_ready.memo.draft import _load_examples, draft as draft_memo
from deal_ready.parse import textlayer
from deal_ready.scorer import rules
from screen import REPORTS, screen_one


def page_marked(pdf: Path) -> str:
    doc = textlayer.parse(pdf)
    return "\n".join(f"--- p{p.page_number} ---\n{p.text}" for p in doc.pages)


def memo_one(pdf: Path, criteria: dict, use_model: bool) -> dict:
    result = screen_one(pdf, criteria, use_vision=True, verbose=False)
    tid = result["target_id"]
    artifacts = draft_memo(result, criteria,
                           doc_text=page_marked(pdf) if use_model else None,
                           use_model=use_model)
    (REPORTS / f"memo_{tid}.md").write_text(artifacts["markdown"], encoding="utf-8")
    (REPORTS / f"callouts_{tid}.json").write_text(
        json.dumps({"target_id": tid, "draft_version": "v2",
                    "judge_status": artifacts["judge_status"],
                    "examples_folded": len(_load_examples()),
                    "callouts": artifacts["callouts"]}, indent=2),
        encoding="utf-8")

    kinds = {}
    for c in artifacts["callouts"]:
        kinds[c["kind"]] = kinds.get(c["kind"], 0) + 1
    print(f"{result['code_name']:<12} score {result['fit']['score']:>5.1f}  "
          f"memo_{tid}.md  callouts: "
          + (", ".join(f"{k} x{v}" for k, v in sorted(kinds.items())) or "none"))
    return {"tid": tid, "status": artifacts["judge_status"]}


def main() -> int:
    ap = argparse.ArgumentParser(description="Draft screening memos with call-outs.")
    ap.add_argument("path", help="a CIM PDF, or a directory of them")
    ap.add_argument("--criteria", default="default")
    ap.add_argument("--no-model", action="store_true",
                    help="mechanical call-outs only - no narrative pass")
    args = ap.parse_args()

    criteria = rules.load_criteria(args.criteria)
    p = Path(args.path)
    pdfs = sorted(p.glob("*.pdf")) if p.is_dir() else [p]
    if not pdfs:
        print(f"no PDFs at {p}")
        return 2

    statuses = [memo_one(pdf, criteria, use_model=not args.no_model) for pdf in pdfs]
    skipped = [s["tid"] for s in statuses if s["status"] != "ok"]
    print(f"\n  -> memos + callouts in {REPORTS.name}/"
          + (f"  (narrative skipped: {', '.join(skipped)})" if skipped else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
