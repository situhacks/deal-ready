# Scorecard - Ridgeline (T03)

**Fit score 52.5/100 - Pass - criteria not met on this profile.** 6/10 of the rubric's metrics recovered from T03_Ridgeline_CIM.pdf.

Blocked by: recurring_below_floor.

## Metrics against the rubric

| Metric | Value | The rubric asks | Verdict | Source |
|---|---|---|---|---|
| ARR | $11.2M | inside $2.0M - $30.0M | meets | p8, textlayer |
| Recurring revenue share | 58% | >= 80% | **breach** | p2, textlayer |
| Gross revenue retention | not stated | >= 85% | - | - |
| Net revenue retention | not stated | target 100% | - | - |
| Gross margin | 52% | >= 65% | **breach** | p8, textlayer |
| EBITDA | $1.0M | positive | meets | p8, textlayer |
| Largest customer share | not stated | <= 15% | - | - |
| Top-five customer share | not stated | <= 35% | - | - |
| YoY growth | 11% | context - no weight on this profile | - | p2, textlayer |

## Every finding

| Severity | Finding | Detail |
|---|---|---|
| blocker | Only 58% of revenue is recurring, against a 80% floor (p2) | The headline ARR is carrying services, implementation or licence revenue that will not repeat. This is the single most common way a software business looks larger than it is; the multiple should be applied to the recurring base, not the headline. |
| warning | Gross margin of 52% is below the 65% floor (p8) | Software margins below the floor usually mean a services-heavy delivery model or hosting costs carried in COGS. It changes what the business is. |
| info | Rule of 40 score is 20, below the growth-investor benchmark (p8) | Growth of 11% plus an EBITDA margin of 9% totals 20. Context rather than a flag: Rule of 40 measures fitness for a growth-and-exit thesis. A permanent-capital holder is buying durability, and a profitable niche business with modest growth will fail this test while being exactly the target it wants. Read it alongside retention, not instead of it. |
| info | 1 core metric(s) not stated in the document | Absence is information. A CIM that omits gross retention has usually omitted it on purpose, and it becomes the first management-call question rather than an assumption: grr_pct. |

---

*Generated from `reports/findings.json` against `criteria/default.json`. The scorecard sorts an inbox; it does not recommend a transaction.*
