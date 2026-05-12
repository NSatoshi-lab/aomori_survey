#!/usr/bin/env python3
"""Streamlit app for reviewing Aomori OCR fields that need manual checks."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from PIL import Image, ImageOps


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RUN_DIR = REPO_ROOT / "outputs" / "runs" / "20260512_ocr_ingest_q6_q99_scoped_patch_full_dry_run"
DEFAULT_LAYOUT_JSON = (
    REPO_ROOT
    / "deliverables"
    / "04_data_entry_analysis"
    / "20260512_aomori_survey_real_scan_layout_v1.json"
)
CROP_VERSION = "v3"
QUESTION_PREVIEW_BOXES = {
    "q1_age_group": (0.045, 0.082, 0.955, 0.312),
    "q2_housing_type": (0.045, 0.257, 0.955, 0.424),
    "q3_building_age_band": (0.045, 0.368, 0.955, 0.566),
    "q4_tenure": (0.045, 0.511, 0.955, 0.678),
    "q5_winter_home_bath_freq": (0.045, 0.623, 0.955, 0.882),
    "q6_window_insulation": (0.045, 0.026, 0.955, 0.220),
    "q7_bath_heater_status": (0.045, 0.215, 0.955, 0.355),
    "q8_reason_codes": (0.045, 0.365, 0.955, 0.700),
    "q9_central_heating_use": (0.045, 0.700, 0.955, 0.960),
    "q10_alt_heating_types": (0.045, 0.043, 0.955, 0.302),
    "q11_dressingroom_cold_7pt": (0.045, 0.297, 0.955, 0.618),
    "q11_bathroom_cold_7pt": (0.045, 0.549, 0.955, 0.870),
}
SINGLE_CHOICE_FIELDS = [
    "q1_age_group",
    "q2_housing_type",
    "q3_building_age_band",
    "q4_tenure",
    "q5_winter_home_bath_freq",
    "q6_window_insulation",
    "q7_bath_heater_status",
    "q9_central_heating_use",
    "q11_dressingroom_cold_7pt",
    "q11_bathroom_cold_7pt",
]
MULTI_CHOICE_FIELDS = ["q8_reason_codes", "q10_alt_heating_types"]
TEXT_FIELDS = ["q8_other_text", "q10_other_text"]
REVIEW_FIELDS = SINGLE_CHOICE_FIELDS + MULTI_CHOICE_FIELDS + TEXT_FIELDS
REVIEW_PHASES = {
    "fallback Q7/Q9": "fallback",
    "99単一選択": "single_99",
    "複数選択 Q8/Q10": "multi",
    "自由記述": "text",
    "すべて": "all",
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
FIELD_LABELS = {
    "q1_age_group": "Q1 年齢",
    "q2_housing_type": "Q2 住宅種別",
    "q3_building_age_band": "Q3 築年数",
    "q4_tenure": "Q4 持家/賃貸",
    "q5_winter_home_bath_freq": "Q5 冬季の自宅入浴頻度",
    "q6_window_insulation": "Q6 浴室の窓の断熱仕様",
    "q7_bath_heater_status": "Q7 浴室暖房乾燥機の使用状況",
    "q8_reason_codes": "Q8 設置していない/使わない理由",
    "q8_other_text": "Q8 その他自由記述",
    "q9_central_heating_use": "Q9 セントラル暖房の使用状況",
    "q10_alt_heating_types": "Q10 使用している暖房設備",
    "q10_other_text": "Q10 その他自由記述",
    "q11_dressingroom_cold_7pt": "Q11 脱衣所の寒さ",
    "q11_bathroom_cold_7pt": "Q11 浴室の寒さ",
}
OPTION_LABELS = {
    "q1_age_group": {
        "1": "18-29",
        "2": "30-39",
        "3": "40-49",
        "4": "50-59",
        "5": "60-69",
        "6": "70-79",
        "7": "80-89",
        "8": "90歳以上",
    },
    "q2_housing_type": {"1": "一戸建て", "2": "集合住宅"},
    "q3_building_age_band": {
        "1": "10年未満",
        "2": "10-19年",
        "3": "20-29年",
        "4": "30年以上",
        "5": "わからない",
    },
    "q4_tenure": {"1": "持家", "2": "賃貸"},
    "q5_winter_home_bath_freq": {
        "1": "毎日",
        "2": "週4-6回",
        "3": "週1-3回",
        "4": "月1-3回",
        "5": "ほとんど入浴しない",
    },
    "q6_window_insulation": {
        "1": "二重サッシ/複層ガラスの窓あり",
        "2": "単板ガラスの窓あり",
        "3": "窓なし",
        "4": "わからない",
    },
    "q7_bath_heater_status": {
        "1": "設置しており、使用もしている",
        "2": "設置しているが、使用していない",
        "3": "設置も使用もしていない",
    },
    "q9_central_heating_use": {
        "1": "24時間使用している",
        "2": "特定の時間帯だけ使用している",
        "3": "使用していない",
    },
    "q8_reason_codes": {
        "1": "既に十分暖かいので必要がない",
        "2": "電気代が気になる",
        "3": "設置費用が高い",
        "4": "住宅の構造上、設置が難しい",
        "5": "賃貸で工事できない",
        "6": "使い方がわからない",
        "7": "故障中で使えない",
        "8": "その他（自由記述）",
    },
    "q10_alt_heating_types": {
        "1": "ストーブ（灯油、ガス、電気）",
        "2": "エアコン",
        "3": "床暖房",
        "4": "その他（自由記述）",
        "5": "使用していない",
    },
    "q11_dressingroom_cold_7pt": {
        "1": "非常に暖かい",
        "2": "2",
        "3": "3",
        "4": "4",
        "5": "5",
        "6": "6",
        "7": "非常に寒い",
    },
    "q11_bathroom_cold_7pt": {
        "1": "非常に暖かい",
        "2": "2",
        "3": "3",
        "4": "4",
        "5": "5",
        "6": "6",
        "7": "非常に寒い",
    },
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Review Aomori OCR 99 fields.")
    parser.add_argument("--run-dir", default=str(DEFAULT_RUN_DIR), help="OCR run directory")
    parser.add_argument(
        "--layout-json",
        default=str(DEFAULT_LAYOUT_JSON),
        help="Real-scan layout JSON used by OCR ingest",
    )
    parser.add_argument(
        "--decisions-csv",
        help="Manual decisions CSV path. Defaults to <run-dir>/manual_review_decisions.csv",
    )
    parser.add_argument(
        "--phase",
        choices=sorted(set(REVIEW_PHASES.values())),
        default="fallback",
        help="Initial review phase",
    )
    return parser.parse_known_args(argv)[0]


def read_csv(path: Path) -> pd.DataFrame:
    encodings = ["utf-8-sig", "utf-8", "cp932", "shift_jis"]
    last_error: Exception | None = None
    for encoding in encodings:
        try:
            return pd.read_csv(path, dtype=str, encoding=encoding).fillna("")
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"Failed to read CSV {path}: {last_error}")


def load_layout(path: Path) -> dict[str, list[tuple[float, float, float, float]]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    layout: dict[str, list[tuple[float, float, float, float]]] = {}
    for field in payload:
        layout[str(field["name"])] = [
            tuple(float(value) for value in option["bbox"])
            for option in field.get("options", [])
        ]
    return layout


def review_item_id(response_id: str, field: str) -> str:
    return f"{response_id}__{field}"


def field_kind(field: str) -> str:
    if field in MULTI_CHOICE_FIELDS:
        return "multi"
    if field in TEXT_FIELDS:
        return "text"
    return "single"


def resolve_path(path: str, base_dir: Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return (base_dir / candidate).resolve()


def question_crop_box(
    field: str,
    option_boxes: list[tuple[float, float, float, float]],
) -> tuple[float, float, float, float]:
    if field in QUESTION_PREVIEW_BOXES:
        return QUESTION_PREVIEW_BOXES[field]
    if not option_boxes:
        raise ValueError(f"No layout options found for {field}")
    min_y = min(box[1] for box in option_boxes)
    max_y = max(box[3] for box in option_boxes)
    top_pad = 0.060
    bottom_pad = 0.060
    if field == "q6_window_insulation":
        bottom_pad = 0.025
    if field == "q9_central_heating_use":
        top_pad = 0.075
    if field == "q8_reason_codes":
        bottom_pad = 0.090
    return (0.045, max(0.0, min_y - top_pad), 0.955, min(1.0, max_y + bottom_pad))


def crop_relative(
    image: Image.Image,
    bbox: tuple[float, float, float, float],
) -> Image.Image:
    width, height = image.size
    x1, y1, x2, y2 = bbox
    return image.crop(
        (
            max(0, int(round(x1 * width))),
            max(0, int(round(y1 * height))),
            min(width, int(round(x2 * width))),
            min(height, int(round(y2 * height))),
        )
    )


def generate_question_crop(
    source_file: str,
    response_id: str,
    field: str,
    layout: dict[str, list[tuple[float, float, float, float]]],
    crop_dir: Path,
) -> str:
    source_path = Path(source_file)
    if not source_path.exists():
        raise FileNotFoundError(f"Source image does not exist: {source_path}")
    crop_dir.mkdir(parents=True, exist_ok=True)
    output_path = crop_dir / f"{response_id}_{source_path.stem}_{field}_question_{CROP_VERSION}.jpg"
    if output_path.exists():
        return str(output_path)
    with Image.open(source_path) as opened:
        image = ImageOps.exif_transpose(opened).convert("RGB")
        crop = crop_relative(image, question_crop_box(field, layout[field]))
        crop.save(output_path, quality=95)
    return str(output_path)


def generate_crop_from_bbox_path(crop_path: str) -> str:
    return crop_path.split(";")[0] if crop_path else ""


def reviewed_source_path(run_dir: Path) -> Path:
    manual_path = run_dir / "aomori_survey_responses_reviewed_manual.csv"
    if manual_path.exists():
        return manual_path
    return run_dir / "aomori_survey_responses_reviewed.csv"


def include_queue_row(row: pd.Series, phase: str, reviewed: pd.DataFrame) -> bool:
    field = str(row["field"])
    issue = str(row["issue_type"])
    if field not in REVIEW_FIELDS:
        return False
    if phase == "all":
        return True
    if phase == "fallback":
        return field in {"q7_bath_heater_status", "q9_central_heating_use"} and (
            "fallback_layout_used" in issue
        )
    if phase == "multi":
        return field in MULTI_CHOICE_FIELDS
    if phase == "text":
        return field in TEXT_FIELDS
    if phase == "single_99":
        response_id = str(row["response_id"])
        match = reviewed[reviewed["response_id"].astype(str).eq(response_id)]
        if match.empty:
            return False
        return field in SINGLE_CHOICE_FIELDS and str(match.iloc[0].get(field, "")).strip() == "99"
    return False


def build_review_items(run_dir: Path, layout_json: Path, phase: str) -> pd.DataFrame:
    reviewed_path = reviewed_source_path(run_dir)
    candidates_path = run_dir / "ocr_candidates.csv"
    queue_path = run_dir / "ocr_review_queue.csv"
    reviewed = read_csv(reviewed_path)
    candidates = read_csv(candidates_path)
    queue = read_csv(queue_path)
    layout = load_layout(layout_json)
    crop_dir = run_dir / "review_question_crops"

    candidate_lookup = {
        (str(row["response_id"]), str(row["field"])): row
        for _, row in candidates.iterrows()
    }
    rows: list[dict[str, str]] = []
    reviewed_by_id = {
        str(row["response_id"]): row for _, row in reviewed.iterrows()
    }
    for _, queue_row in queue.iterrows():
        if not include_queue_row(queue_row, phase, reviewed):
            continue
        response_id = str(queue_row["response_id"])
        field = str(queue_row["field"])
        response = reviewed_by_id.get(response_id)
        candidate = candidate_lookup.get((response_id, field))
        if response is None or candidate is None:
            continue
        source_file = str(candidate["source_file"])
        if field in TEXT_FIELDS:
            question_crop_path = generate_crop_from_bbox_path(str(candidate.get("crop_path", "")))
        else:
            question_crop_path = generate_question_crop(
                source_file=source_file,
                response_id=response_id,
                field=field,
                layout=layout,
                crop_dir=crop_dir,
            )
        rows.append(
            {
                "review_item_id": review_item_id(response_id, field),
                "response_id": response_id,
                "field": field,
                "field_kind": field_kind(field),
                "field_label": FIELD_LABELS[field],
                "current_value": str(response.get(field, "")),
                "candidate_value": str(queue_row.get("candidate_value", "")),
                "review_reason": str(queue_row.get("issue_type", "")),
                "source_file": source_file,
                "question_crop_path": question_crop_path,
            }
        )
    return pd.DataFrame(rows)


def load_decisions(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=DECISION_COLUMNS)
    df = read_csv(path)
    for column in DECISION_COLUMNS:
        if column not in df.columns:
            df[column] = ""
    return df.reindex(columns=DECISION_COLUMNS)


def save_decision(path: Path, item: pd.Series, resolved_value: str, reviewer_note: str) -> None:
    decisions = load_decisions(path)
    item_id = str(item["review_item_id"])
    decisions = decisions[decisions["review_item_id"] != item_id]
    new_row = {
        "review_item_id": item_id,
        "response_id": str(item["response_id"]),
        "field": str(item["field"]),
        "current_value": str(item["current_value"]),
        "resolved_value": str(resolved_value),
        "reviewer_note": reviewer_note,
        "source_file": str(item["source_file"]),
        "question_crop_path": str(item["question_crop_path"]),
        "reviewed_at": datetime.now().isoformat(timespec="seconds"),
    }
    decisions = pd.concat([decisions, pd.DataFrame([new_row])], ignore_index=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    decisions.to_csv(path, index=False, encoding="utf-8-sig", quoting=csv.QUOTE_MINIMAL)


def decision_map(decisions: pd.DataFrame) -> dict[str, pd.Series]:
    if decisions.empty:
        return {}
    deduped = decisions.drop_duplicates(subset=["review_item_id"], keep="last")
    return {str(row["review_item_id"]): row for _, row in deduped.iterrows()}


def select_current_item(items: pd.DataFrame, decisions: dict[str, pd.Series]) -> pd.Series | None:
    if items.empty:
        return None
    unresolved = items[~items["review_item_id"].isin(decisions)]
    if not unresolved.empty:
        return unresolved.iloc[0]
    return items.iloc[0]


def display_name(row: pd.Series, done: bool) -> str:
    status = "済" if done else "未"
    return f"{status} {row['response_id']} {row['field_label']}"


def parse_code_list(value: str) -> set[str]:
    return {token.strip() for token in str(value or "").split(";") if token.strip()}


def render_single_choice(st: Any, decisions_csv: Path, item: pd.Series, reviewer_note: str) -> None:
    options = OPTION_LABELS[str(item["field"])]
    for code, label in options.items():
        if st.button(f"{code}: {label}", key=f"save_{item['review_item_id']}_{code}"):
            save_decision(decisions_csv, item, code, reviewer_note)
            st.rerun()
    st.divider()
    if st.button("99: 判定不能のまま", key=f"save_{item['review_item_id']}_99"):
        save_decision(decisions_csv, item, "99", reviewer_note)
        st.rerun()


def render_multi_choice(
    st: Any,
    decisions_csv: Path,
    item: pd.Series,
    existing: pd.Series | None,
    reviewer_note: str,
) -> None:
    options = OPTION_LABELS[str(item["field"])]
    default_value = (
        str(existing.get("resolved_value", ""))
        if existing is not None
        else str(item.get("current_value", ""))
    )
    selected_defaults = parse_code_list(default_value)
    selected: list[str] = []
    for code, label in options.items():
        checked = code in selected_defaults
        if st.checkbox(f"{code}: {label}", value=checked, key=f"check_{item['review_item_id']}_{code}"):
            selected.append(code)
    resolved_value = ";".join(sorted(selected, key=int))
    st.write(f"保存値: `{resolved_value}`")
    if st.button("複数選択を保存", key=f"save_{item['review_item_id']}_multi"):
        save_decision(decisions_csv, item, resolved_value, reviewer_note)
        st.rerun()


def render_text_choice(
    st: Any,
    decisions_csv: Path,
    item: pd.Series,
    existing: pd.Series | None,
    reviewer_note: str,
) -> None:
    default_value = (
        str(existing.get("resolved_value", ""))
        if existing is not None
        else str(item.get("current_value", ""))
    )
    text_value = st.text_area(
        "自由記述の目視入力",
        value=default_value,
        key=f"text_{item['review_item_id']}",
    )
    if st.button("自由記述を保存", key=f"save_{item['review_item_id']}_text"):
        save_decision(decisions_csv, item, text_value, reviewer_note)
        st.rerun()


def run_app() -> None:
    try:
        import streamlit as st
    except ImportError:
        print("Streamlit is not installed. Install it with: pip install streamlit", file=sys.stderr)
        raise SystemExit(1)

    args = parse_args()
    run_dir = resolve_path(args.run_dir, REPO_ROOT)
    layout_json = resolve_path(args.layout_json, REPO_ROOT)
    decisions_csv = (
        resolve_path(args.decisions_csv, REPO_ROOT)
        if args.decisions_csv
        else run_dir / "manual_review_decisions.csv"
    )

    st.set_page_config(page_title="Aomori OCR Review", layout="wide")
    st.title("青森アンケート OCR 目視レビュー")

    if not run_dir.exists():
        st.error(f"Run directory does not exist: {run_dir}")
        st.stop()
    if not layout_json.exists():
        st.error(f"Layout JSON does not exist: {layout_json}")
        st.stop()

    phase_labels = list(REVIEW_PHASES.keys())
    initial_phase_label = next(
        (label for label, value in REVIEW_PHASES.items() if value == args.phase),
        "fallback Q7/Q9",
    )
    with st.sidebar:
        selected_phase_label = st.selectbox(
            "確認フェーズ",
            phase_labels,
            index=phase_labels.index(initial_phase_label),
        )
    phase = REVIEW_PHASES[selected_phase_label]

    items = build_review_items(run_dir, layout_json, phase)
    decisions_df = load_decisions(decisions_csv)
    decisions = decision_map(decisions_df)

    with st.sidebar:
        st.caption(str(run_dir))
        st.metric("レビュー対象", len(items))
        st.metric("保存済み", len(set(items["review_item_id"]).intersection(decisions)))
        field_choices = ["すべて"] + [FIELD_LABELS[field] for field in REVIEW_FIELDS]
        selected_field_label = st.selectbox("設問フィルタ", field_choices)
        response_query = st.text_input("response_id検索", "")
        show_done = st.checkbox("保存済みも表示", value=True)
        st.caption(f"保存先: {decisions_csv}")

    filtered = items.copy()
    if selected_field_label != "すべて":
        selected_field = next(
            field for field, label in FIELD_LABELS.items() if label == selected_field_label
        )
        filtered = filtered[filtered["field"] == selected_field]
    if response_query.strip():
        filtered = filtered[
            filtered["response_id"].str.contains(response_query.strip(), case=False, na=False)
        ]
    if not show_done:
        filtered = filtered[~filtered["review_item_id"].isin(decisions)]

    if filtered.empty:
        st.info("表示対象のレビュー項目はありません。")
        return

    initial = select_current_item(filtered, decisions)
    assert initial is not None
    item_ids = list(filtered["review_item_id"])
    labels = {
        str(row["review_item_id"]): display_name(
            row, str(row["review_item_id"]) in decisions
        )
        for _, row in filtered.iterrows()
    }
    selected_item_id = st.selectbox(
        "レビュー項目",
        item_ids,
        index=item_ids.index(str(initial["review_item_id"])),
        format_func=lambda item_id: labels[item_id],
    )
    item = filtered[filtered["review_item_id"] == selected_item_id].iloc[0]
    existing = decisions.get(selected_item_id)

    left, right = st.columns([1.35, 1.0])
    with left:
        st.subheader(f"{item['response_id']} / {item['field_label']}")
        crop_path = Path(str(item["question_crop_path"]))
        if crop_path.exists():
            st.image(str(crop_path), use_container_width=True)
            st.caption(str(crop_path))
        else:
            st.warning(f"Question crop is missing: {crop_path}")
        st.text(f"source_file: {item['source_file']}")
        st.text(f"review_reason: {item['review_reason']}")

    with right:
        st.subheader("目視判定")
        st.write(f"確認種別: `{item['field_kind']}`")
        st.write(f"現在値: `{item['current_value']}`")
        st.write(f"OCR候補値: `{item['candidate_value']}`")
        if existing is not None:
            st.success(f"保存済み: `{existing['resolved_value']}`")
        note_key = f"note_{selected_item_id}"
        default_note = "" if existing is None else str(existing.get("reviewer_note", ""))
        reviewer_note = st.text_area("メモ", value=default_note, key=note_key)
        kind = str(item["field_kind"])
        if kind == "multi":
            render_multi_choice(st, decisions_csv, item, existing, reviewer_note)
        elif kind == "text":
            render_text_choice(st, decisions_csv, item, existing, reviewer_note)
        else:
            render_single_choice(st, decisions_csv, item, reviewer_note)


if __name__ == "__main__":
    run_app()
