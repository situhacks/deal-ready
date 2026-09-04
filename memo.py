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
from deal_ready.signals import baserate, customers as customer_signal
from deal_ready.parse import textlayer
from deal_ready.scorer import rules
from screen import REPORTS, screen_one


def parse_pages(pdf: Path) -> tuple[str, dict[int, str]]:
    doc = textlayer.parse(pdf)
    marked = "\n".join(f"--- p{p.page_number} ---\n{p.text}" for p in doc.pages)
    return marked, {p.page_number: p.text for p in doc.pages}


def memo_one(pdf: Path, criteria: dict, use_model: bool) -> dict:
    result = screen_one(pdf, criteria, use_vision=True, verbose=False)
    tid = result["target_id"]
    marked, pages = parse_pages(pdf)
    # Outside signal: the anchor-customer roster off the deck, joined to whatever
    # research is available about those customers. On this synthetic corpus the
    # research verdicts come from the generator, which is what makes the aggregation
    # scoreable offline; against a real document they come from the plugin's research
    # pass. Either way the signal is context, never a score.
    sig = None
    roster = _roster_for(tid, pages, result)
    if roster:
        sig = customer_signal.build(roster).to_dict()

    # Base rate: what comparable past acquisitions went on to do. Auditable by
    # construction - the memo prints the deal ids the cohort was built from.
    br = None
    book = Path(__file__).parent / "data" / "dealbook.json"
    if book.exists():
        br = baserate.compute(
            {"arr_usd": result.get("metrics", {}).get("arr_usd"),
             "grr_pct": result.get("metrics", {}).get("grr_pct")},
            json.loads(book.read_text(encoding="utf-8"))).summary()

    artifacts = draft_memo(result, criteria,
                           doc_text=marked if use_model else None,
                           use_model=use_model, page_texts=pages, signal=sig,
                           base_rate=br)
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



def _roster_for(tid: str, pages: dict, result: dict) -> list[dict]:
    """The anchor-customer roster, with research verdicts attached where known.

    Parsed off the deck so the extraction is exercised for real, then joined to the
    generator's verdicts by name. A customer parsed but not matched keeps its share
    and carries no verdict, which lands it in the unresearched bucket rather than
    quietly counting as healthy.
    """
    from deal_ready.generator.profiles import ALL_PROFILES
    arr = result.get("metrics", {}).get("arr_usd")
    if not pages or not arr:
        return []
    # Only the roster page. Joining the whole document pulled rows out of the
    # financial table and counted them as customers - two phantom entries per target,
    # which then reported as "unresearched" and made the coverage line lie.
    roster_pages = [n for n, t in pages.items() if "anchor customers" in t.lower()]
    if not roster_pages:
        return []
    text = chr(10).join(pages[n] for n in sorted(roster_pages))
    parsed = customer_signal.parse_roster(text, arr)
    if not parsed:
        return []
    known = {}
    for pr in ALL_PROFILES:
        if pr["target_id"] == tid:
            known = {c["name"]: c for c in pr.get("customers", [])}
    out = []
    for name, pct in parsed:
        k = known.get(name)
        out.append({"name": name, "pct_arr": pct,
                    "distress": (k or {}).get("distress"),
                    "note": (k or {}).get("note", "")})
    return out


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
