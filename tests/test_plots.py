import unittest

from plots import line_svg


class PlotTests(unittest.TestCase):
    def test_svg_contains_polylines_and_labels(self):
        svg = line_svg(
            [[0, 0, 0], [1, 1, -1]],
            "Time (ms)",
            "Voltage (V)",
            "Vin / Vout",
            ["Vin", "Vout"],
        )
        self.assertIn("<svg", svg)
        self.assertIn("<polyline", svg)
        self.assertIn("Time (ms)", svg)
        self.assertIn("Vin", svg)
        self.assertNotIn("<script", svg)


    def test_missing_series_labels_do_not_crash(self):
        svg = line_svg(
            [[1, 2, 3], [2, 3, 4]], "Frequency (Hz)", "Value", "AC", ["Gain"]
        )
        self.assertIn("<polyline", svg)
        self.assertIn("Gain", svg)
        self.assertNotIn("<script", svg)


if __name__ == "__main__":
    unittest.main()
