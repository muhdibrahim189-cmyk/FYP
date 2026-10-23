"""
report.py – Carbon Emission & Carbon Tax Statement (PDF).

Laid out after the sample statement (assets/Sample Report FYP.pdf): an agency
letterhead and footer on every page, then Part 1 company details, Part 2
monthly emissions (table, bar chart, summary) and Part 3 the carbon
tax invoice, one part per page.
"""
import io
from datetime import datetime, timedelta

import pandas as pd
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.legends import Legend
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    BaseDocTemplate, Frame, KeepTogether, PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle,
)

from data.emission_factors import company_display_name
from utils.analytics import monthly_ledger_summary
from utils.config import APP_LOGO_PATH, REPORT_PAYMENT_DAYS

# Report periods: label -> calendar months covered.
PERIODS = {"Annual": range(1, 13), "Q1": range(1, 4), "Q2": range(4, 7), "Q3": range(7, 10), "Q4": range(10, 13)}

# The sample statement's palette.
GREEN = colors.HexColor("#1A5D1F")        # letterhead name, title
RULE = colors.HexColor("#2D7C31")         # letterhead rule, Scope 1 bars, total-row line
BLUE = colors.HexColor("#1F6EB1")         # Scope 2 bars
OLIVE = colors.HexColor("#4F6228")        # part banners
NAVY = colors.HexColor("#1F497D")         # table headers
LIGHT_GREEN = colors.HexColor("#E8F4E8")  # label cells, amount-in-words box
LIGHT_BLUE = colors.HexColor("#DBE5F1")   # total rows
GRID = colors.HexColor("#D5DBD5")
MUTED = colors.HexColor("#6B7280")
RED = colors.HexColor("#C00000")

PAGE_W, PAGE_H = LETTER
MARGIN = 68
CONTENT_W = PAGE_W - 2 * MARGIN
S1_COL, S2_COL = "Scope 1 (t CO₂e)", "Scope 2 (t CO₂e)"
WORKBOOK = "Carbon_Emission_Data"
TCO2E = "tCO<sub>2</sub>e"


def _style(name: str, **kw) -> ParagraphStyle:
    return ParagraphStyle(name, fontName=kw.pop("font", "Helvetica"), fontSize=kw.pop("size", 8.5),
                          leading=kw.pop("leading", 11), **kw)


BODY = _style("body")
BODY_BOLD = _style("bodyBold", font="Helvetica-Bold")
INTRO = _style("intro", alignment=TA_JUSTIFY, leading=16)
TITLE = _style("title", font="Helvetica-Bold", size=15, leading=18, alignment=TA_CENTER, textColor=GREEN)
PERIOD = _style("period", size=8.5, alignment=TA_CENTER, textColor=MUTED)
BANNER = _style("banner", font="Helvetica-Bold", size=11, leading=13, textColor=colors.white)
CAPTION = _style("caption", size=7, textColor=MUTED)
HEAD = _style("head", font="Helvetica-Bold", size=7.5, leading=9, alignment=TA_CENTER, textColor=colors.white)
CELL = _style("cell", size=8, leading=10)
NUM = _style("num", size=8, leading=10, alignment=TA_RIGHT)
NUM_BOLD = _style("numBold", font="Helvetica-Bold", size=8, leading=10, alignment=TA_RIGHT)
CELL_BOLD = _style("cellBold", font="Helvetica-Bold", size=8, leading=10)
SMALL_GREY = _style("smallGrey", size=6.5, leading=8, textColor=MUTED)
PAYABLE = _style("payable", font="Helvetica-Bold", size=9.5, leading=12)
PAYABLE_NUM = _style("payableNum", font="Helvetica-Bold", size=9.5, leading=12, alignment=TA_RIGHT)
NOTES = _style("notes", size=6.5, leading=9, textColor=MUTED, leftIndent=6)
CENTER = _style("center", size=8, alignment=TA_CENTER)


# ── Data ───────────────────────────────────────────────────────────────────────
def statement_months(ledger: pd.DataFrame, company: str, year: int, period: str) -> pd.DataFrame:
    """Month, Scope 1, Scope 2 (tCO2e) for the company's months in the period; empty if none are recorded."""
    months = [f"{year}-{m:02d}" for m in PERIODS[period]]
    picked = ledger[(ledger["facility"] == company) & ledger["month"].isin(months)]
    summary = monthly_ledger_summary(picked)
    if summary.empty:
        return summary
    return summary.sort_values("Month", ignore_index=True)[["Month", S1_COL, S2_COL]]


_ONES = ("Zero One Two Three Four Five Six Seven Eight Nine Ten Eleven Twelve Thirteen Fourteen Fifteen "
         "Sixteen Seventeen Eighteen Nineteen").split()
_TENS = "_ _ Twenty Thirty Forty Fifty Sixty Seventy Eighty Ninety".split()
_SCALES = ((10**12, "Trillion"), (10**9, "Billion"), (10**6, "Million"), (1000, "Thousand"))


def _words(n: int) -> str:
    if n < 20:
        return _ONES[n]
    if n < 100:
        return _TENS[n // 10] + ("" if n % 10 == 0 else " " + _ONES[n % 10])
    if n < 1000:
        return _ONES[n // 100] + " Hundred" + ("" if n % 100 == 0 else " " + _words(n % 100))
    for value, name in _SCALES:
        if n >= value:
            return _words(n // value) + f" {name}" + ("" if n % value == 0 else " " + _words(n % value))
    raise AssertionError("unreachable")


def amount_in_words(amount: float) -> str:
    """'Ringgit Malaysia Five Hundred Fifty Million Four Hundred Thousand and Sen Twelve Only'."""
    ringgit, sen = divmod(round(amount * 100), 100)
    return f"Ringgit Malaysia {_words(ringgit)}" + (f" and Sen {_words(sen)}" if sen else "") + " Only"


def _money(value: float) -> str:
    return f"{value:,.2f}"


# ── Page furniture ─────────────────────────────────────────────────────────────
class _NumberedCanvas(Canvas):
    """Draws every page's letterhead and footer once the page count is known ('Page 2 of 3')."""

    def __init__(self, *args, letterhead: dict, **kwargs):
        super().__init__(*args, **kwargs)
        self._letterhead, self._pages = letterhead, []

    def showPage(self):
        self._pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        for number, state in enumerate(self._pages, start=1):
            self.__dict__.update(state)
            self._draw_furniture(number, len(self._pages))
            super().showPage()
        super().save()

    def _draw_furniture(self, page: int, pages: int) -> None:
        info, top = self._letterhead, PAGE_H
        self.drawImage(str(APP_LOGO_PATH), MARGIN, top - 92, width=54, height=54, mask="auto")
        x = MARGIN + 69
        self.setFillColor(GREEN)
        self.setFont("Helvetica-Bold", 12.5)
        self.drawString(x, top - 51, "SISTEM PEMANTAUAN KARBON")
        self.setFillColor(colors.black)
        self.setFont("Helvetica", 7.5)
        self.drawString(x, top - 63, "Carbon Emission Monitoring & Carbon Tax Assessment")
        self.setFillColor(MUTED)
        self.setFont("Helvetica", 6.5)
        self.drawString(x, top - 75, "[Agency address line 1], [Postcode City], [State], Malaysia")
        self.drawString(x, top - 85, "Tel: [03-XXXX XXXX]  |  Email: [email@agency.gov.my]")
        self.setFillColor(colors.black)
        self.setFont("Helvetica", 7)
        self.drawRightString(PAGE_W - MARGIN, top - 50, f"Ref. No.: {info['ref']}")
        self.drawRightString(PAGE_W - MARGIN, top - 60, f"Date: {info['issued']:%d %B %Y}")
        self.setStrokeColor(RULE)
        self.setLineWidth(2)
        self.line(MARGIN, top - 98, PAGE_W - MARGIN, top - 98)
        self.setLineWidth(0.6)
        self.line(MARGIN, top - 101.5, PAGE_W - MARGIN, top - 101.5)
        # Footer
        self.setStrokeColor(GRID)
        self.setLineWidth(0.5)
        self.line(MARGIN, 45, PAGE_W - MARGIN, 45)
        self.setFillColor(MUTED)
        self.setFont("Helvetica", 6.5)
        self.drawString(MARGIN, 33, f"Generated by Sistem Pemantauan Karbon on {info['issued']:%d/%m/%Y %H:%M}")
        self.setFont("Helvetica-Bold", 6.5)
        self.drawString(MARGIN + 212, 33, "CONFIDENTIAL")
        self.setFont("Helvetica", 7)
        self.drawRightString(PAGE_W - MARGIN, 33, f"Page {page} of {pages}")


# ── Building blocks ────────────────────────────────────────────────────────────
def _banner(text: str) -> Table:
    table = Table([[Paragraph(text, BANNER)]], colWidths=[CONTENT_W], rowHeights=[22])
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), OLIVE), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                               ("LEFTPADDING", (0, 0), (-1, -1), 8)]))
    return table


def _label_table(rows: list[list], widths: list[float], label_cols: tuple[int, ...] = (0,)) -> Table:
    """Key/value grid: bold labels on light green, values on white."""
    table = Table([[Paragraph(str(v), CELL_BOLD if c in label_cols else CELL) for c, v in enumerate(row)]
                   for row in rows], colWidths=widths, rowHeights=18)
    style = [("GRID", (0, 0), (-1, -1), 0.5, GRID), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
             ("LEFTPADDING", (0, 0), (-1, -1), 6)]
    style += [("BACKGROUND", (c, 0), (c, -1), LIGHT_GREEN) for c in label_cols]
    table.setStyle(TableStyle(style))
    return table


def _data_table(header: list[str], rows: list[list], widths: list[float], *, total=False,
                row_height: float | None = None) -> Table:
    """Navy-headed grid; numbers are pre-built Paragraphs; an optional light-blue TOTAL last row."""
    table = Table([[Paragraph(h, HEAD) for h in header], *rows], colWidths=widths, repeatRows=1,
                  rowHeights=[26] + [row_height] * len(rows) if row_height else None)
    style = [("BACKGROUND", (0, 0), (-1, 0), NAVY), ("GRID", (0, 0), (-1, -1), 0.5, GRID),
             ("LINEAFTER", (0, 0), (-2, 0), 0.5, colors.white), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]
    if total:
        style += [("BACKGROUND", (0, -1), (-1, -1), LIGHT_BLUE), ("LINEABOVE", (0, -1), (-1, -1), 1.2, RULE)]
    table.setStyle(TableStyle(style))
    return table


def _short(value: float) -> str:
    return f"{value / 1e6:.1f}M" if value >= 1e6 else f"{value / 1e3:.0f}k"


def _chart(months: pd.DataFrame, stacked: bool = True) -> Drawing:
    """
    Scope 1 (green) and Scope 2 (blue) per month: stacked into one bar (annual),
    or side by side with value labels so the small Scope 2 bar stays readable (quarterly).
    """
    width, height = CONTENT_W, 165
    drawing = Drawing(width, height)
    chart = VerticalBarChart()
    chart.x, chart.y, chart.width, chart.height = 36, 26, width - 50, height - 50
    chart.data = [list(months[S1_COL]), list(months[S2_COL])]
    chart.categoryAxis.categoryNames = [f"{pd.Timestamp(m):%b}\n{pd.Timestamp(m):%y}" for m in months["Month"]]
    chart.categoryAxis.labels.fontName, chart.categoryAxis.labels.fontSize = "Helvetica", 5.5
    chart.categoryAxis.labels.dy = -2
    chart.categoryAxis.tickDown = 4
    chart.bars[0].fillColor, chart.bars[1].fillColor = RULE, BLUE
    chart.bars.strokeColor = None
    if stacked:
        chart.categoryAxis.style = "stacked"
        chart.barSpacing, chart.groupSpacing = 0, 7 if len(months) > 6 else 30
        top = max((months[S1_COL] + months[S2_COL]).max(), 1)
    else:
        chart.barSpacing, chart.groupSpacing = 4, 40
        chart.barLabelFormat = _short
        chart.barLabels.fontName, chart.barLabels.fontSize, chart.barLabels.nudge = "Helvetica", 6, 6
        top = max(months[S1_COL].max(), months[S2_COL].max(), 1) * 1.08  # headroom for the labels
    step = 1e6 if top > 2e6 else 10 ** int(len(str(int(top))) - 1)
    while top / step > 5:  # at most ~5 axis labels
        step *= 2
    chart.valueAxis.valueMin, chart.valueAxis.valueStep = 0, step
    chart.valueAxis.valueMax = top * 1.01  # like the sample: the axis stops just above the tallest bar
    chart.valueAxis.labels.fontName, chart.valueAxis.labels.fontSize = "Helvetica", 5.5
    chart.valueAxis.labelTextFormat = _short
    chart.valueAxis.visibleGrid, chart.valueAxis.gridStrokeColor = True, GRID
    chart.valueAxis.gridStrokeWidth = 0.4
    drawing.add(chart)
    legend = Legend()
    legend.x, legend.y = width - 165, height - 6
    legend.columnMaximum, legend.deltax = 1, 70
    legend.fontName, legend.fontSize = "Helvetica", 6.5
    legend.boxAnchor, legend.dx, legend.dy = "nw", 8, 8
    legend.alignment = "right"  # swatch first, then the label
    legend.strokeColor = colors.black
    legend.strokeWidth = 0.4
    legend.colorNamePairs = [(RULE, "Scope 1"), (BLUE, "Scope 2")]
    drawing.add(legend)
    return drawing


# ── Statement ──────────────────────────────────────────────────────────────────
def build_statement(ledger: pd.DataFrame, company: str, year: int, period: str, tax_rate: float,
                    issued: datetime | None = None) -> bytes:
    """
    The statement as PDF bytes. ``ledger`` is the approved ledger (workbook
    totals plus data entry). Raises ValueError when the period has no data.
    """
    months = statement_months(ledger, company, year, period)
    if months.empty:
        raise ValueError(f"No emission data for {company} in {period} {year}.")
    issued = issued or datetime.now()
    due = issued + timedelta(days=REPORT_PAYMENT_DAYS)
    first, last = pd.Timestamp(months["Month"].iloc[0]), pd.Timestamp(months["Month"].iloc[-1])
    span = f"{first:%b %Y} to {last:%b %Y}"
    code = company.upper().replace(" ", "")
    ref = f"SPK/CT/{code}/{first:%Y%m}-{last:%Y%m}"
    invoice_no = f"INV-{code}-{first:%Y%m}-{last:%Y%m}"
    name = company_display_name(company)
    months["Total"] = months[S1_COL] + months[S2_COL]
    months["Tax"] = months["Total"] * tax_rate
    s1, s2, total = months[S1_COL].sum(), months[S2_COL].sum(), months["Total"].sum()
    payable = total * tax_rate
    picked = ledger[(ledger["facility"] == company) & ledger["month"].isin(months["Month"])]
    basis = sorted(picked.loc[picked["submitted_by"] == WORKBOOK, "notes"].dropna().unique())
    entries = int((picked["submitted_by"] != WORKBOOK).sum())
    data_basis = "; ".join(basis) + (f"; plus {entries} data-entry record(s)" if entries else "")
    n = len(months)

    story = [
        # Part 1
        Spacer(1, 8),
        Paragraph("CARBON EMISSION &amp; CARBON TAX STATEMENT", TITLE),
        Spacer(1, 3),
        Paragraph(f"For the period {span}" + ("" if period == "Annual" else f" ({period} {year})"), PERIOD),
        Spacer(1, 12),
        Paragraph("This statement reports the monthly greenhouse gas (GHG) emissions of the company named in Part 1 "
                  "for the reporting period stated, and the carbon tax payable on those emissions. Emissions are "
                  f"reported in tonnes of carbon dioxide equivalent ({TCO2E}) following the scope definitions of "
                  "the GHG Protocol Corporate Standard. The statement contains the following parts:", INTRO),
        Spacer(1, 8),
    ]
    parts = Table([[Paragraph(p, BODY_BOLD), Paragraph(t, BODY)] for p, t in (
        ("Part 1", "Company details"), ("Part 2", "Monthly carbon emission data, chart and summary"),
        ("Part 3", "Carbon tax statement / invoice"))], colWidths=[70, CONTENT_W - 70], rowHeights=16)
    parts.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.5, GRID), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    story += [parts, Spacer(1, 13), _banner("PART 1: COMPANY DETAILS"), Spacer(1, 5), _label_table([
        ["Company Name", f"<b>{name}</b>"],
        ["Reporting Period", f"{span} ({n} month{'s' if n != 1 else ''})"],
        ["Statement Reference No.", ref],
        ["Date of Issue", f"{issued:%d %B %Y}"],
        ["Emission Scopes Reported", "Scope 1 (direct) and Scope 2 (purchased electricity)"],
        ["Data Basis", data_basis or "Data entry"],
    ], [152, CONTENT_W - 152]), PageBreak()]

    # Part 2
    rows = [[Paragraph(str(i), CENTER), Paragraph(f"{pd.Timestamp(r.Month):%b %Y}", CELL),
             Paragraph(_money(r[S1_COL]), NUM), Paragraph(_money(r[S2_COL]), NUM), Paragraph(_money(r.Total), NUM),
             Paragraph(_money(r.Tax), NUM)] for i, (_, r) in enumerate(months.iterrows(), start=1)]
    rows.append(["", Paragraph("TOTAL", CELL_BOLD), Paragraph(_money(s1), NUM_BOLD), Paragraph(_money(s2), NUM_BOLD),
                 Paragraph(_money(total), NUM_BOLD), Paragraph(_money(payable), NUM_BOLD)])
    high, low = months.loc[months["Total"].idxmax()], months.loc[months["Total"].idxmin()]
    story += [
        _banner("PART 2: MONTHLY CARBON EMISSION DATA"), Spacer(1, 6),
        Paragraph("Table 2.1: Monthly Scope 1 and Scope 2 emissions and the carbon tax charged for each month.",
                  CAPTION), Spacer(1, 4),
        _data_table(["No.", "Month", f"Scope 1<br/>({TCO2E})", f"Scope 2<br/>({TCO2E})",
                     f"Total Emission<br/>({TCO2E})", "Carbon Tax<br/>(RM)"],
                    rows, [33, 81, 90, 90, 96, CONTENT_W - 390], total=True, row_height=18.8),
        Spacer(1, 8),
        KeepTogether([Paragraph(f"Figure 2.1: Monthly carbon emissions by scope ({TCO2E})", CAPTION), _chart(months, stacked=period == "Annual")]),
        Spacer(1, 8),
        Paragraph("Table 2.2: Emission summary", CAPTION), Spacer(1, 4),
        _label_table([
            ["Average monthly", f"{_money(total / n)} {TCO2E}", "Scope 1 share", f"{s1 / total:.1%}"],
            ["Highest month", f"{pd.Timestamp(high.Month):%b %Y}: {_money(high.Total)} {TCO2E}", "Scope 2 share",
             f"{s2 / total:.1%}"],
            ["Lowest month", f"{pd.Timestamp(low.Month):%b %Y}: {_money(low.Total)} {TCO2E}", "Months reported",
             str(n)],
        ], [86, 190, 86, CONTENT_W - 362], label_cols=(0, 2)),
        PageBreak(),
    ]

    # Part 3
    bill_to = [Paragraph("<b>BILL TO</b>", _style("bt", size=8.5)), Paragraph(name, _style("bn", size=8.5)),
               Paragraph("[Registered address of the company]", _style("ba", size=8.5, textColor=MUTED))]
    invoice_info = Table([[Paragraph(f"<b>{k}</b>", _style("k", size=8)), Paragraph(v, _style("v", size=8))] for k, v in (
        ("Invoice No.", invoice_no), ("Statement Ref.", ref), ("Invoice Date", f"{issued:%d/%m/%Y}"),
        ("Due Date", f"{due:%d/%m/%Y}"),
        ("Status", '<font color="#C00000"><b>UNPAID</b></font>'))], colWidths=[98, 140], rowHeights=15)
    invoice_info.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    header = Table([[bill_to, invoice_info]], colWidths=[238, CONTENT_W - 238])
    header.setStyle(TableStyle([("BOX", (0, 0), (0, 0), 0.5, GRID), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                ("LEFTPADDING", (0, 0), (0, 0), 8), ("TOPPADDING", (0, 0), (0, 0), 8),
                                ("BOTTOMPADDING", (0, 0), (0, 0), 30), ("LEFTPADDING", (1, 0), (1, 0), 12)]))
    period_line = f"{first:%b %Y} – {last:%b %Y}"

    def description(text: str) -> list:
        return [Paragraph(text, CELL), Paragraph(period_line, SMALL_GREY)]

    invoice_rows = [
        [Paragraph("1", CENTER),
         description("Carbon tax on Scope 1 emissions (direct: fuel combustion)"),
         Paragraph(_money(s1), NUM), Paragraph(_money(tax_rate), NUM), Paragraph(_money(s1 * tax_rate), NUM)],
        [Paragraph("2", CENTER),
         description("Carbon tax on Scope 2 emissions (indirect: purchased electricity)"),
         Paragraph(_money(s2), NUM), Paragraph(_money(tax_rate), NUM), Paragraph(_money(s2 * tax_rate), NUM)],
    ]
    totals = Table([
        [Paragraph("Subtotal", CELL), Paragraph(f"RM {_money(payable)}", NUM)],
        [Paragraph("Less: Exemption / Allowance", CELL), Paragraph("RM 0.00", NUM)],
        [Paragraph("Less: Carbon Credits Offset", CELL), Paragraph("RM 0.00", NUM)],
        [Paragraph("TOTAL AMOUNT PAYABLE", PAYABLE), Paragraph(f"RM {_money(payable)}", PAYABLE_NUM)],
    ], colWidths=[136, 112], rowHeights=[19, 19, 19, 22], hAlign="RIGHT")
    totals.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, 2), 0.5, GRID), ("BACKGROUND", (0, 3), (-1, 3), LIGHT_BLUE),
                                ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    words = Table([[Paragraph(f"<b>Amount in words:</b> {amount_in_words(payable)}", CELL)]],
                  colWidths=[CONTENT_W], rowHeights=20)
    words.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), LIGHT_GREEN), ("BOX", (0, 0), (-1, -1), 0.6, RULE),
                               ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 6)]))
    pay = _style("pay", size=9, leading=12, leftIndent=6)
    story += [
        _banner("PART 3: CARBON TAX STATEMENT / INVOICE"), Spacer(1, 6), header, Spacer(1, 7),
        _data_table(["No.", "Description", f"Taxable Emission<br/>({TCO2E})", f"Rate<br/>(RM / {TCO2E})", "Amount (RM)"],
                    invoice_rows, [33, 204, 85, 66, CONTENT_W - 388]),
        Spacer(1, 4), totals, Spacer(1, 10), words, Spacer(1, 12),
        Paragraph("<b>Payment Instructions</b>", pay),
        Paragraph(f"Please make payment on or before <b>{due:%d %B %Y}</b> and quote the invoice number "
                  f"<b>{invoice_no}</b> as the payment reference.", pay),
        Paragraph("Bank: [Bank name]  |  Account name: [Agency account name]  |  Account no.: [XXXX-XXXX-XXXX]", pay),
        Spacer(1, 10),
        Paragraph("<b>Notes</b>", _style("nh", size=7, textColor=MUTED, leftIndent=6)),
        Paragraph(f"1. Carbon tax is calculated as taxable emissions ({TCO2E}) × RM {tax_rate:,.2f} per {TCO2E}.",
                  NOTES),
        Paragraph("2. Emissions are calculated using SEDG GHG Emissions Calculator factors (GHG Protocol cross-sector "
                  "tools for Scope 1; Suruhanjaya Tenaga grid emission factors for Scope 2).",
                  NOTES),
        Paragraph("3. Any dispute on this statement must be raised in writing within 14 days of the date of issue.",
                  NOTES),
    ]

    buffer = io.BytesIO()
    doc = BaseDocTemplate(buffer, pagesize=LETTER, leftMargin=MARGIN, rightMargin=MARGIN, topMargin=112,
                          bottomMargin=60, title=f"Carbon Tax Statement {company} {span}",
                          author="Sistem Pemantauan Karbon")
    doc.addPageTemplates([PageTemplate(frames=[Frame(MARGIN, 60, CONTENT_W, PAGE_H - 172, id="body",
                                                     leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)])])
    letterhead = {"ref": ref, "issued": issued}
    doc.build(story, canvasmaker=lambda *a, **kw: _NumberedCanvas(*a, letterhead=letterhead, **kw))
    return buffer.getvalue()
