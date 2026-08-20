"""Layer P - what each parse backend makes *available* to everything downstream.

This measures the parser, not the extractor, and the distinction is the point.

We ask a deliberately narrow question: after this backend has run, is the true value
present on the page it lives on, and is it attributable to the right metric? If the
answer is no, no extractor - however good - can recover it. So this is a **ceiling**,
not an accuracy score. It is the most a downstream model could possibly achieve given
what the parser handed it.

Framing it as a ceiling keeps the result honest in both directions. A backend cannot
be blamed for a model's later mistakes, and a model cannot be credited for reading
something it was never shown.

Two grades per field:

    present     - an acceptable rendering of the value appears on the right page
    attributed  - the page also identifies which metric it belongs to

`attributed` is the one that matters. "34%" adrift on a page with no indication that
it is the largest customer's share of ARR is not a recovered concentration figure -
it is a number waiting to be misread.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from deal_ready.values import attribution_present, value_present

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

CARRIER_ORDER = ["prose", "table", "chart"]
CARRIER_LABEL = {
    "prose": "Prose (narrative claims)",
    "table": "Table cells",
    "chart": "Chart-only values",
}


def load_ground_truth() -> list[dict]:
    return json.loads((DATA / "ground_truth.json").read_text(encoding="utf-8"))


def score_document(doc, records: list[dict]) -> list[dict]:
    """Grade one parsed document against the ground truth for its target."""
    out = []
    for r in records:
        page = doc.page(r["page"])
        text = page.text if page else ""
        present = value_present(text, r["metric"], r["value"])
        attributed = present and attribution_present(text, r["metric"])
        out.append({
            **{k: r[k] for k in
               ("target_id", "code_name", "metric", "label", "value", "carrier",
                "labelled_in_chart", "page")},
            "backend": doc.backend,
            "present": present,
            "attributed": attributed,
        })
    return out


def aggregate(rows: list[dict]) -> dict:
    """Roll results up to backend x carrier, which is the table people read."""
    buckets = defaultdict(lambda: {"n": 0, "present": 0, "attributed": 0})
    for r in rows:
        b = buckets[(r["backend"], r["carrier"])]
        b["n"] += 1
        b["present"] += int(r["present"])
        b["attributed"] += int(r["attributed"])
    return {
        f"{backend}|{carrier}": {
            "n": v["n"],
            "present": v["present"],
            "attributed": v["attributed"],
            "present_pct": round(100.0 * v["present"] / v["n"], 1) if v["n"] else 0.0,
            "attributed_pct": round(100.0 * v["attributed"] / v["n"], 1) if v["n"] else 0.0,
        }
        for (backend, carrier), v in buckets.items()
    }


def render_table(agg: dict, backends: list[str]) -> str:
    """The comparison table, as markdown, for the README."""
    head = "| Field type | " + " | ".join(backends) + " |"
    rule = "|---|" + "|".join(["---"] * len(backends)) + "|"
    lines = [head, rule]
    for carrier in CARRIER_ORDER:
        cells = []
        for b in backends:
            v = agg.get(f"{b}|{carrier}")
            cells.append("not run" if v is None
                         else f"{v['attributed_pct']:.0f}% ({v['attributed']}/{v['n']})")
        lines.append(f"| {CARRIER_LABEL[carrier]} | " + " | ".join(cells) + " |")
    return "\n".join(lines)
