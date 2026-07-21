import importlib.util
import unittest
from datetime import datetime
from pathlib import Path

module_path = Path(__file__).resolve().parents[1] / "server2cam.py"
spec = importlib.util.spec_from_file_location("server2cam", module_path)
server2cam = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server2cam)


class TestImageFilename(unittest.TestCase):
    def test_build_image_filename(self):
        filename = server2cam.build_image_filename(
            side="left",
            lat=13.7563,
            lng=100.5018,
            captured_at=datetime(2026, 7, 21, 10, 5, 30),
            ext="jpg",
        )
        self.assertEqual(
            filename,
            "image_left_13.7563_100.5018_20260721_100530.jpg",
        )


if __name__ == "__main__":
    unittest.main()
