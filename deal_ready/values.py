"""Surface forms: how a number can legitimately appear on a page.

A parser does not emit `8400000`. It emits whatever the document printed - "$8.4M"
here. So scoring recovery means asking whether any *acceptable rendering* of the true
value is present, not whether the integer is.

This module is deliberately generous about formatting and strict about identity. It
will accept "$8.4M", "$8,400,000" and "8.4 million" for the same value, and reject
"8.5". Being generous here is the conservative choice: it makes the parsers look as
good as they possibly can, so a low score is a real finding rather than an artifact
of us not recognising the format.
"""

from __future__ import annotations

import re

PERCENT_METRICS = {
    "recurring_pct", "grr_pct", "nrr_pct", "gross_margin_pct",
    "yoy_growth_pct", "top1_customer_pct", "top5_customer_pct",
}
MONEY_METRICS = {"arr_usd", "mrr_usd", "ebitda_usd"}


def _money_forms(v: int) -> set[str]:
    sign = "-" if v < 0 else ""
    a = abs(v)
    forms = {f"{sign}${a:,}", f"{sign}${a}"}
    if a >= 1_000_000:
        m = a / 1_000_000
        forms |= {f"{sign}${m:.1f}M", f"{sign}${m:.2f}M", f"{sign}${m:g}M",
                  f"{sign}${m:.1f} million", f"{sign}${m:g} million"}
        if abs(m - round(m)) < 1e-9:
            forms.add(f"{sign}${round(m)}M")
    if 1_000 <= a < 10_000_000:
        k = a / 1_000
        forms |= {f"{sign}${k:.0f}K", f"{sign}${k:,.0f}K"}
    return forms


def _percent_forms(v: float) -> set[str]:
    forms = set()
    for s in (f"{v:.0f}", f"{v:.1f}", f"{v:g}"):
        forms |= {f"{s}%", f"{s} %", f"{s} percent"}
    return forms


def surface_forms(metric: str, value) -> set[str]:
    """Every rendering of `value` we will accept as a recovery of `metric`."""
    if metric in MONEY_METRICS:
        return _money_forms(int(value))
    if metric in PERCENT_METRICS:
        return _percent_forms(float(value))
    return {str(value)}


def _normalise(text: str) -> str:
    """Fold whitespace and unicode punctuation so matching is not defeated by layout.

    OCR and PDF text layers both scatter spaces and swap hyphens for dashes. None of
    that should count as failing to recover a number.
    """
    t = text.replace("–", "-").replace("—", "-").replace("−", "-")
    t = t.replace(" ", " ")
    t = re.sub(r"(?<=\d)\s+(?=[%KM])", "", t)   # "8.4 M" -> "8.4M"
    t = re.sub(r"\$\s+(?=\d)", "$", t)          # "$ 8.4" -> "$8.4"
    t = re.sub(r"\s+", " ", t)
    return t


def value_present(text: str, metric: str, value) -> bool:
    """Is any acceptable rendering of this value present in `text`?"""
    hay = _normalise(text)
    hay_ci = hay.lower()
    for form in surface_forms(metric, value):
        f = _normalise(form)
        if f in hay or f.lower() in hay_ci:
            return True
    return False


# Words that identify a metric on the page, used to test attribution rather than
# mere presence. A parser that emits "34%" with no idea which series it belongs to
# has not recovered the concentration figure in any useful sense.
METRIC_KEYWORDS = {
    "arr_usd": ["annual recurring revenue", "arr"],
    "mrr_usd": ["monthly recurring revenue", "mrr"],
    "recurring_pct": ["recurring"],
    "grr_pct": ["gross revenue retention", "gross retention"],
    "nrr_pct": ["net revenue retention", "net retention"],
    "gross_margin_pct": ["gross margin"],
    "ebitda_usd": ["ebitda"],
    "yoy_growth_pct": ["grew", "growth", "year over year"],
    "top1_customer_pct": ["largest customer", "top customer", "customer concentration"],
    "top5_customer_pct": ["top five", "top 5", "customers 2-5", "customer concentration"],
}


def attribution_present(text: str, metric: str) -> bool:
    """Does the text identify which metric a number belongs to?"""
    hay = _normalise(text).lower()
    return any(kw in hay for kw in METRIC_KEYWORDS.get(metric, []))
