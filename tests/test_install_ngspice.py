import io
import os
import stat
import tarfile
import tempfile
import unittest
from pathlib import Path

from scripts import install_ngspice


class MicromambaArchiveTests(unittest.TestCase):
    def test_extract_writes_executable_from_archive(self):
        payload = b"#!/bin/sh\necho fake micromamba\n"
        archive = io.BytesIO()
        with tarfile.open(fileobj=archive, mode="w:bz2") as tar:
            member = tarfile.TarInfo("bin/micromamba")
            member.size = len(payload)
            member.mode = 0o644
            tar.addfile(member, io.BytesIO(payload))

        with tempfile.TemporaryDirectory() as directory:
            tools_dir = Path(directory)
            target = install_ngspice.extract_micromamba(archive.getvalue(), tools_dir)

            self.assertEqual(target, tools_dir / "bin" / "micromamba")
            self.assertEqual(target.read_bytes(), payload)
            if os.name == "posix":
                self.assertTrue(target.stat().st_mode & stat.S_IXUSR)


if __name__ == "__main__":
    unittest.main()
