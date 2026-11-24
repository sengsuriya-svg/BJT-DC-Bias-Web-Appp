# Lab 04 CE Amplifier Simulator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the existing Flask Lab 3 app with a real ngspice DC/AC/Transient path for one reference CE voltage-divider circuit while preserving all three analytical DC bias modes.

**Architecture:** `spice_engine.py` validates input, writes a documented netlist, runs `ngspice -b -o` via `subprocess.run` (list args, no shell, timeout, fresh temp dir), and parses ASCII `.print` output into numeric points. `plots.py` turns only those parsed numbers into inline SVG. `app.py` dispatches to the untouched analytical path or the SPICE path; Jinja renders both with explicit provenance labels.

**Tech Stack:** Python 3, Flask 3.0.2, Jinja, stdlib `unittest`, `subprocess`, inline SVG. No new runtime dependency.

**Spec:** `docs/superpowers/specs/2026-11-24-lab04-simulator-design.md`

## Global Constraints

- Do **not** commit, push, or deploy. The user handles GitHub and Render.
- Keep `bjt_model.calculate_bjt_bias` and the Fixed / Emitter / Divider form working unchanged.
- Use `subprocess.run([...], shell=False, timeout=...)` with a fresh temp working directory per run.
- Validate all inputs before netlist creation; unit whitelist `ohm|kohm|mohm`, capacitor units `pF|nF|uF`.
- No fabricated traces, hard-coded gain/cutoff, or mock success. Missing/errored ngspice returns an error status and no plot.
- SPICE results and analytical results must be labeled separately with units and engine/model provenance.
- Generic NPN model assumptions must be printed in the UI; do not call it instructor-verified.
- Tests use `unittest` only. Run with `python -m unittest discover -s tests -v`.

## Review Focus

- `RE = 0` or negative resistance → validation error before any netlist is written; tested in Task 1.
- `ngspice` missing from PATH → `status="error"`, no plot, no success text; tested in Task 1.
- Empty or malformed ngspice log → parser returns explicit error, not stale data; tested in Task 1.
- Changing amplitude/frequency must change netlist values and parsed points; tested in Task 1.
- Analytical regression must still work after UI changes; tested in Task 3 and browser Task 6.

---

### Task 1: SPICE engine with validation, netlist, run, and parsers

**Files:**
- Create: `spice_engine.py`
- Test: `tests/test_spice_engine.py`

**Interfaces:**
- Consumes: Flask form `ImmutableMultiDict`-like mapping from `app.py`.
- Produces:
  - `validate_ce_inputs(form) -> (params|None, error|None)` where `params` has SI values in keys `vcc, r1, r2, rc, re, rl, cin, cout, amplitude, frequency` plus `model`.
  - `build_netlist(params, analysis) -> str` for `analysis in {"dc","ac","tran"}`.
  - `run_ngspice(netlist, timeout=20.0) -> {"ok":bool,"log":str,"error":str|None,"netlist":str}`.
  - `parse_dc(log, params) -> {"values":dict,"error":str|None}`.
  - `parse_ac(log) -> {"points":list,"error":str|None}`.
  - `parse_tran(log) -> {"points":list,"error":str|None}`.
  - `simulate(form, analysis) -> {"status","analysis","engine","model","netlist","values","points","error","log_excerpt"}`.

- [ ] **Step 1: Write failing tests** in `tests/test_spice_engine.py`

```python
import unittest
from unittest.mock import patch
import spice_engine

BASE_FORM = {
    "vcc":"12","r1":"100","r1_unit":"kohm","r2":"22","r2_unit":"kohm",
    "rc":"2.2","rc_unit":"kohm","re":"1","re_unit":"kohm",
    "rl":"10","rl_unit":"kohm","cin":"10","cin_unit":"uF",
    "cout":"10","cout_unit":"uF","amplitude":"0.01","frequency":"1000",
}

class ValidationTests(unittest.TestCase):
    def test_valid_form_returns_si_values(self):
        params, err = spice_engine.validate_ce_inputs(BASE_FORM)
        self.assertIsNone(err)
        self.assertAlmostEqual(params["r1"], 100000.0)
        self.assertAlmostEqual(params["cin"], 10e-6)

    def test_zero_emitter_resistor_is_rejected(self):
        form = dict(BASE_FORM, re="0")
        params, err = spice_engine.validate_ce_inputs(form)
        self.assertIsNone(params)
        self.assertIn("RE", err)

    def test_bad_unit_is_rejected(self):
        form = dict(BASE_FORM, rc_unit="kilo")
        params, err = spice_engine.validate_ce_inputs(form)
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
        log = "v(base) = 2.530000e+00\nv(emit) = 1.830000e+00\nv(col) = 6.710000e+00\n"
        out = spice_engine.parse_dc(log, {"rc":2200.0, "vcc":12.0})
        self.assertIsNone(out["error"])
        self.assertAlmostEqual(out["values"]["vce"], 4.88, places=2)

    def test_parse_ac_reads_frequency_gain_phase(self):
        log = "Index frequency vdb(out) vp(out)\n1 1.000e+00 -4.20e+00 1.75e+02\n2 1.000e+03 2.10e+01 -1.65e+02\n"
        out = spice_engine.parse_ac(log)
        self.assertEqual(len(out["points"]), 2)
        self.assertAlmostEqual(out["points"][1][1], 21.0)

    def test_parse_tran_reads_time_vin_vout(self):
        log = "Index time v(src) v(out)\n1 0.000e+00 0.000e+00 0.000e+00\n2 1.000e-03 1.000e-02 -2.100e-01\n"
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

    @patch("spice_engine.run_ngspice", return_value={"ok":True,"log":"","error":None,"netlist":"x"})
    def test_empty_log_is_error(self, _):
        out = spice_engine.simulate(BASE_FORM, "ac")
        self.assertEqual(out["status"], "error")
        self.assertIsNone(out["points"])
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m unittest discover -s tests -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'spice_engine'`.

- [ ] **Step 3: Implement `spice_engine.py`**

Use the exact signatures from Interfaces. Build the deck with `VCC VCC 0 DC <vcc>`,
`R1 VCC BASE`, `R2 BASE 0`, `RC VCC COL`, `RE EMI 0`, `Q1 COL BASE EMI NPN_GENERIC`,
`CIN SRC BASE`, `COUT COL OUT`, `RL OUT 0`, `VIN SRC 0 SIN(0 <amplitude> <frequency>) AC <amplitude>`,
`.op`, the selected analysis, and a matching `.print` line. Run with
`["ngspice", "-b", "-o", log_name, netlist_name]` in `tempfile.TemporaryDirectory()`.
Parsers must tolerate both `name = value` and tabular `.print` output; raise an explicit
error string on no numeric rows. `simulate()` wraps validation, build, run, parse, and a
200-character `log_excerpt`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest discover -s tests -v`
Expected: all tests PASS.

---

### Task 2: SVG plotting from parsed points

**Files:**
- Create: `plots.py`
- Test: `tests/test_plots.py`

**Interfaces:**
- Consumes: `points` lists from `spice_engine.simulate`.
- Produces: `line_svg(points, x_label, y_label, title, series_labels=None) -> str`.

- [ ] **Step 1: Write failing tests** in `tests/test_plots.py`

```python
import unittest
from plots import line_svg

class PlotTests(unittest.TestCase):
    def test_svg_contains_polylines_and_labels(self):
        svg = line_svg([[0,0,0],[1,1,-1]], "Time (ms)", "Voltage (V)", "Vin / Vout", ["Vin","Vout"])
        self.assertIn("<svg", svg)
        self.assertIn("<polyline", svg)
        self.assertIn("Time (ms)", svg)
        self.assertIn("Vin", svg)
        self.assertNotIn("<script", svg)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m unittest tests.test_plots -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'plots'`.

- [ ] **Step 3: Implement `plots.py`**

Map numeric min/max to a `viewBox="0 0 640 260"` coordinate system, draw axis lines, one
`<polyline>` per series, and text labels. Escape all label text with `html.escape`.
Return the SVG string only; never embed data fetched from anywhere else.

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m unittest tests.test_plots -v`
Expected: PASS.

---

### Task 3: Wire Flask route while preserving analytical regression

**Files:**
- Modify: `app.py:1-41`
- Test: `tests/test_app.py`

**Interfaces:**
- Consumes: `spice_engine.simulate`, `plots.line_svg`, `bjt_model.calculate_bjt_bias`.
- Produces: `index()` renders `results`, `spice_result`, `selected_mode`, `selected_analysis`, `form`.

- [ ] **Step 1: Write failing tests** in `tests/test_app.py`

```python
import unittest
from unittest.mock import patch
from app import app

class AppTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_analytical_divider_still_works(self):
        r = self.client.post("/", data={
            "analysis":"bias","mode":"divider","vcc":"12","r1":"100","r2":"22",
            "rc":"2.2","re":"1","beta":"100","vbe":"0.7",
        })
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"DC Bias Results", r.data)
        self.assertNotIn(b"error-msg", r.data)

    @patch("app.simulate", return_value={"status":"error","error":"ngspice not found","analysis":"dc"})
    def test_spice_error_shows_no_success(self, _):
        r = self.client.post("/", data={"analysis":"spice_dc","vcc":"12"})
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"ngspice not found", r.data)
        self.assertNotIn(b"Engine status: success", r.data)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m unittest tests.test_app -v`
Expected: FAIL because `app` has no `simulate` import and no analysis dispatch.

- [ ] **Step 3: Modify `app.py`**

Keep the existing analytical `try/except ValueError` block unchanged for
`analysis == "bias"`. For `spice_dc|spice_ac|spice_tran`, map to `dc|ac|tran`, call
`simulate(request.form, mapped)`, and attach a `plot` key with `line_svg(...)` only on
success (DC uses a single-value table instead of a plot). Pass `form=request.form` so the
template can repopulate inputs.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest discover -s tests -v`
Expected: all tests PASS.

---

### Task 4: UI refinement for analysis modes and results

**Files:**
- Modify: `templates/index.html`
- Modify: `static/style.css`

**Interfaces:**
- Consumes: `spice_result`, `selected_analysis`, `form` from `app.py`.
- Produces: a single page with Analytical panel and SPICE panel, status badge, values table, and SVG plot area.

- [ ] **Step 1: Add the Analysis Mode selector and SPICE fieldset to `templates/index.html`**

Add a `<select name="analysis">` with values `bias`, `spice_dc`, `spice_ac`, `spice_tran`.
Keep the complete existing bias form inside `<div id="bias-panel">`. Add
`<div id="spice-panel">` with the CE reference inputs and units from the spec. Repopulate
values with `form.get(...)`. Add inline JS to show only the active panel.

- [ ] **Step 2: Add SPICE results rendering**

Show `Engine: ngspice`, `Model: NPN_GENERIC (BF=100, VAF=100, IS=1e-14, RB=10, RC=1)`,
and `Status: ...`. On error show `error-msg` and no plot. On success show a values table
with units and `{{ spice_result.plot|safe }}`. Keep the analytical results section intact
and add a heading `Analytical reference (Lab 3)` above it.

- [ ] **Step 3: Update `static/style.css`**

Add `.analysis-panel`, `.engine-badge`, `.spice-grid`, `.plot-frame`, and responsive
`@media (max-width: 760px)` rules so inputs and SVG are readable on a ~390 px viewport.
Do not change analytical result markup.

- [ ] **Step 4: Verify rendering**

Run: `python -m unittest discover -s tests -v`
Expected: all tests PASS (the app test asserts the analytical section remains).

---

### Task 5: Documentation and honest validation record

**Files:**
- Modify: `README.md`
- Create: `docs/validation.md`

- [ ] **Step 1: Update `README.md`**

Add setup steps: Python 3, `pip install -r requirements.txt`, `ngspice --version`,
`python -m flask --app app run`. Document the generic NPN model assumption, the netlist
format, the `ngspice -b -o` invocation, and that Render must supply ngspice separately.

- [ ] **Step 2: Create `docs/validation.md`**

Use the handout's table columns `Case | Method | Input | Expected/Reference | Observed | Evidence | Status`.
Fill B1 with the unit-test/browser result actually obtained. Fill B2–B6 as `NOT RUN`
with reason `ngspice not installed in local environment and no instructor starter kit`.
Fill B7 with the engine-missing error test result. Fill B8 with the browser result actually
obtained. Do not mark anything PASS without executed evidence.

---

### Task 6: Local browser acceptance for runnable cases

**Files:**
- No code changes unless a defect is found.

- [ ] **Step 1: Start the Flask server**

Run: `python -m flask --app app run --port 5000`
Expected: server starts on `http://127.0.0.1:5000/`.

- [ ] **Step 2: Use the browser tool to run B1, B7, and B8**

Load the `browser` skill first. Navigate, snapshot, submit the analytical divider form,
submit a SPICE form with ngspice missing, and inspect desktop/mobile viewports. Record
observed values and screenshots/evidence in `docs/validation.md`.

- [ ] **Step 3: Record B2–B6 as NOT RUN**

Do not claim SPICE results. Update `docs/validation.md` with the exact reason.
