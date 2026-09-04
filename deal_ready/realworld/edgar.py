"""Quarterly revenue for real companies, straight from SEC filings.

The synthetic corpus can test plumbing and arithmetic. It cannot test whether a
forecast is any good, because the answer key was written by the same hand that wrote
the question. This module exists to get a real answer key.

EDGAR is the right source for that and not only because it is free. **Every number
carries the filing it came from** - accession number, form type, fiscal period, filing
date - so a forecast built on it can be audited back to a document a regulator
received. For accounting work that provenance is not a nicety; a number nobody can
trace is a number nobody can sign.

No API key. SEC asks for a descriptive User-Agent and rate limits to ~10 requests a
second; both are respected here.
"""

from __future__ import annotations

import json
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path

UA = {"User-Agent": "deal-ready research experiment (contact: repo issues)"}
ROOT = Path(__file__).resolve().parents[2]

# Revenue is reported under different tags depending on the filer and the year. Tried
# in order; the first that yields a usable quarterly series wins, and which one was
# used is recorded so the series is reproducible.
REVENUE_TAGS = [
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "RevenueFromContractWithCustomerIncludingAssessedTax",
    "Revenues",
    "SalesRevenueNet",
]


@dataclass
class Point:
    """One quarter of revenue, with the filing that reported it."""
    fy: int
    fp: str
    start: str
    end: str
    value: float
    form: str
    accession: str
    filed: str

    def to_dict(self) -> dict:
        return {"fy": self.fy, "fp": self.fp, "start": self.start, "end": self.end,
                "value": self.value, "form": self.form, "accession": self.accession,
                "filed": self.filed}


def _get(url: str) -> dict:
    time.sleep(0.15)  # stay under SEC's rate limit
    req = urllib.request.Request(url, headers=UA)
    return json.load(urllib.request.urlopen(req, timeout=45))


def quarterly_revenue(cik: int, tag: str | None = None) -> tuple[list[Point], str]:
    """Quarterly revenue points for one company, oldest first.

    Only 10-Q and 10-K facts with a roughly-one-quarter duration are kept. Annual
    figures are dropped rather than divided by four, because a fabricated quarter is
    worse than a missing one.
    """
    tags = [tag] if tag else REVENUE_TAGS
    for t in tags:
        url = (f"https://data.sec.gov/api/xbrl/companyconcept/"
               f"CIK{cik:010d}/us-gaap/{t}.json")
        try:
            data = _get(url)
        except Exception:                                        # noqa: BLE001
            continue
        rows = data.get("units", {}).get("USD", [])
        seen, pts = set(), []
        for r in rows:
            start, end = r.get("start"), r.get("end")
            if not start or not end or not r.get("accn"):
                continue
            days = (_d(end) - _d(start)).days
            if not 80 <= days <= 100:        # one quarter, not a year or a half
                continue
            key = (start, end)
            if key in seen:
                continue
            seen.add(key)
            pts.append(Point(fy=r.get("fy") or 0, fp=r.get("fp") or "",
                             start=start, end=end, value=float(r["val"]),
                             form=r.get("form", ""), accession=r["accn"],
                             filed=r.get("filed", "")))
        pts.sort(key=lambda p: p.end)
        if len(pts) >= 24:
            return pts, t
    return [], ""


def _d(s: str):
    from datetime import date
    y, m, dd = (int(x) for x in s.split("-"))
    return date(y, m, dd)


def fetch(companies: dict[str, int], out_path: Path | None = None) -> dict:
    """Pull every company and write one committed artifact.

    The artifact is the point: once written, the whole forecast experiment reruns
    offline from it, and anyone can trace a number to its filing without re-fetching.
    """
    out: dict = {"source": "SEC EDGAR XBRL companyconcept API",
                 "retrieved": time.strftime("%Y-%m-%d"), "companies": {}}
    for ticker, cik in companies.items():
        pts, tag = quarterly_revenue(cik)
        out["companies"][ticker] = {
            "cik": cik, "tag": tag, "n_quarters": len(pts),
            "points": [p.to_dict() for p in pts],
        }
        print(f"  {ticker:<6} {len(pts):>3} quarters  tag={tag or 'NONE'}")
    if out_path:
        out_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    return out
