"""Tests for repository helper scripts."""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def run_command(args: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args, cwd=cwd, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=False,
    )


class Nc2SraTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if shutil.which("cdo") is None:
            raise unittest.SkipTest("cdo is required for nc2sra tests")
        cls.temp = tempfile.TemporaryDirectory(prefix="plasim-script-tests-")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.work = Path(cls.temp.name)

    def test_grid_selection_and_dimensions(self) -> None:
        """Verify nc2sra detects T21, T31, and T42 grids and preserves their dimensions."""
        cases = [
            ("F16", 64, 32),
            ("F24", 96, 48),
            ("F32", 128, 64),
        ]
        nc2sra = SCRIPTS / "nc2sra"

        for cdo_grid, expected_nx, expected_ny in cases:
            with self.subTest(grid=cdo_grid):
                nc_file = self.work / f"test_{cdo_grid}.nc"
                sra_file = self.work / f"test_{cdo_grid}.sra"

                # Create synthetic input with CDO
                res = run_command([
                    "cdo", "-s", "-f", "nc",
                    "-settaxis,2000-01-01,12:30:00,1day",
                    f"-const,42,{cdo_grid}", str(nc_file),
                ])
                self.assertEqual(res.returncode, 0, f"cdo failed: {res.stderr}")

                # Convert to sra
                conv = run_command([
                    "bash", str(nc2sra),
                    "-d", "20000101", "-t", "1230",
                    str(nc_file), str(sra_file), "172",
                ])
                self.assertEqual(conv.returncode, 0, f"nc2sra failed: {conv.stderr}")

                # Check sra contents
                with sra_file.open("r", encoding="ascii") as f:
                    lines = f.readlines()
                self.assertGreater(len(lines), 1)

                header = lines[0].split()
                self.assertEqual(header[0], "172")
                self.assertEqual(header[2], "20000101")
                self.assertEqual(header[3], "1230")
                self.assertEqual(int(header[4]), expected_nx)
                self.assertEqual(int(header[5]), expected_ny)

                data_values = [float(val) for line in lines[1:] for val in line.split()]
                expected_total = expected_nx * expected_ny
                self.assertEqual(len(data_values), expected_total)
                self.assertTrue(all(val == 42.0 for val in data_values))

    def test_roundtrip_preserves_values_and_orientation(self) -> None:
        """Verify nc2sra preserves array values and orientation from sra2nc output."""
        sra2nc = SCRIPTS / "sra2nc"
        nc2sra = SCRIPTS / "nc2sra"
        t42_sra = ROOT / "plasim" / "dat" / "T42" / "N064_surf_0172.sra"
        if not t42_sra.exists():
            raise unittest.SkipTest("T42 surface fixture not found")

        nc_file = self.work / "roundtrip_t42.nc"
        sra_file = self.work / "roundtrip_t42.sra"

        res1 = run_command(["bash", str(sra2nc), str(t42_sra), str(nc_file)])
        self.assertEqual(res1.returncode, 0, f"sra2nc failed: {res1.stderr}")

        res2 = run_command([
            "bash", str(nc2sra),
            "-d", "20090101", "-t", "0000",
            str(nc_file), str(sra_file), "172",
        ])
        self.assertEqual(res2.returncode, 0, f"nc2sra failed: {res2.stderr}")

        with t42_sra.open("r", encoding="ascii") as f1, sra_file.open("r", encoding="ascii") as f2:
            orig_vals = [float(x) for line in f1.readlines()[1:] for x in line.split()]
            conv_vals = [float(x) for line in f2.readlines()[1:] for x in line.split()]

        self.assertEqual(len(conv_vals), 8192)
        self.assertEqual(len(orig_vals), len(conv_vals))
        max_diff = max(abs(a - b) for a, b in zip(orig_vals, conv_vals))
        self.assertLess(max_diff, 1e-5, f"Values differed by {max_diff}")

    def test_unsupported_grid_rejected(self) -> None:
        """Verify nc2sra rejects an unsupported grid size with exit code 1."""
        nc2sra = SCRIPTS / "nc2sra"
        nc_file = self.work / "unsupported_grid.nc"
        sra_file = self.work / "unsupported_grid.sra"

        # Create F48 grid (unsupported)
        res = run_command([
            "cdo", "-s", "-f", "nc",
            "-settaxis,2000-01-01,12:30:00,1day",
            "-const,1,F48", str(nc_file),
        ])
        self.assertEqual(res.returncode, 0, f"cdo failed: {res.stderr}")

        conv = run_command([
            "bash", str(nc2sra),
            "-d", "20000101", "-t", "1230",
            str(nc_file), str(sra_file), "172",
        ])
        self.assertNotEqual(conv.returncode, 0)
        self.assertIn("Unknown grid size", conv.stdout + conv.stderr)


if __name__ == "__main__":
    unittest.main()
