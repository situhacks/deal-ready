# Changelog

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
