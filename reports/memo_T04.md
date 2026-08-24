# Screening memo — Kestrel (T04)

*Drafted by deal-ready · 10/10 metrics recovered · every figure cites its page · nothing here recommends a transaction.*

## Verdict against the profile

Fit score **85/100** against the "Buy-and-hold vertical market software" profile — Pass - criteria not met on this profile.
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
- Management highlights a difficult-to-replicate data asset but fails to disclose whether the proprietary predictive models are proprietary algorithms or simply trained on historical telematics data, creating ambiguity about the true source of competitive advantage. (p2)

<!--co-T04-judgement-003-->
- The document presents EBITDA as negative while simultaneously adding back one-time transaction and legal costs to justify the valuation, obscuring the operational reality that the company is burning cash at a rate that contradicts its growth metrics. (p8)

<!--co-T04-judgement-004-->
- Retention is reported only as a net figure including expansion and contraction, which masks the possibility that new customers are being acquired solely through aggressive discounts or churned accounts to maintain the recurring revenue total. (p7)

<!--co-T04-judgement-005-->
- The integration surface is described as supporting customer-built extensions via API, yet no evidence is provided regarding the stability of these integrations or whether they rely on third-party vendors that could introduce supply chain risk. (p5)

## Ask the seller

- Gross revenue retention was interpolated from chart geometry, not printed on the page (reader measured 100% on the committed eval). Independent re-read by qwen3.8:27b agrees with the measurement within 0. Confirm or replace
- Net revenue retention was interpolated from chart geometry, not printed on the page (reader measured 100% on the committed eval). Independent re-read by qwen3.8:27b agrees with the measurement within 0. Confirm or replace

---

*3 judgement example(s) folded back from reviewer-accepted corrections shaped this pass. Corrections teach the next version; they never rewrite this one.*