"""Headless PlaSim regression tests using the existing Makefile."""

from __future__ import annotations

import gzip
import math
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "plasim" / "src"
BOUNDARY_DATA = ROOT / "plasim" / "dat" / "T21"
LEGACY_RESTART = ROOT / "tests" / "fixtures" / "earth_t21_l10_day1_360.restart.gz"
NAMELISTS = (
    "fluxmod", "icemod", "landmod", "miscmod", "oceanmod", "planet",
    "radmod", "rainmod", "seamod", "surfmod", "vegmod",
)


def command(args: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> None:
    result = subprocess.run(
        args, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, timeout=120, check=False,
    )
    if result.returncode:
        raise AssertionError(
            f"{' '.join(args)} exited {result.returncode}\n"
            f"{result.stdout[-8000:]}"
        )


def records(path: Path) -> dict[str, bytes]:
    """Read the named records in gfortran's sequential restart file."""
    result: dict[str, bytes] = {}
    with path.open("rb") as stream:
        while True:
            name = _record(stream)
            if name is None:
                break
            result[name.decode("ascii").strip()] = _record(stream)
    return result


def _record(stream) -> bytes | None:
    marker = stream.read(4)
    if not marker:
        return None
    if len(marker) != 4:
        raise AssertionError("Truncated Fortran record marker")
    size = struct.unpack("=i", marker)[0]
    if size < 0:
        raise AssertionError("Unexpected Fortran subrecord")
    data = stream.read(size)
    closing = stream.read(4)
    if len(data) != size or len(closing) != 4 or struct.unpack("=i", closing)[0] != size:
        raise AssertionError("Truncated Fortran record")
    return data


def doubles(data: bytes) -> tuple[float, ...]:
    if len(data) % 8:
        raise AssertionError("Expected double precision values")
    return struct.unpack(f"={len(data) // 8}d", data)


def build_model(build: Path, *, lsg: bool = False) -> Path:
    """Build the serial T21/L10 model with real or stubbed LSG coupling."""
    for program in ("gfortran", "make", "cc"):
        if shutil.which(program) is None:
            raise unittest.SkipTest(f"{program} is required")
    build.mkdir()
    for source in SOURCE.iterdir():
        if source.is_file():
            shutil.copy2(source, build / source.name)
    if lsg:
        shutil.copy2(ROOT / "lsg" / "src" / "lsgmod.f90", build / "lsgmod.f90")
    shutil.copy2(build / "resmod_def.f90", build / "resmod.f90")
    shutil.copy2(build / "make_plasim", build / "makefile")

    env = os.environ.copy()
    env.update({
        "MOST_CC": "cc", "MOST_CC_OPTS": "-O0",
        "MOST_F90": "gfortran", "MOST_F90_OPTS": "-O0",
        "MOST_PREC": "-fdefault-real-8", "MPIMOD": "mpimod_stub",
        "GUIMOD": "guimod_stub", "PUMAX": "pumax_stub",
        "GUILIB": "", "OCEAN": "lsgmod" if lsg else "lsgmod_stub",
        "OCEANCOUP": "cpl" if lsg else "cpl_stub",
    })
    command(["make", "-e", "-j1", "plasim.x"], cwd=build, env=env)
    return build / "plasim.x"


def prepare_run(work: Path, name: str, *, days: int) -> Path:
    run = work / name
    run.mkdir()
    for source in BOUNDARY_DATA.iterdir():
        shutil.copy2(source, run / source.name)
    for module in NAMELISTS:
        (run / f"{module}_namelist").write_text(
            f"&{module}_nl\n/\n", encoding="ascii"
        )
    (run / "plasim_namelist").write_text(
        "&plasim_nl\n"
        f" n_run_years=0, n_run_months=0, n_run_days={days}, "
        "kick=0, ngui=0, seed=1\n/\n", encoding="ascii",
    )
    return run


def run_model(executable: Path, run: Path) -> None:
    command([str(executable)], cwd=run)
    if (run / "Abort_Message").exists():
        raise AssertionError((run / "Abort_Message").read_text())
    for output in ("plasim_diag", "plasim_output", "plasim_status"):
        if not (run / output).is_file() or (run / output).stat().st_size == 0:
            raise AssertionError(f"Missing or empty {output}")


class PlaSimTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = tempfile.TemporaryDirectory(prefix="plasim-tests-")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.work = Path(cls.temp.name)
        cls.executable = build_model(cls.work / "build")

        cls.continuous = cls.prepare_run("continuous", days=2)
        cls.run_model(cls.continuous)
        cls.legacy_status = cls.work / "legacy_status"
        cls.legacy_status.write_bytes(gzip.decompress(LEGACY_RESTART.read_bytes()))

    @classmethod
    def prepare_run(cls, name: str, *, days: int) -> Path:
        return prepare_run(cls.work, name, days=days)

    @classmethod
    def run_model(cls, run: Path) -> None:
        run_model(cls.executable, run)

    def test_t21_two_day_regression(self) -> None:
        state = records(self.continuous / "plasim_status")
        self.assertEqual(struct.unpack("=i", state["nlat"])[0], 32)
        self.assertEqual(struct.unpack("=i", state["nlon"])[0], 64)
        self.assertEqual(struct.unpack("=i", state["nlev"])[0], 10)
        self.assertEqual(struct.unpack("=i", state["nstep"])[0], 11584)

        # Broad numerical baselines: catch changed physics and broken data
        # loading without requiring bitwise agreement across compilers.
        for field, expected_mean, tolerance in (
            ("dt", 277.6539, 0.3),
            ("dq", 0.00905793, 0.0001),
            ("dls", 0.32861328125, 0.0),
        ):
            values = doubles(state[field])
            self.assertTrue(all(map(math.isfinite, values)), field)
            self.assertAlmostEqual(math.fsum(values) / len(values), expected_mean,
                                   delta=tolerance, msg=field)
        self.assertIn("2   days", (self.continuous / "plasim_diag").read_text())

    def test_restart_matches_continuous_run(self) -> None:
        split = self.prepare_run("split", days=1)
        self.run_model(split)
        (split / "plasim_status").replace(split / "plasim_restart")
        self.run_model(split)
        self.assertEqual(
            (split / "plasim_status").read_bytes(),
            (self.continuous / "plasim_status").read_bytes(),
        )

    def test_spectral_restart_matches_continuous_run(self) -> None:
        continuous = self.prepare_run("spectral-continuous", days=2)
        (continuous / "radmod_namelist").write_text(
            "&radmod_nl\n nstartemp=1\n/\n", encoding="ascii"
        )
        self.run_model(continuous)

        split = self.prepare_run("spectral-split", days=1)
        (split / "radmod_namelist").write_text(
            "&radmod_nl\n nstartemp=1\n/\n", encoding="ascii"
        )
        self.run_model(split)
        (split / "plasim_status").replace(split / "plasim_restart")
        self.run_model(split)
        self.assertEqual(
            (split / "plasim_status").read_bytes(),
            (continuous / "plasim_status").read_bytes(),
        )

    def test_classic_earth_state_matches_master(self) -> None:
        """Compare every value in key Earth fields with the master fixture."""
        run = self.prepare_run("classic-earth", days=1)
        self.run_model(run)
        actual = records(run / "plasim_status")
        expected = records(self.legacy_status)
        self.assertEqual(struct.unpack("=i", actual["nstep"])[0], 11552)
        for field in ("dt", "dq", "dalb", "dls", "sz", "sd", "st", "sq", "sp"):
            with self.subTest(field=field):
                reference = doubles(expected[field])
                values = doubles(actual[field])
                self.assertEqual(len(values), len(reference))
                self.assertTrue(all(map(math.isfinite, values)))
                differences = [abs(a - b) for a, b in zip(values, reference)]
                limits = [1e-6 + 1e-6 * abs(b) for b in reference]
                worst = max(range(len(values)), key=lambda i: differences[i] / limits[i])
                self.assertLessEqual(
                    differences[worst], limits[worst],
                    f"{field}[{worst}] differs from master: "
                    f"{values[worst]} vs {reference[worst]}",
                )

    def test_master_restart_can_continue(self) -> None:
        run = self.prepare_run("master-restart", days=1)
        (run / "plasim_restart").write_bytes(self.legacy_status.read_bytes())
        self.run_model(run)
        state = records(run / "plasim_status")
        self.assertEqual(struct.unpack("=i", state["nstep"])[0], 11584)
        self.assertTrue(all(map(math.isfinite, doubles(state["dt"]))))
        reference = records(self.continuous / "plasim_status")
        self.assertEqual(state["dls"], reference["dls"])
        for field in ("dt", "dq", "dalb"):
            with self.subTest(field=field):
                values = doubles(state[field])
                expected = doubles(reference[field])
                self.assertEqual(len(values), len(expected))
                self.assertTrue(all(
                    abs(a - b) <= 1e-6 + 1e-6 * abs(b)
                    for a, b in zip(values, expected)
                ))

    def test_albsmin_namelist_option(self) -> None:
        run = self.prepare_run("namelist-snow-albedo", days=0)
        (run / "plasim_namelist").write_text(
            "&plasim_nl\n n_run_steps=1, kick=0, ngui=0, seed=1\n/\n",
            encoding="ascii",
        )
        namelist = run / "landmod_namelist"
        namelist.write_text("&landmod_nl\n albsmin=0.5\n/\n", encoding="ascii")
        self.run_model(run)


class CalendarTests(unittest.TestCase):
    def test_calendar_boundaries(self) -> None:
        if shutil.which("gfortran") is None:
            raise unittest.SkipTest("gfortran is required")
        with tempfile.TemporaryDirectory(prefix="plasim-calendar-") as directory:
            work = Path(directory)
            executable = work / "calendar_test"
            command([
                "gfortran", "-O0", "-o", str(executable),
                str(SOURCE / "calmod.f90"),
                str(ROOT / "tests" / "calendar_test.f90"),
            ], cwd=work)
            command([str(executable)], cwd=work)


if __name__ == "__main__":
    unittest.main()
