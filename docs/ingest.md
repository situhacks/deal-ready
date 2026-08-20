# How a CIM becomes data

This is the design record for the parsing layer: what was tried, what was measured,
what was rejected, and where the answer would change at a different scale.

It exists because the parse decision is the one most often made by reflex. "We'll OCR
the PDFs" and "we'll just send it to a multimodal model" are both defensible-sounding
and both wrong here, in opposite directions, and the difference shows up as deal risk
rather than as an accuracy metric.

---

## 1. The finding that motivates everything else

A CIM is a deck. Its numbers do not all live in sentences.

In this corpus, **20 of 50 metrics — 40% — exist only inside rasterised charts.** They
were placed there deliberately and verified absent from the text layer by a leak check
that fails the build if one escapes ([`generate.py`](../generate.py)). So the split is
a property of the experiment, not an accident of it.

The 40% is not a random 40%:

| Chart-carried metric | Why it matters to a permanent-capital buyer |
|---|---|
| Gross revenue retention | The honest measure of whether customers stay |
| Net revenue retention | Whether the base grows without new logos |
| Largest customer % of ARR | One departure, one permanent hole |
| Top five customers % of ARR | Whether revenue quality rests on a handful of relationships |

**Every metric that decides the deal is in a picture.** Revenue, margin and EBITDA —
the figures a text layer reads perfectly — tell you how big the company is. The chart
metrics tell you whether to buy it.

### What that costs, measured end to end

Running the screener with `--no-vision`, so only the text layer is used:

| Target | Text-only score | Tier |
|---|---|---|
| Meridian — clean business | 60.0 | Tier 2 |
| Halyard — **34% single-customer concentration** | 60.0 | Tier 2 |
| Ashgrove — **81% gross retention, below floor** | 60.0 | Tier 2 |

Three companies with materially different risk, three identical scores. A text-only
pipeline does not degrade gracefully here; it goes blind precisely where the decision
lives, and it does so *silently* — every field it did read, it read correctly.

That is the case for a heavier parser. Not "vision models are better at tables."

---

## 2. Why OCR is the wrong default

OCR converts pixels to characters. That is a different job from understanding a page,
and the gap shows up in three ways:

- **Tables lose their structure.** OCR can detect the characters in a table and still
  lose which row and column they belonged to. A number without its row label is not a
  recovered figure, it is a number waiting to be misread.
- **Pages are read in isolation.** A metric defined on page 4 and referenced on page 31
  never connects.
- **Charts yield labels, not values.** Where a chart carries no printed data labels,
  the value must be read off an axis — which requires understanding the plot, not
  recognising glyphs.

The scoring here grades both `present` and `attributed` for exactly this reason, and
reports **attributed**. "34%" alone does not count.

**A deliberate nuance in the corpus.** Real CIM charts are inconsistent: pie and bar
charts usually carry data labels, trend lines often do not. This corpus mirrors that —
the concentration chart is labelled, the retention chart is not. It gives OCR a case it
can partially win (recovering digits while losing the series they belong to), which is
a more truthful result than a flat zero.

---

## 3. Why "send the whole PDF to a multimodal model" is also wrong

It works, and it is wasteful in a way that compounds.

Attention spreads across mostly-irrelevant pages and you pay for every one of them.
Published work on field extraction from large financial documents found a staged
pipeline — cheap pass for retrieval, then a compact vision model on the narrowed scope
— beating whole-document VLM calls by roughly **8.8× on field-level accuracy at about
0.7% of the GPU cost**, with ~93% lower latency
([arXiv 2510.23066](https://arxiv.org/abs/2510.23066)).

Accuracy and cost move *together* here, which is the part people miss. Reading less
carefully is not the trade for reading cheaply; reading the right pages is both.

---

## 4. The routing rule

Route by what the page actually is, rather than picking one parser for everything:

| What you are handed | Path | Why |
|---|---|---|
| Born-digital text (most prose, most tables) | Extract the text layer | Lossless, free, and gives exact character spans — which is what a citation is |
| Scanned or image-only pages | OCR as a **retrieval index**, never as the extraction | Good enough to find the page, never good enough to key a number from |
| Charts, plots, visual exhibits | Rasterise the page, read it with a vision model | The layout carries the meaning |
| The whole document at once | Only when the question genuinely spans it | The expensive default |

**Provenance is the constraint that drives all of it.** Every field returns
`{value, page, span_or_bbox, method}`. In diligence the citation *is* the deliverable —
a deal lead checks the source, not the tool's word — so any parser that cannot say
where a number came from has failed regardless of accuracy.

---

## 5. Retrieval: what embeddings do and do not do

The most common confusion in this territory, stated plainly:

> **Embeddings do not read tables. They decide which page to read.**
> Vector search is arithmetic; reading is inference. Embedding a corpus once costs no
> model tokens at query time. Reading one page with a vision model costs ~1,500 input
> tokens and, on this hardware, ~16 seconds.

Retrieval is not there to be clever. It is there to keep the expensive step small.

### Measured: text-embedding routing is sufficient here

Page routing with `nomic-embed-text` over the text layer, on Halyard:

| Metric | Carrier | True page | Router rank |
|---|---|---|---|
| GRR, NRR | chart | 7 | **1** |
| Top-1, Top-5 concentration | chart | 6 | **1** |
| ARR, MRR, margin, EBITDA | table | 8 | 1–2 |
| Recurring %, growth | prose | 2 | 6–8 |

Two things follow. **Text routing finds the chart pages at rank 1** — because those
pages carry text that *describes* what they show ("Retention", "Customer base") even
though the values themselves are pixels. And the prose metrics routing poorly does not
matter, because the text layer already reads them at 100%.

A k=1 router selects **3 of 12 pages**. The expensive step shrinks by 75%, and nothing
is lost.

### Where visual retrieval would earn its cost

Not here. It earns it when a page carries **no indicative text at all** — an unlabelled
exhibit, a scanned appendix, a slide that is nothing but a plot — because then text
routing is blind. That is a data-room problem, not a single-CIM problem.

The corpus-size ladder:

| Scale | Right tool | Why |
|---|---|---|
| One CIM, ~12–60 pages | Read the pages a text router selects | Indexing costs more than reading |
| A dealbook, ~50 CIMs | Retrieve over the structured records already extracted | The visual content has already been converted |
| A data room, 10–50K pages | **Visual late-interaction retrieval (ColPali family)** | Finding the page *is* the problem |

And the honest cost of that last row, so the restraint reads as measurement rather than
avoidance: ColPali-family indexes run **~100–500KB per page**, exceed **150GB at ~400K
documents**, are roughly **two orders of magnitude slower** than single-vector search
because late interaction is exhaustive, and need Vespa or Milvus with custom MaxSim
scoring.

**There is no vector database in this repo, and that is the point.** Late interaction
over 60 pages is a numpy matmul of about 31MB. Reaching for the infrastructure before
the crossover is how a prototype acquires an operations burden it never needed.

---

## 6. What was tried, and what it cost

| Option | Verdict |
|---|---|
| **Text layer** (`pypdf`) | **Kept.** 100% on prose and table fields, 0% on charts. Free, exact spans |
| **OCR** (Tesseract) | Optional, feature-gated. Skips cleanly when absent; shipped to be beaten on the record rather than dismissed |
| **`qwen3-vl:8b`** via Ollama | **Kept as the vision backend.** Reads unlabelled trend charts off the axis, with attribution |
| **`gemma4:latest`** | **Rejected.** Advertises `vision` in `ollama show`, then answers "please provide the page you would like me to transcribe" for an image sent through either `/api/generate` or `/api/chat` — the identical payload qwen3-vl reads without complaint |
| **Gemini Embedding 2** (managed, natively multimodal) | **Not built.** Would buy nothing at this corpus size and would cost a reader an API key to evaluate the repo at all |
| **Baidu Unlimited-OCR** (MIT, VLM-based despite the name) | **Not built.** The credible self-hosted parser for a client whose NDA forbids third-party AI on the data room; needs a torch/transformers stack rather than the Ollama path that already works here |
| **ColModernVBERT** (250M, MIT, CPU-efficient) | **Not built, and it could not have substituted for the VLM anyway** — it is a *retriever*. Its moment is the data-room row above |

---

## 7. Two failures worth writing down

Both were live during the build, both would have published a false finding, and both
are the kind of thing that gets silently absorbed.

**A cached timeout looks exactly like a model that cannot do the task.** A vision call
hit a 300-second ceiling under GPU contention and the empty result was written to
cache. Downstream that is indistinguishable from "the model looked and found nothing"
— it would have scored as a miss and published "vision cannot read charts". The fix is
structural, not a longer timeout: **only successes are cached**, so a failure retries
instead of hardening into a result.

**`num_predict` is a trap on a thinking model.** qwen3-vl emits ~10,000 characters of
reasoning before ~350 characters of transcription, and `/no_think` does not suppress it
through Ollama. Cap the budget below the thinking and the call returns an **empty
string** with `done_reason="length"` — no error, no warning.

And one operational note with a large coefficient: the same page took **220 seconds
while other models were resident on the GPU and 16 seconds once they were not.** A 13×
swing on identical work. Any benchmark that does not control for model residency is
measuring the machine's mood.

---

## 8. What would change at data-room scale

The screener's answer is not the diligence answer, and the difference is worth stating
before someone assumes it generalises:

- **Retrieval becomes the bottleneck**, so visual late-interaction earns its index cost
  and a vector store stops being overhead.
- **Coverage replaces accuracy as the headline.** For contract review the claim is
  "100% first-pass coverage, human verification on every flag plus an N% sample of the
  no-flag pile" — never "the AI cleared the contracts."
- **Build-versus-buy flips.** Hebbia, Kira and Luminance own that category with
  pre-trained clause models. The honest first deliverable there is a benchmark against
  an incumbent on a closed deal's data room, where the findings are already known and
  ground truth is free.
