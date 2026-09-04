"""Head-to-head: is TimesFM even the right foundation model?

TimesFM was picked because it was the model named in the request, not because it won
anything. Recent benchmark reporting puts Amazon's Chronos-2 and Salesforce's Moirai
2.0 ahead of it on GIFT-Eval, so the honest thing is to run them on the same six real
companies rather than take a leaderboard's word for it.

Same data, same split, same metric, same baselines. The baselines stay in because they
are the only thing that decides whether any foundation model earned its keep.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SEASON = 4


def mase(truth, pred, hist):
    denom = np.mean(np.abs(hist[SEASON:] - hist[:-SEASON]))
    return float("nan") if not denom else float(np.mean(np.abs(truth - pred)) / denom)


def mape(truth, pred):
    return float(np.mean(np.abs((truth - pred) / truth)) * 100.0)


def drift(h, n):
    step = (h[-1] - h[0]) / (len(h) - 1)
    return h[-1] + step * np.arange(1, n + 1)


def linear_fit(h, n):
    m, c = np.polyfit(np.arange(len(h)), h, 1)
    return m * np.arange(len(h), len(h) + n) + c


BASELINES = {"drift": drift, "linear_fit": linear_fit}


def timesfm_3(hs, n):
    import timesfm
    m = timesfm.TimesFM3Forecaster.from_pretrained("google/timesfm-3.0-pytorch")
    return [np.asarray(m.predict(context=np.asarray(h, float), horizon=n,
                                 use_znorm=True).forecast, float).reshape(-1)[:n]
            for h in hs]


def chronos_bolt(hs, n):
    """Chronos-Bolt base: distilled, fast, Apache-2.0."""
    import torch
    from chronos import BaseChronosPipeline
    p = BaseChronosPipeline.from_pretrained("amazon/chronos-bolt-base",
                                            device_map="cpu", torch_dtype=torch.float32)
    out = []
    for h in hs:
        q, mean = p.predict_quantiles(
            torch.tensor(np.asarray(h, dtype=np.float32)),
            prediction_length=n, quantile_levels=[0.5])
        out.append(np.asarray(mean[0], dtype=float).reshape(-1)[:n])
    return out


def chronos_2(hs, n):
    """Chronos-2, the model reported ahead of TimesFM on GIFT-Eval."""
    import torch
    from chronos import BaseChronosPipeline
    p = BaseChronosPipeline.from_pretrained("amazon/chronos-2",
                                            device_map="cpu", torch_dtype=torch.float32)
    out = []
    for h in hs:
        q, mean = p.predict_quantiles(
            [np.asarray(h, dtype=np.float32)],
            prediction_length=n, quantile_levels=[0.5])
        m0 = mean[0] if isinstance(mean, (list, tuple)) else mean
        out.append(np.asarray(m0, dtype=float).reshape(-1)[:n])
    return out


MODELS = {"timesfm_3": timesfm_3, "chronos_bolt_base": chronos_bolt,
          "chronos_2": chronos_2}


def run(horizon: int) -> dict:
    data = json.loads((ROOT / "data" / "realworld_revenue.json").read_text("utf-8"))
    series = {tk: np.array([p["value"] for p in c["points"]], dtype=float)
              for tk, c in sorted(data["companies"].items())}
    tickers = sorted(series)
    hist = {t: series[t][:-horizon] for t in tickers}
    truth = {t: series[t][-horizon:] for t in tickers}

    res = {"horizon": horizon, "tickers": tickers, "methods": {}}

    def score(name, preds, secs):
        rows = {t: {"mase": round(mase(truth[t], p, hist[t]), 4),
                    "mape": round(mape(truth[t], p), 3)}
                for t, p in zip(tickers, preds)}
        res["methods"][name] = {
            "status": "ok", "seconds": round(secs, 2), "per_ticker": rows,
            "mean_mase": round(float(np.mean([r["mase"] for r in rows.values()])), 4),
            "mean_mape": round(float(np.mean([r["mape"] for r in rows.values()])), 3)}

    for name, fn in BASELINES.items():
        t0 = time.time()
        score(name, [fn(hist[t], horizon) for t in tickers], time.time() - t0)

    for name, fn in MODELS.items():
        t0 = time.time()
        try:
            score(name, fn([hist[t] for t in tickers], horizon), time.time() - t0)
        except Exception as e:                                   # noqa: BLE001
            res["methods"][name] = {"status": f"unavailable: {type(e).__name__}: "
                                              f"{str(e)[:150]}",
                                    "seconds": round(time.time() - t0, 2)}
    return res


if __name__ == "__main__":
    allr = {}
    for h in (4, 8):
        r = run(h)
        print(f"--- horizon {h}q ---")
        print(f"{'method':<20}{'mean MASE':>11}{'mean MAPE %':>13}{'seconds':>9}")
        ok = [(n, m) for n, m in r["methods"].items() if m["status"] == "ok"]
        for n, m in sorted(ok, key=lambda kv: kv[1]["mean_mase"]):
            print(f"{n:<20}{m['mean_mase']:>11.4f}{m['mean_mape']:>13.3f}"
                  f"{m['seconds']:>9.2f}")
        for n, m in r["methods"].items():
            if m["status"] != "ok":
                print(f"{n:<20}  {m['status']}")
        print()
        allr[f"h{h}"] = r
    p = ROOT / "reports" / "model_bakeoff.json"
    p.write_text(json.dumps(allr, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {p.relative_to(ROOT)}")
