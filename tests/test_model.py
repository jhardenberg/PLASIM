"""Headless PlaSim regression tests using the existing Makefile."""

from __future__ import annotations

import gzip
import math
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "plasim" / "src"
BOUNDARY_DATA = ROOT / "plasim" / "dat" / "T21"
LEGACY_RESTART = ROOT / "tests" / "fixtures" / "earth_t21_l10_day1_360.restart.gz"
DEFAULT_RESTART = ROOT / "tests" / "fixtures" / "earth_t21_l10_day1_2000_fixed.restart.gz"
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


def build_model(build: Path, *, lsg: bool = False, ranks: int = 1) -> Path:
    """Build T21/L10 with serial or MPI communication and optional real LSG."""
    compiler = "mpif90" if ranks > 1 else "gfortran"
    for program in (compiler, "make", "cc"):
        if shutil.which(program) is None:
            raise unittest.SkipTest(f"{program} is required")
    build.mkdir()
    for source in SOURCE.iterdir():
        if source.is_file():
            shutil.copy2(source, build / source.name)
    if lsg:
        shutil.copy2(ROOT / "lsg" / "src" / "lsgmod.f90", build / "lsgmod.f90")
    (build / "resmod.f90").write_text(
        (build / "resmod_def.f90").read_text().replace(
            "NPRO_ATM = 1", f"NPRO_ATM = {ranks}"
        ), encoding="ascii",
    )
    shutil.copy2(build / "make_plasim", build / "makefile")

    env = os.environ.copy()
    env.update({
        "MOST_CC": "cc", "MOST_CC_OPTS": "-O0",
        "MOST_F90": compiler, "MOST_F90_OPTS": "-O0",
        "MOST_PREC": "-fdefault-real-8",
        "MPIMOD": "mpimod" if ranks > 1 else "mpimod_stub",
        "GUIMOD": "guimod_stub", "PUMAX": "pumax_stub",
        "GUILIB": "", "OCEAN": "lsgmod" if lsg else "lsgmod_stub",
        "OCEANCOUP": "cpl" if lsg else "cpl_stub",
    })
    command(["make", "-e", "-j1", "plasim.x"], cwd=build, env=env)
    return build / "plasim.x"


def prepare_run(work: Path, name: str, *, days: int, steps: int = 0) -> Path:
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
        f" n_run_years=0, n_run_months=0, n_run_days={days}, n_run_steps={steps}, "
        "kick=0, ngui=0, seed=1\n/\n", encoding="ascii",
    )
    return run


def run_model(executable: Path, run: Path, *, launcher: list[str] | None = None) -> None:
    command([*(launcher or []), str(executable)], cwd=run)
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
        cls.default_status = cls.work / "default_status"
        cls.default_status.write_bytes(gzip.decompress(DEFAULT_RESTART.read_bytes()))

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
        self.assertEqual(struct.unpack("=i", state["nstep"])[0], 23040064)

        # Broad numerical baselines: catch changed physics and broken data
        # loading without requiring bitwise agreement across compilers.
        for field, expected_mean, tolerance in (
            ("dt", 277.6631607, 0.3),
            ("dq", 0.00906076004, 0.0001),
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

    def check_cloud_diagnostics(self, *, spectral: bool) -> None:
        name = "spectral" if spectral else "classic"
        reference = self.continuous
        if spectral:
            reference = self.prepare_run(f"{name}-cloud-off", days=2)
            (reference / "radmod_namelist").write_text(
                "&radmod_nl\n nstartemp=1\n/\n", encoding="ascii"
            )
            self.run_model(reference)

        diagnostic = self.prepare_run(f"{name}-cloud-on", days=2)
        shutil.copy2(reference / "radmod_namelist", diagnostic)
        namelist = diagnostic / "plasim_namelist"
        namelist.write_text(
            namelist.read_text(encoding="ascii").replace(
                "&plasim_nl\n", "&plasim_nl\n ndiagcf=1,\n"
            ), encoding="ascii",
        )
        self.run_model(diagnostic)

        # Cloud diagnostic fields are output separately, not saved in restart.
        # Every saved state record should therefore be unchanged in this build.
        expected = records(reference / "plasim_status")
        actual = records(diagnostic / "plasim_status")
        self.assertEqual(actual.keys(), expected.keys())
        for field in expected:
            with self.subTest(radiation=name, field=field):
                self.assertTrue(actual[field] == expected[field],
                                f"{field} changed when cloud diagnostics were enabled")

        # Catch disabling the diagnostic calculation or replacing it with zeros.
        nonzero_codes = set()
        with (diagnostic / "plasim_output").open("rb") as stream:
            while (header := _record(stream)) is not None:
                self.assertEqual(len(header), 32)
                code, _, _, _, nlon, nlat, _, _ = struct.unpack("=8i", header)
                data = _record(stream)
                self.assertIsNotNone(data)
                if 101 <= code <= 107:
                    self.assertEqual((nlon, nlat), (64, 32))
                    self.assertEqual(len(data), nlon * nlat * 4)
                    values = struct.unpack(f"={nlon * nlat}f", data)
                    self.assertTrue(all(map(math.isfinite, values)), code)
                    if any(value != 0.0 for value in values):
                        nonzero_codes.add(code)
        self.assertEqual(nonzero_codes, set(range(101, 108)))

    def test_classic_cloud_diagnostics_preserve_state(self) -> None:
        self.check_cloud_diagnostics(spectral=False)

    def test_spectral_cloud_diagnostics_preserve_state(self) -> None:
        self.check_cloud_diagnostics(spectral=True)

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

    def test_dynamic_orbit_uses_restart_year(self) -> None:
        """Cross a year boundary and compare restarted and fresh orbits."""
        for calendar, december_days in ((360, 30), (365, 31)):
            with self.subTest(calendar=calendar):
                def prepare(name, *, year=2000, month=12, days):
                    run = self.prepare_run(f"orbit-{calendar}-{name}", days=days)
                    (run / "plasim_namelist").write_text(
                        "&plasim_nl\n"
                        f" n_start_year={year}, n_start_month={month}, "
                        f"n_days_per_year={calendar}, n_run_years=0, "
                        f"n_run_months=0, n_run_days={days}, "
                        "kick=0, ngui=0, seed=1\n/\n", encoding="ascii",
                    )
                    (run / "planet_namelist").write_text(
                        "&planet_nl\n nfixorb=0\n/\n", encoding="ascii",
                    )
                    return run

                continuous = prepare("continuous", days=december_days + 1)
                self.run_model(continuous)
                diagnostic = (continuous / "plasim_diag").read_text()
                # Record the current limitation: no recalculation inside a run.
                self.assertEqual(re.findall(r"Year AD\s*=\s*(\d+)", diagnostic),
                                 ["2000"])
                self.assertIn("initialization only", diagnostic)

                split = prepare("split", days=december_days)
                self.run_model(split)
                (split / "plasim_status").replace(split / "plasim_restart")
                namelist = split / "plasim_namelist"
                namelist.write_text(namelist.read_text().replace(
                    f"n_run_days={december_days}", "n_run_days=1"
                ), encoding="ascii")
                self.run_model(split)
                diagnostic = (split / "plasim_diag").read_text()
                self.assertEqual(re.findall(r"Year AD\s*=\s*(\d+)", diagnostic),
                                 ["2001"])

                fresh = prepare("fresh", year=2001, month=1, days=1)
                self.run_model(fresh)
                pattern = (r"\* (?:Eccentricity|Obliquity \(deg\)|"
                           r"Long of perh\(deg\))\s*=\s*([\d.+-]+)")
                restarted_orbit = re.findall(pattern, diagnostic)
                self.assertEqual(len(restarted_orbit), 3)
                self.assertEqual(restarted_orbit, re.findall(
                    pattern, (fresh / "plasim_diag").read_text()
                ))
                self.assertNotEqual(restarted_orbit, re.findall(
                    pattern, (continuous / "plasim_diag").read_text()
                ))
                self.assertEqual(records(split / "plasim_status")["nstep"],
                                 records(continuous / "plasim_status")["nstep"])

                # An explicit orbital epoch must still override the restart date.
                (split / "plasim_status").replace(split / "plasim_restart")
                (split / "radmod_namelist").write_text(
                    "&radmod_nl\n iyrbp=50\n/\n", encoding="ascii",
                )
                self.run_model(split)
                self.assertEqual(re.findall(
                    r"Year AD\s*=\s*(\d+)",
                    (split / "plasim_diag").read_text(),
                ), ["1900"])

    def test_fixed_orbit_preserves_explicit_elements(self) -> None:
        for year in (2000, 2001):
            with self.subTest(year=year):
                run = self.prepare_run(f"fixed-orbit-{year}", days=0)
                (run / "plasim_namelist").write_text(
                    f"&plasim_nl\n n_start_year={year}, n_run_steps=1, "
                    "kick=0, ngui=0, seed=1\n/\n", encoding="ascii",
                )
                (run / "planet_namelist").write_text(
                    "&planet_nl\n nfixorb=1, eccen=0.02, obliq=24.0, "
                    "mvelp=105.0\n/\n", encoding="ascii",
                )
                self.run_model(run)
                diagnostic = (run / "plasim_diag").read_text()
                self.assertIn("Use input orbital parameters", diagnostic)
                for label, expected in (("Eccentricity", 0.02),
                                        ("Obliquity (deg)", 24.0),
                                        ("Long of perh(deg)", 105.0)):
                    match = re.search(re.escape(label) + r"\s*=\s*([\d.]+)",
                                      diagnostic)
                    self.assertIsNotNone(match, label)
                    self.assertEqual(float(match.group(1)), expected, label)

    def test_default_earth_state_matches_reference(self) -> None:
        """Check the new defaults without setting either date or orbit mode."""
        run = self.prepare_run("default-earth", days=1)
        self.run_model(run)
        actual = records(run / "plasim_status")
        expected = records(self.default_status)
        self.assertEqual(struct.unpack("=i", actual["nstep"])[0], 23040032)
        self.assertIn("Use input orbital parameters",
                      (run / "plasim_diag").read_text())
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
                    f"{field}[{worst}] differs from default reference: "
                    f"{values[worst]} vs {reference[worst]}",
                )

    def test_master_restart_can_continue(self) -> None:
        def prepare_legacy(name, *, days):
            run = self.prepare_run(name, days=days)
            namelist = run / "plasim_namelist"
            namelist.write_text(namelist.read_text().replace(
                "&plasim_nl\n", "&plasim_nl\n n_start_year=1,\n"
            ), encoding="ascii")
            (run / "planet_namelist").write_text(
                "&planet_nl\n nfixorb=0\n/\n", encoding="ascii",
            )
            return run

        # The historical fixture used year 1 and a calculated Berger orbit.
        run = prepare_legacy("master-restart", days=1)
        (run / "plasim_restart").write_bytes(self.legacy_status.read_bytes())
        self.run_model(run)
        state = records(run / "plasim_status")
        self.assertEqual(struct.unpack("=i", state["nstep"])[0], 11584)
        self.assertTrue(all(map(math.isfinite, doubles(state["dt"]))))
        continuous = prepare_legacy("legacy-continuous", days=2)
        self.run_model(continuous)
        reference = records(continuous / "plasim_status")
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
    @classmethod
    def setUpClass(cls) -> None:
        if shutil.which("gfortran") is None:
            raise unittest.SkipTest("gfortran is required")
        temporary = tempfile.TemporaryDirectory(prefix="plasim-calendar-")
        cls.addClassCleanup(temporary.cleanup)
        cls.work = Path(temporary.name)
        cls.executables = {}
        for precision, flags in (("single", []), ("double", ["-fdefault-real-8"])):
            build = cls.work / precision
            build.mkdir()
            executable = build / "calendar_test"
            command([
                "gfortran", "-O0", "-fcheck=all", *flags, "-o", str(executable),
                str(SOURCE / "calmod.f90"),
                str(ROOT / "tests" / "calendar_test.f90"),
            ], cwd=build)
            cls.executables[precision] = executable

    def check_case(self, case: str) -> None:
        for precision, executable in self.executables.items():
            with self.subTest(precision=precision):
                command([str(executable), case], cwd=self.work)

    def test_calendar_boundaries(self) -> None:
        self.check_case("dates")

    def test_simplified_time_of_day(self) -> None:
        self.check_case("time")

    def test_simplified_perpetual_dates(self) -> None:
        self.check_case("perpetual360")

    def test_gregorian_perpetual_dates(self) -> None:
        self.check_case("perpetual365")

    def test_perpetual_monthly_interpolation(self) -> None:
        self.check_case("interpolation")

    def test_invalid_perpetual_days(self) -> None:
        for precision, executable in self.executables.items():
            for year_days in (360, 365, 660):
                for day in (-1, 0, year_days + 1):
                    with self.subTest(precision=precision, year_days=year_days, day=day):
                        result = subprocess.run(
                            [str(executable), "invalid", str(year_days), str(day)],
                            cwd=self.work, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=10, check=False,
                        )
                        self.assertNotEqual(result.returncode, 0, result.stdout)
                        self.assertIn("YDAY2MMDD: day of year out of range", result.stdout)


if __name__ == "__main__":
    unittest.main()
