import unittest
from unittest.mock import patch

import spice_engine


BASE_FORM = {
    "vcc": "12",
    "r1": "100", "r1_unit": "kohm",
    "r2": "22", "r2_unit": "kohm",
    "rc": "2.2", "rc_unit": "kohm",
    "re": "1", "re_unit": "kohm",
    "rl": "10", "rl_unit": "kohm",
    "cin": "10", "cin_unit": "uF",
    "cout": "10", "cout_unit": "uF",
    "amplitude": "0.01",
    "frequency": "1000",
}


class ValidationTests(unittest.TestCase):
    def test_valid_form_returns_si_values(self):
        params, err = spice_engine.validate_ce_inputs(BASE_FORM)
        self.assertIsNone(err)
        self.assertAlmostEqual(params["r1"], 100000.0)
        self.assertAlmostEqual(params["cin"], 10e-6)

    def test_zero_emitter_resistor_is_rejected(self):
        params, err = spice_engine.validate_ce_inputs(dict(BASE_FORM, re="0"))
        self.assertIsNone(params)
        self.assertIn("RE", err)

    def test_bad_unit_is_rejected(self):
        params, err = spice_engine.validate_ce_inputs(dict(BASE_FORM, rc_unit="kilo"))
        self.assertIsNone(params)
        self.assertIn("unit", err.lower())


class NetlistTests(unittest.TestCase):
    def test_ac_netlist_contains_values_and_analysis(self):
        params, _ = spice_engine.validate_ce_inputs(BASE_FORM)
        deck = spice_engine.build_netlist(params, "ac")
        self.assertIn("R1 VCC BASE 100000", deck)
        self.assertIn(".ac dec", deck)
        self.assertIn(".print ac", deck)
        self.assertIn(".model NPN_GENERIC", deck)

    def test_amplitude_change_appears_in_tran_netlist(self):
        params, _ = spice_engine.validate_ce_inputs(BASE_FORM)
        deck = spice_engine.build_netlist(params, "tran")
        self.assertIn("SIN(0 0.01 1000)", deck)


class ParserTests(unittest.TestCase):
    def test_parse_dc_reads_operating_point(self):
        log = (
            "v(base) = 2.530000e+00\n"
            "v(emit) = 1.830000e+00\n"
            "v(col) = 6.710000e+00\n"
        )
        out = spice_engine.parse_dc(log, {"rc": 2200.0, "vcc": 12.0})
        self.assertIsNone(out["error"])
        self.assertAlmostEqual(out["values"]["vce"], 4.88, places=2)

    def test_parse_ac_reads_frequency_gain_phase(self):
        log = (
            "Index frequency vdb(out) vp(out)\n"
            "1 1.000e+00 -4.20e+00 1.75e+02\n"
            "2 1.000e+03 2.10e+01 -1.65e+02\n"
        )
        out = spice_engine.parse_ac(log)
        self.assertEqual(len(out["points"]), 2)
        self.assertAlmostEqual(out["points"][1][1], 21.0)

    def test_parse_tran_reads_time_vin_vout(self):
        log = (
            "Index time v(src) v(out)\n"
            "1 0.000e+00 0.000e+00 0.000e+00\n"
            "2 1.000e-03 1.000e-02 -2.100e-01\n"
        )
        out = spice_engine.parse_tran(log)
        self.assertEqual(len(out["points"]), 2)
        self.assertAlmostEqual(out["points"][1][2], -0.21)


class ErrorTests(unittest.TestCase):
    @patch("spice_engine.shutil.which", return_value=None)
    def test_missing_engine_returns_error_without_points(self, _):
        out = spice_engine.simulate(BASE_FORM, "dc")
        self.assertEqual(out["status"], "error")
        self.assertIsNone(out["points"])
        self.assertIn("ngspice", out["error"].lower())

    @patch(
        "spice_engine.run_ngspice",
        return_value={"ok": True, "log": "", "error": None, "netlist": "x"},
    )
    def test_empty_log_is_error(self, _):
        out = spice_engine.simulate(BASE_FORM, "ac")
        self.assertEqual(out["status"], "error")
        self.assertIsNone(out["points"])


if __name__ == "__main__":
    unittest.main()
