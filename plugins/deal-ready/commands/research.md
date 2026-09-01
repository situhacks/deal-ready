---
description: Build market context for a target - benchmark bands, comparables, and what would compress the multiple.
argument-hint: <target-name-or-findings.json>
---

Build market context for `$1`.

Load the `market-context` skill and follow it exactly. It runs a scoped four-phase
research pass and returns cited benchmark bands and comparables.

The researcher never reads the CIM. If `$1` is a findings file, take only the metric
names, their values, and the vertical from it - never the document text.

If `$1` is empty, ask which target to research.
