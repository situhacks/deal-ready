# Screening memo — Ridgeline (T03)

*Drafted by deal-ready · 10/10 metrics recovered · every figure cites its page · nothing here recommends a transaction.*

## Verdict against the profile

Fit score **92.2/100** against the "Buy-and-hold software" profile — Pass - criteria not met on this profile.
Blocked by: recurring_below_floor.
The score sorts an inbox; the flags below are the part worth reading.

## The numbers

| metric | value | source |
|---|---|---|
| ARR | $11.2M | p8, textlayer |
| MRR | $933,333 | p8, textlayer |
| Recurring revenue share | 58% | p2, textlayer |
| Gross margin | 52% | p8, textlayer |
| EBITDA | $1.0M | p8, textlayer |
| YoY growth | 11% | p2, textlayer |
| Gross revenue retention | 89% (chart axis — confirm <!--co-T03-axis_read-001-->) | p7, vision |
| Net revenue retention | 97% (chart axis — confirm <!--co-T03-axis_read-002-->) | p7, vision |
| Largest customer share | 12% (chart label <!--co-T03-label_read-001-->) | p6, vision |
| Top-five customer share | 31% (chart label <!--co-T03-label_read-002-->) | p6, vision |

## What the rules flagged

- **BLOCKER** — Only 58% of revenue is recurring, against a 80% floor (p2). The headline ARR is carrying services, implementation or licence revenue that will not repeat. This is the single most common way a software business looks larger than it is; the multiple should be applied to the recurring base, not the headline.
- **WARNING** — Gross margin of 52% is below the 65% floor (p8). Software margins below the floor usually mean a services-heavy delivery model or hosting costs carried in COGS. It changes what the business is.

<details><summary>Context notes (info-grade)</summary>

- Net retention of 97% is below 100%. Below 100% the existing base shrinks without new logos. Not disqualifying for a durable niche product, but it caps organic growth.
- Rule of 40 score is 20, below the growth-investor benchmark. Growth of 11% plus an EBITDA margin of 9% totals 20. Context rather than a flag: Rule of 40 measures fitness for a growth-and-exit thesis. A permanent-capital holder is buying durability, and a profitable niche business with modest growth will fail this test while being exactly the target it wants. Read it alongside retention, not instead of it.

</details>

## Judgement — read with suspicion

*Model observations on the narrative. Each one is a suggestion with a name attached; accept, edit or strike it. Striking is signal too.*

<!--co-T03-judgement-001-->
- The document claims the platform is hosted and configurable but provides no evidence of the underlying technology stack, raising concerns about legacy code dependencies or unsupported infrastructure. (p5)

<!--co-T03-judgement-002-->
- Management attributes all implementation delivery to its own services team without identifying specific individuals or a dedicated technical lead, creating significant founder dependency risk for complex configuration work. (p9)

<!--co-T03-judgement-003-->
- The absence of any mention of the core application's age, language, or database version in the technology section suggests a lack of transparency regarding generational technical risks. (p10)

<!--co-T03-judgement-004-->
- While the document states that ongoing support is included in subscriptions, it fails to quantify the cost of this service relative to revenue, obscuring the true economics of the bundled implementation and support model. (p3)

<!--co-T03-judgement-005-->
- The definition of recurring revenue as 'contracted, annualised' rather than actual cash collected masks the reality that a significant portion of revenue may be tied up in unbilled or uncollected amounts. (p8)

## Ask the seller

- Gross revenue retention was interpolated from chart geometry, not printed on the page (reader measured 100% on the committed eval). Independent re-read by qwen3.8:27b agrees with the measurement within 0. Confirm or replace
- Net revenue retention was interpolated from chart geometry, not printed on the page (reader measured 100% on the committed eval). Independent re-read by qwen3.8:27b agrees with the measurement within 0. Confirm or replace

---

*3 judgement example(s) folded back from reviewer-accepted corrections shaped this pass. Corrections teach the next version; they never rewrite this one.*