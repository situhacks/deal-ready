# Scorecard - Kestrel (T04)

**Fit score 45/100 - Pass - criteria not met on this profile.** 6/10 of the rubric's metrics recovered from T04_Kestrel_CIM.pdf.

Blocked by: ebitda_negative.

## Metrics against the rubric

| Metric | Value | The rubric asks | Verdict | Source |
|---|---|---|---|---|
| ARR | $9.6M | inside $2.0M - $30.0M | meets | p8, textlayer |
| Recurring revenue share | 95% | >= 80% | meets | p2, textlayer |
| Gross revenue retention | not stated | >= 85% | - | - |
| Net revenue retention | not stated | target 100% | - | - |
| Gross margin | 71% | >= 65% | meets | p8, textlayer |
| EBITDA | -$2.4M | positive | **breach** | p8, textlayer |
| Largest customer share | not stated | <= 15% | - | - |
| Top-five customer share | not stated | <= 35% | - | - |
| YoY growth | 22% | context - no weight on this profile | - | p2, textlayer |

## Every finding

| Severity | Finding | Detail |
|---|---|---|
| blocker | EBITDA of -$2.4M is negative (p8) | A permanent-capital buyer holds without an exit to underwrite the burn. Loss-making at this size is a mandate mismatch rather than a valuation argument. |
| info | Rule of 40 score is -3, below the growth-investor benchmark (p8) | Growth of 22% plus an EBITDA margin of -25% totals -3. Context rather than a flag: Rule of 40 measures fitness for a growth-and-exit thesis. A permanent-capital holder is buying durability, and a profitable niche business with modest growth will fail this test while being exactly the target it wants. Read it alongside retention, not instead of it. |
| info | 1 core metric(s) not stated in the document | Absence is information. A CIM that omits gross retention has usually omitted it on purpose, and it becomes the first management-call question rather than an assumption: grr_pct. |

---

*Generated from `reports/findings.json` against `criteria/default.json`. The scorecard sorts an inbox; it does not recommend a transaction.*
