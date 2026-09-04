"""Does giving the model correlated series actually help?

The first real-data test ran TimesFM-3 univariate: one company's revenue, no side
information. That undersold it, because multivariate forecasting with covariates is
the headline feature of version 3 and the whole reason it exists.

So this asks the question properly. Forecast each company's revenue while handing the
model **the other five companies as covariates** - a sector cohort, which is the
closest thing to "what is happening in this industry" that a numeric model can consume.

Two covariate modes, and the difference between them matters:

    past_only      the cohort's history up to the cut. Honest: you would have this.
    past_future    the cohort's history AND its actual future values. Optimistic:
                   you would only have this if the cohort were something you genuinely
                   know ahead, like a published index or a contracted schedule.

Both are reported. The gap between them is the value of knowing something about the
future, which is a real thing to measure and a real thing not to claim you have.
"""

from __future__ import annotations

import json
import sys
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


def main() -> int:
    horizon = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    data = json.loads((ROOT / "data" / "realworld_revenue.json").read_text("utf-8"))
    series = {tk: np.array([p["value"] for p in c["points"]], dtype=float)
              for tk, c in sorted(data["companies"].items())}
    tickers = sorted(series)

    # Align every company on a common window so the cohort covariates line up.
    n = min(len(s) for s in series.values())
    aligned = {tk: s[-n:] for tk, s in series.items()}
    cut = n - horizon

    import timesfm
    model = timesfm.TimesFM3Forecaster.from_pretrained("google/timesfm-3.0-pytorch")

    def cohort(target: str, upto: int) -> np.ndarray:
        """Mean of the other five, z-scored. One covariate channel, not five.

        Shaped (channels, time) - the API runs np.atleast_2d, so a (time, 1)
        array is read as one timestep with T channels and fails on a shape
        mismatch that does not say so.

        A cohort mean is what a sector index actually is, and it keeps the covariate
        count honest - handing a 25-point series five extra channels invites the model
        to fit noise.
        """
        others = np.array([aligned[t][:upto] for t in tickers if t != target])
        m = others.mean(axis=0)
        return (m - m.mean()) / (m.std() or 1.0)

    out = {"horizon": horizon, "tickers": tickers, "aligned_quarters": n, "modes": {}}

    for mode in ("univariate", "past_only", "past_future"):
        rows = {}
        for tk in tickers:
            hist, truth = aligned[tk][:cut], aligned[tk][cut:]
            kw = {}
            if mode == "past_only":
                kw["past_only_covariates"] = cohort(tk, cut).reshape(1, -1)
            elif mode == "past_future":
                kw["past_future_covariates"] = cohort(tk, n).reshape(1, -1)
            try:
                r = model.predict(context=hist, horizon=horizon, use_znorm=True, **kw)
                p = np.asarray(r.forecast, float).reshape(-1)[:horizon]
            except Exception as e:                               # noqa: BLE001
                out["modes"][mode] = {"status": f"unavailable: {type(e).__name__}: "
                                                f"{str(e)[:140]}"}
                rows = None
                break
            rows[tk] = {"mase": round(mase(truth, p, hist), 4),
                        "mape": round(mape(truth, p), 3)}
        if rows:
            out["modes"][mode] = {
                "status": "ok", "per_ticker": rows,
                "mean_mase": round(float(np.mean([r["mase"] for r in rows.values()])), 4),
                "mean_mape": round(float(np.mean([r["mape"] for r in rows.values()])), 3)}

    print(f"horizon {horizon}q, {len(tickers)} companies, {n} aligned quarters\n")
    print(f"{'mode':<14}{'mean MASE':>11}{'mean MAPE %':>13}")
    for mode, m in out["modes"].items():
        if m["status"] == "ok":
            print(f"{mode:<14}{m['mean_mase']:>11.4f}{m['mean_mape']:>13.3f}")
        else:
            print(f"{mode:<14}  {m['status']}")

    p = ROOT / "reports" / f"covariate_test_h{horizon}.json"
    p.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"\nwrote {p.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
