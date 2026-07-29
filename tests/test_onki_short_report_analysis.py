"""Regression tests for the manuscript-specific ONKI short-report analysis."""

from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src" / "scripts"))

from analyze_onki_short_report import (  # noqa: E402
    DEFAULT_COLLECTION_SUMMARY,
    DEFAULT_INPUT,
    FIGURE_FILENAMES,
    FIGURE_FILENAMES_EN,
    MONO,
    build_reason_summary,
    build_table1,
    build_table2,
    prepare_analysis_set,
    render_all_figures,
)
from tabulate_aomori_paper_survey import parse_reason_codes  # noqa: E402


class OnkiShortReportAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.flagged, cls.valid = prepare_analysis_set(DEFAULT_INPUT)

    def test_questionnaire_flow_and_response_rate(self) -> None:
        with DEFAULT_COLLECTION_SUMMARY.open(encoding="utf-8-sig", newline="") as file:
            rows = {row["field"]: row["value"] for row in csv.DictReader(file)}

        self.assertEqual(int(rows["questionnaires_prepared"]), 200)
        self.assertEqual(int(rows["questionnaires_distributed"]), 190)
        self.assertEqual(int(rows["questionnaires_collected"]), 154)
        self.assertEqual(int(rows["questionnaires_not_collected"]), 36)
        self.assertAlmostEqual(154 / 190 * 100, 81.1, places=1)
        self.assertEqual(len(self.flagged), 154)
        self.assertEqual(len(self.valid), 147)

    def test_primary_missing_data_exclusions(self) -> None:
        self.assertEqual(
            int(self.flagged["missing_q7_bath_heater_status"].sum()),
            3,
        )
        self.assertEqual(int(self.flagged["missing_q8_reason_codes"].sum()), 4)
        self.assertEqual(
            int(self.flagged["missing_q11_bathroom_cold_7pt"].sum()),
            0,
        )
        self.assertEqual(int(self.flagged["invalid_main3"].sum()), 7)

    def test_q7_q8_inconsistency_is_not_in_reason_analysis(self) -> None:
        self.assertEqual(
            int(self.flagged["q7_q8_inconsistency_flag"].sum()),
            4,
        )
        target = self.valid[
            self.valid["q7_bath_heater_status"].isin([2, 3])
        ].copy()
        self.assertEqual(len(target), 112)
        self.assertFalse(target["q7_q8_inconsistency_flag"].any())

    def test_multiple_response_overlap_and_reason_totals(self) -> None:
        target = self.valid[
            self.valid["q7_bath_heater_status"].isin([2, 3])
        ].copy()
        code_sets = target["q8_reason_codes"].apply(
            lambda value: set(parse_reason_codes(value))
        )
        no_need = code_sets.apply(lambda codes: 1 in codes)
        cost = code_sets.apply(lambda codes: bool(codes.intersection({2, 3})))
        housing = code_sets.apply(lambda codes: bool(codes.intersection({4, 5})))
        operation = code_sets.apply(lambda codes: bool(codes.intersection({6, 7})))
        barrier = cost | housing | operation

        self.assertEqual(int(no_need.sum()), 31)
        self.assertEqual(int(barrier.sum()), 69)
        self.assertEqual(int(cost.sum()), 41)
        self.assertEqual(int(housing.sum()), 27)
        self.assertEqual(int(operation.sum()), 3)
        self.assertEqual(int((no_need & barrier).sum()), 3)
        self.assertEqual(int((cost & housing).sum()), 2)
        self.assertEqual(int((cost & operation).sum()), 0)
        self.assertEqual(int((housing & operation).sum()), 0)

        reason_summary, _ = build_reason_summary(self.valid)
        barrier_cold = reason_summary[
            reason_summary["reason_key"].eq("barrier")
            & reason_summary["bathroom_cold_group"].eq("寒さ5-7")
        ].iloc[0]
        barrier_comparison = reason_summary[
            reason_summary["reason_key"].eq("barrier")
            & reason_summary["bathroom_cold_group"].eq("寒さ1-4")
        ].iloc[0]
        self.assertEqual(
            (int(barrier_cold["event_n"]), int(barrier_cold["denominator"])),
            (53, 62),
        )
        self.assertEqual(
            (
                int(barrier_comparison["event_n"]),
                int(barrier_comparison["denominator"]),
            ),
            (16, 50),
        )

    def test_central_heating_missing_values_are_excluded(self) -> None:
        self.assertEqual(
            int(self.valid["q9_central_heating_use"].eq(99).sum()),
            7,
        )
        table2 = build_table2(self.valid)
        row = table2[
            table2["equipment_key"].eq("central_heating")
            & table2["outcome"].eq("bathroom_cold_5_7")
        ].iloc[0]
        self.assertEqual(int(row["without_denominator"]), 112)
        self.assertEqual(int(row["with_denominator"]), 28)
        self.assertEqual(int(row["without_event_n"]), 61)
        self.assertEqual(int(row["with_event_n"]), 2)
        self.assertEqual(
            int(row["without_denominator"]) + int(row["with_denominator"]),
            140,
        )

    def test_figure_summary_counts(self) -> None:
        table1 = build_table1(self.valid)
        self.assertEqual(
            int(
                table1[
                    table1["item"].eq("寒さ体感")
                    & table1["category"].eq("浴室寒さ5-7")
                ]["event_n"].iloc[0]
            ),
            66,
        )
        central_used = self.valid[
            self.valid["q9_central_heating_use"].isin([1, 2])
        ]
        self.assertEqual(len(central_used), 28)
        self.assertEqual(
            int(central_used["q7_bath_heater_status"].eq(1).sum()),
            19,
        )

    def test_three_japanese_figures_are_rendered(self) -> None:
        reason_summary, _ = build_reason_summary(self.valid)
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = render_all_figures(
                self.valid,
                reason_summary,
                Path(temp_dir),
            )
            self.assertEqual(set(paths), {1, 2, 3})
            for number, path in paths.items():
                self.assertEqual(path.name, FIGURE_FILENAMES[number])
                self.assertTrue(path.exists())
                self.assertGreater(path.stat().st_size, 10_000)

    def test_three_english_submission_figures_are_rendered(self) -> None:
        reason_summary, _ = build_reason_summary(self.valid)
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = render_all_figures(
                self.valid,
                reason_summary,
                Path(temp_dir),
                language="en",
            )
            self.assertEqual(set(paths), {1, 2, 3})
            for number, path in paths.items():
                self.assertEqual(path.name, FIGURE_FILENAMES_EN[number])
                self.assertTrue(path.exists())
                self.assertGreater(path.stat().st_size, 10_000)

    def test_figure_palette_is_monochrome(self) -> None:
        for color in MONO.values():
            red = color[1:3]
            green = color[3:5]
            blue = color[5:7]
            self.assertEqual(red, green)
            self.assertEqual(green, blue)


if __name__ == "__main__":
    unittest.main()
