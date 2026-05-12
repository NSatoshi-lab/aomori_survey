#!/usr/bin/env python3
"""Derive analysis-only fields from manually reviewed Aomori survey CSV."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RUN_DIR = REPO_ROOT / "outputs" / "runs" / "20260512_ocr_ingest_q6_q99_scoped_patch_full_dry_run"
DERIVED_COLUMNS = [
    "q7_bath_heater_status_analysis",
    "q7_q8_inconsistency_flag",
    "q7_analysis_note",
]
NOTE_RECODED = "q7=1_with_q8_reason_recoded_to_2_for_analysis"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Add Q7/Q8 interpretation fields to reviewed Aomori CSV."
    )
    parser.add_argument("--run-dir", default=str(DEFAULT_RUN_DIR), help="OCR run directory")
    parser.add_argument(
        "--input",
        help="Input reviewed CSV. Defaults to <run-dir>/aomori_survey_responses_reviewed_manual.csv",
    )
    parser.add_argument(
        "--output",
        help="Output CSV. Defaults to <run-dir>/aomori_survey_responses_reviewed_analysis.csv",
    )
    return parser.parse_args()


def read_csv(path: Path) -> pd.DataFrame:
    encodings = ["utf-8-sig", "utf-8", "cp932", "shift_jis"]
    last_error: Exception | None = None
    for encoding in encodings:
        try:
            return pd.read_csv(path, dtype=str, encoding=encoding).fillna("")
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"Failed to read CSV {path}: {last_error}")


def derive_fields(df: pd.DataFrame) -> pd.DataFrame:
    required = ["response_id", "q7_bath_heater_status", "q8_reason_codes", "q8_other_text"]
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise KeyError(f"Input CSV is missing required columns: {missing}")

    output = df.copy()
    q7 = output["q7_bath_heater_status"].astype(str).str.strip()
    q8 = output["q8_reason_codes"].astype(str).str.strip()
    recode_mask = q7.eq("1") & q8.ne("")

    output["q7_bath_heater_status_analysis"] = q7
    output.loc[recode_mask, "q7_bath_heater_status_analysis"] = "2"
    output["q7_q8_inconsistency_flag"] = recode_mask.astype(int).astype(str)
    output["q7_analysis_note"] = ""
    output.loc[recode_mask, "q7_analysis_note"] = NOTE_RECODED
    return output


def main() -> None:
    args = parse_args()
    run_dir = Path(args.run_dir).resolve()
    input_csv = (
        Path(args.input).resolve()
        if args.input
        else run_dir / "aomori_survey_responses_reviewed_manual.csv"
    )
    output_csv = (
        Path(args.output).resolve()
        if args.output
        else run_dir / "aomori_survey_responses_reviewed_analysis.csv"
    )

    df = read_csv(input_csv)
    output = derive_fields(df)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(output_csv, index=False, encoding="utf-8-sig", quoting=csv.QUOTE_MINIMAL)

    recoded = int(output["q7_q8_inconsistency_flag"].eq("1").sum())
    print(f"Rows: {len(output)}")
    print(f"Q7=1 with Q8 reason recoded for analysis: {recoded}")
    print(output_csv)


if __name__ == "__main__":
    main()
