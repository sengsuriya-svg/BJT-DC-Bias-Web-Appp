import re
import unittest

from plots import line_svg


def polyline_x(svg):
    match = re.search(r'<polyline points="([^"]+)"', svg)
    if match is None:
        return []
    return [float(pair.split(",")[0]) for pair in match.group(1).split()]


class AcPlotTests(unittest.TestCase):
    def test_ac_plot_spaces_log_decades_evenly(self):
        svg = line_svg(
            [[1.0, -42.0], [10.0, -38.0], [100.0, -35.0], [1000.0, -34.0]],
            "Frequency (Hz)", "Gain (dB)", "AC frequency response",
            ["Gain (dB)"], log_x=True,
        )
        xs = polyline_x(svg)
        self.assertEqual(len(xs), 4)
        gaps = [b - a for a, b in zip(xs, xs[1:])]
        for gap in gaps:
            self.assertAlmostEqual(gap, gaps[0], delta=0.01)
        self.assertGreater(gaps[0], 100)

    def test_ac_plot_labels_frequency_decades(self):
        svg = line_svg(
            [[1.0, -42.0], [1000.0, -34.0]],
            "Frequency (Hz)", "Gain (dB)", "AC frequency response",
            ["Gain (dB)"], log_x=True,
        )
        self.assertIn(">1<", svg)
        self.assertIn(">1k<", svg)

    def test_y_axis_label_does_not_overlap_title(self):
        svg = line_svg(
            [[1.0, -42.0], [10.0, -35.0]],
            "Frequency (Hz)", "Gain (dB)", "AC frequency response",
            ["Gain (dB)"], log_x=True,
        )
        self.assertIn('transform="rotate(-90', svg)


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
