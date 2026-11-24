# Lab 04 Browser / Engineering Validation

This file records what was actually executed. A `PASS` requires observed evidence; an unrun case is `NOT RUN` with a reason. Screenshots are stored in [`evidence/`](evidence/).

Environment notes:
- Analysis date: 2026-11-24
- Local Python: 3.15.x; Flask 3.0.2 (installed from `requirements.txt`)
- Local server: `python -m flask --app app run --port 5000` → `http://127.0.0.1:5000/`
- Browser: Chromium driven by the OpenCode browser tool (accessibility snapshot + DOM geometry + screenshots)
- ngspice: **not installed locally** (`ngspice --version` → command not found); therefore no SPICE trace can be produced here
- Instructor starter kit: **not supplied** (no netlist/model/adapter files found)
- Deployed site check: `https://bjt-dc-bias-web-appp.onrender.com/` still renders **Lab 03** (`<title>Lab 03: BJT DC Bias Web App</title>`, no `[name=analysis]`, no `#spice-panel`). The Lab 04 files in this working tree are uncommitted, so they were not part of that deployment.

| Case | Method | Input | Expected/Reference | Observed | Evidence | Status |
| --- | --- | --- | --- | --- | --- | --- |
| B1 | Local browser form submit + `unittest` regression | Divider: VCC 12 V, R1 100 kΩ, R2 22 kΩ, RC 2.2 kΩ, RE 1 kΩ, β 100, VBE 0.7 V | Analytical VB/VE/VC/VCE/IB/IC/IE render with no error | Browser showed VB 2.16 V, VE 1.46 V, VC 8.78 V, VCE 7.32 V, IB 14.64 µA, IC 1.46 mA, IE 1.46 mA, “Active region OK”; no `error-msg` | [`evidence/B1-analytical-desktop.jpeg`](evidence/B1-analytical-desktop.jpeg); browser snapshot; `tests.test_app.AppTests.test_analytical_divider_still_works`; 14/14 unittest OK | PASS |
| B2 | Browser `.op` run | Reference CE defaults | VB/VE/VC/VCE/IC from real ngspice output with engine/model/status | Not executed: local ngspice missing; deployed site is still Lab 03 | `ngspice --version` failed; live-site DOM check above | NOT RUN |
| B3 | Browser RE change | Change RE only, rerun DC | Operating point changes from a new run | Not executed | Same as B2 | NOT RUN |
| B4 | Browser `.ac` run | AC mode defaults | Frequency / gain-dB / phase axes from real run | Not executed | Same as B2 | NOT RUN |
| B5 | Browser `.tran` run | 10 mV peak, 1 kHz | Vin/Vout vs time with units; expected inversion | Not executed | Same as B2 | NOT RUN |
| B6 | Browser source change | Change amplitude or frequency, rerun | Waveform changes with input | Not executed | Same as B2 | NOT RUN |
| B7 | Local browser SPICE submit + unit tests | Analysis mode `SPICE · DC`, default CE values, ngspice absent | Visible engine error, status `error`, no plot | `.error-msg` = “ngspice not found in PATH; install ngspice before running SPICE analysis”; badge = “Engine: ngspice · Model: NPN_GENERIC (BF=100, VAF=100, IS=1e-14, RB=10, RC=1) · Status: error”; `plot-frame` count = 0; no “Status: success” text | [`evidence/B7-spice-error-desktop.jpeg`](evidence/B7-spice-error-desktop.jpeg); DOM evaluation; `tests.test_app.AppTests.test_spice_error_shows_no_success`; `tests.test_spice_engine.ErrorTests.test_missing_engine_returns_error_without_points` | PASS |
| B8 | Desktop/mobile layout inspection | Desktop viewport 1296 px; 390 px iframe rendering the same page with SPICE panel open | Inputs, status, units visible; nothing clipped | Desktop: clientWidth 1281, scrollWidth 1281 (no horizontal overflow), `.spice-grid` = `606.5px 606.5px`, 10 inputs, max input right edge 1172 px < 1281 px, badge/error visible. Mobile: viewport 390, clientWidth 375, scrollWidth 375 (no overflow), `matchMedia('(max-width: 760px)')` true, `.spice-grid` = `323px` (single column), 10 inputs, max right edge 266 px < 375 px, header font 16 px | [`evidence/B8-mobile-390px.jpeg`](evidence/B8-mobile-390px.jpeg) plus DOM geometry from both viewports; screenshots captured but this model cannot visually read image pixels, so layout verdict is based on accessibility snapshot + measured geometry | PASS (geometry/a11y) |

## Known gaps

- No verified ngspice version or BJT model can be reported because the executable is absent locally.
- No SPICE plot may be claimed as real until B2–B6 are run with ngspice available.
- The UI uses the documented generic `NPN_GENERIC` model; it is not instructor-verified.
- The deployed Render site currently serves the older Lab 03 build; the user handles commit/push/deploy separately.
