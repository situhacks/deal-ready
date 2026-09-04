"""What usually happens to businesses like this one.

A CIM is a snapshot and the buyer has no future history for the target. But a serial
acquirer has something better than a forecast: **the futures of every other company it
bought.** This layer computes that.

It is not a prediction about the target. It is a prior - the distribution of outcomes
for past deals that resembled it - and the difference matters enough to be worth being
pedantic about. A forecast says "this will grow 6%". A base rate says "of the eleven
businesses we bought that looked like this, the median grew 5.4% and the worst shrank".
The second is arguable. The first invites belief.

**Everything here is auditable by construction.** A cohort is a named list of deal ids.
A reviewer can pull those deals and check the arithmetic by hand, which is the standard
this has to meet: the people reading it reconcile to the penny for a living.

**It fails loudly.** Too few comparables and it says so rather than quoting a median of
three. The failure is the useful output - "we have never bought anything like this" is
a finding.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

# Below this, a cohort median is noise wearing a number's clothes.
MIN_COHORT = 8
# Progressive relaxation: try the tightest match first, widen only as far as needed,
# and always report which rung actually produced the answer.
MATCH_RUNGS = [
    ("vertical + size band + retention band", ("vertical", "size", "retention")),
    ("size band + retention band", ("size", "retention")),
    ("retention band only", ("retention",)),
    ("size band only", ("size",)),
    ("whole book", ()),
]


def _size_band(arr: float) -> str:
    if arr < 3_000_000:
        return "under $3M"
    if arr < 10_000_000:
        return "$3-10M"
    if arr < 20_000_000:
        return "$10-20M"
    return "over $20M"


def _retention_band(grr: float) -> str:
    if grr < 85.0:
        return "under 85%"
    if grr < 92.0:
        return "85-92%"
    return "over 92%"


@dataclass
class BaseRate:
    matched_on: str
    deal_ids: list[str] = field(default_factory=list)
    outcome_cagr: list[float] = field(default_factory=list)
    underwritten_cagr: list[float] = field(default_factory=list)
    target_band: dict = field(default_factory=dict)
    status: str = "ok"

    @property
    def n(self) -> int:
        return len(self.deal_ids)

    def _pct(self, xs, q):
        return round(float(np.percentile(xs, q)), 2) if xs else None

    def summary(self) -> dict:
        o = self.outcome_cagr
        u = self.underwritten_cagr
        gaps = [a - b for a, b in zip(u, o)]
        return {
            "status": self.status,
            "matched_on": self.matched_on,
            "n_comparables": self.n,
            "target_band": self.target_band,
            "outcome_cagr_pct": {
                "p10": self._pct(o, 10), "median": self._pct(o, 50),
                "p90": self._pct(o, 90),
                "share_negative": (round(100.0 * sum(1 for x in o if x < 0) / len(o), 1)
                                   if o else None),
            },
            "underwriting_bias_pts": {
                "median": self._pct(gaps, 50),
                "share_optimistic": (round(100.0 * sum(1 for g in gaps if g > 0)
                                           / len(gaps), 1) if gaps else None),
            },
            "deal_ids": self.deal_ids,
        }

    def headline(self) -> str:
        if self.status != "ok":
            return self.status
        s = self.summary()
        o, b = s["outcome_cagr_pct"], s["underwriting_bias_pts"]
        return (f"Across {self.n} past acquisitions matched on {self.matched_on}, "
                f"revenue grew a median {o['median']}% a year over three years "
                f"(p10 {o['p10']}%, p90 {o['p90']}%); {o['share_negative']}% shrank. "
                f"Underwriting ran {b['median']} points optimistic at the median, "
                f"and was optimistic on {b['share_optimistic']}% of them.")


def compute(target: dict, dealbook: list[dict],
            min_cohort: int = MIN_COHORT) -> BaseRate:
    """Find comparable past deals and summarise what happened to them.

    `target` needs `arr_usd` and `grr_pct`; `vertical` sharpens the match when present.
    Widens the match one rung at a time until the cohort is big enough to mean
    anything, and reports which rung it stopped at - a base rate matched on "whole
    book" is a much weaker claim than one matched on vertical and size, and the memo
    has to be able to tell them apart.
    """
    arr = target.get("arr_usd")
    grr = target.get("grr_pct")
    if arr is None or grr is None:
        return BaseRate(matched_on="none", status=(
            "base rate unavailable - needs ARR and gross retention, and at least one "
            "was not recovered from the document"))

    band = {"vertical": target.get("vertical"), "size": _size_band(float(arr)),
            "retention": _retention_band(float(grr))}

    for label, keys in MATCH_RUNGS:
        if "vertical" in keys and not band["vertical"]:
            continue
        cohort = []
        for d in dealbook:
            ok = True
            for k in keys:
                if k == "vertical":
                    ok = ok and d["vertical"] == band["vertical"]
                elif k == "size":
                    ok = ok and _size_band(d["arr_at_entry_usd"]) == band["size"]
                elif k == "retention":
                    ok = ok and _retention_band(d["grr_pct"]) == band["retention"]
            if ok:
                cohort.append(d)
        if len(cohort) >= min_cohort:
            return BaseRate(
                matched_on=label,
                deal_ids=[d["deal_id"] for d in cohort],
                outcome_cagr=[d["outcome_revenue_cagr_pct"] for d in cohort],
                underwritten_cagr=[d["underwritten_cagr_pct"] for d in cohort],
                target_band=band)

    return BaseRate(matched_on="none", target_band=band, status=(
        f"base rate unavailable - fewer than {min_cohort} comparable past deals even "
        f"across the whole book. Nothing like this has been bought before, which is "
        f"itself worth saying to the committee."))
