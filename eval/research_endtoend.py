"""End to end on a real company: research, base rate, scenario, and does research move it.

The research layer had been built and never run. It could not be run on the synthetic
corpus because those companies do not exist - there is no founder to look up and no
customer to check. So it runs here against a real one.

**AppFolio, chosen because the whole stack can run on it**: real filings already pulled
for the forecasting work, a real vertical (property management software), a real
customer base, and a real end market. It is also an easier research target than a
private company would be, which is stated rather than glossed.

The findings below were gathered by running the `target-research` lenses for real. They
are committed rather than re-fetched so the comparison reproduces, and every one carries
its source, date and tier - including the ones that are the company marketing itself,
which are marked `vendor` and are the reason the tier field exists.

The experiment: run the scenario layer with and without the research block and measure
whether the assumptions actually change. **If outward research does not move the
conclusion, it is decoration.**
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from deal_ready.signals import baserate, scenario           # noqa: E402
from eval.sensitivity import jaccard, words                 # noqa: E402

# The research pass, run 2026-09-04 against the lenses in the target-research skill.
RESEARCH = [
    {"lens": "operators",
     "finding": "Long-serving board chair Andreas von Blottnitz and director Janet Kerr "
                "retired effective 2026-06-29; CEO Shane Trigg took the chairman role "
                "and a new lead independent director was created.",
     "url": "https://ir.appfolioinc.com/corporate-governance/board-of-directors",
     "quote": "retired effective June 29, 2026", "date": "2026-06",
     "tier": "primary", "materiality": "medium",
     "why_it_matters": "CEO and chair combining reduces board independence at the same "
                       "moment two long-tenured directors left."},
    {"lens": "operators",
     "finding": "CEO compensation agreement amended 2026-04-09, increasing salary, bonus "
                "and equity awards.",
     "url": "https://ir.appfolioinc.com/board-member/shane-trigg",
     "quote": "increasing salary, bonus, and equity awards", "date": "2026-04",
     "tier": "primary", "materiality": "low",
     "why_it_matters": "Retention economics for the CEO were reset shortly before the "
                       "governance change."},
    {"lens": "market",
     "finding": "PMS-native AI shipped aggressively across all four incumbents in "
                "2024-25 (Yardi Chat IQ, Entrata ELI+, AppFolio Realm-X, RealPage Lea); "
                "by 2026 operators treat it as a complement rather than a replacement.",
     "url": "https://www.thesisdriven.com/letters/the-future-of-the-property-management/",
     "quote": "highly resistant to disruption over the years", "date": "2026",
     "tier": "practitioner", "materiality": "medium",
     "why_it_matters": "AI parity across incumbents means it is table stakes, not a "
                       "moat - and new entrants are raising capital against them."},
    {"lens": "market",
     "finding": "Category leadership claims for this product come from the vendor's own "
                "blog and are not independent.",
     "url": "https://www.appfolio.com/blog/best-property-management-softwares-compared-2026",
     "quote": "Best Property Management Software 2026", "date": "2026",
     "tier": "vendor", "materiality": "low",
     "why_it_matters": "Marked so it cannot be mistaken for third-party validation."},
    {"lens": "end_market",
     "finding": "National asking rent growth decelerated to 0.1% year over year, the "
                "weakest pace since Q4 2010.",
     "url": "https://www.mmcginvest.com/post/u-s-multi-family-market-outlook-2026-current-conditions-investment-trends-and-five-year-forecast",
     "quote": "decelerated to just 0.1% year-over-year, the weakest pace since",
     "date": "2026", "tier": "practitioner", "materiality": "high",
     "why_it_matters": "Customers price software against rent roll; flat rents compress "
                       "what they will pay per unit."},
    {"lens": "end_market",
     "finding": "Property insurance premiums rising 15-30% annually in Florida, Texas "
                "and Louisiana, squeezing operator margins while rent growth stalls.",
     "url": "https://westpointproperty.com/property-management-trends-2026/",
     "quote": "annual premium increases of 15% to 30%", "date": "2026",
     "tier": "practitioner", "materiality": "high",
     "why_it_matters": "The customer base is in a margin squeeze, which is where "
                       "software budgets get cut first."},
    {"lens": "customers",
     "finding": "The property management acquisition market reopened in 2026 on improved "
                "lending; single-family-rental managers are consolidating at premium "
                "EBITDA multiples.",
     "url": "https://www.yourfloridabusinessbroker.com/property-management-ma-in-2026-why-smart-owners-are-preparing-for-the-next-wave-of-consolidation/",
     "quote": "one of the strongest opportunities owners have seen in years",
     "date": "2026", "tier": "vendor", "materiality": "high",
     "why_it_matters": "Customer consolidation arrives as churn only after two customers "
                       "become one contract - it is invisible in retention until it lands."},
]

COVERAGE = {
    "operators": "board and CEO changes covered from filings; no research on engineering "
                 "or finance leadership tenure",
    "ownership": "NOT RUN - public company, no sale process to explain",
    "customers": "end-market and consolidation covered; NO named customer was researched, "
                 "because a public filer does not disclose an anchor roster",
    "market": "incumbents and AI parity covered; new entrants named but not sized",
    "end_market": "rent growth and insurance covered; no regional breakdown",
    "contracts": "NOT RUN - no concentration flag to justify it",
    "security": "NOT RUN - no breach signal surfaced in the market pass",
    "talent": "NOT RUN - modern stack, no legacy flag",
}

TARGET = {
    "target_id": "APPF", "code_name": "AppFolio",
    "metrics": {"arr_usd": 900_000_000, "grr_pct": 92.0, "nrr_pct": 112.0,
                "yoy_growth_pct": 16.0, "recurring_pct": 94.0},
    "fit": {"score": None, "tier_label": "outside the mandate band - far too large"},
    "findings": [],
}


def main() -> int:
    deals = json.loads((ROOT / "data" / "dealbook.json").read_text("utf-8"))
    br = baserate.compute({"arr_usd": TARGET["metrics"]["arr_usd"],
                           "grr_pct": TARGET["metrics"]["grr_pct"]}, deals).summary()

    print("BASE RATE")
    print(f"  status: {br['status']}")
    print(f"  matched on: {br.get('matched_on')}  n={br.get('n_comparables')}\n")

    without, s1 = scenario.run(TARGET, base_rate=br, signal=None, research=None)
    with_r, s2 = scenario.run(TARGET, base_rate=br, signal=None, research=RESEARCH)

    t1 = " ".join(f"{a.text} {a.rests_on} {a.falsified_by}" for a in without)
    t2 = " ".join(f"{a.text} {a.rests_on} {a.falsified_by}" for a in with_r)
    sim = jaccard(words(t1), words(t2))

    print(f"SCENARIO without research: {len(without)} assumptions ({s1})")
    print(f"SCENARIO with research:    {len(with_r)} assumptions ({s2})")
    print(f"\nsimilarity between them: {sim}")
    print("lower means outward research actually changed the conclusion\n")

    print("--- assumptions WITH research ---")
    for i, a in enumerate(with_r, 1):
        print(f"{i}. {a.text}")
        print(f"   rests on: {a.rests_on}")
        print(f"   falsified by: {a.falsified_by}")

    out = ROOT / "reports" / "research_endtoend.json"
    out.write_text(json.dumps({
        "target": TARGET["code_name"], "researched": "2026-09-04",
        "base_rate": br, "research": RESEARCH, "coverage": COVERAGE,
        "similarity_with_vs_without_research": sim,
        "assumptions_without_research": [a.to_dict() for a in without],
        "assumptions_with_research": [a.to_dict() for a in with_r],
    }, indent=2) + "\n", encoding="utf-8")
    print(f"\nwrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
