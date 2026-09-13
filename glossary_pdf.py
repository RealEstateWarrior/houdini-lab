"""Build the glossary PDF — a Gemini Notebook source kept separate from the
experiment logs, so a term lookup doesn't get answered out of an experiment's
particular context.

Usage:
    python glossary_pdf.py glossary.json out/glossary.pdf
"""

import json
import os
import sys

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (KeepTogether, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

from report_pdf import _register_fonts

ACCENT = colors.HexColor("#2f6d86")
MUTED = colors.HexColor("#5c6470")
RULE = colors.HexColor("#c9cfd8")
TERM_BG = colors.HexColor("#f2f5f8")

CONTENT_W = A4[0] - 40 * mm


def _styles(font):
    return {
        "title": ParagraphStyle("t", fontName=font, fontSize=20, leading=26,
                                textColor=colors.HexColor("#1c2430"), spaceAfter=6),
        "intro": ParagraphStyle("i", fontName=font, fontSize=9.6, leading=15.5,
                                textColor=colors.HexColor("#232a33"), spaceAfter=4),
        "cat": ParagraphStyle("c", fontName=font, fontSize=13, leading=18,
                              textColor=ACCENT, spaceBefore=16, spaceAfter=3),
        "note": ParagraphStyle("n", fontName=font, fontSize=8.8, leading=13.5,
                               textColor=MUTED, spaceAfter=8),
        "term": ParagraphStyle("tm", fontName=font, fontSize=10, leading=14,
                               textColor=colors.HexColor("#16202c")),
        "reading": ParagraphStyle("r", fontName=font, fontSize=8, leading=12,
                                  textColor=MUTED),
        "def": ParagraphStyle("d", fontName=font, fontSize=9.2, leading=14.5,
                              textColor=colors.HexColor("#232a33")),
        "rel": ParagraphStyle("rl", fontName=font, fontSize=8, leading=12,
                              textColor=MUTED, spaceBefore=2),
    }


def _term_block(entry, styles):
    head = entry["term"]
    if entry.get("expand"):
        head += f'　<font size="8" color="#5c6470">{entry["expand"]}</font>'

    left = [Paragraph(head, styles["term"])]
    if entry.get("reading"):
        left.append(Paragraph(f'［{entry["reading"]}］', styles["reading"]))

    right = [Paragraph(entry["def"], styles["def"])]
    if entry.get("related"):
        right.append(Paragraph(f'関連: {entry["related"]}', styles["rel"]))

    table = Table([[left, right]], colWidths=[52 * mm, CONTENT_W - 52 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), TERM_BG),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.25, RULE),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return KeepTogether(table)


def build(data, out_pdf):
    font = _register_fonts()
    styles = _styles(font)

    flow = [Paragraph(data["title"], styles["title"]),
            Paragraph(data["intro"], styles["intro"])]

    for cat in data["categories"]:
        flow.append(Paragraph(cat["label"], styles["cat"]))
        if cat.get("note"):
            flow.append(Paragraph(cat["note"], styles["note"]))
        for entry in cat["terms"]:
            flow.append(_term_block(entry, styles))

    flow.append(Spacer(1, 10 * mm))

    doc = SimpleDocTemplate(
        out_pdf, pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=18 * mm, bottomMargin=18 * mm,
        title=data["title"], author="Houdini 実験室",
    )
    doc.build(flow)
    return out_pdf


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 1
    with open(sys.argv[1], encoding="utf-8") as fp:
        data = json.load(fp)
    os.makedirs(os.path.dirname(os.path.abspath(sys.argv[2])), exist_ok=True)
    print(build(data, sys.argv[2]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
