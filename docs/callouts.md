# Call-outs and corrections — the judgement seam

The scorecard stops at arithmetic. [`README.md`](../README.md) names what is missing
as an honest boundary: Ashgrove scores well on numbers and is the most dangerous
company in the corpus, because founder risk, succession and unsupported infrastructure
are invisible to every rule. This document specifies the layer that closes that gap
without breaking the trust boundary.

The boundary extends by one link. It was:

> the model reads · code decides · a human signs

It becomes:

> the model reads · code decides · **a human corrects · corrections teach**

Nothing about the first three links changes. The model still never computes a number
the business acts on. What is new: the memo stage drafts prose *around* code-computed
values, marks every sentence that carries judgement, and captures what the reviewer
changes. Those corrections are data. They become regression cases and worked examples,
which is how the system improves on a release cadence instead of by silent drift.

## Why call-outs exist

Three facts from the published numbers force them:

1. **Axis-read values top out near 70%** even after escalation. The README already
   states the consequence — treat them as flagged for human confirmation. A call-out
   is that statement made mechanical.
2. **A missing metric is a finding, not a zero**, because its absence is usually
   deliberate. In a memo it must surface as a question to ask, not a blank in a table.
3. **The narrative risk class has no detector yet.** Until a calibrated judge exists,
   the honest substitute is a flagged judgement: the model may observe, but every
   observation ships with its id attached so a human can accept, edit or reject it.

## Call-out kinds

Every kind derives mechanically from artifacts that already exist. Nothing here asks
the model to self-report confidence.

| kind | derived from | meaning |
|---|---|---|
| `axis_read` | `citations[m]["method"] == "vision"` on an escalated page | value was read off a chart axis; ~70% ceiling; confirm or replace |
| `label_read` | `citations[m]["method"] == "vision"`, no escalation | recognition, not inference — low risk, shown for completeness |
| `missing_metric` | in profile, absent from `metrics` | frame the question; if the metric's name sits on a vision-read page, say an exhibit exists and defeated the parser |
| `definition_conflict` | finding whose detail flags a definitional error (e.g. GRR > 100) | the seller mislabelled a metric; do not average it away |
| `judgement` | a memo sentence carrying narrative interpretation | model observed, did not compute; accept / edit / reject |

The `missing_metric` refinement came out of the first review session: T05 reported
gross retention as "never stated - likely deliberate" while page 7 announced
"Gross and net revenue retention, FY22 to FY25" as a chart the parser could not
read. Deliberate omission was the wrong default reading whenever the metric's
name sits on a page the vision tier actually visited. That upgrade is mechanical,
ground-truth-free, and locked by `reg-001` in `eval/regressions.json`.

```yaml
# reports/callouts_T03.json (one entry)
id: co-T03-judgement-004
kind: judgement
anchor: memo:T03#risk-2          # stable span reference into the drafted memo
metric: null                     # or e.g. top1_customer_pct for value-backed kinds
confidence_pct: null             # axis_read carries the measured ceiling (70);
                                 # judgement carries none - honesty about honesty
evidence_page: 11
question: "Founder-written settlement engine with no succession plan - confirm key-person dependency"
```

Rules:

- ids are stable across regenerations of the same draft version (`co-<target>-<kind>-<nn>`),
  so a correction always points at something that still exists.
- `confidence_pct` appears only where a measured number exists. Inventing a confidence
  score for narrative judgement would be the exact sin the scorecard refuses elsewhere.

## Correction records

Capture is diff-based, on purpose. The reviewer edits the memo file they were handed;
nothing new to learn.

```bash
python screen.py data/T03_Kestrel_CIM.pdf        # -> memo_T03.md + callouts_T03.json
$EDITOR reports/memo_T03.md                       # human pass
python deal_ready/memo/capture.py T03             # diff -> structured records
```

```yaml
# data/corrections/T03_session01.yaml
target_id: T03
draft_version: v1
minutes_spent: 14
corrections:
  - callout_id: co-T03-axis_read-001
    field: grr_pct
    before: "88"
    after: "91"
    reason_category: axis_read_error     # subsumed by factual_error at fold-back
  - callout_id: null                     # blind spot - no call-out prompted this
    anchor: memo:T03#summary-1
    before: "no material concentration risk"
    after: "top customer is 34% of ARR per p11 chart"
    reason_category: factual_error
```

`callout_id: null` is the most valuable record in the file: the system missed it and
the reviewer caught it anyway. Blind-spot count per version is the honest quality
metric — precision/recall on call-outs flatters whatever the flagger already knows.

Attribution rule: **pure insertions are never credited to a call-out**, however near
one they sit. An inserted line is content the system did not produce — that is what
blind-spot means. Edits and strikes carry before-text and are attributed to the
nearest anchor above. Triage may reassign by hand.

`reason_category` ∈ `factual_error · judgement_call · preference · new_information`,
with `needs_triage` as the initial state for anything capture cannot classify
mechanically (insertions default there). Nothing folds back while it reads
`needs_triage`.

## Fold-back contract

A correction is received the moment it is captured; it teaches only after triage.
Triage is a human decision, recorded, never automatic:

| reason_category | becomes | lands in |
|---|---|---|
| `factual_error` (value wrong) | regression case — the pipeline must flag this pattern next run | eval cases consumed by `run_checks.py` |
| `factual_error` (extraction gap) | routing/extraction test case | same |
| `judgement_call` (accepted as written) | worked example for future drafts | memo few-shot set |
| `preference` | personal overlay — offered upstream as an example, never merged silently as a default | outside this repo |
| `new_information` | not a system error; logged, no fold-back | session record |

Convergence rule for multiple reviewers (pack era, not today): a `judgement_call`
promotes to shared example when independent reviewers converge; when they split, that
is a policy fork and gets escalated rather than averaged.

## Reproducibility

Same rule as every published number: nothing is claimed unless
[`run_checks.py`](../run_checks.py) reproduces it from committed artifacts. Three
checks guard the loop:

- **correction records are consistent** — every record triaged, every `callout_id`
  resolves against the target's call-outs file, no blind spot carrying an id;
- **fold-back is complete** — every accepted judgement appears in
  `eval/judgement_examples.json`, every extraction gap is asserted by a regression;
- **reviewer regressions hold** — each lesson learned stays visible in current
  artifacts, so the pipeline cannot silently regress past what a reviewer taught it.

A correction that never got committed never happened. A correction that changed
nothing downstream was theatre.

## Deliberately out of scope

- No auto-apply. Corrections teach the next version; they never rewrite the current one.
- No model-authored rubric changes. Rules and criteria stay human-edited files.
- No confidence invention. Where there is no measurement there is no number.
