"""Build the synthetic CIM corpus.

    python generate.py

Writes one PDF deck per target into data/, plus data/ground_truth.json.

No network, no model, no API key. This step is pure Python so the corpus a reviewer
evaluates is the same corpus every time, on any machine.

The leak check at the end is not ceremony. The parse comparison only means something
if chart-carried values are genuinely absent from the text layer, so we verify that
against the file we just wrote rather than trusting that we remembered to.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from deal_ready.generator.profiles import ALL_PROFILES
from deal_ready.generator.render import render_cim

DATA = Path(__file__).parent / "data"


def _page_texts(pdf_path: Path) -> list[str]:
    from pypdf import PdfReader
    return [(p.extract_text() or "") for p in PdfReader(str(pdf_path)).pages]


def check_no_leaks(pdf_path: Path, records: list[dict]) -> list[str]:
    """Prove every chart-carried value is absent from the extractable text.

    A leak would silently invalidate the parse comparison: a parser could 'read the
    chart' by finding the number in a sentence. Better to fail the build.
    """
    text = " ".join(_page_texts(pdf_path))
    normalised = text.replace(",", "")
    problems = []
    for r in records:
        if r["carrier"] != "chart":
            continue
        v = r["value"]
        candidates = {f"{v:.0f}", f"{v:.1f}"}
        for c in candidates:
            # A bare "94" could collide with a year or a headcount, so require the
            # percent form that the metric would actually be written in.
            if f"{c}%" in normalised or f"{c} percent" in normalised:
                problems.append(
                    f"{r['target_id']}/{r['metric']}: chart-only value {c}% found in text layer")
                break
    return problems


def main() -> int:
    DATA.mkdir(parents=True, exist_ok=True)
    all_records: list[dict] = []
    leaks: list[str] = []

    for profile in ALL_PROFILES:
        out = DATA / f"{profile['target_id']}_{profile['code_name']}_CIM.pdf"
        records = render_cim(profile, out)
        found = check_no_leaks(out, records)
        leaks += found
        all_records += records
        pages = records[0]["total_pages"]
        status = "LEAK" if found else "ok"
        print(f"  {out.name:<34} {pages:>2} pages  {len(records):>2} metrics  [{status}]")

    gt = DATA / "ground_truth.json"
    gt.write_text(json.dumps(all_records, indent=2), encoding="utf-8")

    carriers = {}
    for r in all_records:
        carriers[r["carrier"]] = carriers.get(r["carrier"], 0) + 1

    print(f"\n  ground truth -> {gt.relative_to(Path(__file__).parent)}")
    print(f"  {len(all_records)} records across {len(ALL_PROFILES)} targets")
    print("  carriers: " + ", ".join(f"{k}={v}" for k, v in sorted(carriers.items())))

    if leaks:
        print("\nFAILED - chart-only values leaked into the text layer:")
        for p in leaks:
            print(f"  - {p}")
        print("\nThe parse comparison would be invalid. Fix the renderer before continuing.")
        return 1

    print("\n  leak check passed: no chart-only value appears in any text layer")
    return 0


if __name__ == "__main__":
    sys.exit(main())
