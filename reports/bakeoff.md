# Reader bake-off - candidates vs the incumbent, identical grading

Graded 150 field-page pairs. Single-pass candidates: full page at 120 DPI, production transcription prompt, temperature 0, per-model caches committed. References from reports/layer_p.json: `vision:minicpm` is the incumbent's single-pass equivalent; `tiered` is the full production pipeline (cheap page read, exhibit re-reads, measured chart geometry).

| Backend | Prose | Table | Chart (labelled) | Chart (axis) | s/page |
|---|---|---|---|---|---|
| `vision:glm-ocr` | 100% (10/10) | 100% (20/20) | 100% (10/10) | 0% (0/10) | 5.0 |
| `vision:deepseek-ocr` | 0% (0/10) | 100% (20/20) | 0% (0/10) | 0% (0/10) | 18.4 |
| `vision:qwen3.8:27b` | 80% (8/10) | 100% (20/20) | 100% (10/10) | 80% (8/10) | 148.4 |
| `vision:minicpm-v4.6:latest` (incumbent, single-pass) | 100% | 100% | n/a | n/a | see layer_p |
| `tiered:minicpm-v4.6:latest->qwen3.5:4b` (incumbent, full pipeline) | n/a | n/a | n/a | n/a | see layer_p |

Chart columns for single-pass candidates are expected to be weak - no parser reads chart interiors (ParseBench 2026: most under 6%), and the production pipeline gets its axis column from code-measured geometry, not from any single model. The swap question is prose/table fidelity, callout survival (T05 top-five share), and speed; chart geometry is retained regardless of which reader wins.

## Configuration notes

- `deepseek-ocr`: port rejects prompts over ~50 chars; graded on the 40-char core
- `qwen3.8:27b`: newest open general multimodal; the just-use-the-best-reader test

## Not run

- (none)
