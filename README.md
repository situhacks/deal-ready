<img src="assets/banner.svg" alt="deal-ready — CIM screening and pre-LOI deal scoring for software M&A" width="100%">

A confidential information memorandum lands in an inbox: forty-odd pages of prose,
tables and charts describing a software company that is for sale. Somewhere in there
are ten numbers an analyst needs. Finding them means two to four hours of reading, a
spreadsheet, and a one-page recommendation, and about nine in ten of those memoranda
end in "pass" anyway.

This is a first pass at that work, built to run locally. Point it at a CIM and you
get the artifact the analyst was going to assemble by hand: the metrics, the
arithmetic checked against the buyer's rubric, a criteria fit and a tier, and a
drafted memo where every uncertain value carries a call-out. Every figure traces to
the page it came from. Nothing here recommends a transaction; the tool sorts an inbox
and asks questions, and a human signs.

```bash
pip install -r requirements.txt
python generate.py                 # build the synthetic corpus (no model, no network)
python screen.py data/             # screen it: scorecards + findings
python memo.py data/               # draft screening memos with call-outs
python capture.py T05 --edited reports/memo_T05_reviewed.md   # turn a review into records
python run_checks.py               # verify every number in this README, offline
```

Python 3.12, no API key, no account, no paid inference. The parts that need a model
use local models through Ollama. With no models installed, `python screen.py data/
--no-vision` still runs end to end, and the gap between that run and the full one is
the most interesting thing here.

**What you get**

- A **cited scorecard** per target: ten software metrics set against the buyer's
  rubric, eleven deterministic rules, criteria fit and tier. Readable markdown,
  generated from the config, so the rubric and the verdicts are things you can click
  into.
- A **drafted screening memo** where every uncertain value carries a call-out id.
- **Chart-only values measured from pixels**, not guessed by a model, and each one
  independently re-read, with the agreement recorded in the memo.
- A **correction loop**: review the memo, run one command, and your edits become
  regression cases and worked examples that automated checks assert on every future
  run.

**Review a real run, end to end.** Every artifact below is committed. No re-run
needed. One target (Ashgrove, the most dangerous company in the corpus), the whole
loop:

| Step | Artifact |
|---|---|
| the input | [`data/T05_Ashgrove_CIM.pdf`](data/T05_Ashgrove_CIM.pdf) |
| the rubric it is judged against | [`reports/scorecard_template.md`](reports/scorecard_template.md) |
| the scorecard | [`reports/scorecard_T05.md`](reports/scorecard_T05.md) - 97.7, tier 1, and one red-letter breach: gross retention 81% against an 85% floor |
| the same scorecard, machine-readable | [`reports/findings.json`](reports/findings.json) |
| the drafted memo | [`reports/memo_T05.md`](reports/memo_T05.md) - call-out ids on every uncertain value, the chart values and their independent re-read, the questions for the seller |
| the call-outs, machine-readable | [`reports/callouts_T05.json`](reports/callouts_T05.json) |
| a human's review of that memo | [`reports/memo_T05_reviewed.md`](reports/memo_T05_reviewed.md), and the diff-captured session it produced: [`data/corrections/T05_session01.json`](data/corrections/T05_session01.json) |
| what that review taught | [`eval/regressions.json`](eval/regressions.json) and [`eval/judgement_examples.json`](eval/judgement_examples.json) - asserted by `run_checks.py` on every run |

The other four targets live beside these: [`reports/memo_T01.md`](reports/memo_T01.md)
through [`memo_T04.md`](reports/memo_T04.md), their scorecards and call-outs, and the
reader comparison in [`reports/bakeoff.md`](reports/bakeoff.md).

**Contents**: [How it works](#how-it-works) · [The loop](#the-loop) ·
[The finding](#the-finding) · [The numbers](#the-numbers) ·
[The story: v1 → v3](#the-story-v1--v3) · [Honest boundaries](#honest-boundaries) ·
[Using it as a skill](#using-it-as-a-skill) · [Reading order](#reading-order) ·
[Layout](#layout)

---

## How it works

```mermaid
flowchart LR
    PDF["CIM<br/>PDF deck"] --> TL["1 · text layer<br/><i>free, lossless<br/>exact spans</i>"]
    TL -->|"recovered<br/>30 of 50"| RULES
    TL -->|"still missing"| RT["2 · route<br/><i>text embeddings<br/>rank the pages</i>"]
    RT --> V["3 · read<br/><i>0.9B parser<br/>routed pages only</i>"]
    V -->|"page yields<br/>no values"| CH["3b · chart specialist<br/><i>one call: labels · ticks<br/>· estimates</i>"]
    CH --> GEO["3c · geometry<br/><i>code measures the pixels<br/>against those ticks</i>"]
    V --> RULES
    GEO --> RULES
    RULES["4 · deterministic rules<br/><i>arithmetic · no model<br/>reproducible forever</i>"] --> FIT["5 · fit score + tier<br/><i>config-driven<br/>every component shown</i>"]
    FIT --> OUT["cited scorecard<br/>findings.json"]

    classDef free fill:#e8f0fb,stroke:#2a78d6,stroke-width:1.5px,color:#0b0b0b
    classDef paid fill:#fdece4,stroke:#eb6834,stroke-width:1.5px,color:#0b0b0b
    classDef det  fill:#eef1f4,stroke:#5b7ba6,stroke-width:1.5px,color:#0b0b0b
    class TL,RT free
    class V,CH,GEO paid
    class RULES,FIT,OUT det
```

Steps 1–3 exist to make step 4 possible. Blue is free, orange is the step that costs
something, grey decides nothing on its own.

**The model reads. Code decides. A human signs.** No number the business acts on is
computed by a model. That discipline is what lets a deal lead re-run a screen from a
year ago and get the same answer, and it is why most of the work costs nothing.

**We asked whether the strongest model should just read everything.** It is the
obvious question, and the bake-off answered it by measuring every candidate as a
full-page reader on the same pages ([`reports/bakeoff.md`](reports/bakeoff.md)). The
newest open frontier model read 80% of prose fields (it paraphrases), 80% of chart
values, at 148 seconds a page. A 0.9B specialized parser read 100% of prose, tables
and labelled charts in 5 seconds, and dropped unlabelled chart interiors entirely.
There was no single winner. There was a best reader for each job, so the pipeline
assigns each job directly: the parser reads every routed page, and a page that yields
no values goes straight to the frontier model, whose one call supplies the series
labels, the tick glyphs, and its own estimated values. Code then measures the
endpoints from the pixels against those ticks. The estimates are never used as
numbers. They exist to be compared with the measurement, and the memo reports whether
the two paths agree.

**Nothing recommends a transaction.** The tier sorts an inbox. A `Pass` means "not a
fit against this profile", and never "bad company". The profile in
`criteria/default.json` is config, so swapping in a real buyer's scorecard is a
config change rather than a rewrite.

---

## The loop

The pipeline is a straight line. The loop is what makes the tool improve, and it
starts with a human:

```mermaid
flowchart LR
    D["draft memo<br/>every uncertain value<br/>carries a call-out id"] --> R["reviewer edits<br/>the markdown"]
    R --> C["capture.py<br/>diff → structured records"]
    C --> T{"triage"}
    T -->|"factual error"| REG["regression case<br/>asserted on every run"]
    T -->|"judgement accepted"| EX["worked example<br/>in future drafts"]
    T -->|"preference"| OVL["personal overlay<br/>never a global default"]
    REG --> NEXT["next version<br/>gated by checks"]
    EX --> NEXT
    NEXT -->|"a new inbox, a new draft"| D

    classDef human fill:#eef1f4,stroke:#5b7ba6,stroke-width:1.5px,color:#0b0b0b
    classDef code  fill:#e8f0fb,stroke:#2a78d6,stroke-width:1.5px,color:#0b0b0b
    class R human
    class C,T,REG,EX,OVL,NEXT code
```

Reviewer corrections are the real eval set. Three properties make this a loop rather
than a suggestion box:

- **Blind spots are the headline metric.** When a reviewer corrects something no flag
  prompted, the record says so. Those are the most valuable lines in the file, because
  they measure what the system did not even know to flag.
- **Every accepted correction must teach.** If an accepted judgement never became a
  worked example, or an extraction gap was never locked by a regression,
  `run_checks.py` fails.
- **Corrections change the next version, never the current one.** The recursion runs
  on a release cadence a person can audit, and the changelog names who taught what.

The first review session proved the whole loop in miniature. A reviewer caught page 7
of one target announcing a retention chart while both values came back unread. That
blind spot became a mechanical upgrade, the upgrade became a fix, and two regressions
now fail if those values ever go dark again.

---

## The finding

A CIM is a deck, and its numbers do not all live in sentences. In this corpus **20 of
50 metrics exist only inside rasterised charts**, and a leak check fails the build if
one of them escapes into the text layer.

It is not a random 40%. It is gross retention, net retention, largest-customer
concentration and top-five concentration: the metrics that decide whether to buy the
company. Revenue, margin and EBITDA, which a text layer reads perfectly, only tell
you how big it is.

![Recovery by field type: the text layer gets 100% of prose and table fields and 0% of chart-carried ones; the full pipeline lifts charts to 100%](assets/layer-p.png)

The same five companies, the same rules, the only difference being whether the
pipeline could read a chart:

![Criteria fit scores by target: under a text-only read the clean company, the concentrated one and the leaking one all score 60; the full pipeline separates them to 100, 95 and 98](assets/discrimination.png)

Three companies with materially different risk, one identical score. A text-only
pipeline does not degrade gracefully. It goes blind exactly where the decision lives,
and it does so silently, because every field it did read, it read correctly.

---

## The numbers

Reproduce all of them with `python run_checks.py`, offline, from committed artifacts.

**Layer P — what each parse backend makes available.** The percentage of ground-truth
fields recovered and correctly attributed to their metric, on the page the value
actually lives on. This grades the parser, not the extractor: it is a ceiling on what
anything downstream could achieve. See
[`reports/layer_p.md`](reports/layer_p.md).

**Layer R — routing.** Recall@k for the page carrying each metric, and how many pages
the vision step has to read. Routing recovers 100% of chart pages at rank 1, so at
k=1 it selects 15 of 60 pages, a 75% cut, and misses no chart field. See
[`reports/layer_r.md`](reports/layer_r.md).

**The capability boundary.** Chart fields split cleanly by whether the chart printed
its data labels, and the boundary is specific:

| Backend | Charts with data labels | Charts read off the axis |
|---|---|---|
| text layer | 0% (0/10) | 0% (0/10) |
| `minicpm-v4.6` (1B general VLM, page render) | 100% (10/10) | 0% (0/10) |
| `glm-ocr` (0.9B parser, page render) | 100% (10/10) | 0% (0/10) |
| `qwen3.8:27b` (open frontier, page render) | 100% (10/10) | 80% (8/10) |
| production pipeline (parser + chart specialist + geometry) | **100% (10/10)** | **100% (10/10)** |

Reading a printed label is recognition. Reading a value off an axis is spatial
reasoning, and every model that tries it estimates: the frontier model landed three
of five endpoint pairs exact and two within 0.2, which sounds fine until the
arithmetic needs the number. So the pipeline measures instead. The chart model reads
the tick glyphs once. Code finds each series by colour, fits the centreline of the
line entering the end marker (a 13-pixel marker rasterises wherever its sub-pixel
phase lands; a 200-pixel line averages that noise away), and interpolates against
the gridlines. That is arithmetic, and `run_checks.py` re-runs it from the committed
images on any machine, with no GPU and no model.

**A caveat stated plainly:** the corpus is synthetic and this repo wrote it. Ground
truth is a by-product of generation rather than labelling after the fact, which
removes one class of error and leaves another: a generator and a scorer authored in
the same session are favourable to each other by construction. The `realworld/`
manifest exists to test against public documents this pipeline did not write.

---

## The story: v1 → v3

**v1 asked whether the work could be done at all, locally.** The text layer, the
embedding router, tiered local vision, deterministic rules, and the finding that the
decisive 40% of metrics live only in charts. Every model output was committed, so
every number could be re-verified without a GPU.

**v2 asked what the analyst would write next.** The memo, with call-outs derived
mechanically; diff-based correction capture; and the fold-back contract. Its first
review session caught a real blind spot, and that lesson became the regression that
still guards it.

**v2.1 asked why the axis column sat at 70%.** The strong tier was estimating:
reasoning on, lossy page renders. Reasoning off, exhibit re-reads from the PDF's own
embedded image, and pixel measurement in code closed it to 20/20, and the last
change made the axis values verifiable offline like everything else.

**v3 asked whether any of this was the right way, or just our way.** A research wave
read the 2026 document-parsing field and found specialized parsers beating frontier
models at transcription, no benchmark scoring chart interiors at all, and
leaderboard gaps smaller than run-to-run noise. So the swap was decided the only way
that could be trusted: a bake-off on these pages. The reader changed; the guarantees
did not. Then the frontier model's confirmed estimation habit became a control
instead of a risk.

**What v3 did not do:** chase a leaderboard past the evidence, adopt weights whose
license would not survive a commercial read, or replace working stages because a
benchmark implied it.

---

## Honest boundaries

- **The corpus is synthetic**, modelled on publicly described conventions. No real
  memorandum, no real company, no proprietary deal flow.
- **Extraction is deterministic here, not model-driven.** The end-to-end run tests
  stated values against parsed text, which is what keeps it reproducible offline. A
  production build puts a structured-output model call at that seam; the interface
  and the eval harness would not change, which is why the seam exists.
- **The narrative judgement layer ships as flagged suggestions, not a detector.**
  Founder risk, succession gaps, unsupported technology: none of that is visible to
  arithmetic. The memo carries model observations with ids attached so a reviewer can
  accept, edit or strike them. A calibrated judge against a held-out labelled set is
  future work, stated as such.
- **This is not a data-room tool.** The parse answer changes at 10–50K pages; see
  [`docs/ingest.md`](docs/ingest.md) §8.

---

## Using it as a skill

The repository is shaped to drop into an agent:

- **Claude Code**: copy or clone the repo as a skill folder. [`SKILL.md`](SKILL.md)
  at the root carries the name, the trigger description, and the five-command
  walk-through.
- **Any AGENTS.md-reading agent** (Codex-class CLIs, ChatGPT desktop workspace):
  [`AGENTS.md`](AGENTS.md) at the root is the agent-agnostic entry, with the hard
  rules and the pointers.
- **Requirements**: Ollama with `glm-ocr`, `qwen3.8:27b` and `nomic-embed-text`
  pulled. Everything degrades visibly without them, never silently.

---

## Reading order

| File | What it is |
|---|---|
| [`docs/ingest.md`](docs/ingest.md) | **The design record.** Why OCR is the wrong default, why whole-document multimodal is also wrong, what embeddings do and do not do, the corpus-size ladder, what was tried and rejected, and two failures that would have published false findings |
| [`docs/metrics.md`](docs/metrics.md) | Every metric the screen reads: what it is, why a buy-and-hold acquirer prices on it, how a CIM obscures it |
| [`docs/rules.md`](docs/rules.md) | Every rule with its deal rationale |
| [`docs/callouts.md`](docs/callouts.md) | The judgement seam: call-outs, diff-based correction capture, the fold-back contract |
| [`playbook.md`](playbook.md) | The rollout half: shadow mode, who to build with, what will actually go wrong |
| [`docs/hardware.md`](docs/hardware.md) | Local model setup, AMD/ROCm traps, and three failures that would have published false findings |
| [`reports/bakeoff.md`](reports/bakeoff.md) | The reader comparison that chose the current stack, with committed per-model caches |
| [`reports/scorecard_T05.md`](reports/scorecard_T05.md) | A finished scorecard, as the reviewer reads it; the template it is judged against sits beside it |
| [`criteria/default.json`](criteria/default.json) | The investment profile — config, not code |
| [`CHANGELOG.md`](CHANGELOG.md) | Version by version, with what taught what |

---

## Layout

```
generate.py            build the synthetic corpus; fails if a chart value leaks to text
screen.py              the CLI an analyst would run: findings + readable scorecards
memo.py                draft screening memos with call-outs
capture.py             diff an edited memo into correction records
bakeoff.py             compare page-reader candidates, identical grading
parse_corpus.py        run every parse backend, write Layer P
run_checks.py          reproduce every published number, offline

deal_ready/
  generator/           target profiles + PDF deck rendering
  parse/               text layer · reading pipeline · chart geometry, one interface
  embed/               page routing, MaxSim in numpy, no vector database
  scorer/              deterministic rules + criteria fit
  scorecard.py         renders the rubric and per-target scorecards as markdown
  memo/                memo drafting, call-out derivation, the narrative pass
  models/ollama.py     the single door every model call goes through
  values.py            what counts as recovering a number

criteria/              investment profiles
data/                  generated corpus, ground truth, committed model caches, review sessions
eval/                  judgement examples folded back from reviewers, regressions
reports/               generated results: findings, scorecards, memos, call-outs, bake-off
realworld/             manifest of public documents for the spot check (no PDFs committed)
```

Money is whole dollars, integers everywhere. This thing claims figures tie out, and
floats would make that a lie.
