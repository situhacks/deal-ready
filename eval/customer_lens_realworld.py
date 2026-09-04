"""The customer lens, against a target whose customers are a matter of public record.

This is the gap the earlier runs left open. The customer lens is the sharpest one in
the research layer - retention is lagging by construction and cannot contain a customer
who has not left yet - and it had never been tested against real named customers.
The synthetic corpus invents them. AppFolio, being a public filer, discloses no anchor
roster.

**Tyler Technologies closes it.** Its customers are counties, cities and courts, so the
roster is public, and their financial condition is published by rating agencies and
municipal researchers. It is the one vertical where a buyer can genuinely check whether
the customer base is in trouble.

The interesting part is the arithmetic. Both sides of the overlap are published, so the
exposure can be derived with a **pigeonhole floor** rather than estimated: if 21 of the
25 largest cities are customers and at least 20 of those same 25 have budget gaps, then
at least 21 + 20 - 25 = 16 customers are in a budget-gap year. **That is a floor, not a
guess**, and a reviewer can redo it on the back of an envelope - which is the standard
this output has to meet.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Researched 2026-09-04 through the target-research customer and end-market lenses.
FINDINGS = [
    {"lens": "customers", "claim": "customer_base_composition",
     "finding": "23 of the 25 largest US counties and 21 of the 25 largest US cities "
                "are customers; 85% of the customer base is local government.",
     "url": "https://www.tylertech.com/about-us/media-room/fast-facts",
     "quote": "23 of the 25 largest counties", "date": "2026",
     "tier": "vendor", "materiality": "high",
     "why_it_matters": "Establishes the overlap denominator. Vendor-sourced, because "
                       "the company publishes its own client counts - marked as such."},
    {"lens": "customers", "claim": "customer_fiscal_stress",
     "finding": "At least 20 of the 25 most populous US cities reported budget gaps for "
                "fiscal year 2026.",
     "url": "https://www.pew.org/en/research-and-analysis/articles/2025/08/05/big-cities-face-deficits-should-states-worry",
     "quote": "at least 20 of the nation's 25 most populous cities have reported budget "
              "gaps", "date": "2025-08", "tier": "primary", "materiality": "high",
     "why_it_matters": "The other side of the overlap, from an independent research "
                       "institution rather than the vendor."},
    {"lens": "customers", "claim": "rating_actions",
     "finding": "Chicago, Los Angeles, San Francisco and Washington were all downgraded "
                "between December 2024 and April 2025; each of the three largest cities "
                "took a negative rating action in H1 2026, with New York City placed on "
                "negative outlook by Moody's and Fitch.",
     "url": "https://comptroller.nyc.gov/reports/the-risks-to-the-citys-credit-ratings/",
     "quote": "placing New York City on negative outlook", "date": "2026",
     "tier": "primary", "materiality": "high",
     "why_it_matters": "Named, dated stress at specific customers rather than a "
                       "sector generalisation."},
    {"lens": "end_market", "claim": "sector_outlook",
     "finding": "Only 45% of local government finance officers felt optimistic about "
                "meeting fiscal needs in FY2026, down from 64% a year earlier; the "
                "local government sector outlook is 'cautious' as expense pressure "
                "outweighs slowing revenue growth.",
     "url": "https://www.hilltopsecurities.com/municipal_commentary/the-municipal-market-in-2026-hilltopsecurities-sector-credit-outlooks/",
     "quote": "expense pressure is expected to outweigh positive but slowing revenue "
              "growth", "date": "2026", "tier": "practitioner", "materiality": "medium",
     "why_it_matters": "A 19-point fall in finance-officer optimism in one year is the "
                       "leading indicator for discretionary software budgets."},
]

# Both sides of the overlap are published, so the exposure has a derivable floor.
LARGEST_CITIES = 25
CUSTOMERS_AMONG_THEM = 21
STRESSED_AMONG_THEM = 20


def overlap_floor(universe: int, a: int, b: int) -> int:
    """The smallest possible intersection of two subsets of a shared universe.

    Inclusion-exclusion, bounded at zero. Worth doing as arithmetic rather than
    estimation because the result is checkable by hand, which an estimate is not.
    """
    return max(0, a + b - universe)


def main() -> int:
    floor = overlap_floor(LARGEST_CITIES, CUSTOMERS_AMONG_THEM, STRESSED_AMONG_THEM)
    pct = round(100.0 * floor / CUSTOMERS_AMONG_THEM, 1)

    print("CUSTOMER LENS - Tyler Technologies (customers are public entities)\n")
    for f in FINDINGS:
        print(f"[{f['lens']}/{f['tier']}] {f['finding']}")
        print(f"    {f['date']} · {f['url'][:78]}")
    print()
    print("DERIVED EXPOSURE (pigeonhole, not estimation)")
    print(f"  universe                       {LARGEST_CITIES} largest US cities")
    print(f"  of those, customers            {CUSTOMERS_AMONG_THEM}")
    print(f"  of those, with FY26 budget gap {STRESSED_AMONG_THEM}")
    print(f"  minimum overlap                {CUSTOMERS_AMONG_THEM} + "
          f"{STRESSED_AMONG_THEM} - {LARGEST_CITIES} = {floor}")
    print(f"\n  At least {floor} of the {CUSTOMERS_AMONG_THEM} largest-city customers "
          f"({pct}%) are in a budget-gap year.")
    print("  This is a floor. The true number is at least this and may be higher.\n")

    print("COVERAGE, stated")
    print("  - Only the 25 largest cities are covered. Tyler reports 15,000 locations;")
    print("    this says nothing about the other ~14,975.")
    print("  - County customers are NOT covered - the stress research found is city-level.")
    print("  - Budget gap is not the same as churn. It is a pressure signal on a")
    print("    discretionary line, not evidence any contract is at risk.")
    print("  - The customer-count side is vendor-published and unaudited.\n")

    out = ROOT / "reports" / "customer_lens_realworld.json"
    out.write_text(json.dumps({
        "target": "Tyler Technologies", "researched": "2026-09-04",
        "why_this_target": "customers are public entities, so the roster and their "
                           "financial condition are both matters of public record",
        "findings": FINDINGS,
        "derived_exposure": {
            "method": "pigeonhole floor via inclusion-exclusion",
            "universe": LARGEST_CITIES, "customers": CUSTOMERS_AMONG_THEM,
            "stressed": STRESSED_AMONG_THEM, "minimum_overlap": floor,
            "minimum_share_of_large_city_customers_pct": pct,
            "checkable_by_hand": f"{CUSTOMERS_AMONG_THEM} + {STRESSED_AMONG_THEM} - "
                                 f"{LARGEST_CITIES} = {floor}",
        },
        "coverage": {
            "covered": "the 25 largest US cities only",
            "not_covered": "roughly 14,975 other locations; all county customers",
            "caveat": "a budget gap is a pressure signal on a discretionary line, not "
                      "evidence that any contract is at risk",
            "vendor_sourced": "the customer-count side is published by the company",
        },
    }, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
