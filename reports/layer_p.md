# Layer P - what each parse backend makes available

Percentage of ground-truth fields recovered **and correctly attributed** to their metric, on the page the value actually lives on. This grades the parser, not the extractor: it is a ceiling on what any downstream model could achieve given what it was handed.

| Field type | textlayer | vision:minicpm-v4.6:latest | pipeline:glm-ocr->[qwen3.8:27b+geometry] |
|---|---|---|---|
| Prose (narrative claims) | 100% (10/10) | 100% (10/10) | 100% (10/10) |
| Table cells | 100% (20/20) | 100% (20/20) | 100% (20/20) |
| Chart-only values | 0% (0/20) | 50% (10/20) | 100% (20/20) |

## The chart row, split by whether the chart printed its values

This is the finding the aggregate hides. Reading a printed data label is recognition. Reading a value off an axis is spatial reasoning about where a point sits between gridlines. They are different tasks, and they fail differently.

| Backend | Charts with data labels | Charts read off the axis |
|---|---|---|
| `textlayer` | 0% (0/10) | 0% (0/10) |
| `vision:minicpm-v4.6:latest` | 100% (10/10) | 0% (0/10) |
| `pipeline:glm-ocr->[qwen3.8:27b+geometry]` | 100% (10/10) | 100% (10/10) |

**A value read off an axis is measured, and still flagged.** The v1 configuration landed around 70% on the axis column: the strong tier was burning its budget inside a thinking block and reading a lossy page render. In the current pipeline the axis column comes from code-measured geometry, and it reads in full on the committed eval. Every axis-read value still ships flagged - a measured value is not a printed one, and the flag is where the human signs.
