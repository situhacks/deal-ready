---
name: memo-draft
description: Structure a screening memo and its call-outs - what each section carries, how figures cite pages, and the call-out grammar that turns uncertainty into a question a human can answer. Use when drafting the memo after a CIM has been screened.
---

# Draft the memo

**The memo is the artifact a reviewer edits.** Its job is to let a human correct a document
instead of interrogating a JSON file. Everything below serves that.

## Structure

1. **Header** — target, source file, date, tier, score, coverage (`8/11 metrics recovered`).
2. **The numbers** — each metric with its value, page citation, and read type. Axis reads
   visibly marked.
3. **What the rules found** — blockers first, then warnings, then what passed. Each with the
   value that decided it.
4. **Market context** — where each deciding metric sits against its band, dated and sourced.
   Clearly separated from the rules, because it did not score anything.
5. **Observations** — narrative risk the arithmetic cannot see. **Every one flagged as
   judgement**, each with a page.
6. **Open questions** — the call-outs, gathered, ordered so the most consequential is first.

## Citation rule

**Every figure cites its page. No exceptions, including in summary sentences.**

If a sentence in the executive summary says ARR is $8.4M, it carries the page. A number that
appears without a citation in a tidy paragraph is exactly how an unverified figure gets signed.

## Call-out grammar

A call-out is not a warning label. **It is a question with an owner and an answer that would
resolve it.**

```json
{"id": "CO-3", "kind": "axis_read", "metric": "grr_pct", "value": 81.0,
 "evidence_page": 14,
 "question": "Gross retention was measured off the chart axis, not a printed label. Can
              management confirm FY25 gross revenue retention to the nearest point?"}
```

Four kinds:

| Kind | Raised when | The question asks for |
|---|---|---|
| `axis_read` | value measured off chart geometry | confirmation against source data |
| `missing_metric` | metric absent from the document | the number, at the management call |
| `definition_conflict` | the document defines a metric unusually, or two figures disagree | which basis is authoritative |
| `judgement` | a narrative observation | accept, edit, or strike |

**A call-out with no question is a defect.** If you cannot write the question, you do not
understand the uncertainty well enough to flag it — say that instead.

## Tone

Plain. Short sentences. No hedging adverbs and no salesmanship in either direction. The reviewer
is an analyst who will be annoyed by padding and misled by confidence.

**Never write a summary that implies more certainty than the file has.** If coverage was 8 of 11
and two of those eight were axis reads, the opening paragraph says so.

## What the memo never does

- **It never recommends a transaction.** It sorts and asks. A human signs.
- **It never states judgement as finding.** An observation about founder dependency is a
  suggestion, marked as one.
- **It never fills a gap.** A missing metric stays missing and becomes a question.
- **It never launders an axis read.** Even a confirmed one keeps its flag, with the confirmation
  recorded beside it.

## The stop condition

If a value arrived without a citation, or a call-out has no question, **stop and say so**. Do not
write a memo that looks finished. A complete-looking document with an unsourced number in it is
the failure this whole tool exists to prevent.
