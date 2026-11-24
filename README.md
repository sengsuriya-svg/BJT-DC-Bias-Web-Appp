---
title: BJT CE Amplifier Simulator
emoji: ⚡
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
---

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

SPICE modes need an `ngspice` executable. The app looks on `PATH` first, then (on Linux) in the committed `vendor/ngspice/bin/ngspice`, then in `.ngspice/bin/ngspice` if a user-level install was created. If none exists, the app shows an explicit error and no plot — it never returns a fake success.

The committed `vendor/ngspice/` bundle is a Linux x86-64 ngspice 41 build from conda-forge with its required shared libraries under `lib/` and XSPICE code models under `lib/ngspice/`. It has RPATH `$ORIGIN/../lib`, so no `LD_LIBRARY_PATH`, `apt-get`, `sudo` or Render Shell is needed. Windows ignores this bundle: download the installer from the [ngspice download page](https://ngspice.sourceforge.io/download.html), install it, and add the install folder to `PATH`.

### Deploying with Docker (recommended: Hugging Face Spaces, free)

The included `Dockerfile` installs `ngspice` from the Debian package during the **Docker image build**, where root access is available. This avoids the permission problem of Render's free Native runtime entirely. It serves the app with `gunicorn` on `0.0.0.0:${PORT:-7860}`, which matches Hugging Face Spaces (`7860`) and Render Docker (`$PORT`).

For a public URL on Hugging Face Spaces:

1. Sign in to Hugging Face → **New → Space** → owner: you, SDK: **Docker**, visibility: **Public** → create the Space.
2. If the Space is empty, push this repository to it (replace the placeholders):
   ```bash
   git remote add space https://huggingface.co/spaces/<YOUR_USER>/<YOUR_SPACE>
   git push space main
   ```
   The `README.md` frontmatter already declares `sdk: docker` and `app_port: 7860`.
3. Wait for **Building → Running**, then open `https://huggingface.co/spaces/<YOUR_USER>/<YOUR_SPACE>` and submit a SPICE analysis. The badge must show `Engine: ngspice` and `Status: success`.

The same `Dockerfile` also works on a **Render Docker Web Service** if you prefer to stay on Render; create a new Docker service from this repo and leave its Build/Start Commands at the Docker defaults.

### Deploying on Render (free / Native runtime)

**No Build Command change is needed.** Remove the `apt-get ...` Build Command if you added it — Render free Native environments do not grant OS-level package install rights, so `apt-get` fails before the app starts. Leave the service at its default Python settings (`pip install -r requirements.txt`) and keep the existing **Start Command** unchanged. The committed Linux binary in `vendor/ngspice/` is checked out with the repo and discovered automatically at runtime.

Use **Manual Deploy → Deploy latest commit**. To confirm the engine after deploy, open the site and submit a SPICE analysis: the result badge shows `Engine: ngspice` and `Status: success` with real values/plot. If the binary cannot be found, the page shows `ngspice not found in PATH; install ngspice before running SPICE analysis` and draws no plot — it never invents a trace.

`scripts/install_ngspice.py` is kept only as an optional fallback: if you prefer to install ngspice at build time, set Build Command to `python scripts/install_ngspice.py && pip install -r requirements.txt`. It uses a user-level micromamba environment under `.ngspice/` and needs no root access. It is **not** required for the default deploy.

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
3. `spice_engine.build_netlist` writes a batch netlist with `.op` (its node-voltage table is parsed directly) or the selected `.ac` / `.tran` directive with matching `.print` statements.
4. `subprocess.run([resolved_ngspice, "-b", "-o", "run.log", "circuit.cir"], ...)` runs with `shell=False` in a fresh temporary directory with a timeout. `resolved_ngspice` is the executable found on `PATH`, the committed `vendor/ngspice/bin/ngspice` on Linux, or the optional `.ngspice/bin/ngspice`.
5. The ASCII `run.log` is parsed into values/points; `plots.py` draws the SVG. Errors, timeouts and empty logs produce an error status with no plot.

## Tests

```bash
python -m unittest discover -s tests -v
```

The suite covers validation, netlist generation, parsers, engine-missing and empty-log error paths, SVG output, analytical regression and UI availability.

## Current limitations

- No starter kit was provided, so no instructor-verified BJT model exists here.
- B2–B6 were executed locally with a portable Windows ngspice 47 binary on `PATH`; see [`docs/validation.md`](docs/validation.md). The committed Linux bundle is ngspice 41 from conda-forge. Its ELF RPATH and `DT_NEEDED` closure were checked statically, but it cannot be executed in this Windows environment (no Docker/WSL), so the Render runtime itself is unverified here. The Docker image installs Debian's `ngspice` package instead.
- Only the reference voltage-divider CE stage is simulated. Fixed/Emitter bias remain analytical only.
- No emitter bypass capacitor, no free-form circuit editor, and no `render.yaml` in this repository — deployment is either the included `Dockerfile` or the Render Dashboard Build Command documented above.
