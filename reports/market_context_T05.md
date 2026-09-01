# Market context — T05 Ashgrove

**Re-run 2026-09-01 against the source layer.** The first version of this file was three searches
against an open index with source tiers assigned afterwards. It is superseded by this pass, which
searched the whitelisted publishers in [`sources.md`](../plugins/deal-ready/skills/market-context/references/sources.md)
by name and went to their own pages.

**The researcher never saw the CIM.** It received metric names, values, and the vertical.

---

## Phase 0 — Source layer

Whitelist consulted first. Coverage map checked before promising a band. Both standing corrections
applied. **The previous pass's headline claim did not survive contact with a real source layer and
has been replaced** — see the retention section.

## Phase 1 — Scope

**Vertical:** grain handling and agricultural commodity management software.
**Size:** $4.3M ARR — the band that matters most, see below.
**Window:** last 12 months.

| Metric | Value | Band needed | Why it decides |
|---|---|---|---|
| `grr_pct` | 81.0 | retention floor | fails the 85% rubric floor; cost the most weight |
| `nrr_pct` | 86.0 | expansion norm | below the 100% target |
| `arr_usd` | 4,300,000 | size-to-multiple | sits below the smallest published band |
| `yoy_growth_pct` | 2.0 | growth norm | with NRR under 100, new logos carry everything |

## Phase 2 — Four typed passes

### Benchmark — retention

**Two whitelisted publishers, carried separately.**

| Source | Sample | Median GRR | Median NRR |
|---|---|---|---|
| Benchmarkit 2026 | private B2B SaaS + AI-native | **84%** (75th pct 91%) | — |
| SaaS Capital | private B2B >$1M ARR, N=1,000+ | **91%** for bootstrapped $3–20M ARR | **103%** same band |

**Ashgrove sits below both, and below the one that fits it best.** At $4.3M ARR it falls inside
SaaS Capital's bootstrapped $3–20M band, where the median GRR is 91%. It reads 81% — ten points
under its own size cohort, and three under the broad market median.

**Benchmarkit also finds vertical SaaS significantly outperforms horizontal SaaS on GRR.** A
vertical business sitting below the *all-SaaS* median is below a bar it should be clearing.

NRR 86% against 103% for its band, and below the ~97% bottom quartile Benchmarkit reports for the
$25–50k ACV segment.

### Benchmark — multiples

**The size correction dominates everything else here.**

| Band | Median EV/Revenue | Source |
|---|---|---|
| Aventis overall median | 4.5x — **at a median deal size of $80M** | 543 disclosed deals, 2015–2026 |
| $50–100M | ~6.1x | same |
| $20–50M | ~3.2x | same |
| SEG market level, 2Q26 | 4.0x EV/TTM revenue | method not published |

**At $4.3M ARR, Ashgrove is below the smallest band anyone publishes.** The nearest guidance is
founder-led sub-$3M ARR clearing around 2.5x–4.0x. **Quoting the 4.5x median at this target would
overstate it by a wide margin** — that median describes an $80M-EV population.

### Comparable

**Gap.** No software transaction comparable was found at this size in this vertical. The 2026
agtech deals that are public are hardware and biologicals, not commodity-management software.

Structural reason, not a search failure: financial terms are disclosed in **under 10–15%** of
sub-$50M deals, and disclosed deals skew to premium assets — the disclosed population has a median
EV of $80M.

### Trend

SEG 2Q26: the median compressed 4.2x → 4.0x, but dispersion is wide — *"scarce assets with
differentiated data, security, AI capabilities, or mission-critical workflows continue to command
premium valuations."* Benchmarkit's GRR median fell four points year over year (88% → 84%), so the
whole retention distribution moved down, not just this target.

### Critical — what makes this worse than the band suggests

1. **Its own size cohort retains better.** 81% against 91% for bootstrapped $3–20M ARR is the
   sharpest comparison available, and it is unflattering.
2. **Vertical should outperform horizontal, and this does not.**
3. **NRR 86% with 2% growth** means the installed base is contracting and new logos carry the
   number. GRR and NRR must be read together; separately each looks merely weak.
4. **Below the smallest published multiple band**, where the founder-led SDE-hybrid basis applies
   rather than an ARR multiple.

## Phase 3 — Coverage gate

- [x] Every deciding metric has a band or a named gap
- [x] No band rests on a single vendor-tier source — both retention sources are practitioner tier
- [x] M&A and VC multiples labelled separately; nothing here is a VC figure
- [x] Every claim dated inside the window, except ChartMogul (2023, excluded)
- [x] The critical pass produced four risks
- [x] **Contradiction carried:** Benchmarkit 84% and SaaS Capital 91% are not averaged; they are
      different populations and both are reported
- [x] No blacklisted domain cited — enforced by `run_checks.py`

## Phase 4 — Where the numbers sit

**Gross retention 81%.** Below the broad market median (84%), ten points below its own size cohort
(91%), and below a bar that vertical software is supposed to clear more easily than horizontal.
The rubric says "missed an 85% floor by four points." **The market says it retains worse than the
companies it most resembles.**

**Net retention 86%.** Seventeen points below its cohort median.

**ARR $4.3M.** Below the smallest band with published multiples.

**The survey caveat, applied honestly and in the target's favour:** both retention sources are
opt-in surveys, which run 5–10 points high because outperformers volunteer. If the true population
medians are lower, Ashgrove's gap to median narrows. **It does not close** — a ten-point deficit to
its own cohort survives a five-point correction — but the shortfall is smaller than the headline
numbers suggest, and anyone quoting those medians as fact is overstating the case.

**What would have to be true for this to deserve better:** that the retention is cycle-driven
rather than structural, that the grading-rules workflow is genuinely locked in, and that sub-scale
ARR is a starting point rather than a ceiling. None is answerable from the document. All three are
management-call questions.

## Limitations

- **No agriculture-specific retention band or multiple range exists.** Confirmed against the
  coverage map, not merely unfound. Every retention figure here is a horizontal proxy.
- **No comparable transaction at this size in this vertical.**
- **Both retention sources are opt-in surveys** and both were reached through citing pages rather
  than the publishers' own gated reports. Attributed, secondhand.
- **SEG's multiple has no published methodology.** Used for direction, not as a valuation anchor.
- **ChartMogul telemetry, which would correct the survey bias, is stale** — the accessible edition
  is 2023 and measures customer retention rather than GRR.
- **Concentration norms have no market benchmark at all.** The rubric's 15% and 35% caps are the
  acquirer's policy.
- **Context is not a verdict.** Nothing here changed a score or a tier.
