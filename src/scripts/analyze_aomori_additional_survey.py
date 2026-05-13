#!/usr/bin/env python3
"""Generate additional descriptive analyses for the Aomori paper survey."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

try:
    from scipy.stats import chi2_contingency, fisher_exact
except Exception:  # pragma: no cover - optional dependency
    chi2_contingency = None
    fisher_exact = None

from tabulate_aomori_paper_survey import (
    Q8_REASON_LABELS,
    add_label_columns,
    derive_validity_flags,
    normalize_dataframe,
    parse_reason_codes,
    read_csv_with_fallback,
    wilson_ci,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = REPO_ROOT / "data" / "processed" / "aomori_survey_responses_reviewed_confirmed.csv"
SIGNAL_DIFF_PP = 10.0

COLD_OUTCOMES = [
    ("bathroom_cold_5_7", "浴室寒さ5-7"),
    ("dressingroom_cold_5_7", "脱衣所寒さ5-7"),
]

PROFILE_GROUPS = [
    ("age60_group", "年齢（60歳区分）", ["60歳未満", "60歳以上"]),
    ("age70_group", "年齢（70歳区分）", ["70歳未満", "70歳以上"]),
    ("housing_group", "住宅種別", ["集合住宅", "戸建"]),
    ("building30_group", "築年区分", ["30年未満", "30年以上"]),
    ("tenure_group", "所有形態", ["賃貸", "持家"]),
]

EQUIPMENT_GROUPS = [
    ("bath_heater_use_group", "浴室暖房使用", ["なし", "あり"]),
    ("bath_heater_any_group", "浴室暖房設置", ["なし", "あり"]),
    ("central_any_group", "セントラル暖房", ["なし", "あり"]),
    ("stove_group", "ストーブ", ["なし", "あり"]),
    ("no_alt_group", "代替暖房なし", ["なし", "あり"]),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate additional descriptive analyses for Aomori survey."
    )
    parser.add_argument(
        "--input-csv",
        default=str(DEFAULT_INPUT),
        help="Path to confirmed survey CSV.",
    )
    parser.add_argument(
        "--output-dir",
        help=(
            "Path to output directory. Defaults to "
            "outputs/runs/YYYYMMDD_HHMMSS_additional_analysis."
        ),
    )
    return parser.parse_args()


def default_output_dir() -> Path:
    tag = datetime.now().strftime("%Y%m%d_%H%M%S_additional_analysis")
    return REPO_ROOT / "outputs" / "runs" / tag


def bool_label(series: pd.Series) -> pd.Series:
    return series.map({True: "あり", False: "なし"}).fillna("不明")


def contains_code(series: pd.Series, code: int) -> pd.Series:
    return series.fillna("").astype(str).apply(lambda value: code in parse_reason_codes(value))


def prepare_valid_data(input_csv: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = read_csv_with_fallback(input_csv)
    normalized = normalize_dataframe(raw)
    flagged = add_label_columns(derive_validity_flags(normalized))
    valid = flagged[~flagged["invalid_main3"]].copy()

    valid["bathroom_cold_5_7"] = valid["q11_bathroom_cold_7pt"].between(5, 7)
    valid["dressingroom_cold_5_7"] = valid["q11_dressingroom_cold_7pt"].between(5, 7)
    valid["age60_group"] = valid["q1_age_group"].apply(
        lambda x: "60歳未満" if x in [1, 2, 3, 4] else ("60歳以上" if x in [5, 6, 7, 8] else "不明")
    )
    valid["age70_group"] = valid["q1_age_group"].apply(
        lambda x: "70歳未満" if x in [1, 2, 3, 4, 5] else ("70歳以上" if x in [6, 7, 8] else "不明")
    )
    valid["housing_group"] = valid["q2_housing_type"].map({1: "戸建", 2: "集合住宅"}).fillna("不明")
    valid["building30_group"] = valid["q3_building_age_band"].apply(
        lambda x: "30年未満" if x in [1, 2, 3] else ("30年以上" if x == 4 else "不明")
    )
    valid["tenure_group"] = valid["q4_tenure"].map({1: "持家", 2: "賃貸"}).fillna("不明")
    valid["bath_heater_use"] = valid["q7_bath_heater_status"].eq(1)
    valid["bath_heater_any"] = valid["q7_bath_heater_status"].isin([1, 2])
    valid["central_any"] = valid["q9_central_heating_use"].isin([1, 2])
    valid["stove"] = contains_code(valid["q10_alt_heating_types"], 1)
    valid["no_alt"] = contains_code(valid["q10_alt_heating_types"], 5)
    for bool_col, group_col in [
        ("bath_heater_use", "bath_heater_use_group"),
        ("bath_heater_any", "bath_heater_any_group"),
        ("central_any", "central_any_group"),
        ("stove", "stove_group"),
        ("no_alt", "no_alt_group"),
    ]:
        valid[group_col] = bool_label(valid[bool_col])

    valid["equipment_combination"] = valid.apply(equipment_combination_label, axis=1)
    return flagged, valid


def equipment_combination_label(row: pd.Series) -> str:
    parts = []
    if row["bath_heater_use"]:
        parts.append("浴室暖房使用")
    elif row["bath_heater_any"]:
        parts.append("浴室暖房設置未使用")
    if row["central_any"]:
        parts.append("セントラルあり")
    if row["stove"]:
        parts.append("ストーブあり")
    if row["no_alt"]:
        parts.append("代替暖房なし")
    if not parts:
        return "主要設備なし/未回答"
    return "+".join(parts)


def format_p_value(p_value: float | None) -> str:
    if p_value is None or pd.isna(p_value):
        return ""
    if p_value < 0.0001:
        return "p<0.0001"
    if p_value < 0.001:
        return f"{p_value:.4f}"
    if p_value < 0.2:
        return f"{p_value:.3f}"
    if p_value <= 0.99:
        return f"{p_value:.2f}"
    return "p>0.99"


def test_table(table: pd.DataFrame) -> dict:
    if table.empty or table.shape[0] < 2 or table.shape[1] < 2:
        return {"test_method": "判定不可", "p_value": None, "p_value_formatted": "", "small_expected_cell": ""}
    if table.shape == (2, 2) and fisher_exact is not None:
        result = fisher_exact(table.to_numpy())
        p_value = float(result.pvalue) if hasattr(result, "pvalue") else float(result[1])
        small_expected = ""
        if chi2_contingency is not None:
            try:
                _, _, _, expected = chi2_contingency(table.to_numpy())
                small_expected = bool((expected < 5.0).any())
            except Exception:
                small_expected = ""
        return {
            "test_method": "Fisher exact",
            "p_value": p_value,
            "p_value_formatted": format_p_value(p_value),
            "small_expected_cell": small_expected,
        }
    if chi2_contingency is None:
        return {"test_method": "χ2検定不可", "p_value": None, "p_value_formatted": "", "small_expected_cell": ""}
    try:
        _, p_value, _, expected = chi2_contingency(table.to_numpy())
        return {
            "test_method": "χ2検定",
            "p_value": float(p_value),
            "p_value_formatted": format_p_value(float(p_value)),
            "small_expected_cell": bool((expected < 5.0).any()),
        }
    except Exception:
        return {"test_method": "検定計算不可", "p_value": None, "p_value_formatted": "", "small_expected_cell": ""}


def summarize_binary_by_group(
    df: pd.DataFrame,
    outcome_col: str,
    outcome_label: str,
    group_col: str,
    group_label: str,
    order: Iterable[str],
    package: str,
) -> tuple[pd.DataFrame, dict]:
    target = df[df[group_col].isin(order)].copy()
    rows = []
    for category in order:
        subset = target[target[group_col].eq(category)]
        denom = int(len(subset))
        events = int(subset[outcome_col].sum())
        pct = events / denom * 100.0 if denom else 0.0
        ci_lo, ci_hi = wilson_ci(events, denom)
        rows.append(
            {
                "analysis_package": package,
                "outcome": outcome_col,
                "outcome_label": outcome_label,
                "group_variable": group_col,
                "group_label": group_label,
                "group_category": category,
                "event_n": events,
                "denominator": denom,
                "pct": round(pct, 2),
                "ci95_lo_pct": round(ci_lo * 100.0, 2),
                "ci95_hi_pct": round(ci_hi * 100.0, 2),
            }
        )
    summary = pd.DataFrame(rows)
    table = pd.crosstab(target[group_col], target[outcome_col]).reindex(index=list(order), fill_value=0)
    for column in [False, True]:
        if column not in table.columns:
            table[column] = 0
    table = table.reindex(columns=[False, True], fill_value=0)
    test = test_table(table)
    first = summary.iloc[0]
    second = summary.iloc[1]
    diff_pp = float(second["pct"]) - float(first["pct"])
    contrast = {
        "analysis_package": package,
        "analysis_item": f"{outcome_label} × {group_label}",
        "contrast": f"{second['group_category']} - {first['group_category']}",
        "difference_pp": round(diff_pp, 2),
        "abs_difference_pp": round(abs(diff_pp), 2),
        "min_group_n": int(summary["denominator"].min()),
        "test_method": test["test_method"],
        "p_value": test["p_value"],
        "p_value_formatted": test["p_value_formatted"],
        "small_expected_cell": test["small_expected_cell"],
        "interpretation": interpretation_text(outcome_label, group_label, first, second, diff_pp, test),
    }
    contrast.update(reportability(contrast, high_relevance=True))
    return summary, contrast


def interpretation_text(
    outcome_label: str,
    group_label: str,
    first: pd.Series,
    second: pd.Series,
    diff_pp: float,
    test: dict,
) -> str:
    direction = "高い" if diff_pp > 0 else "低い"
    return (
        f"{outcome_label}の割合は、{second['group_category']}で{second['pct']:.2f}% "
        f"({second['event_n']}/{second['denominator']})、{first['group_category']}で"
        f"{first['pct']:.2f}% ({first['event_n']}/{first['denominator']})であり、"
        f"差は{diff_pp:.2f}ppだった。{group_label}との関連は観察研究上の関連として解釈し、"
        f"p値（{test['test_method']}, {test['p_value_formatted'] or '未算出'}）は補助情報とする。"
        f"{second['group_category']}側が{abs(diff_pp):.2f}pp{direction}方向である。"
    )


def reportability(contrast: dict, high_relevance: bool) -> dict:
    abs_diff = float(contrast["abs_difference_pp"])
    min_n = int(contrast["min_group_n"])
    small_expected = contrast["small_expected_cell"] is True
    if min_n < 5:
        category = "報告保留"
        reason = "最小セル数が5未満で、この規模の調査では安定した比較として扱いにくい。"
    elif abs_diff >= SIGNAL_DIFF_PP and min_n >= 20 and high_relevance and not small_expected:
        category = "主要に報告"
        reason = "差が10pp以上で、セル数も比較的安定しており、研究目的に直結する。"
    elif abs_diff >= SIGNAL_DIFF_PP and min_n >= 10:
        category = "補助的に報告"
        reason = "差は10pp以上だが、CI幅または小セルの可能性があり補助的な提示が妥当。"
    elif abs_diff >= SIGNAL_DIFF_PP:
        category = "探索的所見"
        reason = "差は10pp以上だが、小セルまたは不確実性が大きく探索的に留める。"
    else:
        category = "報告保留"
        reason = "差が10pp未満で、今回の追加解析で強調する情報量は限定的。"
    return {"report_category": category, "reportability_reason": reason}


def cold_profile(valid: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    summaries = []
    assessments = []
    for outcome_col, outcome_label in COLD_OUTCOMES:
        for group_col, group_label, order in PROFILE_GROUPS:
            summary, contrast = summarize_binary_by_group(
                valid, outcome_col, outcome_label, group_col, group_label, order, "寒さプロファイル"
            )
            summaries.append(summary)
            assessments.append(contrast)
    return pd.concat(summaries, ignore_index=True), pd.DataFrame(assessments)


def equipment_x_cold(valid: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    summaries = []
    assessments = []
    for outcome_col, outcome_label in COLD_OUTCOMES:
        for group_col, group_label, order in EQUIPMENT_GROUPS:
            summary, contrast = summarize_binary_by_group(
                valid, outcome_col, outcome_label, group_col, group_label, order, "設備と寒さ"
            )
            summaries.append(summary)
            assessments.append(contrast)
    return pd.concat(summaries, ignore_index=True), pd.DataFrame(assessments)


def reason_by_profile(valid: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    target = valid[valid["need_q8"] & ~valid["q7_q8_inconsistency_flag"]].copy()
    target["reason_codes_list"] = target["q8_reason_codes"].apply(parse_reason_codes)
    target["no_need_reason"] = target["reason_codes_list"].apply(lambda xs: 1 in xs)
    target["barrier_reason"] = target["reason_codes_list"].apply(lambda xs: any(code in xs for code in [2, 3, 4, 5, 6, 7]))
    rows = []
    assessments = []
    reason_metrics = [
        ("no_need_reason", "不要群（理由1）"),
        ("barrier_reason", "障壁群（理由2-7）"),
    ]
    for code, label in Q8_REASON_LABELS.items():
        col = f"q8_reason_{code}"
        target[col] = target["reason_codes_list"].apply(lambda xs, c=code: c in xs)
        reason_metrics.append((col, label))

    groups = PROFILE_GROUPS + [("bathroom_cold_group", "浴室寒さ", ["寒くない/中立", "寒い"])]
    target["bathroom_cold_group"] = target["bathroom_cold_5_7"].map({True: "寒い", False: "寒くない/中立"})
    for metric_col, metric_label in reason_metrics:
        for group_col, group_label, order in groups:
            summary, contrast = summarize_binary_by_group(
                target, metric_col, metric_label, group_col, group_label, order, "低設置/未使用理由"
            )
            rows.append(summary)
            contrast["interpretation"] += " Q8は複数回答であり、割合の合計は100%にならない。"
            contrast.update(reportability(contrast, high_relevance=metric_col in ["no_need_reason", "barrier_reason"]))
            assessments.append(contrast)
    return pd.concat(rows, ignore_index=True), pd.DataFrame(assessments)


def equipment_combination_summary(valid: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    assessments = []
    combos = valid["equipment_combination"].value_counts()
    top_combos = list(combos[combos >= 5].index)
    for combo in top_combos:
        valid[f"combo_{combo}"] = valid["equipment_combination"].eq(combo)
        group_col = f"combo_{combo}"
        valid[f"{group_col}_group"] = bool_label(valid[group_col])
        for outcome_col, outcome_label in COLD_OUTCOMES:
            summary, contrast = summarize_binary_by_group(
                valid,
                outcome_col,
                outcome_label,
                f"{group_col}_group",
                f"設備組み合わせ: {combo}",
                ["なし", "あり"],
                "設備組み合わせ",
            )
            rows.append(summary)
            contrast["interpretation"] += " 組み合わせ解析はセルが小さくなりやすいため、過度な比較は避ける。"
            contrast.update(reportability(contrast, high_relevance=False))
            assessments.append(contrast)
    return pd.concat(rows, ignore_index=True), pd.DataFrame(assessments)


def recode_free_text(valid: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in valid.iterrows():
        q8_codes = parse_reason_codes(str(row["q8_reason_codes"]))
        if 8 in q8_codes:
            text = str(row["q8_other_text"]).strip()
            rows.append(
                {
                    "question": "Q8",
                    "response_id": row["response_id"],
                    "text": text,
                    "supplement_category": classify_free_text("Q8", text),
                    "included_in_main_reason_summary": int(row["need_q8"] and not row["q7_q8_inconsistency_flag"]),
                    "interpretation_note": "自由記述は仮説生成・文脈補足であり、主集計とは分けて扱う。",
                }
            )
        q10_codes = parse_reason_codes(str(row["q10_alt_heating_types"]))
        if 4 in q10_codes:
            text = str(row["q10_other_text"]).strip()
            rows.append(
                {
                    "question": "Q10",
                    "response_id": row["response_id"],
                    "text": text,
                    "supplement_category": classify_free_text("Q10", text),
                    "included_in_main_reason_summary": "",
                    "interpretation_note": "自由記述は仮説生成・文脈補足であり、主集計とは分けて扱う。",
                }
            )
    return pd.DataFrame(rows)


def classify_free_text(question: str, text: str) -> str:
    if not text:
        return "その他チェックあり・記述なし"
    if question == "Q10":
        if "ストーブ" in text:
            return "ストーブ詳細"
        if "パネル" in text:
            return "パネルヒーター"
        return "その他設備"
    if any(token in text for token in ["説明", "何ですか", "わから"]):
        return "情報不足・認知不足"
    if any(token in text for token in ["自己負担", "賃貸", "費用"]):
        return "費用・所有制約"
    if any(token in text for token in ["古い", "設備投資", "建て", "設置していない", "後悔", "元から", "もともと"]):
        return "建築時期・後付け制約"
    if any(token in text for token in ["十分", "寒いのが気にならない", "あたたかい", "暖房機"]):
        return "不要・代替暖房で充足"
    return "その他文脈"


def seven_point_distribution(valid: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for variable, label in [
        ("q11_bathroom_cold_7pt", "浴室寒さ7段階"),
        ("q11_dressingroom_cold_7pt", "脱衣所寒さ7段階"),
    ]:
        total = int(valid[variable].notna().sum())
        for score in range(1, 8):
            count = int(valid[variable].eq(score).sum())
            pct = count / total * 100.0 if total else 0.0
            rows.append(
                {
                    "variable": variable,
                    "variable_label": label,
                    "score": score,
                    "count": count,
                    "denominator": total,
                    "pct": round(pct, 2),
                }
            )
    return pd.DataFrame(rows)


def seven_point_by_group(valid: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    assessments = []
    variables = [
        ("q11_bathroom_cold_7pt", "浴室寒さ7段階"),
        ("q11_dressingroom_cold_7pt", "脱衣所寒さ7段階"),
    ]
    for variable, variable_label in variables:
        for group_col, group_label, order in PROFILE_GROUPS:
            target = valid[valid[group_col].isin(order)].copy()
            table = pd.crosstab(target[group_col], target[variable]).reindex(index=order, fill_value=0)
            table = table.reindex(columns=list(range(1, 8)), fill_value=0)
            test = test_table(table)
            pct_by_group = table.div(table.sum(axis=1).replace(0, pd.NA), axis=0).fillna(0) * 100.0
            max_diff = 0.0
            if len(order) == 2:
                max_diff = float((pct_by_group.loc[order[1]] - pct_by_group.loc[order[0]]).abs().max())
            for category in order:
                denom = int(table.loc[category].sum())
                for score in range(1, 8):
                    count = int(table.loc[category, score])
                    pct = count / denom * 100.0 if denom else 0.0
                    rows.append(
                        {
                            "variable": variable,
                            "variable_label": variable_label,
                            "group_variable": group_col,
                            "group_label": group_label,
                            "group_category": category,
                            "score": score,
                            "count": count,
                            "denominator": denom,
                            "pct": round(pct, 2),
                            "test_method": test["test_method"],
                            "p_value": test["p_value"],
                            "p_value_formatted": test["p_value_formatted"],
                            "small_expected_cell": test["small_expected_cell"],
                        }
                    )
            contrast = {
                "analysis_package": "寒さ7段階分布",
                "analysis_item": f"{variable_label} × {group_label}",
                "contrast": f"{order[1]} - {order[0]}（最大カテゴリ差）",
                "difference_pp": round(max_diff, 2),
                "abs_difference_pp": round(max_diff, 2),
                "min_group_n": int(table.sum(axis=1).min()),
                "test_method": test["test_method"],
                "p_value": test["p_value"],
                "p_value_formatted": test["p_value_formatted"],
                "small_expected_cell": test["small_expected_cell"],
                "interpretation": (
                    f"{variable_label}の7段階分布を{group_label}で比較した。"
                    f"最大カテゴリ差は{max_diff:.2f}ppで、p値（{test['test_method']}, "
                    f"{test['p_value_formatted'] or '未算出'}）は分布差の補助情報として扱う。"
                ),
            }
            contrast.update(reportability(contrast, high_relevance=False))
            assessments.append(contrast)
    return pd.DataFrame(rows), pd.DataFrame(assessments)


def write_outputs(output_dir: Path, outputs: dict[str, pd.DataFrame]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for filename, df in outputs.items():
        df.to_csv(output_dir / filename, index=False, encoding="utf-8-sig")


def build_qc(flagged: pd.DataFrame, valid: pd.DataFrame, reason_target_n: int) -> pd.DataFrame:
    total = int(len(flagged))
    invalid = int(flagged["invalid_main3"].sum())
    return pd.DataFrame(
        [
            {"metric": "total_responses", "value": total},
            {"metric": "valid_responses", "value": int(len(valid))},
            {"metric": "invalid_responses", "value": invalid},
            {"metric": "bathroom_cold_5_7_n", "value": int(valid["bathroom_cold_5_7"].sum())},
            {"metric": "dressingroom_cold_5_7_n", "value": int(valid["dressingroom_cold_5_7"].sum())},
            {"metric": "q7_q8_inconsistency_n", "value": int(flagged["q7_q8_inconsistency_flag"].sum())},
            {"metric": "q8_reason_target_n", "value": reason_target_n},
        ]
    )


def save_figures(valid: pd.DataFrame, reason_target: pd.DataFrame, output_dir: Path) -> None:
    figures_dir = output_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    plt.rcParams["font.sans-serif"] = ["Yu Gothic", "Meiryo", "MS Gothic", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    dist = seven_point_distribution(valid)
    pivot = dist.pivot(index="score", columns="variable_label", values="pct")
    ax = pivot.plot(kind="bar", figsize=(8, 4))
    ax.set_xlabel("寒さ尺度（1=非常に暖かい, 7=非常に寒い）")
    ax.set_ylabel("割合(%)")
    ax.set_title("浴室・脱衣所の寒さ7段階分布")
    plt.tight_layout()
    plt.savefig(figures_dir / "cold_7pt_distribution.png", dpi=150)
    plt.close()

    q7 = valid.groupby("q7_status_label")["bathroom_cold_5_7"].mean().mul(100).sort_index()
    ax = q7.plot(kind="bar", figsize=(8, 4))
    ax.set_ylabel("浴室寒さ5-7割合(%)")
    ax.set_title("Q7別の浴室寒さ割合")
    plt.tight_layout()
    plt.savefig(figures_dir / "q7_bathroom_cold_rate.png", dpi=150)
    plt.close()

    equipment_rates = {
        "浴室暖房使用": valid.loc[valid["bath_heater_use"], "bathroom_cold_5_7"].mean() * 100,
        "浴室暖房なし": valid.loc[~valid["bath_heater_use"], "bathroom_cold_5_7"].mean() * 100,
        "セントラルあり": valid.loc[valid["central_any"], "bathroom_cold_5_7"].mean() * 100,
        "ストーブあり": valid.loc[valid["stove"], "bathroom_cold_5_7"].mean() * 100,
        "代替暖房なし": valid.loc[valid["no_alt"], "bathroom_cold_5_7"].mean() * 100,
    }
    ax = pd.Series(equipment_rates).plot(kind="bar", figsize=(8, 4))
    ax.set_ylabel("浴室寒さ5-7割合(%)")
    ax.set_title("主要設備別の浴室寒さ割合")
    plt.tight_layout()
    plt.savefig(figures_dir / "equipment_bathroom_cold_rate.png", dpi=150)
    plt.close()

    code_counts = {}
    code_lists = reason_target["q8_reason_codes"].apply(parse_reason_codes)
    denom = len(reason_target)
    for code, label in Q8_REASON_LABELS.items():
        code_counts[label] = code_lists.apply(lambda xs, c=code: c in xs).sum() / denom * 100 if denom else 0.0
    ax = pd.Series(code_counts).plot(kind="bar", figsize=(9, 4))
    ax.set_ylabel("多重回答率(%)")
    ax.set_title("Q8理由コードの多重回答率")
    plt.tight_layout()
    plt.savefig(figures_dir / "q8_reason_rate.png", dpi=150)
    plt.close()


def top_assessments(assessment: pd.DataFrame, category: str | None = None, limit: int = 8) -> pd.DataFrame:
    df = assessment.copy()
    if category:
        df = df[df["report_category"].eq(category)]
    return df.sort_values(["abs_difference_pp", "min_group_n"], ascending=[False, False]).head(limit)


def write_report(
    output_dir: Path,
    qc: pd.DataFrame,
    assessment: pd.DataFrame,
    free_text: pd.DataFrame,
) -> None:
    metrics = dict(zip(qc["metric"], qc["value"]))
    major = top_assessments(assessment, "主要に報告", 6)
    supportive = top_assessments(assessment, "補助的に報告", 6)
    exploratory = top_assessments(assessment, "探索的所見", 6)

    lines = [
        "# 青森調査 追加解析レポート",
        "",
        "- 目的: 初期解析結果を受け、寒さ、住宅・年齢、設備、未設置/未使用理由の関連を記述的に整理する",
        "- 解析位置づけ: 五所川原市の便宜抽出サンプル内での内訳把握",
        "- 注意: 県全体推定や因果推定は行わない",
        "- 記述ポリシー: `docs/rules/statistical_reporting_policy.md`",
        "- 注目差の基準: 絶対差10pp以上",
        "- p値: 効果量、絶対値、95%CIとセットで補助情報として扱う",
        "",
        "## QC Summary",
        "",
        f"- 有効票数: {metrics['valid_responses']}",
        f"- 浴室寒さ5-7: {metrics['bathroom_cold_5_7_n']}/{metrics['valid_responses']}",
        f"- 脱衣所寒さ5-7: {metrics['dressingroom_cold_5_7_n']}/{metrics['valid_responses']}",
        f"- Q7/Q8不整合票: {metrics['q7_q8_inconsistency_n']}",
        f"- Q8理由集計対象: {metrics['q8_reason_target_n']}",
        "",
        "## 統計学的解釈と報告価値",
        "",
        "各比較では、群間の絶対差、95%CI、p値、最小セル数、小セル注記を併記した。p値は結果を二分するためではなく、観察された差の不確実性を補助的に把握するために用いる。",
        "",
        "### 主要に報告する候補",
        "",
    ]
    lines.extend(assessment_table_lines(major))
    lines.extend(
        [
            "",
            "### 補助的に報告する候補",
            "",
        ]
    )
    lines.extend(assessment_table_lines(supportive))
    lines.extend(
        [
            "",
            "### 探索的所見",
            "",
        ]
    )
    lines.extend(assessment_table_lines(exploratory))
    lines.extend(
        [
            "",
            "## 自由記述補助分類",
            "",
            f"- 自由記述補助分類の対象行数: {len(free_text)}",
            "- 自由記述は主集計へ統合せず、仮説生成・文脈補足として扱う。",
            "",
        ]
    )
    if not free_text.empty:
        category_counts = free_text["supplement_category"].value_counts().reset_index()
        category_counts.columns = ["補助カテゴリ", "件数"]
        lines.extend(["| 補助カテゴリ | 件数 |", "| --- | ---: |"])
        for _, row in category_counts.iterrows():
            lines.append(f"| {row['補助カテゴリ']} | {row['件数']} |")
    lines.extend(
        [
            "",
            "## 出力ファイル",
            "",
            "- `additional_qc_summary.csv`",
            "- `cold_profile_by_group.csv`",
            "- `equipment_x_cold_summary.csv`",
            "- `reason_by_profile_summary.csv`",
            "- `equipment_combination_summary.csv`",
            "- `free_text_recoding_supplement.csv`",
            "- `cold_7pt_by_group.csv`",
            "- `reportability_assessment.csv`",
            "- `figures/*.png`",
        ]
    )
    (output_dir / "additional_analysis_report.md").write_text("\n".join(lines), encoding="utf-8")


def assessment_table_lines(df: pd.DataFrame) -> list[str]:
    if df.empty:
        return ["該当なし。"]
    lines = [
        "| 解析項目 | 差(pp) | p値 | 報告区分 | 評価理由 |",
        "| --- | ---: | --- | --- | --- |",
    ]
    for _, row in df.iterrows():
        lines.append(
            "| "
            + f"{row['analysis_item']} | {row['difference_pp']:.2f} | "
            + f"{row['p_value_formatted'] or ''} | {row['report_category']} | "
            + f"{row['reportability_reason']} |"
        )
    return lines


def main() -> None:
    args = parse_args()
    input_csv = Path(args.input_csv)
    output_dir = Path(args.output_dir) if args.output_dir else default_output_dir()

    flagged, valid = prepare_valid_data(input_csv)
    reason_target = valid[valid["need_q8"] & ~valid["q7_q8_inconsistency_flag"]].copy()

    cold_summary, cold_assessment = cold_profile(valid)
    equipment_summary, equipment_assessment = equipment_x_cold(valid)
    reason_summary, reason_assessment = reason_by_profile(valid)
    combo_summary, combo_assessment = equipment_combination_summary(valid)
    free_text = recode_free_text(valid)
    seven_dist = seven_point_distribution(valid)
    seven_by_group, seven_assessment = seven_point_by_group(valid)
    assessment = pd.concat(
        [
            cold_assessment,
            equipment_assessment,
            reason_assessment,
            combo_assessment,
            seven_assessment,
        ],
        ignore_index=True,
    )
    qc = build_qc(flagged, valid, int(len(reason_target)))

    write_outputs(
        output_dir,
        {
            "additional_qc_summary.csv": qc,
            "cold_profile_by_group.csv": cold_summary,
            "equipment_x_cold_summary.csv": equipment_summary,
            "reason_by_profile_summary.csv": reason_summary,
            "equipment_combination_summary.csv": combo_summary,
            "free_text_recoding_supplement.csv": free_text,
            "cold_7pt_distribution.csv": seven_dist,
            "cold_7pt_by_group.csv": seven_by_group,
            "reportability_assessment.csv": assessment,
        },
    )
    save_figures(valid, reason_target, output_dir)
    write_report(output_dir, qc, assessment, free_text)
    print(output_dir)


if __name__ == "__main__":
    main()
