"""The deterministic spine. No model, no network, no API key.

Everything computable is computed here, in ordinary Python, against numbers a parser
already extracted. That split is the whole trust architecture of this repo:

    The model reads. Code decides. A human signs.

Two reasons it matters more than it looks. First, **auditability**: a deal lead can
re-run these rules on the same inputs and get the same answer forever, which is not
something a model can promise. Second, **cost**: arithmetic is free, and the cheapest
token is the one never spent - the deterministic layer removes most of the work from
the model before the model is ever called.

It also sets an honest ceiling on what may be claimed. These rules are tested against
defects this repo planted itself, so quoting a "true positive rate" for them would be
circular - the answer key was written by the same hand as the exam. What gets reported
is **coverage**: did each rule catch the defect classes it claims to catch, and did it
stay silent on clean data. The second half is the one people skip. A validator that
fires on a healthy company is worse than no validator, because analysts learn to
ignore it.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

CRITERIA_DIR = Path(__file__).resolve().parents[2] / "criteria"

BLOCKER, WARNING, INFO = "blocker", "warning", "info"


@dataclass
class Finding:
    rule_id: str
    severity: str
    headline: str
    detail: str
    values: dict = field(default_factory=dict)
    citation: dict | None = None   # {page, carrier, method} from the parse layer

    def to_dict(self) -> dict:
        return asdict(self)


def load_criteria(name: str = "default") -> dict:
    return json.loads((CRITERIA_DIR / f"{name}.json").read_text(encoding="utf-8"))


def _cite(citations: dict, metric: str) -> dict | None:
    return citations.get(metric) if citations else None


def _money(v) -> str:
    if v is None:
        return "not stated"
    sign = "-" if v < 0 else ""
    a = abs(v)
    return f"{sign}${a/1_000_000:.1f}M" if a >= 1_000_000 else f"{sign}${a:,.0f}"


def evaluate(metrics: dict, criteria: dict, citations: dict | None = None) -> list[Finding]:
    """Run every rule. `metrics` may contain None - a CIM that omits a figure is a
    finding in itself, never a zero."""
    citations = citations or {}
    out: list[Finding] = []
    g = metrics.get

    # --- R1  ARR ties to MRR ---------------------------------------------------
    # The arithmetic check a buyer runs first. If annualised MRR and stated ARR
    # disagree materially, one of them includes something that is not recurring.
    arr, mrr = g("arr_usd"), g("mrr_usd")
    if arr is not None and mrr is not None:
        implied = mrr * 12
        drift = abs(implied - arr) / arr if arr else 0
        if drift > 0.05:
            out.append(Finding(
                "arr_mrr_mismatch", WARNING,
                f"Stated ARR and annualised MRR differ by {drift*100:.1f}%",
                f"MRR of {_money(mrr)} annualises to {_money(implied)}, against a stated "
                f"ARR of {_money(arr)}. A gap this size usually means non-recurring "
                f"revenue sits inside one of the two figures. Ask which.",
                {"stated_arr": arr, "implied_arr": implied, "drift_pct": round(drift*100, 2)},
                _cite(citations, "arr_usd")))

    # --- R2  ARR inside the mandate band ---------------------------------------
    band = criteria["arr_band_usd"]
    if arr is not None and not (band["min"] <= arr <= band["max"]):
        where = "below" if arr < band["min"] else "above"
        out.append(Finding(
            "arr_outside_band", BLOCKER,
            f"ARR of {_money(arr)} sits {where} the mandate band",
            f"The profile targets {_money(band['min'])} to {_money(band['max'])}. This is "
            f"a mandate fit question, not a quality judgement - the company may be "
            f"excellent and still be the wrong size for this buyer.",
            {"arr": arr, "band_min": band["min"], "band_max": band["max"]},
            _cite(citations, "arr_usd")))

    # --- R3  recurring revenue floor -------------------------------------------
    rec = g("recurring_pct")
    floor = criteria["recurring_pct_floor"]["value"]
    if rec is not None and rec < floor:
        out.append(Finding(
            "recurring_below_floor", BLOCKER,
            f"Only {rec:.0f}% of revenue is recurring, against a {floor:.0f}% floor",
            "The headline ARR is carrying services, implementation or licence revenue "
            "that will not repeat. This is the single most common way a software "
            "business looks larger than it is; the multiple should be applied to the "
            "recurring base, not the headline.",
            {"recurring_pct": rec, "floor": floor},
            _cite(citations, "recurring_pct")))

    # --- R4  gross retention floor ---------------------------------------------
    grr = g("grr_pct")
    grr_floor = criteria["grr_pct_floor"]["value"]
    if grr is not None and grr < grr_floor:
        out.append(Finding(
            "grr_below_floor", WARNING,
            f"Gross retention of {grr:.0f}% is below the {grr_floor:.0f}% floor",
            "Gross retention is the honest measure of whether customers stay, because "
            "it excludes expansion. Below the floor the base is leaking, and for a "
            "permanent-capital holder that compounds against you every year.",
            {"grr_pct": grr, "floor": grr_floor},
            _cite(citations, "grr_pct")))

    # --- R5  GRR above 100 is a definition error, not a triumph -----------------
    if grr is not None and grr > 100.0:
        out.append(Finding(
            "grr_above_100", WARNING,
            f"Gross retention reported as {grr:.0f}%, which is not possible",
            "Gross retention cannot exceed 100% by construction - it excludes expansion. "
            "A figure above 100 means net retention has been labelled gross. Worth "
            "correcting before it reaches the model, because it flatters the base.",
            {"grr_pct": grr},
            _cite(citations, "grr_pct")))

    # --- R6  net retention target ----------------------------------------------
    nrr = g("nrr_pct")
    nrr_target = criteria["nrr_pct_target"]["value"]
    if nrr is not None and nrr < nrr_target:
        out.append(Finding(
            "nrr_below_target", INFO,
            f"Net retention of {nrr:.0f}% is below {nrr_target:.0f}%",
            "Below 100% the existing base shrinks without new logos. Not disqualifying "
            "for a durable niche product, but it caps organic growth.",
            {"nrr_pct": nrr, "target": nrr_target},
            _cite(citations, "nrr_pct")))

    # --- R7  gross margin floor -------------------------------------------------
    gm = g("gross_margin_pct")
    gm_floor = criteria["gross_margin_pct_floor"]["value"]
    if gm is not None and gm < gm_floor:
        out.append(Finding(
            "gross_margin_below_floor", WARNING,
            f"Gross margin of {gm:.0f}% is below the {gm_floor:.0f}% floor",
            "Software margins below the floor usually mean a services-heavy delivery "
            "model or hosting costs carried in COGS. It changes what the business is.",
            {"gross_margin_pct": gm, "floor": gm_floor},
            _cite(citations, "gross_margin_pct")))

    # --- R8  profitability ------------------------------------------------------
    ebitda = g("ebitda_usd")
    if criteria["ebitda_positive"]["required"] and ebitda is not None and ebitda <= 0:
        out.append(Finding(
            "ebitda_negative", BLOCKER,
            f"EBITDA of {_money(ebitda)} is negative",
            "A permanent-capital buyer holds without an exit to underwrite the burn. "
            "Loss-making at this size is a mandate mismatch rather than a valuation "
            "argument.",
            {"ebitda_usd": ebitda},
            _cite(citations, "ebitda_usd")))

    # --- R9  Rule of 40 ---------------------------------------------------------
    growth = g("yoy_growth_pct")
    if ebitda is not None and arr and growth is not None:
        margin = 100.0 * ebitda / arr
        r40 = growth + margin
        if r40 < criteria["rule_of_40_floor"]["value"]:
            # INFO, not a warning, and the reason is a domain judgement worth stating.
            #
            # Rule of 40 is a growth-investor test. It asks whether a company is
            # buying growth with margin or margin with growth, which is the right
            # question when you need a step-up at exit in five years.
            #
            # A permanent-capital buyer is not underwriting an exit. It wants a
            # profitable, sticky, slow-growing business it can hold forever - which
            # fails Rule of 40 *by construction*. During development this rule fired
            # on all five targets including the clean one, which is the tell that a
            # metric has been imported from the wrong thesis. Kept because analysts
            # ask for it and it is genuine context; demoted because scoring a
            # permanent-capital target against a venture yardstick would rank the
            # portfolio backwards.
            out.append(Finding(
                "rule_of_40_below_growth_benchmark", INFO,
                f"Rule of 40 score is {r40:.0f}, below the growth-investor benchmark",
                f"Growth of {growth:.0f}% plus an EBITDA margin of {margin:.0f}% totals "
                f"{r40:.0f}. Context rather than a flag: Rule of 40 measures fitness for "
                f"a growth-and-exit thesis. A permanent-capital holder is buying "
                f"durability, and a profitable niche business with modest growth will "
                f"fail this test while being exactly the target it wants. Read it "
                f"alongside retention, not instead of it.",
                {"growth_pct": growth, "ebitda_margin_pct": round(margin, 1),
                 "rule_of_40": round(r40, 1)},
                _cite(citations, "ebitda_usd")))

    # --- R10 customer concentration ---------------------------------------------
    caps = criteria["concentration_caps"]
    t1, t5 = g("top1_customer_pct"), g("top5_customer_pct")
    if t1 is not None and t1 > caps["top1_pct_max"]:
        out.append(Finding(
            "top1_concentration_breach", WARNING,
            f"Largest customer is {t1:.0f}% of ARR, above the {caps['top1_pct_max']:.0f}% cap",
            "One departure removes that share of revenue in a single renewal cycle. "
            "This reprices a deal rather than killing it - but the price should reflect "
            "it, and the contract terms with that customer become diligence priority one.",
            {"top1_pct": t1, "cap": caps["top1_pct_max"]},
            _cite(citations, "top1_customer_pct")))
    if t5 is not None and t5 > caps["top5_pct_max"]:
        out.append(Finding(
            "top5_concentration_breach", WARNING,
            f"Top five customers are {t5:.0f}% of ARR, above the {caps['top5_pct_max']:.0f}% cap",
            "A concentrated base means revenue quality depends on a handful of "
            "relationships that a change of ownership can disturb. Check change-of-"
            "control and assignment clauses in those five contracts first.",
            {"top5_pct": t5, "cap": caps["top5_pct_max"]},
            _cite(citations, "top5_customer_pct")))

    # --- R11 missing figures are findings, not zeros -----------------------------
    required = ["arr_usd", "recurring_pct", "grr_pct", "ebitda_usd"]
    missing = [m for m in required if g(m) is None]
    if missing:
        out.append(Finding(
            "metrics_not_stated", INFO,
            f"{len(missing)} core metric(s) not stated in the document",
            "Absence is information. A CIM that omits gross retention has usually "
            "omitted it on purpose, and it becomes the first management-call question "
            "rather than an assumption: " + ", ".join(missing) + ".",
            {"missing": missing}, None))

    return out


def severity_counts(findings: list[Finding]) -> dict:
    c = {BLOCKER: 0, WARNING: 0, INFO: 0}
    for f in findings:
        c[f.severity] = c.get(f.severity, 0) + 1
    return c
