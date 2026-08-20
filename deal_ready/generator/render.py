"""Render a target profile into a CIM-shaped PDF deck.

The deck matters more than it looks like it should. Three things have to be true or
the parse comparison downstream measures nothing:

1. **The text layer must be real.** ReportLab writes selectable text, so a
   born-digital extractor genuinely gets the prose and the table cells. If we
   rendered whole pages as images, every parser would score the same and the
   experiment would be a tautology.

2. **Charts must be raster.** A chart is a PNG pasted into the page. Values carried
   only by a chart are therefore absent from the text layer *by construction*, not
   by our forgetting to include them.

3. **Page numbers are recorded, not guessed.** Each section is pinned to a known
   page, and ground truth stores the page the value actually landed on. Retrieval
   recall is scored against that, so the router has a real target to hit.

One deliberate nuance in the chart design. Real CIM charts are inconsistent: pie
charts usually carry data labels, trend lines often do not. We mirror that, and
record `labelled` per chart. It gives the parse comparison an honest middle case -
OCR can sometimes recover the *digits* off a labelled chart while losing which
series they belong to, which is a more interesting and more truthful result than a
flat "OCR scores zero".
"""

from __future__ import annotations

import io
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # no display on a build box
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .profiles import METRIC_LABELS

# Page layout for the deck. Section -> 1-indexed page. Fixed on purpose: the
# generator must know where it put every number.
PAGE_MAP = {
    "cover": 1,
    "executive_summary": 2,
    "the_business": 3,
    "market": 4,
    "product": 5,
    "customers": 6,      # concentration chart lives here
    "retention": 7,      # retention chart lives here
    "financials": 8,     # the financial table lives here
    "management": 9,
    "technology": 10,
    "growth": 11,
    "process": 12,
}
TOTAL_PAGES = max(PAGE_MAP.values())

BRAND = colors.HexColor("#1F3A5F")
MUTED = colors.HexColor("#5A6B7D")
RULE = colors.HexColor("#C9D3DD")


def _styles():
    ss = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "cimTitle", parent=ss["Title"], fontName="Helvetica-Bold",
            fontSize=26, leading=31, textColor=BRAND, spaceAfter=18,
        ),
        "h1": ParagraphStyle(
            "cimH1", parent=ss["Heading1"], fontName="Helvetica-Bold",
            fontSize=15, leading=19, textColor=BRAND, spaceBefore=0, spaceAfter=12,
        ),
        "body": ParagraphStyle(
            "cimBody", parent=ss["BodyText"], fontName="Helvetica",
            fontSize=10.5, leading=16, alignment=TA_JUSTIFY, spaceAfter=10,
        ),
        "muted": ParagraphStyle(
            "cimMuted", parent=ss["BodyText"], fontName="Helvetica-Oblique",
            fontSize=9, leading=13, textColor=MUTED, spaceAfter=8,
        ),
    }


def _money(v: int) -> str:
    """Format whole dollars the way a broker deck would."""
    sign = "-" if v < 0 else ""
    a = abs(v)
    if a >= 1_000_000:
        return f"{sign}${a/1_000_000:.1f}M"
    if a >= 1_000:
        return f"{sign}${a/1_000:.0f}K"
    return f"{sign}${a:,}"


def _chart_png(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=170, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    return buf.getvalue()


def _concentration_chart(top1: float, top5: float) -> bytes:
    """Labelled bar chart. Data labels are baked into the raster.

    Labelled on purpose - a determined OCR pass may recover these digits, and the
    parse comparison is more honest for containing a case it can partially win.
    """
    others = max(0.0, 100.0 - top5)
    next4 = max(0.0, top5 - top1)
    labels = ["Largest\ncustomer", "Customers\n2-5", "All other\ncustomers"]
    vals = [top1, next4, others]
    fig, ax = plt.subplots(figsize=(6.2, 3.1))
    bars = ax.bar(labels, vals, color=["#1F3A5F", "#4E7CA8", "#B7C6D4"], width=0.55)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 1.5, f"{v:.0f}%",
                ha="center", va="bottom", fontsize=11, fontweight="bold",
                color="#1F3A5F")
    ax.set_ylabel("Share of ARR (%)", fontsize=9)
    ax.set_ylim(0, max(vals) * 1.25 + 6)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=9)
    # Cumulative top-five callout, drawn INTO the raster.
    # Without this the chart states its components (largest, next four) but never the
    # top-five total, so scoring "did the parser recover top5" would be scoring
    # mental arithmetic rather than reading. Real concentration slides carry this
    # callout; including it keeps the measurement about the page, not about addition.
    ax.text(0.985, 0.94, f"Top 5 customers: {top5:.0f}% of ARR",
            transform=ax.transAxes, ha="right", va="top", fontsize=9.5,
            color="#1F3A5F",
            bbox=dict(boxstyle="round,pad=0.35", facecolor="#EEF2F6",
                      edgecolor="#C9D3DD", linewidth=0.8))
    return _chart_png(fig)


def _retention_chart(grr: float, nrr: float) -> bytes:
    """Unlabelled trend chart. Values must be read off the axis.

    No data labels: recovering these requires understanding the plot, not reading
    characters. This is the clean control in the parse comparison.
    """
    years = ["FY22", "FY23", "FY24", "FY25"]
    grr_series = [grr - 2.4, grr - 1.1, grr - 0.5, grr]
    nrr_series = [nrr - 5.0, nrr - 2.7, nrr - 1.2, nrr]
    fig, ax = plt.subplots(figsize=(6.2, 3.1))
    ax.plot(years, grr_series, marker="o", linewidth=2.2, color="#1F3A5F",
            label="Gross revenue retention")
    ax.plot(years, nrr_series, marker="s", linewidth=2.2, color="#C77B30",
            label="Net revenue retention")
    lo = min(grr_series + nrr_series) - 6
    hi = max(grr_series + nrr_series) + 6
    ax.set_ylim(lo, hi)
    ax.set_ylabel("Percent", fontsize=9)
    ax.legend(fontsize=8.5, frameon=False, loc="lower right")
    ax.grid(axis="y", color=RULE.hexval().replace("0x", "#")[:7], alpha=0.35)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=9)
    return _chart_png(fig)


def _financial_table(vals: dict) -> Table:
    """A real table with a text layer - rows a born-digital parser can reach."""
    rows = [
        ["Metric", "FY25", "Basis"],
        [METRIC_LABELS["arr_usd"], _money(vals["arr_usd"]), "Contracted, annualised"],
        [METRIC_LABELS["mrr_usd"], _money(vals["mrr_usd"]), "Exit month"],
        [METRIC_LABELS["gross_margin_pct"], f"{vals['gross_margin_pct']:.0f}%", "Excl. amortisation"],
        [METRIC_LABELS["ebitda_usd"], _money(vals["ebitda_usd"]), "Adjusted"],
    ]
    t = Table(rows, colWidths=[2.9 * inch, 1.5 * inch, 2.1 * inch], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (1, 1), (1, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F5F8")]),
        ("GRID", (0, 0), (-1, -1), 0.4, RULE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return t


def render_cim(profile: dict, out_path: Path) -> list[dict]:
    """Write one CIM deck and return its ground-truth records.

    Returns one record per metric:
        {target_id, metric, value, carrier, page, labelled}
    `page` is where the renderer actually placed it, so retrieval is scored against
    fact rather than intention.
    """
    st = _styles()
    vals = {k: v["value"] for k, v in profile["metrics"].items()}
    carriers = {k: v["carrier"] for k, v in profile["metrics"].items()}
    nar = profile["narrative"]
    flow = []

    def page(name):
        return PAGE_MAP[name]

    # 1 - cover
    flow += [
        Spacer(1, 1.7 * inch),
        Paragraph("Confidential Information Memorandum", st["title"]),
        Paragraph(f"<b>Project {profile['code_name']}</b>", st["h1"]),
        Paragraph(
            f"{profile['legal_name']} &nbsp;|&nbsp; {profile['vertical'].title()}",
            st["body"]),
        Spacer(1, 0.35 * inch),
        Paragraph(
            "This document is confidential and is provided solely for the purpose of "
            "evaluating a potential transaction. It may not be reproduced or "
            "distributed without written consent.", st["muted"]),
        Spacer(1, 0.9 * inch),
        Paragraph("Prepared by Cardinal &amp; Vale Advisors &nbsp;·&nbsp; FY25", st["muted"]),
        PageBreak(),
    ]

    # 2 - executive summary  (prose carriers land here)
    flow += [Paragraph("Executive summary", st["h1"])]
    flow += [Paragraph(nar["positioning"], st["body"])]
    prose_bits = []
    if carriers.get("recurring_pct") == "prose":
        prose_bits.append(
            f"Approximately <b>{vals['recurring_pct']:.0f}%</b> of total revenue is "
            f"recurring subscription revenue")
    if carriers.get("yoy_growth_pct") == "prose":
        prose_bits.append(
            f"revenue grew <b>{vals['yoy_growth_pct']:.0f}%</b> year over year in FY25")
    if prose_bits:
        flow += [Paragraph(
            f"The business is a {profile['vertical']} platform founded in "
            f"{profile['founded']} and employing {profile['employees']} people from its "
            f"{profile['hq']} headquarters. " + "; ".join(prose_bits) + ".", st["body"])]
    flow += [Paragraph(nar["moat"], st["body"]), PageBreak()]

    # 3 - the business
    flow += [
        Paragraph("The business", st["h1"]),
        Paragraph(nar["positioning"], st["body"]),
        Paragraph(
            "Revenue is contracted under written agreements with defined renewal terms. "
            "Implementation is delivered by the company's own team, and ongoing support "
            "is included in the subscription for all customer tiers.", st["body"]),
        Paragraph(nar["moat"], st["body"]),
        PageBreak(),
    ]

    # 4 - market  (filler, but plausible - retrieval needs distractors)
    flow += [
        Paragraph("Market overview", st["h1"]),
        Paragraph(
            f"The {profile['vertical']} market is fragmented, with a long tail of "
            "regional providers and no single vendor holding a dominant national share. "
            "Buyers are operationally conservative and replacement cycles are measured in "
            "years rather than quarters.", st["body"]),
        Paragraph(
            "Management believes the addressable market continues to expand as smaller "
            "operators retire spreadsheet-based and paper processes, and as regulatory "
            "reporting obligations increase the cost of manual compliance.", st["body"]),
        PageBreak(),
    ]

    # 5 - product
    flow += [
        Paragraph("Product", st["h1"]),
        Paragraph(
            "The platform is delivered as a hosted application with role-based access, "
            "configurable workflow, and an audit trail across every transaction. "
            "Customers access the system through a browser; a mobile companion "
            "application covers field workflows.", st["body"]),
        Paragraph(
            "The published integration surface covers accounting, payments and reporting "
            "endpoints, and a documented API supports customer-built extensions.",
            st["body"]),
        PageBreak(),
    ]

    # 6 - customers  (LABELLED concentration chart; values appear nowhere in text)
    flow += [
        Paragraph("Customer base", st["h1"]),
        Paragraph(
            "The customer base is contracted on written agreements with staggered renewal "
            "dates. The chart below sets out the distribution of annual recurring revenue "
            "across the customer base.", st["body"]),
        Image(io.BytesIO(_concentration_chart(vals["top1_customer_pct"],
                                              vals["top5_customer_pct"])),
              width=6.2 * inch, height=3.1 * inch),
        Spacer(1, 0.12 * inch),
        Paragraph("Distribution of annual recurring revenue by customer, FY25.", st["muted"]),
        PageBreak(),
    ]

    # 7 - retention  (UNLABELLED chart; values readable only off the axis)
    flow += [
        Paragraph("Retention", st["h1"]),
        Paragraph(
            "Retention has been measured on a consistent basis across the periods shown. "
            "Gross retention excludes expansion; net retention includes expansion, "
            "upsell and contraction within the existing base.", st["body"]),
        Image(io.BytesIO(_retention_chart(vals["grr_pct"], vals["nrr_pct"])),
              width=6.2 * inch, height=3.1 * inch),
        Spacer(1, 0.12 * inch),
        Paragraph("Gross and net revenue retention, FY22 to FY25.", st["muted"]),
        PageBreak(),
    ]

    # 8 - financials  (the table)
    flow += [
        Paragraph("Financial summary", st["h1"]),
        Paragraph(
            "The table below summarises FY25 performance. Figures are unaudited and "
            "prepared by management.", st["body"]),
        _financial_table(vals),
        Spacer(1, 0.16 * inch),
        Paragraph(
            "Adjusted EBITDA reflects add-backs for one-time transaction preparation "
            "costs and non-recurring legal expenses.", st["muted"]),
        PageBreak(),
    ]

    # 9 - management  (the key-person signal lives in this prose)
    flow += [
        Paragraph("Management and organisation", st["h1"]),
        Paragraph(nar["management"], st["body"]),
        Paragraph(
            f"Total headcount is {profile['employees']}. The company operates from a "
            f"single office in {profile['hq']} with a distributed support function.",
            st["body"]),
        PageBreak(),
    ]

    # 10 - technology  (the legacy-stack signal lives in this prose)
    flow += [
        Paragraph("Technology", st["h1"]),
        Paragraph(nar["tech"], st["body"]),
        Paragraph(
            "Security controls include role-based access, encryption in transit and at "
            "rest, and an annual third-party penetration test.", st["body"]),
        PageBreak(),
    ]

    # 11 - growth
    flow += [
        Paragraph("Growth initiatives", st["h1"]),
        Paragraph(
            "Management has identified three near-term initiatives: expanding the "
            "integration catalogue, introducing usage-based modules alongside the core "
            "subscription, and extending into adjacent operator segments already served "
            "informally today.", st["body"]),
        PageBreak(),
    ]

    # 12 - process
    flow += [
        Paragraph("Transaction process", st["h1"]),
        Paragraph(
            "Indications of interest are requested by the date set out in the process "
            "letter. Management presentations will be scheduled with selected parties, "
            "and access to a virtual data room will follow execution of a "
            "confidentiality agreement.", st["body"]),
        Paragraph("Enquiries should be directed to the advisor named on the cover.",
                  st["muted"]),
    ]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    SimpleDocTemplate(
        str(out_path), pagesize=letter,
        leftMargin=0.95 * inch, rightMargin=0.95 * inch,
        topMargin=0.95 * inch, bottomMargin=0.85 * inch,
        title=f"Project {profile['code_name']} - Confidential Information Memorandum",
        author="Cardinal & Vale Advisors",
    ).build(flow)

    # Ground truth, written as the document is written.
    carrier_page = {
        "prose": page("executive_summary"),
        "table": page("financials"),
    }
    chart_page = {
        "top1_customer_pct": (page("customers"), True),
        "top5_customer_pct": (page("customers"), True),
        "grr_pct": (page("retention"), False),
        "nrr_pct": (page("retention"), False),
    }

    records = []
    for metric, meta in profile["metrics"].items():
        carrier = meta["carrier"]
        if carrier == "chart":
            pg, labelled = chart_page[metric]
        else:
            pg, labelled = carrier_page[carrier], None
        records.append({
            "target_id": profile["target_id"],
            "code_name": profile["code_name"],
            "metric": metric,
            "label": METRIC_LABELS[metric],
            "value": meta["value"],
            "carrier": carrier,
            "labelled_in_chart": labelled,
            "page": pg,
            "total_pages": TOTAL_PAGES,
        })
    return records
