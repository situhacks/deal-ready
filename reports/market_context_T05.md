# Market context — T05 Ashgrove

**Produced by the `market-context` skill, 2026-09-01.** A worked example of the four-phase
research pass, run on the deciding metrics from the T05 screen.

**The researcher never saw the CIM.** It received metric names, values, and the vertical. Nothing
below was read out of the document.

> ## ⚠ Corrected 2026-09-01 — read this before the analysis
>
> **This pass predates `references/sources.md` and does not meet its standard.** It was three web
> searches against an open index with source tiers assigned afterwards, which is the failure the
> source map now exists to prevent. Kept because two findings survive and one does not.
>
> **Survives — the agriculture gap.** The coverage map confirms it independently: no published
> retention band and no defensible multiple range for agriculture and commodity-handling software.
> Reported here as a gap, correctly.
>
> **Survives — the ARR-to-multiple point**, now better sourced. Aventis Advisors (543 disclosed
> deals, median $80M EV) finds the $50–100M band clears at roughly twice the $20–50M band, and
> founder-led sub-$3M ARR nearer 2.5x–4.0x. At $4.3M ARR the target is well below the inflection.
>
> **Does not survive — "81% is below the 84% median for a class that should beat it."** That median
> comes from an **opt-in survey**, and survey retention medians run 5–10 points high because
> outperformers volunteer and distressed companies do not respond or no longer exist. Billing
> telemetry puts lower-quartile monthly churn at 5.8–9.1%, far below any survey median. So 81% is
> below a *selected* median, which is a much weaker statement than the one made below. The rubric
> breach at the 85% floor stands on its own; the market framing does not add to it as claimed.
>
> **Off-whitelist source.** The retention band below came from a domain that is not on the
> whitelist. It is not blacklisted, but it is not a source this tool should have leaned on.

---

## Phase 1 — Scope

**Vertical:** grain handling and agricultural commodity management software. Narrower than "agtech"
(which spans drones, biologicals and equipment) and narrower than "vertical SaaS".

**As-of window:** last 12 months.

| Metric | Value | Band needed | Why it decides |
|---|---|---|---|
| `grr_pct` | 81.0 | retention floor for this vertical | fails the 85% rubric floor; the criterion that cost the most weight |
| `nrr_pct` | 86.0 | expansion norm | below the 100% target; read together with GRR it says the base is shrinking |
| `yoy_growth_pct` | 2.0 | growth norm at this ARR | 2% growth with NRR below 100 means new logos are carrying everything |
| `arr_usd` | 4,300,000 | size-to-multiple relationship | sits at the small end, where multiples compress |

Concentration (11% / 28%) clears its caps and was not researched.

## Phase 2 — Four typed passes

### Benchmark

**No agriculture-specific retention band was found.** Stating that is the finding; the nearest
defensible proxy is the B2B SaaS distribution, used explicitly as a proxy and not as this
vertical's band.

| Measure | Bottom quartile | Median | Top quartile |
|---|---|---|---|
| GRR | 76% | **84%** | 91% |
| NRR | <95% | **108%** | 125%+ |

> "The median B2B SaaS company has a gross revenue retention rate of 84% — below the 85–90% mark
> that signals strong retention, and down 4 points from 88% the year before."
> — [Growth Spree, B2B SaaS NRR and GRR Benchmarks 2026](https://www.growthspreeofficial.com/blogs/b2b-saas-nrr-grr-net-gross-revenue-retention-benchmarks-2026-by-acv-stage-vertical) · practitioner tier · 2026

**Vertical software should beat the horizontal median, not match it:** switching costs are higher
and workflow integration runs deeper, so "if your NRR matches the horizontal median, you may be
underperforming your actual peer set" (same source).

### Comparable

Agriculture software is a thin, fragmented public comp set — 63 SaaS companies in the category
with combined revenue of ~$335.6M ([Latka](https://getlatka.com/companies/industries/i-agriculture-software),
vendor tier, 2026-06), i.e. an average well under $10M. Named 2026 transactions are **hardware and
biologicals, not commodity-management software**: SKK Holdings / Rantizo drone assets ($258.8M),
TransFRESH / Hazel Technologies
([iGrow News](https://igrownews.com/agtech-consolidation-ma-wave-2026/), 2026).

**No clean software comparable was found at this size in this vertical.** Recorded as a gap.

Broader private SaaS context: private ARR medians ~4–5x, and **deal size is the strongest single
predictor of multiple** — the median roughly doubles between the $20–50M and $50–100M brackets
([L40](https://www.l40.com/insights/saas-multiples), practitioner tier, 2026). At $4.3M ARR,
Ashgrove sits well below that inflection.

### Trend

AgTech funding **peaked in 2022 and has contracted for three years**, and the 2026 M&A wave is the
downstream consequence — ten acquisitions in May 2026, every one strategic, established operators
buying stacks rather than building them
([iGrow News](https://igrownews.com/agtech-consolidation-ma-wave-2026/), 2026). Exits are
consolidation, not IPOs.

### Critical — what would make this worse than the band suggests

1. **The ag cycle is in a trough.** Farmer economics are pressured by low commodity prices
   ([AgTech Navigator](https://www.agtechnavigator.com/Article/2026/01/28/why-agtech-start-ups-failed-last-year-and-a-playbook-for-2026/), 2026-01).
   **This cuts both ways and the direction matters enormously:** 81% GRR during a trough may be
   cyclical and recover, or may be structural and get worse when the cycle turns. Nothing in the
   metrics distinguishes those.
2. **Concentration risk is understated by the percentages.** Reliance on a few large farms or
   enterprise accounts "amplifies churn impact and weakens negotiating leverage" (same source) —
   and Ashgrove's disclosed top-five is 28%, inside the cap.
3. **Differentiation decays without proprietary data or workflow lock-in**, because generic AI and
   off-the-shelf tooling lower the barrier to entry (same source). This is the AI-exposure
   question, and it is a pricing input.
4. **Structural drag on the vertical:** slow-moving, fragmented, price-sensitive buyers, expensive
   customer acquisition, and long sales cycles.

## Phase 3 — Coverage gate

- [x] Every deciding metric has a band **or a named gap** — GRR/NRR use a stated proxy; the
      vertical-specific band is a gap; no software comparable found at this size
- [x] No band rests on a single vendor-tier source
- [x] M&A and VC multiples labelled separately
- [x] Every claim dated inside the window
- [x] The critical pass produced four real risks
- [ ] **Contradiction carried, not averaged:** the ag-cycle finding cuts both ways and is left as
      a question rather than resolved into a direction

## Phase 4 — Where the numbers actually sit

**Gross retention, 81%.** Below the rubric's 85% floor, and also below the **84% B2B median** —
sitting between the bottom quartile (76%) and the median. For a *vertical* business, which should
beat the horizontal median on switching costs, that is worse than the rubric alone shows. The
rubric says "misses a floor by four points". The market says "underperforms the class it should
be outperforming".

**Net retention, 86%.** Below the **bottom quartile (<95%)** and 22 points under the 108% median.
Read with 2% growth, the installed base is contracting and new logos are carrying the number.

**ARR $4.3M.** Below the size bracket where multiples inflect.

**What would have to be true for this to deserve the top of its band:** that the retention is
cycle-driven rather than structural, that the grading-rules workflow is genuinely locked in rather
than replicable with off-the-shelf tooling, and that the sub-scale ARR is a starting point rather
than a ceiling. **None of those is answerable from the document.** All three are management-call
questions.

## Limitations

- **No agriculture-specific retention band exists in accessible sources.** The B2B SaaS
  distribution is a proxy, explicitly labelled, and it may be materially wrong for this vertical.
- **No software comparable at this size in this vertical was found.** The named 2026 deals are
  hardware and biologicals.
- The Latka company count is vendor tier with no stated methodology.
- Retention benchmarks come from a practitioner source, not a statistical agency.
- **Context is not a verdict.** Nothing here changes a score or a tier. It changes what the
  numbers mean, and what to ask about them.
