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
| **3 · TimesFM forecasting** | **Adopt as a separate exhibit. Not in the screen.** See experiment 5 — the real-data test changes the story | `eval/forecast.py`, `reports/forecast_bakeoff.json` |
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


---

## Experiment 5 — TimesFM against real companies, and what it costs the synthetic result

Experiment 3 was a rig test: the generator wrote the answer key, so a good score proved
the plumbing worked and nothing about the world. This is the real one.

**Six real vertical-software companies. 179 quarters of revenue, pulled from their own SEC
filings.** AppFolio, Manhattan Associates, Paycom, Paylocity, Tyler Technologies, Veeva — the asset
class a permanent-hold software acquirer actually looks at. Train on everything up to a cut, forecast
forward, compare to what the companies went on to report.

Source is EDGAR's XBRL API: free, no key, and **every quarter carries the accession number of the
filing that reported it**, which is the property that makes any of this usable for accounting work.

### One year forward

| Method | Mean MASE | Mean MAPE |
|---|---|---|
| timesfm_3 | **0.502** | 5.35% |
| drift | 0.507 | 5.77% |
| timesfm_2.5 | 0.589 | 6.21% |
| linear_fit | 0.823 | 8.77% |
| seasonal_naive | 1.286 | 14.22% |

**TimesFM-3 and drift are tied.** 0.502 against 0.507 is not skill, it is a rounding difference.
And per company there is no consistent winner at all — of six companies, four different methods win
one or more. **Nothing reliably beats anything.**

### Two years forward

| Method | Mean MASE | Mean MAPE |
|---|---|---|
| **drift** | **0.718** | **7.33%** |
| timesfm_3 | 0.846 | 8.35% |
| linear_fit | 1.287 | 12.64% |
| timesfm_2.5 | 1.432 | 15.35% |
| seasonal_naive | 2.239 | 23.57% |

**Drift wins, and it wins four companies out of six.** "Take the last value and add the average
change" beats a 330M foundation model over two years on real software revenue. TimesFM-2.5 at 1.432
is worse than a straight line.

### What this costs the synthetic result, stated plainly

Experiment 3 reported TimesFM-3 at **46% better than the best baseline.** On real data it is **tied
at one year and loses at two.**

**The synthetic corpus flattered the model, and I built the thing that flattered it.** I authored a
decline into the holdout for two archetypes. Drift and linear extrapolate the recent trend, so a
decline they cannot see is exactly where they fail catastrophically — and I had put one there. The
foundation models handled it, scored well, and the number looked like evidence.

It was not evidence. It was a measurement of a choice I had made.

### So when does it actually help?

The real data answers this cleanly, and the answer is narrow:

- **Steady compounding growth → a straight line is as good or better.** Which describes most healthy
  software companies most of the time. Drift *is* the correct model for that, and a foundation model
  adds opacity without accuracy.
- **Regime change → the foundation model earns its place.** Deceleration, inflection, decline. Drift
  assumes the trend continues; when it does not, drift is worse than doing nothing. That was T05 in
  the synthetic run at 1.687 MASE, and it is a real property of extrapolation, not an artifact.

**The honest one-liner: TimesFM is insurance against the trend breaking, not a better ruler.** On a
business that keeps doing what it has been doing, you do not need it.

### What auditable actually looks like

Every run emits, per company and per quarter: what the naive method said, what the model said, **the
dollar difference between them**, and what actually happened. Tyler Technologies, two years out:

| Quarter | Naive | Model | Model − naive | Actual | Model error |
|---|---|---|---|---|---|
| 2024-03-31 | $473.2M | $501.7M | +$28.5M | $512.4M | −$10.7M |
| 2024-06-30 | $471.9M | $508.4M | +$36.5M | $541.0M | −$32.6M |
| 2025-06-30 | $473.2M | $541.9M | +$68.7M | $596.1M | −$54.2M |
| 2026-06-30 | $494.7M | $583.0M | +$88.3M | $645.1M | −$62.1M |

**Read the third column: that is the model's opinion, in dollars.** The naive method says revenue
repeats last year. The model adds $28M rising to $88M — it correctly saw that Tyler was growing.
Reality grew faster still, so the model was **directionally right and consistently short.**

That column is as close to an explanation as a foundation model gives. It does not say *why* the
model added $88M. It does say **exactly how much of the forecast is arithmetic and how much is the
model's judgement**, which is the part a reviewer has to decide whether to accept — and it is
checkable without re-running anything.

And the inputs are traceable: `2024-03-31 · 10-Q · accession 0000860731-24-000025 · filed
2024-04-24`. A number in a memo can be walked back to a document the SEC received.

### Revised verdict on forecasting

**Keep it. Keep it as an exhibit. And ship it with the real-data result attached, not the synthetic
one.**

The synthetic run stays because it demonstrates the pipeline end to end on a document the tool can
actually read. But it is labelled as a demonstration, and **the real-company test is the evidence** —
including the part where a straight line wins.

A forecast in this memo should carry three things or it does not go in: the naive baseline beside it,
the model's delta in dollars, and the sentence that on a steadily growing business the baseline is
probably enough.


---

## Experiment 6 — How much history does forecasting actually need?

**The experiment that decides whether any of this applies to a CIM.** A memorandum gives four annual
figures. A public filer gives twenty-five quarters. Somewhere between them the exercise stops being
arithmetic in a costume. Nobody had told us where, so: hand every method progressively less real
history and watch the error curve.

Mean MASE, one year ahead, six real companies. **Below 1.0 is skill. Above 1.0 is worse than
repeating last year.**

| History | last_value | seasonal_naive | linear_fit | drift | timesfm_3 |
|---|---|---|---|---|---|
| **4 quarters** | 2.519 | 3.416 | **0.934** | 1.039 | **1.472** |
| 6 quarters | 0.850 | 1.139 | **0.377** | 0.472 | 0.526 |
| 8 quarters | 0.708 | 0.976 | 0.335 | 0.352 | **0.305** |
| 12 quarters | 0.747 | 1.048 | 0.475 | **0.337** | 0.389 |
| 16 quarters | 0.721 | 0.997 | 0.495 | **0.346** | 0.351 |
| 20 quarters | 0.834 | 1.149 | 0.493 | 0.413 | **0.358** |
| 24 quarters | 0.832 | 1.194 | 0.649 | 0.435 | **0.349** |

**Read the top row. At four data points every method is broken**, and the foundation model is the
second worst thing you could do — 1.472, meaningfully worse than doing nothing clever. Only a
straight line stays under 1.0, and barely.

**That is the CIM case, measured on real data, and it settles the question: a four-point annual
series cannot be forecast by anything.** Not by a 330M foundation model, not by arithmetic. This is
not a limitation of the tools.

**The cliff is between four and six quarters.** Error drops by more than half. Six real observations
is apparently where a trend becomes visible at all.

**Eight quarters is where the foundation model starts winning** (0.305 against 0.335 for a straight
line), and after that nothing much improves. TimesFM sits flat around 0.35 from 8 quarters to 24.

**And a genuine surprise: more history makes the straight line worse.** `linear_fit` goes from 0.335
at 8 quarters to 0.649 at 24 — because a line fitted through six years of accelerating growth
underfits the recent trend. `drift` avoids this by anchoring to the last value. **More data is not
monotonically better if your method cannot forget.**

---

## Experiment 7 — Do covariates help? I had undersold the model

The first real-data test ran TimesFM-3 **univariate**: one series, no side information. That was
testing the weak configuration, because multivariate forecasting with covariates is the entire
reason version 3 exists. So it was run properly, handing each company **the other five as a sector
cohort** — the closest a numeric model gets to "what is happening in this industry."

| Mode | 1 year (MASE) | 2 years (MASE) |
|---|---|---|
| univariate | **0.358** | 0.530 |
| past_only (cohort history) | 0.412 | 0.587 |
| past_future (cohort history + its actual future) | 0.374 | **0.489** |

**Covariates made it worse at one year, in both modes.** The headline feature did not help.

**Past-only covariates hurt at both horizons.** Handing the model twenty-four quarters of a
correlated series added noise, not signal — which makes sense: twenty-four points is nowhere near
enough for a model to learn a cross-series relationship it can trust.

**Knowing the cohort's future helped only at two years, by 8%.** And that mode is optimistic: it
assumes you know where the sector goes, which you would only have from a published index or a
contracted schedule.

**The design lesson is sharper than the numbers.** The value of a covariate is almost entirely in
**knowing something about the future** — contracted renewals, signed backlog, an announced price
change. Correlated history is close to worthless. So if forecasting ever enters a deal context, the
covariate to fight for is the contracted revenue schedule, not a market index.

---

## Experiment 8 — Is TimesFM even the right model?

It was chosen because it was the model named, not because it won anything. Benchmark reporting puts
Chronos-2 and Moirai 2.0 ahead of it. Same six companies, same split, same metric.

### One year

| Method | Mean MASE | Mean MAPE | Seconds |
|---|---|---|---|
| **chronos_2** | **0.402** | **4.30%** | **0.95** |
| timesfm_3 | 0.502 | 5.35% | 5.54 |
| drift | 0.507 | 5.77% | 0.00 |
| chronos_bolt_base | 0.551 | 6.14% | 10.33 |
| linear_fit | 0.823 | 8.77% | 0.00 |

**Chronos-2 beats TimesFM by 20% and runs six times faster.** The leaderboard was right and the
model we spent the most time on is not the best one.

### Two years

| Method | Mean MASE | Mean MAPE |
|---|---|---|
| **drift** | **0.718** | **7.33%** |
| timesfm_3 | 0.846 | 8.35% |
| chronos_2 | 1.094 | 11.25% |
| linear_fit | 1.287 | 12.64% |
| chronos_bolt_base | 1.526 | 15.79% |

**At two years arithmetic still wins, and Chronos-2 collapses** from best to third — worse than
TimesFM. Chronos-Bolt is poor at both horizons.

**So model choice matters at short horizon and is irrelevant at long horizon**, where nothing has
yet beaten "last value plus average change."

---

## What the forecasting thread actually established

Six experiments in, the picture is consistent and it is not the one we started with.

1. **Four annual data points cannot be forecast.** Measured, on real companies. This closes the
   question of whether forecasting belongs in a CIM screen: it does not.
2. **Eight quarters is the threshold** where a foundation model starts beating arithmetic.
3. **At one year, pick Chronos-2**, not TimesFM. Twenty percent better and six times faster.
4. **At two years, pick arithmetic.** Nothing beats drift.
5. **Covariates are worth having only if they carry future knowledge.** Correlated history hurts.
6. **A foundation model is insurance against the trend breaking**, not a better ruler. On a business
   doing what it has always done, a straight line is the honest answer.

**And the synthetic result that started this — 46% better than baseline — was a measurement of a
choice I made**, not a property of the model. Every number above comes from companies that filed
with the SEC and cannot be edited to flatter anybody.

---

# The prediction system — experiments 9 to 12

A CIM is a snapshot and there is no future history for the target. But a serial acquirer holds
something better than a forecast: **the futures of every other company it bought.** These four
experiments build that idea into a system and then try to break it.

**One constraint over all of it, and it is not decoration: the people who read this output
reconcile to the penny for a living.** Anything reaching them carries a source, a date, or a list of
records the number recomputes from. Nothing reaches them as an assertion.

---

## Experiment 9 — The base rate

**The idea.** Do not predict the target. Report what comparable past acquisitions went on to do.
That is not a forecast, it is a prior, and the difference is the whole thing: a forecast invites
belief, a base rate invites argument.

**What was built.** A 120-deal history, deterministic and seeded, each row carrying the profile at
acquisition and the revenue CAGR three years later, plus what was underwritten at the time.
`signals/baserate.py` matches a target to comparable deals and summarises the outcomes.

**Cohort matching widens one rung at a time and reports which rung it stopped on:** vertical + size
+ retention, then size + retention, then retention alone, then size alone, then the whole book.
**Below eight comparables it refuses** — a median of three is noise wearing a number's clothes, and
"we have never bought anything like this" is itself a finding worth putting in front of a committee.

### Result

| Target | Cohort | Matched on | Median outcome CAGR | Shrank |
|---|---|---|---|---|
| T01 Meridian | 29 | retention band | 6.3% | 0% |
| T02 Halyard | 29 | retention band | 6.3% | 0% |
| T03 Ridgeline | 16 | size + retention | 4.21% | 0% |
| T04 Kestrel | 21 | size + retention | 5.34% | 4.8% |
| **T05 Ashgrove** | **16** | size + retention | **2.1%** | **12.5%** |

Ashgrove's 81% retention puts it in the weakest cohort in the book — median 2.1% growth, p10 of
minus 0.2%, and one in eight shrank outright. **The rubric already flagged its retention. The base
rate says what that has historically meant.**

### The calibration finding

Across the whole book, **underwriting ran +3.72 points optimistic at the median and was optimistic
on 98% of deals.** On Ashgrove's cohort specifically: +3.95 points, optimistic on 100%.

That is the answer to "were our underwriting DCFs correct, or are we underwriting too
aggressively?" — and it needs no model at all. It is arithmetic over outcomes, and it is the one
prediction asset an acquirer owns that nobody outside can compute.

### Auditability

The memo prints the cohort. Not a count — **the deal ids**:

> *Cohort, for audit — every figure above recomputes from these 16 deals: D005, D011, D013, D022,
> D023, D026, D035, D042, D057, D058, D059, D078, D093, D102, D103, D109.*

A reviewer can pull those sixteen rows and redo the median by hand. That is the standard.

**Honest limit: this dealbook is fabricated.** A real acquirer's is the genuinely proprietary
version. What is demonstrated here is the machinery and the shape of the reasoning, not a fact about
any real portfolio.

---

## Experiment 10 — Outward research

**The correction that produced it.** The first research layer read one more line item inside the
CIM. That is a better reader, not a researcher. And the persona red-team failed because four critics
were pointed at the same PDF — they can only surface what is already in it.

**Five lenses, all facing outward**, in `skills/target-research/` with a `target-researcher` agent:

1. **Operators** — founder and management tenure, prior exits, recent departures. Whether the
   business survives its founder leaving, and whether anyone has already started leaving.
2. **Ownership and board** — who owns it, prior institutional money and its vintage. *Why is this
   for sale now*, which the CIM will never answer honestly.
3. **Workforce** — headcount trend, engineering against sales mix, hiring signals. Whether the
   organisation is investing or harvesting.
4. **Customers as organisations** — the sharpest lens, and the one retention cannot reach.
5. **Market and disruptors** — entrants, consolidation, AI exposure, the region and end industry.

**Guardrails that are enforced, not promised.** The researcher holds `WebSearch` and `WebFetch` and
nothing else — **no `Read`, so the confidential document cannot reach a web query.** A check fails
the build if that changes, and a further check now fails if any agent ships without an allowlist
spec at all.

**Two rules that matter more than the lenses.** Absence is never evidence: "no distress found" and
"could not research" are different outputs and may not be collapsed. And research covers the
professional record only — filings, public statements, company history. Nothing a person would be
startled to find in a deal memo.

---

## Experiment 11 — The scenario layer

Every layer beneath this produces facts. This is the only one that produces a view, and **it
deliberately does not produce a number.**

The output is the assumptions the base rate rests on for this target, each carrying **what it rests
on** and **what would falsify it**. An assumption nobody can disprove is a sentiment.

From the Ashgrove memo, unedited:

| Assumption | Rests on | Falsified by |
|---|---|---|
| The two distressed customers represent an isolated risk, not a systemic one | **C** | Evidence from the remaining 72% of ARR — the customers not researched — showing similar distress |
| Revenue CAGR will be comparable to the cohort median of 2.1% because retention is above the historical floor | **A** | GRR dropping below 85% next year, if the current 81% is a trend rather than an anomaly |

**Note what the first one did.** The customer signal reported 28% coverage, and the reasoner turned
the *uncoverage* into the falsification surface. The coverage discipline propagated three layers up
without being told to.

Input blocks are labelled A through D — document, base rate, customer health, external research — so
every assumption traces to the thing that produced it.

---

## Experiment 12 — Does it actually reason, or does it just write?

**The eval that decides whether the scenario layer is worth anything, and almost nobody runs it.**
Change the evidence. See whether the conclusion moves.

Four conditions per target, each flipping one block: baseline, customer health removed, distress
flipped to healthy, base rate replaced with a poor cohort. Similarity is Jaccard over content words
against the baseline — **lower means the conclusion moved when the evidence moved.**

| Condition | Mean similarity |
|---|---|
| Customer health removed | **0.218** |
| Base rate replaced with a weak cohort | **0.252** |
| Customer distress flipped to healthy | 0.411 |

**The conclusions move substantially when the evidence moves.** Roughly four fifths of the content
changes.

**And the outlier is the most reassuring number in the table.** T01 Meridian scored **1.000** on the
healthy condition — a byte-identical output. Meridian has no distressed customers, so flipping them
to healthy changes nothing, and the pipeline correctly produced the same answer for the same input.
Excluding that no-op, the healthy condition averages **0.263**, in line with the others.

**Identical inputs give identical outputs; different inputs give different outputs.** That is the
behaviour you want and it is not what a prose generator would produce.

**What this does not establish.** It shows the reasoner responds to evidence. It says nothing about
whether the assumptions are *correct*, and no threshold is asserted for what similarity ought to be,
because nobody has established one and inventing a pass mark for the occasion would be worse than
reporting the number.

---

## What the prediction system is, in one paragraph

**Not a forecaster.** A base rate from past deals that only the acquirer can compute, the document
read with citations, outward research with dates and coverage, and a reasoning layer that emits
falsifiable assumptions rather than a number. Each layer is independently useful and fails loudly on
its own terms. **None of them touches the score** — `run_checks.py` fails the build if the scoring
path can so much as import a signal.

And the answer to "we have no future history for this target" is that **you have every other
company's future**, which is the one thing the seller's document could never contain.

---

## Experiment 13 — Running the research layer for real, and what it broke

Experiment 10 built the research layer and never ran it. That is a fair criticism of it: a skill
file and an agent definition are not evidence of anything. It could not be run on the synthetic
corpus, because those companies do not exist — there is no founder to look up and no customer to
check — so it was run against a real one.

**AppFolio**, chosen because the whole stack can run on it: filings already pulled for the
forecasting work, a real vertical, a real customer base, a real end market. **A public company is an
easier research target than a private one**, which is worth stating rather than glossing.

### First, the skill was rebuilt deeper

The original five lenses were the ones handed to me. An M&A team researches considerably more, and
the screen itself should decide what matters. So the skill now opens by **composing a plan for the
specific target** rather than running a checklist, and uses the rules that fired as targeting:

| What the screen found | What that makes urgent |
|---|---|
| Concentration breach | **Change-of-control and assignment clauses** — a concentrated base that can walk *because the company changed hands* is a different asset |
| Recurring below floor | What the non-recurring revenue actually **is** — services, perpetual, re-occurring hardware all price differently |
| Retention below floor | Whether it is **cyclical or structural** |
| Legacy stack | Security and breach history, **the talent market for that stack in that geography** |
| Loss-making | Who funds the losses, and the vintage of the money |

Standing lenses became operators, ownership-and-why-now, customers as organisations, market and
disruptors, and **end-market health** — their customers' industry, not just their customers.
Conditional lenses added contracts, security and certification, **vendor and platform dependency**
(concentration runs both ways and only one direction is in the CIM), channel dependency, pricing
power, competitive position from outside, talent market, workforce trajectory, litigation, and
adjacent transactions.

**And it is explicitly discretionary.** The lists are what is usually worth knowing; the agent is
told to follow lines of enquiry nobody could have written down in advance, and to say why. What is
*not* discretionary is the sourcing, the coverage reporting, and the refusal to treat absence as
evidence.

### What the research actually found

Real searches, committed with sources and dates:

- **Board chair and a long-serving director both retired 2026-06-29, and the CEO took the chair.**
  Board independence reduced at the moment two long-tenured directors left. *(primary)*
- **National asking rent growth decelerated to 0.1% year over year, weakest since Q4 2010.**
  Customers price software against rent roll. *(practitioner, high materiality)*
- **Property insurance up 15–30% annually in Florida, Texas and Louisiana.** The customer base is in
  a margin squeeze, which is where software budgets get cut first. *(practitioner, high)*
- **PMS-native AI shipped across all four incumbents in 2024–25 and is now treated as a complement
  rather than a replacement.** AI parity is table stakes, not a moat. *(practitioner)*
- **Category-leadership claims for the product come from the vendor's own blog.** *(vendor, marked
  so it cannot be mistaken for third-party validation)*

That last one is the source-tier discipline earning its keep in a real pass rather than in a rule.

### Does research change the conclusion, or is it decoration?

Ran the scenario layer twice on the same target, once with the research block and once without.

**Similarity between the two: 0.228.** Roughly three quarters of the reasoning changed, and two
assumptions exist only because of block D — including one that took the vendor-tier flag and turned
it into something to challenge.

**Outward research is not decoration. It moves the argument.**

### And it broke the base rate, which is the most useful thing that happened

AppFolio was matched to a cohort and the base rate reported *"matched on size band + retention band,
n=10"* — cleanly, confidently, and wrongly.

**The dealbook spans $2.0M to $27.9M of ARR. AppFolio is roughly $900M — thirty-two times larger
than anything in the book.** The top size band is open-ended ("over $20M"), so a company of any size
above that threshold fell into the same bucket as a $21M deal, and a median drawn from those deals
was reported as if it described it.

**That is exactly the failure the base rate was built to prevent**, and it survived until the layer
was pointed at something real. A synthetic corpus of five targets all inside the mandate band could
never have surfaced it.

Fixed with an out-of-range guard that refuses and names the range:

> *base rate unavailable — this target is outside the range of anything in the book. It is $900.0M
> ARR against a history spanning $2.0M to $27.9M. A cohort median drawn from deals that size would
> not describe it.*

Verified at the boundaries: $4.3M and $25M still match, $900M and $0.5M both refuse.

### What this establishes, and what it does not

**Establishes:** the research layer runs, produces sourced dated findings against a real company,
correctly marks vendor self-promotion, and materially changes the downstream reasoning.

**Does not establish:** that the findings are complete, or that a private target would yield
anything like this. A public filer publishes board changes; a founder-owned business does not. The
coverage record says which lenses were skipped and why — ownership was not run because a public
company has no sale process to explain, contracts were not run because no concentration flag
justified it, and **no named customer was researched at all, because a public filer does not
disclose an anchor roster.** On a real CIM that lens would be the most valuable one and here it was
unavailable.
