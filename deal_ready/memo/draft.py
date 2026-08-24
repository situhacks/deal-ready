"""Draft a screening memo from a screened CIM, with call-outs attached.

The scorecard stops at arithmetic; the memo is where an analyst would start writing.
This module produces that first draft - every figure cited, every uncertain value
flagged, every narrative observation marked as judgement - so the reviewer edits a
document instead of interrogating a JSON file.

Division of labour, unchanged from the rest of the pipeline:

    code    computes every number, decides every value flag (axis_read, missing,
            definition conflict) from mechanical facts about how the value was read
    model   writes connective prose and up to five narrative observations, each
            wrapped in a call-out so a human can accept, edit or reject it
    human   corrects the draft; corrections are captured by capture.py and fold back

The model's observations come from the document text alone. It sees no ground truth,
no scores, no rule verdicts beyond their headlines - it is the "read the narrative"
pass the README names as not built yet, shipped here as flagged suggestions rather
than findings for exactly that reason.

Fold-back: accepted judgement corrections land in eval/judgement_examples.json and
are injected into later prompts as worked examples. That is the whole recursion - a
gated release cadence, not runtime self-modification.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from ..models import ollama
from ..scorer.rules import BLOCKER, WARNING

JUDGE_MODEL = "qwen3.5:4b"

METRIC_LABELS = {
    "arr_usd": "ARR",
    "mrr_usd": "MRR",
    "recurring_pct": "Recurring revenue share",
    "gross_margin_pct": "Gross margin",
    "ebitda_usd": "EBITDA",
    "yoy_growth_pct": "YoY growth",
    "grr_pct": "Gross revenue retention",
    "nrr_pct": "Net revenue retention",
    "top1_customer_pct": "Largest customer share",
    "top5_customer_pct": "Top-five customer share",
}

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES_PATH = ROOT / "eval" / "judgement_examples.json"


def _axis_read_rate() -> int | None:
    """The measured recovery rate for axis-read values, from the committed Layer P.

    The flag quotes the measurement instead of a hardcoded ceiling: whatever the
    committed eval says the strong tier achieves on unlabelled charts is the number
    the call-out carries, so the flag cannot drift from the evidence. None (report
    absent) degrades to an unnumbered flag - the confirmation request survives, the
    false precision does not.
    """
    p = ROOT / "reports" / "layer_p.json"
    if not p.exists():
        return None
    try:
        rep = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    n = att = 0
    for r in rep.get("rows", []):
        if (r.get("carrier") == "chart" and r.get("labelled_in_chart") is False
                and str(r.get("backend", "")).startswith(("tiered", "pipeline"))):
            n += 1
            att += int(r.get("attributed", 0))
    return round(100 * att / n) if n else None


def _money(v) -> str:
    sign = "-" if v < 0 else ""
    a = abs(v)
    return f"{sign}${a/1_000_000:.1f}M" if a >= 1_000_000 else f"{sign}${a:,.0f}"


def fmt_metric(metric: str, v) -> str:
    if v is None:
        return "not stated"
    if metric.endswith("_pct"):
        return f"{v:g}%"
    if metric.endswith("_usd"):
        return _money(v)
    return str(v)


# Where a missing metric's name appears in the document near a page the vision
# tier actually read, "deliberately omitted" is the wrong default reading - the
# exhibit probably exists and defeated the parser. First taught by review session
# T05_session01: p7 announces "Gross and net revenue retention, FY22 to FY25" while
# both values came back unrecovered. Ground-truth-free: page text plus the cache.
MISSING_EXHIBIT_HINTS = {
    "grr_pct": [r"gross\s+revenue\s+retention", r"gross\s+retention"],
    "nrr_pct": [r"net\s+revenue\s+retention", r"net\s+retention"],
    "top1_customer_pct": [r"largest\s+customer", r"top\s+customer"],
    "top5_customer_pct": [r"top\s+(five|5)\s+customers"],
}


def _exhibit_page_for(metric: str, page_texts: dict[int, str] | None,
                      read_pages: set[int]) -> int | None:
    import re as _re
    if not page_texts:
        return None
    hints = MISSING_EXHIBIT_HINTS.get(metric, [])
    for pg in sorted(page_texts):
        if not any(_re.search(h, page_texts[pg], _re.I) for h in hints):
            continue
        if pg in read_pages or _re.search(r"chart|graph|figure|exhibit|axis",
                                          page_texts[pg], _re.I):
            return pg
    return None


def derive_callouts(result: dict, page_texts: dict[int, str] | None = None) -> list[dict]:
    """Value-level call-outs, derived mechanically. No model self-reporting.

    Kinds follow docs/callouts.md. Everything here is computable from the screen
    result and the committed vision cache, which is what makes call-out precision a
    measurable quantity once corrections exist.
    """
    tid = result["target_id"]
    out: list[dict] = []
    counters: dict[str, int] = {}

    def add(kind: str, **kw) -> str:
        counters[kind] = counters.get(kind, 0) + 1
        cid = f"co-{tid}-{kind}-{counters[kind]:03d}"
        out.append({"id": cid, "kind": kind, **kw})
        return cid

    # Vision-read values: axis_read when the value was interpolated from chart
    # geometry, label_read when it came off a printed label. The signal is the
    # screen's own citation record, not cache sniffing - which also fixes the old
    # heuristic's habit of flagging labelled charts on pages that happened to
    # escalate for another reason.
    rate = _axis_read_rate()
    for m, cite in result["citations"].items():
        if cite.get("method") != "vision":
            continue
        if cite.get("read") == "axis":
            measured = (f" (reader measured {rate}% on the committed eval)"
                        if rate is not None else "")
            xc = cite.get("crosscheck")
            crosschecked = ""
            if xc:
                if xc.get("all_agree"):
                    worst = max((r["delta"] for r in xc["pairs"]), default=0)
                    crosschecked = (f" Independent re-read by {xc['model']} agrees "
                                    f"with the measurement within {worst:g}.")
                else:
                    detail = "; ".join(f"{r['label']}: model read {r['read']:g}, "
                                       f"measured {r['measured']:g}"
                                       for r in xc["pairs"] if not r["agree"])
                    crosschecked = (f" Independent re-read by {xc['model']} "
                                    f"DISAGREES ({detail}) - resolve before use.")
            add("axis_read", metric=m, confidence_pct=rate,
                evidence_page=cite.get("page"),
                question=f"{METRIC_LABELS.get(m, m)} was interpolated from chart "
                         f"geometry, not printed on the page{measured}."
                         f"{crosschecked} Confirm or replace")
        else:
            add("label_read", metric=m, confidence_pct=None,
                evidence_page=cite.get("page"),
                question=f"{METRIC_LABELS.get(m, m)} came from a printed chart label")

    # Definition conflicts first-class: the seller mislabelled a metric.
    for f in result["findings"]:
        if f["rule_id"] == "grr_above_100":
            add("definition_conflict", metric="grr_pct", confidence_pct=None,
                evidence_page=(f.get("citation") or {}).get("page"),
                question="Reported gross retention exceeds 100% - net retention has "
                         "been labelled gross; reconcile before it reaches the model")

    # Missing core metrics: absence is information, frame the question. When the
    # metric's name sits on a page the vision tier read, say what actually happened:
    # an exhibit exists and no reliable value came back from it.
    vision_pages = set(result.get("pages_read_with_vision") or [])
    vision_pages |= {c.get("page") for c in result["citations"].values()
                     if c.get("method") == "vision"}
    for f in result["findings"]:
        if f["rule_id"] != "metrics_not_stated":
            continue
        for m in f["values"]["missing"]:
            ex_pg = _exhibit_page_for(m, page_texts, vision_pages)
            if ex_pg is not None:
                q = (f"{METRIC_LABELS.get(m, m)} appears as a chart on p{ex_pg} but "
                     f"no reliable value could be read from it - request the "
                     f"underlying series")
            else:
                q = (f"{METRIC_LABELS.get(m, m)} is never stated - likely "
                     f"deliberate; make it the first management-call question")
            add("missing_metric", metric=m, confidence_pct=None,
                evidence_page=ex_pg, question=q)
    return out


def _load_examples() -> list[dict]:
    """Accepted judgement examples folded back from review sessions."""
    if EXAMPLES_PATH.exists():
        return json.loads(EXAMPLES_PATH.read_text(encoding="utf-8"))
    return []


def judge(doc_text: str, finding_headlines: list[str]) -> tuple[list[dict], str]:
    """The narrative pass. Returns (observations, status).

    The model observes; it does not compute and does not recommend. Every failure
    mode returns a structured miss - an unavailable model skips the section rather
    than degrading the memo silently.
    """
    if not ollama.available() or not ollama.has_model(JUDGE_MODEL):
        return [], "model unavailable - narrative pass skipped"

    examples = _load_examples()
    ex_lines = "\n".join(
        f'- "{{\\"observation\\": {json.dumps(e["observation"])}, '
        f'\\"evidence_page\\": {e["evidence_page"]}}}"  # accepted by a reviewer'
        for e in examples[-3:])

    system = (
        "You are a senior M&A analyst reading a confidential information memorandum "
        "for narrative risk that arithmetic cannot see: founder dependency, customer "
        "concentration behaviour, unsupported technology, thin management depth, "
        "definitions that flatter the numbers. You observe; you do not calculate, "
        "you do not recommend a transaction, you do not restate figures already in "
        "the document. Return at most 5 observations."
    )
    prompt = (
        "Document text follows, page-marked.\n\n"
        f"{doc_text[:14000]}\n\n"
        "Deterministic checks already flagged:\n"
        + "\n".join(f"- {h}" for h in finding_headlines)
        + "\n\nExamples of the calibre expected (from reviewers who accepted them):\n"
        + (ex_lines or "- (none yet)")
        + "\n\nReturn ONLY a JSON array, one object per observation:\n"
          '[{"observation": "<one sentence>", "evidence_page": <int>}]'
    )
    # think=False at the door: with reasoning enabled this model could spend the
    # whole num_predict inside an unterminated thinking block and return an empty
    # string - indistinguishable from a refusal. The strip below stays as a guard
    # for models that ignore the flag.
    reply = ollama.generate(JUDGE_MODEL, prompt, system=system, num_predict=2000,
                            think=False)
    if not reply.ok:
        return [], f"model call failed ({reply.error}) - narrative pass skipped"

    text = re.sub(r"<think>.*?</think>", "", reply.text, flags=re.S)
    m = re.search(r"\[.*\]", text, re.S)
    if not m:
        return [], "model returned no parseable array - narrative pass skipped"
    try:
        raw = json.loads(m.group(0))
        obs = [{"observation": str(o["observation"]).strip(),
                "evidence_page": int(o.get("evidence_page") or 0)}
               for o in raw if isinstance(o, dict) and o.get("observation")]
        return obs[:5], "ok"
    except (json.JSONDecodeError, KeyError, TypeError):
        return [], "model output malformed - narrative pass skipped"


def render_memo(result: dict, criteria: dict, callouts: list[dict],
                observations: list[dict], judge_status: str,
                examples_folded: int) -> tuple[str, list[dict]]:
    """Assemble the markdown memo. Returns (markdown, all_callouts) - the judgement
    ids are minted here because they belong to specific sentences."""

    tid = result["target_id"]
    fit = result["fit"]
    by_kind: dict[str, list[dict]] = {}
    for c in callouts:
        by_kind.setdefault(c["kind"], []).append(c)

    lines: list[str] = []
    lines.append(f"# Screening memo — {result['code_name']} ({tid})")
    lines.append("")
    lines.append(f"*Drafted by deal-ready · {result['metrics_recovered']} metrics "
                 f"recovered · every figure cites its page · nothing here recommends "
                 f"a transaction.*")
    lines.append("")
    lines.append("## Verdict against the profile")
    lines.append("")
    lines.append(f"Fit score **{fit['score']:g}/100** against the "
                 f"\"{criteria['profile_name']}\" profile — {fit['tier_label']}.")
    if fit["blocked_by"]:
        lines.append(f"Blocked by: {', '.join(fit['blocked_by'])}.")
    lines.append("The score sorts an inbox; the flags below are the part worth "
                 "reading.")
    lines.append("")

    lines.append("## The numbers")
    lines.append("")
    lines.append("| metric | value | source |")
    lines.append("|---|---|---|")
    axis_ids = [c for c in by_kind.get("axis_read", [])] + \
               by_kind.get("label_read", [])
    cited = {c["metric"]: c for c in axis_ids}
    for m, v in result["metrics"].items():
        cite = result["citations"].get(m, {})
        src = f"p{cite.get('page')}, {cite.get('method')}"
        cell = fmt_metric(m, v)
        c = cited.get(m)
        if c:
            note = ("chart axis — confirm" if c["kind"] == "axis_read"
                    else "chart label")
            cell += f" ({note} <!--{c['id']}-->)"
        lines.append(f"| {METRIC_LABELS.get(m, m)} | {cell} | {src} |")
    lines.append("")

    flags = [f for f in result["findings"] if f["severity"] in (BLOCKER, WARNING)]
    infos = [f for f in result["findings"] if f["severity"] not in (BLOCKER, WARNING)]
    if flags:
        lines.append("## What the rules flagged")
        lines.append("")
        for f in flags:
            pg = (f.get("citation") or {}).get("page")
            where = f" (p{pg})" if pg else ""
            lines.append(f"- **{f['severity'].upper()}** — {f['headline']}{where}. "
                         f"{f['detail']}")
        lines.append("")
    if infos:
        lines.append("<details><summary>Context notes (info-grade)</summary>")
        lines.append("")
        for f in infos:
            lines.append(f"- {f['headline']}. {f['detail']}")
        lines.append("")
        lines.append("</details>")
        lines.append("")

    if by_kind.get("missing_metric"):
        lines.append("## What the document leaves out")
        lines.append("")
        for c in by_kind["missing_metric"]:
            lines.append(f"- {c['question']} <!--{c['id']}-->")
        lines.append("")

    dc = by_kind.get("definition_conflict", [])
    if dc:
        lines.append("## Definitions to reconcile")
        lines.append("")
        for c in dc:
            lines.append(f"- {c['question']} <!--{c['id']}-->")
        lines.append("")

    # Judgement call-outs are minted here, one per observation sentence.
    judgement: list[dict] = []
    lines.append("## Judgement — read with suspicion")
    lines.append("")
    if observations:
        lines.append("*Model observations on the narrative. Each one is a suggestion "
                     "with a name attached; accept, edit or strike it. Striking is "
                     "signal too.*")
        lines.append("")
        for i, o in enumerate(observations, 1):
            counters = sum(1 for c in callouts if c["kind"] == "judgement") + i
            cid = f"co-{tid}-judgement-{counters:03d}"
            pg = f" (p{o['evidence_page']})" if o.get("evidence_page") else ""
            lines.append(f"<!--{cid}-->")
            lines.append(f"- {o['observation']}{pg}")
            lines.append("")
            judgement.append({"id": cid, "kind": "judgement", "metric": None,
                              "confidence_pct": None,
                              "evidence_page": o.get("evidence_page"),
                              "question": o["observation"]})
    else:
        lines.append(f"*{judge_status}. The memo ships without a narrative pass "
                     f"rather than with a pretended one.*")
        lines.append("")

    lines.append("## Ask the seller")
    lines.append("")
    qs = [c["question"] for c in by_kind.get("missing_metric", [])]
    qs += [c["question"] for c in by_kind.get("definition_conflict", [])]
    qs += [c["question"] for c in by_kind.get("axis_read", [])]
    for q in qs:
        lines.append(f"- {q}")
    if not qs:
        lines.append("- Nothing outstanding from this screen.")
    lines.append("")
    lines.append("---")
    lines.append("")
    if examples_folded:
        lines.append(f"*{examples_folded} judgement example(s) folded back from "
                     f"reviewer-accepted corrections shaped this pass. Corrections "
                     f"teach the next version; they never rewrite this one.*")
    else:
        lines.append("*No reviewer corrections have been folded back yet — first "
                     "draft of the loop.*")
    return "\n".join(lines), callouts + judgement


def draft(result: dict, criteria: dict, doc_text: str | None = None,
          use_model: bool = True, page_texts: dict[int, str] | None = None) -> dict:
    """Full memo stage for one screened target. Returns artifacts dict."""
    callouts = derive_callouts(result, page_texts)
    observations, status = [], "narrative pass disabled (--no-model)"
    if use_model and doc_text:
        observations, status = judge(doc_text, [f["headline"] for f in result["findings"]])
    md, all_callouts = render_memo(result, criteria, callouts, observations, status,
                                   len(_load_examples()))
    return {"markdown": md, "callouts": all_callouts, "judge_status": status}
