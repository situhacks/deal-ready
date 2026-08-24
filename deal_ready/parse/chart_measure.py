"""Measure chart values from pixels. The model reads glyphs; code measures geometry.

A vision model reading a value off an axis is estimating: point sits between the 105
and 110 gridlines, a bit below the middle, call it 108.2. The estimate lands within
tenths of the truth and still misses it - even for the newest open frontier model,
which the 2026-08-24 probe caught at three-of-five endpoint pairs exact and two
within 0.2. But a rendered chart is also just an image with fixed geometry: series
in consistent colors, gridlines at printed tick values, a marker at each data point.
Given the tick values, the value of an endpoint is not an estimation problem at all.
It is a ruler.

Division of labour, the same one the rest of this repo runs:

    model   reads the tick-label glyphs and names the series (recognition)
    code    finds the series pixels, locates the endpoint marker, fits the line,
            interpolates against the gridlines (deterministic, offline-verifiable)

Everything here is pure geometry over an RGB array plus pure comparison logic. No
model call, no cache of its own: given the chart's bytes and the tick values it
returns the same numbers forever, which is what lets `run_checks.py` re-verify
every axis-read value from committed artifacts without a GPU.

Honest limits: this is geometry for rendered charts with gridlines and colour-coded
series - the common case in a CIM exhibit, not a universal one. Photos, 3-D renders
and label-less log axes are out of scope, and callers fall back to asking the seller
when the geometry does not resolve.
"""

from __future__ import annotations

import io
import re
from itertools import permutations

import numpy as np

# A gridline is the background-tinted rule drawn across the plot: low channel
# spread (it is gray, not a colour) and a brightness band below white.
GRID_SPREAD_MAX = 12
GRID_BRIGHTNESS = (200, 246)   # white is 255; the alpha-blended rules sit ~236-243
GRID_ROW_FRACTION = 0.5        # a gridline spans at least half the image width

# A series colour has enough channel spread to not be gray/ink, and enough pixels
# to be a drawn line rather than an artifact.
COLOR_SPREAD_MIN = 30
COLOR_BRIGHTNESS_MAX = 240
SERIES_MIN_FRACTION = 0.003    # of all pixels; a 950x480 line chart series is ~0.8%
COLOR_TOLERANCE = 35           # per-channel, around a series colour's mean

# Anti-aliased text is neutral gray, which can sit inside the per-channel tolerance
# of a dark series colour - and legend text sits right of the last marker. Requiring
# channel spread in the mask excludes it: gray text has none, series ink does.
MASK_SPREAD_MIN = 15

# The FY25 marker is the rightmost blob of a series. Its center is read from the
# right cap - the last few columns, which contain marker and no line.
_ENDPOINT_CAP_COLS = 3

# The line fit runs behind the marker. The marker is ~13px of ink whose rasterized
# center depends on the sub-pixel phase of the true point - one chart's disc
# measured a clean, symmetric 1.3px low, worth exactly the 0.1 that separated a
# pass from a miss. The line entering it is hundreds of columns of the same ink;
# fitting its centerline averages the phase noise out.
_LINE_SPAN = 80          # columns of line fitted behind the marker
_LINE_SKIP = 16          # columns skipped: marker half-width plus anti-aliasing
_MARKER_HALF = 8         # the fit is evaluated at the marker's center, not its edge
_LINE_RUN_TOL = 4.0      # px a column's band center may move between neighbours
_LINE_TRIM = 0.8         # px; residuals beyond this are refit without (marker halo)

# An independent model re-read counts as agreeing with the measurement when it
# lands within this many points. The observed wobble of a frontier-class open
# model on these charts is +/-0.2; half a small gridline gap is generous without
# being blind.
READ_TOLERANCE = 0.5

_MODEL_READ_RE = re.compile(r"^(.+?):\s*([0-9]+(?:\.[0-9]+)?)\s*%?\s*$")
_TICKS_RE = re.compile(r"^ticks:\s*(.*)$", re.I)
_BARE_NUMBER_RE = re.compile(r"^-?\d+(?:\.\d+)?$")


def _rgb(png: bytes) -> np.ndarray:
    from PIL import Image  # matplotlib's own dependency; no extra install
    return np.asarray(Image.open(io.BytesIO(png)).convert("RGB"), dtype=np.int16)


def find_gridlines(rgb: np.ndarray) -> list[float]:
    """Y centers of the horizontal gridlines, top to bottom.

    A candidate row is mostly grid-tinted pixels. Rows are grouped when adjacent -
    anti-aliasing smears one rule across 2-3 rows - and each group collapses to its
    center. Fewer than two lines means no calibration is possible.
    """
    spread = rgb.max(axis=2) - rgb.min(axis=2)
    bright = rgb.mean(axis=2)
    gridish = ((spread <= GRID_SPREAD_MAX)
               & (bright >= GRID_BRIGHTNESS[0]) & (bright < GRID_BRIGHTNESS[1]))
    counts = gridish.sum(axis=1)
    rows = np.where(counts > GRID_ROW_FRACTION * rgb.shape[1])[0]
    groups: list[list[int]] = []
    for y in rows:
        if groups and int(y) - groups[-1][-1] <= 2:
            groups[-1].append(int(y))
        else:
            groups.append([int(y)])
    return [round(float(np.mean(g)), 1) for g in groups]


def find_series(rgb: np.ndarray) -> list[tuple[int, int, int]]:
    """The chart's series colours, largest pixel count first.

    Quantise to /24 bins, keep bins holding enough pixels to be a drawn line, and
    take each bin's mean colour. Anti-aliasing splits one series across neighbouring
    bins, so bins within tolerance of an already-kept colour are absorbed into it.
    """
    spread = rgb.max(axis=2) - rgb.min(axis=2)
    bright = rgb.mean(axis=2)
    colored = (spread > COLOR_SPREAD_MIN) & (bright < COLOR_BRIGHTNESS_MAX)
    px = rgb[colored].astype(np.int64)
    if not len(px):
        return []
    keys = (px[:, 0] // 24) * 100_000 + (px[:, 1] // 24) * 1_000 + (px[:, 2] // 24)
    uniq, counts = np.unique(keys, return_counts=True)
    order = np.argsort(-counts)
    series: list[tuple[int, int, int]] = []
    need = SERIES_MIN_FRACTION * rgb.shape[0] * rgb.shape[1]
    for i in order:
        if counts[i] < need:
            break
        k = int(uniq[i])
        mean = tuple(int(px[keys == k][:, c].mean()) for c in range(3))
        if any(all(abs(mean[c] - s[c]) <= COLOR_TOLERANCE for c in range(3))
               for s in series):
            continue  # anti-aliasing bin of a colour already kept
        series.append(mean)
        if len(series) >= 4:
            break
    return series


def find_endpoint(rgb: np.ndarray,
                  color: tuple[int, int, int]) -> tuple[float, int] | None:
    """(center row, rightmost column) of the final marker blob for one series.

    The rightmost coloured pixels are the final data point; the last few columns
    are pure marker, and their vertical extent is centered on it.
    """
    dist = np.abs(rgb - np.array(color, dtype=np.int16)).max(axis=2)
    spread = rgb.max(axis=2) - rgb.min(axis=2)
    mask = (dist <= COLOR_TOLERANCE) & (spread > MASK_SPREAD_MIN)
    cols = np.where(mask.any(axis=0))[0]
    if not len(cols):
        return None
    x1 = int(cols.max())
    cap = mask[:, max(0, x1 - _ENDPOINT_CAP_COLS):x1 + 1]
    rows = np.where(cap.any(axis=1))[0]
    return float((rows.min() + rows.max()) / 2.0), x1


def line_fit_y(rgb: np.ndarray, color: tuple[int, int, int],
               x_end: int, y_hint: float) -> float | None:
    """Least-squares centerline of the series line just left of its end marker,
    evaluated at the marker's center.

    The walk starts clear of the marker (its columns are flat at the marker's own
    center, and including them tilts the fit) and tracks the contiguous band nearest
    the previous column's center, so a legend swatch crossing the segment cannot
    hijack the fit. Evaluating at the marker's center rather than its right edge
    avoids adding slope x radius to the result - on these charts that difference is
    the gap between 86.0 and 86.1.
    """
    dist = np.abs(rgb - np.array(color, dtype=np.int16)).max(axis=2)
    spread = rgb.max(axis=2) - rgb.min(axis=2)
    mask = (dist <= COLOR_TOLERANCE) & (spread > MASK_SPREAD_MIN)

    xs: list[int] = []
    ys: list[float] = []
    prev = y_hint
    for x in range(x_end - _LINE_SKIP, x_end - _LINE_SKIP - _LINE_SPAN, -1):
        if x < 0:
            break
        rows = np.where(mask[:, x])[0]
        if not len(rows):
            break
        runs: list[list[int]] = []
        for r in rows:
            if runs and int(r) - runs[-1][-1] == 1:
                runs[-1].append(int(r))
            else:
                runs.append([int(r)])
        centers = [(r[0] + r[-1]) / 2.0 for r in runs]
        best = min(centers, key=lambda c: abs(c - prev), default=None)
        if best is None or abs(best - prev) > _LINE_RUN_TOL:
            break
        prev = best
        xs.append(x)
        ys.append(best)
    if len(xs) < _LINE_SPAN // 2:
        return None
    xa = np.array(xs, dtype=float)
    ya = np.array(ys)
    z = np.polyfit(xa, ya, 1)
    # The first columns after the skip can still carry the marker's halo, which
    # tilts the fit. One trimmed refit removes it.
    resid = np.abs(np.polyval(z, xa) - ya)
    keep = resid <= max(_LINE_TRIM, float(np.median(resid) * 3))
    if keep.sum() >= len(xs) * 0.7 and keep.sum() >= 2:
        z = np.polyfit(xa[keep], ya[keep], 1)
    return float(np.polyval(z, float(x_end - _MARKER_HALF)))


def interpolate(y: float, grid_ys: list[float],
                ticks_top_to_bottom: list[float]) -> float | None:
    """Linear interpolation of a pixel row against the gridline calibration."""
    if len(grid_ys) != len(ticks_top_to_bottom) or len(grid_ys) < 2:
        return None
    pts = sorted(zip(grid_ys, ticks_top_to_bottom))      # by pixel row, top first
    for (y1, v1), (y2, v2) in zip(pts, pts[1:]):
        if y1 <= y <= y2:
            return v1 + (y - y1) * (v2 - v1) / (y2 - y1)
    # Outside the calibrated span: extrapolate from the nearest pair rather than
    # return nothing - the caller decides whether the extrapolation is acceptable.
    (y1, v1), (y2, v2) = (pts[0], pts[1]) if y < pts[0][0] else (pts[-2], pts[-1])
    return v1 + (y - y1) * (v2 - v1) / (y2 - y1)


def measure_chart(png: bytes, ticks: list[float]) -> list[float] | None:
    """Geometry's answer for one chart: every series' endpoint value, in pixels.

    `ticks` are the y-axis tick values top to bottom (the caller's model read them
    once, cached). Returns one value per detected series, largest pixel count
    first, or None when the chart does not resolve: no gridlines, tick-count
    mismatch, or a series whose geometry would not close.
    """
    rgb = _rgb(png)
    grid = find_gridlines(rgb)
    series = find_series(rgb)
    if len(grid) < 2 or not series or len(grid) != len(ticks):
        return None
    # Order comes from geometry, not from any model: gridlines run top to bottom
    # and a y axis increases upward, so the top gridline pairs with the largest
    # tick. (Measured reason: a model returned one chart's ticks bottom-to-top
    # despite the prompt, which mirrored every value.)
    calibrated = sorted(ticks, reverse=True)
    values = []
    for color in series:
        ep = find_endpoint(rgb, color)
        if ep is None:
            return None
        y = line_fit_y(rgb, color, ep[1], ep[0]) or ep[0]
        v = interpolate(y, grid, calibrated)
        if v is None:
            return None
        values.append(round(v, 1))
    return values


def parse_model_reads(text: str) -> tuple[list[tuple[str, float]], list[float]]:
    """(series reads, tick values) from the chart model's answer.

    Expected format: one `label: value` line per series plus a `ticks:` line. The
    model's values are estimates and never enter the pipeline's numbers - they join
    measured values to their labels, then serve as the independent cross-check.
    """
    pairs: list[tuple[str, float]] = []
    ticks: list[float] = []
    for line in text.splitlines():
        line = line.strip()
        t = _TICKS_RE.match(line)
        if t:
            ticks = [float(x) for x in t.group(1).split(",")
                     if _BARE_NUMBER_RE.match(x.strip())]
            continue
        m = _MODEL_READ_RE.match(line)
        if m and m.group(1).strip().lower() != "ticks":
            try:
                pairs.append((m.group(1).strip(), float(m.group(2))))
            except ValueError:
                continue
    return pairs, ticks


def join_by_proximity(rows: list[tuple[str, float]],
                      values: list[float]) -> list[tuple[str, float]] | None:
    """Measured values joined to series labels by the assignment that best matches
    the rows' own (estimated) values - identity or permutation, whichever minimises
    total distance. Returns None when the counts do not match."""
    if not rows or len(rows) != len(values):
        return None
    best, best_err = None, None
    for perm in permutations(range(len(values))):
        err = sum(abs(rows[i][1] - values[perm[i]]) for i in range(len(rows)))
        if best_err is None or err < best_err:
            best, best_err = perm, err
    return [(rows[i][0], values[best[i]]) for i in range(len(rows))]


def block_from_pairs(pairs: list[tuple[str, float]]) -> str:
    lines = ["[Measured from the chart's pixels - authoritative over the "
             "estimates above]"]
    lines += [f"{label}: {value:.1f}% (measured off the axis)"
              for label, value in pairs]
    return "\n".join(lines)


def crosscheck(measured: list[tuple[str, float]],
               model_reads: list[tuple[str, float]]) -> list[dict] | None:
    """Compare measured values against an independent model's reads, by label.

    Label matching is exact first, then containment - the escalation model and
    the transcription may format a series name slightly differently. Returns one
    record per measured series; None when the two lists do not cover the same
    series, which means the cross-check is inconclusive rather than agreeing.
    """
    if not measured or not model_reads:
        return None
    recs = []
    for label, mval in measured:
        read = next((v for l, v in model_reads if l == label), None)
        if read is None:
            read = next((v for l, v in model_reads
                         if label.lower() in l.lower() or l.lower() in label.lower()),
                        None)
        if read is None:
            return None
        recs.append({"label": label, "measured": mval, "read": read,
                     "delta": round(abs(mval - read), 2),
                     "agree": abs(mval - read) <= READ_TOLERANCE})
    return recs
