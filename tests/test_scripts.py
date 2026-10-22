"""Tests for repository helper scripts."""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import sys
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

    def test_sra2nc_timestamp_handling(self) -> None:
        """Verify sra2nc preserves non-midnight HHMM timestamps and maps missing time to midnight."""
        sra2nc = SCRIPTS / "sra2nc"
        cases = [
            ("1230", "2000-01-01T12:30:00"),
            ("600", "2000-01-01T06:00:00"),
            ("0", "2000-01-01T00:00:00"),
            ("0000", "2000-01-01T00:00:00"),
            ("-1", "2000-01-01T00:00:00"),
        ]
        for time_header, expected_timestamp in cases:
            with self.subTest(time_header=time_header):
                sra_file = self.work / f"test_time_{time_header}.sra"
                nc_file = self.work / f"test_time_{time_header}.nc"

                with sra_file.open("w", encoding="ascii") as f:
                    f.write(f"       172         0  20000101      {time_header:>4}        64        32         0         0\n")
                    for _ in range(256):
                        f.write("  42.0  42.0  42.0  42.0  42.0  42.0  42.0  42.0\n")

                res = run_command(["bash", str(sra2nc), str(sra_file), str(nc_file)])
                self.assertEqual(res.returncode, 0, f"sra2nc failed: {res.stderr}")

                res_ts = run_command(["cdo", "-s", "showtimestamp", str(nc_file)])
                self.assertEqual(res_ts.returncode, 0, f"cdo showtimestamp failed: {res_ts.stderr}")
                self.assertEqual(res_ts.stdout.strip(), expected_timestamp)

    def test_roundtrip_non_midnight_timestamp(self) -> None:
        """Verify sra2nc and nc2sra roundtrip preserves non-midnight timestamps and values."""
        sra2nc = SCRIPTS / "sra2nc"
        nc2sra = SCRIPTS / "nc2sra"

        orig_sra = self.work / "orig_noon.sra"
        nc_file = self.work / "noon.nc"
        roundtrip_sra = self.work / "roundtrip_noon.sra"

        with orig_sra.open("w", encoding="ascii") as f:
            f.write("       172         0  20000101      1230        64        32         0         0\n")
            for _ in range(256):
                f.write("  42.0  42.0  42.0  42.0  42.0  42.0  42.0  42.0\n")

        res1 = run_command(["bash", str(sra2nc), str(orig_sra), str(nc_file)])
        self.assertEqual(res1.returncode, 0, f"sra2nc failed: {res1.stderr}")

        res_ts = run_command(["cdo", "-s", "showtimestamp", str(nc_file)])
        self.assertEqual(res_ts.returncode, 0, f"cdo showtimestamp failed: {res_ts.stderr}")
        self.assertEqual(res_ts.stdout.strip(), "2000-01-01T12:30:00")

        res2 = run_command([
            "bash", str(nc2sra),
            "-d", "20000101", "-t", "1230",
            str(nc_file), str(roundtrip_sra), "172",
        ])
        self.assertEqual(res2.returncode, 0, f"nc2sra failed: {res2.stderr}")

        with orig_sra.open("r", encoding="ascii") as f1, roundtrip_sra.open("r", encoding="ascii") as f2:
            lines1 = f1.readlines()
            lines2 = f2.readlines()

        header1 = lines1[0].split()
        header2 = lines2[0].split()
        self.assertEqual(header2[0], header1[0])
        self.assertEqual(header2[2], header1[2])
        self.assertEqual(header2[3], header1[3])
        self.assertEqual(header2[4], header1[4])
        self.assertEqual(header2[5], header1[5])

        vals1 = [float(x) for line in lines1[1:] for x in line.split()]
        vals2 = [float(x) for line in lines2[1:] for x in line.split()]
        self.assertEqual(len(vals1), len(vals2))
        max_diff = max(abs(a - b) for a, b in zip(vals1, vals2))
        self.assertLess(max_diff, 1e-5)


class MostRunScriptTests(unittest.TestCase):
    """Regression tests for MoSt generated run script (issue #52)."""

    def test_most_c_write_run_script_directives(self) -> None:
        """Verify most.c WriteRunScript generates set -e and proper if guards for optional LSG products."""
        most_c = (ROOT / "most.c").read_text()
        self.assertIn('fputs("set -e\\n",fp);', most_c)
        self.assertIn('fputs("   if [ -e Abort_Message ]; then exit 1; fi\\n",fp);', most_c)
        self.assertIn('if [ -e mat77 ]; then cp mat77 restart/mat77; fi', most_c)
        self.assertIn('if [ -e kleiswi ]; then cp kleiswi restart/kleiswi; fi', most_c)
        self.assertIn('if [ -e kleiin1 ]; then cp kleiin1 restart/$LSGRESTNAME; fi', most_c)
        self.assertNotIn('[ -e kleiin1 ] && cp kleiin1 restart/$LSGRESTNAME', most_c)

    def test_run_script_execution_behavior(self) -> None:
        """Verify script exit status for non-LSG success, model failure, abort, conversion, and LSG archiving."""
        with tempfile.TemporaryDirectory(prefix="plasim-runscript-test-") as tmpdir:
            work = Path(tmpdir)
            script_path = work / "test_run"
            script_content = (
                "#!/bin/bash\n"
                "set -e\n"
                "EXP=TEST\n"
                "YEAR1=1\n"
                "YEAR2=1\n"
                'average="-m"\n'
                f"srv2nc={work / 'mock_srv2nc'}\n"
                "[ $# == 1 ] && cd $1\n"
                "rm -f plasim_restart\n"
                "rm -f Abort_Message\n"
                "mkdir -p output\n"
                "mkdir -p restart\n"
                "for ((YEAR=$YEAR1; YEAR<=$YEAR2; YEAR++)); do\n"
                "   DATANAME=`printf '%s_PLA.%04d.nc' $EXP $YEAR`\n"
                "   OCENAME=`printf '%s_OCE.%04d.nc' $EXP $YEAR`\n"
                "   ICENAME=`printf '%s_ICE.%04d.nc' $EXP $YEAR`\n"
                "   LSGNAME=`printf '%s_LSG.%04d.nc' $EXP $YEAR`\n"
                "   DIAGNAME=`printf '%s_DIAG.%04d.txt' $EXP $YEAR`\n"
                "   RESTNAME=`printf '%s_REST.%04d' $EXP $YEAR`\n"
                "   LSGRESTNAME=`printf '%s_LSGREST.%04d' $EXP $YEAR`\n"
                "   ./mock_model\n"
                "   if [ -e Abort_Message ]; then exit 1; fi\n"
                "   if [ -e plasim_diag ]; then mv plasim_diag output/$DIAGNAME; fi\n"
                "   if [ -e plasim_output ]; then $srv2nc $average plasim_output output/$DATANAME; fi\n"
                "   if [ -e ocean_output ]; then $srv2nc $average ocean_output output/$OCENAME; fi\n"
                "   if [ -e ice_output ]; then $srv2nc $average ice_output output/$ICENAME; fi\n"
                "   if [ -e lsg_output ]; then $srv2nc lsg_output output/$LSGNAME; fi\n"
                "   if [ -e plasim_status ]; then\n"
                "      cp plasim_status plasim_restart\n"
                "      mv plasim_status restart/$RESTNAME\n"
                "   fi\n"
                "   if [ -e mat77 ]; then cp mat77 restart/mat77; fi\n"
                "   if [ -e kleiswi ]; then cp kleiswi restart/kleiswi; fi\n"
                "   if [ -e kleiin1 ]; then cp kleiin1 restart/$LSGRESTNAME; fi\n"
                "done\n"
            )
            script_path.write_text(script_content)
            script_path.chmod(0o755)

            mock_model = work / "mock_model"
            mock_srv2nc = work / "mock_srv2nc"

            # 1. Non-LSG run succeeds with exit 0 (issue #52 primary defect)
            mock_srv2nc.write_text('#!/bin/bash\ntouch "${@: -1}"\n')
            mock_srv2nc.chmod(0o755)
            mock_model.write_text(
                "#!/bin/bash\n"
                "touch plasim_diag plasim_output ocean_output ice_output plasim_status\n"
            )
            mock_model.chmod(0o755)

            res = run_command([str(script_path), str(work)], cwd=work)
            self.assertEqual(res.returncode, 0, f"Script failed unexpectedly: {res.stderr}")
            self.assertTrue((work / "output" / "TEST_PLA.0001.nc").is_file())
            self.assertTrue((work / "output" / "TEST_OCE.0001.nc").is_file())
            self.assertTrue((work / "output" / "TEST_ICE.0001.nc").is_file())
            self.assertTrue((work / "output" / "TEST_DIAG.0001.txt").is_file())
            self.assertTrue((work / "restart" / "TEST_REST.0001").is_file())
            self.assertTrue((work / "plasim_restart").is_file())

            # 2. Model execution failure returns non-zero
            mock_model.write_text("#!/bin/bash\nexit 42\n")
            res = run_command([str(script_path), str(work)], cwd=work)
            self.assertEqual(res.returncode, 42)

            # 3. Abort_Message causes exit 1
            mock_model.write_text("#!/bin/bash\ntouch Abort_Message\n")
            res = run_command([str(script_path), str(work)], cwd=work)
            self.assertEqual(res.returncode, 1)

            # 4. Conversion failure returns non-zero
            mock_model.write_text(
                "#!/bin/bash\n"
                "touch plasim_diag plasim_output plasim_status mat77 kleiswi kleiin1\n"
            )
            mock_srv2nc.write_text("#!/bin/bash\nexit 7\n")
            res = run_command([str(script_path), str(work)], cwd=work)
            self.assertEqual(res.returncode, 7)

            # 5. Coupled LSG run archives ocean matrices and restarts with exit 0
            mock_srv2nc.write_text('#!/bin/bash\ntouch "${@: -1}"\n')
            res = run_command([str(script_path), str(work)], cwd=work)
            self.assertEqual(res.returncode, 0, f"LSG run failed: {res.stderr}")
            self.assertTrue((work / "restart" / "mat77").is_file())
            self.assertTrue((work / "restart" / "kleiswi").is_file())
            self.assertTrue((work / "restart" / "TEST_LSGREST.0001").is_file())


class DeriveLsgSraTests(unittest.TestCase):
    """Tests for scripts/derive_lsg_sra.py across model resolutions."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = tempfile.TemporaryDirectory(prefix="plasim-derive-sra-")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.work = Path(cls.temp.name)

    def test_derive_sra_resolutions_and_diagnostics(self) -> None:
        """Verify derive_lsg_sra.py adapts T21, T31, and T42 masks to achieve kmiss_a=0 and kmiss_v=0."""
        script = SCRIPTS / "derive_lsg_sra.py"
        topogr = ROOT / "lsg" / "dat" / "topogr"

        cases = [
            ("T21", 64, 32, ROOT / "plasim" / "dat" / "T21" / "N032_surf_0172.sra"),
            ("T31", 96, 48, ROOT / "plasim" / "dat" / "T31" / "N048_surf_0172.sra"),
            ("T42", 128, 64, ROOT / "plasim" / "dat" / "T42" / "N064_surf_0172.sra"),
        ]

        for res, nxa, nya, input_sra in cases:
            with self.subTest(resolution=res):
                out_sra = self.work / f"N{nya:03d}_surf_0172.sra"
                proc = run_command([
                    sys.executable, str(script),
                    "-i", str(input_sra),
                    "-t", str(topogr),
                    "-o", str(out_sra),
                    "-s", "B",
                ])
                self.assertEqual(proc.returncode, 0, f"derive_lsg_sra failed for {res}: {proc.stderr}")
                self.assertIn("Missing atm ocean points (kmiss_a): 0", proc.stdout)
                self.assertIn("Missing ocean vectors (kmiss_v):    0", proc.stdout)
                self.assertTrue(out_sra.is_file())

                header = [int(x) for x in out_sra.read_text(encoding="ascii").splitlines()[0].split()]
                self.assertEqual(header[0], 172)
                self.assertEqual(header[4], nxa)
                self.assertEqual(header[5], nya)


if __name__ == "__main__":
    unittest.main()
