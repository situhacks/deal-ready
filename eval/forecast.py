"""Forecast bake-off: foundation models against the baselines that decide the question.

48 months of history per target, 12 held out, scored against ground truth the generator
authored. That last property is the reason this is worth running - almost every
forecasting demo has no truth for the window it predicts.

**The baselines are the experiment, not the control.** A 200-330M foundation model that
cannot beat a straight line on a smooth series has told you something, and that result
is as publishable here as a win would be. Reported either way.

MASE is scaled by the in-sample seasonal naive error, so 1.0 means "no better than
repeating last year's month". Below 1.0 is skill; above 1.0 is worse than doing nothing
clever.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SEASON = 12


def mase(truth: np.ndarray, pred: np.ndarray, history: np.ndarray) -> float:
    """Mean absolute scaled error against in-sample seasonal naive."""
    denom = np.mean(np.abs(history[SEASON:] - history[:-SEASON]))
    if denom == 0:
        return float("nan")
    return float(np.mean(np.abs(truth - pred)) / denom)


def mape(truth: np.ndarray, pred: np.ndarray) -> float:
    return float(np.mean(np.abs((truth - pred) / truth)) * 100.0)


# ---------------------------------------------------------------- baselines
def seasonal_naive(history: np.ndarray, h: int) -> np.ndarray:
    """Repeat the same month last year. The bar every model has to clear."""
    return np.array([history[-SEASON + (i % SEASON)] for i in range(h)])


def linear_fit(history: np.ndarray, h: int) -> np.ndarray:
    """Least-squares line through the history, extended. The other honest bar."""
    x = np.arange(len(history))
    m, c = np.polyfit(x, history, 1)
    return m * np.arange(len(history), len(history) + h) + c


def drift(history: np.ndarray, h: int) -> np.ndarray:
    """Last value plus average per-period change."""
    step = (history[-1] - history[0]) / (len(history) - 1)
    return history[-1] + step * np.arange(1, h + 1)


BASELINES = {"seasonal_naive": seasonal_naive, "linear_fit": linear_fit, "drift": drift}


# ---------------------------------------------------------------- foundation models
def timesfm_25(histories: list[np.ndarray], h: int):
    """TimesFM 2.5, 200M, Apache-2.0 weights."""
    import timesfm
    model = timesfm.TimesFM_2p5_200M_torch.from_pretrained(
        "google/timesfm-2.5-200m-pytorch")
    model.compile(timesfm.ForecastConfig(
        max_context=512, max_horizon=h, normalize_inputs=True))
    point, _ = model.forecast(horizon=h, inputs=[list(x) for x in histories])
    return [np.asarray(p, dtype=float)[:h] for p in point]


def timesfm_3(histories: list[np.ndarray], h: int):
    """TimesFM 3, 330M. Weights are non-commercial; fine for an experiment.

    Different API from 2.5 - a `TimesFM3Forecaster` with `predict`, one series at a
    time, rather than a compiled batch `forecast`.
    """
    import timesfm
    model = timesfm.TimesFM3Forecaster.from_pretrained("google/timesfm-3.0-pytorch")
    out = []
    for x in histories:
        r = model.predict(context=np.asarray(x, dtype=float), horizon=h, use_znorm=True)
        out.append(np.asarray(r.forecast, dtype=float).reshape(-1)[:h])
    return out


MODELS = {"timesfm_2.5": timesfm_25, "timesfm_3": timesfm_3}


# ---------------------------------------------------------------- runner
def run(series_path: Path | None = None) -> dict:
    series_path = series_path or ROOT / "data" / "monthly_series.json"
    data = json.loads(series_path.read_text(encoding="utf-8"))
    tids = sorted(data)
    h = data[tids[0]]["holdout_months"]
    n_hist = data[tids[0]]["history_months"]

    hist, truth = {}, {}
    for t in tids:
        s = np.array(data[t]["series_usd"], dtype=float)
        hist[t], truth[t] = s[:n_hist], s[n_hist:]

    results: dict = {"horizon": h, "history_months": n_hist, "targets": tids,
                     "methods": {}}

    for name, fn in BASELINES.items():
        rows, t0 = {}, time.time()
        for t in tids:
            p = fn(hist[t], h)
            rows[t] = {"mase": round(mase(truth[t], p, hist[t]), 4),
                       "mape": round(mape(truth[t], p), 3)}
        results["methods"][name] = {
            "status": "ok", "seconds": round(time.time() - t0, 2), "per_target": rows,
            "mean_mase": round(float(np.mean([r["mase"] for r in rows.values()])), 4),
            "mean_mape": round(float(np.mean([r["mape"] for r in rows.values()])), 3)}

    for name, fn in MODELS.items():
        t0 = time.time()
        try:
            preds = fn([hist[t] for t in tids], h)
        except Exception as e:                                   # noqa: BLE001
            # A model that will not load is reported, never silently skipped - the
            # same rule the vision path follows.
            results["methods"][name] = {
                "status": f"unavailable: {type(e).__name__}: {str(e)[:180]}",
                "seconds": round(time.time() - t0, 2)}
            continue
        rows = {}
        for t, p in zip(tids, preds):
            rows[t] = {"mase": round(mase(truth[t], p, hist[t]), 4),
                       "mape": round(mape(truth[t], p), 3)}
        results["methods"][name] = {
            "status": "ok", "seconds": round(time.time() - t0, 2), "per_target": rows,
            "mean_mase": round(float(np.mean([r["mase"] for r in rows.values()])), 4),
            "mean_mape": round(float(np.mean([r["mape"] for r in rows.values()])), 3)}

    return results


def render(res: dict) -> str:
    lines = [f"Horizon {res['horizon']} months, history {res['history_months']}, "
             f"{len(res['targets'])} targets", ""]
    lines.append(f"{'method':<18}{'mean MASE':>11}{'mean MAPE %':>13}{'seconds':>10}  status")
    ok = [(n, m) for n, m in res["methods"].items() if m["status"] == "ok"]
    for n, m in sorted(ok, key=lambda kv: kv[1]["mean_mase"]):
        lines.append(f"{n:<18}{m['mean_mase']:>11.4f}{m['mean_mape']:>13.3f}"
                     f"{m['seconds']:>10.2f}  ok")
    for n, m in res["methods"].items():
        if m["status"] != "ok":
            lines.append(f"{n:<18}{'-':>11}{'-':>13}{m['seconds']:>10.2f}  {m['status']}")
    return "\n".join(lines)


if __name__ == "__main__":
    r = run()
    print(render(r))
    out = ROOT / "reports" / "forecast_bakeoff.json"
    out.write_text(json.dumps(r, indent=2) + "\n", encoding="utf-8")
    print(f"\nwrote {out.relative_to(ROOT)}")
