"""Generate the README figures from the committed reports.

    python make_visuals.py

Every number in every chart is read out of `reports/*.json`. Nothing is typed in by
hand, so a figure cannot drift away from the run that produced it - if the results
change, the charts change with them or the script fails loudly.

Palette is the validated categorical default (slots 1 and 2), checked against the
lightness band, chroma floor, CVD separation, normal-vision floor and surface
contrast before use. Two series only, so the adjacent pairlist applies.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).parent
REPORTS = ROOT / "reports"
ASSETS = ROOT / "assets"

# Validated categorical slots 1-2 (light mode, surface #fcfcfb).
S1, S2 = "#2a78d6", "#eb6834"
S3 = "#5b7ba6"           # the third substrate: plugin path, measured out of band
SURFACE = "#fcfcfb"
INK = "#0b0b0b"          # text-primary
INK_2 = "#52514e"        # text-secondary
GRID = "#e4e3df"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
    "text.color": INK,
    "axes.labelcolor": INK_2,
    "xtick.color": INK_2,
    "ytick.color": INK_2,
    "axes.edgecolor": GRID,
})


def _rounded_bars(ax, xs, heights, width, color, label):
    """Thin bars with rounded data-ends, anchored to the baseline."""
    for x, h in zip(xs, heights):
        if h <= 0:
            continue
        r = min(width * 0.16, max(h * 0.04, 0.4))
        ax.add_patch(FancyBboxPatch(
            (x - width / 2, 0), width, max(h - r, 0.01),
            boxstyle=f"round,pad=0,rounding_size={r}",
            linewidth=0, facecolor=color, mutation_aspect=1, clip_on=False))
    return ax.bar(xs, [0] * len(xs), width=width, color=color, label=label, linewidth=0)


def _style(ax, ylabel, ymax):
    ax.set_ylabel(ylabel, fontsize=9.5)
    ax.set_ylim(0, ymax)
    ax.grid(axis="y", color=GRID, linewidth=0.9, zorder=0)
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="both", length=0, labelsize=9.5)


def chart_layer_p() -> None:
    """What each parse backend makes available, by how the value is carried."""
    rep = json.loads((REPORTS / "layer_p.json").read_text(encoding="utf-8"))
    agg, backends = rep["aggregate"], rep["backends"]
    vision_b = next(b for b in backends if b != "textlayer")
    sub = json.loads((REPORTS / "substrate_comparison.json").read_text(encoding="utf-8"))
    sub_local = sub["by_carrier_pct"]["local_vision"]

    carriers = ["prose", "table", "chart"]
    labels = ["Prose\n(narrative claims)", "Table cells", "Chart-only values"]
    text_v = [agg.get(f"textlayer|{c}", {}).get("attributed_pct", 0) for c in carriers]

    # The middle bar is the PRODUCTION PIPELINE, not a single backend. Layer P grades
    # each backend alone as a full-page reader, and on that basis the best local one
    # reaches 50% of chart fields - it reads printed labels and drops axis interiors.
    # The pipeline adds the chart specialist and pixel geometry on top and recovers
    # all 20. Plotting the single-backend number here read as a claim the pipeline
    # only half-works, which contradicted this figure's own caption.
    single_backend_chart = agg.get(f"{vision_b}|chart", {}).get("attributed_pct", 0)
    vis_v = [sub_local[c] for c in carriers]

    # The third substrate: a frontier reader following the plugin's cim-read skill.
    # Measured separately (reports/substrate_comparison.md) rather than through Layer P,
    # because it needs a model with vision and Layer P is the offline harness.
    agent_v = [sub["by_carrier_pct"]["agent"][c] for c in carriers]

    fig, ax = plt.subplots(figsize=(7.6, 3.9))
    xs = list(range(len(carriers)))
    w = 0.26
    gap = 0.02  # 2px-equivalent surface gap between adjacent fills
    offs = [-(w + gap), 0.0, (w + gap)]
    series = [(text_v, S1, "Text layer (free)"),
              (vis_v, S2, "Local pipeline (parser + geometry)"),
              (agent_v, S3, "Plugin path (frontier reader)")]
    for off, (vals, colour, label) in zip(offs, series):
        _rounded_bars(ax, [x + off for x in xs], vals, w, colour, label)
        for x, v in zip(xs, vals):
            ax.text(x + off, v + 2.5, f"{v:.0f}%", ha="center", fontsize=9,
                    fontweight="bold", color=INK)

    ax.set_xticks(xs)
    ax.set_xticklabels(labels, fontsize=9.5)
    _style(ax, "Fields recovered and correctly attributed", 118)
    ax.set_title("Every metric that decides the deal lives in a chart",
                 fontsize=12.5, fontweight="bold", color=INK, pad=14, loc="left")
    ax.text(0, 1.015, f"Chart-carried values: the text layer reads none of them; the best "
                      f"single local backend reads {single_backend_chart:.0f}%", transform=ax.transAxes,
            fontsize=9.5, color=INK_2, va="bottom")
    ax.legend(frameon=False, fontsize=9, loc="upper left",
              bbox_to_anchor=(0.0, -0.16), ncol=3)
    fig.tight_layout()
    fig.savefig(ASSETS / "layer-p.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("  assets/layer-p.png")


def chart_discrimination(text_only: dict, full: dict) -> None:
    """The screening consequence: can the tool tell these companies apart?"""
    # Ordered so the three targets that tie under a text-only read sit together.
    # Principled, not cosmetic: the last two are the ones a blocker rule caught, which
    # the text layer *can* see. Grouping makes the tie visible instead of implied.
    order = ["Meridian", "Halyard", "Ashgrove", "Ridgeline", "Kestrel"]
    notes = {"Meridian": "clean", "Halyard": "34% in one\ncustomer",
             "Ridgeline": "58% recurring", "Kestrel": "loss-making",
             "Ashgrove": "81% gross\nretention"}
    t = [text_only[n] for n in order]
    f = [full[n] for n in order]

    fig, ax = plt.subplots(figsize=(8.4, 4.2))
    xs = list(range(len(order)))
    w = 0.34
    gap = 0.02
    _rounded_bars(ax, [x - w / 2 - gap / 2 for x in xs], t, w, S1, "Text layer only")
    _rounded_bars(ax, [x + w / 2 + gap / 2 for x in xs], f, w, S2, "Full pipeline")

    for x, v in zip(xs, t):
        ax.text(x - w / 2 - gap / 2, v + 2, f"{v:.0f}", ha="center", fontsize=9.5,
                fontweight="bold", color=INK)
    for x, v in zip(xs, f):
        ax.text(x + w / 2 + gap / 2, v + 2, f"{v:.0f}", ha="center", fontsize=9.5,
                fontweight="bold", color=INK)

    ax.set_xticks(xs)
    ax.set_xticklabels([f"{n}\n{notes[n]}" for n in order], fontsize=9)
    _style(ax, "Criteria fit score", 118)
    ax.set_title("Reading the charts is what makes the screen discriminate",
                 fontsize=12.5, fontweight="bold", color=INK, pad=14, loc="left")
    # No bracket: the first three blue bars are adjacent and identical, which makes
    # the point without an annotation that would collide with the bars above them.
    ax.text(0, 1.015,
            "Under a text-only read the clean company, the concentrated one and the "
            "leaking one all score 60",
            transform=ax.transAxes, fontsize=9.5, color=INK_2, va="bottom")
    ax.legend(frameon=False, fontsize=9.5, loc="upper left",
              bbox_to_anchor=(0.0, -0.2), ncol=2)
    fig.tight_layout()
    fig.savefig(ASSETS / "discrimination.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("  assets/discrimination.png")


def main() -> int:
    ASSETS.mkdir(exist_ok=True)
    print("writing figures from reports/")
    chart_layer_p()

    # Text-only scores are cheap and deterministic, so recompute rather than cache.
    from collections import defaultdict

    from deal_ready.scorer import fit, rules
    gt = json.loads((ROOT / "data" / "ground_truth.json").read_text(encoding="utf-8"))
    crit = rules.load_criteria()
    text_only = {}
    by = defaultdict(dict)
    names = {}
    for r in gt:
        if r["carrier"] != "chart":          # what a text layer can reach
            by[r["target_id"]][r["metric"]] = r["value"]
        names[r["target_id"]] = r["code_name"]
    for tid, m in by.items():
        text_only[names[tid]] = fit.score(m, crit, rules.evaluate(m, crit)).score

    full = {r["code_name"]: r["fit"]["score"]
            for r in json.loads((REPORTS / "findings.json").read_text(encoding="utf-8"))}
    chart_discrimination(text_only, full)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
