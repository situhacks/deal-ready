"""Page routing - decide which pages are worth reading before paying to read them.

The economic argument this repo is really about:

    Vector search is arithmetic. Reading is inference.
    Embedding 60 pages once and searching them costs no model tokens at query time.
    Reading one page with a vision model costs ~1,500 input tokens and ninety seconds.

So retrieval is not there to be clever. It is there to keep the expensive step small.

**Routing and reading are separable, and conflating them is the common mistake.**
An embedding never reads a table; it decides which page a reader should look at. That
distinction decides which kind of embedding you need:

- Where a page carries text that *describes* what it shows - a heading reading
  "Retention", a sentence about gross and net retention - **text embeddings over the
  text layer are enough to find it**, even when the numbers themselves live only in a
  chart on that page. Cheap, local, no GPU.
- Where a page carries no indicative text at all - an unlabelled exhibit, a scanned
  appendix, a slide that is nothing but a plot - text routing is blind and **visual
  retrieval (ColPali family, e.g. ColModernVBERT) earns its cost**.

This module implements the first, measures it, and reports the result honestly. If
text routing already recovers the pages, saying so is worth more than reaching for
late interaction because it sounds better. `docs/ingest.md` records where the line
sits and what changes at data-room scale.

Single-vector cosine, brute force, in numpy. At 60 pages that is a matmul of trivial
size; a vector database here would be infrastructure bought to solve nothing.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..models import ollama

DEFAULT_EMBED_MODEL = "nomic-embed-text:latest"

# What an analyst is actually looking for, per metric. Deliberately phrased as
# natural questions rather than keyword bags: the point is to test retrieval, and
# handing it the exact page wording would be marking our own homework.
METRIC_QUERIES = {
    "arr_usd": "annual recurring revenue ARR for the most recent fiscal year",
    "mrr_usd": "monthly recurring revenue MRR exit month",
    "recurring_pct": "what share of total revenue is recurring subscription revenue",
    "grr_pct": "gross revenue retention rate excluding expansion",
    "nrr_pct": "net revenue retention including expansion and upsell",
    "gross_margin_pct": "gross margin percentage",
    "ebitda_usd": "adjusted EBITDA profitability",
    "yoy_growth_pct": "year over year revenue growth rate",
    "top1_customer_pct": "largest single customer share of annual recurring revenue, customer concentration",
    "top5_customer_pct": "top five customers combined share of annual recurring revenue concentration",
}


@dataclass
class RouteResult:
    metric: str
    query: str
    ranked_pages: list[int]
    scores: list[float]

    def top_k(self, k: int) -> list[int]:
        return self.ranked_pages[:k]

    def rank_of(self, page: int) -> int | None:
        """1-indexed rank of `page`, or None if absent."""
        return self.ranked_pages.index(page) + 1 if page in self.ranked_pages else None


def _l2(a: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(a, axis=-1, keepdims=True)
    return a / np.clip(n, 1e-12, None)


def embed_pages(page_texts: dict[int, str], model: str = DEFAULT_EMBED_MODEL):
    """Embed each page's text. Returns (page_numbers, matrix) or None if unavailable.

    Empty pages are kept in the index rather than dropped. A page that contributes
    nothing should be *outranked*, not hidden - hiding it would flatter recall by
    shrinking the haystack.
    """
    pages = sorted(page_texts)
    texts = [page_texts[p].strip() or "(this page contains no extractable text)"
             for p in pages]
    vecs = ollama.embed(model, texts)
    if not vecs:
        return None
    return pages, _l2(np.asarray(vecs, dtype=np.float32))


def route(page_texts: dict[int, str], metrics: list[str] | None = None,
          model: str = DEFAULT_EMBED_MODEL) -> dict[str, RouteResult] | None:
    """Rank every page against every metric query."""
    idx = embed_pages(page_texts, model)
    if idx is None:
        return None
    pages, page_mat = idx

    metrics = metrics or list(METRIC_QUERIES)
    queries = [METRIC_QUERIES[m] for m in metrics]
    qvecs = ollama.embed(model, queries)
    if not qvecs:
        return None
    q_mat = _l2(np.asarray(qvecs, dtype=np.float32))

    sims = q_mat @ page_mat.T           # (metrics x pages) - the whole search
    out: dict[str, RouteResult] = {}
    for i, metric in enumerate(metrics):
        order = np.argsort(-sims[i])
        out[metric] = RouteResult(
            metric=metric,
            query=METRIC_QUERIES[metric],
            ranked_pages=[pages[j] for j in order],
            scores=[round(float(sims[i][j]), 4) for j in order],
        )
    return out


def pages_to_read(routes: dict[str, RouteResult], k: int) -> list[int]:
    """Union of the top-k pages across all metrics - what a router would actually send."""
    sel: set[int] = set()
    for r in routes.values():
        sel.update(r.top_k(k))
    return sorted(sel)
