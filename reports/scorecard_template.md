# Scorecard template - Buy-and-hold software

Models the acquisition criteria of buy-and-hold software acquirers: durable, mission-critical products with recurring revenue. Swapping in a real scorecard is a config change, not a rewrite - which is the point of keeping this out of the code.

**Posture.** Durability over growth. A permanent-capital buyer holds forever, so retention, mission-criticality and revenue quality outrank growth rate. A Pass means 'not a fit against this profile', never 'bad company'.

## The rubric

| Demand | Threshold | Weight |
|---|---|---|
| ARR inside the mandate band | $2.0M - $30.0M | 15 |
| Recurring revenue share, floor | 80% | 20 |
| Gross revenue retention, floor | 85% | 20 |
| Net revenue retention, target | 100% | 10 |
| Gross margin, floor | 65% | 10 |
| EBITDA positive | required | 15 |
| Customer concentration caps | largest <= 15%, top five <= 35% | 10 |
| Rule of 40 | >= 40%, context only | 0 |

Concentration note: Breaching either does not auto-fail. It reprices: a buyer underwrites the risk that one departure removes a material share of revenue.

Rule of 40 note: Weight 0 by design. Rule of 40 is a growth-investor test; a permanent-capital buyer is not underwriting an exit. Reported as context, never scored. See deal_ready/scorer/rules.py R9.

## Tier bands

- Score >= 75: Tier 1 - advance to management call
- Score >= 55: Tier 2 - diligence questions attached
- Below 55: Pass - criteria not met on this profile

Blocker rules - a breach on any of these caps the tier regardless of score: recurring_below_floor, ebitda_negative, arr_outside_band.

*This document is generated from `criteria/default.json`. Edit the JSON, re-run, and the template follows - it is never hand-edited.*
