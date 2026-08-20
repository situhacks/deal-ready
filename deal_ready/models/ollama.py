"""The single door every model call goes through.

There is exactly one reason this module exists as a seam rather than a convenience:
**what a local model does, and whether it runs at all, varies wildly by machine - and
none of that is a parser's business.**

Two examples this repo hit while being built, both worth knowing before you debug the
wrong thing:

- **A model can advertise a capability it will not honour.** `gemma4:latest` lists
  `vision` in `ollama show` and then answers "please provide the page you would like
  me to transcribe" for an image sent through either `/api/generate` or `/api/chat` -
  the identical payload `qwen3-vl:8b` reads without complaint.
- **`num_predict` is a silent trap on a thinking model.** qwen3-vl emits ~10k
  characters of reasoning before ~350 characters of answer. Cap the budget below that
  and the call returns an EMPTY string with `done_reason="length"`. It looks exactly
  like a model that cannot read charts.

GPU support is the third variable. AMD RDNA 2 cards differ: gfx1030 (RX 6800/6900 XT)
is natively ROCm-supported and needs nothing, while gfx1031/gfx1032 (RX 6700/6600)
require `HSA_OVERRIDE_GFX_VERSION=10.3.0` and hit a ROCm 6.4.3+ regression that
segfaults on first prompt and falls back to CPU; `OLLAMA_VULKAN=1` sidesteps it.

So: every call is routed here, every call has a timeout, and every failure returns a
structured miss rather than an exception. A backend that cannot reach a model reports
"not run" and the eval prints "not run" - it does not crash, and it never quietly
substitutes a different answer. Being explicit about what did not happen is the whole
discipline this repo is arguing for.

Talks to localhost only. No external network, no API key, no account.
"""

from __future__ import annotations

import base64
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
DEFAULT_TIMEOUT = int(os.environ.get("DEAL_READY_TIMEOUT", "300"))


@dataclass
class ModelReply:
    ok: bool
    text: str = ""
    error: str = ""
    model: str = ""
    seconds: float = 0.0
    eval_count: int | None = None       # tokens the model generated
    prompt_eval_count: int | None = None  # tokens it read

    @property
    def tokens_in(self) -> int:
        return self.prompt_eval_count or 0

    @property
    def tokens_out(self) -> int:
        return self.eval_count or 0


def _post(path: str, payload: dict, timeout: int) -> dict:
    req = urllib.request.Request(
        f"{HOST}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def available() -> bool:
    """Is a local Ollama reachable at all?"""
    try:
        urllib.request.urlopen(f"{HOST}/api/tags", timeout=5).read()
        return True
    except Exception:
        return False


def installed_models() -> list[str]:
    try:
        with urllib.request.urlopen(f"{HOST}/api/tags", timeout=10) as r:
            data = json.loads(r.read().decode("utf-8"))
        return sorted(m["name"] for m in data.get("models", []))
    except Exception:
        return []


def has_model(name: str) -> bool:
    have = installed_models()
    return name in have or any(m.split(":")[0] == name.split(":")[0] for m in have)


def generate(
    model: str,
    prompt: str,
    images: list[bytes] | None = None,
    system: str | None = None,
    temperature: float = 0.0,
    num_predict: int | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> ModelReply:
    """One completion. `images` are raw PNG/JPEG bytes.

    temperature defaults to 0: this pipeline is measured, and a scorer whose inputs
    wander between runs cannot be measured.
    """
    payload: dict = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        # Hold the model resident between pages. Without this Ollama unloads on its
        # idle timer and every page pays a 6.6GB reload - and, observed here, a call
        # issued into that window can hang rather than queue.
        "keep_alive": "30m",
        "options": {"temperature": temperature},
    }
    if num_predict is not None:
        payload["options"]["num_predict"] = num_predict
    if system:
        payload["system"] = system
    if images:
        payload["images"] = [base64.b64encode(b).decode("ascii") for b in images]

    t0 = time.time()
    try:
        data = _post("/api/generate", payload, timeout)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")[:300]
        return ModelReply(False, error=f"HTTP {e.code}: {body}", model=model,
                          seconds=time.time() - t0)
    except Exception as e:
        return ModelReply(False, error=f"{type(e).__name__}: {e}", model=model,
                          seconds=time.time() - t0)

    return ModelReply(
        ok=True,
        text=data.get("response", ""),
        model=model,
        seconds=time.time() - t0,
        eval_count=data.get("eval_count"),
        prompt_eval_count=data.get("prompt_eval_count"),
    )


def embed(model: str, texts: list[str], timeout: int = DEFAULT_TIMEOUT) -> list[list[float]] | None:
    """Text embeddings. Returns None if the model or server is unavailable."""
    try:
        data = _post("/api/embed", {"model": model, "input": texts}, timeout)
        return data.get("embeddings")
    except Exception:
        return None


def describe_runtime() -> dict:
    """What actually ran, for the README and the reproducibility note."""
    return {
        "host": HOST,
        "reachable": available(),
        "models": installed_models(),
        "vulkan_env": os.environ.get("OLLAMA_VULKAN"),
        "hsa_override": os.environ.get("HSA_OVERRIDE_GFX_VERSION"),
    }
