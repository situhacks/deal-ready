# Screening memo — Ashgrove (T05)

*Drafted by deal-ready · 10/10 metrics recovered · every figure cites its page · nothing here recommends a transaction.*

## Verdict against the profile

Fit score **97.7/100** against the "Buy-and-hold software" profile — Tier 1 - advance to management call.
The score sorts an inbox; the flags below are the part worth reading.

## The numbers

| metric | value | source |
|---|---|---|
| ARR | $4.3M | p8, textlayer |
| MRR | $358,333 | p8, textlayer |
| Recurring revenue share | 84% | p2, textlayer |
| Gross margin | 69% | p8, textlayer |
| EBITDA | $1.2M | p8, textlayer |
| YoY growth | 2% | p2, textlayer |
| Gross revenue retention | 81% (chart axis — confirm <!--co-T05-axis_read-001-->) | p7, vision |
| Net revenue retention | 86% (chart axis — confirm <!--co-T05-axis_read-002-->) | p7, vision |
| Largest customer share | 11% (chart label <!--co-T05-label_read-001-->) | p6, vision |
| Top-five customer share | 28% (chart label <!--co-T05-label_read-002-->) | p6, vision |

## What the rules flagged

- **WARNING** — Gross retention of 81% is below the 85% floor (p7). Gross retention is the honest measure of whether customers stay, because it excludes expansion. Below the floor the base is leaking, and for a permanent-capital holder that compounds against you every year.

<details><summary>Context notes (info-grade)</summary>

- Net retention of 86% is below 100%. Below 100% the existing base shrinks without new logos. Not disqualifying for a durable niche product, but it caps organic growth.
- Rule of 40 score is 29, below the growth-investor benchmark. Growth of 2% plus an EBITDA margin of 27% totals 29. Context rather than a flag: Rule of 40 measures fitness for a growth-and-exit thesis. A permanent-capital holder is buying durability, and a profitable niche business with modest growth will fail this test while being exactly the target it wants. Read it alongside retention, not instead of it.

</details>

## Judgement — read with suspicion

*Model observations on the narrative. Each one is a suggestion with a name attached; accept, edit or strike it. Striking is signal too.*

<!--co-T05-judgement-001-->
- The founder is the sole architect of the settlement engine and personally manages relationships with the six largest customers, creating a critical dependency where his absence would halt core operations. (p9)

<!--co-T05-judgement-002-->
- Revenue growth of 2% combined with a Rule of 40 score of 29 indicates that organic expansion is insufficient to outpace operational risks or capital requirements. (p8)

<!--co-T05-judgement-003-->
- The settlement logic relies on two decades of encoded provincial grading rules, yet the underlying Delphi application lacks automated test coverage and runs on an unsupported database version. (p10)

<!--co-T05-judgement-004-->
- Gross retention of 81% falls significantly below the 85% floor, suggesting that customer churn is not being effectively managed despite recurring revenue contracts. (p7)

<!--co-T05-judgement-005-->
- The document defines gross margin as excluding amortisation and EBITDA with specific add-backs, which obscures the true economic cost of maintaining the legacy technology stack. (p8)

## Outside the document — for consideration, not scoring

*None of this moved a metric, a rule, a fit score or a tier. It is context a reviewer weighs, and it carries its own uncertainty.*

**Customer health.** 2 of 5 researched customers show distress signals, together 18.0% of ARR. Largest is Kettleridge Grain Co-operative at 11.0%. Roster covers 28.0% of ARR; the remainder was not researched.

| Customer | Share of ARR | Status |
|---|---|---|
| Kettleridge Grain Co-operative | 11.0% | **distress** — merging with a larger co-op that runs a competing system |
| Braemar Elevators | 7.0% | **distress** — two elevators idled through the price trough |
| Dunmore Agri Services | 4.0% | no signal found — stable |
| Solway Commodity Handling | 3.49% | no signal found — stable |
| Ninebark Farms Alliance | 2.51% | no signal found — stable |

*Roster covers 28.0% of ARR. 5 researched, 0 not. An unresearched customer is an open question, not a clean bill of health.*

> **Why this is not in the retention number.** Gross retention is a lagging measure. It cannot contain a customer that has not left yet, so a distressed customer base and a healthy retention history are perfectly consistent with each other.

**Base rate — what happened to businesses like this one.**

Matched on **size band + retention band** against **16 past acquisitions**. This is not a forecast for this target; it is what comparable businesses went on to do.

| | Revenue CAGR, 3 years after acquisition |
|---|---|
| 10th percentile | -0.2% |
| **Median** | **2.1%** |
| 90th percentile | 6.35% |
| Shrank outright | 12.5% of the cohort |

**Underwriting calibration on that same cohort: the case ran 3.95 points optimistic at the median, and was optimistic on 100.0% of them.** Read the median above with that in mind.

*Cohort, for audit — every figure above recomputes from these 16 deals: D005, D011, D013, D022, D023, D026, D035, D042, D057, D058, D059, D078, D093, D102, D103, D109.*

## What would have to be true

*Not a forecast. These are the assumptions the base rate rests on for this target, each one traceable to the input that produced it and each one stated so it can be disproved. An assumption nobody can disprove is a sentiment and does not belong here.*

| # | Assumption | Rests on | Falsified by |
|---|---|---|---|
| 1 | The acquisition will achieve a revenue CAGR comparable to the median of past deals (2.1%) because gross retention is above the historical floor. | A | Evidence showing Gross Retention (GRR) drops below 85% in the next fiscal year, specifically if the current 81% figure is an anomaly rather than a trend. |
| 2 | The top customer concentration risk (28%) will not result in significant revenue volatility or churn. | A | Evidence of the largest customer, Kettleridge Grain Co-operative (11% ARR), initiating a contract termination or reducing spend by more than 50%. |
| 3 | The two distressed customers identified in the research roster represent an isolated risk and do not indicate broader systemic issues. | C | Evidence from the remaining 72% of ARR (customers not researched) showing similar distress signals, such as delayed payments or reduced usage metrics. |
| 4 | The underwriting margin applied to past acquisitions remains valid for this deal given its specific size and retention profile. | B | Evidence that the current deal's fit score (97.7) or growth rate (2.0%) deviates significantly from the 16 past deals used to establish the base rate. |
| 5 | No external market factors will negatively impact Ashgrove's ability to retain customers or grow revenue. | D | Emergence of new competitors, regulatory changes, or economic shifts that directly affect the target's industry sector. |

*Input blocks: **A** the document · **B** the base rate from past acquisitions · **C** customer health · **D** external research.*

## Ask the seller

- Gross revenue retention was interpolated from chart geometry, not printed on the page (reader measured 100% on the committed eval). Independent re-read by qwen3.8:27b agrees with the measurement within 0.1. Confirm or replace
- Net revenue retention was interpolated from chart geometry, not printed on the page (reader measured 100% on the committed eval). Independent re-read by qwen3.8:27b agrees with the measurement within 0.1. Confirm or replace

---

*3 judgement example(s) folded back from reviewer-accepted corrections shaped this pass. Corrections teach the next version; they never rewrite this one.*