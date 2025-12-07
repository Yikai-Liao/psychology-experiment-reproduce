import tempfile
import unittest
import zipfile
from pathlib import Path

from example_workspace.util import (
    Screen,
    load_clean_excel,
    load_docx_text,
    polar_deg_to_manim,
    visual_angle_to_pixels,
)


TEST_DATA_DIR = Path(__file__).parent / "test_paper" / "data"


class TestDataIO(unittest.TestCase):
    def test_load_clean_excel(self):
        zip_path = TEST_DATA_DIR / "Exp.1a&1b.zip"
        assert zip_path.exists()

        with zipfile.ZipFile(zip_path) as zf:
            with zf.open("Exp.1a&1b/Exp.1a_clean.xlsx") as source:
                with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                    tmp.write(source.read())
                    temp_path = Path(tmp.name)

        df = load_clean_excel(temp_path)
        temp_path.unlink(missing_ok=True)

        self.assertFalse(df.empty)
        self.assertGreaterEqual(len(df.columns), 1)

    def test_load_docx_text(self):
        docx_path = TEST_DATA_DIR / "Instructions for data and analysis.docx"
        text = load_docx_text(docx_path)
        self.assertIn("data", text.lower())
        self.assertGreater(len(text.split()), 5)


class TestVision(unittest.TestCase):
    def test_visual_angle_conversion(self):
        spec = Screen()
        px = visual_angle_to_pixels(2.0, spec)
        self.assertGreater(px, 0)
        manim_point = polar_deg_to_manim(2.0, 45, spec)
        self.assertEqual(len(manim_point), 3)
        self.assertNotEqual(manim_point[0], 0)
        self.assertNotEqual(manim_point[1], 0)


if __name__ == "__main__":
    unittest.main()
