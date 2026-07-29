#!/usr/bin/env python3
"""Apply ONKI manuscript page and paragraph settings to a Pandoc DOCX."""

from __future__ import annotations

import argparse
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm, Pt


BODY_FONT = "Yu Mincho"
LATIN_FONT = "Times New Roman"
FIGURE_SECTION_TITLES = ("Figure Legends", "Figures")
FIGURE_BODY_TITLES = ("Figure 1", "Figure 2", "Figure 3")
LEGEND_PAGE_BREAK_PREFIXES = ("Figure 2.", "Figure 3.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Format a Pandoc-generated manuscript DOCX as A4 with approximately "
            "35 Japanese characters per line and 32 lines per page."
        )
    )
    parser.add_argument("input_docx", type=Path)
    parser.add_argument("--output-docx", type=Path)
    return parser.parse_args()


def set_run_font(run, size: Pt) -> None:
    run.font.name = LATIN_FONT
    run.font.size = size
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), BODY_FONT)


def set_style_font(style, size: Pt) -> None:
    style.font.name = LATIN_FONT
    style.font.size = size
    style._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), BODY_FONT)


def mark_header_row(row) -> None:
    table_row_properties = row._tr.get_or_add_trPr()
    repeat = OxmlElement("w:tblHeader")
    repeat.set(qn("w:val"), "true")
    table_row_properties.append(repeat)


def prevent_row_split(row) -> None:
    table_row_properties = row._tr.get_or_add_trPr()
    cannot_split = OxmlElement("w:cantSplit")
    table_row_properties.append(cannot_split)


def format_document(input_docx: Path, output_docx: Path) -> None:
    document = Document(input_docx)

    for section in document.sections:
        section.page_width = Mm(210)
        section.page_height = Mm(297)
        section.top_margin = Mm(25)
        section.bottom_margin = Mm(25)
        section.left_margin = Mm(30)
        section.right_margin = Mm(30)

    styles = document.styles
    set_style_font(styles["Normal"], Pt(12))
    styles["Normal"].paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    styles["Normal"].paragraph_format.line_spacing = Pt(21.5)
    styles["Normal"].paragraph_format.space_after = Pt(0)

    heading_sizes = {
        "Title": Pt(15),
        "Heading 1": Pt(13),
        "Heading 2": Pt(12),
        "Heading 3": Pt(12),
    }
    for style_name, size in heading_sizes.items():
        if style_name in styles:
            set_style_font(styles[style_name], size)

    in_english_abstract = False
    for paragraph in document.paragraphs:
        paragraph_text = paragraph.text.strip()
        has_drawing = bool(paragraph._p.xpath(".//w:drawing"))
        if paragraph_text == "English Title":
            paragraph.paragraph_format.page_break_before = True
        elif paragraph_text in FIGURE_SECTION_TITLES:
            paragraph.paragraph_format.page_break_before = True
        elif paragraph_text in FIGURE_BODY_TITLES[1:]:
            paragraph.paragraph_format.page_break_before = True
        elif paragraph_text.startswith(LEGEND_PAGE_BREAK_PREFIXES):
            paragraph.paragraph_format.page_break_before = True
        if paragraph_text == "English Abstract":
            in_english_abstract = True
        elif in_english_abstract and paragraph_text in FIGURE_SECTION_TITLES:
            in_english_abstract = False

        if has_drawing:
            paragraph.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
            paragraph.paragraph_format.line_spacing = 1.0
        elif in_english_abstract and paragraph_text != "English Abstract":
            paragraph.paragraph_format.line_spacing_rule = WD_LINE_SPACING.DOUBLE
            paragraph.paragraph_format.line_spacing = 2.0
        elif paragraph.style.name == "Normal":
            paragraph.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
            paragraph.paragraph_format.line_spacing = Pt(21.5)

        for run in paragraph.runs:
            if paragraph.style.name == "Title":
                set_run_font(run, Pt(15))
            elif paragraph.style.name.startswith("Heading"):
                set_run_font(run, Pt(12))
            else:
                set_run_font(run, Pt(12))

    for table in document.tables:
        if table.rows:
            mark_header_row(table.rows[0])
        for row in table.rows:
            prevent_row_split(row)
            for cell in row.cells:
                cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                for paragraph in cell.paragraphs:
                    paragraph.paragraph_format.line_spacing_rule = (
                        WD_LINE_SPACING.SINGLE
                    )
                    paragraph.paragraph_format.space_after = Pt(0)
                    for run in paragraph.runs:
                        set_run_font(run, Pt(9))

    output_docx.parent.mkdir(parents=True, exist_ok=True)
    document.save(output_docx)


def main() -> None:
    args = parse_args()
    input_docx = args.input_docx.resolve()
    output_docx = (
        args.output_docx.resolve() if args.output_docx else input_docx
    )
    if not input_docx.exists():
        raise FileNotFoundError(input_docx)
    format_document(input_docx, output_docx)
    print(output_docx)


if __name__ == "__main__":
    main()
