"""Ngspice adapter for the Lab 04 reference CE amplifier.

The module owns four things: input validation, netlist generation, execution of
the external ngspice process, and parsing of its ASCII ``.print`` output. It
never invents a result: any missing engine, failed run, or empty output is
returned as an explicit error with no plottable data.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

RESISTANCE_UNITS = {"ohm": 1.0, "kohm": 1e3, "mohm": 1e6}
CAPACITANCE_UNITS = {"pf": 1e-12, "nf": 1e-9, "uf": 1e-6}
MODEL_NAME = "NPN_GENERIC"
MODEL_CARD = ".model NPN_GENERIC NPN(BF=100 VAF=100 IS=1e-14 RB=10 RC=1)"
MODEL_LABEL = "NPN_GENERIC (BF=100, VAF=100, IS=1e-14, RB=10, RC=1)"
ANALYSES = {"dc", "ac", "tran"}

_NUMBER_RE = re.compile(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?")


def _fmt(value: float) -> str:
    return f"{value:.6g}"


def _number(form, key: str, label: str, low: float, high: float) -> tuple[float | None, str | None]:
    raw = form.get(key)
    if raw is None or str(raw).strip() == "":
        return None, f"{label} is required"
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None, f"{label} must be a number"
    if not low <= value <= high:
        return None, f"{label} must be between {low} and {high}"
    return value, None


def _scaled(
    form,
    key: str,
    unit_key: str,
    units: dict[str, float],
    label: str,
    high: float,
) -> tuple[float | None, str | None]:
    raw = form.get(unit_key, "")
    unit = str(raw).strip().lower()
    if unit not in units:
        allowed = ", ".join(sorted(units))
        return None, f"{label} unit must be one of {allowed}"
    multiplier = units[unit]
    value, error = _number(form, key, label, 0.0, high / multiplier)
    if error:
        return None, error
    if value == 0:
        return None, f"{label} must be greater than 0"
    return value * multiplier, None


def validate_ce_inputs(form) -> tuple[dict | None, str | None]:
    """Validate a Flask-like form mapping and return SI-unit circuit values."""
    params: dict[str, float | str] = {}

    vcc, error = _number(form, "vcc", "VCC", 0.1, 100.0)
    if error:
        return None, error
    params["vcc"] = vcc

    for key, label in (
        ("r1", "R1"), ("r2", "R2"), ("rc", "RC"),
        ("re", "RE"), ("rl", "RL"),
    ):
        value, error = _scaled(
            form, key, f"{key}_unit", RESISTANCE_UNITS, label, 1e7
        )
        if error:
            return None, error
        params[key] = value

    for key, label in (("cin", "Cin"), ("cout", "Cout")):
        value, error = _scaled(
            form, key, f"{key}_unit", CAPACITANCE_UNITS, label, 1e-3
        )
        if error:
            return None, error
        params[key] = value

    amplitude, error = _number(form, "amplitude", "Source amplitude", 1e-6, 10.0)
    if error:
        return None, error
    params["amplitude"] = amplitude

    frequency, error = _number(form, "frequency", "Source frequency", 1.0, 1e9)
    if error:
        return None, error
    params["frequency"] = frequency
    params["model"] = MODEL_LABEL

    return params, None


def build_netlist(params: dict, analysis: str) -> str:
    """Write a batch-mode netlist for one reference CE voltage-divider circuit."""
    if analysis not in ANALYSES:
        raise ValueError(f"Unsupported analysis: {analysis}")

    t_stop = max(5.0 / params["frequency"], 1e-3)
    t_step = t_stop / 200.0

    analysis_lines = {
        "dc": [".op", ".print op v(base) v(emit) v(col)"],
        "ac": [".ac dec 20 1 10Meg", ".print ac frequency vdb(out) vp(out)"],
        "tran": [
            f".tran {_fmt(t_step)} {_fmt(t_stop)}",
            ".print tran time v(src) v(out)",
        ],
    }

    lines = [
        "* Lab 04 reference CE voltage-divider amplifier",
        ".option numdgt=6",
        f"VCC VCC 0 DC {_fmt(params['vcc'])}",
        f"R1 VCC BASE {_fmt(params['r1'])}",
        f"R2 BASE 0 {_fmt(params['r2'])}",
        f"RC VCC COL {_fmt(params['rc'])}",
        f"RE EMI 0 {_fmt(params['re'])}",
        f"Q1 COL BASE EMI {MODEL_NAME}",
        f"CIN SRC BASE {_fmt(params['cin'])}",
        f"COUT COL OUT {_fmt(params['cout'])}",
        f"RL OUT 0 {_fmt(params['rl'])}",
        "VIN SRC 0 "
        f"SIN(0 {_fmt(params['amplitude'])} {_fmt(params['frequency'])}) "
        f"AC {_fmt(params['amplitude'])}",
        MODEL_CARD,
        *analysis_lines[analysis],
        ".end",
    ]
    return "\n".join(lines) + "\n"


def run_ngspice(netlist: str, timeout: float = 20.0) -> dict:
    """Execute ngspice in batch mode in a fresh temporary directory."""
    if shutil.which("ngspice") is None:
        return {
            "ok": False,
            "log": "",
            "error": "ngspice not found in PATH; install ngspice before running SPICE analysis",
            "netlist": netlist,
        }

    try:
        with tempfile.TemporaryDirectory(prefix="bjt-spice-") as directory:
            workdir = Path(directory)
            netlist_path = workdir / "circuit.cir"
            log_path = workdir / "run.log"
            netlist_path.write_text(netlist, encoding="utf-8")

            completed = subprocess.run(
                ["ngspice", "-b", "-o", log_path.name, netlist_path.name],
                cwd=str(workdir),
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            log = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
            if not log.strip():
                log = completed.stdout or ""
            error = None
            if completed.returncode != 0:
                error = (
                    f"ngspice exited with code {completed.returncode}: "
                    f"{(completed.stderr or log).strip()[:300]}"
                )
            elif not log.strip():
                error = "ngspice produced no output"
            return {"ok": error is None, "log": log, "error": error, "netlist": netlist}
    except subprocess.TimeoutExpired:
        return {"ok": False, "log": "", "error": f"ngspice timed out after {timeout}s", "netlist": netlist}
    except OSError as exc:
        return {"ok": False, "log": "", "error": f"could not start ngspice: {exc}", "netlist": netlist}


def _extract_named(log: str, name: str) -> float | None:
    match = re.search(rf"{re.escape(name)}\s*=\s*({_NUMBER_RE.pattern})", log)
    return float(match.group(1)) if match else None


def _table_rows(log: str, required: tuple[str, ...]) -> list[list[float]]:
    lines = log.splitlines()
    rows: list[list[float]] = []
    in_table = False
    for line in lines:
        stripped = line.strip()
        if all(token in stripped for token in required):
            in_table = True
            continue
        if not in_table or not stripped:
            continue
        parts = stripped.split()
        try:
            values = [float(part) for part in parts]
        except ValueError:
            # Repeated headers and dashed page separators are part of the same
            # table; any other non-numeric line marks the end of the table.
            if rows and not set(stripped) <= set("-= "):
                break
            continue
        if len(values) >= 4 and float(values[0]).is_integer():
            values = values[-3:]
        if len(values) >= 3:
            rows.append(values[:3])
    return rows


def parse_dc(log: str, params: dict) -> dict:
    """Return DC operating-point values from ngspice output."""
    vb = _extract_named(log, "v(base)")
    ve = _extract_named(log, "v(emit)")
    vc = _extract_named(log, "v(col)")
    if None in (vb, ve, vc):
        rows = _table_rows(log, ("v(base)", "v(emit)", "v(col)"))
        if rows:
            vb, ve, vc = rows[-1]

    if None in (vb, ve, vc):
        return {"values": None, "error": "No DC operating point found in ngspice output"}

    ic_ma = (params["vcc"] - vc) / params["rc"] * 1000.0
    return {
        "values": {
            "vb": round(vb, 4),
            "ve": round(ve, 4),
            "vc": round(vc, 4),
            "vce": round(vc - ve, 4),
            "ic_ma": round(ic_ma, 4),
        },
        "error": None,
    }


def parse_ac(log: str) -> dict:
    """Return frequency / gain-dB / phase-degree points from ngspice output."""
    rows = _table_rows(log, ("frequency", "vdb(out)", "vp(out)"))
    if not rows:
        return {"points": None, "error": "No AC sweep data found in ngspice output"}
    return {"points": rows, "error": None}


def parse_tran(log: str) -> dict:
    """Return time / vin / vout points from ngspice output."""
    rows = _table_rows(log, ("time", "v(src)", "v(out)"))
    if not rows:
        return {"points": None, "error": "No transient data found in ngspice output"}
    return {"points": rows, "error": None}


def _error_result(analysis: str, message: str, model: str | None = None, netlist: str | None = None, log_excerpt: str = "") -> dict:
    return {
        "status": "error",
        "analysis": analysis,
        "engine": "ngspice",
        "model": model,
        "netlist": netlist,
        "values": None,
        "points": None,
        "error": message,
        "log_excerpt": log_excerpt[:200],
    }


def simulate(form, analysis: str) -> dict:
    """Validate, run, and parse one SPICE analysis; never fake a success."""
    if analysis not in ANALYSES:
        return _error_result(analysis, f"Unsupported analysis: {analysis}")

    params, error = validate_ce_inputs(form)
    if error:
        return _error_result(analysis, error)

    netlist = build_netlist(params, analysis)
    run = run_ngspice(netlist)
    if not run["ok"]:
        return _error_result(analysis, run["error"] or "ngspice run failed", params["model"], netlist)

    log = run["log"]
    if not log.strip():
        return _error_result(analysis, "ngspice produced no output", params["model"], netlist)

    if analysis == "dc":
        parsed = parse_dc(log, params)
    elif analysis == "ac":
        parsed = parse_ac(log)
    else:
        parsed = parse_tran(log)

    if parsed["error"]:
        return _error_result(analysis, parsed["error"], params["model"], netlist, log)

    return {
        "status": "success",
        "analysis": analysis,
        "engine": "ngspice",
        "model": params["model"],
        "netlist": netlist,
        "values": parsed.get("values"),
        "points": parsed.get("points"),
        "error": None,
        "log_excerpt": log[:200],
    }
