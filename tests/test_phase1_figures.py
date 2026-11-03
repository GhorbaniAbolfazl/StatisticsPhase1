import json
import tempfile
import unittest
from pathlib import Path

from src.phase1_figures import box_summary, histogram_counts, prepare_plot_data, render_figures
from src.phase1_dataset import load_dataset

ROOT = Path(__file__).resolve().parents[1]


class FigureTests(unittest.TestCase):
    def test_histogram_includes_last_endpoint_once(self):
        self.assertEqual(histogram_counts([0, 1.9, 2, 4], [0, 2, 4]), [2, 2])

    def test_histogram_rejects_dropped_observations(self):
        with self.assertRaises(ValueError):
            histogram_counts([-1, 2], [0, 2, 4])

    def test_box_whiskers_are_observed_values_and_outlier_is_retained(self):
        s = box_summary([0, 1, 2, 3, 20])
        self.assertEqual((s["q1"], s["med"], s["q3"]), (1, 2, 3))
        self.assertEqual((s["whislo"], s["whishi"]), (0, 3))

    def test_each_histogram_and_group_accounts_for_all_people(self):
        rows, _ = load_dataset(ROOT)
        d = prepare_plot_data(rows)
        self.assertEqual(sum(d["moca"]["integer_counts"]) + sum(d["moca"]["fractional_counts"]), 1228)
        self.assertEqual(sum(d["thickness"]["counts"]), 1237)
        self.assertEqual([g["n_main_pair"] for g in d["groups"]], [842, 7, 251, 128])

    def test_paired_panels_include_every_participant(self):
        d = json.loads((ROOT / "reports/phase1/figures_metadata.json").read_text())
        check = d["visual_checks"]["04_group_comparison"]
        self.assertEqual(check["raw_points_per_panel"], [842, 7, 251, 128] * 2)
        self.assertTrue(check["text_within_canvas"])

    def test_figures_do_not_inherit_dark_notebook_theme(self):
        rows, _ = load_dataset(ROOT)
        data = prepare_plot_data(rows)
        # Initialize the noninteractive backend/cache before changing rcParams.
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            first, second = Path(a), Path(b)
            render_figures(first, rows, data)
            import matplotlib.pyplot as plt
            with plt.rc_context({"axes.facecolor": "black", "text.color": "white",
                                 "axes.labelcolor": "white", "xtick.color": "white", "ytick.color": "white"}):
                render_figures(second, rows, data)
            for path in (first / "reports/phase1/figures").glob("*.png"):
                self.assertEqual(path.read_bytes(), (second / path.relative_to(first)).read_bytes())
