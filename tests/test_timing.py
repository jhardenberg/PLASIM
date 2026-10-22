"""Atmospheric presets and real LSG ten-day coupling across resolutions."""

import math
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile
import unittest

from test_lsg import floats, lsg_output_records
from test_model import ROOT, build_model, doubles, prepare_run, records, run_model


class CouplingTimingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="plasim-coupling-timing-")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.work = Path(cls.temp.name)
        cls.executables = {}

    def executable(self, latitudes=32, ranks=1):
        key = latitudes, ranks
        if key not in self.executables:
            self.executables[key] = build_model(
                self.work / f"build-{latitudes}-{ranks}", lsg=True,
                latitudes=latitudes, ranks=ranks, fflags="-O2",
            )
        return self.executables[key]

    def prepare(self, name, resolution="T21", days=10, steps=0,
                atmosphere="", ocean=""):
        run = prepare_run(self.work, name, resolution=resolution, days=days, steps=steps)
        for source in (ROOT / "lsg/dat").iterdir():
            shutil.copy2(source, run / source.name)
        path = run / "plasim_namelist"
        path.write_text(path.read_text().replace(
            "&plasim_nl\n", "&plasim_nl\n n_start_year=1, n_days_per_year=360, "
            "ndiagcf=0, " + atmosphere + "\n"))
        (run / "oceanmod_namelist").write_text(
            "&oceanmod_nl\n nlsg=1, nocean=1, nhdiff=0, " + ocean + "\n/\n")
        (run / "input").write_text(
            "&param\n kiterm=8, ntback=100000000, ntout=1, ntsurf=1\n/\n")
        return run

    def check_ocean(self, run, steps):
        diag = (run / "plasim_diag").read_text()
        self.assertRegex(diag, rf"last timestep\s*=\s*{steps}\b")
        ocean = lsg_output_records(run / "lsg_output")
        dates = sorted({key[2] for key in ocean})
        self.assertEqual(len(dates), steps)
        for code in (-2, -5, -52, -53, -18):
            for date in dates:
                values = floats(ocean[code, 1, date])
                self.assertTrue(all(map(math.isfinite, values)), (code, date))
                self.assertGreater(max(map(abs, values)), 0, (code, date))
            if steps > 1 and code in (-2, -5):
                self.assertNotEqual(ocean[code, 1, dates[0]], ocean[code, 1, dates[-1]])
        state = records(run / "plasim_status")
        for field in ("dt", "dq", "ysst", "dicec", "yfldo"):
            values = doubles(state[field])
            self.assertTrue(all(map(math.isfinite, values)), field)
        self.assertGreater(max(map(abs, doubles(state["yfldo"]))), 0)

    def test_defaults_advance_lsg_in_serial_and_mpi(self):
        ranks_list = [1]
        if shutil.which("mpif90") and shutil.which("mpiexec"):
            ranks_list.append(2)
        for ranks in ranks_list:
            for resolution, latitudes, minutes, per_day in (
                    ("T21", 32, 45, 32), ("T31", 48, 30, 48), ("T42", 64, 20, 72)):
                with self.subTest(resolution=resolution, ranks=ranks):
                    days = 20 if ranks == 1 else 10
                    run = self.prepare(f"default-{resolution}-{ranks}", resolution, days)
                    launcher = ["mpiexec", "--bind-to", "none", "-n", str(ranks)] if ranks > 1 else None
                    run_model(self.executable(latitudes, ranks), run, launcher=launcher, timeout=300)
                    diag = (run / "plasim_diag").read_text()
                    self.assertRegex(diag, rf"Timestep\s*:\s*{minutes}\s*\[min\]")
                    self.assertRegex(diag, rf"Timesteps / day\s*:\s*{per_day}\b")
                    self.assertRegex(diag, rf"NAOMOD\s*=\s*{10 * per_day}\b")
                    self.assertRegex(diag, r"DT set by PlaSim:.*864000\.")
                    state = records(run / "plasim_status")
                    for name, expected in (("nlat", latitudes), ("nlon", 2 * latitudes),
                                           ("nstep", (360 + days) * per_day)):
                        self.assertEqual(struct.unpack("=i", state[name])[0], expected, name)
                    self.check_ocean(run, days // 10)

    def test_automatic_matches_explicit_most_presets_at_startup(self):
        for resolution, latitudes, minutes in (("T21", 32, 45), ("T31", 48, 30), ("T42", 64, 20)):
            with self.subTest(resolution=resolution):
                automatic = self.prepare(f"startup-auto-{resolution}", resolution, days=0, steps=1)
                explicit = self.prepare(f"startup-most-{resolution}", resolution, days=0, steps=1,
                                        atmosphere=f"mpstep={minutes},", ocean="naomod=0,")
                for run in (automatic, explicit):
                    run_model(self.executable(latitudes), run)
                self.assertEqual((automatic / "plasim_status").read_bytes(),
                                 (explicit / "plasim_status").read_bytes())

    def test_explicit_atmospheric_timing_sets_default_cadence(self):
        for name, option in (("minutes", "mpstep=30,"), ("steps", "ntspd=48,")):
            with self.subTest(option=option):
                run = self.prepare(f"override-{name}", atmosphere=option)
                run_model(self.executable(), run)
                diag = (run / "plasim_diag").read_text()
                self.assertRegex(diag, r"NAOMOD\s*=\s*480\b")
                self.assertRegex(diag, r"DT set by PlaSim:.*864000\.")
                self.check_ocean(run, 1)

    def test_new_default_restart_matches_continuous(self):
        for resolution, latitudes in (("T31", 48), ("T42", 64)):
            with self.subTest(resolution=resolution):
                continuous = self.work / f"default-{resolution}-1"
                if not (continuous / "plasim_status").exists():
                    self.prepare(f"default-{resolution}-1", resolution, days=20)
                    run_model(self.executable(latitudes), continuous, timeout=300)
                split = self.prepare(f"split-{resolution}", resolution, days=10)
                run_model(self.executable(latitudes), split, timeout=300)
                shutil.copy2(split / "plasim_status", split / "plasim_restart")
                run_model(self.executable(latitudes), split, timeout=300)
                for filename in ("plasim_status", "kleiin1"):
                    self.assertEqual((split / filename).read_bytes(),
                                     (continuous / filename).read_bytes(), filename)
                full_ocean = lsg_output_records(continuous / "lsg_output")
                last_date = max(key[2] for key in full_ocean)
                self.assertEqual(lsg_output_records(split / "lsg_output"),
                                 {k: v for k, v in full_ocean.items() if k[2] == last_date})

    def test_invalid_cadences_fail_before_lsg_initialization(self):
        ranks_list = [1, 2] if shutil.which("mpif90") and shutil.which("mpiexec") else [1]
        for ranks in ranks_list:
            for name, option in (("negative", "naomod=-1,"), ("subday", "naomod=16,"),
                                 ("fractional", "naomod=321,"), ("clock", "ntspd=16,")):
                with self.subTest(ranks=ranks, option=option):
                    run = self.prepare(f"invalid-{name}-{ranks}", days=0, steps=1, ocean=option)
                    launcher = ["mpiexec", "--bind-to", "none", "-n", str(ranks)] if ranks > 1 else []
                    result = subprocess.run([*launcher, str(self.executable(ranks=ranks))], cwd=run,
                                            text=True, capture_output=True, timeout=30)
                    self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                    diag = (run / "plasim_diag").read_text()
                    self.assertIn("ERROR: LSG", diag)
                    self.assertNotIn("DT set by PlaSim", diag)
