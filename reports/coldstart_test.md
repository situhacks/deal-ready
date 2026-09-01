# Cold-start test — can an agent that has never seen this repo use it?

**Run 2026-08-31.** An agent with no prior context was given two things: the repo path and a CIM
path. It was told the repo contains a plugin with instructions, and to find them and follow them.

It was walled off from `data/ground_truth.json`, `reports/`, `eval/`, and `data/corrections/` —
every file containing the answers — and forbidden from running the repo's Python, because the
question was whether the *instructions* are followable, not whether the pipeline works. It read
the PDF itself and confirmed at the end that it had broken none of those constraints.

**It reached Gate 1 and stopped, which is correct.** Stages beyond that need an operator reply it
could not get.

## Two numbers that are easy to confuse

**The agent's reading accuracy was 10 of 10 — every rubric metric, correct.** Separately, and
measured across the whole corpus afterwards, both substrates read all twenty chart-carried values
exactly ([`substrate_comparison.md`](substrate_comparison.md)).

**The 70 and the 97.7 below are the target company's score against the rubric, out of 100.** They
have nothing to do with how well the agent read. Binary award of each criterion's weight gives
Ashgrove 70; proportional credit gives it 97.7. That is a defect in the *rubric documentation*,
not in the reading.

## What it got right

All ten rubric metrics recovered from the document, read types classified correctly, both
chart-carried retention values measured off the axis to within 0.1 of ground truth (81.0 and
86.0), and the concentration figures taken as printed labels with an axis cross-check. It also
independently derived the ARR-versus-annualised-MRR tie-out, caught that gross margin cannot be
verified without a revenue line, and flagged the founder-dependency and 1998-core narrative risks
as judgement rather than findings.

Its Gate 1 questions were the right six, including two the pipeline does not ask: the size of the
EBITDA add-backs, and what "approximately 84%" actually is on a metric carrying a 20-point weight
and a blocker rule.

## What it found — the defects that mattered

**1. The documented entry path led away from the plugin.** `AGENTS.md` said start at `SKILL.md`;
`SKILL.md` was the five-command Python walkthrough and never mentioned `plugins/`. A cold agent
following the docs runs the thing it was told not to run. It found the plugin by listing files.

*Fixed:* root `SKILL.md` deleted, `AGENTS.md` now names both paths and says which one an agent
asked to screen a document wants.

**2. The scoring award rule was never stated, and it flips the tier.** `deal-rules` gave weights
and tier bands but never said how a criterion converts to points. Binary award produced 70 →
Tier 2. Proportional produced 97.7 → Tier 1. The agent inferred binary, flagged the inference as
the single biggest gap, and deliberately did not read `scorer/fit.py` to resolve it — because
doing so would have hidden the defect.

**The implementation is proportional. Its estimate of 97.7 was exact.** So a plugin-only user
would have reached a different verdict than the repo on the same document.

*Fixed:* `deal-rules` now states the award rule with a worked example.

**3. The plugin never said how a PDF becomes pixels.** `axis` reads are defined as measured off
chart geometry, but nothing said how the reader sees the chart. In this environment the agent hit
`pdftoppm is not installed` and wrote its own rasteriser.

*Fixed:* `cim-read` gained a step 0 — read the PDF directly, and if rendering is unavailable, say
so and stop rather than falling back to the text layer silently.

**4. `cim-screen` undercut the plugin as a standalone**, telling the reader to prefer the
deterministic path when the repo is present, with no branch for it being unavailable — and no
guidance at all for a run with no human to answer a gate.

*Fixed:* the skill now says it is self-sufficient, and that a run with nobody present stops at the
first gate rather than waiving all three.

**5. Two files disagreed about this document.** `docs/rules.md` said Ashgrove "scores well on
every rule above." It does not — the gross-retention warning fires. *Fixed.*

**6. Smaller:** the Rule of 40 denominator was undefined (fixed — take margin over ARR when total
revenue is absent, and say so); the coverage statistic named no canonical metric list (fixed —
the ten scored metrics are enumerated); `criteria.json` referenced a repo path that does not exist
in a plugin-only install (fixed); which read type ships when a label and an axis agree was
unspecified (fixed — the label ships, with the measurement recorded as a cross-check); and two
empty `skills/` directories cost it a detour (removed).

## The defect the test surfaced indirectly

Chasing the scoring question exposed a worse one. The README quoted T05 at **97.7, Tier 1**, while
the committed `findings.json` said **60.0, Tier 2 with 6 of 10 metrics recovered** — and gross
retention, the number the README calls out, was not in it at all.

Cause: `run_checks.py` verified the deterministic path by running `screen.py --no-vision`, **which
wrote to `reports/`**. Every run of the verification suite silently replaced the committed full
run with a degraded one. A verification suite that corrupts the artifacts it verifies is worse
than no suite.

*Fixed:* `screen.py` gained `--reports-dir`, the check writes to scratch, and a new check asserts
the committed run is the full run so a degraded set cannot sit in `reports/` unnoticed.

## What this test does not establish

- **One document, one agent, one run.** Not a sample.
- **Synthetic corpus.** These charts were rendered from known values and are cleaner than a real
  scan.
- **Not a true install.** The agent read the plugin from the filesystem rather than having it
  installed through the marketplace, so command registration and skill auto-routing are still
  unverified.
- **No gate was actually answered**, so stages 4 through 7 — market context, the memo, the
  hand-back — remain untested end to end.
- The agent disclosed one judgement call: it wrote its own pixel-measurement script outside the
  repo, which it judged inside the spirit of the permitted rasterisation step. Recorded here
  rather than buried.
