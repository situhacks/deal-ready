---
description: Screen a CIM end to end - cited scorecard, market context, drafted memo. Pauses for you at each gate.
argument-hint: <path-to-cim.pdf>
---

Screen the CIM at `$1`.

Load the `cim-screen` skill and follow it exactly. It defines the five stages, the three
human gates, and what each stage writes.

If `$1` is empty, ask which file to screen before doing anything else.

Run the whole thing in this one conversation. Do not ask the operator to invoke another
command to continue - when a gate is reached, present the gate and wait for their reply,
then carry on from where you stopped.
