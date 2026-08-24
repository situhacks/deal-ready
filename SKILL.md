---
name: deal-ready
description: Screen a CIM (confidential information memorandum) into a cited scorecard and a first-draft memo with call-outs. Chart-carried metrics via local vision models, deterministic rule checks, uncertainty flagged, reviewer corrections captured so the next draft learns from them.
---

# Deal Ready

Point this skill at a CIM PDF. You get back a cited scorecard (metrics, arithmetic,
criteria fit, tier) and a drafted screening memo where every uncertain value carries
a call-out id. Nothing recommends a transaction; the tool sorts an inbox and asks
questions, and a human signs.

## Walk-through

1. **Screen** - `python screen.py <pdf-or-folder>`
   Writes `reports/findings.json`. Exit code 1 means blocker-tier findings exist.
2. **Draft memos** - `python memo.py <pdf-or-folder>`
   Writes `reports/memo_<TARGET>.md` plus `reports/callouts_<TARGET>.json`. Every
   figure cites its page. Call-outs mark values measured off a chart axis, missing
   metrics, definition conflicts, and narrative judgement from a local model.
3. **Review** - edit the memo file directly. Confirm or replace flagged values,
   tighten or strike model observations, add anything the flags missed. Additions
   are recorded as blind spots; they are the most valuable corrections.
4. **Capture** - `python capture.py <TARGET> --edited reports/memo_<TARGET>_reviewed.md --minutes N`
   Diffs your edit into structured correction records under `data/corrections/`.
   Triage any left as `needs_triage`, then commit them.
5. **Fold back** - accepted judgement edits go to `eval/judgement_examples.json`;
   extraction gaps become entries in `eval/regressions.json`. Future drafts carry
   the examples; `run_checks.py` verifies every accepted correction actually taught
   something and every regression still holds.

## Requirements

Python 3.12. Models are local through Ollama (`glm-ocr` reads every page,
`qwen3.5:4b` re-reads exhibits and tick glyphs, `nomic-embed-text` routes;
`minicpm-v4.6` is the general-VLM reference backend for `bakeoff.py` comparisons).
Without them the pipeline still runs deterministically and reports which parts did
not execute. No API keys, no network calls to model providers, ever.

## Honest boundaries

The corpus in `data/` is synthetic. Values read off a chart axis are measured from
the chart's own pixels - the model reads the tick-label glyphs once, code fits the
line geometry against the gridlines - and they ship flagged anyway, because a value
recovered from a picture is not a value the seller printed. Charts without clean
geometry (no gridlines, uncolour-coded series) fall back to the model's
transcription and keep the flag. Narrative observations are suggestions with ids
attached, never findings. Corrections change the next draft, never the current one.
