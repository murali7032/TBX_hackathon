"""Generate an aesthetically refined TBX Insight hackathon presentation."""
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt, Emu

OUT = Path(__file__).resolve().parent / "TBX_Insight_Hackathon_Presentation.pptx"
OUT_ALT = Path(__file__).resolve().parent / "TBX_Insight_Presentation_v2.pptx"

# Brand palette
NAVY = RGBColor(0x0B, 0x1F, 0x3A)
NAVY_DEEP = RGBColor(0x07, 0x16, 0x2A)
CYAN = RGBColor(0x00, 0xAE, 0xEF)
CYAN_SOFT = RGBColor(0xD9, 0xF3, 0xFC)
CYAN_MID = RGBColor(0x4D, 0xC9, 0xF5)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
SLATE = RGBColor(0x1E, 0x29, 0x3B)
BODY = RGBColor(0x33, 0x41, 0x55)
MUTED = RGBColor(0x64, 0x74, 0x8B)
LIGHT = RGBColor(0xF1, 0xF5, 0xF9)
CARD = RGBColor(0xFF, 0xFF, 0xFF)
LINE = RGBColor(0xE2, 0xE8, 0xF0)
WARM = RGBColor(0xF8, 0xFA, 0xFC)

FONT = "Calibri"
TOTAL = 14


def set_run(run, size=14, bold=False, color=BODY, italic=False):
    run.font.name = FONT
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color


def fill_shape(shape, color):
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()


def stroke(shape, color=LINE, width=1):
    shape.line.color.rgb = color
    shape.line.width = Pt(width)


def round_rect(slide, left, top, width, height, fill=CARD, border=LINE, radius=0.1):
    s = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    fill_shape(s, fill)
    if border:
        stroke(s, border, 1)
    else:
        s.line.fill.background()
    try:
        s.adjustments[0] = radius
    except Exception:
        pass
    return s


def rect(slide, left, top, width, height, color):
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    fill_shape(s, color)
    return s


def oval(slide, left, top, width, height, color):
    s = slide.shapes.add_shape(MSO_SHAPE.OVAL, left, top, width, height)
    fill_shape(s, color)
    return s


def textbox(slide, left, top, width, height, lines, valign=MSO_ANCHOR.TOP):
    """lines: list of dicts or tuples (text, size, bold, color, align?, space_after?)."""
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.auto_size = None
    try:
        tf._txBody.bodyPr.set("anchor", {MSO_ANCHOR.TOP: "t", MSO_ANCHOR.MIDDLE: "ctr", MSO_ANCHOR.BOTTOM: "b"}[valign])
    except Exception:
        pass

    first = True
    for item in lines:
        if isinstance(item, str):
            text, size, bold, color, align, after = item, 13, False, BODY, PP_ALIGN.LEFT, 6
        elif isinstance(item, dict):
            text = item.get("t", "")
            size = item.get("s", 13)
            bold = item.get("b", False)
            color = item.get("c", BODY)
            align = item.get("a", PP_ALIGN.LEFT)
            after = item.get("sa", 6)
        else:
            # tuple pad
            text = item[0]
            size = item[1] if len(item) > 1 else 13
            bold = item[2] if len(item) > 2 else False
            color = item[3] if len(item) > 3 else BODY
            align = item[4] if len(item) > 4 else PP_ALIGN.LEFT
            after = item[5] if len(item) > 5 else 6

        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.text = text
        p.alignment = align
        p.space_after = Pt(after)
        p.space_before = Pt(0)
        for r in p.runs:
            set_run(r, size=size, bold=bold, color=color)
    return box


def write_in_shape(shape, lines, valign=MSO_ANCHOR.TOP):
    tf = shape.text_frame
    tf.clear()
    tf.word_wrap = True
    try:
        shape.text_frame.paragraphs  # ensure
        tf.auto_size = None
    except Exception:
        pass
    first = True
    for item in lines:
        if isinstance(item, str):
            text, size, bold, color, align, after = item, 13, False, BODY, PP_ALIGN.LEFT, 4
        elif isinstance(item, dict):
            text = item["t"]
            size = item.get("s", 13)
            bold = item.get("b", False)
            color = item.get("c", BODY)
            align = item.get("a", PP_ALIGN.LEFT)
            after = item.get("sa", 4)
        else:
            text = item[0]
            size = item[1] if len(item) > 1 else 13
            bold = item[2] if len(item) > 2 else False
            color = item[3] if len(item) > 3 else BODY
            align = item[4] if len(item) > 4 else PP_ALIGN.LEFT
            after = item[5] if len(item) > 5 else 4
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.text = text
        p.alignment = align
        p.space_after = Pt(after)
        for r in p.runs:
            set_run(r, size=size, bold=bold, color=color)


def page_bg(slide, tinted=False):
    rect(slide, Inches(0), Inches(0), Inches(13.333), Inches(7.5), WARM if not tinted else LIGHT)
    # soft decorative orbs
    o1 = oval(slide, Inches(11.6), Inches(-0.6), Inches(2.4), Inches(2.4), CYAN_SOFT)
    o2 = oval(slide, Inches(-0.8), Inches(6.2), Inches(2.0), Inches(2.0), CYAN_SOFT)


def header(slide, kicker, title, subtitle=None):
    """Slim branded header band."""
    rect(slide, Inches(0), Inches(0), Inches(13.333), Inches(1.15), NAVY)
    rect(slide, Inches(0), Inches(1.15), Inches(13.333), Inches(0.06), CYAN)
    # small accent pill
    pill = round_rect(slide, Inches(0.55), Inches(0.22), Inches(1.55), Inches(0.28), CYAN, None, 0.5)
    write_in_shape(pill, [{"t": kicker.upper(), "s": 9, "b": True, "c": NAVY, "a": PP_ALIGN.CENTER, "sa": 0}])
    textbox(
        slide,
        Inches(0.55),
        Inches(0.52),
        Inches(12),
        Inches(0.5),
        [{"t": title, "s": 24, "b": True, "c": WHITE, "sa": 0}],
    )
    if subtitle:
        textbox(
            slide,
            Inches(0.55),
            Inches(1.35),
            Inches(12.2),
            Inches(0.35),
            [{"t": subtitle, "s": 12, "b": False, "c": MUTED, "sa": 0}],
        )


def footer(slide, page):
    rect(slide, Inches(0), Inches(7.22), Inches(13.333), Inches(0.28), NAVY)
    textbox(
        slide,
        Inches(0.55),
        Inches(7.24),
        Inches(9),
        Inches(0.24),
        [{"t": "TBX Insight  ·  Corporate Banking Infrastructure for a Connected Financial Ecosystem", "s": 9, "c": CYAN_MID, "sa": 0}],
    )
    textbox(
        slide,
        Inches(11.5),
        Inches(7.24),
        Inches(1.4),
        Inches(0.24),
        [{"t": f"{page:02d}  /  {TOTAL:02d}", "s": 9, "b": True, "c": WHITE, "a": PP_ALIGN.RIGHT, "sa": 0}],
    )


def shot_slot(slide, left, top, width, height, caption):
    """Elegant screenshot drop zone."""
    outer = round_rect(slide, left, top, width, height, WHITE, CYAN, 0.06)
    # inner dashed-feel panel
    inner = round_rect(
        slide,
        left + Inches(0.12),
        top + Inches(0.12),
        width - Inches(0.24),
        height - Inches(0.24),
        LIGHT,
        None,
        0.05,
    )
    write_in_shape(
        inner,
        [
            {"t": "＋  Add screenshot", "s": 16, "b": True, "c": NAVY, "a": PP_ALIGN.CENTER, "sa": 8},
            {"t": caption, "s": 11, "c": MUTED, "a": PP_ALIGN.CENTER, "sa": 4},
            {"t": "Insert → Pictures  ·  replace this frame", "s": 10, "c": MUTED, "a": PP_ALIGN.CENTER, "sa": 0},
        ],
    )
    return outer


def section_label(slide, left, top, text):
    pill = round_rect(slide, left, top, Inches(len(text) * 0.11 + 0.4), Inches(0.28), CYAN_SOFT, None, 0.5)
    write_in_shape(pill, [{"t": text.upper(), "s": 9, "b": True, "c": NAVY, "a": PP_ALIGN.CENTER, "sa": 0}])


def blank(prs):
    return prs.slide_layouts[6]


def build():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    layout = blank(prs)

    # ═══════════════════════════════════════
    # 1 · TITLE
    # ═══════════════════════════════════════
    s = prs.slides.add_slide(layout)
    rect(s, Inches(0), Inches(0), Inches(13.333), Inches(7.5), NAVY_DEEP)
    # geometric accents
    rect(s, Inches(0), Inches(0), Inches(0.22), Inches(7.5), CYAN)
    oval(s, Inches(10.8), Inches(-1.2), Inches(4), Inches(4), RGBColor(0x0F, 0x2A, 0x4A))
    oval(s, Inches(11.5), Inches(5.2), Inches(3), Inches(3), RGBColor(0x0D, 0x28, 0x45))
    # cyan diagonal hint bar
    rect(s, Inches(0), Inches(6.85), Inches(13.333), Inches(0.08), CYAN)

    textbox(s, Inches(0.9), Inches(1.55), Inches(10), Inches(0.35),
            [{"t": "TBX FINANCE  ·  BVP TECH CATALYST HACKATHON", "s": 11, "b": True, "c": CYAN, "sa": 0}])
    textbox(s, Inches(0.9), Inches(2.1), Inches(11), Inches(1.1),
            [{"t": "TBX Insight", "s": 54, "b": True, "c": WHITE, "sa": 0}])
    textbox(s, Inches(0.9), Inches(3.35), Inches(10), Inches(1.1),
            [
                {"t": "A grounded finance assistant that answers", "s": 20, "c": RGBColor(0xCB, 0xD5, 0xE1), "sa": 2},
                {"t": "from your ledger — never from guesses.", "s": 20, "c": CYAN, "sa": 0},
            ])
    # bottom meta chips
    for i, label in enumerate(["React + FastAPI", "PostgreSQL", "Gemini Flash / Lite", "Evidence-first UX"]):
        x = 0.9 + i * 2.9
        chip = round_rect(s, Inches(x), Inches(5.5), Inches(2.7), Inches(0.42), RGBColor(0x12, 0x2F, 0x4E), None, 0.4)
        write_in_shape(chip, [{"t": label, "s": 11, "b": True, "c": WHITE, "a": PP_ALIGN.CENTER, "sa": 0}])

    # ═══════════════════════════════════════
    # 2 · AGENDA
    # ═══════════════════════════════════════
    s = prs.slides.add_slide(layout)
    page_bg(s)
    header(s, "Overview", "Agenda", "A focused path from problem → proof")
    items = [
        ("01", "Problem", "Why finance Q&A fails without grounding"),
        ("02", "Approach", "SQL-first tools, evidence, guardrails"),
        ("03", "Architecture", "End-to-end system & request path"),
        ("04", "Model choice", "Smallest model that stays accurate"),
        ("05", "Demo flow", "Live walkthrough script"),
        ("06", "Sample Q&A", "Grounded answers + screenshot slots"),
    ]
    for i, (num, title, desc) in enumerate(items):
        col = i % 3
        row = i // 3
        x = 0.55 + col * 4.2
        y = 1.95 + row * 2.35
        c = round_rect(s, Inches(x), Inches(y), Inches(3.95), Inches(2.05), WHITE, LINE, 0.08)
        # left accent
        rect(s, Inches(x), Inches(y), Inches(0.1), Inches(2.05), CYAN)
        textbox(s, Inches(x + 0.35), Inches(y + 0.35), Inches(3.3), Inches(1.5),
                [
                    {"t": num, "s": 28, "b": True, "c": CYAN, "sa": 6},
                    {"t": title, "s": 18, "b": True, "c": NAVY, "sa": 6},
                    {"t": desc, "s": 12, "c": MUTED, "sa": 0},
                ])
    footer(s, 2)

    # ═══════════════════════════════════════
    # 3 · PROBLEM
    # ═══════════════════════════════════════
    s = prs.slides.add_slide(layout)
    page_bg(s)
    header(s, "Context", "The problem", "Routine finance questions shouldn’t require a dashboard expedition")

    left = round_rect(s, Inches(0.55), Inches(1.75), Inches(6.05), Inches(4.9), WHITE, LINE, 0.08)
    textbox(s, Inches(0.85), Inches(2.0), Inches(5.5), Inches(4.4),
            [
                {"t": "TODAY", "s": 10, "b": True, "c": CYAN, "sa": 8},
                {"t": "Finance teams field the same lookups on repeat.", "s": 16, "b": True, "c": NAVY, "sa": 12},
                {"t": "• Static reports & exports for simple questions", "s": 13, "c": BODY, "sa": 6},
                {"t": "• Vendor spend / unreconciled status = wait on ops", "s": 13, "c": BODY, "sa": 6},
                {"t": "• Everyday decisions slow down", "s": 13, "c": BODY, "sa": 14},
                {"t": "THE STAKES", "s": 10, "b": True, "c": CYAN, "sa": 8},
                {"t": "An invented number isn’t a minor bug —", "s": 14, "c": BODY, "sa": 4},
                {"t": "it’s a liability for audits and trust.", "s": 14, "b": True, "c": NAVY, "sa": 0},
            ])

    right = round_rect(s, Inches(6.85), Inches(1.75), Inches(5.95), Inches(4.9), NAVY, None, 0.08)
    textbox(s, Inches(7.2), Inches(2.05), Inches(5.3), Inches(4.4),
            [
                {"t": "CHALLENGE", "s": 10, "b": True, "c": CYAN, "sa": 10},
                {"t": "Plain-language questions.\nLedger-truthful answers.", "s": 20, "b": True, "c": WHITE, "sa": 14},
                {"t": "✓ Natural language understanding", "s": 13, "c": RGBColor(0xE2, 0xE8, 0xF0), "sa": 7},
                {"t": "✓ Grounded retrieval only", "s": 13, "c": RGBColor(0xE2, 0xE8, 0xF0), "sa": 7},
                {"t": "✓ Verifiable evidence + SQL", "s": 13, "c": RGBColor(0xE2, 0xE8, 0xF0), "sa": 7},
                {"t": "✓ Honest “insufficient data”", "s": 13, "c": RGBColor(0xE2, 0xE8, 0xF0), "sa": 7},
                {"t": "✓ Lightweight model constraint", "s": 13, "c": RGBColor(0xE2, 0xE8, 0xF0), "sa": 14},
                {"t": "Scoring focus: Grounding 30%  ·  Efficiency 20%", "s": 11, "b": True, "c": CYAN, "sa": 0},
            ])
    footer(s, 3)

    # ═══════════════════════════════════════
    # 4 · APPROACH
    # ═══════════════════════════════════════
    s = prs.slides.add_slide(layout)
    page_bg(s)
    header(s, "Method", "Our approach", "Compute in SQL · Explain in language · Never invent figures")

    pillars = [
        ("01", "Grounded retrieval", "Every fact comes from PostgreSQL via read-only SELECT tools — never model memory."),
        ("02", "Compute, then narrate", "Filters, MoM %, anomalies run in SQL. The LLM only explains returned rows."),
        ("03", "Verifiable answers", "Plain answer + evidence table + collapsible SQL + CSV / Excel export."),
        ("04", "Hard guardrails", "Ambiguity → chips. Missing data → say so. Thumbs-down → regenerate SQL."),
    ]
    for i, (num, title, body) in enumerate(pillars):
        col, row = i % 2, i // 2
        x, y = 0.55 + col * 6.4, 1.85 + row * 2.45
        c = round_rect(s, Inches(x), Inches(y), Inches(6.1), Inches(2.2), WHITE, LINE, 0.08)
        badge = round_rect(s, Inches(x + 0.3), Inches(y + 0.35), Inches(0.7), Inches(0.7), CYAN_SOFT, None, 0.2)
        write_in_shape(badge, [{"t": num, "s": 16, "b": True, "c": NAVY, "a": PP_ALIGN.CENTER, "sa": 0}])
        textbox(s, Inches(x + 1.2), Inches(y + 0.4), Inches(4.5), Inches(1.5),
                [
                    {"t": title, "s": 17, "b": True, "c": NAVY, "sa": 8},
                    {"t": body, "s": 13, "c": MUTED, "sa": 0},
                ])
    footer(s, 4)

    # ═══════════════════════════════════════
    # 5 · ARCHITECTURE
    # ═══════════════════════════════════════
    s = prs.slides.add_slide(layout)
    page_bg(s)
    header(s, "System", "Architecture", "TBX Insight — grounded tool-calling loop")

    layers = [
        ("USER", "TBX Insight UI", "React · Vite\nChat + Dashboard", CYAN_SOFT, NAVY),
        ("API", "FastAPI Gateway", "/chat · /api\n/export · /health", WHITE, NAVY),
        ("AGENT", "Gemini Tool Loop", "Session memory\nSchema-aware tools", NAVY, WHITE),
        ("DATA", "PostgreSQL 18", "bank · account\n\"transaction\"", WHITE, NAVY),
    ]
    for i, (kicker, title, body, bg, fg) in enumerate(layers):
        x = 0.45 + i * 3.2
        c = round_rect(s, Inches(x), Inches(1.8), Inches(2.95), Inches(2.35), bg, LINE if bg != NAVY else None, 0.08)
        textbox(s, Inches(x + 0.2), Inches(1.95), Inches(2.55), Inches(2.0),
                [
                    {"t": kicker, "s": 10, "b": True, "c": CYAN if bg == NAVY else CYAN, "sa": 6},
                    {"t": title, "s": 15, "b": True, "c": fg if bg == NAVY else NAVY, "sa": 8},
                    {"t": body, "s": 12, "c": RGBColor(0xCB, 0xD5, 0xE1) if bg == NAVY else MUTED, "sa": 0},
                ])
        if i < 3:
            textbox(s, Inches(x + 2.85), Inches(2.7), Inches(0.4), Inches(0.4),
                    [{"t": "›", "s": 22, "b": True, "c": CYAN, "sa": 0}])

    tools = round_rect(s, Inches(0.45), Inches(4.4), Inches(12.4), Inches(1.05), WHITE, LINE, 0.08)
    textbox(s, Inches(0.7), Inches(4.55), Inches(12), Inches(0.8),
            [
                {"t": "TOOL BELT", "s": 10, "b": True, "c": CYAN, "sa": 4},
                {"t": "read_database_guide   ·   list_tables   ·   run_sql_query   ·   find_accounts   ·   analyze_debit_trends", "s": 12, "b": True, "c": NAVY, "sa": 0},
            ])

    contract = round_rect(s, Inches(0.45), Inches(5.6), Inches(12.4), Inches(1.05), NAVY, None, 0.08)
    textbox(s, Inches(0.7), Inches(5.75), Inches(12), Inches(0.8),
            [
                {"t": "RESPONSE CONTRACT", "s": 10, "b": True, "c": CYAN, "sa": 4},
                {"t": "answer  +  evidence{sql, columns, rows}  +  confidence  +  status  +  choices / insights", "s": 12, "c": WHITE, "sa": 0},
            ])
    footer(s, 5)

    # ═══════════════════════════════════════
    # 6 · REQUEST PATH
    # ═══════════════════════════════════════
    s = prs.slides.add_slide(layout)
    page_bg(s)
    header(s, "System", "Request path", "From natural language to a verified ledger answer")

    steps = [
        ("1", "Ask", "NL question +\noptimize_for"),
        ("2", "Clarify", "Ambiguous?\nAccount chips"),
        ("3", "Plan", "LLM selects\ntools + SQL"),
        ("4", "Query", "Read-only\nPostgres"),
        ("5", "Evidence", "Rows + SQL\nretained"),
        ("6", "Answer", "Narrate only\nfrom rows"),
    ]
    for i, (n, title, body) in enumerate(steps):
        x = 0.4 + i * 2.15
        # circle number
        circ = oval(s, Inches(x + 0.65), Inches(1.75), Inches(0.55), Inches(0.55), CYAN)
        textbox(s, Inches(x + 0.65), Inches(1.82), Inches(0.55), Inches(0.45),
                [{"t": n, "s": 14, "b": True, "c": NAVY, "a": PP_ALIGN.CENTER, "sa": 0}])
        c = round_rect(s, Inches(x), Inches(2.5), Inches(2.0), Inches(1.85), WHITE, LINE, 0.08)
        textbox(s, Inches(x + 0.15), Inches(2.7), Inches(1.7), Inches(1.5),
                [
                    {"t": title, "s": 14, "b": True, "c": NAVY, "a": PP_ALIGN.CENTER, "sa": 8},
                    {"t": body, "s": 11, "c": MUTED, "a": PP_ALIGN.CENTER, "sa": 0},
                ])
        if i < 5:
            textbox(s, Inches(x + 1.9), Inches(3.2), Inches(0.3), Inches(0.35),
                    [{"t": "→", "s": 14, "b": True, "c": CYAN, "sa": 0}])

    note = round_rect(s, Inches(0.45), Inches(4.7), Inches(12.4), Inches(1.95), NAVY, None, 0.08)
    textbox(s, Inches(0.8), Inches(4.95), Inches(11.8), Inches(1.6),
            [
                {"t": "DATA MODEL", "s": 10, "b": True, "c": CYAN, "sa": 8},
                {"t": "bank  (1)   ———<   account  (many)   ———<   \"transaction\"  (many)", "s": 15, "b": True, "c": WHITE, "sa": 10},
                {"t": "Seed  ·  10 banks  ·  10 accounts  ·  10 transactions     |     Hosting  ·  React → FastAPI → Gemini → Postgres on EC2", "s": 12, "c": RGBColor(0x94, 0xA3, 0xB8), "sa": 0},
            ])
    footer(s, 6)

    # ═══════════════════════════════════════
    # 7 · MODEL CHOICE
    # ═══════════════════════════════════════
    s = prs.slides.add_slide(layout)
    page_bg(s)
    header(s, "Efficiency", "Model choice rationale", "Constraint: lowest possible model, highest possible accuracy (≤ 20B)")

    # three model cards
    models = [
        ("EFFICIENT", "Gemini 3.5\nFlash-Lite", "Cost / speed mode\nRoutine lookups\nSame tool loop", CYAN_SOFT),
        ("PRIMARY", "Gemini 3.5\nFlash", "Balanced & Precision\nStrong tool use\nMulti-turn coherence", NAVY),
        ("NOT USED", "Frontier giants", "Scored down without\njustification\nAccuracy ≠ parameter count", WHITE),
    ]
    for i, (tag, name, body, bg) in enumerate(models):
        x = 0.55 + i * 4.2
        c = round_rect(s, Inches(x), Inches(1.8), Inches(3.95), Inches(2.7), bg, LINE if bg != NAVY else None, 0.08)
        fg = WHITE if bg == NAVY else NAVY
        muted = RGBColor(0xCB, 0xD5, 0xE1) if bg == NAVY else MUTED
        textbox(s, Inches(x + 0.3), Inches(2.0), Inches(3.35), Inches(2.3),
                [
                    {"t": tag, "s": 10, "b": True, "c": CYAN if bg == NAVY else CYAN, "sa": 8},
                    {"t": name, "s": 20, "b": True, "c": fg, "sa": 10},
                    {"t": body, "s": 12, "c": muted, "sa": 0},
                ])

    how = round_rect(s, Inches(0.55), Inches(4.75), Inches(12.2), Inches(1.9), WHITE, LINE, 0.08)
    textbox(s, Inches(0.85), Inches(4.95), Inches(11.6), Inches(1.55),
            [
                {"t": "HOW A SMALL MODEL STAYS ACCURATE", "s": 10, "b": True, "c": CYAN, "sa": 8},
                {"t": "Schema guide as a tool   ·   Hard “never invent” rules   ·   Aggregations in SQL   ·   Synthesis if tools exhaust   ·   Feedback → new SQL", "s": 13, "b": True, "c": NAVY, "sa": 8},
                {"t": "Result: lightweight NL layer + heavy lifting in the database — judged on efficiency without sacrificing grounding.", "s": 12, "c": MUTED, "sa": 0},
            ])
    footer(s, 7)

    # ═══════════════════════════════════════
    # 8 · DEMO FLOW
    # ═══════════════════════════════════════
    s = prs.slides.add_slide(layout)
    page_bg(s)
    header(s, "Live", "Demo flow", "Suggested 5–7 minute walkthrough")

    flow = [
        ("A", "Dashboard", "Open workspace metrics, spend-by-bank, top payees"),
        ("B", "Balances", "Ask HDFC balances — chips or summed evidence"),
        ("C", "Reference", "Lookup ref HDFCH01078329532 → exact debit row"),
        ("D", "Show the math", "Debits by month + MoM chart; expand SQL evidence"),
        ("E", "Exceptions", "Unreconciled (UTR NULL) or anomaly callouts"),
        ("F", "Feedback", "Thumbs-down regenerates with an alternate SQL path"),
    ]
    for i, (letter, title, body) in enumerate(flow):
        y = 1.7 + i * 0.82
        badge = oval(s, Inches(0.65), Inches(y + 0.08), Inches(0.55), Inches(0.55), NAVY if i % 2 == 0 else CYAN)
        textbox(s, Inches(0.65), Inches(y + 0.15), Inches(0.55), Inches(0.45),
                [{"t": letter, "s": 14, "b": True, "c": WHITE if i % 2 == 0 else NAVY, "a": PP_ALIGN.CENTER, "sa": 0}])
        row = round_rect(s, Inches(1.45), Inches(y), Inches(11.25), Inches(0.7), WHITE, LINE, 0.1)
        textbox(s, Inches(1.7), Inches(y + 0.12), Inches(10.8), Inches(0.5),
                [{"t": f"{title}    —    {body}", "s": 14, "b": False, "c": NAVY, "sa": 0}])
    footer(s, 8)

    # ═══════════════════════════════════════
    # 9 · SAMPLE Q&A BALANCES
    # ═══════════════════════════════════════
    s = prs.slides.add_slide(layout)
    page_bg(s)
    header(s, "Evidence", "Sample Q&A — Balances", "Grounded in account.available_balance for bank_code = HDFC")

    q = round_rect(s, Inches(0.55), Inches(1.7), Inches(6.15), Inches(2.2), CYAN_SOFT, None, 0.08)
    textbox(s, Inches(0.85), Inches(1.9), Inches(5.6), Inches(1.8),
            [
                {"t": "QUESTION", "s": 10, "b": True, "c": CYAN, "sa": 6},
                {"t": "What's the balance for HDFC accounts?", "s": 16, "b": True, "c": NAVY, "sa": 10},
                {"t": "List each HDFC account (masked last-4) with balance; clarify if a single last-4 was intended.", "s": 12, "c": MUTED, "sa": 0},
            ])
    a = round_rect(s, Inches(6.9), Inches(1.7), Inches(5.85), Inches(2.2), WHITE, LINE, 0.08)
    textbox(s, Inches(7.2), Inches(1.9), Inches(5.3), Inches(1.8),
            [
                {"t": "SAMPLE ANSWER (SEED)", "s": 10, "b": True, "c": CYAN, "sa": 6},
                {"t": "XXXX9069  →  ₹ -2,59,07,487.00", "s": 13, "b": True, "c": NAVY, "sa": 3},
                {"t": "XXXX4137  →  ₹ -9,47,66,029.00", "s": 13, "b": True, "c": NAVY, "sa": 3},
                {"t": "XXXX3445  →  ₹ -13,16,29,423.33", "s": 13, "b": True, "c": NAVY, "sa": 6},
                {"t": "Combined ≈ ₹ -25.22 Cr  ·  negative = ledger / overdraft style", "s": 11, "c": MUTED, "sa": 0},
            ])
    shot_slot(s, Inches(0.55), Inches(4.15), Inches(12.2), Inches(2.55),
              "Chat UI — HDFC balance question, answer, and evidence dropdown")
    footer(s, 9)

    # ═══════════════════════════════════════
    # 10 · SAMPLE REF
    # ═══════════════════════════════════════
    s = prs.slides.add_slide(layout)
    page_bg(s)
    header(s, "Evidence", "Sample Q&A — Reference lookup", "Search transaction_reference_id (plaintext)")

    q = round_rect(s, Inches(0.55), Inches(1.7), Inches(6.15), Inches(2.15), CYAN_SOFT, None, 0.08)
    textbox(s, Inches(0.85), Inches(1.9), Inches(5.6), Inches(1.7),
            [
                {"t": "QUESTION", "s": 10, "b": True, "c": CYAN, "sa": 6},
                {"t": "Find transaction with ref\nHDFCH01078329532", "s": 16, "b": True, "c": NAVY, "sa": 8},
                {"t": "Tool: run_sql_query on \"transaction\"", "s": 12, "c": MUTED, "sa": 0},
            ])
    a = round_rect(s, Inches(6.9), Inches(1.7), Inches(5.85), Inches(2.15), WHITE, LINE, 0.08)
    textbox(s, Inches(7.2), Inches(1.9), Inches(5.3), Inches(1.7),
            [
                {"t": "SAMPLE ANSWER", "s": 10, "b": True, "c": CYAN, "sa": 6},
                {"t": "1 debit · 24 Jun 2026 · ₹7,959.00", "s": 15, "b": True, "c": NAVY, "sa": 8},
                {"t": "Narration: NEFT … UMANG SELECTION…", "s": 12, "c": BODY, "sa": 4},
                {"t": "UTR on file (masked in the reply)", "s": 12, "c": MUTED, "sa": 0},
            ])
    shot_slot(s, Inches(0.55), Inches(4.1), Inches(12.2), Inches(2.6),
              "Chat UI — reference hit with View evidence & SQL expanded")
    footer(s, 10)

    # ═══════════════════════════════════════
    # 11 · SAMPLE UNRECONCILED / MOM
    # ═══════════════════════════════════════
    s = prs.slides.add_slide(layout)
    page_bg(s)
    header(s, "Evidence", "Sample Q&A — Exceptions & spend math", "Unreconciled ≈ UTR IS NULL  ·  MoM via SQL LAG")

    left = round_rect(s, Inches(0.55), Inches(1.7), Inches(6.15), Inches(2.2), WHITE, LINE, 0.08)
    textbox(s, Inches(0.85), Inches(1.9), Inches(5.6), Inches(1.8),
            [
                {"t": "Q  ·  Which transactions are still unreconciled?", "s": 12, "b": True, "c": NAVY, "sa": 8},
                {"t": "Rows with utr_number IS NULL — e.g. Paresh NEFT ₹9,241, Gautam IMPS ₹110, inbound credit ₹36,810. State clearly if no formal reconcile flag exists.", "s": 12, "c": MUTED, "sa": 0},
            ])
    right = round_rect(s, Inches(6.9), Inches(1.7), Inches(5.85), Inches(2.2), NAVY, None, 0.08)
    textbox(s, Inches(7.2), Inches(1.9), Inches(5.3), Inches(1.8),
            [
                {"t": "Q  ·  Debits by month with MoM change", "s": 12, "b": True, "c": CYAN, "sa": 8},
                {"t": "Monthly debit totals + MoM % from SQL; chart in UI; anomalies when spend ≫ median.", "s": 12, "c": RGBColor(0xCB, 0xD5, 0xE1), "sa": 8},
                {"t": "Seed debit spend ≈ ₹2,49,806.00", "s": 13, "b": True, "c": WHITE, "sa": 0},
            ])
    shot_slot(s, Inches(0.55), Inches(4.15), Inches(6.0), Inches(2.55), "Screenshot — unreconciled answer")
    shot_slot(s, Inches(6.75), Inches(4.15), Inches(6.0), Inches(2.55), "Screenshot — MoM chart + evidence")
    footer(s, 11)

    # ═══════════════════════════════════════
    # 12 · DASHBOARD SURFACE
    # ═══════════════════════════════════════
    s = prs.slides.add_slide(layout)
    page_bg(s)
    header(s, "Product", "Dashboard surface", "Paste your live TBX Finance workspace screenshot")
    shot_slot(s, Inches(0.55), Inches(1.7), Inches(12.2), Inches(5.0),
              "Full dashboard — metrics · spend by bank · top payees")
    footer(s, 12)

    # ═══════════════════════════════════════
    # 13 · CHAT SURFACE
    # ═══════════════════════════════════════
    s = prs.slides.add_slide(layout)
    page_bg(s)
    header(s, "Product", "TBX Insight chat", "Empty state and an active grounded conversation")
    shot_slot(s, Inches(0.55), Inches(1.7), Inches(6.0), Inches(5.0), "Empty state — hero + suggestions")
    shot_slot(s, Inches(6.75), Inches(1.7), Inches(6.0), Inches(5.0), "Active chat — answer · chips · evidence")
    footer(s, 13)

    # ═══════════════════════════════════════
    # 14 · CLOSE
    # ═══════════════════════════════════════
    s = prs.slides.add_slide(layout)
    rect(s, Inches(0), Inches(0), Inches(13.333), Inches(7.5), NAVY_DEEP)
    rect(s, Inches(0), Inches(0), Inches(0.22), Inches(7.5), CYAN)
    oval(s, Inches(-1), Inches(-1), Inches(3.5), Inches(3.5), RGBColor(0x0F, 0x2A, 0x4A))
    oval(s, Inches(11), Inches(5), Inches(3.5), Inches(3.5), RGBColor(0x0D, 0x28, 0x45))
    rect(s, Inches(0), Inches(7.15), Inches(13.333), Inches(0.08), CYAN)

    textbox(s, Inches(0.9), Inches(1.6), Inches(11), Inches(0.4),
            [{"t": "BUSINESS IMPACT", "s": 11, "b": True, "c": CYAN, "sa": 0}])
    textbox(s, Inches(0.9), Inches(2.15), Inches(11.2), Inches(2.4),
            [
                {"t": "Seconds to a trustworthy answer.", "s": 26, "b": True, "c": WHITE, "sa": 10},
                {"t": "Every figure is query-backed and exportable.", "s": 18, "c": RGBColor(0xCB, 0xD5, 0xE1), "sa": 8},
                {"t": "Small model + strong tools = efficient and accurate.", "s": 18, "c": RGBColor(0xCB, 0xD5, 0xE1), "sa": 0},
            ])
    textbox(s, Inches(0.9), Inches(5.0), Inches(11), Inches(1.2),
            [
                {"t": "Thank you", "s": 36, "b": True, "c": WHITE, "sa": 8},
                {"t": "TBX Insight  ·  TBX Finance  ·  Questions welcome", "s": 14, "c": CYAN, "sa": 0},
            ])

    target = OUT
    try:
        # Probe write access without corrupting a half-written pptx
        with open(OUT, "ab"):
            pass
    except PermissionError:
        target = OUT_ALT

    prs.save(target)
    print(f"Wrote {target}")
    if target == OUT_ALT:
        print("Note: close the open PPTX in PowerPoint/Cursor, then re-run to refresh the main filename.")


if __name__ == "__main__":
    build()
