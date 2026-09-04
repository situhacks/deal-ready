"""The scenario layer: what would have to be true for this to work out.

Every layer beneath this produces facts. The document says what the seller wrote, the
base rate says what comparable acquisitions went on to do, the signals say what is
happening outside. None of them is a view.

This is the view, and it is deliberately not a number. **A forecast invites belief; an
assumption invites challenge**, and the second is the only thing worth putting in front
of a committee that reconciles to the penny.

So the output is a short list of assumptions that would have to hold for the base rate
to apply to this target, each one carrying:

    the assumption      stated so it can be argued with
    rests on            which input produced it, by name
    falsified by        what evidence would kill it

That last field is the discipline. An assumption nobody can disprove is a sentiment,
and sentiment does not belong in a deal memo.

**Nothing here scores.** It cannot reach the scorecard - `run_checks.py` fails the
build if the scoring path can import this module at all.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from ..models import ollama

MODEL = "qwen3.5:4b"


@dataclass
class Assumption:
    text: str
    rests_on: str
    falsified_by: str

    def to_dict(self) -> dict:
        return {"assumption": self.text, "rests_on": self.rests_on,
                "falsified_by": self.falsified_by}


def build_brief(result: dict, base_rate: dict | None,
                signal: dict | None, research: list[dict] | None) -> str:
    """Everything the reasoner is allowed to see, each block labelled by origin.

    Labelled on purpose: the reasoner is asked to name which input each assumption
    rests on, and it cannot do that honestly if the inputs arrive as one undifferentiated
    wall of text.
    """
    m = result.get("metrics", {})
    out = [f"TARGET: {result.get('code_name')}", "",
           "[A] EXTRACTED FROM THE DOCUMENT"]
    for k in sorted(m):
        out.append(f"  {k}: {m[k]}")
    fits = result.get("fit", {})
    out.append(f"  fit score: {fits.get('score')} -> {fits.get('tier_label')}")
    for f in result.get("findings", []):
        if f.get("severity") in ("blocker", "warning"):
            out.append(f"  RULE: {f.get('headline')}")

    out += ["", "[B] BASE RATE FROM PAST ACQUISITIONS"]
    if base_rate and base_rate.get("status") == "ok":
        o = base_rate["outcome_cagr_pct"]
        b = base_rate["underwriting_bias_pts"]
        out.append(f"  matched on {base_rate['matched_on']} across "
                   f"{base_rate['n_comparables']} past deals")
        out.append(f"  outcome revenue CAGR: p10 {o['p10']}%, median {o['median']}%, "
                   f"p90 {o['p90']}%; {o['share_negative']}% shrank")
        out.append(f"  underwriting ran {b['median']} points optimistic at the median")
    else:
        out.append("  none available")

    out += ["", "[C] CUSTOMER HEALTH"]
    out.append(f"  {signal['headline']}" if signal else "  not researched")

    out += ["", "[D] EXTERNAL RESEARCH"]
    if research:
        for r in research[:12]:
            out.append(f"  ({r.get('lens')}) {r.get('finding')} "
                       f"[{r.get('date')}, {r.get('tier')}]")
    else:
        out.append("  none available")
    return "\n".join(out)


def run(result: dict, base_rate: dict | None = None, signal: dict | None = None,
        research: list[dict] | None = None) -> tuple[list[Assumption], str]:
    """Ask for the assumptions, not the answer. Fails soft like every model call here."""
    if not ollama.available() or not ollama.has_model(MODEL):
        return [], "model unavailable - scenario pass skipped"

    brief = build_brief(result, base_rate, signal, research)
    system = (
        "You are preparing a screening memo for an investment committee of accountants. "
        "They do not want a prediction. They want to know what would have to be true "
        "for this acquisition to perform like comparable past ones, and what evidence "
        "would prove each assumption wrong. "
        "You never state a forecast, a valuation, or a recommendation. "
        "Every assumption must name which labelled input block it rests on - A, B, C or "
        "D - because a reviewer has to be able to trace it.")
    prompt = (
        f"{brief}\n\n"
        "Return ONLY a JSON array of 3 to 5 objects, most consequential first:\n"
        '[{"assumption": "<one sentence that could be false>", '
        '"rests_on": "<A/B/C/D and what specifically>", '
        '"falsified_by": "<what evidence would disprove it>"}]')
    reply = ollama.generate(MODEL, prompt, system=system, num_predict=1100, think=False)
    if not reply.ok:
        return [], f"model call failed ({reply.error}) - scenario pass skipped"

    text = re.sub(r"<think>.*?</think>", "", reply.text, flags=re.S)
    m = re.search(r"\[.*\]", text, re.S)
    if not m:
        return [], "model returned no parseable array - scenario pass skipped"
    try:
        raw = json.loads(m.group(0))
    except json.JSONDecodeError:
        return [], "model returned malformed JSON - scenario pass skipped"

    out = []
    for o in raw[:5]:
        if isinstance(o, dict) and o.get("assumption"):
            out.append(Assumption(str(o["assumption"]).strip(),
                                  str(o.get("rests_on", "")).strip(),
                                  str(o.get("falsified_by", "")).strip()))
    return out, "ok" if out else "no assumptions parsed"
