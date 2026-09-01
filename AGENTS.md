# deal-ready

Screen a CIM (confidential information memorandum) into a cited scorecard and a
first-draft memo with call-outs. Local models only - no API keys, no network calls
to model providers, ever.

**There are two ways in, and you should pick deliberately:**

- **The plugin** — [`plugins/deal-ready/`](plugins/deal-ready/), registered in
  [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json). Commands,
  agents and skills. Needs no clone, no Python, no models. Start at
  [`plugins/deal-ready/skills/cim-screen/SKILL.md`](plugins/deal-ready/skills/cim-screen/SKILL.md),
  which is the workflow and its gates.
- **The repo** — the substrate and the evidence. `python screen.py <pdf>` for the
  deterministic run, `python review.py` to check numbers you already wrote,
  `python run_checks.py` to reproduce every published figure offline. Needs Ollama.

If you are an agent asked to screen a document, you want the plugin. If you are
changing how screening works, you want both.

Hard rules that govern every change here:

- **The model reads; code decides; a human signs.** No number the business acts on
  is computed by a model.
- **Nothing is published unless `run_checks.py` reproduces it** from committed
  artifacts, offline, on any machine.
- **Chart-interior values are measured from pixels**
  (`deal_ready/parse/chart_measure.py`), never taken from a model's estimate. An
  independent model re-read may agree or disagree with the measurement - it is
  never the source.
- **Corrections teach the next version; they never rewrite the current one.**

Layout and design record: [`README.md`](README.md). Reader-model comparisons:
[`reports/bakeoff.md`](reports/bakeoff.md).
