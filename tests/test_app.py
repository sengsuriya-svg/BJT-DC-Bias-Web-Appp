import unittest
from unittest.mock import patch

from app import app


class AppTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_analytical_divider_still_works(self):
        response = self.client.post("/", data={
            "analysis": "bias",
            "mode": "divider",
            "vcc": "12",
            "r1": "100",
            "r2": "22",
            "rc": "2.2",
            "re": "1",
            "beta": "100",
            "vbe": "0.7",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"DC Bias Results", response.data)
        self.assertNotIn(b"error-msg", response.data)

    @patch("app.simulate", return_value={
        "status": "error",
        "error": "ngspice not found",
        "analysis": "dc",
    })
    def test_spice_error_shows_no_success(self, _):
        response = self.client.post("/", data={
            "analysis": "spice_dc",
            "vcc": "12",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"ngspice not found", response.data)
        self.assertIn(b"Status: error", response.data)
        self.assertNotIn(b"plot-frame", response.data)
        self.assertNotIn(b"Status: success", response.data)

    def test_page_offers_analysis_modes_and_spice_inputs(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'name="analysis"', response.data)
        self.assertIn(b'spice-panel', response.data)
        self.assertIn(b'value="spice_dc"', response.data)
        self.assertIn(b'name="amplitude"', response.data)

    def test_page_states_generic_model_is_an_assumption(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Generic model assumption", response.data)
        self.assertIn(b"not instructor-verified", response.data)

    @patch("app.simulate", return_value={
        "status": "error", "error": "ngspice not found", "analysis": "dc",
    })
    def test_spice_units_are_preserved_after_submit(self, _):
        response = self.client.post("/", data={
            "analysis": "spice_dc",
            "s_r1_unit": "ohm",
            "s_cin_unit": "nF",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<option value="ohm" selected>', response.data)
        self.assertIn(b'<option value="nF" selected>', response.data)

    def test_analytical_units_are_preserved_after_submit(self):
        response = self.client.post("/", data={
            "analysis": "bias", "mode": "divider", "r1_unit": "ohm",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<option value="ohm" selected>', response.data)


def success_result(analysis, points=None, values=None):
    return {
        "status": "success",
        "analysis": analysis,
        "engine": "ngspice",
        "model": "NPN_GENERIC (test)",
        "netlist": "* test deck",
        "values": values,
        "points": points,
        "error": None,
        "log_excerpt": "test output",
    }


class SpiceSuccessTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    @patch("app.simulate", return_value=success_result(
        "ac", [[1.0, -4.0, 175.0], [1000.0, 21.0, -165.0]]
    ))
    def test_successful_ac_renders_gain_plot(self, _):
        response = self.client.post("/", data={"analysis": "spice_ac"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"plot-frame", response.data)
        self.assertIn(b"AC frequency response", response.data)
        self.assertNotIn(b"error-msg", response.data)

    @patch("app.simulate", return_value=success_result(
        "ac", [[1.0, -42.0, 0.0], [10.0, -38.0, 0.0], [1000.0, -34.0, 0.0]]
    ))
    def test_ac_result_uses_log_frequency_axis(self, _):
        response = self.client.post("/", data={"analysis": "spice_ac"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b">1k<", response.data)

    @patch("app.simulate", return_value=success_result(
        "tran", [[0.0, 0.0, 0.0], [0.001, 0.01, -0.21]]
    ))
    def test_successful_tran_renders_plot(self, _):
        response = self.client.post("/", data={"analysis": "spice_tran"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"plot-frame", response.data)
        self.assertIn(b"Transient response", response.data)

    @patch("app.simulate", return_value=success_result(
        "dc", values={"vb": 2.16, "ve": 1.46, "vc": 8.78, "vce": 7.32, "ic_ma": 1.46}
    ))
    def test_successful_dc_shows_values_without_plot(self, _):
        response = self.client.post("/", data={"analysis": "spice_dc"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"8.78 V", response.data)
        self.assertNotIn(b"plot-frame", response.data)

    @patch("app.simulate", return_value={
        "status": "error", "error": "ngspice not found", "analysis": "ac",
    })
    def test_error_has_no_plot_and_no_success_badge(self, _):
        response = self.client.post("/", data={"analysis": "spice_ac"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"ngspice not found", response.data)
        self.assertNotIn(b"plot-frame", response.data)


if __name__ == "__main__":
    unittest.main()
