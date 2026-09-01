# Benchmark figures — whitelisted publishers only

**Rebuilt 2026-09-01 from the publishers named in [`sources.md`](sources.md).** The previous
version of this file carried per-vertical multiples traceable to a domain that is now blacklisted;
those are gone rather than corrected, because there was nothing under them.

**Read [`sources.md`](sources.md) first.** Its two standing corrections apply to everything here:
survey retention medians run 5–10 points high, and deal size predicts multiple more strongly than
vertical does.

Every figure below carries its publisher, date, and sample. **A figure without those three does not
belong in this file.**

---

## Valuation multiples

### Aventis Advisors — the best-sourced multiples available

Published **2026-04-01**. Methodology, verbatim: *"In our analysis of Private SaaS M&A
transactions, we looked at 1,000+ software deals since 2015 and marked the ones where the target
company is considered to be operating a SaaS business model."*

**543** transactions with disclosed revenue multiples; **232** with disclosed EBITDA multiples;
2015–2026.

| | Median | Q1 | Q3 | Median deal size |
|---|---|---|---|---|
| EV/Revenue | **4.5x** | 2.4x | 8.1x | $80M |
| EV/EBITDA | **23.0x** | 12.8x | 47.1x | $181M |

**By deal size — the single most important row in this file:**

| Band | Median EV/Revenue |
|---|---|
| $50–100M | **~6.1x** |
| $20–50M | **~3.2x** |

The $50–100M band clears at nearly **double** the $20–50M band. **The medians above describe an
$80M-EV population.** Quoting 4.5x at a $4M ARR target is a category error, not a rounding one.

### Software Equity Group — quarterly market level

**2Q26.** Median private SaaS M&A multiple **4.0x EV/TTM revenue**, down from 4.2x; mean eased
6.3x → 6.2x. **698** transactions in the quarter (up 9.6% from 637 in 2Q25); **2,784** TTM.

**Caveat, and it is not small:** the published brief states deal counts and its 106-company public
index, but **does not state how private deal multiples are calculated or sourced.** Use SEG for
market direction and volume. Use Aventis when you need a multiple with a method behind it.

SEG's qualitative read is worth carrying: *"scarce assets with differentiated data, security, AI
capabilities, or mission-critical workflows continue to command premium valuations"* — dispersion
is wide even as the median compresses.

---

## Retention

**Two whitelisted publishers disagree. Both are carried. Do not average them.**

### Benchmarkit — 2026 B2B SaaS & AI-Native Metrics

| | 2026 | Prior year |
|---|---|---|
| Median GRR | **84%** | 88% |
| 75th percentile GRR | **91%** | 95% |

**A four-point drop in the median in one year.** Two segment findings matter for vertical software:

- **Vertical SaaS significantly outperforms horizontal SaaS on GRR.** A vertical business at the
  horizontal median is underperforming its own peer set.
- Seat-based pricing shows the lowest median GRR of any pricing model.

*Reached via thesaascfo.com (2026-06-30), not Benchmarkit's own page — the figure is attributed,
the URL is secondhand.*

### SaaS Capital — annual private B2B survey

Sample: private B2B SaaS above $1M ARR; **N=1,000+**; median growth across the sample 24%.
NRR defined verbatim as *"(Monthly Recurring Revenue in December of 2024 only from customers who
were customers in December 2023) ÷ (Total MRR in December 2023)"* (2025-09-18 edition).

| Segment | GRR | NRR |
|---|---|---|
| Bootstrapped, $3–20M ARR | **91%** | **103%** |
| ACV $25–50k | — | 102% median, 111% top quartile, 97% bottom quartile |

Higher NRR correlates with higher ACV throughout.

*The bootstrapped $3–20M row comes from a search summary of SaaS Capital's 2026 figures, not from
a page directly opened. Flagged rather than dropped, because it is the closest published band to a
lower-middle-market target.*

### Why the two disagree, and how to use it

**Different populations, not a data error.** SaaS Capital surveys bootstrapped private B2B above
$1M ARR; Benchmarkit's 2026 sample includes AI-native companies and a broader spread. For a target
in the $1–20M ARR range, **both are relevant and they bracket the answer**: roughly 84% at the
broad median, roughly 91% for the bootstrapped size band that most resembles it.

**And both are opt-in surveys**, so both run high. See `sources.md`, correction 1.

### ChartMogul — telemetry, but stale

The whitelist admits ChartMogul because billing telemetry captures the distressed and departed
companies surveys miss. **The accessible report is the 2023 edition** (2,100+ businesses, 12 months
ending March 2023), which is outside the recency window and measures **customer retention**, not
gross revenue retention — a different metric.

From it: B2B with ARPA >$1k/month reached 85.8% customer retention at the top quartile and 91.9%
best-in-class; monthly customer churn ran 1–2% for the top 25% and 3–4% at the median.

**Do not quote these as current, and do not quote them as GRR.** The value of the row is the
correction it supports — telemetry medians sit below survey medians — not the numbers themselves.

---

## Coverage by vertical

**Healthcare IT is the only vertical with a defensible published multiple:** 5.3x EV/Revenue and
18.8x EV/EBITDA, Capstone Partners, disclosed transactions 2023 – July 2025.

**Every other vertical is a gap or a horizontal proxy.** The full map is in
[`sources.md`](sources.md). When a vertical is a gap, say so — do not substitute the horizontal
median and let it read as vertical-specific.

---

## Diligence economics

Lower-middle-market software, **$100K–$350K+** per transaction: QoE and accounting $35–90K;
technical and code $20–50K; legal and tax $40–120K; SaaS operations and commercial $15–40K.

Intermediated: 2–4 weeks to LOI, 4–9 months to close, 50–70% conversion, 5–15% auction premium.
Proprietary: 18–36 months to LOI, 1–3% conversion from first touch, then 70–85% LOI-to-close at
10–30% below auction pricing.

---

## What could not be reached

- **SaaS Capital's 2026 edition** and **Benchmarkit's own report** are gated or were not opened
  directly; both figures above are attributed but secondhand.
- **ChartMogul's January 2026 edition** — the public URL served the 2023 report.
- **Bridge Group (N=287)** covers sales quotas and ramp, not screening metrics. Whitelisted but not
  used here.
- **PitchBook** is paid. Financial terms are disclosed in under 10–15% of sub-$50M deals anyway.
- **No source found** for customer-concentration norms in private vertical software. The rubric's
  15% and 35% caps are the acquirer's policy, not a market benchmark, and should never be presented
  as one.
