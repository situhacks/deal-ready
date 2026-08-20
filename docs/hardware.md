# Running the local models

Nothing here needs a GPU. The deterministic path — generate, validate, score, and the
whole check suite — is plain Python and runs anywhere. The vision and routing steps
want a local model, and this page is what would otherwise cost you an evening.

## What was used

| | |
|---|---|
| GPU | AMD Radeon RX 6900 XT, 16GB (gfx1030) |
| Runtime | Ollama 0.32.14, Windows |
| Vision | `minicpm-v4.6` — 1B, 1.6GB pull |
| Escalation | `qwen3.5:4b` — for charts with no printed data labels |
| Routing | `nomic-embed-text` — 274MB |
| Full corpus pass | 20 pages, ~6.4 minutes |

Total download to reproduce the vision results: **under 2GB**. That was a deliberate
choice — see [`ingest.md`](ingest.md) for the measurements behind it.

## AMD, and the part that wastes people's evenings

ROCm support differs sharply *within* RDNA 2, which is why "it works on AMD" is not a
useful statement on its own:

- **gfx1030 (RX 6800 / 6900 XT)** is natively supported. Nothing to configure.
- **gfx1031 / gfx1032 (RX 6700 / 6600 series)** are not. They map to gfx1030 via
  `HSA_OVERRIDE_GFX_VERSION=10.3.0` — except **ROCm 6.4.3 and later shipped a
  regression** where those cards load a model and then segfault on the first prompt,
  silently falling back to CPU. It is the most common "I followed every guide and it
  still doesn't work" report for AMD in 2026, and it is not your fault.

If you are on one of those cards, in order of reliability: set `OLLAMA_VULKAN=1` to
bypass ROCm entirely; or pin a pre-6.4.3 ROCm; or use a rebuilt-library fork.

**The repo does not care which of those you did.** Every model call goes through
`deal_ready/models/ollama.py`, every call has a timeout, and a failure returns a
structured miss. A backend that cannot reach a model prints "not run" — never a zero.

## Three traps, all of which bit during the build

**1. A cached timeout is indistinguishable from a model that found nothing.**
A vision call hit a 300-second ceiling under GPU contention, and the empty result was
written to cache. Downstream that scores as a miss and publishes "vision cannot read
charts" — an infrastructure failure dressed as a capability finding. The fix is
structural rather than a longer timeout: **only successes are cached**, and
`run_checks.py` enforces it.

**2. `num_predict` silently truncates a thinking model into an empty answer.**
`qwen3-vl:8b` emits ~10,000 characters of reasoning before ~350 characters of
transcription, and `/no_think` does not suppress it through Ollama. Cap the budget
below the thinking and the call returns an **empty string** with
`done_reason="length"` — no error, no warning. This is most of why the 1B default was
chosen: it does not think, so it cannot be truncated mid-thought.

**3. Model residency dominates timing by more than model choice does.**
The same page took **220 seconds while other models were resident on the GPU and 16
seconds once they were not** — a 13× swing on identical work. Any benchmark that does
not control for what else is loaded is measuring the machine's mood. The adapter sends
`keep_alive: 30m` so a corpus pass does not pay a 1.6GB reload per page.

## Context length

8192 is sufficient and does not need raising. A page image costs ~1,500 input tokens
and a transcription ~500 out. Context was never the constraint here — thinking length
was.

## A model can advertise a capability it will not honour

`gemma4:latest` lists `vision` in `ollama show` and then replies *"please provide the
page you would like me to transcribe"* to an image sent through either
`/api/generate` or `/api/chat` — the identical payload the other models read without
complaint. Recorded rather than quietly dropped, because "we tried two and one did not
work" is information a reader deserves.

## No GPU at all?

Everything still runs:

```bash
python generate.py                  # no model
python screen.py data/ --no-vision  # deterministic path only
python run_checks.py                # verifies published numbers from committed artifacts
```

The vision cache is committed, so the Layer P numbers can be verified without running
a model at all. Regenerating the raw outputs needs local models; **verifying the
measurement does not.** That separation is deliberate — a reviewer who had to buy
hardware to check your numbers will simply not check them.
