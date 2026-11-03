import json
import tempfile
import unittest
from pathlib import Path

from scripts.package_phase1 import inventory_files, check_root

ROOT = Path(__file__).resolve().parents[1]


class PackageTests(unittest.TestCase):
    def test_inventory_contains_only_existing_files(self):
        self.assertGreater(len(inventory_files(ROOT)), 40)

    def test_raw_inputs_are_external_to_submission_zip(self):
        files = inventory_files(ROOT)
        external = {f["path"] for f in files if not f.get("archive", True)}
        self.assertEqual(external, {"data/udslong_imputed.csv", "data/mriscanclean.csv", "data/combined_adjacency_matrix.csv"})

    def test_inventory_rejects_path_traversal_and_missing_files(self):
        for path in ["../outside", "missing.txt", "/outside"]:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp); (root / "config").mkdir()
                (root / "config/phase1_delivery_files.json").write_text(json.dumps({"files": [{"path": path}]}))
                with self.assertRaises(ValueError):
                    inventory_files(root)

    def test_complete_project_has_no_broken_local_links(self):
        checks = check_root(ROOT)
        self.assertGreater(checks["local_links_verified"], 100)
        self.assertEqual(checks["errors"], 0)
