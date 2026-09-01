# The rules, and the question each one opens

Every rule here is deterministic Python over values a parser extracted. No model
decides anything on this page.

The framing that makes them useful: **a finding is not a verdict, it is the next
question.** A screen exists to turn forty pages into a short list of things to ask on
the management call. Each rule below therefore carries what it checks, why a
permanent-capital buyer cares, and what an analyst should ask next.

Severities: **blocker** caps the tier regardless of score · **warning** reprices or
adds a diligence workstream · **info** is context that should not move a decision on
its own.

| # | Rule | Severity | What it checks |
|---|---|---|---|
| R1 | `arr_mrr_mismatch` | warning | Stated ARR vs annualised MRR, >5% drift |
| R2 | `arr_outside_band` | **blocker** | ARR inside the mandate band |
| R3 | `recurring_below_floor` | **blocker** | Recurring share of revenue vs floor |
| R4 | `grr_below_floor` | warning | Gross retention vs floor |
| R5 | `grr_above_100` | warning | Gross retention reported above 100% |
| R6 | `nrr_below_target` | info | Net retention below 100% |
| R7 | `gross_margin_below_floor` | warning | Gross margin vs floor |
| R8 | `ebitda_negative` | **blocker** | Profitability |
| R9 | `rule_of_40_below_growth_benchmark` | info | Growth + margin (scored at zero weight) |
| R10 | `top1_concentration_breach` / `top5_concentration_breach` | warning | Customer concentration vs caps |
| R11 | `metrics_not_stated` | info | Which core metrics the document omits |

---

### R1 · ARR does not tie to annualised MRR

The first arithmetic a buyer runs. If exit-month MRR times twelve is materially below
stated ARR, non-recurring revenue is sitting inside the headline — implementation fees,
training, one-time licences.

**Ask:** what exactly is inside the ARR figure, line by line? And what is the
twelve-month MRR series, not the exit month?

### R2 · ARR outside the mandate band — *blocker*

A fit question, not a quality judgement. The company may be excellent and simply be the
wrong size for this buyer. Below the band it cannot absorb the overhead of being owned;
above it, the buyer is competing with a different class of acquirer.

**Ask:** nothing — this one is a routing decision, not a diligence item.

### R3 · Recurring revenue below floor — *blocker*

The metric that decides whether this is software or a consultancy with software
attached. Blocker because it changes what multiple applies, not merely what price.

**Ask:** split revenue into subscription, services, and one-time for three years. Then
re-run the screen against the subscription line alone and see what is left.

### R4 · Gross retention below floor

The base is leaking. For a buyer that holds forever, a leak compounds every year of
ownership — this is the number that most separates a permanent asset from a wasting one.

**Ask:** logo churn versus revenue churn, and the reason codes. Customers lost to
competitors, to insourcing, and to going out of business are three different diseases.

### R5 · Gross retention reported above 100%

Not possible by construction: gross retention excludes expansion. A figure above 100
means net retention has been labelled gross, which flatters the base.

**Ask:** the definition, in writing, and the calculation for both figures. Politely —
this is usually sloppiness rather than intent, but it must be corrected before the
number reaches a model.

### R6 · Net retention below 100% — *info*

The installed base shrinks without new logos. Not disqualifying for a durable niche
product with nothing to upsell, but it caps organic growth.

**Ask:** is there a second product, and has anyone tried to sell it to this base?

### R7 · Gross margin below floor

Usually a services-heavy delivery model or hosting costs that never came down.

**Ask:** where support headcount is booked. Support classified as R&D rather than COGS
lifts margin without changing the business at all.

### R8 · EBITDA negative — *blocker*

A permanent-capital buyer has no exit to underwrite the burn. Loss-making at this size
is a mandate mismatch rather than a valuation argument.

**Ask:** nothing, unless the loss is a deliberate growth investment the buyer intends to
switch off — in which case model it switched off and re-screen.

### R9 · Rule of 40 — *info, and deliberately unscored*

Kept as context, given zero weight. It is a growth-investor test: it asks whether burn
is buying growth, which matters when you need a step-up at exit. A permanent-capital
buyer wants a profitable, sticky, slow-growing business, which fails Rule of 40 by
construction.

During development this fired on all five targets **including the clean one** — the tell
that a benchmark has been imported from the wrong thesis. See
[`metrics.md`](metrics.md) for the longer version.

### R10 · Customer concentration above caps

One departure removes that share of revenue in a single renewal cycle. This reprices a
deal; it rarely kills one.

**Ask:** the change-of-control and assignment clauses in those contracts, first. The
risk is not that a customer is large — it is that a large customer may be entitled to
walk *because the company changed hands*. Then: contract end dates, who owns the
relationship, and whether that person is staying.

### R11 · Core metrics not stated — *info*

**Absence is information.** A CIM that omits gross retention has usually omitted it on
purpose. This rule exists so a gap becomes the first management-call question rather
than a silent zero in an average.

**Ask:** for the missing figure directly, and note how long it takes to arrive.

---

## What these rules cannot see

Worth being explicit, because the gap is where the real risk lives.

Ashgrove in this corpus clears every blocker and still scores 97.7 into Tier 1 — its only
flags are a gross-retention warning and two info lines — and it is the most dangerous
company in the set: the founder is the only person who has worked on the settlement
engine, writes production code, approves every release, holds the six largest customer
relationships personally, and there is no succession plan. The core is a 1998 Delphi
application with no test coverage on an unsupported database.

**None of that is visible to arithmetic.** It is visible in the narrative, and catching
it needs a calibrated judgement layer scored against a held-out labelled set — not
another rule. Until that exists, this tool reads the numbers and a human reads the
document.

That division is the honest version of what a screener is for.
