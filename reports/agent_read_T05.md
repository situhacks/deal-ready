# Agent-path read — T05 Ashgrove, chart-carried metrics

**What this is:** a frontier model reading the same pages the local pipeline reads, following
`plugins/deal-ready/skills/cim-read/SKILL.md`. It is the first data point for the
two-substrate comparison.

**What this is not:** a check. `run_checks.py` cannot reproduce it — it needs a model with
vision, which is exactly the dependency the offline suite exists to avoid. **Nothing in this
file is a verified number.** It is a recorded observation with its provenance attached.

| | |
|---|---|
| Date | 2026-08-31 |
| Reader | frontier model with vision, reading page renders at 120 dpi |
| Pages | `data/T05_Ashgrove_CIM.pdf` p6, p7 |
| Instructions | `cim-read` skill, unmodified |
| Reproducible offline | **No** |

## Result

| Metric | Read | Type | Ground truth | Correct |
|---|---|---|---|---|
| `grr_pct` | 81.0 | `axis` | 81.0 | yes |
| `nrr_pct` | 86.0 | `axis` | 86.0 | yes |
| `top1_customer_pct` | 11.0 | `label` | 11.0 | yes |
| `top5_customer_pct` | 28.0 | `label` | 28.0 | yes |

**4 of 4 correct. Read types classified correctly in all four cases.**

## What the read types turned on

**p7 — retention chart, both series `axis`.** The chart has gridlines at 2.5-point intervals
and no data labels. Gross retention's FY25 endpoint sits just above the 80.0 line, roughly a
fifth of the way to 82.5; net retention's sits between 85.0 and 87.5, nearer the lower. Both are
interpolations against gridlines, so both are `axis` and both carry low confidence — correctly,
because nothing printed on that page states either number.

**p6 — concentration chart, both `label`.** The bars carry printed values (`11%`, `17%`, `72%`)
and a callout box reads "Top 5 customers: 28% of ARR". These are printed, so they are `label`
reads at high confidence. **The 28% is never computed** — 11 + 17 is the same number, but the
document states it, and stating beats deriving.

**One definition note, recorded per the skill:** p7 says gross retention excludes expansion and
net retention includes expansion, upsell and contraction. That is the conventional definition,
so it is not a trap here — but it is the kind of sentence that is a trap when it differs, and it
belongs in the record either way.

## Why this matters for the comparison

The local pipeline reaches these same four values by a different route: a 0.9B parser reads the
printed labels on p6, and for p7 a chart specialist supplies series labels and tick glyphs while
code measures the pixel geometry against them. The frontier reader gets there by looking.

**Both arrive at 81.0. That is the point of running both.** The interesting column in the
comparison table is not accuracy on this page — it is cost, latency, and what each does when it
is wrong. This file records one page-pair from one target and settles nothing about the general
case.

## Honest limits of this test

- **One target, two pages, four metrics.** Not a corpus result.
- **Not a cold start.** The reader had the `cim-read` instructions in context. It does not test
  whether an agent encountering the plugin fresh routes to the right skill on its own.
- **Synthetic corpus.** These charts were rendered by `generate.py` from known values, so they
  are cleaner than a real CIM scan.
- **No cost or latency captured.** Those are the columns that would make this a comparison
  rather than a spot check.
