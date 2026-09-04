"""A synthetic history of past acquisitions, with what happened next.

A screen reads a snapshot. The question it cannot answer from the document is "what
usually happens to businesses like this one" - and that answer does not live in the
CIM, it lives in the acquirer's own history.

So the corpus grows one: 120 completed deals, each with the profile at acquisition and
the outcome three years later. Deterministic and seeded, like everything else here.

**What this is not.** These are invented outcomes. A real acquirer's dealbook is the
one genuinely proprietary prediction asset they own; this is a stand-in that lets the
machinery be built and tested. Every number the base-rate layer produces on this corpus
is a fact about a fabricated history, and the code says so wherever it reports one.

**What makes it useful anyway.** The relationships encoded here are the ones a
permanent-hold buyer would actually expect - retention at entry predicts outcome far
more than growth does, concentration hurts, and low recurring share hurts most - so a
base-rate layer built against it exercises the real reasoning shape.
"""

from __future__ import annotations

import numpy as np

VERTICALS = ["healthcare", "government", "education", "field services", "logistics",
             "manufacturing", "property", "legal", "financial services", "agriculture"]
REGIONS = ["North America", "UK", "Europe", "ANZ", "Brazil"]

N_DEALS = 120
SEED = 20260904
OUTCOME_YEARS = 3


def build(n: int = N_DEALS, seed: int = SEED) -> list[dict]:
    """One row per completed acquisition, oldest first.

    `outcome_revenue_cagr` is what the business actually did over three years of
    ownership. `underwritten_cagr` is what was assumed at the time - deliberately
    optimistic on average, because that is the bias a calibration layer exists to
    find.
    """
    rng = np.random.default_rng(seed)
    deals = []
    for i in range(n):
        vertical = VERTICALS[rng.integers(len(VERTICALS))]
        region = REGIONS[rng.integers(len(REGIONS))]
        year = int(2016 + (i * 10) // n)

        arr = float(np.round(rng.uniform(1.5, 28.0), 2)) * 1_000_000
        grr = float(np.round(rng.normal(88.0, 6.0), 1))
        nrr = float(np.round(grr + rng.uniform(2.0, 22.0), 1))
        recurring = float(np.round(np.clip(rng.normal(85.0, 11.0), 45.0, 99.0), 1))
        top1 = float(np.round(np.clip(rng.gamma(2.2, 5.0), 2.0, 45.0), 1))
        growth = float(np.round(rng.normal(9.0, 7.0), 1))

        # The relationship a permanent-hold buyer would expect: what the business
        # retains matters more than what it was growing at, concentration is a drag,
        # and revenue that is not really recurring is the worst signal of the three.
        outcome = (0.42 * (grr - 88.0)
                   + 0.10 * (nrr - 100.0)
                   + 0.16 * (recurring - 85.0)
                   - 0.11 * max(0.0, top1 - 15.0)
                   + 0.13 * growth
                   + rng.normal(0.0, 3.1))
        outcome_cagr = float(np.round(outcome / 1.6 + 4.0, 2))

        # Underwriting is optimistic, and more optimistic on faster-growing targets -
        # the bias a calibration layer is built to surface.
        underwritten = float(np.round(outcome_cagr + rng.normal(2.6, 2.2)
                                      + 0.09 * max(0.0, growth), 2))

        deals.append({
            "deal_id": f"D{i + 1:03d}",
            "acquired": year,
            "vertical": vertical,
            "region": region,
            "arr_at_entry_usd": int(arr),
            "grr_pct": grr,
            "nrr_pct": nrr,
            "recurring_pct": recurring,
            "top1_customer_pct": top1,
            "yoy_growth_pct": growth,
            "underwritten_cagr_pct": underwritten,
            "outcome_revenue_cagr_pct": outcome_cagr,
            "outcome_window_years": OUTCOME_YEARS,
        })
    return deals
