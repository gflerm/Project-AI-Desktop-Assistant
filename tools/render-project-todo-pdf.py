#!/usr/bin/env python3
"""Render the master Project TARS TODO Markdown as a polished PDF."""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    Flowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


INK = colors.HexColor("#172033")
MUTED = colors.HexColor("#657084")
NAVY = colors.HexColor("#193A5A")
BLUE = colors.HexColor("#1677A8")
CYAN = colors.HexColor("#40BBD1")
GREEN = colors.HexColor("#2F855A")
AMBER = colors.HexColor("#B7791F")
RED = colors.HexColor("#C2413A")
PAPER = colors.HexColor("#F6F8FB")
LINE = colors.HexColor("#D9E1EA")
WHITE = colors.white


def clean_text(value: str) -> str:
    """Normalize punctuation to glyphs available in every PDF viewer."""
    return (
        value.replace("\u2014", " - ")
        .replace("\u2013", "-")
        .replace("\u2011", "-")
        .replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2194", "<->")
        .replace("\u2192", "->")
        .replace("\u00a0", " ")
    )


def inline_markup(value: str) -> str:
    value = clean_text(value.strip())
    value = re.sub(r"\[([^]]+)\]\(([^)]+)\)", r"\1", value)
    value = html.escape(value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", value)
    value = re.sub(r"`([^`]+)`", r'<font name="TarsMono">\1</font>', value)
    return value


class CriticalPathDiagram(Flowable):
    """Vector flow diagram replacing the source Markdown ASCII diagram."""

    def __init__(self, width: float):
        super().__init__()
        self.width = width
        self.height = 104 * mm

    def _node(self, canvas: Canvas, x: float, y: float, w: float, h: float,
              goal: str, label: str, state: str = "pending") -> None:
        fills = {
            "ready": colors.HexColor("#FFF3D6"),
            "active": colors.HexColor("#DDF4E8"),
            "pending": colors.HexColor("#EAF0F6"),
        }
        strokes = {"ready": AMBER, "active": GREEN, "pending": colors.HexColor("#8FA2B5")}
        canvas.setFillColor(fills[state])
        canvas.setStrokeColor(strokes[state])
        canvas.setLineWidth(1.2)
        canvas.roundRect(x, y, w, h, 3 * mm, fill=1, stroke=1)
        canvas.setFillColor(strokes[state])
        canvas.setFont("TarsBold", 7.5)
        canvas.drawCentredString(x + w / 2, y + h - 10, goal)
        canvas.setFillColor(INK)
        canvas.setFont("TarsRegular", 6.5)
        words = label.split()
        lines, current = [], ""
        for word in words:
            candidate = (current + " " + word).strip()
            if canvas.stringWidth(candidate, "TarsRegular", 6.5) <= w - 8:
                current = candidate
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
        baseline = y + h / 2 + (len(lines) - 1) * 3.6 - 3
        for index, line in enumerate(lines[:2]):
            canvas.drawCentredString(x + w / 2, baseline - index * 7.2, line)

    @staticmethod
    def _arrow(canvas: Canvas, x1: float, y1: float, x2: float, y2: float) -> None:
        canvas.setStrokeColor(BLUE)
        canvas.setFillColor(BLUE)
        canvas.setLineWidth(1.2)
        canvas.line(x1, y1, x2, y2)
        angle_x = 5 if x2 >= x1 else -5
        canvas.line(x2, y2, x2 - angle_x, y2 + 3)
        canvas.line(x2, y2, x2 - angle_x, y2 - 3)

    def draw(self) -> None:
        canvas = self.canv
        canvas.saveState()
        canvas.setFillColor(PAPER)
        canvas.roundRect(0, 0, self.width, self.height, 4 * mm, fill=1, stroke=0)
        canvas.setFillColor(NAVY)
        canvas.setFont("TarsBold", 12)
        canvas.drawString(8 * mm, self.height - 13 * mm, "Critical path to full-system proof")
        canvas.setFillColor(MUTED)
        canvas.setFont("TarsRegular", 7)
        canvas.drawRightString(self.width - 8 * mm, self.height - 13 * mm,
                               "Green: active  |  Amber: ready  |  Grey: queued")

        margin = 7 * mm
        gap = 4 * mm
        node_w = (self.width - 2 * margin - 4 * gap) / 5
        node_h = 17 * mm
        xs = [margin + index * (node_w + gap) for index in range(5)]
        y_top, y_mid, y_bottom = 59 * mm, 36 * mm, 13 * mm

        nodes = {
            "G0": (xs[0], y_top, "PC corpus", "ready"),
            "G1": (xs[0], y_bottom, "P4 capture", "active"),
            "G3": (xs[1], y_top, "Offline VAD", "pending"),
            "G2": (xs[1], y_bottom, "Push-to-talk", "pending"),
            "G4": (xs[2], y_mid, "Endpointing", "active"),
            "G6": (xs[3], y_top, "AFE / VADNet", "pending"),
            "G5": (xs[3], y_bottom, "Pi streaming", "pending"),
            "G7": (xs[4], y_mid, "STT / enrollment", "pending"),
        }
        for goal, (x, y, label, state) in nodes.items():
            self._node(canvas, x, y, node_w, node_h, goal, label, state)

        def right(goal: str):
            x, y, _, _ = nodes[goal]
            return x + node_w, y + node_h / 2

        def left(goal: str):
            x, y, _, _ = nodes[goal]
            return x, y + node_h / 2

        for source, target in (("G0", "G3"), ("G1", "G2"), ("G3", "G4"),
                               ("G2", "G4"), ("G4", "G6"), ("G4", "G5"),
                               ("G6", "G7"), ("G5", "G7")):
            self._arrow(canvas, *right(source), *left(target))

        canvas.setStrokeColor(CYAN)
        canvas.setLineWidth(2)
        canvas.line(margin, 7 * mm, self.width - margin, 7 * mm)
        canvas.setFillColor(NAVY)
        canvas.setFont("TarsBold", 8)
        canvas.drawCentredString(self.width / 2, 3.5 * mm,
                                 "Then: G8 facial state integration -> G9 concurrent soak test")
        canvas.restoreState()


class TarsDocTemplate(SimpleDocTemplate):
    def __init__(self, filename: str, **kwargs):
        super().__init__(filename, **kwargs)
        self._section = "Project TODO and Verification"

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name == "H1":
            self._section = clean_text(flowable.getPlainText())


def register_fonts() -> None:
    fonts = Path("C:/Windows/Fonts")
    choices = {
        "TarsRegular": [fonts / "segoeui.ttf", fonts / "arial.ttf"],
        "TarsBold": [fonts / "segoeuib.ttf", fonts / "arialbd.ttf"],
        "TarsMono": [fonts / "consola.ttf", fonts / "cour.ttf"],
    }
    for name, candidates in choices.items():
        selected = next((path for path in candidates if path.exists()), None)
        if selected is None:
            raise FileNotFoundError(f"No suitable font found for {name}")
        pdfmetrics.registerFont(TTFont(name, str(selected)))


def styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("Title", parent=base["Title"], fontName="TarsBold",
                                fontSize=25, leading=29, textColor=NAVY,
                                alignment=TA_LEFT, spaceAfter=5 * mm),
        "subtitle": ParagraphStyle("Subtitle", parent=base["BodyText"],
                                   fontName="TarsRegular", fontSize=9.5,
                                   leading=14, textColor=MUTED, spaceAfter=3 * mm),
        "h1": ParagraphStyle("H1", parent=base["Heading1"], fontName="TarsBold",
                             fontSize=17, leading=21, textColor=NAVY,
                             spaceBefore=7 * mm, spaceAfter=3 * mm,
                             keepWithNext=True),
        "h2": ParagraphStyle("H2", parent=base["Heading2"], fontName="TarsBold",
                             fontSize=12.5, leading=16, textColor=BLUE,
                             spaceBefore=4 * mm, spaceAfter=2 * mm,
                             keepWithNext=True),
        "body": ParagraphStyle("Body", parent=base["BodyText"], fontName="TarsRegular",
                               fontSize=8.8, leading=13.2, textColor=INK,
                               spaceAfter=2.2 * mm),
        "small": ParagraphStyle("Small", parent=base["BodyText"], fontName="TarsRegular",
                                fontSize=7.4, leading=10, textColor=INK),
        "bullet": ParagraphStyle("Bullet", parent=base["BodyText"], fontName="TarsRegular",
                                 fontSize=8.6, leading=12.5, textColor=INK,
                                 leftIndent=5 * mm, firstLineIndent=-3 * mm,
                                 spaceAfter=1.2 * mm),
        "code": ParagraphStyle("Code", parent=base["Code"], fontName="TarsMono",
                               fontSize=7.4, leading=10, textColor=INK,
                               backColor=PAPER, borderColor=LINE, borderWidth=0.5,
                               borderPadding=7, spaceBefore=2 * mm, spaceAfter=3 * mm),
        "callout": ParagraphStyle("Callout", parent=base["BodyText"], fontName="TarsRegular",
                                  fontSize=8.3, leading=12, textColor=INK),
    }


def make_checkbox(text: str, done: bool, st) -> Table:
    label = "DONE" if done else "TODO"
    chip_color = GREEN if done else AMBER
    table = Table([
        [Paragraph(f'<font color="white"><b>{label}</b></font>', st["small"]),
         Paragraph(inline_markup(text), st["body"])]
    ], colWidths=[16 * mm, 155 * mm], hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), chip_color),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (0, 0), "CENTER"),
        ("LEFTPADDING", (0, 0), (0, 0), 3),
        ("RIGHTPADDING", (0, 0), (0, 0), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (1, 0), (1, 0), 7),
        ("LINEBELOW", (1, 0), (1, 0), 0.25, LINE),
    ]))
    return table


def make_markdown_table(rows: list[list[str]], st, width: float) -> Table:
    columns = max(len(row) for row in rows)
    normalized = [row + [""] * (columns - len(row)) for row in rows]
    data = [[Paragraph(inline_markup(cell), st["small"]) for cell in row] for row in normalized]
    if columns == 4:
        col_widths = [18 * mm, 58 * mm, 48 * mm, width - 124 * mm]
    elif columns == 3:
        col_widths = [width * 0.23, width * 0.25, width * 0.52]
    elif columns == 2:
        col_widths = [width * 0.30, width * 0.70]
    else:
        col_widths = [width / columns] * columns
    table = Table(data, colWidths=col_widths, repeatRows=1, hAlign="LEFT")
    commands = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "TarsBold"),
        ("GRID", (0, 0), (-1, -1), 0.35, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    for row_index in range(1, len(data)):
        if row_index % 2 == 0:
            commands.append(("BACKGROUND", (0, row_index), (-1, row_index), PAPER))
    table.setStyle(TableStyle(commands))
    return table


def page_decor(canvas: Canvas, doc: TarsDocTemplate) -> None:
    canvas.saveState()
    page_w, page_h = A4
    canvas.setFillColor(NAVY)
    canvas.rect(0, page_h - 10 * mm, page_w, 10 * mm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("TarsBold", 7.5)
    canvas.drawString(18 * mm, page_h - 6.4 * mm, "PROJECT TARS")
    canvas.setFont("TarsRegular", 7)
    canvas.drawRightString(page_w - 18 * mm, page_h - 6.4 * mm,
                           clean_text(doc._section)[:82])
    canvas.setStrokeColor(CYAN)
    canvas.setLineWidth(1.2)
    canvas.line(18 * mm, 12 * mm, page_w - 18 * mm, 12 * mm)
    canvas.setFillColor(MUTED)
    canvas.setFont("TarsRegular", 7)
    canvas.drawString(18 * mm, 7.5 * mm, "Master implementation, test and verification tracker")
    canvas.drawRightString(page_w - 18 * mm, 7.5 * mm, f"Page {doc.page}")
    canvas.restoreState()


def parse_markdown(source: Path, content_width: float):
    st = styles()
    lines = source.read_text(encoding="utf-8").splitlines()
    story = []
    paragraph_parts: list[str] = []
    index = 0
    first_heading = True

    def flush_paragraph():
        nonlocal paragraph_parts
        if paragraph_parts:
            text = " ".join(part.strip() for part in paragraph_parts)
            if text.startswith("**Evidence:**") or text.startswith("**Exit condition:**"):
                label, body = text.split(":**", 1)
                label = label.replace("**", "")
                body = body.strip()
                table = Table([[Paragraph(f"<b>{inline_markup(label)}</b>", st["callout"]),
                                Paragraph(inline_markup(body), st["callout"])]],
                              colWidths=[27 * mm, content_width - 27 * mm])
                table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EAF6F9")),
                    ("BOX", (0, 0), (-1, -1), 0.6, CYAN),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]))
                story.extend([table, Spacer(1, 2 * mm)])
            else:
                story.append(Paragraph(inline_markup(text), st["body"]))
            paragraph_parts = []

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            index += 1
            continue
        if stripped == "---":
            flush_paragraph()
            story.append(Spacer(1, 1.5 * mm))
            index += 1
            continue
        if stripped.startswith("```"):
            flush_paragraph()
            code_lines = []
            index += 1
            while index < len(lines) and not lines[index].strip().startswith("```"):
                code_lines.append(clean_text(lines[index]))
                index += 1
            index += 1
            code = "\n".join(code_lines)
            if "G0 PC corpus" in code:
                story.extend([CriticalPathDiagram(content_width), Spacer(1, 3 * mm)])
            else:
                story.append(Preformatted(code, st["code"], maxLineLength=94))
            continue
        heading = re.match(r"^(#{1,2})\s+(.+)$", stripped)
        if heading:
            flush_paragraph()
            level = len(heading.group(1))
            text = heading.group(2)
            if first_heading:
                story.append(Spacer(1, 10 * mm))
                story.append(Paragraph(inline_markup(text), st["title"]))
                story.append(Table([["PRIMARY PROJECT CONTROL DOCUMENT"]], colWidths=[73 * mm],
                                   style=TableStyle([
                                       ("BACKGROUND", (0, 0), (-1, -1), CYAN),
                                       ("TEXTCOLOR", (0, 0), (-1, -1), NAVY),
                                       ("FONTNAME", (0, 0), (-1, -1), "TarsBold"),
                                       ("FONTSIZE", (0, 0), (-1, -1), 8),
                                       ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                                       ("TOPPADDING", (0, 0), (-1, -1), 5),
                                       ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                                   ])))
                story.append(Spacer(1, 6 * mm))
                first_heading = False
            else:
                story.append(Paragraph(inline_markup(text), st["h1" if level == 1 else "h2"]))
            index += 1
            continue
        if stripped.startswith("|") and stripped.endswith("|"):
            flush_paragraph()
            rows = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                cells = [cell.strip() for cell in lines[index].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
                    rows.append(cells)
                index += 1
            story.extend([make_markdown_table(rows, st, content_width), Spacer(1, 3 * mm)])
            continue
        checkbox = re.match(r"^- \[([ xX])\]\s+(.+)$", stripped)
        if checkbox:
            flush_paragraph()
            text = checkbox.group(2)
            lookahead = index + 1
            while lookahead < len(lines):
                candidate = lines[lookahead]
                if not candidate.startswith("  ") or candidate.strip().startswith(("- ", "#", "|", "```")):
                    break
                text += " " + candidate.strip()
                lookahead += 1
            story.extend([make_checkbox(text, checkbox.group(1).lower() == "x", st), Spacer(1, 0.8 * mm)])
            index = lookahead
            continue
        bullet = re.match(r"^-\s+(.+)$", stripped)
        numbered = re.match(r"^(\d+)\.\s+(.+)$", stripped)
        if bullet or numbered:
            flush_paragraph()
            marker = "-" if bullet else numbered.group(1) + "."
            text = bullet.group(1) if bullet else numbered.group(2)
            story.append(Paragraph(f"<b>{marker}</b> {inline_markup(text)}", st["bullet"]))
            index += 1
            continue
        if stripped.startswith("**Status:**") or stripped.startswith("**Date:**") or stripped.startswith("**Owner:**"):
            flush_paragraph()
            story.append(Paragraph(inline_markup(stripped), st["subtitle"]))
            index += 1
            continue
        paragraph_parts.append(stripped)
        index += 1

    flush_paragraph()
    return story


def build_pdf(source: Path, output: Path) -> None:
    register_fonts()
    output.parent.mkdir(parents=True, exist_ok=True)
    doc = TarsDocTemplate(
        str(output), pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=18 * mm, bottomMargin=18 * mm,
        title="Project TARS - Project TODO and Verification",
        author="Project TARS",
        subject="Master implementation, testing and verification tracker",
    )
    story = parse_markdown(source, A4[0] - 36 * mm)
    doc.build(story, onFirstPage=page_decor, onLaterPages=page_decor)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path,
                        default=Path("docs/Project-TODO-and-Verification.md"))
    parser.add_argument("--output", type=Path,
                        default=Path("output/pdf/Project-TODO-and-Verification.pdf"))
    args = parser.parse_args()
    build_pdf(args.source.resolve(), args.output.resolve())
    print(args.output.resolve())


if __name__ == "__main__":
    main()
