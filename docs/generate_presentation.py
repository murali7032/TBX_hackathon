"""Generate TBX Finance hackathon presentation deck."""
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import nsmap
from pptx.oxml import parse_xml
from pptx.util import Inches, Pt, Emu

OUT = Path(__file__).resolve().parent / "TBX_Insight_Hackathon_Presentation.pptx"

NAVY = RGBColor(0x0B, 0x1F, 0x3A)
CYAN = RGBColor(0x00, 0xAE, 0xEF)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
SLATE = RGBColor(0x33, 0x41, 0x55)
MUTED = RGBColor(0x64, 0x74, 0x8B)
LIGHT = RGBColor(0xF5, 0xF7, 0xFA)
CARD = RGBColor(0xFF, 0xFF, 0xFF)
BORDER = RGBColor(0xE2, 0xE8, 0xF0)
SOFT = RGBColor(0xE6, 0xF7, 0xFD)


def set_run(run, size=14, bold=False, color=SLATE, font="Montserrat"):
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color


def add_text(tf, text, size=14, bold=False, color=SLATE, align=PP_ALIGN.LEFT, space_after=6):
    p = tf.paragraphs[0] if not tf.paragraphs[0].text else tf.add_paragraph()
    if not tf.paragraphs[0].text and len(tf.paragraphs) == 1:
        p = tf.paragraphs[0]
    p.text = text
    p.alignment = align
    p.space_after = Pt(space_after)
    for r in p.runs:
        set_run(r, size=size, bold=bold, color=color)
    return p


def write_box(shape, lines, default_size=13):
    """lines: list of (text, size, bold, color) or plain str."""
    tf = shape.text_frame
    tf.clear()
    tf.word_wrap = True
    first = True
    for item in lines:
        if isinstance(item, str):
            text, size, bold, color = item, default_size, False, SLATE
        else:
            text, size, bold, color = item
        if first:
            p = tf.paragraphs[0]
            first = False
        else:
            p = tf.add_paragraph()
        p.text = text
        p.space_after = Pt(4)
        for r in p.runs:
            set_run(r, size=size, bold=bold, color=color)


def fill(shape, color):
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()


def card(slide, left, top, width, height, fill_color=CARD, line_color=BORDER):
    s = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    fill(s, fill_color)
    s.line.color.rgb = line_color
    s.line.width = Pt(1)
    try:
        s.adjustments[0] = 0.08
    except Exception:
        pass
    return s


def banner(slide, title, subtitle=None):
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(1.05))
    fill(bar, NAVY)
    accent = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(1.05), Inches(13.333), Inches(0.08))
    fill(accent, CYAN)

    tb = slide.shapes.add_textbox(Inches(0.55), Inches(0.22), Inches(10.5), Inches(0.7))
    tf = tb.text_frame
    tf.clear()
    p = tf.paragraphs[0]
    p.text = title
    set_run(p.runs[0], size=26, bold=True, color=WHITE)
    if subtitle:
        sub = slide.shapes.add_textbox(Inches(0.55), Inches(1.25), Inches(12), Inches(0.4))
        stf = sub.text_frame
        stf.clear()
        sp = stf.paragraphs[0]
        sp.text = subtitle
        set_run(sp.runs[0], size=13, bold=False, color=MUTED)


def footer(slide, page, total=14):
    tb = slide.shapes.add_textbox(Inches(0.55), Inches(7.15), Inches(10), Inches(0.3))
    tf = tb.text_frame
    tf.clear()
    p = tf.paragraphs[0]
    p.text = "TBX Insight  ·  TBX Finance  ·  BVP Tech Catalyst Hackathon"
    set_run(p.runs[0], size=10, color=MUTED)
    nb = slide.shapes.add_textbox(Inches(11.6), Inches(7.15), Inches(1.2), Inches(0.3))
    ntf = nb.text_frame
    ntf.clear()
    np = ntf.paragraphs[0]
    np.text = f"{page} / {total}"
    np.alignment = PP_ALIGN.RIGHT
    set_run(np.runs[0], size=10, color=MUTED)


def screenshot_slot(slide, left, top, width, height, label="Paste demo screenshot here"):
    s = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    fill(s, LIGHT)
    s.line.color.rgb = CYAN
    s.line.width = Pt(1.5)
    # dashed look via caption
    tf = s.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER
    p = tf.paragraphs[0]
    p.text = "📷  SCREENSHOT PLACEHOLDER"
    set_run(p.runs[0], size=14, bold=True, color=NAVY)
    p2 = tf.add_paragraph()
    p2.text = label
    p2.alignment = PP_ALIGN.CENTER
    set_run(p2.runs[0], size=11, color=MUTED)
    p3 = tf.add_paragraph()
    p3.text = "(Insert image → crop to fit)"
    p3.alignment = PP_ALIGN.CENTER
    set_run(p3.runs[0], size=10, color=MUTED)
    return s


def blank_slide(prs):
    return prs.slide_layouts[6]  # blank


def build():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = blank_slide(prs)
    total = 14

    # —— 1 Title ——
    s = prs.slides.add_slide(blank)
    bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
    fill(bg, NAVY)
    stripe = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(0.18), Inches(7.5))
    fill(stripe, CYAN)
    t = s.shapes.add_textbox(Inches(0.9), Inches(1.8), Inches(11), Inches(1))
    tf = t.text_frame
    p = tf.paragraphs[0]
    p.text = "TBX INSIGHT"
    set_run(p.runs[0], size=44, bold=True, color=WHITE)
    t2 = s.shapes.add_textbox(Inches(0.9), Inches(2.7), Inches(11), Inches(1.2))
    tf2 = t2.text_frame
    p2 = tf2.paragraphs[0]
    p2.text = "A grounded finance assistant that answers\nfrom your ledger — never from guesses."
    set_run(p2.runs[0], size=22, bold=False, color=CYAN)
    t3 = s.shapes.add_textbox(Inches(0.9), Inches(4.3), Inches(11), Inches(1.2))
    tf3 = t3.text_frame
    write_box(
        t3,
        [
            ("TBX Finance  ·  BVP Tech Catalyst Hackathon", 14, True, WHITE),
            ("Problem: Build a Finance Assistant That Actually Understands You", 13, False, RGBColor(0xCB, 0xD5, 0xE1)),
            ("Stack: React · FastAPI · PostgreSQL · Google Gemini (Flash / Flash-Lite)", 12, False, RGBColor(0x94, 0xA3, 0xB8)),
        ],
    )

    # —— 2 Agenda ——
    s = prs.slides.add_slide(blank)
    banner(s, "Agenda", "What we will cover in this demo")
    items = [
        ("01", "The problem — why finance chatbots fail without grounding"),
        ("02", "Our approach — tools, SQL, evidence, and guardrails"),
        ("03", "Architecture — end-to-end system diagram"),
        ("04", "Model choice — lowest possible model, highest possible accuracy"),
        ("05", "Demo flow — how a question becomes a verified answer"),
        ("06", "Sample Q&A — grounded answers + screenshot slots"),
        ("07", "Impact & next steps"),
    ]
    for i, (num, text) in enumerate(items):
        y = 1.55 + i * 0.7
        c = card(s, Inches(0.7), Inches(y), Inches(11.9), Inches(0.58), SOFT if i % 2 == 0 else CARD)
        write_box(
            c,
            [(f"{num}    {text}", 15, True if i < 2 else False, NAVY)],
        )
    footer(s, 2, total)

    # —— 3 Problem ——
    s = prs.slides.add_slide(blank)
    banner(s, "The Problem", "Finance teams drown in lookup work — and invented numbers are a liability")
    left = card(s, Inches(0.55), Inches(1.55), Inches(6.0), Inches(5.1))
    write_box(
        left,
        [
            ("Today’s pain", 16, True, NAVY),
            ("", 6, False, MUTED),
            ("• Dashboards & exports for routine questions", 13, False, SLATE),
            ("• “What did we pay vendor X last month?” means", 13, False, SLATE),
            ("   hunting reports or pinging finance ops", 13, False, SLATE),
            ("• Same lookups, repeated — high-value work slips", 13, False, SLATE),
            ("", 8, False, MUTED),
            ("Why this is harder than a normal chatbot", 16, True, NAVY),
            ("", 6, False, MUTED),
            ("A wrong or invented figure is not a UX bug —", 13, False, SLATE),
            ("it undermines reconciliation, audits, and trust.", 13, True, CYAN),
        ],
    )
    right = card(s, Inches(6.8), Inches(1.55), Inches(5.9), Inches(5.1), NAVY)
    write_box(
        right,
        [
            ("Challenge", 16, True, CYAN),
            ("", 8, False, WHITE),
            ("Build a conversational assistant that:", 13, False, WHITE),
            ("", 6, False, WHITE),
            ("✓ Accepts plain-language finance questions", 13, False, WHITE),
            ("✓ Answers only from real ledger data", 13, False, WHITE),
            ("✓ Shows evidence users can verify", 13, False, WHITE),
            ("✓ Says “I don’t know” when data is missing", 13, False, WHITE),
            ("✓ Uses the smallest model that still works", 13, False, WHITE),
            ("", 10, False, WHITE),
            ("Scored heavily on Accuracy & Grounding (30%)", 12, True, CYAN),
            ("and Model Efficiency (20%).", 12, True, CYAN),
        ],
    )
    footer(s, 3, total)

    # —— 4 Approach ——
    s = prs.slides.add_slide(blank)
    banner(s, "Our Approach", "Compute in SQL · Explain in language · Never invent figures")
    pillars = [
        ("Grounded retrieval", "Every fact comes from PostgreSQL via read-only SELECT / WITH tools — not model memory."),
        ("Compute, then narrate", "Filters, joins, MoM %, anomalies run in SQL. The LLM explains results — it does not recalculate."),
        ("Verifiable answers", "Plain-language reply + evidence table + SQL (collapsible) + CSV/Excel export."),
        ("Guardrails", "Ambiguous account → clarification chips. Missing data → insufficient_data. Thumbs-down → retry different SQL."),
    ]
    for i, (title, body) in enumerate(pillars):
        col = i % 2
        row = i // 2
        x = 0.55 + col * 6.35
        y = 1.55 + row * 2.55
        c = card(s, Inches(x), Inches(y), Inches(6.05), Inches(2.3))
        write_box(
            c,
            [
                (f"{i+1:02d}  {title}", 16, True, NAVY),
                ("", 8, False, MUTED),
                (body, 13, False, SLATE),
            ],
        )
    footer(s, 4, total)

    # —— 5 Architecture ——
    s = prs.slides.add_slide(blank)
    banner(s, "Architecture", "TBX Insight — grounded tool-calling loop")

    boxes = [
        (0.45, 1.7, 2.5, 1.35, "User", "TBX Insight UI\nReact + Vite"),
        (3.3, 1.7, 2.7, 1.35, "API", "FastAPI\n/chat · /api · /export"),
        (6.4, 1.7, 3.0, 1.35, "Agent", "Gemini tool loop\n+ session memory"),
        (9.8, 1.7, 2.9, 1.35, "Data", "PostgreSQL\nbank · account · txn"),
    ]
    for x, y, w, h, title, body in boxes:
        c = card(s, Inches(x), Inches(y), Inches(w), Inches(h), NAVY)
        write_box(
            c,
            [
                (title, 12, True, CYAN),
                (body, 12, False, WHITE),
            ],
        )
    # arrows as text
    for x in [2.95, 6.0, 9.4]:
        a = s.shapes.add_textbox(Inches(x), Inches(2.15), Inches(0.4), Inches(0.4))
        tf = a.text_frame
        p = tf.paragraphs[0]
        p.text = "→"
        set_run(p.runs[0], size=20, bold=True, color=CYAN)

    tools = card(s, Inches(0.45), Inches(3.35), Inches(12.4), Inches(1.55))
    write_box(
        tools,
        [
            ("Tool belt (agent actions)", 14, True, NAVY),
            ("read_database_guide  ·  list_tables  ·  run_sql_query  ·  find_accounts  ·  analyze_debit_trends", 12, False, SLATE),
            ("Guardrails: read-only SQL · mask account # / UTR · quote \"transaction\" · no invented banks or balances", 12, False, MUTED),
        ],
    )

    outs = card(s, Inches(0.45), Inches(5.1), Inches(12.4), Inches(1.55), SOFT)
    write_box(
        outs,
        [
            ("Response contract", 14, True, NAVY),
            ("answer (markdown)  +  evidence {columns, rows, sql}  +  confidence  +  status  +  choices / insights", 12, False, SLATE),
            ("UX: clarification chips · MoM / anomaly callouts · collapsible evidence · thumbs-up/down retry · export", 12, False, SLATE),
        ],
    )
    footer(s, 5, total)

    # —— 6 Architecture detail diagram ——
    s = prs.slides.add_slide(blank)
    banner(s, "Architecture — Request Path", "From natural language to verified ledger answer")
    steps = [
        ("1. Ask", "User sends NL question\n+ optimize_for mode"),
        ("2. Ambiguity", "Multi-account bank/last4?\n→ clarification chips"),
        ("3. Plan", "LLM picks tools\nusing schema guide"),
        ("4. Query", "Read-only SQL on\nPostgres finance DB"),
        ("5. Verify", "Rows → evidence table\nSQL retained"),
        ("6. Answer", "Narrate only from\nrows; flag gaps"),
    ]
    for i, (t, b) in enumerate(steps):
        x = 0.4 + i * 2.15
        c = card(s, Inches(x), Inches(1.7), Inches(2.0), Inches(2.4))
        write_box(
            c,
            [
                (t, 14, True, CYAN if i % 2 == 0 else NAVY),
                ("", 6, False, MUTED),
                (b, 11, False, SLATE),
            ],
        )
    note = card(s, Inches(0.45), Inches(4.4), Inches(12.4), Inches(2.2), NAVY)
    write_box(
        note,
        [
            ("Data model (scoped)", 14, True, CYAN),
            ("bank (1)  ——<  account (many)  ——<  \"transaction\" (many)", 13, False, WHITE),
            ("Seed: 10 banks · 10 accounts · 10 transactions  |  Currency: single-company INR ledger", 12, False, RGBColor(0xCB, 0xD5, 0xE1)),
            ("Hosting: React UI → FastAPI → Gemini API → PostgreSQL 18 on EC2", 12, False, RGBColor(0x94, 0xA3, 0xB8)),
        ],
    )
    footer(s, 6, total)

    # —— 7 Model choice ——
    s = prs.slides.add_slide(blank)
    banner(s, "Model Choice Rationale", "Constraint: lowest possible model, highest possible accuracy (≤20B)")
    left = card(s, Inches(0.55), Inches(1.55), Inches(6.1), Inches(5.1))
    write_box(
        left,
        [
            ("What we chose", 16, True, NAVY),
            ("", 6, False, MUTED),
            ("Primary: Gemini 3.5 Flash", 14, True, CYAN),
            ("Balanced / Precision modes — strong tool use,", 12, False, SLATE),
            ("schema following, and multi-turn coherence.", 12, False, SLATE),
            ("", 8, False, MUTED),
            ("Efficiency: Gemini 3.5 Flash-Lite", 14, True, CYAN),
            ("Cost / Efficient mode — same tool loop,", 12, False, SLATE),
            ("lower latency & token cost for routine lookups.", 12, False, SLATE),
            ("", 8, False, MUTED),
            ("Why not a frontier giant?", 14, True, NAVY),
            ("Judged on efficiency. Accuracy comes from SQL", 12, False, SLATE),
            ("grounding — not from a larger parametric brain.", 12, False, SLATE),
        ],
    )
    right = card(s, Inches(6.9), Inches(1.55), Inches(5.8), Inches(5.1), SOFT)
    write_box(
        right,
        [
            ("How we keep a small model accurate", 15, True, NAVY),
            ("", 6, False, MUTED),
            ("1. Schema + LLM_TOOL_GUIDE injected as tools", 12, False, SLATE),
            ("2. Hard rules: never invent; mask PII; read-only", 12, False, SLATE),
            ("3. Aggregations in SQL (MoM via LAG, anomalies)", 12, False, SLATE),
            ("4. Synthesis pass if tool budget exhausts", 12, False, SLATE),
            ("5. User feedback → regenerate with new SQL", 12, False, SLATE),
            ("", 10, False, MUTED),
            ("Optimize_for modes in UI", 13, True, NAVY),
            ("Efficient → flash-lite", 12, False, SLATE),
            ("Balanced / Precision → flash", 12, False, SLATE),
            ("", 8, False, MUTED),
            ("Result: lightweight NL layer + heavy lifting in DB", 12, True, CYAN),
        ],
    )
    footer(s, 7, total)

    # —— 8 Demo flow ——
    s = prs.slides.add_slide(blank)
    banner(s, "Demo Flow", "Suggested live walkthrough (5–7 minutes)")
    flow = [
        ("A", "Open Dashboard", "Show debit/credit totals, spend-by-bank, top payees — workspace context."),
        ("B", "Ask a balance question", "“What's the balance for HDFC accounts?” → clarification or summed balances + evidence."),
        ("C", "Lookup by reference", "“Find transaction with ref HDFCH01078329532” → exact row, amount, narration."),
        ("D", "Show the math", "Debits by month with MoM + chart; expand Evidence & SQL."),
        ("E", "Anomaly / unreconciled", "Flag spend spikes or NULL UTR rows; export CSV."),
        ("F", "Feedback loop", "Thumbs-down regenerates with alternate SQL path."),
    ]
    for i, (letter, title, body) in enumerate(flow):
        y = 1.5 + i * 0.85
        badge = card(s, Inches(0.55), Inches(y), Inches(0.7), Inches(0.7), NAVY)
        write_box(badge, [(letter, 18, True, CYAN)])
        box = card(s, Inches(1.45), Inches(y), Inches(11.2), Inches(0.7))
        write_box(
            box,
            [(f"{title}  —  {body}", 13, False, SLATE)],
        )
    footer(s, 8, total)

    # —— 9 Sample Q&A 1 ——
    s = prs.slides.add_slide(blank)
    banner(s, "Sample Q&A — Balances", "Grounded in account.available_balance for bank_code = HDFC")
    q = card(s, Inches(0.55), Inches(1.5), Inches(6.2), Inches(2.4), SOFT)
    write_box(
        q,
        [
            ("Question", 12, True, CYAN),
            ("What's the balance for HDFC accounts?", 15, True, NAVY),
            ("", 6, False, MUTED),
            ("Expected assistant behavior", 12, True, MUTED),
            ("List each HDFC account (masked last-4) with", 12, False, SLATE),
            ("available_balance; optionally sum. Offer chips", 12, False, SLATE),
            ("if user meant a single last-4.", 12, False, SLATE),
        ],
    )
    a = card(s, Inches(6.95), Inches(1.5), Inches(5.8), Inches(2.4))
    write_box(
        a,
        [
            ("Sample answer (from seed data)", 12, True, CYAN),
            ("HDFC has 3 accounts, e.g.:", 12, False, SLATE),
            ("XXXX9069 → ₹ -2,59,07,487.00", 12, True, NAVY),
            ("XXXX4137 → ₹ -9,47,66,029.00", 12, True, NAVY),
            ("XXXX3445 → ₹ -13,16,29,423.33", 12, True, NAVY),
            ("Combined ≈ ₹ -25,22,03,039.33", 12, True, NAVY),
            ("(negative = overdraft / ledger style)", 11, False, MUTED),
        ],
    )
    screenshot_slot(
        s,
        Inches(0.55),
        Inches(4.1),
        Inches(12.2),
        Inches(2.6),
        "Chat UI: HDFC balance question + answer + evidence dropdown",
    )
    footer(s, 9, total)

    # —— 10 Sample Q&A 2 ——
    s = prs.slides.add_slide(blank)
    banner(s, "Sample Q&A — Reference Lookup", "Search transaction_reference_id (plaintext)")
    q = card(s, Inches(0.55), Inches(1.5), Inches(6.2), Inches(2.35), SOFT)
    write_box(
        q,
        [
            ("Question", 12, True, CYAN),
            ("Find transaction with ref HDFCH01078329532", 14, True, NAVY),
            ("", 6, False, MUTED),
            ("Tool path: run_sql_query on \"transaction\"", 12, False, SLATE),
            ("WHERE transaction_reference_id = …", 12, False, SLATE),
        ],
    )
    a = card(s, Inches(6.95), Inches(1.5), Inches(5.8), Inches(2.35))
    write_box(
        a,
        [
            ("Sample answer", 12, True, CYAN),
            ("Found 1 debit on 24 Jun 2026", 13, True, NAVY),
            ("Amount: ₹7,959.00", 13, False, SLATE),
            ("Narration: NEFT … UMANG SELECTION…", 12, False, SLATE),
            ("Account linked; UTR on file (masked).", 12, False, SLATE),
        ],
    )
    screenshot_slot(
        s,
        Inches(0.55),
        Inches(4.05),
        Inches(12.2),
        Inches(2.65),
        "Chat UI: reference lookup result + View evidence & SQL expanded",
    )
    footer(s, 10, total)

    # —— 11 Sample Q&A 3 ——
    s = prs.slides.add_slide(blank)
    banner(s, "Sample Q&A — Reconciliation & Spend Math", "Unreconciled = UTR NULL · MoM via SQL LAG")
    left = card(s, Inches(0.55), Inches(1.5), Inches(6.2), Inches(2.5), SOFT)
    write_box(
        left,
        [
            ("Q: Which transactions are still unreconciled?", 13, True, NAVY),
            ("A: Rows with utr_number IS NULL — e.g. NEFT to", 12, False, SLATE),
            ("Paresh Vikrant Ghase (₹9,241), IMPS Gautam", 12, False, SLATE),
            ("Singh (₹110), and the inbound credit IMPS", 12, False, SLATE),
            ("SELECTIONMALIGAI (₹36,810). State clearly if", 12, False, SLATE),
            ("the dataset has no formal reconcile flag.", 12, False, MUTED),
        ],
    )
    right = card(s, Inches(6.95), Inches(1.5), Inches(5.8), Inches(2.5))
    write_box(
        right,
        [
            ("Q: Show me the math — debits by month + MoM", 13, True, NAVY),
            ("A: Monthly debit totals with MoM % from SQL;", 12, False, SLATE),
            ("chart in UI; anomaly months flagged when", 12, False, SLATE),
            ("spend ≫ median. Expand evidence for SQL.", 12, False, SLATE),
            ("Total seed debit spend ≈ ₹2,49,806.00", 12, True, CYAN),
        ],
    )
    screenshot_slot(
        s,
        Inches(0.55),
        Inches(4.2),
        Inches(6.0),
        Inches(2.5),
        "Screenshot: unreconciled answer",
    )
    screenshot_slot(
        s,
        Inches(6.75),
        Inches(4.2),
        Inches(6.0),
        Inches(2.5),
        "Screenshot: MoM chart + evidence",
    )
    footer(s, 11, total)

    # —— 12 Dashboard screenshot ——
    s = prs.slides.add_slide(blank)
    banner(s, "Product Surface — Dashboard", "TBX Finance workspace overview (paste live UI)")
    screenshot_slot(
        s,
        Inches(0.55),
        Inches(1.55),
        Inches(12.2),
        Inches(5.2),
        "Full-width Dashboard: metrics · spend by bank · top payees",
    )
    footer(s, 12, total)

    # —— 13 Chat screenshot ——
    s = prs.slides.add_slide(blank)
    banner(s, "Product Surface — TBX Insight Chat", "Empty state + conversation (paste live UI)")
    screenshot_slot(
        s,
        Inches(0.55),
        Inches(1.55),
        Inches(6.0),
        Inches(5.2),
        "Empty state: TBX Insight hero + suggestions",
    )
    screenshot_slot(
        s,
        Inches(6.75),
        Inches(1.55),
        Inches(6.0),
        Inches(5.2),
        "Active chat: answer · chips · evidence toggle",
    )
    footer(s, 13, total)

    # —— 14 Closing ——
    s = prs.slides.add_slide(blank)
    bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
    fill(bg, NAVY)
    stripe = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(0.18), Inches(7.5))
    fill(stripe, CYAN)
    t = s.shapes.add_textbox(Inches(0.9), Inches(1.5), Inches(11), Inches(1))
    p = t.text_frame.paragraphs[0]
    p.text = "Business impact"
    set_run(p.runs[0], size=28, bold=True, color=CYAN)
    body = s.shapes.add_textbox(Inches(0.9), Inches(2.3), Inches(11.2), Inches(3.2))
    write_box(
        body,
        [
            ("Seconds to a trustworthy answer — no dashboard hunt.", 16, False, WHITE),
            ("Every number is query-backed and exportable for audit.", 16, False, WHITE),
            ("Small model + strong tools = efficient and accurate.", 16, False, WHITE),
            ("", 12, False, WHITE),
            ("Thank you", 32, True, WHITE),
            ("TBX Insight  ·  TBX Finance  ·  Questions welcome", 14, False, CYAN),
        ],
    )

    prs.save(OUT)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    build()
