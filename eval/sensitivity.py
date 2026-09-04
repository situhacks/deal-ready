"""Does the reasoner actually reason, or does it just write?

This is the eval that decides whether the scenario layer is worth anything, and almost
nobody runs it. **Change the evidence. See whether the conclusion moves.**

A reasoner given a strong base rate and a clean customer base should reach different
assumptions than one given a weak base rate and two failing anchor customers. If the
output is broadly the same either way, the layer is not reasoning over evidence - it is
generating plausible deal-memo prose, and plausible prose is exactly what an accountant
should not be handed.

Four evidence conditions per target, all derived from the real one by flipping a single
block:

    baseline        everything as extracted
    no_customers    customer health removed entirely
    healthy         customer distress flipped to clean
    weak_baserate   base rate replaced with a poor cohort

Similarity is Jaccard over content words. **High similarity between conditions that
should disagree is the failure.** There is no pass mark asserted here, because nobody
has established one; the number is reported and interpreted in the write-up rather than
graded against a threshold invented for the occasion.
"""

from __future__ import annotations

import json
import re
import sys
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from deal_ready.generator.profiles import ALL_PROFILES        # noqa: E402
from deal_ready.signals import baserate, customers as C, scenario  # noqa: E402

STOP = set("the a an and or of to in for is are was were be been it its this that with "
           "as at by on from not no if would could should may might will can has have "
           "had do does did but their there they them then than which who what when".split())


def words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]{3,}", text.lower()) if w not in STOP}


def jaccard(a: set[str], b: set[str]) -> float:
    return round(len(a & b) / len(a | b), 3) if (a or b) else 0.0


def weak_base_rate() -> dict:
    """A deliberately poor cohort, same shape as a real one."""
    return {"status": "ok", "matched_on": "size band + retention band",
            "n_comparables": 14,
            "outcome_cagr_pct": {"p10": -6.5, "median": -1.8, "p90": 2.1,
                                 "share_negative": 64.3},
            "underwriting_bias_pts": {"median": 6.4, "share_optimistic": 100.0},
            "deal_ids": [f"D{i:03d}" for i in range(900, 914)]}


def main() -> int:
    findings = json.loads((ROOT / "reports" / "findings.json").read_text("utf-8"))
    deals = json.loads((ROOT / "data" / "dealbook.json").read_text("utf-8"))
    by_tid = {r["target_id"]: r for r in findings}

    rows, all_sims = [], []
    for pr in ALL_PROFILES:
        tid = pr["target_id"]
        res = by_tid[tid]
        m = res.get("metrics", {})
        br = baserate.compute({"arr_usd": m.get("arr_usd"),
                               "grr_pct": m.get("grr_pct")}, deals).summary()
        sig = C.build(pr["customers"]).to_dict()

        healthy = deepcopy(pr["customers"])
        for c in healthy:
            c["distress"] = False
            c["note"] = "no signal found"

        conditions = {
            "baseline": (br, sig),
            "no_customers": (br, None),
            "healthy": (br, C.build(healthy).to_dict()),
            "weak_baserate": (weak_base_rate(), sig),
        }

        texts, statuses = {}, {}
        for name, (b, s) in conditions.items():
            assumptions, status = scenario.run(res, base_rate=b, signal=s)
            texts[name] = " ".join(f"{a.text} {a.rests_on} {a.falsified_by}"
                                   for a in assumptions)
            statuses[name] = f"{status} ({len(assumptions)})"

        base_w = words(texts["baseline"])
        sims = {n: jaccard(base_w, words(t))
                for n, t in texts.items() if n != "baseline"}
        all_sims.append(sims)
        rows.append({"target_id": tid, "code_name": pr["code_name"],
                     "statuses": statuses, "similarity_to_baseline": sims,
                     "assumptions_baseline": texts["baseline"][:1200]})
        print(f"{tid} {pr['code_name']:<11} " +
              "  ".join(f"{n}={v:.3f}" for n, v in sims.items()))

    mean = {k: round(sum(s[k] for s in all_sims) / len(all_sims), 3)
            for k in all_sims[0]}
    print("\nmean similarity to baseline: " +
          "  ".join(f"{k}={v}" for k, v in mean.items()))
    print("lower means the conclusion moved when the evidence moved")

    out = ROOT / "reports" / "sensitivity.json"
    out.write_text(json.dumps({"mean_similarity": mean, "per_target": rows},
                              indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
