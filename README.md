# BJT-DC-Bias-Web-Appp

Flask web app for ENG29 2121. The Lab 3 analytical DC-bias calculator is preserved, and Lab 04 adds a reference Common-Emitter amplifier simulator driven by an external ngspice process.

## What is included

- **Analytical DC Bias (Lab 3):** Fixed, Emitter and Voltage Divider modes via `bjt_model.calculate_bjt_bias`.
- **SPICE CE simulator (Lab 04):** one voltage-divider CE stage with DC `.op`, AC `.ac` and transient `.tran` runs.
- `spice_engine.py`: validates inputs, converts units, writes a netlist, calls `ngspice -b -o`, and parses real output.
- `plots.py`: renders inline SVG from parsed numeric points only. No fabricated or hard-coded traces.

## Setup

```bash
python --version          # Python 3.x
python -m pip install -r requirements.txt
python -m flask --app app run
# open http://127.0.0.1:5000/
```

### ngspice (external program, not a pip package)

SPICE modes require the `ngspice` executable on `PATH`:

```bash
ngspice --version
```

On Windows, download the installer from the [ngspice download page](https://ngspice.sourceforge.io/download.html), install it, and add the install folder to `PATH`. If it is missing, the app shows an explicit error and no plot — it never returns a fake success.

The production host (Render) must also provide ngspice in its build/runtime environment; this repository does not install it automatically.

## Reference circuit and model

Baseline fixture used by the SPICE panel:

| Parameter | Value |
| --- | --- |
| VCC | 12 V |
| R1 / R2 | 100 kΩ / 22 kΩ |
| RC / RE / RL | 2.2 kΩ / 1 kΩ / 10 kΩ |
| Cin / Cout | 10 µF / 10 µF |
| Source | 10 mV peak, 1 kHz |
| BJT | `NPN_GENERIC` (BF=100, VAF=100, IS=1e-14, RB=10, RC=1) |

No instructor-verified starter kit was supplied, so the BJT model above is a **documented generic assumption**, not a specific part number and not instructor-verified. SPICE results are labeled separately from the analytical Lab 3 results.

## How a SPICE run works

1. The browser submits CE values and the selected analysis.
2. `spice_engine.validate_ce_inputs` checks numbers, ranges and units.
3. `spice_engine.build_netlist` writes a batch netlist with `.op` and the selected `.ac` / `.tran` directive plus matching `.print` statements.
4. `subprocess.run(["ngspice", "-b", "-o", "run.log", "circuit.cir"], ...)` runs in a fresh temporary directory with a timeout.
5. The ASCII `run.log` is parsed into values/points; `plots.py` draws the SVG. Errors, timeouts and empty logs produce an error status with no plot.

## Tests

```bash
python -m unittest discover -s tests -v
```

The suite covers validation, netlist generation, parsers, engine-missing and empty-log error paths, SVG output, analytical regression and UI availability.

## Current limitations

- No starter kit was provided, so no instructor-verified BJT model exists here.
- ngspice was not installed in the local development environment when this code was written; browser cases B2–B6 are recorded as `NOT RUN` in [`docs/validation.md`](docs/validation.md).
- Only the reference voltage-divider CE stage is simulated. Fixed/Emitter bias remain analytical only.
- No emitter bypass capacitor, no free-form circuit editor, and no deployment changes in this repository.
