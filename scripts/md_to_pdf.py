#!/usr/bin/env python3
"""Конвертер Markdown -> PDF з підтримкою кирилиці (Arial, вбудований TTF).

Використання:
    python3 scripts/md_to_pdf.py docs/файл1.md docs/файл2.md ...

Кожен .md конвертується у .pdf поруч із оригіналом.
"""
import html
import re
import sys
from pathlib import Path

from markdown_it import MarkdownIt
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

FONT_DIR = Path("/System/Library/Fonts/Supplemental")
FONT_REGULAR = "Arial"
FONT_BOLD = "Arial-Bold"
FONT_ITALIC = "Arial-Italic"


def register_fonts() -> None:
    pdfmetrics.registerFont(TTFont(FONT_REGULAR, str(FONT_DIR / "Arial.ttf")))
    pdfmetrics.registerFont(TTFont(FONT_BOLD, str(FONT_DIR / "Arial Bold.ttf")))
    pdfmetrics.registerFont(TTFont(FONT_ITALIC, str(FONT_DIR / "Arial Italic.ttf")))


def build_styles():
    styles = getSampleStyleSheet()
    base = dict(fontName=FONT_REGULAR, alignment=TA_LEFT, leading=14)
    custom = {
        "Body": ParagraphStyle("Body", parent=styles["Normal"], fontSize=10, spaceAfter=6, **base),
        "H1": ParagraphStyle(
            "H1", parent=styles["Heading1"], fontName=FONT_BOLD, fontSize=18,
            spaceBefore=4, spaceAfter=10, textColor=colors.HexColor("#1a1a1a"),
        ),
        "H2": ParagraphStyle(
            "H2", parent=styles["Heading2"], fontName=FONT_BOLD, fontSize=14,
            spaceBefore=14, spaceAfter=8, textColor=colors.HexColor("#1a1a1a"),
        ),
        "H3": ParagraphStyle(
            "H3", parent=styles["Heading3"], fontName=FONT_BOLD, fontSize=12,
            spaceBefore=10, spaceAfter=6, textColor=colors.HexColor("#1a1a1a"),
        ),
        "H4": ParagraphStyle(
            "H4", parent=styles["Heading4"], fontName=FONT_BOLD, fontSize=11,
            spaceBefore=8, spaceAfter=4,
        ),
        "ListItem": ParagraphStyle("ListItem", parent=styles["Normal"], fontSize=10, leading=14, fontName=FONT_REGULAR),
        "TableCell": ParagraphStyle("TableCell", parent=styles["Normal"], fontSize=9, leading=12, fontName=FONT_REGULAR),
        "TableHeader": ParagraphStyle("TableHeader", parent=styles["Normal"], fontSize=9, leading=12, fontName=FONT_BOLD, textColor=colors.white),
        "Quote": ParagraphStyle("Quote", parent=styles["Normal"], fontSize=10, leading=14, fontName=FONT_ITALIC, leftIndent=12, textColor=colors.HexColor("#444444")),
    }
    return custom


def inline_to_markup(tokens) -> str:
    """Перетворює inline-токени markdown-it на reportlab mini-markup рядок."""
    out = []
    for t in tokens:
        if t.type == "text":
            out.append(html.escape(t.content))
        elif t.type == "code_inline":
            # Base14 Courier не має кирилиці (застосований шрифт має підтримувати uk/ru).
            out.append(
                f'<font face="{FONT_REGULAR}" size="9" color="#8a2b06">{html.escape(t.content)}</font>'
            )
        elif t.type == "strong_open":
            out.append("<b>")
        elif t.type == "strong_close":
            out.append("</b>")
        elif t.type == "em_open":
            out.append("<i>")
        elif t.type == "em_close":
            out.append("</i>")
        elif t.type == "link_open":
            href = dict(t.attrs).get("href", "")
            out.append(f'<link href="{html.escape(href)}" color="blue">')
        elif t.type == "link_close":
            out.append("</link>")
        elif t.type == "softbreak":
            out.append(" ")
        elif t.type == "hardbreak":
            out.append("<br/>")
        elif t.type == "image":
            alt = t.content or ""
            out.append(html.escape(alt))
    return "".join(out)


def render_table(token_stream, i, styles):
    """token_stream[i] == 'table_open'. Повертає (Table flowable, новий i)."""
    rows = []
    header_row_idx = None
    i += 1
    in_header = False
    while token_stream[i].type != "table_close":
        tok = token_stream[i]
        if tok.type == "thead_open":
            in_header = True
        elif tok.type == "thead_close":
            in_header = False
        elif tok.type == "tr_open":
            row = []
            i += 1
            while token_stream[i].type != "tr_close":
                if token_stream[i].type in ("th_open", "td_open"):
                    i += 1
                    inline_tok = token_stream[i]
                    text = inline_to_markup(inline_tok.children or [])
                    style = styles["TableHeader"] if in_header else styles["TableCell"]
                    row.append(Paragraph(text, style))
                    i += 1  # inline
                    i += 1  # close tag
                    continue
                i += 1
            rows.append(row)
            if in_header:
                header_row_idx = len(rows) - 1
        i += 1
    table = Table(rows, hAlign="LEFT", repeatRows=1 if header_row_idx is not None else 0)
    style_cmds = [
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if header_row_idx is not None:
        style_cmds.append(("BACKGROUND", (0, header_row_idx), (-1, header_row_idx), colors.HexColor("#2f5233")))
    table.setStyle(TableStyle(style_cmds))
    return table, i


def render_list(token_stream, i, styles, ordered):
    """token_stream[i] == 'bullet_list_open' / 'ordered_list_open'."""
    close_type = "ordered_list_close" if ordered else "bullet_list_close"
    items = []
    i += 1
    while token_stream[i].type != close_type:
        if token_stream[i].type == "list_item_open":
            i += 1
            parts = []
            while token_stream[i].type != "list_item_close":
                tok = token_stream[i]
                if tok.type == "paragraph_open":
                    i += 1
                    text = inline_to_markup(token_stream[i].children or [])
                    parts.append(Paragraph(text, styles["ListItem"]))
                    i += 1  # inline
                    i += 1  # paragraph_close
                    continue
                if tok.type == "bullet_list_open":
                    sub, i = render_list(token_stream, i, styles, ordered=False)
                    parts.append(sub)
                    continue
                if tok.type == "ordered_list_open":
                    sub, i = render_list(token_stream, i, styles, ordered=True)
                    parts.append(sub)
                    continue
                i += 1
            items.append(ListItem(parts if len(parts) > 1 else parts[0], leftIndent=10))
        i += 1
    bullet_type = "1" if ordered else "bullet"
    flow = ListFlowable(items, bulletType=bullet_type, start=1 if ordered else None, leftIndent=14, bulletFontName=FONT_REGULAR, bulletFontSize=9)
    return flow, i


def convert(md_path: Path, styles) -> list:
    md = MarkdownIt("commonmark", {"html": False}).enable("table")
    text = md_path.read_text(encoding="utf-8")
    tokens = md.parse(text)

    story = []
    i = 0
    n = len(tokens)
    while i < n:
        tok = tokens[i]
        if tok.type == "heading_open":
            level = tok.tag  # h1..h4
            i += 1
            inline_text = inline_to_markup(tokens[i].children or [])
            style_key = {"h1": "H1", "h2": "H2", "h3": "H3"}.get(level, "H4")
            story.append(Paragraph(inline_text, styles[style_key]))
            i += 1  # inline
            i += 1  # heading_close
            continue
        if tok.type == "paragraph_open":
            i += 1
            inline_text = inline_to_markup(tokens[i].children or [])
            if inline_text.strip():
                story.append(Paragraph(inline_text, styles["Body"]))
            i += 1  # inline
            i += 1  # paragraph_close
            continue
        if tok.type == "bullet_list_open":
            flow, i = render_list(tokens, i, styles, ordered=False)
            story.append(flow)
            story.append(Spacer(1, 6))
            continue
        if tok.type == "ordered_list_open":
            flow, i = render_list(tokens, i, styles, ordered=True)
            story.append(flow)
            story.append(Spacer(1, 6))
            continue
        if tok.type == "table_open":
            table, i = render_table(tokens, i, styles)
            story.append(table)
            story.append(Spacer(1, 10))
            continue
        if tok.type == "hr":
            story.append(Spacer(1, 4))
            story.append(HRFlowable(width="100%", color=colors.HexColor("#cccccc"), thickness=0.75))
            story.append(Spacer(1, 8))
            i += 1
            continue
        if tok.type == "blockquote_open":
            i += 1
            while tokens[i].type != "blockquote_close":
                if tokens[i].type == "paragraph_open":
                    i += 1
                    inline_text = inline_to_markup(tokens[i].children or [])
                    story.append(Paragraph(inline_text, styles["Quote"]))
                    i += 1
                    i += 1
                    continue
                i += 1
            i += 1  # blockquote_close
            continue
        i += 1
    return story


def convert_file(md_path: Path) -> Path:
    styles = build_styles()
    story = convert(md_path, styles)
    pdf_path = md_path.with_suffix(".pdf")
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=md_path.stem,
    )
    doc.build(story)
    return pdf_path


def main(argv: list) -> int:
    if not argv:
        print("Використання: python3 md_to_pdf.py файл1.md [файл2.md ...]")
        return 1
    register_fonts()
    for arg in argv:
        md_path = Path(arg).resolve()
        if not md_path.exists():
            print(f"Пропущено (не знайдено): {md_path}")
            continue
        pdf_path = convert_file(md_path)
        print(f"OK: {pdf_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
