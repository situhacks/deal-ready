# Layer R - page routing

Does the router rank the page that actually carries each value inside the top k? Ground truth is the page the generator planted it on.

## Read the carrier breakdown, not the aggregate

The headline recall@1 across all fields is **50%**, and on its own that number is misleading. Routing only has a job to do for fields the text layer cannot read. Split by carrier:

| Carrier | recall@1 | Does routing matter here? |
|---|---|---|
| **Chart-only** | **100% (20/20)** | **Yes - these are the only fields that need a vision model** |
| Table | 25% (5/20) | No - text layer already recovers these at 100% |
| Prose | 0% (0/10) | No - same |

**Routing is perfect exactly where it is needed and irrelevant everywhere else.** Chart pages carry headings and prose describing what they show ("Retention", "Customer base"), so cheap text embeddings find them at rank 1 every time - even though the values themselves are pixels. Prose and table fields rank poorly and it costs nothing, because they were never going to the vision model.

That is also the argument for *not* reaching for visual retrieval here. It earns its cost when a page has no indicative text at all - an unlabelled exhibit, a scanned appendix - which is a data-room problem, not a single-CIM problem. See docs/ingest.md section 5.

## What it saves

| k | pages selected | reduction | vision tokens | wall clock |
|---|---|---|---|---|
| 1 | 15/60 | 75% fewer | ~22,500 vs 90,000 | ~4.8 min vs 19.0 min |
| 2 | 15/60 | 75% fewer | ~22,500 vs 90,000 | ~4.8 min vs 19.0 min |
| 3 | 24/60 | 60% fewer | ~36,000 vs 90,000 | ~7.6 min vs 19.0 min |

At k=1 the expensive step runs on **15 of 60 pages** and no chart field is missed. Reading is what costs; finding is what is cheap.

