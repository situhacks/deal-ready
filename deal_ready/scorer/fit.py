"""Criteria fit: a 0-100 score and a tier.

The score is a *sorting* device, not a verdict. Its job is to order a week's inbound
so an analyst opens the right CIM first, and to make the reasoning legible when they
disagree with it. Every component is shown with its weight, so a deal lead can see
which line moved the number rather than being handed a total.

Two deliberate constraints:

**Nothing here is a model call.** Weights come from `criteria/*.json`, arithmetic
happens in Python, and the same inputs produce the same score forever. A score a deal
lead cannot reproduce is a score they will stop trusting the first time it surprises
them.

**A missing metric scores zero for its component but is reported as missing.** It is
not imputed and not skipped. Silently dropping an absent figure would quietly inflate
every incomplete CIM, which is exactly the document most likely to be hiding
something.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .rules import BLOCKER, Finding


@dataclass
class Component:
    key: str
    label: str
    weight: float
    earned: float
    basis: str

    @property
    def pct(self) -> float:
        return 100.0 * self.earned / self.weight if self.weight else 0.0


@dataclass
class FitResult:
    score: float
    tier: str
    tier_label: str
    components: list[Component] = field(default_factory=list)
    blocked_by: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "score": round(self.score, 1),
            "tier": self.tier,
            "tier_label": self.tier_label,
            "blocked_by": self.blocked_by,
            "components": [
                {"key": c.key, "label": c.label, "weight": c.weight,
                 "earned": round(c.earned, 2), "pct": round(c.pct, 1), "basis": c.basis}
                for c in self.components
            ],
        }


def _band_score(value, lo, hi, weight) -> tuple[float, str]:
    if value is None:
        return 0.0, "not stated"
    if lo <= value <= hi:
        return weight, "within band"
    # Partial credit falling off the edge - a company just outside the band is not
    # equivalent to one an order of magnitude away.
    edge = lo if value < lo else hi
    ratio = min(value, edge) / max(value, edge) if max(value, edge) else 0
    return round(weight * max(0.0, ratio), 2), "outside band"


def _floor_score(value, floor, weight, cap_ratio=1.25) -> tuple[float, str]:
    if value is None:
        return 0.0, "not stated"
    if value >= floor:
        return weight, "meets floor"
    ratio = max(0.0, value / floor) if floor else 0.0
    return round(weight * ratio, 2), "below floor"


def score(metrics: dict, criteria: dict, findings: list[Finding]) -> FitResult:
    g = metrics.get
    comps: list[Component] = []

    w = criteria["arr_band_usd"]
    earned, basis = _band_score(g("arr_usd"), w["min"], w["max"], w["weight"])
    comps.append(Component("arr_band", "ARR within mandate band", w["weight"], earned, basis))

    w = criteria["recurring_pct_floor"]
    earned, basis = _floor_score(g("recurring_pct"), w["value"], w["weight"])
    comps.append(Component("recurring", "Recurring revenue share", w["weight"], earned, basis))

    w = criteria["grr_pct_floor"]
    earned, basis = _floor_score(g("grr_pct"), w["value"], w["weight"])
    comps.append(Component("grr", "Gross revenue retention", w["weight"], earned, basis))

    w = criteria["nrr_pct_target"]
    earned, basis = _floor_score(g("nrr_pct"), w["value"], w["weight"])
    comps.append(Component("nrr", "Net revenue retention", w["weight"], earned, basis))

    w = criteria["gross_margin_pct_floor"]
    earned, basis = _floor_score(g("gross_margin_pct"), w["value"], w["weight"])
    comps.append(Component("gross_margin", "Gross margin", w["weight"], earned, basis))

    w = criteria["ebitda_positive"]
    e = g("ebitda_usd")
    earned = w["weight"] if (e is not None and e > 0) else 0.0
    basis = "not stated" if e is None else ("profitable" if e > 0 else "loss-making")
    comps.append(Component("ebitda", "Profitability", w["weight"], earned, basis))

    # Customer concentration IS scored: for a buyer that holds forever, one
    # customer leaving is a permanent hole, not a bad quarter. Rule of 40 is not
    # scored at all - see criteria/default.json and rules.py R9 for why.
    caps = criteria["concentration_caps"]
    cw = caps.get("weight", 10)
    t1, t5 = g("top1_customer_pct"), g("top5_customer_pct")
    if t1 is None and t5 is None:
        earned, basis = 0.0, "not stated"
    else:
        halves = []
        for val, cap in ((t1, caps["top1_pct_max"]), (t5, caps["top5_pct_max"])):
            if val is None:
                halves.append(0.0)
            elif val <= cap:
                halves.append(1.0)
            else:
                halves.append(max(0.0, cap / val))   # falls off as the breach widens
        earned = round(cw * sum(halves) / 2.0, 2)
        basis = "within caps" if earned == cw else "above caps"
    comps.append(Component("concentration", "Customer concentration", cw, earned, basis))

    total_weight = sum(c.weight for c in comps)
    raw = 100.0 * sum(c.earned for c in comps) / total_weight if total_weight else 0.0

    # A blocker caps the tier regardless of score. A company can look strong on
    # seven components and still be the wrong size or loss-making, and the tier must
    # say so rather than letting a good average bury it.
    blockers = [f.rule_id for f in findings if f.severity == BLOCKER]
    tiers = criteria["tiers"]
    labels = tiers["labels"]
    if blockers:
        tier, label = "pass", labels["pass"]
    elif raw >= tiers["tier_1_min_score"]:
        tier, label = "tier_1", labels["tier_1"]
    elif raw >= tiers["tier_2_min_score"]:
        tier, label = "tier_2", labels["tier_2"]
    else:
        tier, label = "pass", labels["pass"]

    return FitResult(score=raw, tier=tier, tier_label=label,
                     components=comps, blocked_by=blockers)
