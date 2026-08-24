"""Measure chart values from pixels. The model reads glyphs; code measures geometry.

A vision model reading a value off an axis is estimating: point sits between the 105
and 110 gridlines, a bit below the middle, call it 108.2. The estimate lands within
tenths of the truth and still misses it, which is exactly why axis-read values used
to ship flagged at a measured ceiling. But a rendered chart is also just an image
with fixed geometry - series in consistent colors, gridlines at printed tick values,
a marker at each data point. Given the tick values, the value of an endpoint is not
an estimation problem at all. It is a ruler.

Division of labour, the same one the rest of this repo runs:

    model   reads the tick-label glyphs and names the series (recognition - the task
            small vision models measurably do at 100%)
    code    finds the series pixels, locates the endpoint marker, interpolates
            against the gridlines (arithmetic - deterministic, re-runnable offline)

Everything in this module is pure geometry over an RGB array. No model call, no
network, no cache of its own: given the chart's bytes and the tick values it returns
the same numbers forever, which is what lets `run_checks.py` re-verify every
axis-read value from committed artifacts without a GPU.

Honest limits: this is geometry for rendered charts with gridlines and colour-coded
series - the common case in a CIM exhibit, not a universal one. Photos, 3-D renders
and label-less log axes are out of scope, and the callers fall back to the model's
own transcription when the geometry does not resolve.
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

# The FY25 marker is the rightmost blob of a series. Its center is read from the
# right cap - the last few columns, which contain marker and no line.
_ENDPOINT_CAP_COLS = 3

# Anti-aliased text is neutral gray, which can sit inside the per-channel tolerance
# of a dark series colour - and legend text sits right of the last marker. Requiring
# channel spread in the mask excludes it: gray text has none, series ink does.
MASK_SPREAD_MIN = 15


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
        r, g, b = (k // 100_000) * 24, ((k // 1_000) % 100) * 24, (k % 1_000) * 24
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


_LINE_SPAN = 80          # columns of line fitted behind the marker
_LINE_SKIP = 16          # columns skipped: marker half-width plus anti-aliasing
_MARKER_HALF = 8         # the fit is evaluated at the marker's center, not its edge
_LINE_RUN_TOL = 4.0      # px a column's band center may move between neighbours
_LINE_TRIM = 0.8         # px; residuals beyond this are refit without (marker halo)


def line_fit_y(rgb: np.ndarray, color: tuple[int, int, int],
               x_end: int, y_hint: float) -> float | None:
    """Least-squares centerline of the series line just left of its end marker,
    evaluated at `x_end`.

    The marker is ~13px of ink, and the rasterized center of a small disc depends
    on the sub-pixel phase of the true point - one chart's disc measured a clean,
    symmetric 1.3px low, worth exactly the 0.1 that separated a pass from a miss.
    The line entering it is hundreds of columns of the same ink; fitting its
    centerline averages the phase noise out and extrapolates to the marker's x.

    The walk starts clear of the marker (its columns are flat at the marker's own
    center, and including them tilts the fit) and tracks the contiguous band nearest
    the previous column's center, so a legend swatch crossing the segment cannot
    hijack the fit - it is a different band, farther from the tracker. The fitted
    line is evaluated at the marker's center: at the marker's right edge the
    extrapolation would add slope x radius, which on these charts is the difference
    between 86.0 and 86.1.
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
    # tilts the fit and shows up as a systematic +0.1 on rising series. One
    # trimmed refit removes it: drop the worst residuals, refit what remains.
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


_ROW_RE = re.compile(r"^(.+?)\s*\|\s*(?:.+?\|\s*)*([0-9.]+)\s*%\s*\|?\s*$")
_SEP_RE = re.compile(r"^[\s|:-]+$")


def parse_series_rows(crop_text: str) -> list[tuple[str, float]]:
    """(label, last percentage) per series row of a crop transcription.

    The transcription's own values are the model's estimates; they are used here
    only to join measured series to their labels - the guess sits next to the
    measurement, and the assignment that agrees with the guesses wins.
    """
    rows: list[tuple[str, float]] = []
    for line in crop_text.splitlines():
        line = line.strip()
        if not line or _SEP_RE.match(line):
            continue
        m = _ROW_RE.match(line)
        if m:
            try:
                rows.append((m.group(1).strip().strip("*"), float(m.group(2))))
            except ValueError:
                continue
    return rows


def measured_block(crop_text: str, values: list[float]) -> str | None:
    """The text appended to a crop transcription when measurement resolved.

    Joins measured series values to the transcription's row labels: with the guesses
    beside them, the assignment (identity or permutation) that minimises total
    distance wins. Returns None when the transcription does not parse into matching
    rows - the transcription then stands alone, as before.
    """
    rows = parse_series_rows(crop_text)
    if not rows or len(rows) != len(values):
        return None
    best, best_err = None, None
    for perm in permutations(range(len(values))):
        err = sum(abs(rows[i][1] - values[perm[i]]) for i in range(len(rows)))
        if best_err is None or err < best_err:
            best, best_err = perm, err
    lines = ["[Measured from the chart's pixels - authoritative over the "
             "estimates above]"]
    for i, (label, _guess) in enumerate(rows):
        lines.append(f"{label}: {values[best[i]]:.1f}% (measured off the axis)")
    return "\n".join(lines)
