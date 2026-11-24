"""
Builds docs/AFAMA_Harness_Technical_Manual.pdf

    venv\\Scripts\\python docs\\build_manual.py

Requires: reportlab (pip install -r docs/requirements-docs.txt)
"""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, Preformatted, KeepTogether, NextPageTemplate, PageBreakIfNotEmpty,
)
from reportlab.platypus.tableofcontents import TableOfContents

OUT = Path(__file__).resolve().parent / "AFAMA_Harness_Technical_Manual.pdf"

# ── Fonts ────────────────────────────────────────────────────────────────
FONT_DIR = Path("C:/Windows/Fonts")
try:
    pdfmetrics.registerFont(TTFont("Body", str(FONT_DIR / "arial.ttf")))
    pdfmetrics.registerFont(TTFont("Body-Bold", str(FONT_DIR / "arialbd.ttf")))
    pdfmetrics.registerFont(TTFont("Body-Italic", str(FONT_DIR / "ariali.ttf")))
    pdfmetrics.registerFont(TTFont("Mono", str(FONT_DIR / "consola.ttf")))
    pdfmetrics.registerFontFamily("Body", normal="Body", bold="Body-Bold",
                                  italic="Body-Italic", boldItalic="Body-Bold")
    BODY, BOLD, MONO = "Body", "Body-Bold", "Mono"
except Exception:  # non-Windows fallback
    BODY, BOLD, MONO = "Helvetica", "Helvetica-Bold", "Courier"

# ── Palette ──────────────────────────────────────────────────────────────
NAVY = colors.HexColor("#1F3A5F")
BLUE = colors.HexColor("#2F6DB5")
LIGHT = colors.HexColor("#EAF1FA")
GREY = colors.HexColor("#F3F4F6")
MID = colors.HexColor("#9CA3AF")
TEXT = colors.HexColor("#1F2937")
GREEN = colors.HexColor("#E7F5EC")
AMBER = colors.HexColor("#FDF3E1")
RED = colors.HexColor("#FBE9E9")

# ── Styles ───────────────────────────────────────────────────────────────
S = {
    "body": ParagraphStyle("body", fontName=BODY, fontSize=9.5, leading=13.5,
                           textColor=TEXT, spaceAfter=5),
    "H1": ParagraphStyle("H1", keepWithNext=1, fontName=BOLD, fontSize=17, leading=21,
                         textColor=NAVY, spaceBefore=4, spaceAfter=10),
    "H2": ParagraphStyle("H2", keepWithNext=1, fontName=BOLD, fontSize=12.5, leading=16,
                         textColor=BLUE, spaceBefore=10, spaceAfter=5),
    "H3": ParagraphStyle("H3", keepWithNext=1, fontName=BOLD, fontSize=10.5, leading=14,
                         textColor=NAVY, spaceBefore=6, spaceAfter=3),
    "bullet": ParagraphStyle("bullet", fontName=BODY, fontSize=9.5, leading=13.5,
                             textColor=TEXT, leftIndent=14, bulletIndent=4, spaceAfter=2),
    "cell": ParagraphStyle("cell", fontName=BODY, fontSize=8.3, leading=10.8, textColor=TEXT),
    "cellb": ParagraphStyle("cellb", fontName=BOLD, fontSize=8.3, leading=10.8,
                            textColor=colors.white),
    "code": ParagraphStyle("code", fontName=MONO, fontSize=7.8, leading=9.8,
                           textColor=TEXT),
    "caption": ParagraphStyle("caption", fontName=BODY, fontSize=8, leading=10,
                              textColor=MID, alignment=TA_CENTER, spaceBefore=3, spaceAfter=8),
    "note": ParagraphStyle("note", fontName=BODY, fontSize=9, leading=12.5, textColor=TEXT),
}

W = A4[0] - 4 * cm  # usable width


# ── Flowable helpers ─────────────────────────────────────────────────────
def c(s: str) -> str:
    """Inline code."""
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f'<font name="{MONO}" size="8.6" color="#0B4F8A">{s}</font>'


def P(t):
    return Paragraph(t, S["body"])


def H1(t):
    return Paragraph(t, S["H1"])


def H2(t):
    return Paragraph(t, S["H2"])


def H3(t):
    return Paragraph(t, S["H3"])


def bullets(items):
    return [Paragraph(i, S["bullet"], bulletText="•") for i in items]


def numbered(items):
    return [Paragraph(i, S["bullet"], bulletText=f"{n}.") for n, i in enumerate(items, 1)]


def code(text):
    pre = Preformatted(text.strip("\n"), S["code"])
    t = Table([[pre]], colWidths=[W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), GREY),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
        ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return KeepTogether([t, Spacer(1, 6)])


def table(rows, widths, header=True, zebra=True):
    data = []
    for r_i, row in enumerate(rows):
        style = S["cellb"] if (header and r_i == 0) else S["cell"]
        data.append([Paragraph(str(x), style) for x in row])
    total = sum(widths)
    t = Table(data, colWidths=[W * w / total for w in widths], repeatRows=1 if header else 0)
    st = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D1D5DB")),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    if header:
        st.append(("BACKGROUND", (0, 0), (-1, 0), NAVY))
    if zebra:
        for i in range(1 if header else 0, len(rows)):
            if i % 2 == 0:
                st.append(("BACKGROUND", (0, i), (-1, i), GREY))
    t.setStyle(TableStyle(st))
    return [t, Spacer(1, 8)]


def callout(text, kind="info"):
    bg = {"info": LIGHT, "ok": GREEN, "warn": AMBER, "risk": RED}[kind]
    edge = {"info": BLUE, "ok": colors.HexColor("#2E8B57"),
            "warn": colors.HexColor("#C98A1B"), "risk": colors.HexColor("#B83232")}[kind]
    t = Table([[Paragraph(text, S["note"])]], colWidths=[W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LINEBEFORE", (0, 0), (0, -1), 3, edge),
        ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return [t, Spacer(1, 8)]


def brk(story):
    """Section break: drop trailing spacers so they cannot spill onto a blank page."""
    while story and isinstance(story[-1], Spacer):
        story.pop()
    story.append(PageBreakIfNotEmpty())


def caption(t):
    return Paragraph(t, S["caption"])


# ── Diagram helpers ──────────────────────────────────────────────────────
def box(d, x, y, w, h, label, fill=LIGHT, stroke=BLUE, size=8, bold=False, sub=None):
    d.add(Rect(x, y, w, h, rx=4, ry=4, fillColor=fill, strokeColor=stroke, strokeWidth=0.8))
    if sub:
        d.add(String(x + w / 2, y + h / 2 + 1.5, label, fontName=BOLD if bold else BODY,
                     fontSize=size, textAnchor="middle", fillColor=TEXT))
        d.add(String(x + w / 2, y + h / 2 - size + 0.5, sub, fontName=BODY,
                     fontSize=size - 1.5, textAnchor="middle", fillColor=colors.HexColor("#4B5563")))
    else:
        d.add(String(x + w / 2, y + h / 2 - size / 3, label, fontName=BOLD if bold else BODY,
                     fontSize=size, textAnchor="middle", fillColor=TEXT))


def arrow(d, x1, y1, x2, y2, color=NAVY, label=None, lx=0, ly=0):
    d.add(Line(x1, y1, x2, y2, strokeColor=color, strokeWidth=0.9))
    import math
    ang = math.atan2(y2 - y1, x2 - x1)
    s = 5
    p1 = (x2 - s * math.cos(ang - 0.4), y2 - s * math.sin(ang - 0.4))
    p2 = (x2 - s * math.cos(ang + 0.4), y2 - s * math.sin(ang + 0.4))
    d.add(Polygon([x2, y2, p1[0], p1[1], p2[0], p2[1]], fillColor=color, strokeColor=color))
    if label:
        d.add(String((x1 + x2) / 2 + lx, (y1 + y2) / 2 + ly, label, fontName=BODY,
                     fontSize=6.8, textAnchor="middle", fillColor=colors.HexColor("#4B5563")))


def layer_diagram():
    d = Drawing(W, 300)
    layers = [
        ("Entry point", "main.py  —  CLI, task id, SIGTERM handler", colors.HexColor("#DCE7F5")),
        ("Orchestration", "orchestrator/  —  LangGraph graph, state, routing, context", colors.HexColor("#E3ECF8")),
        ("Node wrapper", "orchestrator/nodes.py  —  one function per step, error guards", colors.HexColor("#EAF1FA")),
        ("Agents", "agents/  +  skills/*.md  —  prompt building, output contracts", colors.HexColor("#EEF5FB")),
        ("LLM client", "core/llm.py  —  rate limit, retry, structured-output parsing", colors.HexColor("#F1F7FC")),
        ("Backends", "core/backends.py  —  Ollama  |  vLLM", colors.HexColor("#F5F9FD")),
    ]
    y = 262
    for name, desc, fill in layers:
        box(d, 0, y, 0.70 * W, 32, name, fill=fill, bold=True, size=8.5, sub=desc)
        y -= 42
    # side services
    sx = 0.74 * W
    sw = 0.26 * W
    box(d, sx, 220, sw, 74, "Contracts", fill=GREEN, stroke=colors.HexColor("#2E8B57"),
        bold=True, sub="core/schemas.py")
    box(d, sx, 136, sw, 74, "Tools (MCP)", fill=AMBER, stroke=colors.HexColor("#C98A1B"),
        bold=True, sub="mcp_servers/")
    box(d, sx, 52, sw, 74, "Knowledge base", fill=AMBER, stroke=colors.HexColor("#C98A1B"),
        bold=True, sub="rag/  →  ChromaDB")
    box(d, 0, 2, W, 30, "Audit & observability", fill=RED, stroke=colors.HexColor("#B83232"),
        bold=True, sub="core/logger.py → audit/events.jsonl   ·   structlog console   ·   LangSmith (optional)")
    for yy in (262, 220, 178, 136, 94):
        arrow(d, 0.35 * W, yy, 0.35 * W, yy - 10 + 0.0)
    return d


def pipeline_diagram():
    d = Drawing(W, 470)
    bw, bh = 170, 26
    cx = 150
    x = cx - bw / 2
    steps = [
        ("User request + scenario id", GREY, None),
        ("1  Evidence Agent", LIGHT, "RAG + scenario metadata → EvidenceReport"),
        ("2  Technical Agent", LIGHT, "AgentOpinion"),
        ("3  Quality Agent", LIGHT, "AgentOpinion"),
        ("4  Compliance Agent", LIGHT, "AgentOpinion"),
        ("5  Critic Agent", LIGHT, "ComparativeReview"),
        ("6  Synthesis Agent", LIGHT, "FinalSynthesis"),
        ("7  Validator Agent", LIGHT, "ValidationReport"),
        ("Prepare human review", GREY, "Markdown report + proposed actions"),
        ("Human approval", AMBER, "approve / reject (CLI)"),
    ]
    y = 440
    ys = []
    for label, fill, note in steps:
        box(d, x, y, bw, bh, label, fill=fill, bold=True, size=8)
        if note:
            d.add(String(x + bw + 10, y + bh / 2 - 3, note, fontName=BODY, fontSize=7.2,
                         fillColor=colors.HexColor("#4B5563")))
        ys.append(y)
        y -= 42
    for i in range(len(ys) - 1):
        arrow(d, cx, ys[i], cx, ys[i + 1] + bh)
    # specialists bracket
    d.add(Line(x - 14, ys[2] + bh, x - 14, ys[4], strokeColor=MID, strokeWidth=0.7))
    d.add(String(x - 18, (ys[2] + ys[4] + bh) / 2, "sequential (Ollama)", fontName=BODY,
                 fontSize=6.5, textAnchor="end", fillColor=MID))
    d.add(String(x - 18, (ys[2] + ys[4] + bh) / 2 - 9, "parallel (vLLM)", fontName=BODY,
                 fontSize=6.5, textAnchor="end", fillColor=MID))
    # retry loop validator -> synthesis (left side; right side holds the notes)
    red = colors.HexColor("#B83232")
    lx0 = x - 30
    d.add(Line(x, ys[7] + bh / 2, lx0, ys[7] + bh / 2, strokeColor=red))
    d.add(Line(lx0, ys[7] + bh / 2, lx0, ys[6] + bh / 2, strokeColor=red))
    arrow(d, lx0, ys[6] + bh / 2, x, ys[6] + bh / 2, color=red)
    d.add(String(lx0 - 4, (ys[6] + ys[7]) / 2 + bh / 2 + 4, "failed and retry_count ≤ 2",
                 fontName=BODY, fontSize=6.8, textAnchor="end", fillColor=red))
    d.add(String(lx0 - 4, (ys[6] + ys[7]) / 2 + bh / 2 - 5, "→ re-run synthesis",
                 fontName=BODY, fontSize=6.8, textAnchor="end", fillColor=red))
    # terminal branches
    yb = ys[-1] - 46
    box(d, cx - bw / 2 - 60, yb, 120, bh, "Automation", fill=GREEN,
        stroke=colors.HexColor("#2E8B57"), bold=True, size=8)
    box(d, cx + bw / 2 - 60, yb, 120, bh, "Handle rejection", fill=RED,
        stroke=colors.HexColor("#B83232"), bold=True, size=8)
    arrow(d, cx - 20, ys[-1], cx - bw / 2, yb + bh, label="approve", lx=-14, ly=2)
    arrow(d, cx + 20, ys[-1], cx + bw / 2, yb + bh, label="anything else", lx=22, ly=2)
    d.add(String(cx - bw / 2 - 60 + 60, yb - 10, "report .md + ticket .json", fontName=BODY,
                 fontSize=6.8, textAnchor="middle", fillColor=colors.HexColor("#4B5563")))
    return d


def structured_output_diagram():
    d = Drawing(W, 150)
    labels = [
        ("Pydantic schema", "→ example instance"),
        ("System prompt", "skill + format rule"),
        ("generate()", "semaphore + retry"),
        ("Extract JSON", "balanced {…} blocks"),
        ("Validate", "latest block first"),
    ]
    bw, bh, gap = 82, 40, (W - 5 * 82) / 4
    y = 95
    for i, (a, b) in enumerate(labels):
        x = i * (bw + gap)
        box(d, x, y, bw, bh, a, bold=True, size=7.6, sub=b)
        if i:
            arrow(d, x - gap, y + bh / 2, x, y + bh / 2)
    box(d, W - bw, 18, bw, 34, "Typed object", fill=GREEN, stroke=colors.HexColor("#2E8B57"),
        bold=True, size=7.6, sub="returned to agent")
    arrow(d, W - bw / 2, y, W - bw / 2, 52, label="valid", lx=12)
    box(d, W - 2 * bw - gap, 18, bw, 34, "Retry (≤3)", fill=AMBER,
        stroke=colors.HexColor("#C98A1B"), bold=True, size=7.6, sub="then LLMParseError")
    arrow(d, W - bw / 2 - 18, y, W - bw - gap - bw / 2, 52, label="invalid", lx=-14, ly=4)
    d.add(Line(W - 2 * bw - gap, 35, 2 * (bw + gap) + bw / 2, 35, strokeColor=colors.HexColor("#C98A1B")))
    arrow(d, 2 * (bw + gap) + bw / 2, 35, 2 * (bw + gap) + bw / 2, y,
          color=colors.HexColor("#C98A1B"))
    return d


def rag_diagram():
    d = Drawing(W, 150)
    bw, bh = 86, 40
    gap = (W - 5 * bw) / 4
    row = [
        ("data/<category>/", ".md .json .pdf …"),
        ("Loader", "markitdown for PDF/Office"),
        ("Chunker", "3000 chars, 300 overlap"),
        ("Embedder", "nomic-embed-text"),
        ("ChromaDB", "id = source#chunk"),
    ]
    y = 95
    for i, (a, b) in enumerate(row):
        x = i * (bw + gap)
        box(d, x, y, bw, bh, a, bold=True, size=7.6, sub=b,
            fill=AMBER if i in (0, 4) else LIGHT,
            stroke=colors.HexColor("#C98A1B") if i in (0, 4) else BLUE)
        if i:
            arrow(d, x - gap, y + bh / 2, x, y + bh / 2)
    d.add(String(0, y + bh + 8, "INGESTION  (python main.py --ingest, or automatically when empty)",
                 fontName=BOLD, fontSize=7.5, fillColor=NAVY))
    y2 = 5
    row2 = [
        ("Request + scenario", "user input"),
        ("Query builder", "≈8 derived queries"),
        ("Vector search", "2 × top_k per query"),
        ("Selector", "dedupe · rank · cap · budget"),
        ("Evidence prompt", "≤ 9 000 chars"),
    ]
    for i, (a, b) in enumerate(row2):
        x = i * (bw + gap)
        box(d, x, y2, bw, bh, a, bold=True, size=7.6, sub=b,
            fill=GREEN if i == 4 else LIGHT,
            stroke=colors.HexColor("#2E8B57") if i == 4 else BLUE)
        if i:
            arrow(d, x - gap, y2 + bh / 2, x, y2 + bh / 2)
    d.add(String(0, y2 + bh + 8, "RETRIEVAL  (Evidence Agent, every investigation)",
                 fontName=BOLD, fontSize=7.5, fillColor=NAVY))
    arrow(d, 4 * (bw + gap) + bw / 2, y, 2 * (bw + gap) + bw / 2 + 20, y2 + bh,
          color=MID, label="query", lx=-26, ly=-6)
    return d


# ── Document template with TOC + header/footer ───────────────────────────
class ManualDoc(BaseDocTemplate):
    def __init__(self, filename, **kw):
        super().__init__(filename, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                         topMargin=2.2 * cm, bottomMargin=2 * cm,
                         title="AFAMA Harness Technical Manual",
                         author="Syed Waqar Ul Haq",
                         subject="Architecture, operation and development of the AFAMA multi-agent harness")
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="f")
        self.addPageTemplates([
            PageTemplate(id="cover", frames=[frame], onPage=self._cover),
            PageTemplate(id="body", frames=[frame], onPage=self._decor),
        ])
        self._h = 0

    def beforeDocument(self):
        self._h = 0  # multiBuild runs several passes; keys must repeat identically

    def afterFlowable(self, f):
        if isinstance(f, Paragraph) and f.style.name in ("H1", "H2"):
            text = f.getPlainText()
            level = 0 if f.style.name == "H1" else 1
            key = f"h{self._h}"
            self._h += 1
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(text, key, level=level, closed=level > 0)
            self.notify("TOCEntry", (level, text, self.page, key))

    @staticmethod
    def _cover(canv, doc):
        canv.saveState()
        canv.setFillColor(NAVY)
        canv.rect(0, A4[1] - 9.5 * cm, A4[0], 9.5 * cm, fill=1, stroke=0)
        canv.setFillColor(BLUE)
        canv.rect(0, A4[1] - 9.8 * cm, A4[0], 0.3 * cm, fill=1, stroke=0)
        canv.restoreState()

    @staticmethod
    def _decor(canv, doc):
        canv.saveState()
        canv.setStrokeColor(colors.HexColor("#D1D5DB"))
        canv.setLineWidth(0.5)
        canv.line(2 * cm, A4[1] - 1.6 * cm, A4[0] - 2 * cm, A4[1] - 1.6 * cm)
        canv.line(2 * cm, 1.4 * cm, A4[0] - 2 * cm, 1.4 * cm)
        canv.setFont(BODY, 7.5)
        canv.setFillColor(MID)
        canv.drawString(2 * cm, A4[1] - 1.4 * cm, "AFAMA — Harness Technical Manual")
        canv.drawRightString(A4[0] - 2 * cm, A4[1] - 1.4 * cm, "Version 1.0 · November 2026")
        canv.drawString(2 * cm, 1.0 * cm, "github.com/Wiki1998-dev/Autoagent")
        canv.drawRightString(A4[0] - 2 * cm, 1.0 * cm, f"Page {doc.page}")
        canv.restoreState()


# ── Content ──────────────────────────────────────────────────────────────
def build():
    story = []

    # ---------- Cover ----------
    title = ParagraphStyle("t", fontName=BOLD, fontSize=30, leading=36, textColor=colors.white)
    subt = ParagraphStyle("st", fontName=BODY, fontSize=13.5, leading=18,
                          textColor=colors.HexColor("#DCE7F5"))
    story += [
        Spacer(1, 1.4 * cm),
        Paragraph("AFAMA", title),
        Spacer(1, 4),
        Paragraph("Automotive Failure Analysis Multi-Agent System", subt),
        Spacer(1, 14),
        Paragraph("Harness Technical Manual", ParagraphStyle(
            "t2", fontName=BOLD, fontSize=18, leading=22, textColor=colors.white)),
        Paragraph("Architecture · Operation · Development", subt),
        Spacer(1, 4.3 * cm),
    ]
    story += table([
        ["Document", "Details"],
        ["Version", "1.0"],
        ["Date", "24 November 2026"],
        ["Author / maintainer", "Syed Waqar Ul Haq"],
        ["Repository", "github.com/Wiki1998-dev/Autoagent (branch main)"],
        ["Code baseline", f"Commit {c('3c139e3')} plus the evidence-retrieval update in "
                          f"{c('agents/evidence_agent.py')} and {c('config.py')} described in §14"],
        ["Audience", "Developers, ML/AI engineers and operators who run, maintain or extend AFAMA"],
        ["Status", "Released"],
    ], [1, 3])
    story += [NextPageTemplate("body"), PageBreak()]

    # ---------- TOC ----------
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle("toc0", fontName=BOLD, fontSize=10, leading=15, leftIndent=0,
                       textColor=NAVY),
        ParagraphStyle("toc1", fontName=BODY, fontSize=9, leading=12.5, leftIndent=16,
                       textColor=TEXT),
    ]
    story += [Paragraph("Contents", S["H1"].clone("toch", spaceAfter=12)), toc, PageBreak()]

    # ---------- 1 Introduction ----------
    story += [H1("1  Introduction"), H2("1.1  Purpose")]
    story.append(P(
        "AFAMA investigates automotive failure scenarios with a team of eight specialised AI agents "
        "that run entirely on local hardware. This manual documents the <b>harness</b>: the software "
        "that surrounds the language model and turns a single text-in/text-out function into a "
        "reliable, auditable, multi-step investigation. The harness decides which agent runs when, "
        "what each agent sees, what shape its answer must take, what happens when it fails, which "
        "tools and documents it can use, and what is recorded for later review."))
    story.append(P(
        "The language model is interchangeable (Llama 3.1, Llama 3.2, any vLLM-served model). "
        "Everything described here is the part that stays the same."))
    story += [H2("1.2  Scope")]
    story += bullets([
        "Architecture and data flow of the investigation pipeline.",
        "Each harness layer: orchestration, node wrapper, agents, LLM client, data contracts, tools, "
        "knowledge base, human approval, automation and audit.",
        "Configuration, installation and operation (Windows reference set-up).",
        "Development guide: how to tune, extend and verify the harness.",
        "Development history, known limitations and troubleshooting.",
    ])
    story.append(P("Out of scope: the engineering validity of conclusions produced by the agents. "
                   "Reports are decision support and always pass through human approval."))
    story += [H2("1.3  Terminology")]
    story += table([
        ["Term", "Meaning in this manual"],
        ["Harness", "All code around the LLM: orchestration, prompts, contracts, tools, retrieval, logging."],
        ["Agent", "A Python class that builds a prompt, calls the LLM and returns a validated object."],
        ["Skill", "A Markdown file in " + c("skills/") + " used verbatim as an agent's system prompt."],
        ["Node", "A function in the LangGraph graph that runs one agent (or one non-LLM step)."],
        ["State", c("InvestigationState") + ": the shared dictionary that flows between nodes."],
        ["Contract", "A Pydantic model in " + c("core/schemas.py") + " that an agent's output must satisfy."],
        ["Backend", "The LLM server adapter: Ollama (local) or vLLM (OpenAI-compatible)."],
        ["RAG", "Retrieval-augmented generation: searching the local knowledge base for evidence."],
        ["Chunk", "A ≤3 000-character slice of a document, embedded and stored separately."],
        ["MCP", "Model Context Protocol. Tool servers built with FastMCP in " + c("mcp_servers/") + "."],
        ["HITL", "Human in the loop: the approval step before any file is written."],
    ], [1, 4])
    story += [H2("1.4  Design principles")]
    story += table([
        ["Principle", "How the harness implements it"],
        ["Local and private", "Ollama or self-hosted vLLM; embeddings and vector store on disk. No cloud API is required."],
        ["Prompts are data", "Agent behaviour lives in Markdown skill files; changing it needs no Python change."],
        ["Typed hand-offs", "Every agent output is a Pydantic model; malformed output is rejected at the boundary."],
        ["Degrade visibly", "A failing agent writes a clearly marked placeholder; the run continues to human review."],
        ["Everything is traceable", "Each step appends structured events to " + c("audit/events.jsonl") + "."],
        ["Human decides", "Nothing is saved or ticketed until a person approves."],
        ["Pluggable backend", "One environment variable switches between Ollama and vLLM."],
    ], [1.2, 4])
    brk(story)

    # ---------- 2 Architecture ----------
    story += [H1("2  System Architecture"), H2("2.1  Layered view")]
    story.append(P("The harness is organised in layers. Each layer only talks to the one below it, "
                   "plus the shared services on the right (contracts, tools, knowledge base) and the "
                   "audit log at the bottom."))
    story += [layer_diagram(), caption("Figure 1 — Harness layers and shared services")]
    story += table([
        ["Layer", "Location", "Responsibility"],
        ["Entry point", c("main.py"), "Parse CLI arguments, create task id, install SIGTERM handler, build dependencies, start the graph, log the outcome."],
        ["Orchestration", c("orchestrator/graph.py, state.py, routing.py, context.py"), "Workflow definition, shared state, conditional routing, dependency injection."],
        ["Node wrapper", c("orchestrator/nodes.py"), "Run one agent per node, convert its output to state updates, catch agent failures."],
        ["Agents", c("agents/*.py, skills/*.md"), "Build prompts from state, call the LLM, return typed results."],
        ["LLM client", c("core/llm.py"), "Concurrency limit, transport retries, structured-output generation and parsing."],
        ["Backends", c("core/backends.py"), "Translate a chat request to Ollama or vLLM."],
        ["Contracts", c("core/schemas.py"), "Pydantic models for every hand-off."],
        ["Tools", c("mcp_servers/"), "Knowledge search, scenario lookup, report and ticket persistence."],
        ["Knowledge base", c("rag/"), "Ingestion, chunking, embedding, ChromaDB storage and search."],
        ["Audit", c("core/logger.py"), "Thread-safe, rotating JSONL event log."],
    ], [1, 1.6, 3])

    brk(story)
    story += [H2("2.2  Investigation pipeline")]
    story.append(P("A run takes a free-text request (by default the SC-042 demonstration) and moves it "
                   "through eight agents. Figure 2 shows the control flow, including the bounded "
                   "synthesis-retry loop and the approval branch."))
    story += [pipeline_diagram(), caption("Figure 2 — Control flow of one investigation")]
    story += table([
        ["#", "Stage", "What happens"],
        ["1", "Evidence", "Loads scenario metadata (if the request names an " + c("SC-nnn") + " id), runs ≈8 knowledge-base queries, and asks the LLM to organise the hits into an " + c("EvidenceReport") + "."],
        ["2–4", "Specialists", "Technical, Quality and Compliance agents each read the evidence and produce an " + c("AgentOpinion") + " from their own perspective."],
        ["5", "Critic", "Compares the three opinions: agreements, disagreements, weak and unsupported claims."],
        ["6", "Synthesis", "Merges everything into one " + c("FinalSynthesis") + ", accepting only supported findings."],
        ["7", "Validator", "Checks the synthesis against the evidence; a failed check re-runs synthesis (max. 2 retries)."],
        ["–", "Review & approval", "Formats a Markdown report, proposes actions, waits for the operator's decision."],
        ["8", "Automation", "On approval, saves the report and creates a follow-up ticket."],
    ], [0.4, 1, 4.2])

    story += [H2("2.3  Repository layout")]
    story.append(code("""
Autoagent/
├── main.py                  CLI entry point
├── config.py                all settings (environment-driven)
├── agents/                  8 agent classes (+ base_specialist.py)
├── skills/                  8 agent system prompts (Markdown)
├── core/                    llm.py, backends.py, schemas.py, logger.py, skill_loader.py
├── orchestrator/            graph.py, nodes.py, routing.py, state.py, context.py
├── mcp_servers/             knowledge_server.py, analysis_server.py, automation_server.py
├── rag/                     setup.py, adapter.py, ingestion/, embeddings/, vectorstores/, retrieval/
│   └── vectorstores/chroma_db/   persisted vector store (committed)
├── data/                    knowledge base sources (incidents, requirements, Standards, …)
├── workspace/reports|tickets/    automation outputs
├── audit/events.jsonl       append-only audit log
└── docs/                    this manual and its generator
"""))
    story += [H2("2.4  Start-up sequence")]
    story.append(P("What " + c("python main.py") + " does, in order:"))
    story += numbered([
        "Parse " + c("--ingest") + ", " + c("--query") + ", " + c("--model") + ", " + c("--task-id") + "; generate " + c("INV-YYYYMMDD-HHMMSS") + " if no id is given.",
        "Install a SIGTERM handler that logs " + c("investigation_aborted") + " and exits with code 130.",
        "Build the knowledge adapter; ingest " + c("data/") + " if the collection is empty or " + c("--ingest") + " was passed.",
        "Create the " + c("LLM") + " client for the configured backend and model.",
        "Wrap LLM and adapter in a frozen " + c("PipelineContext") + ".",
        "Compile the LangGraph graph (sequential or parallel specialists, from config).",
        "Invoke the graph with " + c("{task_id, user_request, retry_count: 0}") + " and the context in " + c("config['configurable']['pipeline_ctx']") + ".",
        "Log the decision and automation results; append " + c("investigation_complete") + " to the audit log.",
    ])
    brk(story)

    # ---------- 3 Orchestration ----------
    story += [H1("3  Orchestration Layer"), H2("3.1  Graph construction")]
    story.append(P(c("build_graph()") + " in " + c("orchestrator/graph.py") + " registers eleven nodes and "
                   "wires them with plain and conditional edges, then compiles the graph. The only "
                   "structural option is " + c("PARALLEL_SPECIALISTS") + ":"))
    story += bullets([
        "<b>False</b> (default for Ollama): evidence → technical → quality → compliance → critic. "
        "Ollama serves one request at a time; concurrent calls can drop connections.",
        "<b>True</b> (default for vLLM): the three specialists fan out from evidence and join at the critic. "
        "Safe because each specialist writes a different state key, so LangGraph merges the branches without conflict.",
    ])
    story += [H2("3.2  Shared state")]
    story.append(P(c("InvestigationState") + " is a " + c("TypedDict(total=False)") + ". Nodes never call "
                   "each other; they communicate only by reading and writing these keys. Values are "
                   "stored as plain dicts (" + c("model_dump()") + ") so the state is serialisable."))
    story += table([
        ["Key", "Type", "Written by", "Read by"],
        [c("task_id"), "str", "main.py", "all nodes"],
        [c("user_request"), "str", "main.py", "gather_evidence"],
        [c("evidence_report"), "dict", "gather_evidence", "specialists, synthesis, validation"],
        [c("technical_opinion"), "dict", "run_technical", "critic, synthesis"],
        [c("quality_opinion"), "dict", "run_quality", "critic, synthesis"],
        [c("compliance_opinion"), "dict", "run_compliance", "critic, synthesis"],
        [c("comparative_review"), "dict", "run_critic", "synthesis, validation"],
        [c("final_synthesis"), "dict", "run_synthesis", "validation, review, automation"],
        [c("validation_report"), "dict", "run_validation", "routing, review"],
        [c("retry_count"), "int", "main.py (0), run_synthesis (+1)", "route_after_validation"],
        [c("report_markdown"), "str", "prepare_human_review", "human_approval, automation"],
        [c("proposed_actions"), "list[dict]", "prepare_human_review", "human_approval"],
        [c("human_decision"), "str", "human_approval", "route_after_human"],
        [c("human_feedback"), "str", "human_approval", "automation, rejection"],
        [c("automation_results"), "list[dict]", "run_automation", "main.py"],
    ], [1.4, 0.7, 1.5, 1.7])
    story += [H2("3.3  Routing rules")]
    story.append(H3("route_after_validation"))
    story += bullets([
        "Validation passed → " + c("prepare_human_review") + ".",
        "Otherwise, if " + c("retry_count > 2") + " → " + c("prepare_human_review") + " with a " + c("max_retries_exceeded") + " warning.",
        "Otherwise → " + c("run_synthesis") + " again.",
    ])
    story.append(P("Because " + c("run_synthesis") + " increments " + c("retry_count") + " before the check, "
                   "synthesis runs at most <b>three</b> times (one initial pass plus two retries). A "
                   "validator that crashes is treated as a failed validation, so the retry path also "
                   "covers transient validator errors."))
    story.append(H3("route_after_human"))
    story.append(P("Only the exact (lower-cased, trimmed) answer " + c("approve") + " leads to automation. "
                   "Every other input, including typos and empty input, is treated as a rejection."))
    story += [H2("3.4  Dependency injection")]
    story.append(P("The LLM client and knowledge adapter are passed per invocation through LangGraph's "
                   "config, not held in module globals. Each node calls " + c("_ctx(config)") + ", which "
                   "raises a clear " + c("RuntimeError") + " if the context is missing. "
                   + c("PipelineContext") + " is a frozen dataclass, so nodes cannot swap dependencies "
                   "mid-run, and several investigations can run in one process without sharing state."))
    story += [H2("3.5  Node contract and failure semantics")]
    story.append(P("Every LLM-backed node follows the same pattern:"))
    story.append(code("""
def run_x(state: InvestigationState, config: RunnableConfig) -> dict:
    logger.info("node_start", node="run_x", task_id=state["task_id"])
    try:
        result = XAgent(llm=_ctx(config).llm).run(...)        # typed Pydantic object
        logger.info("node_complete", ...)
        return {"x_output": result.model_dump()}             # state update
    except (LLMParseError, ConnectionError) as e:
        logger.error("node_agent_error", ...)
        log_event("node_error", "run_x", task_id, data={"error": str(e)}, status="error")
        return {"x_output": {...placeholder with the error text...}}
"""))
    story.append(P("Placeholders are shaped like the real contract, so downstream agents keep working "
                   "and the failure is visible in the final report rather than hidden:"))
    story += table([
        ["Node", "Placeholder on failure"],
        ["gather_evidence", "Empty incident/requirement lists; summary and evidence gap state that collection failed."],
        ["run_technical / quality / compliance", "Confidence 0.0, no findings, open question " + c("Agent failed: …") + "."],
        ["run_critic", "All review lists empty."],
        ["run_synthesis", "Summary " + c("Synthesis failed: …") + "; unresolved point requests manual review. Still increments " + c("retry_count") + "."],
        ["run_validation", c("passed = False") + " with zero counts, which triggers the retry path."],
    ], [1.6, 4])
    story += callout("<b>Scope of the guard.</b> Only " + c("LLMParseError") + " and " + c("ConnectionError")
                     + " are caught. Any other exception (for example a bug in an agent) propagates, is "
                     "logged as " + c("investigation_error") + " by " + c("main.py") + ", and stops the run. "
                     "That is intentional: programming errors should not be disguised as model failures.", "warn")
    brk(story)

    # ---------- 4 Agents ----------
    story += [H1("4  Agent Layer"), H2("4.1  Anatomy of an agent")]
    story += numbered([
        "Load its skill: " + c("load_skill(\"<name>\")") + " reads " + c("skills/<name>.md") + " (missing file → " + c("FileNotFoundError") + " at construction).",
        "Log " + c("agent_start") + ".",
        "Build a user prompt from its inputs (JSON-serialised state values).",
        "Call " + c("llm.generate_structured(prompt, schema=…, system=skill)") + ".",
        "Log " + c("agent_complete") + " with a few summary numbers and return the typed object.",
    ])
    story += [H2("4.2  Agent roster")]
    story += table([
        ["Agent", "Class / skill", "Inputs", "Output", "LLM"],
        ["Evidence", c("EvidenceAgent") + "<br/>" + c("evidence_agent.md"), "request, scenario metadata, RAG hits", c("EvidenceReport"), "yes"],
        ["Technical", c("TechnicalAgent") + "<br/>" + c("technical_agent.md"), "evidence_report", c("AgentOpinion"), "yes"],
        ["Quality", c("QualityAgent") + "<br/>" + c("quality_agent.md"), "evidence_report", c("AgentOpinion"), "yes"],
        ["Compliance", c("ComplianceAgent") + "<br/>" + c("compliance_agent.md"), "evidence_report", c("AgentOpinion"), "yes"],
        ["Critic", c("CriticAgent") + "<br/>" + c("critic_agent.md"), "three opinions", c("ComparativeReview"), "yes"],
        ["Synthesis", c("SynthesisAgent") + "<br/>" + c("synthesis_agent.md"), "evidence, three opinions, review", c("FinalSynthesis"), "yes"],
        ["Validator", c("ValidatorAgent") + "<br/>" + c("validator_agent.md"), "evidence, synthesis, review", c("ValidationReport"), "yes"],
        ["Automation", c("AutomationAgent") + "<br/>" + c("automation_agent.md"), "synthesis, report, feedback", c("list[AutomationResult]"), "no"],
    ], [0.9, 1.7, 1.6, 1.3, 0.4])
    story.append(P("The Automation Agent is deterministic: it calls the automation tools directly and "
                   "never asks the LLM, so no model output can trigger file writes on its own."))
    story += [H2("4.3  Specialist base class")]
    story.append(P("The three specialists inherit " + c("BaseSpecialistAgent") + " and override only two "
                   "class attributes. Their different behaviour comes entirely from their skill files:"))
    story.append(code("""
class QualityAgent(BaseSpecialistAgent):
    agent_name = "quality_agent"
    skill_name = "quality_agent"      # → skills/quality_agent.md
"""))
    story.append(P("The base class also forces " + c("opinion.agent_name") + " to the correct value, so a "
                   "model that mislabels itself cannot confuse the critic."))
    story += [H2("4.4  Skill files")]
    story.append(P("Each skill is a Markdown document loaded verbatim as the system prompt. The shipped "
                   "skills share this structure:"))
    story += table([
        ["Section", "Purpose"],
        ["# Role", "Who the agent is inside the pipeline."],
        ["# Goal", "The outcome it must deliver."],
        ["# Context", "What it receives and who consumes its output."],
        ["# Domain Knowledge", "Failure mechanisms and standards it should consider (ISO 26262, ISO 21448/SOTIF, UNECE R157/R79)."],
        ["# Rules", "Hard constraints, e.g. separate observations from hypotheses, cite a source for every claim."],
        ["Output guidance / examples", "Field-level hints that match the agent's Pydantic contract."],
    ], [1.3, 4])
    story += callout("Keep skill examples aligned with " + c("core/schemas.py") + ". The LLM client "
                     "already appends a generated JSON example of the contract; a contradicting example "
                     "inside the skill is a common source of parse failures (see commit " + c("b3e64e1") + ").", "info")
    story += [H2("4.5  Evidence retrieval strategy")]
    story.append(P("The Evidence Agent is the only agent that queries the knowledge base. Its retrieval "
                   "is implemented by two functions in " + c("agents/evidence_agent.py") + "."))
    story.append(H3("build_search_queries(user_request, scenario_data)"))
    story.append(P("Queries come from the actual request and scenario, not from a fixed domain list, so "
                   "a brake or steering investigation retrieves brake or steering evidence. For SC-042 it "
                   "produces:"))
    story += table([
        ["Source", "Query"],
        ["Request text (≤500 chars)", "Investigate scenario SC-042, find similar incidents, …"],
        ["System + environment", "camera radar pedestrian detection failure night rain wet"],
        ["Scenario notes", "Possible sensor disagreement under low-light conditions."],
        ["Prediction disagreement", "… sensor disagreement: camera model predicted background; radar model predicted pedestrian"],
        ["Explainability summary", "camera radar pedestrian detection road reflections pedestrian region"],
        ["Requirements", "safety requirement camera radar pedestrian detection night rain wet"],
        ["Test evidence", "test report camera radar pedestrian detection night rain wet"],
        ["Process (always)", "human oversight investigation approval"],
    ], [1.4, 4])
    story.append(H3("select_evidence(results)"))
    story += numbered([
        "Each query fetches " + c("2 × RETRIEVAL_TOP_K") + " hits (default 10), so smaller documents are not crowded out before selection.",
        "De-duplicate by <b>(source, chunk)</b>, keeping the best score, so several sections of one large document can be used.",
        "Rank all hits by similarity.",
        "Take at most " + c("EVIDENCE_MAX_CHUNKS_PER_SOURCE") + " (3) chunks from any one file.",
        "Stop adding text at " + c("EVIDENCE_CHAR_BUDGET") + " (9 000 characters, ≈2 250 tokens), so the prompt fits the model's context window. Ollama silently truncates the beginning of over-long prompts, which would remove the system prompt.",
    ])
    story.append(P("Each block in the prompt is labelled with its source, chunk number and score, e.g. "
                   + c("--- Source: ISO26262.pdf [part 69] (score: 0.64) ---") + "."))
    brk(story)

    # ---------- 5 LLM client ----------
    story += [H1("5  LLM Client"), H2("5.1  Interface")]
    story += table([
        ["Method", "Returns", "Use"],
        [c("generate(prompt, system='', retries=3)"), "str", "Raw text. Handles transport retries and the concurrency limit."],
        [c("generate_structured(prompt, schema, system='', retries=3)"), "Pydantic model", "Typed output for agents. Wraps " + c("generate") + " with format instructions, parsing and validation retries."],
    ], [2.4, 0.9, 2.5])
    story += [H2("5.2  Concurrency control")]
    story.append(P("A process-wide " + c("threading.Semaphore(LLM_MAX_CONCURRENT)") + " gates every model "
                   "call. The default is 1 for Ollama and 4 for vLLM. Even with parallel specialists, no "
                   "more than this many requests reach the server at once."))
    story += [H2("5.3  Transport retries")]
    story.append(P("Any exception from the backend is retried up to three attempts with <i>full-jitter</i> "
                   "exponential backoff: the wait is a random value in [0, 2<super>attempt</super>] seconds, "
                   "so several threads recovering at once do not hit the server simultaneously. After the "
                   "last attempt a " + c("ConnectionError") + " is raised with backend-specific advice "
                   "(check " + c("ollama ps") + ", or the vLLM URL)."))
    story += [H2("5.4  Structured-output pipeline")]
    story += [structured_output_diagram(), caption("Figure 3 — How generate_structured() turns free text into a typed object")]
    story += numbered([
        "<b>Example, not schema.</b> " + c("_build_example()") + " walks the Pydantic JSON Schema (resolving " + c("$ref") + ", " + c("anyOf") + ", enums, nested models) and builds a filled-in example. Small models tend to echo a raw JSON Schema back as their answer; an example is far less likely to be copied.",
        "<b>Format rule.</b> The example and an \"output only this JSON object\" instruction are appended to the agent's skill to form the system prompt.",
        "<b>Extraction.</b> Markdown fences are stripped, then every balanced top-level " + c("{…}") + "/" + c("[…]") + " block is extracted with a string-aware bracket scanner.",
        "<b>Validation.</b> Candidates are tried <i>latest first</i> (the real answer usually follows any preamble or echoed example); the first that validates wins.",
        "<b>Retry.</b> If none validates, the call is repeated (up to 3 times, sleeping 1 s × attempt). All candidate errors are reported, then " + c("LLMParseError") + " is raised.",
    ])
    story += callout("Worst case per agent: 3 parse attempts × 3 transport attempts = 9 model calls. On a "
                     "CPU-only machine one call takes several minutes, so persistent parse failures are "
                     "expensive. Use a model that follows JSON instructions reliably.", "warn")
    story += [H2("5.5  Backends")]
    story += table([
        ["", "OllamaBackend", "VLLMBackend"],
        ["Selected by", c("LLM_BACKEND=ollama") + " (default)", c("LLM_BACKEND=vllm")],
        ["Client", c("ollama.Client(host, timeout)"), c("openai.OpenAI(base_url, api_key, timeout)")],
        ["Model setting", c("LLM_MODEL"), c("VLLM_MODEL")],
        ["Concurrency", "One request at a time (default)", "Continuous batching; true parallel requests"],
        ["Defaults", "sequential specialists, 1 concurrent call", "parallel specialists, 4 concurrent calls"],
        ["Typical host", "Developer workstation, CPU or consumer GPU", "GPU server or Kubernetes"],
    ], [1, 2, 2])
    story.append(P("Both implement " + c("chat(messages, temperature, max_tokens) -> str") + ". A new backend "
                   "only needs that method plus a branch in " + c("build_backend()") + "."))
    story += [H2("5.6  Tracing")]
    story.append(P(c("generate") + " and " + c("generate_structured") + " are decorated with LangSmith's "
                   + c("@traceable") + ". Tracing is off unless " + c("LANGCHAIN_TRACING_V2=true") + " and "
                   + c("LANGCHAIN_API_KEY") + " are set in " + c(".env") + ". Note that enabling it sends "
                   "prompts to LangSmith, which conflicts with the fully local design; use a self-hosted "
                   "LangSmith or leave it disabled for confidential data."))
    brk(story)

    # ---------- 6 Contracts ----------
    story += [H1("6  Data Contracts")]
    story.append(P("All models live in " + c("core/schemas.py") + " and are the single source of truth for "
                   "agent hand-offs. Constraints are enforced by Pydantic v2 at parse time."))
    story += table([
        ["Model", "Fields", "Constraints / notes"],
        [c("SourceReference"), "source, excerpt, relevance", "Used inside EvidenceReport."],
        [c("EvidenceReport"), "task_id, scenario_summary, similar_incidents[], relevant_requirements[], evidence_gaps[]", "Lists of SourceReference."],
        [c("Hypothesis"), "description, confidence, supporting_sources[]", "confidence ∈ [0, 1]."],
        [c("AgentOpinion"), "agent_name, key_findings[], claims[], confidence, evidence_refs[], open_questions[]", "confidence ∈ [0, 1]; agent_name overwritten by base class."],
        [c("Disagreement"), "topic, positions[], resolution_suggestion", "One position per disagreeing agent."],
        [c("ComparativeReview"), "agreements[], disagreements[], weak_claims[], unsupported_claims[], additional_evidence_needed[], synthesis_guidance[]", "disagreements typed as Disagreement."],
        [c("FinalSynthesis"), "final_summary, accepted_findings[], rejected_findings[], unresolved_points[], recommended_next_steps[]", "Drives the report and ticket."],
        [c("ValidationIssue"), "severity, description, recommendation", "severity ∈ {info, warning, critical}."],
        [c("ValidationReport"), "passed, issues[], supported_claims, unsupported_claims", c("passed") + " drives the retry loop."],
        [c("ProposedAction"), "action_type, parameters, risk_level", "action_type ∈ {create_ticket, save_report}; risk ∈ {low, medium, high}."],
        [c("AutomationResult"), "success, action_type, output_reference?, error?", "One per executed action."],
    ], [1.3, 2.6, 2])

    # ---------- 7 Tools ----------
    story += [H1("7  Tool Layer (MCP Servers)")]
    story.append(P("Capabilities that touch data or the file system are exposed as FastMCP tools. In the "
                   "CLI they are called in-process as normal Python functions; the " + c("@mcp.tool()") + " "
                   "boundary lets each server be deployed as its own service later without changing agent code."))
    story += table([
        ["Server", "Tool", "Purpose"],
        [c("knowledge_server"), c("search_internal_docs, find_similar_incidents, search_requirements"), "RAG search over the knowledge base (adapter injected with " + c("set_adapter()") + ")."],
        [c("analysis_server"), c("get_scenario_metadata"), "Load " + c("data/scenarios/<id>.json") + "; used by " + c("gather_evidence") + "."],
        [c("analysis_server"), c("compare_sensor_predictions, get_xai_summary"), "Sensor disagreement and explainability summaries for a scenario."],
        [c("automation_server"), c("save_report"), "Write " + c("workspace/reports/<task_id>.md") + "; an existing file is first backed up with a UTC timestamp suffix."],
        [c("automation_server"), c("create_ticket"), "Write " + c("workspace/tickets/ENG-<UTC timestamp>.json") + "."],
    ], [1.2, 2.2, 2.6])
    story.append(P("Path handling in the analysis and automation servers was hardened against path "
                   "traversal (commit " + c("ec67468") + "), so a crafted scenario or task id cannot write "
                   "outside the workspace."))
    story.append(P("To run a server as an independent process:"))
    story.append(code("""
uvicorn mcp_servers.knowledge_server:mcp  --port 8100
uvicorn mcp_servers.analysis_server:mcp   --port 8101
uvicorn mcp_servers.automation_server:mcp --port 8102
"""))
    story.append(P("Then replace the in-process imports in " + c("orchestrator/nodes.py") + " and "
                   + c("agents/automation_agent.py") + " with FastMCP client calls. The port variables in "
                   + c("config.py") + " are documentation only; nothing reads them yet."))
    brk(story)

    # ---------- 8 RAG ----------
    story += [H1("8  Knowledge Base (RAG)")]
    story += [rag_diagram(), caption("Figure 4 — Ingestion and retrieval paths")]
    story += [H2("8.1  Ingestion")]
    story += bullets([
        "<b>Loader</b> (" + c("rag/ingestion/loader.py") + "): walks each sub-folder of " + c("data/") + "; the folder name becomes the " + c("category") + ". " + c(".md") + " is read as text, " + c(".json") + " is pretty-printed, everything else (PDF, DOCX, XLSX, PPTX) goes through MarkItDown. Unparseable files are skipped with a message.",
        "<b>Chunker</b>: documents longer than 3 000 characters are split into overlapping chunks (300-character overlap), preferring paragraph boundaries. Short documents stay whole.",
        "<b>Embedder</b> (" + c("rag/embeddings/ollama_embedder.py") + "): " + c("ollama.embed(model, input, truncate=True)") + " with " + c("nomic-embed-text") + ". Truncation protects against chunks that exceed the embedding context (dense tables can use many tokens per character).",
        "<b>Store</b> (" + c("rag/vectorstores/chroma_store.py") + "): ChromaDB upsert. Id = " + c("source") + " for whole documents, " + c("source#chunk") + " for chunks; metadata keeps source, category, path and chunk.",
    ])
    story += [H2("8.2  Store safeguards")]
    story += bullets([
        "The embedding model name is stamped into the collection metadata. Opening the store with a different " + c("EMBED_MODEL") + " raises " + c("RuntimeError") + " instead of silently mixing incompatible vectors.",
        "Each query runs in a watchdog thread with a 30-second timeout (" + c("CHROMA_QUERY_TIMEOUT") + ").",
        "Empty results raise " + c("EmptyRAGError") + ", which the adapter converts to an empty list with a warning.",
        "Score = 1 − distance (higher is more similar).",
    ])
    story += [H2("8.3  Current corpus")]
    story += table([
        ["Category", "Files", "Notes"],
        ["incidents", "INC-001, INC-002, INC-003", "Past perception incidents"],
        ["requirements", "REQ-HO-004, REQ-ROB-002", "Human oversight; robustness in adverse visibility"],
        ["test_reports", "TR-017, TR-021", "Validation results"],
        ["model_cards", "camera_vit_v4, fusion_logic", "Camera model and fusion logic descriptions"],
        ["scenarios", "SC-042.json", "Also read directly by the analysis server"],
        ["Standards", "ISO26262.pdf (7.3 MB)", "Converted with MarkItDown; ≈250 chunks"],
    ], [1, 1.8, 2.4])
    story.append(P("Total: 260 entries in the collection. The corpus is focused on camera/radar pedestrian "
                   "detection; investigations of other systems need matching documents in " + c("data/") + "."))
    story += [H2("8.4  When to re-ingest")]
    story.append(P("Run " + c("python main.py --ingest") + " after adding or editing files in " + c("data/")
                   + ", after changing " + c("EMBED_MODEL") + ", or after changing the chunking constants. "
                   "On the reference machine the ISO 26262 conversion alone takes about four minutes."))

    # ---------- 9 HITL / automation ----------
    story += [H1("9  Human Approval and Automation")]
    story += bullets([
        "<b>prepare_human_review</b> renders a Markdown report (summary, accepted/rejected findings, unresolved points, next steps, validation result and issues) and proposes two fixed actions: " + c("save_report") + " (risk low) and " + c("create_ticket") + " (risk medium).",
        "<b>human_approval</b> prints the report and asks " + c("Approve these actions? (approve/reject)") + "; on reject it asks for feedback. The decision is logged as " + c("human_decision") + ".",
        "<b>run_automation</b> (approve) saves the report and creates the ticket; the ticket body is the final summary and its metadata carries next steps and any feedback.",
        "<b>handle_rejection</b> (anything else) logs " + c("investigation_rejected") + " with the feedback and ends the run without writing files.",
    ])
    story.append(P("For unattended tests the decision can be piped in: " + c("echo approve | python main.py") + ". "
                   "Streamlit is listed in the requirements as the intended web front-end for this step "
                   "but is not implemented yet."))
    brk(story)

    # ---------- 10 Audit ----------
    story += [H1("10  Observability and Audit"), H2("10.1  Audit log")]
    story.append(P(c("core/logger.py") + " appends one JSON object per line to " + c("audit/events.jsonl")
                   + " through a " + c("RotatingFileHandler") + " (10 MB per file, 5 backups). Writes and "
                   + c("read_audit_log(task_id)") + " share a lock, so readers never see a half-written line."))
    story.append(code("""
{"timestamp": "2026-11-22T15:51:56.486820+00:00", "event_type": "action_executed",
 "agent": "automation_agent", "task_id": "SETUP-TEST", "status": "ok",
 "data": {"action": "save_report", "path": "...\\\\workspace\\\\reports\\\\SETUP-TEST.md"}}
"""))
    story += table([
        ["event_type", "Emitted by", "Meaning"],
        [c("investigation_start"), "main.py", "Run started; data holds the request."],
        [c("agent_start / agent_complete"), "each agent", "Agent boundaries; complete carries summary counts."],
        [c("node_error"), "nodes.py", "Agent failed; placeholder used. data.error has the message."],
        [c("human_decision"), "human_approval", "Decision and feedback."],
        [c("action_executed"), "automation agent", "Report path or ticket id."],
        [c("investigation_complete"), "main.py", "Run finished; data.decision."],
        [c("investigation_rejected"), "handle_rejection", "Rejected with feedback."],
        [c("investigation_aborted"), "main.py", "Ctrl+C or SIGTERM."],
        [c("investigation_error"), "main.py", "Unhandled exception; run stopped."],
    ], [1.7, 1.2, 2.8])
    story += [H2("10.2  Console log")]
    story.append(P("structlog prints human-readable progress events: " + c("pipeline_init") + ", "
                   + c("llm_ready") + ", " + c("node_start") + ", " + c("node_complete") + " (with counts such "
                   "as findings or confidence), " + c("node_agent_error") + ", " + c("retrying_synthesis") + ", "
                   + c("max_retries_exceeded") + ", " + c("automation_result") + ". These are not persisted; "
                   "redirect output to a file when you need them."))

    # ---------- 11 Configuration ----------
    story += [H1("11  Configuration Reference")]
    story.append(P("All settings are read from environment variables, normally via a " + c(".env") + " file in "
                   "the project root (template: " + c(".env.example") + ")."))
    story += table([
        ["Variable", "Default", "Description"],
        [c("LLM_BACKEND"), "ollama", c("ollama") + " or " + c("vllm") + "."],
        [c("LLM_MODEL"), "llama3.1", "Ollama chat model. Reference PC uses " + c("llama3.2:3b") + "."],
        [c("LLM_TEMPERATURE"), "0.1", "Sampling temperature for all agents."],
        [c("LLM_MAX_TOKENS"), "4096", "Max output tokens per call."],
        [c("LLM_TIMEOUT"), "9999999 → capped 2 000 000 s", "Per-request timeout. Capped because Windows sockets reject larger values."],
        [c("LLM_MAX_CONCURRENT"), "1 (ollama) / 4 (vllm)", "Concurrent LLM calls across threads."],
        [c("PARALLEL_SPECIALISTS"), "false (ollama) / true (vllm)", "Run the three specialists concurrently."],
        [c("OLLAMA_BASE_URL"), "http://localhost:11434", "Ollama server (chat). Embeddings use the ollama library default host."],
        [c("EMBED_MODEL"), "nomic-embed-text", "Embedding model; must match the ingested collection."],
        [c("VLLM_BASE_URL"), "http://localhost:8000/v1", "vLLM OpenAI-compatible endpoint."],
        [c("VLLM_MODEL"), "meta-llama/Llama-3.1-8B-Instruct", "Model id served by vLLM."],
        [c("VLLM_API_KEY"), "(empty)", "Only if the vLLM server requires auth. A warning is printed when unset."],
        [c("CHROMA_COLLECTION"), "autoagent_knowledge", "ChromaDB collection name."],
        [c("RETRIEVAL_TOP_K"), "5", "Base hits per query (evidence agent fetches 2×)."],
        [c("EVIDENCE_MAX_CHUNKS_PER_SOURCE"), "3", "Max chunks from one file in the evidence prompt."],
        [c("EVIDENCE_CHAR_BUDGET"), "9000", "Max evidence characters in the prompt. Raise for larger-context models."],
        [c("KNOWLEDGE/ANALYSIS/AUTOMATION_MCP_PORT"), "8100 / 8101 / 8102", "Documentation only."],
        [c("LANGCHAIN_TRACING_V2, LANGCHAIN_API_KEY, LANGCHAIN_PROJECT"), "unset", "Optional LangSmith tracing."],
    ], [2, 1.5, 2.6])
    story.append(P("Code constants (change in source): " + c("CHUNK_CHARS=3000") + ", " + c("CHUNK_OVERLAP=300")
                   + " (" + c("rag/ingestion/loader.py") + "); " + c("CHROMA_QUERY_TIMEOUT=30") + " ("
                   + c("chroma_store.py") + "); " + c("MAX_RETRIES=2") + " (" + c("routing.py") + "); "
                   "LLM retries = 3 (" + c("core/llm.py") + ")."))
    brk(story)

    # ---------- 12 Installation & operation ----------
    story += [H1("12  Installation and Operation"), H2("12.1  Reference environment")]
    story += table([
        ["Component", "Version / value"],
        ["OS", "Windows 11 Pro (build 26200)"],
        ["CPU inference", "AMD Radeon Vega 10 integrated graphics (no CUDA); 14 GB RAM"],
        ["Python", "3.12.10 in " + c("venv/") + " (3.15 is too new for onnxruntime/chromadb wheels)"],
        ["Ollama", "0.40.16"],
        ["Models", c("llama3.2:3b") + " (2.0 GB, active), " + c("llama3.1") + " (4.9 GB), " + c("nomic-embed-text") + " (274 MB)"],
        ["Key packages", "chromadb 1.5, langgraph 1.2, fastmcp 4.2, pydantic 2.14, markitdown 0.1.9 with PDF/Office extras"],
        ["System runtime", "Microsoft Visual C++ 2015+ Redistributable (x64), required by onnxruntime"],
    ], [1.2, 4])
    story += [H2("12.2  Installation steps (Windows)")]
    story.append(code("""
# 1. Python 3.12 next to any newer system Python (Python install manager)
py install 3.12

# 2. Native runtime and model server
winget install Microsoft.VCRedist.2015+.x64
winget install Ollama.Ollama

# 3. Project environment
cd Autoagent
py -V:3.12 -m venv venv
venv\\Scripts\\python -m pip install -r requirements.txt
copy .env.example .env            # then set LLM_MODEL (see 12.5)

# 4. Models
ollama pull nomic-embed-text
ollama pull llama3.2:3b           # or llama3.1 on machines with >= 16 GB free RAM / a GPU

# 5. Knowledge base (only needed if data/ changed; the repo ships a built index)
venv\\Scripts\\python main.py --ingest
"""))
    story += [H2("12.3  Running")]
    story += table([
        ["Command", "Effect"],
        [c("python main.py"), "Demo investigation of SC-042."],
        [c("python main.py --query \"…\""), "Custom request. Include an " + c("SC-nnn") + " id to load scenario metadata."],
        [c("python main.py --model llama3.1"), "Override the model for this run."],
        [c("python main.py --task-id INV-2026-001"), "Fixed task id (report file name, audit key)."],
        [c("python main.py --ingest"), "Rebuild the vector store before running."],
        [c("echo approve | python main.py"), "Non-interactive approval (testing)."],
    ], [2.2, 3])
    story.append(P("Set " + c("PYTHONIOENCODING=utf-8") + " if the console shows encoding errors for "
                   "box-drawing or emoji characters in the output."))
    story += [H2("12.4  Measured performance")]
    story.append(P("Full SC-042 run on the reference machine with " + c("llama3.2:3b") + " (22 Nov 2026, task "
                   + c("SETUP-TEST") + "): all agents succeeded, validation passed first time."))
    story += table([
        ["Stage", "Duration", "Result"],
        ["Evidence", "3 min 25 s", "3 incidents, 1 requirement, 5 gaps"],
        ["Technical", "4 min 32 s", "2 findings, confidence 0.60"],
        ["Quality", "2 min 56 s", "4 findings, confidence 0.80"],
        ["Compliance", "2 min 46 s", "2 findings, confidence 0.65"],
        ["Critic", "5 min 23 s", "1 agreement, 2 disagreements, 1 weak claim"],
        ["Synthesis", "5 min 25 s", "2 accepted, 2 rejected"],
        ["Validator", "3 min 57 s", "passed, 3 supported / 0 unsupported"],
        ["<b>Total</b>", "<b>28 min 24 s</b>", "report + ticket written"],
    ], [1.3, 1.2, 3])
    story += [H2("12.5  Choosing a model")]
    story += bullets([
        "<b>llama3.2:3b</b>: fits CPU-only machines with ~4 GB free RAM. JSON compliance was good in testing; reasoning depth and use of long evidence are limited.",
        "<b>llama3.1 (8B)</b>: noticeably better analysis but needs ~6 GB RAM for the model alone. On the reference PC it was terminated for low memory while other applications were open.",
        "<b>vLLM + GPU</b>: for production throughput; enable parallel specialists and raise " + c("LLM_MAX_CONCURRENT") + ".",
        "When moving to a model with a larger context window, raise " + c("EVIDENCE_CHAR_BUDGET") + " accordingly.",
    ])
    brk(story)

    # ---------- 13 Development guide ----------
    story += [H1("13  Development Guide"), H2("13.1  Conventions")]
    story += bullets([
        "No loose dictionaries between agents: every new hand-off gets a Pydantic model in " + c("core/schemas.py") + ".",
        "Prompts live in " + c("skills/") + "; Python builds only the data part of the prompt.",
        "Every LLM-backed node catches " + c("LLMParseError") + "/" + c("ConnectionError") + " and returns a contract-shaped placeholder.",
        "Every agent logs " + c("agent_start") + " and " + c("agent_complete") + "; side effects log " + c("action_executed") + ".",
        "Dependencies arrive through " + c("PipelineContext") + ", never module globals.",
        "File-system writes go through the automation tools, which validate paths.",
    ])
    story += [H2("13.2  Tuning agent behaviour")]
    story.append(P("Edit the agent's " + c("skills/<agent>.md") + ": rules, domain knowledge, tone, field "
                   "guidance. No restart of anything other than the run itself is needed. Keep any "
                   "examples consistent with the agent's contract."))
    story += [H2("13.3  Adding a new agent")]
    story += numbered([
        "<b>Contract</b>: add an output model to " + c("core/schemas.py") + ".",
        "<b>Skill</b>: create " + c("skills/<name>.md") + " with Role, Goal, Context, Rules and output guidance.",
        "<b>Agent</b>: create " + c("agents/<name>.py") + " following the anatomy in §4.1.",
        "<b>State</b>: add an output key to " + c("InvestigationState") + ".",
        "<b>Node</b>: add a guarded node function with a placeholder to " + c("orchestrator/nodes.py") + ".",
        "<b>Wiring</b>: register the node and edges in " + c("build_graph()") + ".",
        "<b>Consumers</b>: pass the new key to downstream agents and, if relevant, to the report in " + c("prepare_human_review") + ".",
        "<b>Verify</b>: run the agent alone (§13.8), then a full run.",
    ])
    story.append(code("""
# agents/safety_case_agent.py
class SafetyCaseAgent:
    def __init__(self, llm: LLM):
        self.llm = llm
        self.skill = load_skill("safety_case_agent")

    def run(self, task_id: str, final_synthesis: dict) -> SafetyCaseReview:
        log_event("agent_start", "safety_case_agent", task_id)
        prompt = f"Investigation {task_id}.\\nSynthesis:\\n{json.dumps(final_synthesis, indent=2)}\\n" \\
                 "Assess the impact on the safety case. Produce a SafetyCaseReview as JSON."
        out = self.llm.generate_structured(prompt=prompt, schema=SafetyCaseReview, system=self.skill)
        log_event("agent_complete", "safety_case_agent", task_id, data={"items": len(out.items)})
        return out

# orchestrator/graph.py
graph.add_node("run_safety_case", run_safety_case)
graph.add_edge("run_validation", ...)   # insert where it belongs in the flow
"""))
    story += [H2("13.4  Adding a specialist perspective")]
    story.append(P("For another opinion of the same shape (e.g. cybersecurity), subclass "
                   + c("BaseSpecialistAgent") + ", write " + c("skills/cyber_agent.md") + ", add "
                   + c("cyber_opinion") + " to the state, a node, graph edges (in both the sequential chain "
                   "and the parallel fan-out), and pass the opinion to the critic and synthesis agents."))
    story += [H2("13.5  Adding a tool")]
    story += numbered([
        "Add a function decorated with " + c("@mcp.tool()") + " to the appropriate server (or a new server module).",
        "Type its parameters and return a Pydantic model or plain JSON-serialisable value.",
        "Validate any path or identifier input; never build file paths from raw strings.",
        "Call it from a node or deterministic agent through the decorated function, not server internals.",
    ])
    story += [H2("13.6  Extending the knowledge base")]
    story.append(P("Drop files into an existing or new sub-folder of " + c("data/") + " (the folder name becomes "
                   "the category) and run " + c("python main.py --ingest") + ". Add a scenario JSON to "
                   + c("data/scenarios/") + " to make " + c("SC-nnn") + " requests load its metadata; the "
                   "evidence agent automatically turns its fields into search queries."))
    story += [H2("13.7  Switching backend or model")]
    story.append(code("""
# .env — larger local model
LLM_MODEL=llama3.1

# .env — vLLM server
LLM_BACKEND=vllm
VLLM_BASE_URL=http://gpu-server:8000/v1
VLLM_MODEL=meta-llama/Llama-3.1-8B-Instruct
"""))
    story += [H2("13.8  Verification recipes")]
    story.append(P("There is no automated test suite yet. These checks were used during development:"))
    story.append(code("""
# Import smoke test (all modules load, dependencies present)
python -c "import main, mcp_servers.knowledge_server, mcp_servers.analysis_server, mcp_servers.automation_server"

# Retrieval only — no LLM call
python -c "from rag.setup import build_knowledge_adapter as b; a=b(); \\
  [print(round(r.score,3), r.source, r.metadata.get('chunk')) for r in a.search('rain camera', 5)]"

# One agent with the real model (~4 min on CPU)
python -c "import json; from rag.setup import build_knowledge_adapter as b; from core.llm import LLM; \\
  from agents.evidence_agent import EvidenceAgent; sc=json.load(open('data/scenarios/SC-042.json')); \\
  print(EvidenceAgent(LLM(), b()).run('T1', 'Investigate SC-042', sc))"

# Full run, non-interactive
echo approve | python main.py --task-id TEST-001
"""))
    story += callout("Test runs append to " + c("audit/events.jsonl") + " and may write files to "
                     + c("workspace/") + ". Opening the vector store also updates internal ChromaDB files. "
                     "Restore them before committing: " + c("git checkout -- audit rag/vectorstores/chroma_db") + ".", "info")
    story += [H2("13.9  Repository practice")]
    story += bullets([
        c(".gitattributes") + " marks " + c("chroma_db/**") + ", " + c("*.bin") + ", " + c("*.sqlite3") + " and " + c("*.pdf") + " as binary. Without it, Windows line-ending conversion can corrupt the vector index on commit.",
        "The built vector store is committed so fresh clones work without ingestion; rebuild and commit it when " + c("data/") + " or chunking changes.",
        c("venv/") + ", " + c(".env") + " and " + c("__pycache__/") + " are excluded locally via " + c(".git/info/exclude") + ". Adding a project " + c(".gitignore") + " is recommended.",
        "Commits are authored under the maintainer's git identity.",
    ])
    brk(story)

    # ---------- 14 History ----------
    story += [H1("14  Development History"), H2("14.1  Initial development (July 2026)")]
    story += table([
        ["Commit", "Date", "Change"],
        [c("aa18b22"), "2026-07-11", "Initial commit: pipeline, agents, RAG, MCP servers."],
        [c("aba3b7f"), "2026-07-12", "Fixes."],
        [c("92ba995"), "2026-07-12", "vLLM backend; ingestion of any file type via MarkItDown."],
        [c("ada1397"), "2026-07-12", "Documentation."],
        [c("ec67468"), "2026-07-13", "Path-traversal fixes in MCP servers; report backup strategy."],
        [c("cbaaf01"), "2026-07-13", "Timeouts for LLM backends and ChromaDB queries."],
        [c("829253a"), "2026-07-13", "Removed unused imports and dead code."],
        [c("fbd6a50"), "2026-07-13", "Fixed partial-line read race in the audit logger (shared lock)."],
        [c("4a16098"), "2026-07-13", "Node-level error handling, structlog, SIGTERM handler."],
        [c("8e47b27"), "2026-07-13", "Stronger Pydantic schemas; automation agent uses typed results."],
        [c("89f8820"), "2026-07-13", "Rate-limit semaphore, all parse errors surfaced, exponential backoff."],
        [c("7a6386a"), "2026-07-13", "Graceful empty RAG results; embedding-model version check."],
        [c("48dd526"), "2026-07-13", "Configuration and README for production architecture."],
        [c("2c9b004"), "2026-07-13", "LangSmith tracing for LLM and LangGraph."],
        [c("4f41ba6"), "2026-07-13", "Increased LLM timeout (later found to break Windows)."],
        [c("b3e64e1"), "2026-07-13", "Critic skill examples aligned with the Disagreement schema."],
        [c("52064e9, 94626a2"), "2026-07-13", "README renamed to AFAMA."],
    ], [1, 0.9, 4])
    story += [H2("14.2  Windows port and retrieval fixes (November 2026)")]
    story += table([
        ["Issue", "Symptom", "Root cause", "Fix"],
        ["Python too new", "Dependency wheels unavailable", "System Python 3.15", "Python 3.12 venv"],
        ["onnxruntime", c("DLL load failed while importing onnxruntime_pybind11_state"), "VC++ runtime missing", "Installed VC++ 2015+ Redistributable"],
        ["Every LLM call failed", c("OverflowError: timeout doesn't fit into C timeval"), "Timeout 9 999 999 s exceeds the Windows socket limit (~2 147 483 s)", c("LLM_TIMEOUT") + " capped at 2 000 000 s (" + c("fc6463d") + ")"],
        ["ISO 26262 never indexed", "MarkItDown asked for " + c("markitdown[pdf]") + "; file skipped", "PDF extras not installed", "Extras added to requirements (" + c("fc6463d") + ")"],
        ["PDF embedding crashed", c("input length exceeds the context length"), "Whole documents embedded in one call", "Overlapping chunking; " + c("ollama.embed(truncate=True)") + "; chunk ids (" + c("fc6463d") + ")"],
        ["Vector index at risk", "Git warned LF→CRLF on " + c(".bin") + " files", "autocrlf treated binaries as text", c(".gitattributes") + " (" + c("3c139e3") + ")"],
        ["Out of memory", "Run killed during first LLM call", "8B model on 14 GB shared RAM", "Switched to " + c("llama3.2:3b") + "; full run verified (" + c("3c139e3") + ")"],
        ["Domain-locked retrieval", "Brake queries searched for camera evidence", "Hard-coded queries", "Queries derived from request and scenario (§4.5)"],
        ["Large documents under-used", "Only one ISO chunk reached the LLM", "De-duplication by file name", "Per-chunk de-duplication with per-file cap and character budget (§4.5)"],
    ], [1.1, 1.6, 1.5, 1.8])
    story += callout("The last two rows (evidence retrieval) are implemented in the working tree of "
                     + c("agents/evidence_agent.py") + " and " + c("config.py") + " and were verified with "
                     "retrieval tests and an Evidence Agent run; commit them together with this manual.", "info")

    # ---------- 15 Limitations ----------
    story += [H1("15  Known Limitations and Roadmap")]
    story += table([
        ["Area", "Limitation", "Suggested improvement"],
        ["Retry loop", "Synthesis retries use the identical prompt; validator issues are not fed back, so at temperature 0.1 a retry rarely changes the result.", "Pass " + c("validation_report.issues") + " into the synthesis prompt on retries."],
        ["Critic", "The critic sees the three opinions but not the evidence report, so it cannot check claims against sources.", "Add the evidence report (or its source list) to the critic prompt."],
        ["Human approval", "CLI " + c("input()") + " only; any answer other than " + c("approve") + " rejects.", "Streamlit or API approval; confirm unexpected input."],
        ["Proposed actions", "Always the same two actions.", "Let synthesis propose actions within the " + c("ProposedAction") + " contract."],
        ["MCP usage", "Evidence agent calls the adapter directly; knowledge-server tools are unused; ports unused.", "Route retrieval through the tools; add a client mode."],
        ["Corpus", "Focused on camera/radar pedestrian detection.", "Add documents per system (brakes, steering, powertrain)."],
        ["Model quality", "3B model under-uses long evidence and can mix details (the sample report says “dusk” for a night scenario).", "Larger model or GPU host; add a reranker; keep validation strict."],
        ["Context window", "Ollama " + c("num_ctx") + " is not set explicitly; protection relies on the evidence budget.", "Expose " + c("num_ctx") + " in config and size budgets from it."],
        ["Testing", "No automated tests or CI.", "Unit tests for parsing, routing and selection; a recorded-response integration test."],
        ["Privacy", "LangSmith tracing, if enabled, sends prompts off-host.", "Keep disabled or self-host."],
        ["Code hygiene", "Backoff cap constant is far larger than its “30 s” comment (harmless: max wait is 4 s).", "Set the constant to 30."],
    ], [1.1, 2.6, 2.3])
    brk(story)

    # ---------- 16 Troubleshooting ----------
    story += [H1("16  Troubleshooting")]
    story += table([
        ["Symptom", "Likely cause", "Action"],
        [c("Failed to reach 'ollama' backend after 3 attempts"), "Ollama not running, model not pulled, out of memory.", "Start Ollama; " + c("ollama list") + "; " + c("ollama ps") + "; use a smaller model."],
        [c("OverflowError: timeout doesn't fit into C timeval"), "Pre-fix code on Windows.", "Update to " + c("fc6463d") + " or later; keep " + c("LLM_TIMEOUT") + " ≤ 2 000 000."],
        [c("ImportError: DLL load failed … onnxruntime"), "VC++ runtime missing.", c("winget install Microsoft.VCRedist.2015+.x64")],
        ["pip: no matching distribution", "Python version too new, or network timeout.", "Use Python 3.12; " + c("pip install --timeout 60 --retries 8 …")],
        [c("input length exceeds the context length") + " during ingest", "Pre-fix embedder.", "Update code; " + c("python main.py --ingest") + "."],
        ["RuntimeError about embedding model mismatch", c("EMBED_MODEL") + " differs from the ingested collection.", c("python main.py --ingest")],
        ["Repeated " + c("LLM parse attempt … failed"), "Model not following JSON format, or output truncated.", "Larger model; raise " + c("LLM_MAX_TOKENS") + "; check the skill's examples."],
        ["Process killed / system freezes", "Not enough RAM for the model.", "Close applications; " + c("llama3.2:3b") + "."],
        ["Report full of “Agent failed” placeholders", "LLM unavailable during the run.", "Check console " + c("node_agent_error") + " lines and " + c("node_error") + " audit events."],
        ["Garbled console characters / UnicodeEncodeError", "Windows console code page.", c("set PYTHONIOENCODING=utf-8")],
        [c("git push") + " 401 Unauthorized", "Not signed in to GitHub.", c("git credential-manager github login")],
    ], [2, 1.8, 2.2])

    # ---------- Appendix ----------
    story += [H1("Appendix A  Sample Output")]
    story.append(P("Excerpt of " + c("workspace/reports/SETUP-TEST.md") + " produced by the verified run "
                   "(llama3.2:3b, 22 Nov 2026):"))
    story.append(code("""
# Investigation Report: SETUP-TEST

## Accepted Findings
- Camera model's performance in combined rain+dusk conditions is not documented, making it
  difficult to assess its reliability under these conditions (supported by Technical Agent,
  corroborated by Quality Agent)
- System FMEA does not explicitly consider combined rain+dusk as a separate scenario, which may
  lead to inadequate risk assessment (supported by Quality Agent, confirmed by Compliance Agent)

## Rejected Findings
- Potential non-compliance with SOTIF acceptance criteria for pedestrian detection under adverse
  visibility (rejected due to sparse evidence and conflicting claims)

## Recommended Next Steps
- Obtain and review the camera model card to validate performance envelope for rain+dusk conditions
- Add combined adverse visibility scenarios (rain+dusk, fog+night) to the V&V test plan
- Verify sensor fusion fallback behaviour when camera confidence is below threshold

## Validation
Passed: True
Supported claims: 3
Unsupported claims: 0
"""))
    story.append(P("The matching ticket " + c("workspace/tickets/ENG-20261122-155156.json") + " carries the "
                   "final summary as its body and the five recommended next steps in its metadata."))

    doc = ManualDoc(str(OUT))
    doc.multiBuild(story)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    build()
