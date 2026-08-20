# Layer P - what each parse backend makes available

Percentage of ground-truth fields recovered **and correctly attributed** to their metric, on the page the value actually lives on. This grades the parser, not the extractor: it is a ceiling on what any downstream model could achieve given what it was handed.

| Field type | textlayer | tiered:minicpm-v4.6:latest->qwen3.5:4b |
|---|---|---|
| Prose (narrative claims) | 100% (10/10) | 100% (10/10) |
| Table cells | 100% (20/20) | 100% (20/20) |
| Chart-only values | 0% (0/20) | 80% (16/20) |

## The chart row, split by whether the chart printed its values

This is the finding the aggregate hides. Reading a printed data label is recognition. Reading a value off an axis is spatial reasoning about where a point sits between gridlines. They are different tasks, and they fail differently.

| Backend | Charts with data labels | Charts read off the axis |
|---|---|---|
| `textlayer` | 0% (0/10) | 0% (0/10) |
| `tiered:minicpm-v4.6:latest->qwen3.5:4b` | 90% (9/10) | 70% (7/10) |

**A value read off an axis is not yet trustworthy enough to act on.** Even with escalation to a larger model it lands around 70% here - useful for triage, not acceptable for a figure that reprices a deal. The consequence is not a better prompt. It is to treat axis-read values as **flagged for human confirmation**, and to ask the seller for the underlying data rather than inferring it from a picture.
