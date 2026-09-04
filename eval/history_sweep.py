"""How much history do you actually need before forecasting means anything?

This is the experiment that decides whether any of the forecasting work applies to a
CIM at all. A memorandum gives you four annual figures. A public filer gives you
twenty-five quarters. Somewhere between those two the exercise stops being arithmetic
dressed up as prediction and starts being useful, and nobody has told us where.

So: take the real companies, hand each method progressively less history, and watch
the error curve. The interesting output is not which model wins - it is **the point on
the x-axis where every method collapses**, because that is the honest boundary of the
whole idea.

Real data only. The synthetic corpus cannot answer this: I chose its shape, so I would
be measuring my own assumption about how much history a pattern needs.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SEASON = 4
HORIZON = 4          # one year ahead, the easier of the two horizons


def mase(truth, pred, hist):
    if len(hist) <= SEASON:
        # Too short to scale against seasonal naive; fall back to mean absolute
        # change so the metric stays defined rather than silently NaN.
        denom = np.mean(np.abs(np.diff(hist))) if len(hist) > 1 else np.nan
    else:
        denom = np.mean(np.abs(hist[SEASON:] - hist[:-SEASON]))
    return float("nan") if not denom else float(np.mean(np.abs(truth - pred)) / denom)


def seasonal_naive(h, n):
    if len(h) < SEASON:
        return np.repeat(h[-1], n)
    return np.array([h[-SEASON + (i % SEASON)] for i in range(n)])


def linear_fit(h, n):
    if len(h) < 2:
        return np.repeat(h[-1], n)
    m, c = np.polyfit(np.arange(len(h)), h, 1)
    return m * np.arange(len(h), len(h) + n) + c


def drift(h, n):
    if len(h) < 2:
        return np.repeat(h[-1], n)
    step = (h[-1] - h[0]) / (len(h) - 1)
    return h[-1] + step * np.arange(1, n + 1)


def last_value(h, n):
    return np.repeat(h[-1], n)


BASELINES = {"last_value": last_value, "seasonal_naive": seasonal_naive,
             "linear_fit": linear_fit, "drift": drift}


def main() -> int:
    data = json.loads((ROOT / "data" / "realworld_revenue.json").read_text("utf-8"))
    series = {tk: np.array([p["value"] for p in c["points"]], dtype=float)
              for tk, c in sorted(data["companies"].items())}

    # History lengths worth asking about: 4 is a CIM, 8 is two years of quarters,
    # 24 is what a public filer hands you.
    lengths = [4, 6, 8, 12, 16, 20, 24]

    import timesfm
    tfm = timesfm.TimesFM3Forecaster.from_pretrained("google/timesfm-3.0-pytorch")

    rows = {}
    for n_hist in lengths:
        per_method = {k: [] for k in list(BASELINES) + ["timesfm_3"]}
        for tk, s in series.items():
            if len(s) < n_hist + HORIZON:
                continue
            cut = len(s) - HORIZON
            hist, truth = s[cut - n_hist:cut], s[cut:]
            for name, fn in BASELINES.items():
                per_method[name].append(mase(truth, fn(hist, HORIZON), hist))
            p = np.asarray(tfm.predict(context=hist, horizon=HORIZON,
                                       use_znorm=True).forecast, float)[:HORIZON]
            per_method["timesfm_3"].append(mase(truth, p, hist))
        rows[n_hist] = {k: round(float(np.nanmean(v)), 4) for k, v in per_method.items()
                        if v}
        got = rows[n_hist]
        print(f"history {n_hist:>3} quarters  " +
              "  ".join(f"{k}={got[k]:.3f}" for k in got))

    out = {"horizon": HORIZON, "season": SEASON,
           "companies": sorted(series), "mean_mase_by_history": rows}
    p = ROOT / "reports" / "history_sweep.json"
    p.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"\nwrote {p.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
