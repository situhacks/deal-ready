"""Does the persona red-team add anything the rules do not already have?

The claim being tested is narrow and falsifiable: **a persona swarm earns its place only
if it raises real risks the deterministic rules cannot see.** Anything it raises that a
rule already caught is redundant, and anything it raises that is not real is noise.

Scoring uses what the corpus already knows. Each profile declares `seeded_defects`, the
rules fire on those, and the customer roster carries distress verdicts. So every
challenge lands in one of three buckets:

    redundant   the rules already flagged this - no new information
    novel-real  maps to a real risk in the profile that no rule can express
    noise       maps to nothing

Judged by keyword mapping rather than by a model, because a model grading a model on a
corpus it cannot verify is how you get a number that means nothing.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from deal_ready.generator.profiles import ALL_PROFILES          # noqa: E402
from deal_ready.parse import textlayer                           # noqa: E402
from deal_ready.signals import customers as C, redteam as R      # noqa: E402

# What the deterministic rules already say. A challenge hitting one of these is
# redundant: true, but the memo had it before the personas spoke.
RULE_TERMS = {
    "concentration": ["concentration", "largest customer", "top five", "top 5",
                      "single customer", "one customer"],
    "recurring": ["recurring", "one-time", "one time", "services revenue"],
    "ebitda": ["ebitda", "loss-making", "unprofitable", "negative earnings"],
    "retention": ["retention", "grr", "nrr", "churn rate"],
    "margin": ["gross margin", "margin"],
    "arr_band": ["arr", "annual recurring revenue", "size of the business"],
}

# Real risks the corpus encodes that NO rule can express. These are the only things a
# red-team can add, so they are what it is scored on.
NOVEL_TERMS = {
    "founder_dependency": ["founder", "key person", "succession", "single point",
                           "bus factor", "one person", "departs", "leaves"],
    "legacy_tech": ["legacy", "delphi", "rewrite", "modernis", "moderniz",
                    "technical debt", "unsupported", "test coverage", "1998"],
    # "ai" must match as a word, never as a substring - it hides inside "retain",
    # "remaining" and "available", which silently inflated this bucket on the first
    # run and with it the headline novel rate.
    "ai_displacement": [r"ai", "commodit", "displace", r"llm", "automat"],
    "customer_health": ["going out of business", "insolven", "creditor",
                        "customer's own", "distress", "acquired by a competitor",
                        "consolidat", "bankrupt"],
    "definition_quality": ["definition", "basis", "adjusted", "add-back", "add back",
                           "excludes", "flatter"],
}

# Which novel risks are genuinely present per archetype. Anything else is noise.
PRESENT = {
    "clean_gem": {"definition_quality", "ai_displacement"},
    "concentration_risk": {"customer_health", "definition_quality", "ai_displacement"},
    "fake_saas_low_recurring": {"definition_quality", "customer_health",
                                "ai_displacement"},
    "unprofitable_high_growth": {"definition_quality", "customer_health",
                                 "ai_displacement"},
    "legacy_tech_key_person": {"founder_dependency", "legacy_tech", "customer_health",
                               "definition_quality", "ai_displacement"},
}


def _hit(term: str, text: str) -> bool:
    """Plain substring, unless the term is written as a regex word boundary."""
    return bool(re.search(term, text)) if term.startswith(r"") else term in text


def classify(text: str, archetype: str) -> tuple[str, str]:
    low = text.lower()
    for tag, terms in NOVEL_TERMS.items():
        if any(_hit(t, low) for t in terms):
            return ("novel-real", tag) if tag in PRESENT[archetype] else ("noise", tag)
    for tag, terms in RULE_TERMS.items():
        if any(_hit(t, low) for t in terms):
            return "redundant", tag
    return "noise", "unmapped"


def main() -> int:
    findings = json.loads((ROOT / "reports" / "findings.json").read_text("utf-8"))
    by_tid = {r["target_id"]: r for r in findings}
    rows, totals = [], {"redundant": 0, "novel-real": 0, "noise": 0}

    for pr in ALL_PROFILES:
        tid = pr["target_id"]
        pdf = next((ROOT / "data").glob(f"{tid}_*.pdf"))
        doc = textlayer.parse(pdf)
        pages = {p.page_number: p.text for p in doc.pages}
        sig = C.build(pr["customers"]).to_dict()
        challenges, status = R.run(by_tid[tid], sig, doc.text)
        counts = {"redundant": 0, "novel-real": 0, "noise": 0}
        tags = []
        for ch in challenges:
            bucket, tag = classify(f"{ch.concern} {ch.question}", pr["archetype"])
            counts[bucket] += 1
            totals[bucket] += 1
            tags.append((bucket, tag, ch.persona, ch.question))
        rows.append({"target_id": tid, "code_name": pr["code_name"],
                     "archetype": pr["archetype"], "status": status,
                     "n": len(challenges), "counts": counts,
                     "challenges": [{"bucket": b, "tag": t, "persona": p,
                                     "question": q} for b, t, p, q in tags]})
        print(f"{tid} {pr['code_name']:<11} {len(challenges):>2} challenges  "
              f"redundant {counts['redundant']}  novel {counts['novel-real']}  "
              f"noise {counts['noise']}   ({status})")

    n = sum(totals.values())
    print(f"\nTOTAL {n} challenges: redundant {totals['redundant']}, "
          f"novel-real {totals['novel-real']}, noise {totals['noise']}")
    if n:
        print(f"novel rate {100*totals['novel-real']/n:.0f}%, "
              f"noise rate {100*totals['noise']/n:.0f}%")
    out = ROOT / "reports" / "redteam_eval.json"
    out.write_text(json.dumps({"totals": totals, "per_target": rows}, indent=2) + "\n",
                   encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
