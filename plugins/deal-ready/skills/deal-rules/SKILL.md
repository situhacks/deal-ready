---
name: deal-rules
description: The screening rubric - thresholds, weights, tier bands, blocker rules - and how to apply it deterministically. Use when scoring a target against acquisition criteria, or when someone asks why a target landed in a tier.
---

# Apply the rubric

The rubric is data, not code: `references/criteria.json`. Swapping in a real acquirer's
scorecard is a config change. That is deliberate — the judgement layer is the asset, and it
should be editable by the people who own the judgement.

**This profile models a buy-and-hold software acquirer.** Its posture, verbatim from the file:

> *Durability over growth. A permanent-capital buyer holds forever, so retention,
> mission-criticality and revenue quality outrank growth rate. A Pass means "not a fit against
> this profile", never "bad company".*

Say that out loud when reporting a Pass. It is the difference between a screen and a judgement.

## The criteria

| Criterion | Threshold | Weight |
|---|---|---|
| ARR band | $2M–$30M | 15 |
| Recurring revenue share | ≥ 80% | 20 |
| Gross revenue retention | ≥ 85% | 20 |
| Net revenue retention | ≥ 100% | 10 |
| Gross margin | ≥ 65% | 10 |
| EBITDA positive | required | 15 |
| Customer concentration | top-1 ≤ 15%, top-5 ≤ 35% | 10 |
| Rule of 40 | ≥ 40 | **0 — reported, never scored** |

**Rule of 40 carries weight zero by design.** It is a growth-investor test, and a
permanent-capital buyer is not underwriting an exit. Report it as context. Do not let it move a
score, and do not let anyone quietly re-add it because the number looks good.

Its denominator is a trap worth naming: EBITDA margin over *what?* A CIM often states ARR and
EBITDA but never total revenue, and the two bases give different answers. **Take the margin over
ARR when total revenue is not stated, and say which basis you used.** A zero-weight metric is
exactly where an undefined formula hides until someone re-weights it.

## How a criterion converts to points

**Partial credit, not pass/fail.** This is the rule that decides the tier, so it is stated
here rather than left to convention.

| Criterion shape | Meets it | Misses it |
|---|---|---|
| **Floor** (recurring, GRR, NRR, gross margin) | full weight | `weight × (value ÷ floor)` |
| **Band** (ARR) | full weight | `weight × (nearer edge ÷ further of value and edge)` |
| **Required** (EBITDA positive) | full weight | zero |
| **Missing metric** | — | **zero for that component, and reported missing** |

Worked, on a target with gross retention of 81% against an 85% floor and a weight of 20:

```
20 × (81 ÷ 85) = 19.06 earned, basis "below floor"
```

**Not zero.** Binary scoring would drop that target roughly 20 points and can move it a whole
tier — the difference between "advance to management call" and "diligence questions attached"
on a company that missed a floor by four points. Partial credit is what makes the score a
sorting device rather than a verdict.

**Round only at the end.** Components carry two decimals; the score is rounded once.

## Tiers

| Score | Tier |
|---|---|
| ≥ 75 | Tier 1 — advance to management call |
| ≥ 55 | Tier 2 — diligence questions attached |
| < 55 | Pass — criteria not met on this profile |

**Report the coverage beside the score, always.** A 97.7 from ten recovered metrics and a 97.7
from six are not the same claim, and the score alone cannot tell them apart.

## Blockers

Three findings are blockers regardless of score: **recurring share below the floor**, **negative
EBITDA**, **ARR outside the band**.

A blocker is not a veto on the company. It means this profile does not screen it in, and the
reason is stated so a human can override with their eyes open.

## Concentration is a repricing signal, not a fail

From the file: breaching a cap *"does not auto-fail. It reprices: a buyer underwrites the risk
that one departure removes a material share of revenue."* Report the exposure in revenue terms —
what leaves if the top customer leaves — not just the percentage.

## How to apply it

1. **Compute derived values rather than trusting stated ones** when both exist. If a stated
   margin and a computed margin disagree, that is a **definition conflict** and a finding, not a
   rounding difference to resolve silently.
2. **Evaluate every criterion, including ones that pass.** The record of what passed is what
   makes the score auditable.
3. **Record which value decided each criterion**, with its page and read type. A criterion
   decided by an axis read is a criterion decided by an interpolation, and the memo must say so.
4. **A missing metric is not a zero.** Score what you have, report the coverage, and name what
   was missing. Silently treating absent as failing is how a screen becomes wrong.
5. **Do not adjust the tier because the narrative is good.** The rubric is the rubric. If the
   narrative matters, it goes in the memo as a flagged observation.

## What the rubric cannot do

It does not know the vertical's benchmark bands — 85% gross retention clears this floor but sits
below the premium threshold in healthcare IT. That is what `market-context` is for, and it is why
context sits beside the scorecard rather than inside it.

It also does not price AI exposure, which increasingly moves multiples. That is a diligence
question this profile does not yet encode — a known gap, stated rather than hidden.
