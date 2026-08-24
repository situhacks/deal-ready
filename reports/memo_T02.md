# Screening memo — Halyard (T02)

*Drafted by deal-ready · 10/10 metrics recovered · every figure cites its page · nothing here recommends a transaction.*

## Verdict against the profile

Fit score **94.7/100** against the "Buy-and-hold vertical market software" profile — Tier 1 - advance to management call.
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
- The business relies on two co-founders who personally manage the largest commercial relationships, creating significant operational risk if either departs. (p9)

<!--co-T02-judgement-002-->
- Revenue concentration is severe with the top five customers accounting for 71% of ARR and a single customer representing 34%, leaving little room for organic growth to offset potential churn. (p6)

<!--co-T02-judgement-003-->
- The core platform is a .NET monolith built in 2020 that runs on a single region with warm standby, lacking the architectural depth or geographic redundancy required for enterprise-grade port operations software. (p10)

<!--co-T02-judgement-004-->
- Management defines gross margin as excluding amortisation and EBITDA via add-backs for transaction costs, which obscures the true profitability impact of heavy implementation and integration expenses. (p8)

<!--co-T02-judgement-005-->
- Retention metrics are presented only as net retention including expansion, masking whether the core product is actually driving stickiness or if growth is purely driven by upselling existing clients. (p7)

## Ask the seller

- Gross revenue retention was interpolated from chart geometry, not printed on the page (reader measured 100% on the committed eval). Independent re-read by qwen3.8:27b agrees with the measurement within 0.2. Confirm or replace
- Net revenue retention was interpolated from chart geometry, not printed on the page (reader measured 100% on the committed eval). Independent re-read by qwen3.8:27b agrees with the measurement within 0.2. Confirm or replace

---

*3 judgement example(s) folded back from reviewer-accepted corrections shaped this pass. Corrections teach the next version; they never rewrite this one.*