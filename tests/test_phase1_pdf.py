import json
from io import BytesIO
import tempfile
import unittest
from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from scripts.build_phase1_pdf import (FONT_FILES, PersianText, ReportCanvas, notebook_title, verify_notebook_images,
                                      verify_report, visual)

ROOT = Path(__file__).resolve().parents[1]


class PdfTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pdfmetrics.registerFont(TTFont("Fa", str(ROOT / FONT_FILES["Fa"])))

    def test_bookmarks_point_to_distinct_numbered_pages(self):
        canvas = ReportCanvas(BytesIO())
        for key in ["first", "second"]:
            canvas._page_bookmarks.append((key, key))
            canvas.drawString(50, 100, key)
            canvas.showPage()
        canvas.save()
        self.assertNotEqual(canvas._destinations["first"].page.name,
                            canvas._destinations["second"].page.name)

    def test_title_skips_html_direction_wrapper(self):
        text = '<div dir="rtl">\n\n# عنوان علمی پروژه\n\nمتن'
        self.assertEqual(notebook_title(text), "عنوان علمی پروژه")

    def test_missing_title_fails_instead_of_printing_html(self):
        with self.assertRaises(ValueError):
            notebook_title('<div dir="rtl">\nمتن بدون عنوان')

    def test_long_identifier_wraps_inside_table_width(self):
        pdfmetrics.registerFont(TTFont("Fa", str(ROOT / FONT_FILES["Fa"])))
        text = PersianText("ENTORHINAL_THICKNESS_MEAN", size=9)
        text.wrap(90, 700)
        self.assertGreater(len(text.lines), 1)
        self.assertTrue(all(pdfmetrics.stringWidth(visual(line), "Fa", 9) <= 90 for line in text.lines))

    def test_notebook_and_pdf_use_identical_pngs(self):
        verify_notebook_images(ROOT)

    def test_stale_notebook_images_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "notebooks").mkdir()
            (root / "reports/phase1/figures").mkdir(parents=True)
            (root / "notebooks/phase1.ipynb").write_text(json.dumps({"cells": []}))
            for name in ["01_moca_distribution", "02_entorhinal_distribution", "03_cognitive_status", "04_group_comparison"]:
                (root / f"reports/phase1/figures/{name}.png").write_bytes(b"image")
            with self.assertRaisesRegex(ValueError, "Notebook images differ"):
                verify_notebook_images(root)

    def test_saved_pdf_matches_its_sources(self):
        self.assertTrue(verify_report(ROOT)["pdf_sources_verified"])
