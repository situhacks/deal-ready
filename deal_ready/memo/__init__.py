"""The memo stage: everything up to first draft, with the uncertainty left in.

See docs/callouts.md for the design record. Two rules govern this package:

1. Every number in a drafted memo is injected verbatim from code-computed results.
   The model never writes a figure; it writes observations, and each observation
   ships with a call-out id attached.
2. Where there is no measurement there is no confidence number. Axis-read values
   carry the rate measured on the committed eval (reports/layer_p.json, quoted live);
   narrative judgement carries nothing.
"""
