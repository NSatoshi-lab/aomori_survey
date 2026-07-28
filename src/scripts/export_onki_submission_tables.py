#!/usr/bin/env python3
"""Export manuscript Tables 1 and 2 as an English Excel workbook."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter


ITEM_LABELS = {
    "年齢": "Age",
    "住宅種別": "Housing type",
    "築年帯": "Building age",
    "所有形態": "Tenure",
    "浴室窓": "Bathroom window",
    "浴室暖房乾燥機": "Bathroom heater-dryer",
    "セントラル暖房": "Central heating",
    "寒さ体感": "Perceived coldness",
}

CATEGORY_LABELS = {
    "18-49歳": "18-49 years",
    "50-59歳": "50-59 years",
    "60-69歳": "60-69 years",
    "70歳以上": "≥70 years",
    "一戸建て": "Detached house",
    "集合住宅": "Apartment/condominium",
    "30年未満": "<30 years",
    "30年以上": "≥30 years",
    "不明": "Unknown",
    "持家": "Owner-occupied",
    "賃貸": "Rented",
    "無回答": "Missing",
    "二重サッシ・複層ガラス": "Double window/double glazing",
    "単板ガラス": "Single glazing",
    "窓なし": "No window",
    "不明・無回答": "Unknown/missing",
    "設置して使用": "Installed and used",
    "設置しているが未使用": "Installed but not used",
    "未設置": "Not installed",
    "24時間使用": "Used 24 hours",
    "時間限定使用": "Used for limited hours",
    "不使用": "Not used",
    "浴室寒さ5-7": "Bathroom score 5-7",
    "脱衣所寒さ5-7": "Dressing-room score 5-7",
}

EQUIPMENT_LABELS = {
    "浴室暖房乾燥機使用": "Bathroom heater-dryer use",
    "浴室暖房乾燥機設置": "Bathroom heater-dryer installation",
    "セントラル暖房使用": "Central heating use",
}

OUTCOME_LABELS = {
    "浴室寒さ5-7": "Bathroom",
    "脱衣所寒さ5-7": "Dressing room",
}

GROUP_LABELS = {
    "bath_heater_use": ("Not used", "Used"),
    "bath_heater_installed": ("Not installed", "Installed"),
    "central_heating": ("Not used", "Used"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("analysis_dir", type=Path)
    parser.add_argument("output_xlsx", type=Path)
    return parser.parse_args()


def format_ci(low: float, high: float) -> str:
    return f"[{low:.1f}, {high:.1f}]"


def build_table1(table1: pd.DataFrame) -> pd.DataFrame:
    output = pd.DataFrame(
        {
            "Item": table1["item"].map(ITEM_LABELS),
            "Category": table1["category"].map(CATEGORY_LABELS),
            "n/N (%)": table1.apply(
                lambda row: (
                    f"{int(row['event_n'])}/{int(row['denominator'])} "
                    f"({row['pct']:.1f})"
                ),
                axis=1,
            ),
            "95% CI": table1.apply(
                lambda row: format_ci(
                    row["ci95_lo_pct"],
                    row["ci95_hi_pct"],
                ),
                axis=1,
            ),
        }
    )
    if output[["Item", "Category"]].isna().any().any():
        raise ValueError("Unmapped Table 1 label")
    return output


def build_table2(table2: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in table2.itertuples(index=False):
        comparison_label, equipment_label = GROUP_LABELS[row.equipment_key]
        rows.append(
            {
                "Equipment classification": EQUIPMENT_LABELS[row.equipment_label],
                "Area": OUTCOME_LABELS[row.outcome_label],
                "Comparison group n/N (%; 95% CI)": (
                    f"{comparison_label} "
                    f"{int(row.without_event_n)}/{int(row.without_denominator)} "
                    f"({row.without_pct:.1f}; "
                    f"{format_ci(row.without_ci95_lo_pct, row.without_ci95_hi_pct)})"
                ),
                "Equipment group n/N (%; 95% CI)": (
                    f"{equipment_label} "
                    f"{int(row.with_event_n)}/{int(row.with_denominator)} "
                    f"({row.with_pct:.1f}; "
                    f"{format_ci(row.with_ci95_lo_pct, row.with_ci95_hi_pct)})"
                ),
                "Difference (pp; 95% CI)": (
                    f"{row.difference_pp:.1f} "
                    f"{format_ci(row.difference_ci95_lo_pp, row.difference_ci95_hi_pp)}"
                ),
            }
        )
    return pd.DataFrame(rows)


def style_workbook(output_xlsx: Path) -> None:
    from openpyxl import load_workbook

    workbook = load_workbook(output_xlsx)
    for sheet in workbook.worksheets:
        sheet.freeze_panes = "A2"
        for cell in sheet[1]:
            cell.font = Font(bold=True)
            cell.alignment = Alignment(wrap_text=True, vertical="center")
        for row in sheet.iter_rows(min_row=2):
            for cell in row:
                cell.alignment = Alignment(wrap_text=True, vertical="top")
        for column_index, column in enumerate(sheet.columns, start=1):
            max_length = max(len(str(cell.value or "")) for cell in column)
            sheet.column_dimensions[get_column_letter(column_index)].width = min(
                max(max_length + 2, 12),
                42,
            )
    workbook.save(output_xlsx)


def main() -> None:
    args = parse_args()
    analysis_dir = args.analysis_dir.resolve()
    output_xlsx = args.output_xlsx.resolve()
    table1 = pd.read_csv(analysis_dir / "table1_characteristics.csv")
    table2 = pd.read_csv(analysis_dir / "table2_equipment_and_cold.csv")
    output_xlsx.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_xlsx, engine="openpyxl") as writer:
        build_table1(table1).to_excel(writer, sheet_name="Table 1", index=False)
        build_table2(table2).to_excel(writer, sheet_name="Table 2", index=False)
        captions = pd.DataFrame(
            {
                "Figure/Table": ["Table 1", "Table 2", "Fig. 1"],
                "English title": [
                    (
                        "Participant, Housing, Equipment, and Perceived "
                        "Coldness Characteristics"
                    ),
                    (
                        "Bathroom and Dressing-room Coldness Scores of 5-7 "
                        "by Heating Equipment Use or Installation"
                    ),
                    (
                        "Reasons for Non-use or Non-installation of Bathroom "
                        "Heater-Dryers by Perceived Bathroom Coldness"
                    ),
                ],
            }
        )
        captions.to_excel(writer, sheet_name="Captions", index=False)
    style_workbook(output_xlsx)
    print(output_xlsx)


if __name__ == "__main__":
    main()
