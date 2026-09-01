# Source whitelist, blacklist, and coverage map

**Consult this before searching, not after.** The failure this file exists to prevent is the one
that produced the first version of `reports/market_context_T05.md`: search an open index, take what
comes back, assign source tiers afterwards. Tiers assigned after the fact are rationalisation.

Derived from a dedicated source-mapping research pass, 2026-09-01, **with corrections applied** —
see "Where the source research contradicted itself" at the bottom. It was not ingested as-is.

---

## How to use this

1. **Search the whitelist publishers by name first.** Go to the publisher's own page, not to
   whoever summarised them.
2. **Never cite a blacklisted domain**, even when it is the only thing that has the number.
3. **Check the coverage map before promising a band.** If the vertical is a Gap, say so — that is a
   correct answer.
4. **Apply the two standing corrections** below to every retention and multiple figure you quote.

## Tier definitions

| Tier | Means |
|---|---|
| **Primary** | Regulatory filing, transacting party's own disclosure, statistical agency, or a named study with published sample frame and method |
| **Practitioner** | Bank, M&A advisor, accounting firm or research house publishing a stated methodology **and** sample size |
| **Vendor** | Anyone selling a product adjacent to the claim, including data platforms marketing their own dataset |
| **Content farm** | No methodology, no sample, no author; numbers that appear nowhere else |

---

## Whitelist

| Publisher | Tier | Covers | Sample | Cadence | Citable |
|---|---|---|---|---|---|
| **Software Equity Group** | Practitioner | Private SaaS M&A multiples, public SaaS index, buyer survey | 2,784 TTM private transactions; 106 public companies; ~200 CEOs and buyers | Quarterly + annual | Yes |
| **Aventis Advisors** | Practitioner | Disclosed global SaaS M&A multiples by deal size | 543 disclosed deals 2015–2026; median $80M EV; IQR 2.4x–8.1x | Periodic | Yes |
| **SaaS Capital** | Practitioner | Private B2B SaaS growth, NRR/GRR, bootstrapped vs VC | N=1,000+, 14th annual survey | Annual | Yes |
| **Benchmarkit / Pavilion** | Practitioner | GTM metrics, CAC payback, margins, GRR/NRR | Metric-specific, N=43 to N=342 | Annual | Yes — **always quote the metric's own N** |
| **ChartMogul** | Vendor | Retention and churn from billing telemetry | 2,100–2,500+ active businesses | Quarterly | Yes **for retention/churn only** — never for multiples |
| **Capstone Partners** | Practitioner | Healthcare IT M&A multiples | Disclosed healthcare IT deals 2023 – Jul 2025 | Periodic | Yes |
| **Bridge Group** | Practitioner | Sales quotas, ramp, attrition | N=287 B2B SaaS orgs | Annual | Yes |
| **PitchBook** | Vendor (paid) | LMM deal volume; financials disclosed in **<10–15%** of sub-$50M deals | — | Continuous | Volume yes; small-deal multiples usually inferred |

**Go to the publisher.** The source research reached several of these through aggregator summaries
rather than the publishers' own pages. A whitelist entry authorises *the publisher*, not whoever
quoted it — if you cannot reach the original, say the figure is secondhand.

## Blacklist — never cite, even if it is the only hit

```
firstpagesage.com      subjolt.com          vandfort.com
biztoolkitpro.com      saashero.net         calcmastery.com
universalflow.io       growthcentr.com      fiscallion.io
```

Three traced examples of why:

- **"26% median growth / 101% NRR"** — originates in a Pavilion/Benchmarkit survey where NRR came
  from N=228 and growth from N=149, collected Feb–Mar 2024 as TTM-or-expected. Aggregators
  republished preliminary estimates as finalised industry facts with the sample sizes and timing
  qualifiers stripped.
- **"16-month CAC payback / $1.30 per $1 new ARR"** — Benchmarkit's figure came from N=198 of a
  342-company sample, and the blended $1.30 masks new-logo at $1.63 against expansion at $0.80.
  Aggregators dropped the subset boundary and the split.
- **FirstPageSage's vertical multiple grid** — asserts transaction multiples across 15+ verticals
  and revenue tiers with **zero transaction logging, no sample size, no date boundaries, no target
  names and no stated method**. Generated to capture long-tail valuation search intent.

---

## Coverage map — corrected

**Correction applied:** the source research marked ten verticals "Published" for multiples while
sourcing them from FirstPageSage, which the same research blacklists. Those are downgraded here.
A blacklisted source cannot supply a published band.

| Vertical | Retention | Multiples | Status |
|---|---|---|---|
| Healthcare IT | GRR 90–92%, NRR 105–112% (proxy) | **5.3x EV/Rev, 18.8x EV/EBITDA** — Capstone, disclosed 2023–Jul 2025 | **Published** (multiples only) |
| Legal | Gap — B2B proxy | Gap | Proxy only |
| Construction | Gap — SMB proxy | Gap | Proxy only |
| Field services | Gap | Gap | **Gap** |
| Education | Gap — mid-market proxy | Gap | Proxy only |
| Insurance | Gap | Gap | **Gap** |
| Manufacturing / ERP | Gap — mid-market proxy | Gap | Proxy only |
| Property | Gap — SMB proxy | Gap | Proxy only |
| Energy | Gap | Gap | **Gap** |
| Media / broadcast | Gap | Gap | **Gap** |
| Wealth & asset mgmt | Gap | Gap | **Gap** |
| Transportation / logistics | Gap | Gap | **Gap** |
| Government | Gap — enterprise proxy | Gap | Proxy only |
| Agriculture & commodity | Gap — SMB proxy | Gap | **Gap** |

**Healthcare IT is the only vertical with a defensible published multiple.** Everything else is a
horizontal proxy or nothing. Say that rather than reaching for a number.

---

## Two standing corrections — apply to every figure

### 1. Survey retention medians are inflated by 5–10 points

Published GRR of 88–91% and NRR of 101–103% come from **opt-in surveys**. Outperformers volunteer;
distressed companies do not respond or no longer exist. Billing-telemetry data shows lower-quartile
companies at 5.8–9.1% *monthly* churn — an annual GRR far below any survey median.

**So a target at 81% GRR is not obviously below-market.** It is below the *survey* median, which is
a selected sample. Prefer telemetry sources for retention, and when quoting a survey median, say
that it is one.

### 2. Deal size predicts multiple more strongly than vertical

- Disclosed deals skew large — median disclosed deal is **$80M EV**, so disclosed medians describe
  a different population than a $4M ARR target.
- The $50–100M band clears at roughly **twice** the multiple of the $20–50M band.
- Founder-led sub-$3M ARR clears nearer **2.5x–4.0x ARR**, often on an SDE-hybrid basis, against a
  headline LMM median of 4.0x–4.5x EV/Revenue.

**Quoting a disclosed median at a small target systematically overvalues it.** Name the size band
every time.

### And never mix these asset classes

| Basis | Typical | Why it differs |
|---|---|---|
| VC growth round | 10.0x–15.0x+ ARR | Minority stake, hypergrowth, liquidation preferences |
| Public SaaS index | ~3.2x–3.6x EV/Rev | Liquidity, scale, public consensus |
| Disclosed M&A mean | 6.3x–6.4x EV/Rev | Skewed by large disclosed deals |
| **LMM M&A median** | **4.0x–4.5x EV/Rev** | Control purchase, historical cash flow |

---

## Diligence economics, for scale

Lower-middle-market software: **$100K–$350K+** per transaction. QoE and accounting $35–90K;
technical and code $20–50K; legal and tax $40–120K; SaaS operations and commercial $15–40K.
Intermediated processes run 2–4 weeks to LOI and 4–9 months to close at 50–70% conversion, with a
5–15% auction premium; proprietary sourcing runs 18–36 months to LOI at 1–3% conversion but closes
at 70–85% and 10–30% below auction pricing.

---

## Where the source research contradicted itself

Recorded because a source map that hides its own defects is worse than none.

1. **It blacklisted FirstPageSage and then used it for ten verticals' multiples.** Corrected above by
   downgrading every affected row. This is the single largest change from the raw research.
2. **Several whitelist rows cite aggregators rather than publishers** — Aventis reached via one
   summary site, SaaS Capital via another, Benchmarkit via a third, Capstone via a fourth. The
   publishers are legitimate; the URLs are secondhand. Go to the source.
3. **The "annual GRR below 50–60%" figure is derived**, not published — compounded from ChartMogul's
   monthly churn rates by the researcher. The direction is sound and the specific annual number is
   an inference. Do not quote it as ChartMogul's.
4. **Healthcare IT retention (90–92% / 105–112%) is proxy, not vertical-specific**, despite the row
   reading as published. Only the Capstone multiple is vertical-specific there.
