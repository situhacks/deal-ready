"""TimesFM against real companies, with an audit trail.

The synthetic test could only show the plumbing works - the answer key was written by
the same hand as the question. This one uses six real vertical-software companies,
179 quarters of revenue pulled from their own SEC filings, and asks the only question
that matters: **forecast one and two years forward, then compare to what actually
happened.**

Auditability is the point, not a feature. Accounting work cannot use a number nobody
can trace, so every run reports three things a reviewer can check independently:

    the inputs      every quarter cites the filing that reported it
    the baseline    what a naive method would have said, computed in code
    the delta       what the model added on top, per quarter, in dollars

That last column is the closest thing to an explanation a foundation model can give.
It does not say *why* the model moved a number, and this file does not pretend
otherwise - but it does say exactly *how much* of the answer is the model's opinion
rather than arithmetic, which is the part a reviewer has to decide whether to accept.

Quarterly data, so the seasonal period is 4.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SEASON = 4


def mase(truth, pred, history) -> float:
    denom = np.mean(np.abs(history[SEASON:] - history[:-SEASON]))
    return float("nan") if denom == 0 else float(np.mean(np.abs(truth - pred)) / denom)


def mape(truth, pred) -> float:
    return float(np.mean(np.abs((truth - pred) / truth)) * 100.0)


def seasonal_naive(h, n):
    return np.array([h[-SEASON + (i % SEASON)] for i in range(n)])


def linear_fit(h, n):
    m, c = np.polyfit(np.arange(len(h)), h, 1)
    return m * np.arange(len(h), len(h) + n) + c


def drift(h, n):
    step = (h[-1] - h[0]) / (len(h) - 1)
    return h[-1] + step * np.arange(1, n + 1)


BASELINES = {"seasonal_naive": seasonal_naive, "linear_fit": linear_fit, "drift": drift}


def timesfm_25(histories, n):
    import timesfm
    m = timesfm.TimesFM_2p5_200M_torch.from_pretrained("google/timesfm-2.5-200m-pytorch")
    m.compile(timesfm.ForecastConfig(max_context=512, max_horizon=n,
                                     normalize_inputs=True))
    pt, _ = m.forecast(horizon=n, inputs=[list(x) for x in histories])
    return [np.asarray(p, dtype=float)[:n] for p in pt]


def timesfm_3(histories, n):
    import timesfm
    m = timesfm.TimesFM3Forecaster.from_pretrained("google/timesfm-3.0-pytorch")
    return [np.asarray(m.predict(context=np.asarray(x, float), horizon=n,
                                 use_znorm=True).forecast, float).reshape(-1)[:n]
            for x in histories]


MODELS = {"timesfm_2.5": timesfm_25, "timesfm_3": timesfm_3}


def run(horizon: int) -> dict:
    data = json.loads((ROOT / "data" / "realworld_revenue.json").read_text("utf-8"))
    tickers, hist, truth, prov = [], {}, {}, {}
    for tk, c in sorted(data["companies"].items()):
        pts = c["points"]
        if len(pts) < horizon + 12:
            continue
        vals = np.array([p["value"] for p in pts], dtype=float)
        tickers.append(tk)
        hist[tk], truth[tk] = vals[:-horizon], vals[-horizon:]
        prov[tk] = {"cik": c["cik"], "tag": c["tag"],
                    "train_quarters": len(vals) - horizon,
                    "first": pts[0]["end"], "last_train": pts[-horizon - 1]["end"],
                    "holdout_from": pts[-horizon]["end"],
                    "holdout_filings": [
                        {"period": f"{p['fy']}{p['fp']}", "end": p["end"],
                         "form": p["form"], "accession": p["accession"],
                         "filed": p["filed"], "value": p["value"]}
                        for p in pts[-horizon:]],
                    }

    res = {"horizon_quarters": horizon, "season": SEASON, "tickers": tickers,
           "provenance": prov, "methods": {}}

    def score(name, preds, secs):
        rows = {t: {"mase": round(mase(truth[t], p, hist[t]), 4),
                    "mape": round(mape(truth[t], p), 3)}
                for t, p in zip(tickers, preds)}
        res["methods"][name] = {
            "status": "ok", "seconds": round(secs, 2), "per_ticker": rows,
            "mean_mase": round(float(np.mean([r["mase"] for r in rows.values()])), 4),
            "mean_mape": round(float(np.mean([r["mape"] for r in rows.values()])), 3)}
        return {t: p for t, p in zip(tickers, preds)}

    base_preds = {}
    for name, fn in BASELINES.items():
        t0 = time.time()
        base_preds[name] = score(name, [fn(hist[t], horizon) for t in tickers],
                                 time.time() - t0)

    for name, fn in MODELS.items():
        t0 = time.time()
        try:
            preds = fn([hist[t] for t in tickers], horizon)
        except Exception as e:                                   # noqa: BLE001
            res["methods"][name] = {"status": f"unavailable: {type(e).__name__}: "
                                              f"{str(e)[:160]}",
                                    "seconds": round(time.time() - t0, 2)}
            continue
        model_preds = score(name, preds, time.time() - t0)

        # The audit column: what the model added on top of seasonal naive, and what
        # the truth turned out to be. A reviewer can see how much of the answer is
        # the model's opinion rather than arithmetic.
        res["methods"][name]["audit"] = {
            t: {"naive": [round(float(x)) for x in base_preds["seasonal_naive"][t]],
                "model": [round(float(x)) for x in model_preds[t]],
                "model_minus_naive": [round(float(a - b)) for a, b in
                                      zip(model_preds[t],
                                          base_preds["seasonal_naive"][t])],
                "actual": [round(float(x)) for x in truth[t]]}
            for t in tickers}
    return res


def render(res: dict) -> str:
    out = [f"Horizon {res['horizon_quarters']} quarters "
           f"({res['horizon_quarters'] // 4} year(s)), {len(res['tickers'])} companies: "
           f"{', '.join(res['tickers'])}", ""]
    out.append(f"{'method':<18}{'mean MASE':>11}{'mean MAPE %':>13}{'seconds':>9}")
    ok = [(n, m) for n, m in res["methods"].items() if m["status"] == "ok"]
    for n, m in sorted(ok, key=lambda kv: kv[1]["mean_mase"]):
        out.append(f"{n:<18}{m['mean_mase']:>11.4f}{m['mean_mape']:>13.3f}"
                   f"{m['seconds']:>9.2f}")
    for n, m in res["methods"].items():
        if m["status"] != "ok":
            out.append(f"{n:<18}  {m['status']}")
    return "\n".join(out)


if __name__ == "__main__":
    all_res = {}
    for h in (4, 8):
        r = run(h)
        print(render(r)); print()
        all_res[f"h{h}"] = r
    p = ROOT / "reports" / "forecast_realworld.json"
    p.write_text(json.dumps(all_res, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {p.relative_to(ROOT)}")
