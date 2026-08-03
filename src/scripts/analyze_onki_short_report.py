#!/usr/bin/env python3
"""Generate manuscript summaries and three figures for the ONKI short report."""

from __future__ import annotations

import argparse
import json
import platform
import shutil
from datetime import datetime
from pathlib import Path
from typing import Callable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib import patheffects
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

FIGURE_FILENAMES = {
    1: "onki_short_report_figure1_participant_profile.png",
    2: "onki_short_report_figure2_heating_concurrent_use.png",
    3: "onki_short_report_figure3_barrier_by_bathroom_coldness.png",
}

FIGURE_FILENAMES_EN = {
    1: "onki_short_report_figure1_participant_profile_en.png",
    2: "onki_short_report_figure2_heating_concurrent_use_en.png",
    3: "onki_short_report_figure3_barrier_by_bathroom_coldness_en.png",
}

MONO = {
    "black": "#111111",
    "dark": "#3B3B3B",
    "medium_dark": "#666666",
    "medium": "#929292",
    "light": "#BDBDBD",
    "very_light": "#E3E3E3",
    "white": "#FFFFFF",
}


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
        "--figure-output-dir",
        help=(
            "Optional directory for stable copies of the three submission "
            "figure PNG files."
        ),
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


def configure_japanese_plotting() -> str:
    candidates = [
        "Noto Sans JP",
        "BIZ UDPゴシック",
        "Yu Gothic UI",
        "Meiryo UI",
    ]
    installed = {font.name for font in font_manager.fontManager.ttflist}
    selected = next((name for name in candidates if name in installed), None)
    if selected is None:
        raise RuntimeError(
            "日本語図を生成できるフォントが見つかりません。"
            "Noto Sans JP等をインストールしてください。"
        )
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": [selected],
            "axes.unicode_minus": False,
            "figure.facecolor": MONO["white"],
            "axes.facecolor": MONO["white"],
            "text.color": MONO["black"],
            "axes.labelcolor": MONO["black"],
            "axes.edgecolor": MONO["black"],
            "xtick.color": MONO["black"],
            "ytick.color": MONO["black"],
            "hatch.color": MONO["black"],
            "hatch.linewidth": 0.9,
        }
    )
    return selected


def format_count_labels(
    labels: list[str],
    counts: list[int],
    language: str = "ja",
) -> list[str]:
    if language == "en":
        return [
            f"{label} (n={count})"
            for label, count in zip(labels, counts)
        ]
    return [
        f"{label}（n={count}）"
        for label, count in zip(labels, counts)
    ]


def apply_text_outline(
    label: plt.Text,
    foreground: str,
    outline: str,
    linewidth: float = 2.8,
    weight_stroke_width: float = 1.3,
) -> None:
    label.set_color(foreground)
    label.set_fontweight(900)
    label.set_path_effects(
        [
            patheffects.Stroke(linewidth=linewidth, foreground=outline),
            patheffects.Stroke(
                linewidth=weight_stroke_width,
                foreground=foreground,
            ),
            patheffects.Normal(),
        ]
    )


def draw_donut(
    ax: plt.Axes,
    counts: list[int],
    labels: list[str],
    colors: list[str],
    hatches: list[str],
    title: str,
    legend_columns: int = 1,
    language: str = "ja",
) -> None:
    wedges, _, autotexts = ax.pie(
        counts,
        startangle=90,
        counterclock=False,
        colors=colors,
        wedgeprops={
            "width": 0.42,
            "edgecolor": MONO["black"],
            "linewidth": 0.9,
        },
        autopct=lambda pct: f"{pct:.1f}%" if pct >= 5 else "",
        pctdistance=0.77,
        textprops={
            "fontsize": 14,
            "fontweight": "bold",
            "color": MONO["black"],
        },
    )
    for wedge, hatch in zip(wedges, hatches):
        wedge.set_hatch(hatch)
    for wedge, label in zip(wedges, autotexts):
        red, green, blue, _ = wedge.get_facecolor()
        luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue
        if luminance < 0.48:
            apply_text_outline(label, MONO["white"], MONO["black"])
        else:
            apply_text_outline(label, MONO["black"], MONO["white"])

    ax.set_title(title, fontsize=16, fontweight="bold", pad=12)
    ax.legend(
        wedges,
        format_count_labels(labels, counts, language=language),
        loc="upper center",
        bbox_to_anchor=(0.5, -0.02),
        frameon=False,
        fontsize=12.5,
        ncol=legend_columns,
        handlelength=1.5,
        handleheight=1.2,
        columnspacing=1.2,
        labelspacing=0.8,
    )
    ax.set_aspect("equal")


def render_figure1_profile(
    valid: pd.DataFrame,
    output_path: Path,
    language: str = "ja",
) -> None:
    configure_japanese_plotting()
    english = language == "en"
    fig, axes = plt.subplots(2, 2, figsize=(9.2, 7.4))
    fig.suptitle(
        (
            f"Participant characteristics (n={len(valid)})"
            if english
            else f"回答者の基礎情報（n={len(valid)}）"
        ),
        fontsize=20,
        fontweight="bold",
        y=0.99,
    )

    age_categories = ["18-49歳", "50-59歳", "60-69歳", "70歳以上"]
    age_labels = (
        ["18-49 years", "50-59 years", "60-69 years", "70 years or older"]
        if english
        else age_categories
    )
    age_counts = [
        int(valid["age_compact"].eq(category).sum())
        for category in age_categories
    ]
    draw_donut(
        axes[0, 0],
        age_counts,
        age_labels,
        [
            MONO["dark"],
            MONO["medium_dark"],
            MONO["light"],
            MONO["very_light"],
        ],
        ["", "///", "\\\\", "xx"],
        "Age" if english else "年齢",
        legend_columns=2,
        language=language,
    )

    housing_counts = [
        int(valid["q2_housing_type"].eq(code).sum()) for code in [1, 2]
    ]
    draw_donut(
        axes[0, 1],
        housing_counts,
        (
            ["Detached house", "Multi-unit housing"]
            if english
            else ["一戸建て", "集合住宅"]
        ),
        [MONO["dark"], MONO["very_light"]],
        ["", "///"],
        "Housing type" if english else "住宅種別",
        language=language,
    )

    heater_counts = [
        int(valid["q7_bath_heater_status"].eq(code).sum()) for code in [1, 2, 3]
    ]
    draw_donut(
        axes[1, 0],
        heater_counts,
        (
            ["Installed and used", "Installed but not used", "Not installed"]
            if english
            else ["設置して使用", "設置しているが未使用", "未設置"]
        ),
        [MONO["dark"], MONO["medium"], MONO["very_light"]],
        ["", "///", "xx"],
        "Bathroom heater-dryer" if english else "浴室暖房乾燥機",
        language=language,
    )

    ax = axes[1, 1]
    total = len(valid)
    bathroom_cold = int(valid["bathroom_cold_5_7"].sum())
    dressingroom_cold = int(valid["dressingroom_cold_5_7"].sum())
    cold_counts = [bathroom_cold, dressingroom_cold]
    cold_pct = [count / total * 100.0 for count in cold_counts]
    other_pct = [100.0 - value for value in cold_pct]
    y_positions = [0, 1]
    ax.barh(
        y_positions,
        cold_pct,
        color=MONO["dark"],
        edgecolor=MONO["black"],
        linewidth=0.9,
        hatch="///",
        height=0.50,
        label="寒さ5-7",
    )
    ax.barh(
        y_positions,
        other_pct,
        left=cold_pct,
        color=MONO["very_light"],
        edgecolor=MONO["black"],
        linewidth=0.9,
        hatch="xx",
        height=0.50,
        label="寒さ1-4",
    )
    for position, count, pct in zip(y_positions, cold_counts, cold_pct):
        label = ax.text(
            pct / 2,
            position,
            (
                f"{count}/{total}\n({pct:.1f}%)"
                if english
                else f"{count}/{total}人\n（{pct:.1f}%）"
            ),
            ha="center",
            va="center",
            fontsize=11.5,
        )
        apply_text_outline(label, MONO["white"], MONO["black"], linewidth=2.6)

    ax.set_yticks(y_positions)
    ax.set_yticklabels(
        ["Bathroom", "Dressing room"] if english else ["浴室", "脱衣所"],
        fontsize=13,
    )
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xticks([0, 50, 100])
    ax.tick_params(axis="x", labelsize=10.5)
    ax.set_xlabel(
        "Respondents (%)" if english else "回答者割合（%）",
        fontsize=11.5,
    )
    ax.set_title(
        "Perceived coldness" if english else "寒さ体感",
        fontsize=16,
        fontweight="bold",
        pad=12,
    )
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.23),
        frameon=False,
        labels=(
            ["Coldness 5-7", "Coldness 1-4"]
            if english
            else ["寒さ5-7", "寒さ1-4"]
        ),
        fontsize=11.5,
        ncol=2,
        handlelength=1.8,
        handleheight=1.2,
    )
    ax.grid(axis="x", color=MONO["light"], linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)

    fig.subplots_adjust(
        left=0.05,
        right=0.95,
        top=0.91,
        bottom=0.08,
        wspace=0.30,
        hspace=0.58,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def render_barrier_figure(
    reason_summary: pd.DataFrame,
    output_path: Path,
    language: str = "ja",
) -> None:
    configure_japanese_plotting()
    english = language == "en"
    groups = ["寒さ5-7", "寒さ1-4"]
    rows = (
        reason_summary[
            reason_summary["reason_key"].eq("barrier")
            & reason_summary["bathroom_cold_group"].isin(groups)
        ]
        .set_index("bathroom_cold_group")
        .loc[groups]
    )
    barrier_pct = rows["pct"].astype(float).to_list()
    no_barrier_pct = [100.0 - value for value in barrier_pct]
    y_positions = [0, 1]

    fig, ax = plt.subplots(figsize=(8.6, 3.8))
    ax.barh(
        y_positions,
        barrier_pct,
        color=MONO["dark"],
        edgecolor=MONO["black"],
        linewidth=0.9,
        hatch="///",
        height=0.52,
        label=(
            "At least one barrier (reasons 2-7)"
            if english
            else "障壁あり（理由2-7）"
        ),
    )
    ax.barh(
        y_positions,
        no_barrier_pct,
        left=barrier_pct,
        color=MONO["very_light"],
        edgecolor=MONO["black"],
        linewidth=0.9,
        hatch="xx",
        height=0.52,
        label="No barrier" if english else "障壁なし",
    )
    for position, (_, row) in zip(y_positions, rows.iterrows()):
        label = ax.text(
            float(row["pct"]) / 2,
            position,
            (
                (
                    f"{int(row['event_n'])}/{int(row['denominator'])} "
                    f"({float(row['pct']):.1f}%)"
                )
                if english
                else (
                    f"{int(row['event_n'])}/{int(row['denominator'])}人"
                    f"（{float(row['pct']):.1f}%）"
                )
            ),
            ha="center",
            va="center",
            fontsize=14,
        )
        apply_text_outline(label, MONO["white"], MONO["black"], linewidth=2.6)

    ax.set_yticks(y_positions)
    ax.set_yticklabels(
        (
            [
                "Bathroom coldness 5-7\n"
                f"(n={int(rows.loc['寒さ5-7', 'denominator'])})",
                "Bathroom coldness 1-4\n"
                f"(n={int(rows.loc['寒さ1-4', 'denominator'])})",
            ]
            if english
            else [
                f"浴室寒さ5-7\n（n={int(rows.loc['寒さ5-7', 'denominator'])}）",
                f"浴室寒さ1-4\n（n={int(rows.loc['寒さ1-4', 'denominator'])}）",
            ]
        ),
        fontsize=12.5,
    )
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.tick_params(axis="x", labelsize=11.5)
    ax.set_xlabel(
        "Respondents (%)" if english else "回答者割合（%）",
        fontsize=13,
    )
    ax.set_title(
        (
            "Barriers to installation or use by perceived bathroom coldness"
            if english
            else "浴室寒さ別にみた未設置・未使用の障壁"
        ),
        fontsize=16 if english else 17,
        fontweight="bold",
        pad=14,
    )
    ax.grid(axis="x", color=MONO["light"], linewidth=0.8)
    ax.set_axisbelow(True)
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.22),
        frameon=False,
        fontsize=11.5,
        ncol=2,
        handlelength=2.0,
        handleheight=1.2,
    )
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    fig.subplots_adjust(left=0.20, right=0.97, top=0.82, bottom=0.30)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def render_heating_figure(
    valid: pd.DataFrame,
    output_path: Path,
    language: str = "ja",
) -> None:
    configure_japanese_plotting()
    english = language == "en"
    central_available = valid[valid["q9_central_heating_use"].isin([1, 2, 3])]
    central_used = central_available[
        central_available["q9_central_heating_use"].isin([1, 2])
    ]
    central_not_used = len(central_available) - len(central_used)
    concurrent = int(central_used["q7_bath_heater_status"].eq(1).sum())
    not_concurrent = len(central_used) - concurrent

    fig, axes = plt.subplots(1, 2, figsize=(9.0, 4.4))
    fig.suptitle(
        (
            "Central heating and concurrent bathroom heater-dryer use"
            if english
            else "セントラル暖房の使用と浴室暖房乾燥機との併用"
        ),
        fontsize=16 if english else 17,
        fontweight="bold",
        y=0.98,
    )
    draw_donut(
        axes[0],
        [len(central_used), central_not_used],
        (
            ["Used central heating", "Did not use central heating"]
            if english
            else ["セントラル暖房を使用", "使用していない"]
        ),
        [MONO["dark"], MONO["very_light"]],
        ["///", "xx"],
        (
            f"Central heating (n={len(central_available)})"
            if english
            else f"セントラル暖房（n={len(central_available)}）"
        ),
        language=language,
    )
    draw_donut(
        axes[1],
        [concurrent, not_concurrent],
        (
            [
                "Also used a bathroom heater-dryer",
                "Did not use or install one",
            ]
            if english
            else ["浴室暖房乾燥機も使用", "未使用・未設置"]
        ),
        [MONO["dark"], MONO["very_light"]],
        ["///", "xx"],
        (
            f"Concurrent use among users (n={len(central_used)})"
            if english
            else f"使用者における併用（n={len(central_used)}）"
        ),
        language=language,
    )
    fig.subplots_adjust(
        left=0.05,
        right=0.95,
        top=0.82,
        bottom=0.18,
        wspace=0.32,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def render_all_figures(
    valid: pd.DataFrame,
    reason_summary: pd.DataFrame,
    output_dir: Path,
    language: str = "ja",
) -> dict[int, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    filenames = (
        FIGURE_FILENAMES_EN
        if language == "en"
        else FIGURE_FILENAMES
    )
    paths = {
        number: output_dir / filename
        for number, filename in filenames.items()
    }
    render_figure1_profile(valid, paths[1], language=language)
    render_heating_figure(valid, paths[2], language=language)
    render_barrier_figure(reason_summary, paths[3], language=language)
    return paths


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
    central_used = valid[valid["q9_central_heating_use"].isin([1, 2])]
    assert int(central_used["q7_bath_heater_status"].eq(1).sum()) == 19

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

    figure_paths = render_all_figures(
        valid,
        reason_summary,
        output_dir / "figures",
    )
    english_figure_paths = render_all_figures(
        valid,
        reason_summary,
        output_dir / "figures_en",
        language="en",
    )
    if args.figure_output_dir:
        stable_figure_dir = Path(args.figure_output_dir).resolve()
        stable_figure_dir.mkdir(parents=True, exist_ok=True)
        for paths, filenames in [
            (figure_paths, FIGURE_FILENAMES),
            (english_figure_paths, FIGURE_FILENAMES_EN),
        ]:
            for number, source in paths.items():
                shutil.copy2(
                    source,
                    stable_figure_dir / filenames[number],
                )

    table1.to_csv(output_dir / "table1_characteristics.csv", index=False)
    table2.to_csv(output_dir / "table2_equipment_and_cold.csv", index=False)
    reason_summary.to_csv(output_dir / "figure3_reason_summary.csv", index=False)
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
