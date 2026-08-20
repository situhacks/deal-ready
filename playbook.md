# Running this on a real deal team

A tool that works and is not used has failed. This is the rollout half, written as
plainly as the code.

## Where it sits

A CIM arrives from a banker. Today an analyst spends two to four hours keying ten
numbers into a spreadsheet and writing a one-pager, and around nine in ten of those
memoranda end in "pass". The screen is not the hard thinking — it is the volume that
crowds out the hard thinking.

This slots in before the analyst opens the deck, not instead of it:

```
CIM arrives
   → screen.py produces a cited scorecard in minutes
   → the analyst reads the scorecard first, then the deck
   → flags become the management-call question list
   → the scorecard rides along as an IC pre-read appendix
   → the banker sends corrected numbers → re-run → diff the findings
```

The shrinking flag list between versions is the progress bar on a live deal.

## Rollout: shadow mode first

Do not ask anyone to trust it. Run it **beside** the analyst's manual read for the
first few weeks and compare.

1. **Shadow.** Every CIM gets screened; the analyst works as they always have. Log
   where the tool and the human disagree. Disagreements are the product at this stage —
   each one is either a rule that is wrong or a document that is unusual, and both are
   worth knowing.
2. **Compare, don't announce.** After three or four weeks you have a real number for
   time-per-screen and a list of the tool's actual failure modes. That is what earns
   the next conversation.
3. **Promote to triage ordering.** The tool decides what gets read first, not what gets
   killed. Reordering an inbox is reversible within a day; killing a deal is not.
4. **Never promote past the decision.** The tier sorts. The LOI decision stays human,
   permanently. This is not a caution to be relaxed later — it is the design.

## Who to build with

One deal lead, on live deals, from day one. Not a committee and not a pilot cohort.

Adoption in this kind of work is practitioner-led: the person whose Tuesday got shorter
tells the next person, and that carries further than any rollout plan. The rule of thumb
that holds up: **build against a live deal, let the result recruit the next user.**

## What to measure

Two numbers, one of each kind, from the first week:

- **The eval number.** Field-level recovery and rule coverage, from `run_checks.py`.
  This is whether the machine works.
- **The business number.** Minutes per screen, and screens per analyst per week. This is
  whether it matters.

Then one more that people forget: **the override rate.** How often does the analyst
disagree with the tier? Rising override is not a failure — it is the signal that the
criteria profile needs tuning, and `criteria/default.json` is config precisely so that
tuning is a five-minute change rather than a ticket.

## What will actually go wrong

- **Input variance, not the model.** Every banker formats a CIM differently. That is why
  normalisation is its own layer in front, and why the validator never loosens to
  accommodate mess — a check that can't fail isn't a check.
- **Silence gets read as endorsement.** "No flags found" must always render as *what was
  checked and found nothing*, never as "clean". The wording matters more than it sounds.
- **The narrative risks stay invisible.** Founder dependency, legacy stack, a settlement
  engine one person understands: none of it is arithmetic. Until a calibrated judgement
  layer exists and is scored on held-out labels, a human reads the document. Say so out
  loud, repeatedly, or people will stop doing it.

## What this is not

It does not recommend a transaction. It produces the artifact an analyst was going to
build by hand, with every figure traceable to the page it came from, faster and more
consistently — and hands the judgement back.

A `Pass` means "not a fit against this profile". It never means "bad company".
