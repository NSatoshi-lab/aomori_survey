#!/usr/bin/env python3
"""Tabulate Goshogawara Q1-Q11 paper survey results for Step 5."""

from __future__ import annotations

import argparse
import math
from datetime import datetime
from pathlib import Path
from typing import Iterable, List

import pandas as pd

try:
    from scipy.stats import chi2_contingency, fisher_exact
except Exception:  # pragma: no cover - optional dependency
    chi2_contingency = None
    fisher_exact = None


EXPECTED_COLUMNS = [
    "response_id",
    "q1_age_group",
    "q2_housing_type",
    "q3_building_age_band",
    "q4_tenure",
    "q5_winter_home_bath_freq",
    "q6_window_insulation",
    "q7_bath_heater_status",
    "q8_reason_codes",
    "q8_other_text",
    "q9_central_heating_use",
    "q10_alt_heating_types",
    "q10_other_text",
    "q11_dressingroom_cold_7pt",
    "q11_bathroom_cold_7pt",
]

NUMERIC_COLUMNS = [
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

TEXT_COLUMNS = [
    "response_id",
    "q8_reason_codes",
    "q8_other_text",
    "q10_alt_heating_types",
    "q10_other_text",
]

NO_NEED_REASON_CODES = {1}
BARRIER_REASON_CODES = {2, 3, 4, 5, 6, 7}
CONFIDENCE_Z_95 = 1.96
MAIN_ANALYSIS_VALID_THRESHOLD = 80
EXPLORATORY_ANALYSIS_VALID_THRESHOLD = 60
MAIN_MISSING_RATE_THRESHOLD_PCT = 20.0

# Sample-size design constants fixed by Step 5 v2 spec.
SAMPLE_SIZE_DESIGN_P = 0.5
SAMPLE_SIZE_DESIGN_E = 0.12
SAMPLE_SIZE_DESIGN_DEFF = 1.2
SAMPLE_SIZE_DESIGN_INVALID_RATE = 0.15
SAMPLE_SIZE_DESIGN_TARGET_ROUND = 10
REPO_ROOT = Path(__file__).resolve().parents[2]

SINGLE_CHOICE_LABEL_COLUMNS = [
    ("q1_age_group", "q1_age_group_label", "Q1 年代"),
    ("q2_housing_type", "q2_housing_label", "Q2 住宅種別"),
    ("q3_building_age_band", "q3_building_age_band_label", "Q3 築年帯"),
    ("q4_tenure", "q4_tenure_label", "Q4 所有形態"),
    ("q5_winter_home_bath_freq", "q5_winter_home_bath_freq_label", "Q5 冬季自宅入浴頻度"),
    ("q6_window_insulation", "q6_window_insulation_label", "Q6 浴室窓断熱"),
    ("q7_bath_heater_status", "q7_status_label", "Q7 浴室暖房乾燥機"),
    ("q9_central_heating_use", "q9_label", "Q9 セントラル暖房"),
    ("q11_dressingroom_cold_7pt", "q11_dressingroom_label", "Q11 脱衣所寒さ"),
    ("q11_bathroom_cold_7pt", "q11_bathroom_label", "Q11 浴室寒さ"),
]

Q8_REASON_LABELS = {
    1: "1_既に十分暖かいので必要がない",
    2: "2_電気代が気になる",
    3: "3_設置費用が高い",
    4: "4_住宅の構造上、設置が難しい",
    5: "5_賃貸で工事できない",
    6: "6_使い方がわからない",
    7: "7_故障中で使えない",
    8: "8_その他",
}

Q10_ALT_HEATING_LABELS = {
    1: "1_ストーブ",
    2: "2_エアコン",
    3: "3_床暖房",
    4: "4_その他",
    5: "5_使用していない",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate required tabulations for Aomori Q1-Q11 paper survey."
    )
    parser.add_argument("--input-csv", required=True, help="Path to input CSV")
    parser.add_argument(
        "--output-dir",
        help=(
            "Path to output directory. Defaults to "
            "outputs/runs/YYYYMMDD_HHMMSS_initial_analysis."
        ),
    )
    return parser.parse_args()


def default_output_dir() -> Path:
    tag = datetime.now().strftime("%Y%m%d_%H%M%S_initial_analysis")
    return REPO_ROOT / "outputs" / "runs" / tag


def read_csv_with_fallback(path: Path) -> pd.DataFrame:
    encodings = ["utf-8-sig", "utf-8", "cp932", "shift_jis"]
    last_error = None
    for encoding in encodings:
        try:
            return pd.read_csv(path, dtype=str, encoding=encoding)
        except Exception as exc:  # pragma: no cover - fallback path
            last_error = exc
    raise RuntimeError(f"Failed to read CSV with fallback encodings: {last_error}")


def ensure_columns(df: pd.DataFrame, expected: Iterable[str]) -> None:
    missing = [col for col in expected if col not in df.columns]
    if missing:
        raise KeyError(f"Missing columns in input CSV: {missing}")


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    ensure_columns(d, EXPECTED_COLUMNS)
    d = d[EXPECTED_COLUMNS].copy()
    for col in NUMERIC_COLUMNS:
        d[col] = pd.to_numeric(d[col], errors="coerce").astype("Int64")
    for col in TEXT_COLUMNS:
        d[col] = d[col].fillna("").astype(str).str.strip()
    return d


def is_missing_numeric(series: pd.Series) -> pd.Series:
    return series.isna() | series.eq(99)


def derive_validity_flags(d: pd.DataFrame) -> pd.DataFrame:
    out = d.copy()
    q7 = out["q7_bath_heater_status"]
    q8 = out["q8_reason_codes"]
    q11_bath = out["q11_bathroom_cold_7pt"]

    need_q8 = q7.isin([2, 3])
    miss_q7 = is_missing_numeric(q7)
    miss_q8 = need_q8 & q8.eq("")
    miss_q11_bath = is_missing_numeric(q11_bath)

    out["need_q8"] = need_q8
    out["q7_q8_inconsistency_flag"] = q7.eq(1) & q8.ne("")
    out["missing_q7_bath_heater_status"] = miss_q7
    out["missing_q8_reason_codes"] = miss_q8
    out["missing_q11_bathroom_cold_7pt"] = miss_q11_bath
    out["invalid_main3"] = miss_q7 | miss_q8 | miss_q11_bath
    return out


def add_label_columns(d: pd.DataFrame) -> pd.DataFrame:
    out = d.copy()
    out["q7_status_label"] = out["q7_bath_heater_status"].map(
        {
            1: "1_設置して使用",
            2: "2_設置しているが未使用",
            3: "3_未設置",
            99: "99_無回答",
        }
    ).fillna("99_無回答")
    out["q9_label"] = out["q9_central_heating_use"].map(
        {1: "1_24時間使用", 2: "2_時間限定使用", 3: "3_不使用", 99: "99_無回答"}
    ).fillna("99_無回答")
    out["q1_age_group_label"] = out["q1_age_group"].map(
        {
            1: "1_18-29",
            2: "2_30-39",
            3: "3_40-49",
            4: "4_50-59",
            5: "5_60-69",
            6: "6_70-79",
            7: "7_80-89",
            8: "8_90歳以上",
            99: "99_無回答",
        }
    ).fillna("99_無回答")
    out["q3_building_age_band_label"] = out["q3_building_age_band"].map(
        {
            1: "1_10年未満",
            2: "2_10-19年",
            3: "3_20-29年",
            4: "4_30年以上",
            5: "5_わからない",
            99: "99_無回答",
        }
    ).fillna("99_無回答")
    out["q4_tenure_label"] = out["q4_tenure"].map(
        {1: "1_持家", 2: "2_賃貸", 99: "99_無回答"}
    ).fillna("99_無回答")
    out["q5_winter_home_bath_freq_label"] = out["q5_winter_home_bath_freq"].map(
        {
            1: "1_毎日",
            2: "2_週4-6回",
            3: "3_週1-3回",
            4: "4_月1-3回",
            5: "5_ほとんど入浴しない",
            99: "99_無回答",
        }
    ).fillna("99_無回答")
    out["q6_window_insulation_label"] = out["q6_window_insulation"].map(
        {
            1: "1_二重サッシ/複層ガラスあり",
            2: "2_単板ガラスあり",
            3: "3_窓なし",
            4: "4_わからない",
            99: "99_無回答",
        }
    ).fillna("99_無回答")
    out["q11_dressingroom_label"] = out["q11_dressingroom_cold_7pt"].map(
        {
            1: "1_非常に暖かい",
            2: "2_暖かい",
            3: "3_やや暖かい",
            4: "4_どちらでもない",
            5: "5_やや寒い",
            6: "6_寒い",
            7: "7_非常に寒い",
            99: "99_無回答",
        }
    ).fillna("99_無回答")
    out["q11_bathroom_label"] = out["q11_bathroom_cold_7pt"].map(
        {
            1: "1_非常に暖かい",
            2: "2_暖かい",
            3: "3_やや暖かい",
            4: "4_どちらでもない",
            5: "5_やや寒い",
            6: "6_寒い",
            7: "7_非常に寒い",
            99: "99_無回答",
        }
    ).fillna("99_無回答")
    out["q2_housing_label"] = out["q2_housing_type"].map(
        {1: "1_一戸建て", 2: "2_集合住宅", 99: "99_無回答"}
    ).fillna("99_無回答")
    out["bathroom_cold_binary"] = out["q11_bathroom_cold_7pt"].apply(label_cold_binary)
    return out


def label_cold_binary(value: object) -> str:
    if pd.isna(value):
        return "無回答"
    n = int(value)
    if 5 <= n <= 7:
        return "寒い(5-7)"
    if 1 <= n <= 4:
        return "寒くない/中立(1-4)"
    return "無回答"


def parse_reason_codes(value: str) -> List[int]:
    if not value:
        return []
    codes: List[int] = []
    for token in value.split(";"):
        token = token.strip()
        if not token:
            continue
        try:
            codes.append(int(token))
        except ValueError:
            continue
    return codes


def reason_dominance(valid: pd.DataFrame) -> dict:
    target = valid[valid["need_q8"] & ~valid["q7_q8_inconsistency_flag"]].copy()
    if target.empty:
        return {
            "reason_target_n": 0,
            "no_need_pct": 0.0,
            "barrier_pct": 0.0,
            "gap_pp": 0.0,
            "dominant_group": "判定不可",
        }

    code_lists = target["q8_reason_codes"].apply(parse_reason_codes)
    has_no_need = code_lists.apply(
        lambda xs: any(code in NO_NEED_REASON_CODES for code in xs)
    )
    has_barrier = code_lists.apply(
        lambda xs: any(code in BARRIER_REASON_CODES for code in xs)
    )

    no_need_pct = float(has_no_need.mean() * 100.0)
    barrier_pct = float(has_barrier.mean() * 100.0)
    gap_pp = abs(no_need_pct - barrier_pct)

    if gap_pp >= 10.0:
        dominant_group = "不要群優勢" if no_need_pct > barrier_pct else "障壁群優勢"
    else:
        dominant_group = "拮抗(差10pp未満)"

    return {
        "reason_target_n": int(len(target)),
        "no_need_pct": round(no_need_pct, 2),
        "barrier_pct": round(barrier_pct, 2),
        "gap_pp": round(gap_pp, 2),
        "dominant_group": dominant_group,
    }


def wilson_ci(success: int, total: int, z: float = CONFIDENCE_Z_95) -> tuple[float, float]:
    if total <= 0:
        return (0.0, 0.0)
    phat = success / total
    denom = 1.0 + (z * z) / total
    center = (phat + (z * z) / (2.0 * total)) / denom
    margin = (
        z
        * math.sqrt(
            (phat * (1.0 - phat) / total) + ((z * z) / (4.0 * total * total))
        )
        / denom
    )
    lo = max(0.0, center - margin)
    hi = min(1.0, center + margin)
    return (lo, hi)


def summarize_q7_q9(valid: pd.DataFrame) -> dict:
    target = valid[
        valid["q7_bath_heater_status"].isin([1, 2, 3])
        & valid["q9_central_heating_use"].isin([1, 2, 3])
    ].copy()
    if target.empty:
        return {
            "target_n": 0,
            "rows": [],
            "test_method": "判定不可",
            "test_p": None,
            "small_expected_cell": None,
        }

    q7_order = ["1_設置して使用", "2_設置しているが未使用", "3_未設置"]
    q9_order = ["1_24時間使用", "2_時間限定使用", "3_不使用"]
    table = pd.crosstab(
        target["q7_status_label"], target["q9_label"], dropna=False
    ).reindex(index=q7_order, columns=q9_order, fill_value=0)

    rows = []
    for group in table.index:
        row_total = int(table.loc[group].sum())
        for col in table.columns:
            count = int(table.loc[group, col])
            pct = (count / row_total * 100.0) if row_total else 0.0
            ci_lo, ci_hi = wilson_ci(count, row_total)
            rows.append(
                {
                    "group": group,
                    "q9_category": col,
                    "count": count,
                    "row_total": row_total,
                    "pct": round(pct, 2),
                    "ci95_lo_pct": round(ci_lo * 100.0, 2),
                    "ci95_hi_pct": round(ci_hi * 100.0, 2),
                }
            )

    test_method = "記述統計のみ"
    test_p = None
    small_expected_cell = None
    if chi2_contingency is not None:
        try:
            _, p_chi, _, expected = chi2_contingency(table.to_numpy())
            small_expected_cell = bool((expected < 5.0).any())
            if not small_expected_cell:
                test_method = "χ2検定"
                test_p = float(p_chi)
            elif fisher_exact is not None and table.shape == (2, 2):
                fisher_res = fisher_exact(table.to_numpy())
                test_p = (
                    float(fisher_res.pvalue)
                    if hasattr(fisher_res, "pvalue")
                    else float(fisher_res[1])
                )
                test_method = "Fisher exact"
            else:
                test_method = "expected<5: exact法未実装のため記述統計のみ"
        except Exception:
            test_method = "記述統計のみ（検定計算不可）"

    return {
        "target_n": int(len(target)),
        "rows": rows,
        "test_method": test_method,
        "test_p": test_p,
        "small_expected_cell": small_expected_cell,
    }


def analysis_gate(valid_count: int, missing_rate_pct: float) -> str:
    if missing_rate_pct >= MAIN_MISSING_RATE_THRESHOLD_PCT:
        return "記述中心（主要欠損率20%以上）"
    if valid_count >= MAIN_ANALYSIS_VALID_THRESHOLD:
        return "主解析（有効80以上）"
    if valid_count >= EXPLORATORY_ANALYSIS_VALID_THRESHOLD:
        return "探索的解析（有効60-79）"
    return "記述中心（有効60未満）"


def sample_size_requirements(
    e: float,
    p: float = SAMPLE_SIZE_DESIGN_P,
    deff: float = SAMPLE_SIZE_DESIGN_DEFF,
    invalid_rate: float = SAMPLE_SIZE_DESIGN_INVALID_RATE,
    z: float = CONFIDENCE_Z_95,
) -> dict:
    n0 = (z * z * p * (1.0 - p)) / (e * e)
    n0_ceil = int(math.ceil(n0))
    n_valid = int(math.ceil(n0_ceil * deff))
    n_collected = int(math.ceil(n_valid / (1.0 - invalid_rate)))
    n_operational = int(
        math.ceil(n_collected / SAMPLE_SIZE_DESIGN_TARGET_ROUND)
        * SAMPLE_SIZE_DESIGN_TARGET_ROUND
    )
    return {
        "e": e,
        "n0": n0,
        "n0_ceil": n0_ceil,
        "n_valid": n_valid,
        "n_collected": n_collected,
        "n_operational": n_operational,
    }


def save_crosstabs(valid: pd.DataFrame, output_dir: Path) -> None:
    table1 = pd.crosstab(
        valid["q7_status_label"], valid["q11_bathroom_label"], dropna=False
    )
    table1.to_csv(
        output_dir / "table1_q7_status_x_bathroom_cold_7pt.csv",
        encoding="utf-8-sig",
    )

    table2 = pd.crosstab(valid["q7_status_label"], valid["q9_label"], dropna=False)
    table2.to_csv(
        output_dir / "table2_q7_status_x_central_heating.csv",
        encoding="utf-8-sig",
    )

    reasons = valid[
        valid["need_q8"]
        & ~valid["q7_q8_inconsistency_flag"]
        & valid["q8_reason_codes"].ne("")
    ][
        ["q8_reason_codes", "q2_housing_label"]
    ].copy()
    if reasons.empty:
        table3 = pd.DataFrame(columns=["reason_code", "housing_type", "count"])
    else:
        reasons["reason_code_list"] = reasons["q8_reason_codes"].apply(parse_reason_codes)
        exploded = reasons.explode("reason_code_list")
        exploded = exploded[exploded["reason_code_list"].notna()].copy()
        exploded["reason_code"] = exploded["reason_code_list"].astype(int)
        table3 = pd.crosstab(exploded["reason_code"], exploded["q2_housing_label"], dropna=False)
    table3.to_csv(
        output_dir / "table3_q8_reason_x_housing_type.csv",
        encoding="utf-8-sig",
    )


def summarize_single_choice(valid: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for variable, label_col, variable_label in SINGLE_CHOICE_LABEL_COLUMNS:
        total = int(len(valid))
        counts = valid[label_col].value_counts(dropna=False).sort_index()
        for category, count_value in counts.items():
            count = int(count_value)
            pct = (count / total * 100.0) if total else 0.0
            ci_lo, ci_hi = wilson_ci(count, total)
            rows.append(
                {
                    "summary_type": "single_choice",
                    "variable": variable,
                    "variable_label": variable_label,
                    "category": category,
                    "count": count,
                    "denominator": total,
                    "pct": round(pct, 2),
                    "ci95_lo_pct": round(ci_lo * 100.0, 2),
                    "ci95_hi_pct": round(ci_hi * 100.0, 2),
                }
            )
    return pd.DataFrame(rows)


def summarize_multiple_choice(
    denominator_df: pd.DataFrame,
    variable: str,
    variable_label: str,
    code_labels: dict[int, str],
) -> pd.DataFrame:
    total = int(len(denominator_df))
    code_lists = denominator_df[variable].fillna("").astype(str).apply(parse_reason_codes)
    rows = []
    for code, label in code_labels.items():
        count = int(code_lists.apply(lambda xs: code in xs).sum())
        pct = (count / total * 100.0) if total else 0.0
        ci_lo, ci_hi = wilson_ci(count, total)
        rows.append(
            {
                "summary_type": "multiple_choice",
                "variable": variable,
                "variable_label": variable_label,
                "category": label,
                "count": count,
                "denominator": total,
                "pct": round(pct, 2),
                "ci95_lo_pct": round(ci_lo * 100.0, 2),
                "ci95_hi_pct": round(ci_hi * 100.0, 2),
            }
        )

    empty_count = int(
        denominator_df[variable].fillna("").astype(str).str.strip().eq("").sum()
    )
    if empty_count:
        pct = (empty_count / total * 100.0) if total else 0.0
        ci_lo, ci_hi = wilson_ci(empty_count, total)
        rows.append(
            {
                "summary_type": "multiple_choice",
                "variable": variable,
                "variable_label": variable_label,
                "category": "empty_無回答/非該当",
                "count": empty_count,
                "denominator": total,
                "pct": round(pct, 2),
                "ci95_lo_pct": round(ci_lo * 100.0, 2),
                "ci95_hi_pct": round(ci_hi * 100.0, 2),
            }
        )
    return pd.DataFrame(rows)


def save_descriptive_summary(valid: pd.DataFrame, output_dir: Path) -> pd.DataFrame:
    q8_target = valid[valid["need_q8"] & ~valid["q7_q8_inconsistency_flag"]].copy()
    summary = pd.concat(
        [
            summarize_single_choice(valid),
            summarize_multiple_choice(
                q8_target,
                "q8_reason_codes",
                "Q8 未使用/未設置理由（Q7=2/3）",
                Q8_REASON_LABELS,
            ),
            summarize_multiple_choice(
                valid,
                "q10_alt_heating_types",
                "Q10 代替暖房設備",
                Q10_ALT_HEATING_LABELS,
            ),
        ],
        ignore_index=True,
    )
    summary.to_csv(output_dir / "descriptive_summary.csv", index=False, encoding="utf-8-sig")
    return summary


def save_q7_q8_inconsistency_supplement(
    flagged: pd.DataFrame, output_dir: Path
) -> pd.DataFrame:
    supplement = flagged[flagged["q7_q8_inconsistency_flag"]].copy()
    columns = [
        "response_id",
        "q7_bath_heater_status",
        "q7_status_label",
        "q8_reason_codes",
        "q8_other_text",
        "q9_central_heating_use",
        "q9_label",
        "q11_bathroom_cold_7pt",
        "q11_bathroom_label",
        "invalid_main3",
    ]
    supplement = supplement[columns]
    supplement.to_csv(
        output_dir / "q7_q8_inconsistency_supplement.csv",
        index=False,
        encoding="utf-8-sig",
    )
    return supplement


def save_free_text_summary(valid: pd.DataFrame, output_dir: Path) -> pd.DataFrame:
    rows = []
    for _, row in valid.iterrows():
        q8_codes = parse_reason_codes(str(row["q8_reason_codes"]))
        if 8 in q8_codes:
            text = str(row["q8_other_text"]).strip()
            rows.append(
                {
                    "question": "Q8",
                    "response_id": row["response_id"],
                    "selected_other_code": 1,
                    "text": text,
                    "text_status": "記述あり" if text else "その他チェックあり・記述なし",
                    "included_in_main_reason_summary": int(
                        bool(row["need_q8"])
                        and not bool(row["q7_q8_inconsistency_flag"])
                    ),
                }
            )

        q10_codes = parse_reason_codes(str(row["q10_alt_heating_types"]))
        if 4 in q10_codes:
            text = str(row["q10_other_text"]).strip()
            rows.append(
                {
                    "question": "Q10",
                    "response_id": row["response_id"],
                    "selected_other_code": 1,
                    "text": text,
                    "text_status": "記述あり" if text else "その他チェックあり・記述なし",
                    "included_in_main_reason_summary": "",
                }
            )

    summary = pd.DataFrame(
        rows,
        columns=[
            "question",
            "response_id",
            "selected_other_code",
            "text",
            "text_status",
            "included_in_main_reason_summary",
        ],
    )
    summary.to_csv(output_dir / "free_text_summary.csv", index=False, encoding="utf-8-sig")
    return summary


def save_supplemental_outputs(flagged: pd.DataFrame, output_dir: Path) -> dict:
    valid = flagged[~flagged["invalid_main3"]].copy()
    descriptive = save_descriptive_summary(valid, output_dir)
    inconsistency = save_q7_q8_inconsistency_supplement(flagged, output_dir)
    free_text = save_free_text_summary(valid, output_dir)
    q8_other = free_text[free_text["question"].eq("Q8")]
    q10_other = free_text[free_text["question"].eq("Q10")]
    return {
        "descriptive_rows": int(len(descriptive)),
        "q7_q8_inconsistency_n": int(len(inconsistency)),
        "q8_other_n": int(len(q8_other)),
        "q8_other_nonempty_n": int(q8_other["text"].astype(str).str.strip().ne("").sum()),
        "q10_other_n": int(len(q10_other)),
        "q10_other_nonempty_n": int(q10_other["text"].astype(str).str.strip().ne("").sum()),
    }


def save_qc_and_report(
    flagged: pd.DataFrame, output_dir: Path, supplemental: dict
) -> None:
    total = int(len(flagged))
    invalid = int(flagged["invalid_main3"].sum())
    valid_count = total - invalid
    missing_rate = round((invalid / total * 100.0), 2) if total else 0.0

    gate = analysis_gate(valid_count, missing_rate)
    is_main_analysis = int(gate == "主解析（有効80以上）")
    is_exploratory = int(gate == "探索的解析（有効60-79）")
    is_descriptive_only = int(gate.startswith("記述中心"))
    valid = flagged[~flagged["invalid_main3"]].copy()
    dominance = reason_dominance(valid)
    q7q9 = summarize_q7_q9(valid)

    design_primary = sample_size_requirements(e=SAMPLE_SIZE_DESIGN_E)
    design_sens_tight = sample_size_requirements(e=0.10)
    design_sens_loose = sample_size_requirements(e=0.15)

    qc = pd.DataFrame(
        [
            {"metric": "total_responses", "value": total},
            {"metric": "valid_responses", "value": valid_count},
            {"metric": "invalid_responses", "value": invalid},
            {"metric": "main_missing_rate_pct", "value": missing_rate},
            {"metric": "analysis_gate_label", "value": gate},
            {"metric": "analysis_gate_main", "value": is_main_analysis},
            {"metric": "analysis_gate_exploratory", "value": is_exploratory},
            {"metric": "analysis_gate_descriptive_only", "value": is_descriptive_only},
            {
                "metric": "missing_q7_bath_heater_status_n",
                "value": int(flagged["missing_q7_bath_heater_status"].sum()),
            },
            {
                "metric": "missing_q8_reason_codes_n",
                "value": int(flagged["missing_q8_reason_codes"].sum()),
            },
            {
                "metric": "missing_q11_bathroom_cold_7pt_n",
                "value": int(flagged["missing_q11_bathroom_cold_7pt"].sum()),
            },
            {
                "metric": "q7_q8_inconsistency_n",
                "value": supplemental["q7_q8_inconsistency_n"],
            },
            {"metric": "reason_target_n", "value": dominance["reason_target_n"]},
            {"metric": "no_need_pct", "value": dominance["no_need_pct"]},
            {"metric": "barrier_pct", "value": dominance["barrier_pct"]},
            {"metric": "gap_pp", "value": dominance["gap_pp"]},
            {"metric": "dominant_group", "value": dominance["dominant_group"]},
            {"metric": "q7q9_target_n", "value": q7q9["target_n"]},
            {"metric": "q7q9_test_method", "value": q7q9["test_method"]},
            {
                "metric": "q7q9_test_p",
                "value": "" if q7q9["test_p"] is None else round(q7q9["test_p"], 6),
            },
            {
                "metric": "q7q9_small_expected_cell",
                "value": ""
                if q7q9["small_expected_cell"] is None
                else int(q7q9["small_expected_cell"]),
            },
            {"metric": "design_n0_e12", "value": round(design_primary["n0"], 2)},
            {"metric": "design_n0_ceil_e12", "value": design_primary["n0_ceil"]},
            {"metric": "design_n_valid_e12", "value": design_primary["n_valid"]},
            {"metric": "design_n_collected_e12", "value": design_primary["n_collected"]},
            {
                "metric": "design_n_operational_e12",
                "value": design_primary["n_operational"],
            },
            {
                "metric": "design_n_collected_e10",
                "value": design_sens_tight["n_collected"],
            },
            {
                "metric": "design_n_collected_e15",
                "value": design_sens_loose["n_collected"],
            },
        ]
    )
    qc.to_csv(output_dir / "qc_summary.csv", index=False, encoding="utf-8-sig")

    report_lines = [
        "# 五所川原市 紙アンケート集計レポート",
        "",
        "- 目的: 配布版Q1-Q11の初期解析、必須3表出力、品質ゲート確認",
        "- 解析位置づけ: 五所川原市の便宜抽出サンプル内での内訳把握",
        "- 注意: 県全体推定や因果推定は行わない",
        "- 記述ポリシー: `docs/rules/statistical_reporting_policy.md`",
        f"- 総票数: {total}",
        f"- 有効票数: {valid_count}",
        f"- 無効票数: {invalid}",
        f"- 主要欠損率: {missing_rate}%",
        f"- 解析ゲート: {gate}",
        f"- Q7/Q8不整合票: {supplemental['q7_q8_inconsistency_n']}",
        "",
        "## 目標回答数の計算再現（固定前提）",
        "",
        "- 入力: E=0.12, p=0.5, deff=1.2, invalid=0.15",
        f"- n0={design_primary['n0']:.2f} -> {design_primary['n0_ceil']}",
        f"- n_valid={design_primary['n_valid']}",
        f"- n_collected={design_primary['n_collected']}",
        f"- n_operational={design_primary['n_operational']}",
        "",
        "## 感度テスト（許容誤差E）",
        "",
        f"- E=0.10: n_collected={design_sens_tight['n_collected']}",
        f"- E=0.15: n_collected={design_sens_loose['n_collected']}",
        "",
        "## Q7-Q9 記述統計",
        "",
        f"- 対象票数: {q7q9['target_n']}",
        f"- 検定法: {q7q9['test_method']}",
        (
            "- p値: 記述統計のみ"
            if q7q9["test_p"] is None
            else f"- p値: {q7q9['test_p']:.6f}"
        ),
        "- 行割合は95%CI（Wilson）を併記",
    ]
    if q7q9["rows"]:
        report_lines.extend(
            [
                "",
                "| 群 | Q9カテゴリ | n | 分母 | 割合(%) | 95%CI(%) |",
                "| --- | --- | ---: | ---: | ---: | --- |",
            ]
        )
        for row in q7q9["rows"]:
            report_lines.append(
                "| "
                + f"{row['group']} | {row['q9_category']} | {row['count']} | {row['row_total']} | "
                + f"{row['pct']:.2f} | [{row['ci95_lo_pct']:.2f}, {row['ci95_hi_pct']:.2f}] |"
            )
    report_lines.extend(
        [
            "",
            "## 優勢判定（不要群 vs 障壁群）",
            "",
            f"- 判定対象票数: {dominance['reason_target_n']}",
            f"- 不要群割合: {dominance['no_need_pct']}%",
            f"- 障壁群割合: {dominance['barrier_pct']}%",
            f"- 差: {dominance['gap_pp']}pp",
            f"- 判定: {dominance['dominant_group']}",
            "",
            "## 自由記述（その他）",
            "",
            f"- Q8その他チェックあり: {supplemental['q8_other_n']}",
            f"- Q8その他の記述あり: {supplemental['q8_other_nonempty_n']}",
            f"- Q10その他チェックあり: {supplemental['q10_other_n']}",
            f"- Q10その他の記述あり: {supplemental['q10_other_nonempty_n']}",
            "- 初期解析では再カテゴリ化せず、`free_text_summary.csv` に原文一覧を出力",
            "",
            "## Q7/Q8不整合票",
            "",
            "- 方針: Q7原票値を主解析に残し、Q8理由の主要集計からは除外",
            "- 補足表: `q7_q8_inconsistency_supplement.csv`",
            "",
            "## 出力ファイル",
            "",
            "- `qc_summary.csv`",
            "- `descriptive_summary.csv`",
            "- `table1_q7_status_x_bathroom_cold_7pt.csv`",
            "- `table2_q7_status_x_central_heating.csv`",
            "- `table3_q8_reason_x_housing_type.csv`",
            "- `q7_q8_inconsistency_supplement.csv`",
            "- `free_text_summary.csv`",
        ]
    )
    (output_dir / "tabulation_report.md").write_text(
        "\n".join(report_lines), encoding="utf-8"
    )


def main() -> None:
    args = parse_args()
    input_csv = Path(args.input_csv)
    output_dir = Path(args.output_dir) if args.output_dir else default_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)

    raw = read_csv_with_fallback(input_csv)
    normalized = normalize_dataframe(raw)
    flagged = derive_validity_flags(normalized)
    labeled = add_label_columns(flagged)
    valid = labeled[~labeled["invalid_main3"]].copy()

    save_crosstabs(valid, output_dir)
    supplemental = save_supplemental_outputs(labeled, output_dir)
    save_qc_and_report(labeled, output_dir, supplemental)
    print(output_dir)


if __name__ == "__main__":
    main()
