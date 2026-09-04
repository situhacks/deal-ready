# Enrichment experiments — running record

**Question behind all four:** a screen reads numbers off a document. Sometimes the number is not
the whole story, and the state of the world around the company matters. Can outside signals and
prediction enrich the memo?

**Constraint held throughout: none of this scores.** Everything here lands in the memo as flagged
context a human reads and judges. Nothing moves a criterion, a fit score, or a tier. The moment a
signal moves a number, the tool stops being the thing whose numbers re-derive offline.

Started 2026-09-03. Kept as it went, including what failed.

---

## Experiment 1 — Customer health

**Why this one first:** it is what the acquirer actually asked for. *"Wouldn't it be rich to find
out our customers might be going out of business, and there's predicting future churn that might
happen as a result of it... what is possible when human time isn't your constraint?"*

That is not extrapolation. A retention curve is a lagging measure — **it cannot contain a customer
that has not left yet.** The question is whether the target's customers are themselves in trouble,
and nobody researches four hundred of them by hand because it costs more than it returns.

### What was built

The corpus had no customers, so the generator gained them: five named anchor accounts per target,
each with a share of ARR and a ground-truth `distress` flag the generator owns. A thirteenth page
renders the roster into the deck.

`deal_ready/signals/customers.py` parses the roster off the page, aggregates researched distress
into a share of ARR, and emits a call-out phrased as a question.

### Two things the repo caught while building it

**The leak guard fired, correctly.** The roster first printed "Share of ARR" as percentages — and
the top-1 and top-5 shares are chart-carried by design. Printing them as text leaked chart-only
values into the text layer and would have invalidated the central finding. `generate.py` refused to
build. The roster now prints **dollar contract values**; the percentage is derived.

**The page went last on purpose.** Appending as page 13 leaves every existing page number
untouched, so the committed ground truth, the vision cache and the pixel re-measurement checks keep
pointing at the same pages.

### Result

**Roster extraction: 25/25 customers across 5 targets (100%),** names and derived shares matching
ground truth.

| Target | Severity | Distressed % of ARR | Roster covers |
|---|---|---|---|
| T01 Meridian | none | 0.0 | 19.0% |
| T02 Halyard | **material** | **49.0** | 71.0% |
| T03 Ridgeline | noted | 8.0 | 31.0% |
| T04 Kestrel | noted | 4.0 | 26.0% |
| T05 Ashgrove | **material** | **18.0** | 28.0% |

### The finding that justifies the whole experiment

**T02 Halyard already fails the concentration rule** — one customer at 34% against a 15% cap. The
rubric catches that. What the rubric cannot see is that **that customer filed for creditor
protection**, and the second-largest at 15% was **acquired by a competitor running a rival
platform**. Together 49% of ARR is under a live threat that appears nowhere in a retention history
of 96%.

The number said "concentrated." The world said "concentrated, and the anchor is sinking." That gap
is the entire argument for the enrichment layer.

T05 Ashgrove is the subtler version: 81% gross retention already breaches the floor, and two
customers totalling 18% of ARR are consolidating or idling through the commodity trough. The
retention line is backward-looking; the trough is not over.

### Honest limits

- **Discovery is not tested and cannot be.** These companies do not exist, so whether research
  correctly identifies distress is unmeasurable here. What is measured is roster extraction and the
  aggregation arithmetic. The research step is the plugin path.
- **Coverage bounds everything.** T01's roster covers 19% of ARR. A clean read across five
  customers says nothing about the other 81%, and the signal reports that on every line.
- **Derived percentages carry rounding error.** The deck prints `$2.1M`, so T02's largest parses at
  34.43% against a true 34.0%. Tolerable for a signal, and it would not be tolerable for a score,
  which is one more reason this never becomes one.
- **An unresearched customer is counted as unresearched**, never as healthy. The distinction is the
  point.

---

## Experiment 2 — The outside-signal layer

`plugins/deal-ready/skills/outside-signals/SKILL.md`. The wide search the whitelist deliberately
does not cover: customer health, demand direction, buyer appetite, AI exposure, cycle context.

**The wall is the design.** Tier A is the whitelist — bands with a sample and a method, citable in a
memo. Tier B is this — dated observations a human weighs. **A Tier B finding may never become a
Tier A number.** Without that separation the wide search contaminates the careful part, and the
careful part is the only reason anyone trusts the tool.

The T05 research from the earlier round already produced a good Tier B finding — the commodity
trough that changes what 81% retention *might mean* without changing the number — and had nowhere
to put it. It ended up in a limitations section. That is the gap this closes.

---

## Experiment 3 — TimesFM against the baselines that decide it

### The unlock

A CIM carries four annual points and nothing forecasts from four points. So the generator grew a
time axis: **60 monthly observations per target, 48 as history, 12 held out**, built from the
profile's own stated ARR and growth so it cannot drift away from the deck. Deterministic, seeded,
regenerates identically.

**The generator owns the future, which is the only reason this is worth running.** Almost every
forecasting demo has no ground truth for the window it predicts. This one does, the same way every
other number in the repo does.

Two archetypes deteriorate inside the holdout — the concentration case and the legacy case — because
a forecaster that only sees smooth growth is being tested on the wrong thing.

### Result — 12-month horizon, 5 targets, MASE against in-sample seasonal naive

| Method | Mean MASE | Mean MAPE | Seconds |
|---|---|---|---|
| **timesfm_3** (330M) | **0.354** | **2.46%** | 2.55 |
| **timesfm_2.5** (200M) | 0.441 | 3.20% | 4.76 |
| drift | 0.660 | 3.65% | 0.00 |
| linear_fit | 0.717 | 4.32% | 0.00 |
| seasonal_naive | 1.154 | 9.68% | 0.00 |

**Both foundation models beat every baseline.** TimesFM-3 is 46% better than the best baseline on
MASE, and faster than 2.5 despite being larger.

### Where the gain actually lives — the per-target table is the finding

| Target | timesfm_3 | timesfm_2.5 | drift | linear_fit | seasonal_naive |
|---|---|---|---|---|---|
| T01 clean | 0.182 | 0.232 | 0.224 | 0.382 | 1.276 |
| T02 concentration *(decays)* | 0.254 | 0.321 | 0.481 | 0.451 | 1.010 |
| T03 fake saas *(lumpy)* | 0.348 | **0.754** | 0.501 | 0.453 | 1.149 |
| T04 unprofitable | 0.389 | 0.356 | 0.405 | 0.603 | 1.469 |
| T05 legacy *(decays)* | 0.596 | 0.543 | **1.687** | **1.697** | 0.863 |

**On the clean target the foundation model is barely worth it** — drift scores 0.224 against
TimesFM-3's 0.182. A straight line is nearly as good on a smooth series, which is what the baseline
existed to reveal.

**On the decaying target the baselines actively hurt.** Drift at 1.687 and linear at 1.697 are
*worse than doing nothing* — worse than repeating last year's month — because they project a growth
trend into a decline. Both foundation models hold near 0.55. **That is where the model earns its
place: not on the easy series, on the one where naive extrapolation is dangerous.**

**And 2.5 is unreliable where 3 is not.** On the lumpy revenue series T03, TimesFM-2.5 scores 0.754,
worse than both drift and a straight line. TimesFM-3 handles it at 0.348.

### Two API notes for anyone repeating this

TimesFM-3 is **not** a drop-in for 2.5. Different class (`TimesFM3Forecaster`, not
`TimesFM_2p5_200M_torch`), different call (`predict` one series at a time, not a compiled batch
`forecast`), and the result is a `ForecastOutput` whose array is on `.forecast`. The published model
id is `google/timesfm-3.0-pytorch`.

### Honest limits

- **The corpus is favourable.** Trend plus sine seasonality plus gaussian noise is close to what a
  time-series foundation model is trained on. Real ARR has step changes, contract lumpiness and
  churn events. **This result would not transfer unchanged to a real book of business.**
- **Five series is not a sample.** It is an existence proof and a baseline comparison, nothing more.
- **The decay was authored.** Both models handled it well, but the corpus author decided how sharp
  it was.
- **No forecast goes in the scorecard.** It is a separate exhibit with its own eval.

---

## Experiment 4 — Persona red-team, measured against the rules

Borrowed from the swarm-simulation projects, reframed. Those ask a population of agents *what will
happen*, and the literature is unkind: against 120,000+ personas of real humans, LLM agents scored
MCC 0.29 while ordinary text classifiers scored 0.36, with individual-level accuracy under 5%. So
this does not forecast. **Four personas read the values and the customer signal and generate
challenges**, and the output is scored as coverage.

Each challenge lands in one of three buckets: **redundant** (a rule already flagged it),
**novel-real** (a risk the corpus encodes that no rule can express), or **noise**.

### Result — 59 challenges across 5 targets, stable across three consecutive runs

| Bucket | Count | Share |
|---|---|---|
| Redundant | 20 | 34% |
| **Novel-real** | **12** | **20%** |
| **Noise** | **27** | **46%** |

**One in five challenges is genuinely new. Nearly half are noise.**

### A measurement bug worth recording, because it doubled the headline

The first run reported a **41% novel rate**. It was wrong. The classifier matched `"ai"` as a
substring, and `"ai"` hides inside **"ret*ai*n"**, **"rem*ai*ning"** and **"av*ai*lable"** — so
ordinary retention questions were being counted as AI-displacement insights. Word-boundary matching
took the novel rate from 41% to 20%.

**I also suspected run-to-run instability when the number moved. That was wrong too** — three
consecutive runs produce 20/12/27 identically. The entire swing was the bug.

### The good ones are genuinely good

> *"Can Ashgrove's two-decade-old provincial grading logic be re-engineered fast enough if
> Saskatchewan regulators change their settlement rules next harvest?"*

> *"If Kettleridge exits and Braemar delays renewal, does the remaining roster have enough mass to
> absorb a 20% ARR shock?"*

Neither is expressible as a rule. The second one reads the customer signal against the concentration
number — a join no threshold can make.

### The honest cost

Twelve challenges per target, of which roughly two are new and five or six are noise. **A reviewer
pays attention for all twelve.** That ratio is the argument against shipping it unbounded, and it is
why the adoption verdict below is conditional rather than enthusiastic.

---

# What we adopt

| Experiment | Verdict | Where it lives |
|---|---|---|
| **1 · Customer health** | **Adopt. Shipped.** | A memo section, `deal_ready/signals/customers.py` |
| **2 · Outside-signal layer** | **Adopt. Shipped.** | `outside-signals` skill; the Tier A/B wall |
| **3 · TimesFM forecasting** | **Adopt as a separate exhibit. Not in the screen.** | `eval/forecast.py`, `reports/forecast_bakeoff.json` |
| **4 · Persona red-team** | **Not adopted as-is.** Kept as an eval | `eval/redteam_eval.py`, no memo section |

## 1 and 2 — adopted, and the reason is one paragraph in a memo

T02 Halyard fails the concentration rule at 34% against a 15% cap, and the rubric catches that
perfectly. What no rule can reach is that **the 34% customer filed for creditor protection and the
15% customer was bought by a competitor running a rival platform.** Forty-nine percent of ARR is
under live threat, against a retention history of 96%.

**That is the whole thesis of the enrichment layer in one target.** The number was right and
incomplete. A retention measure is lagging by construction — it cannot contain a customer that has
not left yet — so a healthy retention line and a collapsing customer base are perfectly consistent,
and only one of them is in the document.

Both ship as **context for consideration**, in their own memo section, under a heading that says
they scored nothing.

## 3 — TimesFM: real skill, wrong shape for a CIM

**It works, and the per-target table says where.** On the clean series a straight line is nearly as
good. On the decaying series, drift and linear fit score 1.687 and 1.697 — *worse than repeating
last year's month* — while both foundation models hold near 0.55. **A model earns its place where
naive extrapolation is actively dangerous, which is exactly the target you most need to be right
about.**

**But it needs a monthly series, and a CIM gives you four annual points.** The corpus grew a time
axis to make the experiment possible; a real deal would not hand you one. So this is adopted as an
**exhibit with its own eval and its own limits**, never as an input to the screen — and the repo now
has a check that makes that structural rather than a promise.

If a data room ever produces monthly ARR, the machinery is here and measured.

## 4 — the red-team: good questions, bad ratio

**Twelve challenges per target: roughly two genuinely new, four redundant, five or six noise.** The
good ones are very good — *"can two-decade-old provincial grading logic be re-engineered fast enough
if regulators change settlement rules next harvest?"* is not expressible as a rule, and no threshold
could ever produce it.

**But a reviewer pays attention for all twelve.** A 20% novel rate against a 46% noise rate is not a
trade a screening tool should make on the reviewer's behalf, and shipping it unbounded would spend
the credibility the rest of the memo earns.

**Kept as an eval, not a feature.** If it ships later it needs a filter and a hard cap — three
challenges per target, best-of — and that filter needs its own measurement before anyone trusts it.

## What the experiments cost, honestly

Two real bugs, both mine, both found by measuring rather than reading:

- **The roster leaked chart values into the text layer.** The generator's own leak guard failed the
  build and refused to write the corpus. Fixed by printing dollars instead of percentages.
- **The red-team's novel rate was double what it should have been**, because `"ai"` matched inside
  `"retain"`. 41% became 20% when the classifier learned about word boundaries. **I then suspected
  run-to-run instability, which was also wrong** — three consecutive runs are identical, and the
  entire swing was the bug.

The second one matters more than it looks. **A measurement instrument reported a result twice as
good as the truth, and nothing but re-reading the raw output would have caught it.** That is the
argument for keeping the raw challenges committed alongside the score.

## The rule that governs all of it

**Nothing here scores.** Not the customer signal, not a forecast, not a persona's question. The wall
is enforced by `run_checks.py`: the scorer, the rules, the fit calculation and `screen.py` may not
import the signals package at all. Wire an outside signal into a criterion and the build goes red.

That is the only reason the enrichment layer is safe to add. The screen's numbers still re-derive
offline from committed artifacts, exactly as before — and the world around the company now sits
beside them, clearly labelled as something a human has to weigh.
