# Changelog

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
