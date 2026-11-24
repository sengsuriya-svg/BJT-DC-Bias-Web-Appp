"""Install ngspice without root privileges for the Render native build.

Render's free native runtime does not allow apt-get / OS-level package installs.
This script downloads a standalone micromamba binary with the Python standard
library, extracts it, and creates a local conda environment containing ngspice.
The app discovers ``.ngspice/bin/ngspice`` at runtime, so no Shell access is
needed after the build.
"""

from __future__ import annotations

import io
import os
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

MICROMAMBA_URL = "https://micro.mamba.pm/api/micromamba/linux-64/latest"
PACKAGE_SPEC = "ngspice=41"
PROJECT_DIR = Path(__file__).resolve().parent.parent
PREFIX = PROJECT_DIR / ".ngspice"
TOOLS_DIR = PROJECT_DIR / ".tools"


def extract_micromamba(archive: bytes, tools_dir: Path) -> Path:
    """Write the executable from a micromamba tar.bz2 archive into tools_dir."""
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:bz2") as tar:
        source = tar.extractfile("bin/micromamba")
        if source is None:
            raise RuntimeError("micromamba archive has no bin/micromamba member")
        target = tools_dir / "bin" / "micromamba"
        target.parent.mkdir(parents=True, exist_ok=True)
        with source, target.open("wb") as destination:
            shutil.copyfileobj(source, destination)
        target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return target


def main() -> None:
    if sys.platform != "linux":
        raise SystemExit("install_ngspice.py is intended for the Linux Render build environment")

    binary = PREFIX / "bin" / "ngspice"
    if binary.is_file():
        print(f"ngspice already installed at {binary}")
        return

    print(f"Downloading micromamba from {MICROMAMBA_URL}")
    with urllib.request.urlopen(MICROMAMBA_URL, timeout=120) as response:
        archive = response.read()
    micromamba = extract_micromamba(archive, TOOLS_DIR)

    print(f"Creating local environment with {PACKAGE_SPEC}")
    with tempfile.TemporaryDirectory(prefix="mamba-root-") as root_prefix:
        environment = os.environ.copy()
        environment["MAMBA_ROOT_PREFIX"] = root_prefix
        subprocess.run(
            [
                str(micromamba),
                "create",
                "--yes",
                "--prefix",
                str(PREFIX),
                "--channel",
                "conda-forge",
                "--override-channels",
                PACKAGE_SPEC,
            ],
            check=True,
            env=environment,
        )

    if not binary.is_file():
        raise SystemExit(f"micromamba did not create {binary}")
    subprocess.run([str(binary), "--version"], check=True)


if __name__ == "__main__":
    main()
