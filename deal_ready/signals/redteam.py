"""Persona red-team: generate the questions a skeptical buyer would ask.

The idea is borrowed from the swarm-simulation projects; the framing is not. Those
projects ask a population of agents *what will happen*, and the benchmark literature is
unkind to that - against 120,000+ personas of real humans, LLM agents predicted
reactions at MCC 0.29 while ordinary text classifiers scored 0.36, and individual-level
prediction sits under 5%. Asking these things to forecast is asking them to do the one
thing they measurably do worse than a cheaper method.

So this does not forecast. **It generates challenges, and the output is scored as
coverage rather than as prediction.** A persona that raises a real risk the rules cannot
see is a hit. One that raises noise is a false flag. That is the same scoring the
reviewer loop already uses for blind spots, which is the point - it plugs into a metric
that exists rather than inventing one.

Nothing here scores the target. It writes questions.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from ..models import ollama

MODEL = "qwen3.5:4b"

PERSONAS = {
    "operator": (
        "a permanent-hold acquirer's operating partner who has integrated forty small "
        "software companies and has seen every way a founder-dependent business breaks "
        "after the founder leaves"),
    "cfo": (
        "a CFO who has found revenue quality problems in a dozen diligences: services "
        "revenue counted as recurring, adjusted EBITDA hiding real costs, definitions "
        "that flatter"),
    "customer": (
        "a commercial diligence lead who thinks about the customer base as businesses "
        "with their own troubles, not as a retention percentage"),
    "technologist": (
        "an engineer who assesses whether a product's moat survives cheap AI tooling, "
        "and who has seen legacy stacks that cannot be modernised at any price"),
}


@dataclass
class Challenge:
    persona: str
    question: str
    concern: str

    def to_dict(self) -> dict:
        return {"persona": self.persona, "concern": self.concern,
                "question": self.question}


def _brief(result: dict, signal: dict | None, narrative: str) -> str:
    m = result.get("metrics", {})
    lines = [f"Target: {result.get('code_name')}", "", "Extracted metrics:"]
    for k, v in sorted(m.items()):
        lines.append(f"- {k}: {v}")
    if signal:
        lines += ["", f"Customer research: {signal['headline']}"]
        for c in signal.get("customers", []):
            if c["distressed"]:
                lines.append(f"- {c['name']} ({c['pct_arr']}% of ARR): {c['evidence']}")
    lines += ["", "Document narrative (excerpt):", narrative[:2600]]
    return "\n".join(lines)


def run(result: dict, signal: dict | None, narrative: str,
        personas: dict | None = None) -> tuple[list[Challenge], str]:
    """Ask each persona for its sharpest challenges. Fails soft, like every model call."""
    personas = personas or PERSONAS
    if not ollama.available() or not ollama.has_model(MODEL):
        return [], "model unavailable - red-team skipped"

    brief = _brief(result, signal, narrative)
    out: list[Challenge] = []
    for name, description in personas.items():
        system = (
            f"You are {description}. You are reviewing an acquisition target. "
            "You do not compute numbers and you do not recommend a transaction. "
            "You raise the questions the arithmetic cannot answer. Be specific to "
            "this company; generic diligence questions are worthless.")
        prompt = (
            f"{brief}\n\nReturn ONLY a JSON array of at most 3 objects:\n"
            '[{"concern": "<four words>", "question": "<one sharp question>"}]')
        reply = ollama.generate(MODEL, prompt, system=system, num_predict=700,
                                think=False)
        if not reply.ok:
            continue
        text = re.sub(r"<think>.*?</think>", "", reply.text, flags=re.S)
        m = re.search(r"\[.*\]", text, re.S)
        if not m:
            continue
        try:
            for o in json.loads(m.group(0))[:3]:
                if isinstance(o, dict) and o.get("question"):
                    out.append(Challenge(name, str(o["question"]).strip(),
                                         str(o.get("concern", "")).strip()))
        except json.JSONDecodeError:
            continue
    return out, "ok" if out else "no parseable challenges"
