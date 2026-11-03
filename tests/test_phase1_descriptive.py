import math
import json
import unittest
from pathlib import Path

import numpy as np
from src.phase1_dataset import load_dataset, SAMPLE_FLAGS

from src.phase1_descriptive import categorical_frequencies, numeric_summary, quantile


class DescriptiveTests(unittest.TestCase):
    def test_all_stored_numeric_summaries_match_independent_numpy(self):
        root = Path(__file__).resolve().parents[1]
        rows, _ = load_dataset(root)
        stored = json.loads((root / "reports/phase1/descriptive_statistics.json").read_text())
        for summary in stored["numeric"]:
            population = [r for r in rows if (summary["sample"] == "all_shared" or r[SAMPLE_FLAGS[summary["sample"]]])
                          and (summary["stratum_code"] is None or r["NACCUDSD_ANALYSIS"] == summary["stratum_code"])]
            values = np.array([r[summary["variable"]] for r in population if r[summary["variable"]] is not None])
            with self.subTest(variable=summary["variable"], sample=summary["sample"], group=summary["stratum_code"]):
                self.assertEqual(summary["n_usable"], len(values))
                self.assertAlmostEqual(summary["mean"], np.mean(values))
                self.assertAlmostEqual(summary["sd_sample"], np.std(values, ddof=1))
                for key, value in zip(["q1", "median", "q3"], np.quantile(values, [.25, .5, .75], method="linear")):
                    self.assertAlmostEqual(summary[key], value)

    def test_sample_sd_uses_n_minus_one(self):
        s = numeric_summary([1, 2, 3, 4, None])
        self.assertAlmostEqual(s["mean"], 2.5)
        self.assertAlmostEqual(s["sd_sample"], math.sqrt(5 / 3))
        self.assertEqual((s["n_population"], s["n_usable"], s["n_unusable"]), (5, 4, 1))

    def test_type_seven_quantiles(self):
        self.assertEqual([quantile([4, 1, 3, 2], p) for p in [.25, .5, .75]], [1.75, 2.5, 3.25])

    def test_empty_and_singleton_sd_remain_undefined(self):
        self.assertIsNone(numeric_summary([])["mean"])
        self.assertIsNone(numeric_summary([1])["sd_sample"])
        self.assertEqual(numeric_summary([0])["median"], 0)

    def test_nonfinite_and_boolean_values_are_rejected(self):
        for value in [True, float("nan"), float("inf")]:
            with self.assertRaises(ValueError):
                numeric_summary([value])

    def test_percentage_denominators_are_distinct(self):
        a, b, missing = categorical_frequencies([1, 1, 2, None], {1: "a", 2: "b"})
        self.assertEqual(a["percent_of_population"], 50)
        self.assertAlmostEqual(a["percent_of_available"], 200 / 3)
        self.assertIsNone(missing["percent_of_available"])
        self.assertEqual(sum(r["count"] for r in [a, b, missing]), 4)

    def test_unknown_category_is_not_silently_dropped(self):
        with self.assertRaises(ValueError):
            categorical_frequencies([1, 7], {1: "a"})
