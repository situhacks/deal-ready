# deal-ready

Screen a CIM (confidential information memorandum) into a cited scorecard and a
first-draft memo with call-outs. Local models only - no API keys, no network calls
to model providers, ever.

**Start from [`SKILL.md`](SKILL.md)**: the walk-through (five commands, what each
produces) and the honest boundaries. Hard rules that govern every change here:

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
