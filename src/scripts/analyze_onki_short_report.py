#!/usr/bin/env python3
"""Generate manuscript tables and Figure 1 for the ONKI short report."""

from __future__ import annotations

import argparse
import json
import platform
from datetime import datetime
from pathlib import Path
from typing import Callable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from tabulate_aomori_paper_survey import (
    add_label_columns,
    derive_validity_flags,
    normalize_dataframe,
    parse_reason_codes,
    read_csv_with_fallback,
    wilson_ci,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = (
    REPO_ROOT
    / "data"
    / "processed"
    / "aomori_survey_responses_reviewed_confirmed.csv"
)
DEFAULT_COLLECTION_SUMMARY = (
    REPO_ROOT / "data" / "processed" / "aomori_survey_collection_summary.csv"
)

REASON_DEFINITIONS: list[tuple[str, str, Callable[[set[int]], bool]]] = [
    ("no_need", "不要（理由1）", lambda codes: 1 in codes),
    ("barrier", "障壁（理由2-7）", lambda codes: bool(codes.intersection(range(2, 8)))),
    ("cost", "費用系（理由2-3）", lambda codes: bool(codes.intersection({2, 3}))),
    (
        "housing_installation",
        "住宅・設置制約系（理由4-5）",
        lambda codes: bool(codes.intersection({4, 5})),
    ),
    (
        "operation_failure",
        "使用方法・故障系（理由6-7）",
        lambda codes: bool(codes.intersection({6, 7})),
    ),
    ("other", "その他（理由8）", lambda codes: 8 in codes),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate ONKI short-report tables, figure, and QC report."
    )
    parser.add_argument("--input-csv", default=str(DEFAULT_INPUT))
    parser.add_argument(
        "--collection-summary",
        default=str(DEFAULT_COLLECTION_SUMMARY),
    )
    parser.add_argument(
        "--output-dir",
        help=(
            "Output directory. Defaults to "
            "outputs/runs/YYYYMMDD_HHMMSS_onki_short_report_analysis."
        ),
    )
    parser.add_argument(
        "--figure-output",
        help="Optional stable copy path for the submission Figure 1 PNG.",
    )
    return parser.parse_args()


def default_output_dir() -> Path:
    tag = datetime.now().strftime("%Y%m%d_%H%M%S_onki_short_report_analysis")
    return REPO_ROOT / "outputs" / "runs" / tag


def proportion_summary(events: int, total: int) -> dict[str, float | int]:
    if total <= 0:
        raise ValueError("The denominator must be positive.")
    lo, hi = wilson_ci(events, total)
    return {
        "event_n": events,
        "denominator": total,
        "pct": round(events / total * 100.0, 2),
        "ci95_lo_pct": round(lo * 100.0, 2),
        "ci95_hi_pct": round(hi * 100.0, 2),
    }


def newcombe_difference(
    events_a: int,
    total_a: int,
    events_b: int,
    total_b: int,
) -> tuple[float, float, float]:
    """Newcombe-Wilson CI for the difference p_a - p_b."""
    p_a = events_a / total_a
    p_b = events_b / total_b
    lo_a, hi_a = wilson_ci(events_a, total_a)
    lo_b, hi_b = wilson_ci(events_b, total_b)
    difference = p_a - p_b
    lower = difference - ((p_a - lo_a) ** 2 + (hi_b - p_b) ** 2) ** 0.5
    upper = difference + ((hi_a - p_a) ** 2 + (p_b - lo_b) ** 2) ** 0.5
    return (
        round(difference * 100.0, 2),
        round(lower * 100.0, 2),
        round(upper * 100.0, 2),
    )


def prepare_analysis_set(input_csv: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = read_csv_with_fallback(input_csv)
    normalized = normalize_dataframe(raw)
    flagged = derive_validity_flags(normalized)
    labeled = add_label_columns(flagged)
    valid = labeled[~labeled["invalid_main3"]].copy()

    valid["bathroom_cold_5_7"] = valid["q11_bathroom_cold_7pt"].isin([5, 6, 7])
    valid["dressingroom_cold_5_7"] = valid["q11_dressingroom_cold_7pt"].isin(
        [5, 6, 7]
    )
    valid["bathroom_cold_group"] = valid["bathroom_cold_5_7"].map(
        {False: "寒さ1-4", True: "寒さ5-7"}
    )
    valid["age_compact"] = pd.cut(
        valid["q1_age_group"].astype(float),
        bins=[0, 3, 4, 5, 8],
        labels=["18-49歳", "50-59歳", "60-69歳", "70歳以上"],
    )
    return flagged, valid


def add_table1_row(
    rows: list[dict[str, object]],
    section: str,
    category: str,
    events: int,
    total: int,
) -> None:
    row: dict[str, object] = {
        "item": section,
        "category": category,
    }
    row.update(proportion_summary(events, total))
    rows.append(row)


def build_table1(valid: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    total = len(valid)

    for category in ["18-49歳", "50-59歳", "60-69歳", "70歳以上"]:
        add_table1_row(
            rows,
            "年齢",
            category,
            int(valid["age_compact"].eq(category).sum()),
            total,
        )

    mappings = [
        (
            "住宅種別",
            "q2_housing_type",
            [(1, "一戸建て"), (2, "集合住宅")],
        ),
        (
            "築年帯",
            "q3_building_age_band",
            [
                ((1, 2, 3), "30年未満"),
                (4, "30年以上"),
                (5, "不明"),
            ],
        ),
        (
            "所有形態",
            "q4_tenure",
            [(1, "持家"), (2, "賃貸"), (99, "無回答")],
        ),
        (
            "浴室窓",
            "q6_window_insulation",
            [
                (1, "二重サッシ・複層ガラス"),
                (2, "単板ガラス"),
                (3, "窓なし"),
                ((4, 99), "不明・無回答"),
            ],
        ),
        (
            "浴室暖房乾燥機",
            "q7_bath_heater_status",
            [
                (1, "設置して使用"),
                (2, "設置しているが未使用"),
                (3, "未設置"),
            ],
        ),
        (
            "セントラル暖房",
            "q9_central_heating_use",
            [
                (1, "24時間使用"),
                (2, "時間限定使用"),
                (3, "不使用"),
                (99, "無回答"),
            ],
        ),
    ]
    for section, column, categories in mappings:
        for codes, label in categories:
            code_list = list(codes) if isinstance(codes, tuple) else [codes]
            add_table1_row(
                rows,
                section,
                label,
                int(valid[column].isin(code_list).sum()),
                total,
            )

    add_table1_row(
        rows,
        "寒さ体感",
        "浴室寒さ5-7",
        int(valid["bathroom_cold_5_7"].sum()),
        total,
    )
    add_table1_row(
        rows,
        "寒さ体感",
        "脱衣所寒さ5-7",
        int(valid["dressingroom_cold_5_7"].sum()),
        total,
    )
    return pd.DataFrame(rows)


def build_reason_summary(valid: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    target = valid[valid["q7_bath_heater_status"].isin([2, 3])].copy()
    target["reason_code_set"] = target["q8_reason_codes"].apply(
        lambda value: set(parse_reason_codes(value))
    )

    rows: list[dict[str, object]] = []
    for key, label, predicate in REASON_DEFINITIONS:
        target[key] = target["reason_code_set"].apply(predicate)
        for group in ["全体", "寒さ1-4", "寒さ5-7"]:
            subset = (
                target
                if group == "全体"
                else target[target["bathroom_cold_group"].eq(group)]
            )
            summary: dict[str, object] = {
                "reason_key": key,
                "reason_label": label,
                "bathroom_cold_group": group,
            }
            summary.update(
                proportion_summary(int(subset[key].sum()), int(len(subset)))
            )
            rows.append(summary)

    summary_df = pd.DataFrame(rows)
    difference_rows = []
    for key, label, _ in REASON_DEFINITIONS:
        low_group = target[target["bathroom_cold_group"].eq("寒さ1-4")]
        high_group = target[target["bathroom_cold_group"].eq("寒さ5-7")]
        difference, ci_lo, ci_hi = newcombe_difference(
            int(high_group[key].sum()),
            len(high_group),
            int(low_group[key].sum()),
            len(low_group),
        )
        difference_rows.append(
            {
                "reason_key": key,
                "reason_label": label,
                "contrast": "寒さ5-7 - 寒さ1-4",
                "difference_pp": difference,
                "difference_ci95_lo_pp": ci_lo,
                "difference_ci95_hi_pp": ci_hi,
            }
        )
    return summary_df, pd.DataFrame(difference_rows)


def equipment_groups(
    valid: pd.DataFrame,
) -> list[tuple[str, str, pd.DataFrame, pd.Series]]:
    return [
        (
            "bath_heater_use",
            "浴室暖房乾燥機使用",
            valid,
            valid["q7_bath_heater_status"].eq(1),
        ),
        (
            "bath_heater_installed",
            "浴室暖房乾燥機設置",
            valid,
            valid["q7_bath_heater_status"].isin([1, 2]),
        ),
        (
            "central_heating",
            "セントラル暖房使用",
            valid[valid["q9_central_heating_use"].isin([1, 2, 3])].copy(),
            valid.loc[
                valid["q9_central_heating_use"].isin([1, 2, 3]),
                "q9_central_heating_use",
            ].isin([1, 2]),
        ),
    ]


def build_table2(valid: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    outcomes = [
        ("bathroom_cold_5_7", "浴室寒さ5-7"),
        ("dressingroom_cold_5_7", "脱衣所寒さ5-7"),
    ]
    for key, label, target, has_equipment in equipment_groups(valid):
        has_equipment = has_equipment.reindex(target.index)
        for outcome, outcome_label in outcomes:
            available = target["q11_bathroom_cold_7pt"].isin(range(1, 8))
            if outcome == "dressingroom_cold_5_7":
                available = target["q11_dressingroom_cold_7pt"].isin(range(1, 8))
            analysis = target[available].copy()
            equipment = has_equipment.loc[analysis.index]
            without = analysis[~equipment]
            with_equipment = analysis[equipment]
            without_events = int(without[outcome].sum())
            with_events = int(with_equipment[outcome].sum())
            without_summary = proportion_summary(without_events, len(without))
            with_summary = proportion_summary(with_events, len(with_equipment))
            difference, ci_lo, ci_hi = newcombe_difference(
                with_events,
                len(with_equipment),
                without_events,
                len(without),
            )
            rows.append(
                {
                    "equipment_key": key,
                    "equipment_label": label,
                    "outcome": outcome,
                    "outcome_label": outcome_label,
                    "without_event_n": without_summary["event_n"],
                    "without_denominator": without_summary["denominator"],
                    "without_pct": without_summary["pct"],
                    "without_ci95_lo_pct": without_summary["ci95_lo_pct"],
                    "without_ci95_hi_pct": without_summary["ci95_hi_pct"],
                    "with_event_n": with_summary["event_n"],
                    "with_denominator": with_summary["denominator"],
                    "with_pct": with_summary["pct"],
                    "with_ci95_lo_pct": with_summary["ci95_lo_pct"],
                    "with_ci95_hi_pct": with_summary["ci95_hi_pct"],
                    "difference_pp": difference,
                    "difference_ci95_lo_pp": ci_lo,
                    "difference_ci95_hi_pp": ci_hi,
                }
            )
    return pd.DataFrame(rows)


def render_figure1(
    reason_summary: pd.DataFrame,
    output_path: Path,
) -> None:
    display_keys = [
        "no_need",
        "barrier",
        "cost",
        "housing_installation",
        "operation_failure",
        "other",
    ]
    english_labels = {
        "no_need": "Unnecessary (reason 1)",
        "barrier": "Any barrier (reasons 2-7)",
        "cost": "Cost (reasons 2-3)",
        "housing_installation": "Housing/installation (reasons 4-5)",
        "operation_failure": "Operation/failure (reasons 6-7)",
        "other": "Other (reason 8)",
    }
    display = reason_summary[
        reason_summary["reason_key"].isin(display_keys)
        & reason_summary["bathroom_cold_group"].isin(["寒さ1-4", "寒さ5-7"])
    ].copy()
    labels = [english_labels[key] for key in display_keys]

    plt.rcParams["font.sans-serif"] = [
        "Yu Gothic",
        "Meiryo",
        "MS Gothic",
        "DejaVu Sans",
    ]
    plt.rcParams["axes.unicode_minus"] = False
    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    y_positions = list(range(len(display_keys)))
    offsets = {"寒さ1-4": -0.12, "寒さ5-7": 0.12}
    colors = {"寒さ1-4": "#4C78A8", "寒さ5-7": "#E45756"}
    legend_labels = {
        "寒さ1-4": "Coldness 1-4",
        "寒さ5-7": "Coldness 5-7",
    }

    for group in ["寒さ1-4", "寒さ5-7"]:
        subset = (
            display[display["bathroom_cold_group"].eq(group)]
            .set_index("reason_key")
            .loc[display_keys]
        )
        x = subset["pct"].astype(float).to_numpy()
        lower = x - subset["ci95_lo_pct"].astype(float).to_numpy()
        upper = subset["ci95_hi_pct"].astype(float).to_numpy() - x
        y = [position + offsets[group] for position in y_positions]
        ax.errorbar(
            x,
            y,
            xerr=[lower, upper],
            fmt="o",
            capsize=3,
            markersize=6,
            linewidth=1.3,
            color=colors[group],
            label=legend_labels[group],
        )

    ax.set_yticks(y_positions)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("Selected responses (%)")
    ax.set_title("Reasons for non-use or non-installation by bathroom coldness")
    ax.grid(axis="x", alpha=0.25)
    ax.legend(title="Bathroom coldness")
    fig.text(
        0.01,
        0.01,
        "Multiple responses were allowed. Points show proportions; "
        "horizontal lines show Wilson 95% confidence intervals.",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def write_markdown_tables(
    table1: pd.DataFrame,
    table2: pd.DataFrame,
    output_dir: Path,
) -> None:
    def as_markdown(data: pd.DataFrame) -> str:
        columns = [str(column) for column in data.columns]
        lines = [
            "| " + " | ".join(columns) + " |",
            "| " + " | ".join("---" for _ in columns) + " |",
        ]
        for row in data.itertuples(index=False, name=None):
            values = [str(value).replace("|", "\\|") for value in row]
            lines.append("| " + " | ".join(values) + " |")
        return "\n".join(lines) + "\n"

    t1 = table1.copy()
    t1["n (%)"] = t1.apply(
        lambda row: f"{row['event_n']}/{row['denominator']} ({row['pct']:.1f})",
        axis=1,
    )
    t1["95%CI"] = t1.apply(
        lambda row: f"[{row['ci95_lo_pct']:.1f}, {row['ci95_hi_pct']:.1f}]",
        axis=1,
    )
    (output_dir / "table1.md").write_text(
        as_markdown(t1[["item", "category", "n (%)", "95%CI"]]),
        encoding="utf-8",
    )

    t2 = table2.copy()
    t2["設備なし n/N (%)"] = t2.apply(
        lambda row: (
            f"{row['without_event_n']}/{row['without_denominator']} "
            f"({row['without_pct']:.1f})"
        ),
        axis=1,
    )
    t2["設備あり n/N (%)"] = t2.apply(
        lambda row: (
            f"{row['with_event_n']}/{row['with_denominator']} "
            f"({row['with_pct']:.1f})"
        ),
        axis=1,
    )
    t2["割合差（pp）[95%CI]"] = t2.apply(
        lambda row: (
            f"{row['difference_pp']:.1f} "
            f"[{row['difference_ci95_lo_pp']:.1f}, "
            f"{row['difference_ci95_hi_pp']:.1f}]"
        ),
        axis=1,
    )
    (output_dir / "table2.md").write_text(
        as_markdown(
            t2[
                [
                    "equipment_label",
                    "outcome_label",
                    "設備なし n/N (%)",
                    "設備あり n/N (%)",
                    "割合差（pp）[95%CI]",
                ]
            ]
        ),
        encoding="utf-8",
    )


def validate_results(
    collection_summary: pd.DataFrame,
    flagged: pd.DataFrame,
    valid: pd.DataFrame,
    reason_summary: pd.DataFrame,
    table2: pd.DataFrame,
) -> dict[str, int | float]:
    collection = collection_summary.set_index("field")["value"]
    prepared = int(collection["questionnaires_prepared"])
    distributed = int(collection["questionnaires_distributed"])
    collected = int(collection["questionnaires_collected"])
    response_rate = collected / distributed * 100.0
    reason_target_n = int(
        reason_summary.loc[
            (reason_summary["reason_key"].eq("barrier"))
            & (reason_summary["bathroom_cold_group"].eq("全体")),
            "denominator",
        ].iloc[0]
    )
    central_rows = table2[table2["equipment_key"].eq("central_heating")]

    assert prepared == 200
    assert distributed == 190
    assert collected == 154
    assert round(response_rate, 1) == 81.1
    assert len(flagged) == 154
    assert len(valid) == 147
    assert reason_target_n == 112
    assert int(flagged["q7_q8_inconsistency_flag"].sum()) == 4
    assert int(valid["q9_central_heating_use"].eq(99).sum()) == 7
    assert set(central_rows["without_denominator"]) == {112}
    assert set(central_rows["with_denominator"]) == {28}

    return {
        "questionnaires_prepared": prepared,
        "questionnaires_distributed": distributed,
        "questionnaires_collected": collected,
        "response_rate_pct": round(response_rate, 1),
        "total_responses": len(flagged),
        "analysis_responses": len(valid),
        "reason_analysis_responses": reason_target_n,
        "q7_q8_inconsistency_n": int(
            flagged["q7_q8_inconsistency_flag"].sum()
        ),
        "central_heating_missing_n": int(
            valid["q9_central_heating_use"].eq(99).sum()
        ),
    }


def write_report(
    output_dir: Path,
    qc: dict[str, int | float],
    reason_summary: pd.DataFrame,
    reason_differences: pd.DataFrame,
    table2: pd.DataFrame,
) -> None:
    def reason_row(key: str, group: str) -> pd.Series:
        return reason_summary[
            reason_summary["reason_key"].eq(key)
            & reason_summary["bathroom_cold_group"].eq(group)
        ].iloc[0]

    barrier_all = reason_row("barrier", "全体")
    barrier_low = reason_row("barrier", "寒さ1-4")
    barrier_high = reason_row("barrier", "寒さ5-7")
    no_need_all = reason_row("no_need", "全体")
    barrier_diff = reason_differences[
        reason_differences["reason_key"].eq("barrier")
    ].iloc[0]
    central_bath = table2[
        table2["equipment_key"].eq("central_heating")
        & table2["outcome"].eq("bathroom_cold_5_7")
    ].iloc[0]

    lines = [
        "# ONKI短報用再集計レポート",
        "",
        "## 対象者フロー",
        "",
        f"- 準備: {qc['questionnaires_prepared']}部",
        f"- 配布: {qc['questionnaires_distributed']}部",
        f"- 回収: {qc['questionnaires_collected']}部",
        f"- 回収率: {qc['response_rate_pct']:.1f}%",
        f"- 解析対象: {qc['analysis_responses']}部",
        f"- Q8理由解析: {qc['reason_analysis_responses']}部",
        "",
        "## 主要結果",
        "",
        (
            f"- 障壁あり: {barrier_all['event_n']}/{barrier_all['denominator']} "
            f"({barrier_all['pct']:.2f}%, "
            f"95%CI [{barrier_all['ci95_lo_pct']:.2f}, "
            f"{barrier_all['ci95_hi_pct']:.2f}])"
        ),
        (
            f"- 不要: {no_need_all['event_n']}/{no_need_all['denominator']} "
            f"({no_need_all['pct']:.2f}%, "
            f"95%CI [{no_need_all['ci95_lo_pct']:.2f}, "
            f"{no_need_all['ci95_hi_pct']:.2f}])"
        ),
        (
            f"- 障壁あり（寒さ1-4）: {barrier_low['event_n']}/"
            f"{barrier_low['denominator']} ({barrier_low['pct']:.2f}%)"
        ),
        (
            f"- 障壁あり（寒さ5-7）: {barrier_high['event_n']}/"
            f"{barrier_high['denominator']} ({barrier_high['pct']:.2f}%)"
        ),
        (
            f"- 障壁ありの割合差（寒さ5-7 - 寒さ1-4）: "
            f"{barrier_diff['difference_pp']:.2f}pp, "
            f"95%CI [{barrier_diff['difference_ci95_lo_pp']:.2f}, "
            f"{barrier_diff['difference_ci95_hi_pp']:.2f}]"
        ),
        (
            f"- 浴室寒さ5-7（セントラル暖房不使用）: "
            f"{central_bath['without_event_n']}/"
            f"{central_bath['without_denominator']} "
            f"({central_bath['without_pct']:.2f}%)"
        ),
        (
            f"- 浴室寒さ5-7（セントラル暖房使用）: "
            f"{central_bath['with_event_n']}/"
            f"{central_bath['with_denominator']} "
            f"({central_bath['with_pct']:.2f}%)"
        ),
        "",
        "## 欠損・不整合",
        "",
        f"- Q7/Q8不整合: {qc['q7_q8_inconsistency_n']}部",
        (
            f"- セントラル暖房無回答: "
            f"{qc['central_heating_missing_n']}部（比較から除外）"
        ),
        "",
        "## 統計記述",
        "",
        "- 割合の95%CI: Wilson法",
        "- 割合差の95%CI: Newcombe-Wilson法",
        "- 調整回帰およびp値中心の評価は実施しない",
        "",
    ]
    (output_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    input_csv = Path(args.input_csv).resolve()
    collection_path = Path(args.collection_summary).resolve()
    output_dir = (
        Path(args.output_dir).resolve()
        if args.output_dir
        else default_output_dir().resolve()
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    collection_summary = pd.read_csv(collection_path, dtype=str)
    flagged, valid = prepare_analysis_set(input_csv)
    table1 = build_table1(valid)
    reason_summary, reason_differences = build_reason_summary(valid)
    table2 = build_table2(valid)

    figure_path = output_dir / "figures" / "figure1_reason_by_bathroom_cold.png"
    render_figure1(reason_summary, figure_path)
    if args.figure_output:
        stable_figure = Path(args.figure_output).resolve()
        render_figure1(reason_summary, stable_figure)

    table1.to_csv(output_dir / "table1_characteristics.csv", index=False)
    table2.to_csv(output_dir / "table2_equipment_and_cold.csv", index=False)
    reason_summary.to_csv(output_dir / "figure1_reason_summary.csv", index=False)
    reason_differences.to_csv(
        output_dir / "reason_difference_summary.csv",
        index=False,
    )
    write_markdown_tables(table1, table2, output_dir)

    qc = validate_results(
        collection_summary,
        flagged,
        valid,
        reason_summary,
        table2,
    )
    pd.DataFrame(
        [{"metric": key, "value": value} for key, value in qc.items()]
    ).to_csv(output_dir / "qc_summary.csv", index=False)
    write_report(output_dir, qc, reason_summary, reason_differences, table2)

    meta = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "input_csv": str(input_csv),
        "collection_summary": str(collection_path),
        "output_dir": str(output_dir),
        "python": platform.python_version(),
        "packages": {
            "pandas": pd.__version__,
            "matplotlib": matplotlib.__version__,
        },
        "methods": {
            "proportion_ci": "Wilson 95% CI",
            "difference_ci": "Newcombe-Wilson 95% CI",
            "adjusted_regression": False,
            "p_value_testing": False,
        },
    }
    (output_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
