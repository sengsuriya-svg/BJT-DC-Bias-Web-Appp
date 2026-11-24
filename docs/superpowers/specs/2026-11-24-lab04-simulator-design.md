# Lab 04 CE Amplifier Simulator — Short Design

**Date:** 2026-11-24
**Source:** `C:\Users\b6829513\Downloads\Lab04_BJT_Amplifier_Simulator_2-2569.html`
**Status:** Approved by user instruction to proceed with the 180-minute activities; A1–A5 already complete.

## Intent

Extend the existing Flask Lab 3 BJT DC Bias web app into a minimal BJT Common-Emitter
Amplifier Simulator v1. Keep the three analytical DC bias modes working exactly as they
are. Add a separate SPICE path for **one** reference voltage-divider CE circuit with
DC `.op`, AC `.ac`, and transient `.tran` results from a real external ngspice process.

## Goals

- Preserve `bjt_model.calculate_bjt_bias` and the existing Fixed / Emitter / Divider form.
- Add an Analysis Mode selector: Analytical DC Bias (default) / SPICE DC / SPICE AC / SPICE Transient.
- Add CE reference inputs: VCC, R1, R2, RC, RE, RL, Cin, Cout, source amplitude, source frequency.
- Generate a documented netlist, run `ngspice -b -o <log> <netlist>` via `subprocess.run`
  with a list of arguments, `shell=False`, a timeout, and a fresh temp working directory.
- Parse real ngspice output into values + units, and render SVG plots from those parsed points.
- Label SPICE results and Analytical results separately, with engine status and BJT model shown.
- Fail visibly when ngspice is missing, errors, times out, or produces empty output. Never show
  a stale graph with a success status.

## Non-goals

- No fabricated traces, hard-coded gain/cutoff values, or mock plots.
- No claim that the BJT model is instructor-verified: no starter kit was provided.
- No rewrite of the Lab 3 app, no new React/Vite frontend, no chart-library dependency.
- No commit, push, or Render deployment — the user handles those.
- No free-form circuit editor, FET, emitter bypass capacitor, or AC for all bias modes.

## Constraints

- Flask `3.0.2`, gunicorn `21.2.0` stay in `requirements.txt`; no new runtime dependency.
- Tests use Python `unittest` so no test dependency is added.
- Input validation before netlist creation: positive resistances/capacitances, VCC > 0,
  amplitude > 0, frequency > 0, bounded values, unit whitelist `ohm|kohm|mohm`.
- Generic NPN model card with explicit documented assumptions (BF=100, VAF=100,
  IS=1e-14, RB=10, RC=1) is used because no verified starter model exists.
- Baseline CE fixture: VCC 12 V, R1 100 kΩ, R2 22 kΩ, RC 2.2 kΩ, RE 1 kΩ,
  RL 10 kΩ, Cin/Cout 10 µF, source 10 mV peak at 1 kHz.
- Local ngspice is absent; SPICE browser cases B2–B6 must be recorded as NOT RUN until
  the user installs ngspice and deploys it on Render.

## Approaches considered

1. **Reuse a starter kit adapter** — rejected: no starter files exist locally or in the repo.
2. **Install ngspice immediately and build a verified parser** — deferred: user handles
   environment/Render, and handout forbids inventing an instructor-verified model.
3. **Write a self-contained adapter with honest error states and unit-tested parsers** — chosen:
   code is ready when ngspice becomes available, and failure is explicit rather than faked.

## Builder decisions

- `spice_engine.py` owns validation, netlist generation, execution, and parsing.
- `plots.py` owns SVG generation from parsed numeric points only.
- `app.py` dispatches between the untouched analytical path and the SPICE path.
- `templates/index.html` keeps the old form and adds the SPICE section.
- `docs/validation.md` records B1–B8 truthfully, including NOT RUN entries.
