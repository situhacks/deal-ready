# Screening memo — Halyard (T02)

*Drafted by deal-ready · 10/10 metrics recovered · every figure cites its page · nothing here recommends a transaction.*

## Verdict against the profile

Fit score **94.7/100** against the "Buy-and-hold software" profile — Tier 1 - advance to management call.
The score sorts an inbox; the flags below are the part worth reading.

## The numbers

| metric | value | source |
|---|---|---|
| ARR | $6.1M | p8, textlayer |
| MRR | $508,333 | p8, textlayer |
| Recurring revenue share | 88% | p2, textlayer |
| Gross margin | 74% | p8, textlayer |
| EBITDA | $1.2M | p8, textlayer |
| YoY growth | 9% | p2, textlayer |
| Gross revenue retention | 96% (chart axis — confirm <!--co-T02-axis_read-001-->) | p7, vision |
| Net revenue retention | 103% (chart axis — confirm <!--co-T02-axis_read-002-->) | p7, vision |
| Largest customer share | 34% (chart label <!--co-T02-label_read-001-->) | p6, vision |
| Top-five customer share | 71% (chart label <!--co-T02-label_read-002-->) | p6, vision |

## What the rules flagged

- **WARNING** — Largest customer is 34% of ARR, above the 15% cap (p6). One departure removes that share of revenue in a single renewal cycle. This reprices a deal rather than killing it - but the price should reflect it, and the contract terms with that customer become diligence priority one.
- **WARNING** — Top five customers are 71% of ARR, above the 35% cap (p6). A concentrated base means revenue quality depends on a handful of relationships that a change of ownership can disturb. Check change-of-control and assignment clauses in those five contracts first.

<details><summary>Context notes (info-grade)</summary>

- Rule of 40 score is 29, below the growth-investor benchmark. Growth of 9% plus an EBITDA margin of 20% totals 29. Context rather than a flag: Rule of 40 measures fitness for a growth-and-exit thesis. A permanent-capital holder is buying durability, and a profitable niche business with modest growth will fail this test while being exactly the target it wants. Read it alongside retention, not instead of it.

</details>

## Judgement — read with suspicion

*Model observations on the narrative. Each one is a suggestion with a name attached; accept, edit or strike it. Striking is signal too.*

<!--co-T02-judgement-001-->
- The two co-founders hold day-to-day commercial relationships with the largest accounts while no CTO exists to oversee technical strategy or succession planning. (p9)

<!--co-T02-judgement-002-->
- Revenue growth of 9% combined with a Rule of 40 score of 29 indicates that organic expansion is insufficient to offset the risks posed by high customer concentration. (p8)

<!--co-T02-judgement-003-->
- The largest customer represents 34% of ARR, creating significant displacement risk if their operational needs change or they seek a cheaper alternative. (p13)

<!--co-T02-judgement-004-->
- Top five customers account for 71% of total revenue, meaning the company's financial stability is heavily dependent on retaining just a handful of clients. (p13)

<!--co-T02-judgement-005-->
- The product relies on a .NET monolith architecture with no documented test coverage or succession plan, creating generational technical risk rather than incremental one. (p10)

## Outside the document — for consideration, not scoring

*None of this moved a metric, a rule, a fit score or a tier. It is context a reviewer weighs, and it carries its own uncertainty.*

**Customer health.** 2 of 5 researched customers show distress signals, together 49.43% of ARR. Largest is Tidewater Logistics Group at 34.43%. Roster covers 71.43% of ARR; the remainder was not researched.

| Customer | Share of ARR | Status |
|---|---|---|
| Tidewater Logistics Group | 34.43% | **distress** — filed for creditor protection Q3 FY25; two depots closed |
| Ferrand Freight Systems | 15.0% | **distress** — acquired by a competitor running a rival platform |
| Ostrand Haulage | 9.0% | no signal found — stable |
| Calder Transport Co-op | 7.0% | no signal found — stable |
| Merrow Distribution | 6.0% | no signal found — stable |

*Roster covers 71.43% of ARR. 5 researched, 0 not. An unresearched customer is an open question, not a clean bill of health.*

> **Why this is not in the retention number.** Gross retention is a lagging measure. It cannot contain a customer that has not left yet, so a distressed customer base and a healthy retention history are perfectly consistent with each other.

**Base rate — what happened to businesses like this one.**

Matched on **retention band only** against **29 past acquisitions**. This is not a forecast for this target; it is what comparable businesses went on to do.

| | Revenue CAGR, 3 years after acquisition |
|---|---|
| 10th percentile | 3.88% |
| **Median** | **6.3%** |
| 90th percentile | 10.45% |
| Shrank outright | 0.0% of the cohort |

**Underwriting calibration on that same cohort: the case ran 3.8 points optimistic at the median, and was optimistic on 100.0% of them.** Read the median above with that in mind.

*Cohort, for audit — every figure above recomputes from these 29 deals: D001, D002, D004, D006, D008, D017, D019, D020, D024, D030, D032, D036, D041, D045, D047, D048, D052, D062, D066, D082, D084, D089, D092, D096, D110, D112, D115, D119, D120.*

## What would have to be true

*Not a forecast. These are the assumptions the base rate rests on for this target, each one traceable to the input that produced it and each one stated so it can be disproved. An assumption nobody can disprove is a sentiment and does not belong here.*

| # | Assumption | Rests on | Falsified by |
|---|---|---|---|
| 1 | The acquisition will achieve a revenue CAGR comparable to the median of past deals (6.3%) because Halyard's retention metrics are strong. | B, specifically the 'matched on retention band only across 29 past deals' and the resulting underwriting logic. | Evidence showing that Halyard's specific distress signals (49.43% of ARR) correlate with a failure to meet the median CAGR in similar historical cases. |
| 2 | The top customer concentration risk is manageable because it falls within the documented cap rules for Tier 1 fit. | A, specifically the 'Largest customer is 34% of ARR' and 'Top five customers are 71% of ARR' data points against the stated caps. | Evidence from C showing that Tidewater Logistics Group (34.43%) is experiencing distress signals that could trigger churn, violating the implicit assumption of stability. |
| 3 | The absence of external research indicates a lack of hidden risks rather than a gap in known data. | D, specifically 'none available'. | Evidence emerging from C regarding the distress signals at Tidewater Logistics Group that were not captured by external sources. |
| 4 | The high gross margin and recurring revenue percentages will sustain growth without degradation. | A, specifically 'gross_margin_pct: 74.0', 'recurring_pct: 88.0', and 'nrr_pct: 103.0'. | Evidence from C indicating that the distress signals affecting nearly half of ARR could lead to margin compression or churn, negating the benefit of high NRR. |

*Input blocks: **A** the document · **B** the base rate from past acquisitions · **C** customer health · **D** external research.*

## Ask the seller

- Gross revenue retention was interpolated from chart geometry, not printed on the page (reader measured 100% on the committed eval). Independent re-read by qwen3.8:27b agrees with the measurement within 0.2. Confirm or replace
- Net revenue retention was interpolated from chart geometry, not printed on the page (reader measured 100% on the committed eval). Independent re-read by qwen3.8:27b agrees with the measurement within 0.2. Confirm or replace

---

*3 judgement example(s) folded back from reviewer-accepted corrections shaped this pass. Corrections teach the next version; they never rewrite this one.*