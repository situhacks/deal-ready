"""Customer-health signal: churn risk from the state of the customer base.

The screen reads a retention curve and tells you what churn *has been*. This asks a
different question, and it is the one an acquirer actually wants: are the target's
customers themselves in trouble? A retention line is a lagging indicator by
construction - it cannot contain a customer that has not left yet.

Nobody researches four hundred customers of an acquisition target by hand, because it
costs more than it returns. That is the whole reason this exists as an agent task.

Division of labour, the same one the rest of the pipeline uses:

    document   names the anchor customers and their contract values
    research   finds out how each of those customers is doing (plugin path, web)
    code       aggregates distress into a share of ARR and decides the flag
    human      reads it and forms a view

**Nothing here scores.** The output is a flagged observation for the memo, never a
criterion and never a tier movement. A customer being in trouble is a question to ask
management, not an arithmetic fact about the target.

What is testable offline is the aggregation and the flag rule. Whether research
correctly identifies distress is not testable against a synthetic corpus - those
companies do not exist - so it is not claimed here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# A single customer at or above this share, in distress, is material on its own.
SINGLE_MATERIAL_PCT = 10.0
# Aggregate distressed share at or above this is material regardless of any single one.
AGGREGATE_MATERIAL_PCT = 15.0

_MONEY = re.compile(r"\$\s?(\d+(?:[.,]\d+)?)\s*([KMB])?", re.I)
_MULT = {"k": 1_000, "m": 1_000_000, "b": 1_000_000_000}


@dataclass
class CustomerFinding:
    name: str
    pct_arr: float
    distressed: bool
    evidence: str = ""

    def to_dict(self) -> dict:
        return {"name": self.name, "pct_arr": round(self.pct_arr, 2),
                "distressed": self.distressed, "evidence": self.evidence}


@dataclass
class CustomerSignal:
    findings: list[CustomerFinding] = field(default_factory=list)
    researched: int = 0
    unresearched: int = 0

    @property
    def distressed(self) -> list[CustomerFinding]:
        return [f for f in self.findings if f.distressed]

    @property
    def distressed_pct(self) -> float:
        return round(sum(f.pct_arr for f in self.distressed), 2)

    @property
    def covered_pct(self) -> float:
        """Share of ARR the roster accounts for at all.

        Reported because it bounds every other number here. A roster covering 19% of
        ARR cannot tell you much about the other 81%, and saying so is the difference
        between a signal and a claim.
        """
        return round(sum(f.pct_arr for f in self.findings), 2)

    def severity(self) -> str:
        if not self.distressed:
            return "none"
        if (self.distressed_pct >= AGGREGATE_MATERIAL_PCT
                or any(f.pct_arr >= SINGLE_MATERIAL_PCT for f in self.distressed)):
            return "material"
        return "noted"

    def headline(self) -> str:
        n = len(self.distressed)
        if not n:
            return (f"No distress signals found across {self.researched} researched "
                    f"customers covering {self.covered_pct}% of ARR.")
        biggest = max(self.distressed, key=lambda f: f.pct_arr)
        return (f"{n} of {self.researched} researched customers show distress signals, "
                f"together {self.distressed_pct}% of ARR. Largest is {biggest.name} at "
                f"{biggest.pct_arr}%. Roster covers {self.covered_pct}% of ARR; the "
                f"remainder was not researched.")

    def to_dict(self) -> dict:
        return {
            "severity": self.severity(),
            "headline": self.headline(),
            "distressed_pct_arr": self.distressed_pct,
            "roster_covers_pct_arr": self.covered_pct,
            "researched": self.researched,
            "unresearched": self.unresearched,
            "customers": [f.to_dict() for f in self.findings],
        }


def parse_roster(page_text: str, arr_usd: int | None) -> list[tuple[str, float]]:
    """Read the anchor-customer table off a page into (name, pct_of_arr).

    The deck prints contract values in dollars, not percentages - the shares are
    chart-carried and printing them as text would leak them. So the percentage is
    derived here, which means it needs ARR and returns nothing without it rather than
    guessing a denominator.
    """
    if not arr_usd:
        return []
    lines = [ln.strip() for ln in page_text.splitlines() if ln.strip()]
    out: list[tuple[str, float]] = []

    def _usd(m) -> float:
        raw = float(m.group(1).replace(",", ""))
        return raw * _MULT.get((m.group(2) or "").lower(), 1)

    for i, line in enumerate(lines):
        m = _MONEY.search(line)
        if not m:
            continue
        # A PDF table serialises either as "Name  $2.1M" on one line or as the name
        # and the value on consecutive lines, depending on the writer. Handle both:
        # take the text before the money on this line, and fall back to the previous
        # line when there is none.
        name = line[:m.start()].strip(" \t|-–—:")
        if not name and i:
            prev = lines[i - 1]
            if not _MONEY.search(prev):
                name = prev.strip(" \t|-–—:")
        if not name or len(name) < 3:
            continue
        # Column headers and prose sentences are not customers.
        if name.lower() in {"customer", "annual contract value", "metric", "basis"}:
            continue
        if len(name.split()) > 8:
            continue
        pct = 100.0 * _usd(m) / arr_usd
        # A roster line should be a customer, not the ARR row itself or a total.
        if 0.05 <= pct <= 80.0:
            out.append((name, round(pct, 2)))
    return out


def build(roster: list[dict]) -> CustomerSignal:
    """Aggregate researched customers into a signal.

    Each entry needs `name` and `pct_arr`. `distress` may be True, False, or absent -
    absent means *not researched*, which is counted separately and never silently
    treated as healthy. That distinction is the whole point: an unresearched customer
    is an open question, not a clean bill of health.
    """
    sig = CustomerSignal()
    for c in roster:
        if "distress" not in c or c["distress"] is None:
            sig.unresearched += 1
            continue
        sig.researched += 1
        sig.findings.append(CustomerFinding(
            name=c["name"], pct_arr=float(c["pct_arr"]),
            distressed=bool(c["distress"]), evidence=c.get("note", "")))
    return sig


def callout(sig: CustomerSignal) -> dict | None:
    """The memo call-out, or None when there is nothing to ask.

    Phrased as a question with an owner, like every other call-out in this pipeline.
    """
    if sig.severity() == "none":
        return None
    names = ", ".join(f.name for f in sig.distressed)
    return {
        "kind": "customer_health",
        "severity": sig.severity(),
        "distressed_pct_arr": sig.distressed_pct,
        "question": (
            f"Research indicates distress at {names}, together {sig.distressed_pct}% "
            f"of ARR. None of this is visible in the retention history, which is a "
            f"lagging measure. Can management confirm the current status and renewal "
            f"posture of these accounts?"),
    }
