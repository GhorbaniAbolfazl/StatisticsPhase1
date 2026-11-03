import copy
import tempfile
import unittest
from pathlib import Path

from src.phase1_dataset import (build_dataset, build_flow, denominator_rows, enrich_rows,
                               load_dataset, read_typed_csv, write_csv)
from src.phase1_quality import audit, load_table

ROOT = Path(__file__).resolve().parents[1]


class DatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = build_dataset(ROOT)

    def test_all_shared_participants_are_preserved(self):
        self.assertEqual(len(self.bundle["rows"]), 1237)
        self.assertEqual(len({r["NACCID"] for r in self.bundle["rows"]}), 1237)

    def test_saved_rows_equal_reconstruction_from_raw_inputs(self):
        stored, _ = load_dataset(ROOT)
        self.assertEqual(stored, self.bundle["rows"])

    def test_eligibility_counts_and_nesting(self):
        self.assertEqual({k: s["included"] for k, s in self.bundle["samples"].items()},
                         {"main_pair": 1228, "main_common": 1226, "integer_pair": 984, "integer_common": 982})
        for r in self.bundle["rows"]:
            self.assertFalse(r["INTEGER_SENSITIVITY_COMMON_ELIGIBLE"] and not r["MAIN_COMMON_SAMPLE_ELIGIBLE"])

    def test_csv_roundtrip_preserves_raw_strings_null_and_false(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "participants.csv"
            write_csv(path, self.bundle["rows"], self.bundle["fields"])
            self.assertEqual(read_typed_csv(path, self.bundle["fields"]), self.bundle["rows"])

    def test_flow_conserves_people_at_every_step(self):
        for step in build_flow(self.bundle["rows"]):
            self.assertEqual(step["n_before"] - step["n_removed"], step["n_after"])

    def test_variable_specific_denominators_include_missing_education(self):
        den = denominator_rows(self.bundle["rows"])
        educ = next(r for r in den if r["sample"] == "main_pair" and r["variable"] == "EDUC_ANALYSIS")
        self.assertEqual((educ["n_population"], educ["n_usable"], educ["n_unusable"]), (1228, 1226, 2))

    def test_join_uses_ids_when_mri_order_changes(self):
        report, prepared, _ = audit(ROOT)
        _, uds = load_table(ROOT / "data/udslong_imputed.csv")
        _, mri = load_table(ROOT / "data/mriscanclean.csv")
        shuffled = enrich_rows(prepared, uds, list(reversed(mri)), report)
        for original, changed in zip(self.bundle["rows"], shuffled):
            a, b = copy.copy(original), copy.copy(changed)
            a.pop("MRI_CSV_LINE"); b.pop("MRI_CSV_LINE")
            self.assertEqual(a, b)
