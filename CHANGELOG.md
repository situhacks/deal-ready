# Changelog

## v3.2.0 — 2026-08-24

- The escalation ladder is gone. The bake-off that measured every candidate as a
  full-page reader settled the question the ladder existed to answer: no single
  model wins, so the pipeline now assigns each job to its measured best, directly.
  GLM-OCR reads every page (100% prose/table/labelled charts, 5s/page); pages that
  yield no values go straight to the chart specialist; qwen3.5 and minicpm leave the
  runtime path (minicpm stays as the bake-off reference).
- The chart path collapsed from three model calls to one: qwen3.8:27b reads an
  exhibit once - series labels, tick glyphs, and its own estimated values - code
  measures the endpoints against those ticks, and the estimates become the
  cross-check against the measurement in the same call. Reader runtime on this
  corpus: 100s.
- Readable scorecards: `screen.py` now renders the investment rubric
  (`scorecard_template.md`) and each target's numbers set against it
  (`scorecard_<TARGET>.md`) as markdown, generated from the config so they cannot
  drift; `run_checks.py` regenerates and byte-compares them (13 checks total).
- README rewritten: article shape (takeaway and quick-start at the top, the
  correction loop as its own diagrammed section, the version story at the bottom),
  worked-example links to every committed artifact in the loop, and a plainer voice
  throughout. AGENTS.md added as the agent-agnostic entry point (Claude Code reads
  SKILL.md; Codex-class agents read AGENTS.md).
- tiered.py renamed to reading.py; the backend label is now
  `pipeline:glm-ocr->[qwen3.8:27b+geometry]`.

## v3.1.0 — 2026-08-24

- Cross-check tier: every measured axis value now carries an agreement record from
  an independent perception path. Qwen3.8-27B (newest open general multimodal)
  re-reads each measured chart; agreement within half a gridline gap builds
  confidence in the memo call-out, disagreement prints "resolve before use". The
  measurement stays the number the pipeline uses - the read is a second opinion,
  never a source.
- Probe evidence (committed reads): three of five endpoint pairs read exact, two
  within 0.2, tick labels digit-identical to the strong tier's - the research's
  prediction that a frontier-class model still estimates rather than measures,
  confirmed on this corpus and turned into a control instead of a risk.
- Optional by design: without the model installed the cross-check skips and no
  agreement is claimed. `run_checks.py` verifies the committed reads still agree
  offline, alongside the existing pixel re-measurement.

## v3.0.0 — 2026-08-24

- The cheap tier is now a specialized parser: GLM-OCR (0.9B, MIT) reads every page,
  replacing the general 1B VLM. Bake-off evidence (bakeoff.py, reports/bakeoff.md):
  identical graded fidelity on prose, tables and labelled charts - including the
  chart-internal callout box v2.1 was built around - at ~5s/page vs ~19s. End-to-end
  latency fell ~44% (526s -> 297s on this corpus) with under half the token spend.
- The escalation trigger learned the parser signature: a specialized reader drops
  unlabelled chart interiors AND the exhibit vocabulary, so "no numeric values at
  all" now escalates on its own, whatever the page mentions. Pages with numbers and
  an exhibit mention still escalate (annotation-drop insurance).
- bakeoff.py: candidate readers graded identically on the ground-truth pages, same
  prompt, per-model committed caches, "not installed" recorded as not run. Round-1
  findings include a disqualifying quirk the model card does not mention:
  deepseek-ocr's Ollama port instant-stops on any prompt over ~50 characters
  (bisected), so it cannot hold the never-invent transcription contract.
- vision.parse accepts per-call prompt/system and a cache variant, so candidates
  with different instruction contracts grade under their own cache namespaces.
- Everything measured in v2.1 holds: 20/20 chart values, axis column from committed
  pixel geometry, 12/12 offline checks. The swap changed who reads pages; it did not
  change what the pipeline can prove.

## v2.1.0 — 2026-08-24

- The axis column is closed: chart-only values 20/20 on the committed eval, up from
  16/20, and the axis split from 7/10 to 10/10. Three changes did it, none of them a
  bigger model:
  - `think=False` at the model door. The v1 escalation burned 119-171s a page inside
    an unterminated thinking block; with reasoning off the same model answers in
    6-17s and lands within tenths.
  - Escalation re-reads the exhibit, not the page: the PDF's own embedded image at
    native resolution instead of a 120 DPI render. This also recovered chart-internal
    callout boxes the cheap pass had been silently dropping.
  - Axis values are measured, not estimated (`chart_measure.py`). The model reads the
    tick-label glyphs once, cached; code finds each series by colour, fits the
    centreline of the line entering the end marker, and interpolates against the
    gridlines. `run_checks.py` re-measures all ten values from committed pixels with
    no GPU and no model - the same offline verifiability the arithmetic rules always
    had.
- The escalation trigger now fires on every exhibit page. The loud-failure gate made
  sense at ~150s a page and made no sense at 6-17s, and it had a blind spot no
  trigger could close: a dropped annotation on a page full of numbers. The
  axis-versus-label classification that drives flagging is unchanged and still
  ground-truth-free.
- Memos flag axis-read values with the rate measured on the committed eval, quoted
  live from `reports/layer_p.json` rather than a hardcoded ceiling.
- Review-session history is frozen per session (`callouts_<target>_session<N>.json`),
  so regenerating a target's call-outs no longer rewrites what a reviewer saw.
- reg-001 evolved with the lesson it guards: the T05 p7 retention values must stay
  recovered from p7 and flagged, not merely asked about. reg-002 covers net retention.

## v2.0.0 — 2026-08-23

- Memo stage: drafted screening memos with page-cited figures and five kinds of
  call-outs derived mechanically from screen results (`memo.py`, `deal_ready/memo/`).
- Narrative pass through the ollama door with `think=False`; fails soft, never fakes.
- Correction capture by diff on the edited markdown, blind spots included
  (`capture.py`).
- Fold-back contract enforced offline by three new checks: records consistent,
  fold-back complete, reviewer regressions hold. First session (T05) already taught
  one mechanical upgrade, locked as reg-001.
- `think` parameter added to the model door after qwen3.5 returned empty strings
  while burning its whole budget inside an unterminated thinking block.

## v1.0.0 — 2026-08-23

- Initial tagged release: text-layer extraction, embedding-based page routing,
  tiered local vision for chart-carried metrics, deterministic rules, criteria fit
  and tiering, committed caches, fully offline reproduction via `run_checks.py`.
