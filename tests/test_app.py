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
        self.assertNotIn(b"Engine status: success", response.data)

    def test_page_offers_analysis_modes_and_spice_inputs(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'name="analysis"', response.data)
        self.assertIn(b'spice-panel', response.data)
        self.assertIn(b'value="spice_dc"', response.data)
        self.assertIn(b'name="amplitude"', response.data)


if __name__ == "__main__":
    unittest.main()
