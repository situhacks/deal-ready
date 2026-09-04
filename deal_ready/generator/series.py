"""Monthly ARR series for each target, authored by the generator.

The annual figures in a CIM are four points. Nothing forecasts from four points, and
saying otherwise would manufacture exactly the false precision this repo exists to
refuse. So the corpus grows a time axis: 60 monthly observations per target, of which
the last 12 are held out.

**The generator owns the future.** That is the only reason a forecasting experiment
here is worth running - almost every forecasting demo has no ground truth for the
period it predicts, and this one does by construction, the same way every other number
in this repo does.

The series is built from the profile's own stated facts so it cannot drift away from
the deck: it ends at the stated ARR, grows at the stated year-over-year rate, and
carries seasonality and noise a real subscription business would show. Seeded per
target, so regeneration reproduces it exactly.
"""

from __future__ import annotations

import math

import numpy as np

HISTORY_MONTHS = 48
HOLDOUT_MONTHS = 12
TOTAL_MONTHS = HISTORY_MONTHS + HOLDOUT_MONTHS

# Seasonality is real in vertical software - budget cycles, academic years, harvest
# windows - and a forecaster that cannot see it is being tested on the wrong thing.
# Amplitude as a fraction of level, per archetype.
_SEASON = {
    "clean_gem": 0.020,
    "concentration_risk": 0.035,
    "fake_saas_low_recurring": 0.055,   # re-occurring, not recurring: lumpier
    "unprofitable_high_growth": 0.025,
    "legacy_tech_key_person": 0.045,    # commodity cycle bleeds into renewals
}
_NOISE = {
    "clean_gem": 0.006,
    "concentration_risk": 0.012,
    "fake_saas_low_recurring": 0.020,
    "unprofitable_high_growth": 0.010,
    "legacy_tech_key_person": 0.014,
}


def monthly_arr(profile: dict) -> np.ndarray:
    """60 monthly ARR observations ending at the profile's stated FY25 ARR.

    Deterministic given the profile: same target, same series, forever.
    """
    arr = float(profile["metrics"]["arr_usd"]["value"])
    growth = float(profile["metrics"]["yoy_growth_pct"]["value"]) / 100.0
    arch = profile["archetype"]
    seed = int(profile["target_id"][1:])
    rng = np.random.default_rng(seed * 7919)

    # Work backwards from the stated ARR so month 48 (the end of history) lands on it.
    monthly_growth = (1.0 + growth) ** (1.0 / 12.0)
    idx = np.arange(TOTAL_MONTHS)
    trend = arr * monthly_growth ** (idx - (HISTORY_MONTHS - 1))

    season = 1.0 + _SEASON[arch] * np.sin(2.0 * math.pi * (idx % 12) / 12.0)
    noise = 1.0 + rng.normal(0.0, _NOISE[arch], TOTAL_MONTHS)

    series = trend * season * noise

    # The archetypes that are deteriorating should deteriorate in the holdout, because
    # that is the thing a forecaster would have to see coming. Applied only to the
    # forecast window, and only where the profile already says the business is weak.
    if arch in ("legacy_tech_key_person", "concentration_risk"):
        decay = np.linspace(1.0, 0.965, HOLDOUT_MONTHS)
        series[HISTORY_MONTHS:] *= decay

    return np.round(series, 2)


def split(series: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """History the model sees, and the truth it is scored against."""
    return series[:HISTORY_MONTHS], series[HISTORY_MONTHS:]


def build_all(profiles: list[dict]) -> dict:
    """Every target's series, in a shape that serialises to committed JSON."""
    out = {}
    for p in profiles:
        s = monthly_arr(p)
        out[p["target_id"]] = {
            "code_name": p["code_name"],
            "archetype": p["archetype"],
            "history_months": HISTORY_MONTHS,
            "holdout_months": HOLDOUT_MONTHS,
            "series_usd": [float(x) for x in s],
        }
    return out
