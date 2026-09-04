# Screening memo — Kestrel (T04)

*Drafted by deal-ready · 10/10 metrics recovered · every figure cites its page · nothing here recommends a transaction.*

## Verdict against the profile

Fit score **85/100** against the "Buy-and-hold software" profile — Pass - criteria not met on this profile.
Blocked by: ebitda_negative.
The score sorts an inbox; the flags below are the part worth reading.

## The numbers

| metric | value | source |
|---|---|---|
| ARR | $9.6M | p8, textlayer |
| MRR | $800,000 | p8, textlayer |
| Recurring revenue share | 95% | p2, textlayer |
| Gross margin | 71% | p8, textlayer |
| EBITDA | -$2.4M | p8, textlayer |
| YoY growth | 22% | p2, textlayer |
| Gross revenue retention | 87% (chart axis — confirm <!--co-T04-axis_read-001-->) | p7, vision |
| Net revenue retention | 112% (chart axis — confirm <!--co-T04-axis_read-002-->) | p7, vision |
| Largest customer share | 9% (chart label <!--co-T04-label_read-001-->) | p6, vision |
| Top-five customer share | 26% (chart label <!--co-T04-label_read-002-->) | p6, vision |

## What the rules flagged

- **BLOCKER** — EBITDA of -$2.4M is negative (p8). A permanent-capital buyer holds without an exit to underwrite the burn. Loss-making at this size is a mandate mismatch rather than a valuation argument.

<details><summary>Context notes (info-grade)</summary>

- Rule of 40 score is -3, below the growth-investor benchmark. Growth of 22% plus an EBITDA margin of -25% totals -3. Context rather than a flag: Rule of 40 measures fitness for a growth-and-exit thesis. A permanent-capital holder is buying durability, and a profitable niche business with modest growth will fail this test while being exactly the target it wants. Read it alongside retention, not instead of it.

</details>

## Judgement — read with suspicion

*Model observations on the narrative. Each one is a suggestion with a name attached; accept, edit or strike it. Striking is signal too.*

<!--co-T04-judgement-001-->
- The business relies on a single founder who writes production code for its core settlement logic, with no CTO or documented succession plan to mitigate the risk of operational paralysis if that individual departs. (p9)

<!--co-T04-judgement-002-->
- Revenue growth of 22% combined with negative EBITDA yields a Rule of 40 score of -3, indicating the company is burning cash at a rate that makes organic scaling without significant external capital highly improbable. (p8)

<!--co-T04-judgement-003-->
- The document highlights 'data asset' quality as a moat but fails to disclose whether the proprietary telematics models are deterministic algorithms or probabilistic AI, leaving uncertainty about their ability to predict failures before they occur. (p2)

<!--co-T04-judgement-004-->
- While gross retention is reported, the absence of net retention metrics obscures whether the company can sustainably acquire new customers to offset churn and expansion within its existing base. (p7)

<!--co-T04-judgement-005-->
- The anchor customer list consists entirely of healthcare providers, creating a narrow market concentration that exposes the business to sector-specific regulatory or operational shocks unrelated to general fleet maintenance trends. (p13)

## Outside the document — for consideration, not scoring

*None of this moved a metric, a rule, a fit score or a tier. It is context a reviewer weighs, and it carries its own uncertainty.*

**Customer health.** 1 of 5 researched customers show distress signals, together 4.0% of ARR. Largest is Aldercrest Medical at 4.0%. Roster covers 26.0% of ARR; the remainder was not researched.

| Customer | Share of ARR | Status |
|---|---|---|
| Verity Health Network | 9.0% | no signal found — expanding |
| Stonebridge Clinics | 7.0% | no signal found — stable |
| Aldercrest Medical | 4.0% | **distress** — two sites closed, headcount reduction announced |
| Pemberton Care Group | 3.5% | no signal found — stable |
| Wynhurst Family Health | 2.5% | no signal found — stable |

*Roster covers 26.0% of ARR. 5 researched, 0 not. An unresearched customer is an open question, not a clean bill of health.*

> **Why this is not in the retention number.** Gross retention is a lagging measure. It cannot contain a customer that has not left yet, so a distressed customer base and a healthy retention history are perfectly consistent with each other.

**Base rate — what happened to businesses like this one.**

Matched on **size band + retention band** against **21 past acquisitions**. This is not a forecast for this target; it is what comparable businesses went on to do.

| | Revenue CAGR, 3 years after acquisition |
|---|---|
| 10th percentile | 3.03% |
| **Median** | **5.34%** |
| 90th percentile | 8.11% |
| Shrank outright | 4.8% of the cohort |

**Underwriting calibration on that same cohort: the case ran 3.63 points optimistic at the median, and was optimistic on 95.2% of them.** Read the median above with that in mind.

*Cohort, for audit — every figure above recomputes from these 21 deals: D007, D009, D012, D025, D034, D050, D063, D065, D069, D071, D074, D088, D090, D097, D100, D104, D107, D108, D113, D114, D118.*

## What would have to be true

*Not a forecast. These are the assumptions the base rate rests on for this target, each one traceable to the input that produced it and each one stated so it can be disproved. An assumption nobody can disprove is a sentiment and does not belong here.*

| # | Assumption | Rests on | Falsified by |
|---|---|---|---|
| 1 | The acquisition will achieve positive EBITDA growth comparable to the median historical performance of similar deals. | A (EBITDA of -$2.4M is negative) | Evidence showing that Kestrel's current operating losses are due to temporary scaling costs rather than structural inefficiencies, or data proving that the company has already achieved profitability despite the negative EBITDA figure. |
| 2 | The recurring revenue base is stable and will not experience significant churn beyond the net retention rate of 112%. | A (NRR of 112%) | Customer health data indicating distress signals among a disproportionate number of customers, or external research revealing industry-wide trends causing higher-than-expected churn. |
| 3 | The top five customers represent a manageable concentration risk that does not threaten overall business continuity. | A (Top 5 customer percentage is 26%) | Evidence showing that one or more of the top five customers are actively planning to exit, have financial distress themselves, or represent a significant portion of total revenue loss if they leave. |
| 4 | The company's growth trajectory is sustainable given its current year-over-year growth rate. | A (YoY growth percentage is 22%) | Evidence showing that the recent growth was driven by a one-time event, such as a large acquisition or a temporary market spike, rather than organic expansion. |
| 5 | The gross margin of 71% is indicative of long-term profitability potential. | A (Gross margin percentage is 71%) | Evidence showing that the high gross margin is due to temporary factors, such as a lack of inventory costs or one-time revenue recognition practices, which are not sustainable. |

*Input blocks: **A** the document · **B** the base rate from past acquisitions · **C** customer health · **D** external research.*

## Ask the seller

- Gross revenue retention was interpolated from chart geometry, not printed on the page (reader measured 100% on the committed eval). Independent re-read by qwen3.8:27b agrees with the measurement within 0. Confirm or replace
- Net revenue retention was interpolated from chart geometry, not printed on the page (reader measured 100% on the committed eval). Independent re-read by qwen3.8:27b agrees with the measurement within 0. Confirm or replace

---

*3 judgement example(s) folded back from reviewer-accepted corrections shaped this pass. Corrections teach the next version; they never rewrite this one.*