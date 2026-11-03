import copy
import json
import unittest
from pathlib import Path

from src.phase1_quality import classify, iqr_review, prepare_selected

ROOT = Path(__file__).resolve().parents[1]


class QualityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads((ROOT / "config/phase1_quality_rules.json").read_text())

    def participant(self, score="25", education="16"):
        return {"NACCID": "NACC000001", "MOCATOTS": score, "NACCAGE": "68", "SEX": "2",
                "EDUC": education, "NACCUDSD": "1"}

    def image(self, left="2.0", right="4.0"):
        return {"NACCID": "NACC000001", "NACCUDSD": "1",
                "LH_ENTORHINAL_AVGTH": left, "RH_ENTORHINAL_AVGTH": right}

    def test_special_codes_are_variable_specific(self):
        self.assertEqual(classify("99", self.config["uds"]["EDUC"])[0], "known_special")
        self.assertEqual(classify("9", self.config["uds"]["MOCATOTS"])[0], "reference_compatible")

    def test_moca_fractional_score_is_retained_only_in_main(self):
        row = prepare_selected([self.participant("25.4")], [self.image()], self.config)[0]
        self.assertEqual(row["MOCATOTS_ANALYSIS"], 25.4)
        self.assertTrue(row["MAIN_PAIR_ELIGIBLE"])
        self.assertFalse(row["INTEGER_SENSITIVITY_PAIR_ELIGIBLE"])

    def test_unusable_moca_is_never_clipped(self):
        for score in ["30.8", "88", "-4", "NaN", "inf", ""]:
            with self.subTest(score=score):
                row = prepare_selected([self.participant(score)], [self.image()], self.config)[0]
                self.assertIsNone(row["MOCATOTS_ANALYSIS"])
                self.assertEqual(row["MOCATOTS_RAW"], score)

    def test_missing_education_does_not_remove_main_pair(self):
        row = prepare_selected([self.participant(education="99")], [self.image()], self.config)[0]
        self.assertTrue(row["MAIN_PAIR_ELIGIBLE"])
        self.assertFalse(row["MAIN_COMMON_SAMPLE_ELIGIBLE"])

    def test_bilateral_mean_requires_both_sides(self):
        for right in ["0", "-1", "NaN", ""]:
            row = prepare_selected([self.participant()], [self.image(right=right)], self.config)[0]
            self.assertIsNone(row["ENTORHINAL_THICKNESS_MEAN"])
        row = prepare_selected([self.participant()], [self.image()], self.config)[0]
        self.assertEqual(row["ENTORHINAL_THICKNESS_MEAN"], 3.0)

    def test_duplicate_ids_prevent_ambiguous_join(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            prepare_selected([self.participant()] * 2, [self.image()], self.config)

    def test_preparation_keeps_source_values_unchanged(self):
        uds, mri = [self.participant("25.4")], [self.image()]
        before = copy.deepcopy((uds, mri))
        prepare_selected(uds, mri, self.config)
        self.assertEqual((uds, mri), before)

    def test_iqr_flags_are_review_only_and_exclude_boundary(self):
        result = iqr_review("test", list("abcde"), [0, 1, 2, 3, 20])
        self.assertEqual(result["flagged"], 1)
        self.assertEqual(result["issues"][0]["NACCID"], "e")
        self.assertEqual(result["n"], 5)
