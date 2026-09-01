---
description: Check a human-filled scorecard against the source document. Reports disagreed, agreed, and could-not-check.
argument-hint: <path-to-cim.pdf> <path-to-asserted-values.json|csv|yaml>
---

Run reviewer mode: check the asserted values in `$2` against the document at `$1`.

Load the `review-check` skill and follow it exactly.

This mode does not draft anything and does not score. It reports three buckets and stops.
Silence is never a verdict: if a value could not be checked, it goes in the third bucket
and is named.

If either argument is missing, ask for it before reading anything.
