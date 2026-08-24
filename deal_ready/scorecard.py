"""Render the investment rubric and per-target scorecards as readable markdown.

The rubric lives in `criteria/default.json` because it is config - swap in a real
acquirer's scorecard without touching code. But config is for the machine; the
analyst reviewing a screen needs the same two documents in front of them as text:
what the buyer demands (`render_template`), and how one target landed against it
(`render_target`). Both are generated, never hand-written, so they cannot drift
from the JSON they describe - `run_checks.py` regenerates and byte-compares them.
"""

from __future__ import annotations

import json
from pathlib import Path


def _money(v) -> str:
    sign = "-" if v < 0 else ""
    a = abs(int(v))
    return f"{sign}${a/1_000_000:.1f}M" if a >= 1_000_000 else f"{sign}${a:,.0f}"


def _pct(v) -> str:
    return f"{v:g}%"


def _band(w: dict) -> str:
    lo, hi = w.get("min"), w.get("max")
    lo_s = _money(lo) if lo else "any"
    hi_s = _money(hi) if hi else "any"
    return f"{lo_s} - {hi_s}"


def render_template(criteria: dict) -> str:
    """The organization's rubric: what this buyer demands, and what each demand weighs."""
    tiers = criteria["tiers"]
    lines = [
        f"# Scorecard template - {criteria['profile_name']}",
        "",
        criteria["description"],
        "",
        f"**Posture.** {criteria['posture']}",
        "",
        "## The rubric",
        "",
        "| Demand | Threshold | Weight |",
        "|---|---|---|",
        f"| ARR inside the mandate band | {_band(criteria['arr_band_usd'])} "
        f"| {criteria['arr_band_usd']['weight']} |",
        f"| Recurring revenue share, floor | {_pct(criteria['recurring_pct_floor']['value'])} "
        f"| {criteria['recurring_pct_floor']['weight']} |",
        f"| Gross revenue retention, floor | {_pct(criteria['grr_pct_floor']['value'])} "
        f"| {criteria['grr_pct_floor']['weight']} |",
        f"| Net revenue retention, target | {_pct(criteria['nrr_pct_target']['value'])} "
        f"| {criteria['nrr_pct_target']['weight']} |",
        f"| Gross margin, floor | {_pct(criteria['gross_margin_pct_floor']['value'])} "
        f"| {criteria['gross_margin_pct_floor']['weight']} |",
        f"| EBITDA positive | required "
        f"| {criteria['ebitda_positive']['weight']} |",
        f"| Customer concentration caps | largest <= {_pct(criteria['concentration_caps']['top1_pct_max'])}, "
        f"top five <= {_pct(criteria['concentration_caps']['top5_pct_max'])} "
        f"| {criteria['concentration_caps']['weight']} |",
        f"| Rule of 40 | >= {_pct(criteria['rule_of_40_floor']['value'])}, context only "
        f"| {criteria['rule_of_40_floor']['weight']} |",
        "",
        f"Concentration note: {criteria['concentration_caps']['note']}",
        "",
        f"Rule of 40 note: {criteria['rule_of_40_floor']['note']}",
        "",
        "## Tier bands",
        "",
        f"- Score >= {tiers['tier_1_min_score']}: {tiers['labels']['tier_1']}",
        f"- Score >= {tiers['tier_2_min_score']}: {tiers['labels']['tier_2']}",
        f"- Below {tiers['tier_2_min_score']}: {tiers['labels']['pass']}",
        "",
        "Blocker rules - a breach on any of these caps the tier regardless of "
        f"score: {', '.join(criteria['blocker_rules'])}.",
        "",
        "*This document is generated from `criteria/default.json`. Edit the JSON, "
        "re-run, and the template follows - it is never hand-edited.*",
        "",
    ]
    return "\n".join(lines)


def render_target(result: dict, criteria: dict) -> str:
    """One target's scorecard: its numbers set against the rubric, every finding shown."""
    fit = result["fit"]
    lines = [
        f"# Scorecard - {result['code_name']} ({result['target_id']})",
        "",
        f"**Fit score {fit['score']:g}/100 - {fit['tier_label']}.** "
        f"{result['metrics_recovered']} of the rubric's metrics recovered from "
        f"{result['source']}.",
        "",
    ]
    if fit.get("blocked_by"):
        lines += [f"Blocked by: {', '.join(fit['blocked_by'])}.", ""]

    lines += [
        "## Metrics against the rubric",
        "",
        "| Metric | Value | The rubric asks | Verdict | Source |",
        "|---|---|---|---|---|",
    ]

    def cite(m):
        c = result["citations"].get(m, {})
        pg = c.get("page")
        how = c.get("method", "")
        via = f", {c.get('read')} read" if c.get("read") else ""
        return f"p{pg}, {how}{via}" if pg else how or "-"

    m = result["metrics"]

    def v(metric):
        """(display value, verdict) against the rubric, from the metric alone."""
        val = m.get(metric)
        if val is None:
            return "not stated", "-"
        if metric == "arr_usd":
            band = criteria["arr_band_usd"]
            ok = band["min"] <= val <= band["max"]
        elif metric == "ebitda_usd":
            ok = val > 0
        elif metric == "nrr_pct":
            return (f"{val:g}%",
                    "meets" if val >= criteria["nrr_pct_target"]["value"]
                    else "below target")
        elif metric in ("top1_customer_pct", "top5_customer_pct"):
            cap = (criteria["concentration_caps"]["top1_pct_max"]
                   if metric == "top1_customer_pct"
                   else criteria["concentration_caps"]["top5_pct_max"])
            # A cap breach reprices the deal; it does not auto-fail it.
            return f"{val:g}%", "meets" if val <= cap else "watch"
        elif metric == "yoy_growth_pct":
            return f"{val:g}%", "-"
        else:
            floor = criteria[f"{metric}_floor"]["value"]
            ok = val >= floor
        return f"{val:g}%" if metric.endswith("_pct") else _money(val), \
            "meets" if ok else "**breach**"

    rows = [
        ("ARR", "arr_usd", f"inside {_band(criteria['arr_band_usd'])}"),
        ("Recurring revenue share", "recurring_pct",
         f">= {_pct(criteria['recurring_pct_floor']['value'])}"),
        ("Gross revenue retention", "grr_pct",
         f">= {_pct(criteria['grr_pct_floor']['value'])}"),
        ("Net revenue retention", "nrr_pct",
         f"target {_pct(criteria['nrr_pct_target']['value'])}"),
        ("Gross margin", "gross_margin_pct",
         f">= {_pct(criteria['gross_margin_pct_floor']['value'])}"),
        ("EBITDA", "ebitda_usd", "positive"),
        ("Largest customer share", "top1_customer_pct",
         f"<= {_pct(criteria['concentration_caps']['top1_pct_max'])}"),
        ("Top-five customer share", "top5_customer_pct",
         f"<= {_pct(criteria['concentration_caps']['top5_pct_max'])}"),
        ("YoY growth", "yoy_growth_pct", "context - no weight on this profile"),
    ]
    for label, metric, asks in rows:
        value, verdict = v(metric)
        lines.append(f"| {label} | {value} | {asks} | {verdict} | {cite(metric)} |")

    lines += ["", "## Every finding", "",
              "| Severity | Finding | Detail |", "|---|---|---|"]
    for f in result["findings"]:
        c = f.get("citation") or {}
        where = f" (p{c['page']})" if c.get("page") else ""
        lines.append(f"| {f['severity']} | {f['headline']}{where} | {f['detail']} |")

    lines += [
        "",
        "---",
        "",
        f"*Generated from `reports/findings.json` against `criteria/default.json`. "
        f"The scorecard sorts an inbox; it does not recommend a transaction.*",
        "",
    ]
    return "\n".join(lines)


def write_all(results: list[dict], criteria: dict, reports_dir: Path) -> list[str]:
    """Write the template and one scorecard per target. Returns the paths written."""
    reports_dir.mkdir(parents=True, exist_ok=True)
    written = []
    template = reports_dir / "scorecard_template.md"
    template.write_text(render_template(criteria), encoding="utf-8")
    written.append(template.name)
    for result in results:
        p = reports_dir / f"scorecard_{result['target_id']}.md"
        p.write_text(render_target(result, criteria), encoding="utf-8")
        written.append(p.name)
    return written
