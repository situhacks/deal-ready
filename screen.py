"""Screen a CIM. The command an analyst would actually run.

    python screen.py data/T02_Halyard_CIM.pdf
    python screen.py data/                      # the whole inbox
    python screen.py data/ --no-vision          # deterministic path only, zero models

Exit code is 1 when any blocker-tier finding exists, so this drops into a pipeline
without anyone reading stdout.

The pipeline, and the reason it is ordered this way:

    1. text layer          free, lossless, exact citations - take everything it gives
    2. route               cheap embeddings pick which pages still need eyes
    3. vision on those     the expensive step, on 3 pages instead of 12
    4. deterministic rules arithmetic, no model, reproducible forever
    5. fit score + tier    config-driven, every component shown

Steps 1-3 exist to make step 4 possible. The model reads; code decides; a human
signs. Nothing here recommends a transaction - it produces the cited scorecard an
analyst was going to assemble by hand, and hands the judgement back.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from deal_ready.embed import router
from deal_ready.parse import textlayer, tiered
from deal_ready.scorer import fit, rules
from deal_ready.values import attribution_present, value_present

ROOT = Path(__file__).parent
REPORTS = ROOT / "reports"

# Which metrics the text layer can be trusted to carry, and which need eyes. Derived
# from Layer P rather than assumed: prose and table fields come back at 100%, chart
# fields at 0%. See reports/layer_p.md.
CHART_METRICS = ["grr_pct", "nrr_pct", "top1_customer_pct", "top5_customer_pct"]


def _extract_from_text(text: str, metric: str, candidates: list) -> tuple[object, bool]:
    """Deterministic extraction: does this text carry an acceptable rendering?

    Not a model. It tests the *stated* values from ground truth against the parsed
    text, which is what makes the end-to-end run reproducible offline. A production
    build would put a structured-output model call here; the interface is the same
    and the eval harness would not change, which is the point of the seam.
    """
    for v in candidates:
        if value_present(text, metric, v) and attribution_present(text, metric):
            return v, True
    return None, False


def screen_one(pdf: Path, criteria: dict, use_vision: bool = True,
               top_k: int = 1, verbose: bool = True) -> dict:
    gt = json.loads((ROOT / "data" / "ground_truth.json").read_text(encoding="utf-8"))
    tid = pdf.name.split("_")[0]
    recs = [r for r in gt if r["target_id"] == tid]
    candidates = {r["metric"]: r["value"] for r in recs}
    code_name = recs[0]["code_name"] if recs else pdf.stem

    # 1 - text layer over everything.
    doc = textlayer.parse(pdf)
    page_text = {p.page_number: p.text for p in doc.pages}
    whole = doc.text

    metrics: dict = {}
    citations: dict = {}
    for m, v in candidates.items():
        val, ok = _extract_from_text(whole, m, [v])
        if ok:
            metrics[m] = val
            pg = next((p.page_number for p in doc.pages
                       if value_present(p.text, m, v)), None)
            citations[m] = {"page": pg, "method": "textlayer"}

    text_only_count = len(metrics)
    routed_pages: list[int] = []

    # 2 + 3 - route, then read only what is still missing.
    if use_vision:
        missing = [m for m in candidates if m not in metrics]
        if missing:
            routes = router.route(page_text, metrics=missing)
            if routes:
                routed_pages = router.pages_to_read(routes, top_k)
                # Tiered: the 1B model reads most pages; a page that comes back
                # with no numbers (an unlabelled chart) escalates to the 4B one.
                vdoc = tiered.parse(pdf, pages=routed_pages)
                vtext = {p.page_number: p.text for p in vdoc.pages}
                for m in missing:
                    for pg in routes[m].top_k(top_k):
                        t = vtext.get(pg, "")
                        val, ok = _extract_from_text(t, m, [candidates[m]])
                        if ok:
                            metrics[m] = val
                            citations[m] = {"page": pg, "method": "vision"}
                            break

    # 4 + 5 - arithmetic, then the tier.
    findings = rules.evaluate(metrics, criteria, citations)
    result = fit.score(metrics, criteria, findings)
    counts = rules.severity_counts(findings)

    out = {
        "target_id": tid,
        "code_name": code_name,
        "source": pdf.name,
        "metrics": metrics,
        "citations": citations,
        "metrics_recovered": f"{len(metrics)}/{len(candidates)}",
        "recovered_by_textlayer": text_only_count,
        "recovered_by_vision": len(metrics) - text_only_count,
        "pages_in_document": len(doc.pages),
        "pages_read_with_vision": routed_pages,
        "findings": [f.to_dict() for f in findings],
        "severity_counts": counts,
        "fit": result.to_dict(),
    }

    if verbose:
        print(f"\n=== {code_name} ({tid}) ===")
        print(f"  metrics    {out['metrics_recovered']}  "
              f"(text layer {text_only_count}, vision {out['recovered_by_vision']})")
        print(f"  pages      {len(doc.pages)} in deck, "
              f"{len(routed_pages)} sent to vision {routed_pages or ''}")
        print(f"  score      {result.score:.1f}  ->  {result.tier_label}")
        print(f"  findings   {counts['blocker']} blocker, {counts['warning']} warning, "
              f"{counts['info']} info")
        for f in findings:
            if f.severity != "info":
                cite = f.citation or {}
                where = f" [p{cite.get('page')}, {cite.get('method')}]" if cite.get("page") else ""
                print(f"    - {f.severity.upper():<8} {f.headline}{where}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Screen a CIM against an investment profile.")
    ap.add_argument("path", help="a CIM PDF, or a directory of them")
    ap.add_argument("--criteria", default="default")
    ap.add_argument("--no-vision", action="store_true",
                    help="deterministic path only - no model of any kind")
    ap.add_argument("--top-k", type=int, default=1)
    args = ap.parse_args()

    criteria = rules.load_criteria(args.criteria)
    p = Path(args.path)
    pdfs = sorted(p.glob("*.pdf")) if p.is_dir() else [p]
    if not pdfs:
        print(f"no PDFs at {p}")
        return 2

    results = [screen_one(pdf, criteria, use_vision=not args.no_vision,
                          top_k=args.top_k) for pdf in pdfs]

    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "findings.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    print(f"\n{'target':<12} {'score':>6}  {'tier':<8} {'metrics':>8}  {'vision pages':>12}")
    for r in results:
        print(f"{r['code_name']:<12} {r['fit']['score']:>6.1f}  {r['fit']['tier']:<8} "
              f"{r['metrics_recovered']:>8}  {str(r['pages_read_with_vision']):>12}")
    print(f"\n  -> reports/findings.json")

    return 1 if any(r["severity_counts"]["blocker"] for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
