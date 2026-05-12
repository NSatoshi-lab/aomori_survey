#!/usr/bin/env python3
"""Apply manual Aomori OCR review decisions to a reviewed response CSV."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RUN_DIR = REPO_ROOT / "outputs" / "runs" / "20260512_ocr_ingest_q6_q99_scoped_patch_full_dry_run"
REVIEW_FIELDS = {
    "q1_age_group": {"1", "2", "3", "4", "5", "6", "7", "8", "99"},
    "q2_housing_type": {"1", "2", "99"},
    "q3_building_age_band": {"1", "2", "3", "4", "5", "99"},
    "q4_tenure": {"1", "2", "99"},
    "q5_winter_home_bath_freq": {"1", "2", "3", "4", "5", "99"},
    "q6_window_insulation": {"1", "2", "3", "4", "99"},
    "q7_bath_heater_status": {"1", "2", "3", "99"},
    "q9_central_heating_use": {"1", "2", "3", "99"},
    "q11_dressingroom_cold_7pt": {"1", "2", "3", "4", "5", "6", "7", "99"},
    "q11_bathroom_cold_7pt": {"1", "2", "3", "4", "5", "6", "7", "99"},
}
MULTI_CHOICE_FIELDS = {
    "q8_reason_codes": {"1", "2", "3", "4", "5", "6", "7", "8"},
    "q10_alt_heating_types": {"1", "2", "3", "4", "5"},
}
TEXT_FIELDS = {"q8_other_text", "q10_other_text"}
ROUTINE_REVIEW_NOTES = {
    "チェックなし",
    "自由記述なし",
    "文字記載なし",
}
OTHER_TEXT_BY_MULTI_FIELD = {
    "q8_reason_codes": ("8", "q8_other_text"),
    "q10_alt_heating_types": ("4", "q10_other_text"),
}
DECISION_COLUMNS = [
    "review_item_id",
    "response_id",
    "field",
    "current_value",
    "resolved_value",
    "reviewer_note",
    "source_file",
    "question_crop_path",
    "reviewed_at",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Apply manual review decisions to Aomori reviewed OCR CSV."
    )
    parser.add_argument("--run-dir", default=str(DEFAULT_RUN_DIR), help="OCR run directory")
    parser.add_argument(
        "--reviewed-csv",
        help="Reviewed CSV to update. Defaults to <run-dir>/aomori_survey_responses_reviewed.csv",
    )
    parser.add_argument(
        "--decisions-csv",
        help="Manual decisions CSV. Defaults to <run-dir>/manual_review_decisions.csv",
    )
    parser.add_argument(
        "--output",
        help="Output CSV. Defaults to <run-dir>/aomori_survey_responses_reviewed_manual.csv",
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


def validate_decisions(decisions: pd.DataFrame, reviewed: pd.DataFrame) -> pd.DataFrame:
    missing = [column for column in DECISION_COLUMNS if column not in decisions.columns]
    if missing:
        raise KeyError(f"Decision CSV is missing columns: {missing}")
    if "response_id" not in reviewed.columns:
        raise KeyError("Reviewed CSV is missing response_id")

    normalized = decisions.copy().fillna("")
    normalized = normalized.drop_duplicates(subset=["review_item_id"], keep="last")

    response_ids = set(reviewed["response_id"].astype(str))
    errors: list[str] = []
    for _, row in normalized.iterrows():
        response_id = str(row["response_id"])
        field = str(row["field"])
        resolved_value = str(row["resolved_value"]).strip()
        if response_id not in response_ids:
            errors.append(f"{row['review_item_id']}: unknown response_id {response_id}")
            continue
        if field not in REVIEW_FIELDS and field not in MULTI_CHOICE_FIELDS and field not in TEXT_FIELDS:
            errors.append(f"{row['review_item_id']}: unsupported field {field}")
            continue
        if field in REVIEW_FIELDS and resolved_value not in REVIEW_FIELDS[field]:
            errors.append(
                f"{row['review_item_id']}: invalid value {resolved_value} for {field}"
            )
            continue
        if field in MULTI_CHOICE_FIELDS:
            codes = [token.strip() for token in resolved_value.split(";") if token.strip()]
            if len(codes) != len(set(codes)):
                errors.append(f"{row['review_item_id']}: duplicate codes in {resolved_value}")
                continue
            invalid = [code for code in codes if code not in MULTI_CHOICE_FIELDS[field]]
            if invalid:
                errors.append(
                    f"{row['review_item_id']}: invalid codes {invalid} for {field}"
                )
    if errors:
        preview = "\n".join(errors[:20])
        raise ValueError(f"Invalid manual review decisions:\n{preview}")
    return normalized


def is_substantive_note(note: str) -> bool:
    normalized = str(note).strip()
    if not normalized:
        return False
    if normalized in ROUTINE_REVIEW_NOTES:
        return False
    if "どちらもチェック" in normalized:
        return False
    return True


def apply_decisions(reviewed: pd.DataFrame, decisions: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    output = reviewed.copy()
    if "manual_review_notes" not in output.columns:
        output["manual_review_notes"] = ""
    output_index = {
        str(response_id): index for index, response_id in output["response_id"].items()
    }
    applied = 0
    notes_by_response: dict[str, list[str]] = {}
    for _, row in decisions.iterrows():
        response_id = str(row["response_id"])
        field = str(row["field"])
        resolved_value = str(row["resolved_value"]).strip()
        reviewer_note = str(row["reviewer_note"]).strip()
        row_index = output_index[response_id]
        output.at[row_index, field] = resolved_value
        if is_substantive_note(reviewer_note):
            notes_by_response.setdefault(response_id, []).append(f"{field}: {reviewer_note}")
            if field in OTHER_TEXT_BY_MULTI_FIELD:
                other_code, text_field = OTHER_TEXT_BY_MULTI_FIELD[field]
                codes = {token.strip() for token in resolved_value.split(";") if token.strip()}
                if other_code in codes and not str(output.at[row_index, text_field]).strip():
                    output.at[row_index, text_field] = reviewer_note
        applied += 1
    for response_id, notes in notes_by_response.items():
        row_index = output_index[response_id]
        existing = str(output.at[row_index, "manual_review_notes"]).strip()
        combined = "; ".join(notes)
        output.at[row_index, "manual_review_notes"] = (
            f"{existing}; {combined}" if existing else combined
        )
    return output, applied


def main() -> None:
    args = parse_args()
    run_dir = Path(args.run_dir).resolve()
    reviewed_csv = (
        Path(args.reviewed_csv).resolve()
        if args.reviewed_csv
        else run_dir / "aomori_survey_responses_reviewed.csv"
    )
    decisions_csv = (
        Path(args.decisions_csv).resolve()
        if args.decisions_csv
        else run_dir / "manual_review_decisions.csv"
    )
    output_csv = (
        Path(args.output).resolve()
        if args.output
        else run_dir / "aomori_survey_responses_reviewed_manual.csv"
    )

    reviewed = read_csv(reviewed_csv)
    decisions = read_csv(decisions_csv)
    valid_decisions = validate_decisions(decisions, reviewed)
    output, applied = apply_decisions(reviewed, valid_decisions)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(output_csv, index=False, encoding="utf-8-sig", quoting=csv.QUOTE_MINIMAL)
    print(f"Applied {applied} decisions")
    print(output_csv)


if __name__ == "__main__":
    main()
