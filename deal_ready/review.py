"""Reviewer mode: check a human's asserted values against the document.

The screening path answers "what does this document say?". This path answers a
different question - "is what you wrote supported by it?" - and the difference
matters more than it looks.

When a machine drafts and a human checks, the human stops doing the thinking; the
measured version of that is well documented, and the person ends up verifying output
rather than forming judgement. When the human writes and the machine checks, the
human keeps the reps and gets a second pair of eyes. This module is the second
shape.

Three buckets, always three:

    disagreed        the document supports a different number, and here is the page
    agreed           checked and matched - the record of what was actually verified
    could_not_check  named, with a reason, never silently dropped

That third bucket is the whole safety property. A checker that only speaks when it
finds something teaches its user that silence means correct, and the failure is
invisible because there is no output to inspect. So a run where everything matched
still reports coverage: "I checked 7 of your 11 values" is the finding. "Looks good"
is not an output this module can produce.

What it deliberately does not do: rescore, rank findings by importance, or write a
corrected value into anyone's sheet. A disagreement is reported, not applied.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .embed import router
from .parse import reading, textlayer
from .values import (MONEY_METRICS, PERCENT_METRICS, METRIC_KEYWORDS,
                     _normalise, attribution_present, value_present)

# How much text around a metric keyword counts as "near it". Wide enough to cross a
# line break in a PDF text layer, narrow enough that the next bullet's number does
# not get attributed to this metric.
WINDOW = 140

_PCT = re.compile(r"(\d+(?:\.\d+)?)\s*%")
_MONEY = re.compile(r"\$\s?(\d+(?:,\d{3})*(?:\.\d+)?)\s*([KMB])?", re.I)
_MULT = {"k": 1_000, "m": 1_000_000, "b": 1_000_000_000}


@dataclass
class Check:
    """One asserted value, checked."""
    metric: str
    asserted: object
    verdict: str                      # agreed | disagreed | could_not_check
    page: int | None = None
    method: str | None = None         # textlayer | vision
    read: str | None = None           # label | axis (vision only)
    document_says: list = field(default_factory=list)
    reason: str = ""

    def to_dict(self) -> dict:
        d = {"metric": self.metric, "asserted": self.asserted, "verdict": self.verdict}
        if self.page is not None:
            d["page"] = self.page
        if self.method:
            d["method"] = self.method
        if self.read:
            d["read"] = self.read
        if self.document_says:
            d["document_says"] = self.document_says
        if self.reason:
            d["reason"] = self.reason
        return d


def _candidates_near(text: str, metric: str, limit: int = 3) -> list:
    """Numbers of the right shape sitting near a keyword that names this metric.

    Ordered by distance from the keyword and capped, because some keywords are
    generic - "growth" and "grew" sit near plenty of numbers that are not the growth
    rate - and an unordered list of everything in the window reads as noise rather
    than as evidence.

    It still returns several rather than picking one. Picking would be a judgement
    about which number the writer meant, and this module does not make judgements
    about the writer's intent; it shows them what is actually there, nearest first.
    """
    hay = _normalise(text)
    low = hay.lower()
    hits: list[tuple[int, object]] = []
    for kw in METRIC_KEYWORDS.get(metric, []):
        for m in re.finditer(re.escape(kw), low):
            lo = max(0, m.start() - WINDOW)
            hi = min(len(hay), m.end() + WINDOW)
            window = hay[lo:hi]
            anchor = m.start() - lo
            pattern = _PCT if metric in PERCENT_METRICS else (
                _MONEY if metric in MONEY_METRICS else None)
            if pattern is None:
                continue
            for g in pattern.finditer(window):
                if metric in PERCENT_METRICS:
                    v: object = float(g.group(1))
                else:
                    raw = float(g.group(1).replace(",", ""))
                    v = int(raw * _MULT.get((g.group(2) or "").lower(), 1))
                hits.append((abs(g.start() - anchor), v))

    hits.sort(key=lambda h: h[0])
    out: list = []
    for _, v in hits:
        if v not in out:
            out.append(v)
        if len(out) >= limit:
            break
    return out


def _scan(pages: dict[int, str], metric: str, asserted, method: str,
          meta: dict | None = None) -> Check | None:
    """Look for the asserted value, then for what the document says instead.

    Returns None when the metric is not attributed anywhere in these pages, which is
    the caller's signal to try another backend before giving up on it.
    """
    attributed: list[int] = []
    for pg, text in pages.items():
        if not attribution_present(text, metric):
            continue
        attributed.append(pg)
        if value_present(text, metric, asserted):
            read = None
            if meta:
                read = ("axis" if meta.get(pg, {}).get("chart_kind") == "unlabelled"
                        else "label")
            return Check(metric, asserted, "agreed", page=pg, method=method, read=read)

    if not attributed:
        return None

    for pg in attributed:
        cands = _candidates_near(pages[pg], metric)
        if cands:
            read = None
            if meta:
                read = ("axis" if meta.get(pg, {}).get("chart_kind") == "unlabelled"
                        else "label")
            return Check(metric, asserted, "disagreed", page=pg, method=method,
                         read=read, document_says=cands)

    return Check(metric, asserted, "could_not_check", page=attributed[0], method=method,
                 reason="the metric is named on this page but no value of the right "
                        "shape sits near it")


def check_one(pdf: Path, asserted: dict, use_vision: bool = True,
              top_k: int = 1, verbose: bool = True) -> dict:
    """Check one document against one asserted value set."""
    doc = textlayer.parse(pdf)
    page_text = {p.page_number: p.text for p in doc.pages}

    checks: dict[str, Check] = {}
    # A text-layer "could not check" is not an answer yet. The metric being *named* in
    # prose while its value lives in a chart is the ordinary case in a CIM deck, and
    # treating that as resolved would skip the reader that exists for exactly it. Hold
    # those as fallbacks and try the vision path first.
    fallback: dict[str, Check] = {}
    for metric, value in asserted.items():
        res = _scan(page_text, metric, value, "textlayer")
        if res is None:
            continue
        if res.verdict == "could_not_check":
            fallback[metric] = res
        else:
            checks[metric] = res

    unresolved = [m for m in asserted if m not in checks]
    routed_pages: list[int] = []

    if use_vision and unresolved:
        routes = router.route(page_text, metrics=unresolved)
        if routes:
            routed_pages = router.pages_to_read(routes, top_k)
            vdoc = reading.parse(pdf, pages=routed_pages)
            vtext = {p.page_number: p.text for p in vdoc.pages}
            vmeta = {p.page_number: p.meta for p in vdoc.pages}
            for metric in unresolved:
                res = _scan(vtext, metric, asserted[metric], "vision", meta=vmeta)
                if res is not None and res.verdict != "could_not_check":
                    checks[metric] = res
                elif res is not None and metric not in fallback:
                    fallback[metric] = res

    for metric in asserted:
        if metric in checks:
            continue
        checks[metric] = fallback.get(metric) or Check(
            metric, asserted[metric], "could_not_check",
            reason="not found in the document - a management-call question, "
                   "not an estimate")

    buckets = {"disagreed": [], "agreed": [], "could_not_check": []}
    for m in asserted:
        buckets[checks[m].verdict].append(checks[m].to_dict())

    out = {
        "source": pdf.name,
        "asserted_count": len(asserted),
        "checked_count": len(buckets["disagreed"]) + len(buckets["agreed"]),
        "coverage_pct": round(
            100.0 * (len(buckets["disagreed"]) + len(buckets["agreed"])) / len(asserted), 1
        ) if asserted else 0.0,
        "pages_read_with_vision": routed_pages,
        **buckets,
    }
    if verbose:
        render(out)
    return out


def render(result: dict) -> None:
    """The three buckets, counts first.

    Counts lead because a reader who stops after four lines should still know how
    much of their sheet was actually verified.
    """
    print(f"\n=== {result['source']} ===")
    print(f"CHECKED: {result['checked_count']} of {result['asserted_count']} "
          f"asserted values ({result['coverage_pct']}% coverage)")
    print(f"  DISAGREED     {len(result['disagreed'])}")
    print(f"  AGREED        {len(result['agreed'])}")
    print(f"  COULD NOT     {len(result['could_not_check'])}")

    if result["disagreed"]:
        print("\n--- DISAGREED ---")
        for c in result["disagreed"]:
            says = ", ".join(str(v) for v in c["document_says"])
            where = f"p{c.get('page')}  {c.get('method')}"
            if c.get("read"):
                where += f"/{c['read']}"
            print(f"{c['metric']:<20} asserted {c['asserted']}   "
                  f"document {says}   {where}")
            if c.get("read") == "axis":
                print("  " + " " * 18 + "Measured off chart geometry, not a printed "
                      "label. Confirm against source data.")

    if result["could_not_check"]:
        print("\n--- COULD NOT CHECK ---")
        for c in result["could_not_check"]:
            print(f"{c['metric']:<20} {c['reason']}")

    if result["agreed"]:
        print("\n--- AGREED ---")
        for c in result["agreed"]:
            where = f"p{c.get('page')}  {c.get('method')}"
            if c.get("read"):
                where += f"/{c['read']}"
            print(f"{c['metric']:<20} {c['asserted']}   {where}")
    print()
