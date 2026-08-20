"""Synthetic target profiles.

Every number a CIM will state originates here, so ground truth is a by-product of
generation rather than something labelled afterwards. That ordering is the whole
point: labels written after the fact inherit the reader's mistakes.

Each metric declares a `carrier` - the medium the renderer must place it in:

    prose  - stated in a sentence of body text
    table  - a cell in a real table with a text layer
    chart  - plotted in a rasterised chart and stated NOWHERE else

`chart` is the control. A value carried only by a chart is invisible to text
extraction and to OCR by construction, so any parser that reports it is genuinely
reading the picture. If a chart value leaks into prose the experiment is void, and
`check_no_leaks()` exists to prove it did not.
"""

from __future__ import annotations

# Money is whole dollars, integers throughout. Floats would make "ties to the
# dollar" a lie the moment we summed anything.

CLEAN_GEM = {
    "target_id": "T01",
    "code_name": "Meridian",
    "legal_name": "Meridian Practice Systems, Inc.",
    "vertical": "dental practice management software",
    "archetype": "clean_gem",
    "founded": 2009,
    "employees": 61,
    "hq": "Columbus, Ohio",
    "seeded_defects": [],
    "metrics": {
        "arr_usd": {"value": 8_400_000, "carrier": "table"},
        "mrr_usd": {"value": 700_000, "carrier": "table"},
        "recurring_pct": {"value": 91.0, "carrier": "prose"},
        "grr_pct": {"value": 94.0, "carrier": "chart"},
        "nrr_pct": {"value": 108.0, "carrier": "chart"},
        "gross_margin_pct": {"value": 78.0, "carrier": "table"},
        "ebitda_usd": {"value": 1_850_000, "carrier": "table"},
        "yoy_growth_pct": {"value": 14.0, "carrier": "prose"},
        "top1_customer_pct": {"value": 6.0, "carrier": "chart"},
        "top5_customer_pct": {"value": 19.0, "carrier": "chart"},
    },
    "narrative": {
        "positioning": (
            "Meridian is the system of record for mid-market dental groups, running "
            "scheduling, clinical charting, claims submission and patient billing in a "
            "single workflow. Practices sign multi-year agreements and renew on "
            "auto-renewal terms."
        ),
        "moat": (
            "Switching costs are high: a practice migrating away must move eleven years "
            "of clinical records and re-credential every payer connection."
        ),
        "management": (
            "The founder stepped back to a board seat in 2021. A professional CEO has run "
            "the company since, supported by a CTO and VP Revenue who each joined before "
            "2018."
        ),
        "tech": (
            "The platform was re-architected onto a managed cloud stack between 2019 and "
            "2022. Deployment is continuous and the on-premise footprint was retired."
        ),
    },
}

CONCENTRATION_RISK = {
    "target_id": "T02",
    "code_name": "Halyard",
    "legal_name": "Halyard Logistics Software Ltd.",
    "vertical": "port and terminal operations software",
    "archetype": "concentration_risk",
    "founded": 2011,
    "employees": 44,
    "hq": "Halifax, Nova Scotia",
    "seeded_defects": ["top1_concentration_breach", "top5_concentration_breach"],
    "metrics": {
        "arr_usd": {"value": 6_100_000, "carrier": "table"},
        "mrr_usd": {"value": 508_333, "carrier": "table"},
        "recurring_pct": {"value": 88.0, "carrier": "prose"},
        "grr_pct": {"value": 96.0, "carrier": "chart"},
        "nrr_pct": {"value": 103.0, "carrier": "chart"},
        "gross_margin_pct": {"value": 74.0, "carrier": "table"},
        "ebitda_usd": {"value": 1_220_000, "carrier": "table"},
        "yoy_growth_pct": {"value": 9.0, "carrier": "prose"},
        # The defect: one customer is 34% of ARR, top five are 71%.
        "top1_customer_pct": {"value": 34.0, "carrier": "chart"},
        "top5_customer_pct": {"value": 71.0, "carrier": "chart"},
    },
    "narrative": {
        "positioning": (
            "Halyard schedules berth allocation, yard moves and gate throughput for "
            "container terminals. The product is embedded in daily terminal operations "
            "and integrated with customs filing."
        ),
        "moat": (
            "Terminal operators run Halyard as the operational spine; an outage stops "
            "gate traffic, which makes displacement risk low once installed."
        ),
        "management": (
            "The two co-founders remain in post as CEO and CTO and hold day-to-day "
            "commercial relationships with the largest accounts."
        ),
        "tech": (
            "A .NET monolith with a React front end added in 2020. Infrastructure runs in "
            "a single region with a warm standby."
        ),
    },
}

FAKE_SAAS = {
    "target_id": "T03",
    "code_name": "Ridgeline",
    "legal_name": "Ridgeline Municipal Solutions LLC",
    "vertical": "municipal permitting and licensing software",
    "archetype": "fake_saas_low_recurring",
    "founded": 2006,
    "employees": 88,
    "hq": "Boise, Idaho",
    "seeded_defects": ["recurring_below_floor", "services_revenue_in_arr"],
    "metrics": {
        # Headline ARR is inflated by implementation and training revenue.
        "arr_usd": {"value": 11_200_000, "carrier": "table"},
        "mrr_usd": {"value": 933_333, "carrier": "table"},
        # The defect: only 58% of that is genuinely recurring.
        "recurring_pct": {"value": 58.0, "carrier": "prose"},
        "grr_pct": {"value": 89.0, "carrier": "chart"},
        "nrr_pct": {"value": 97.0, "carrier": "chart"},
        "gross_margin_pct": {"value": 52.0, "carrier": "table"},
        "ebitda_usd": {"value": 1_010_000, "carrier": "table"},
        "yoy_growth_pct": {"value": 11.0, "carrier": "prose"},
        "top1_customer_pct": {"value": 12.0, "carrier": "chart"},
        "top5_customer_pct": {"value": 31.0, "carrier": "chart"},
    },
    "narrative": {
        "positioning": (
            "Ridgeline supplies permitting, inspections and business-licence workflow to "
            "small and mid-sized municipalities. Contracts are typically five years and "
            "include a substantial configuration phase."
        ),
        "moat": (
            "Public-sector procurement cycles are long and incumbents are rarely "
            "displaced mid-term."
        ),
        "management": (
            "A long-tenured leadership team, most of whom joined before 2014. Delivery is "
            "led by a services organisation of 39 people."
        ),
        "tech": (
            "Each municipality runs a configured instance. Configuration is performed by "
            "the services team rather than by the customer."
        ),
    },
}

UNPROFITABLE_GROWTH = {
    "target_id": "T04",
    "code_name": "Kestrel",
    "legal_name": "Kestrel Fleet Intelligence Inc.",
    "vertical": "commercial fleet maintenance software",
    "archetype": "unprofitable_high_growth",
    "founded": 2018,
    "employees": 73,
    "hq": "Austin, Texas",
    "seeded_defects": ["ebitda_negative", "rule_of_40_fail"],
    "metrics": {
        "arr_usd": {"value": 9_600_000, "carrier": "table"},
        "mrr_usd": {"value": 800_000, "carrier": "table"},
        "recurring_pct": {"value": 95.0, "carrier": "prose"},
        "grr_pct": {"value": 87.0, "carrier": "chart"},
        "nrr_pct": {"value": 112.0, "carrier": "chart"},
        "gross_margin_pct": {"value": 71.0, "carrier": "table"},
        # The defect: burning money, and growth does not cover it.
        "ebitda_usd": {"value": -2_400_000, "carrier": "table"},
        "yoy_growth_pct": {"value": 22.0, "carrier": "prose"},
        "top1_customer_pct": {"value": 9.0, "carrier": "chart"},
        "top5_customer_pct": {"value": 26.0, "carrier": "chart"},
    },
    "narrative": {
        "positioning": (
            "Kestrel predicts maintenance events for commercial truck fleets using "
            "telematics feeds, and schedules service before a vehicle fails in transit."
        ),
        "moat": (
            "Model quality improves with fleet-miles observed, and the data asset is "
            "difficult for a new entrant to assemble."
        ),
        "management": (
            "A venture-backed team hired for growth. The CRO and VP Engineering both "
            "joined within the last eighteen months."
        ),
        "tech": (
            "Event-driven services on a managed cloud platform. Engineering headcount is "
            "41 of 73 employees."
        ),
    },
}

LEGACY_KEY_PERSON = {
    "target_id": "T05",
    "code_name": "Ashgrove",
    "legal_name": "Ashgrove Grain Systems Corp.",
    "vertical": "agricultural grain elevator management software",
    "archetype": "legacy_tech_key_person",
    "founded": 1997,
    "employees": 29,
    "hq": "Regina, Saskatchewan",
    "seeded_defects": ["key_person_dependency", "legacy_stack_rewrite_risk", "grr_below_floor"],
    "metrics": {
        "arr_usd": {"value": 4_300_000, "carrier": "table"},
        "mrr_usd": {"value": 358_333, "carrier": "table"},
        "recurring_pct": {"value": 84.0, "carrier": "prose"},
        # The defect: gross retention below the floor.
        "grr_pct": {"value": 81.0, "carrier": "chart"},
        "nrr_pct": {"value": 86.0, "carrier": "chart"},
        "gross_margin_pct": {"value": 69.0, "carrier": "table"},
        "ebitda_usd": {"value": 1_160_000, "carrier": "table"},
        "yoy_growth_pct": {"value": 2.0, "carrier": "prose"},
        "top1_customer_pct": {"value": 11.0, "carrier": "chart"},
        "top5_customer_pct": {"value": 28.0, "carrier": "chart"},
    },
    "narrative": {
        "positioning": (
            "Ashgrove handles grain intake, grading, storage allocation and settlement for "
            "country elevators across the prairie provinces."
        ),
        "moat": (
            "Settlement logic encodes two decades of provincial grading rules that "
            "customers rely on being correct at harvest."
        ),
        # Deliberately explicit: the founder is load-bearing.
        "management": (
            "The founder remains CEO and is the only person who has worked on the "
            "settlement engine. He writes production code, approves every release, and "
            "holds the relationships with the six largest elevators personally. There is "
            "no CTO and no documented succession plan."
        ),
        "tech": (
            "The core is a Delphi application first shipped in 1998, with a web layer "
            "bolted on in 2013. The settlement engine has no automated test coverage and "
            "runs on an unsupported database version."
        ),
    },
}

ALL_PROFILES = [
    CLEAN_GEM,
    CONCENTRATION_RISK,
    FAKE_SAAS,
    UNPROFITABLE_GROWTH,
    LEGACY_KEY_PERSON,
]

# Human-readable labels, used in tables, charts and the readiness report alike so a
# reader can trace one metric through every artifact.
METRIC_LABELS = {
    "arr_usd": "Annual Recurring Revenue",
    "mrr_usd": "Monthly Recurring Revenue",
    "recurring_pct": "Recurring revenue (% of total)",
    "grr_pct": "Gross Revenue Retention",
    "nrr_pct": "Net Revenue Retention",
    "gross_margin_pct": "Gross margin",
    "ebitda_usd": "EBITDA",
    "yoy_growth_pct": "Year-over-year growth",
    "top1_customer_pct": "Largest customer (% of ARR)",
    "top5_customer_pct": "Top five customers (% of ARR)",
}


def carriers_for(profile: dict) -> dict[str, str]:
    """Map metric key -> carrier medium for one profile."""
    return {k: v["carrier"] for k, v in profile["metrics"].items()}


def values_for(profile: dict) -> dict[str, float]:
    """Map metric key -> the true value for one profile."""
    return {k: v["value"] for k, v in profile["metrics"].items()}


def chart_only_metrics(profile: dict) -> list[str]:
    """Metrics that must appear in no text anywhere in the document."""
    return [k for k, v in profile["metrics"].items() if v["carrier"] == "chart"]
