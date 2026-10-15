"""Regression tests for the real, headless PlaSim–LSG coupled model."""

from __future__ import annotations

import math
from pathlib import Path
import shutil
import struct
import tempfile
import unittest

from test_model import (
    ROOT, _record, build_model, doubles, prepare_run, records, run_model,
)


def floats(data: bytes) -> tuple[float, ...]:
    return struct.unpack(f"={len(data) // 4}f", data)


def lsg_output_records(path: Path) -> dict[tuple[int, int, int], bytes]:
    """Read LSG Service records, keyed by code, level, and date."""
    result = {}
    with path.open("rb") as stream:
        while (header := _record(stream)) is not None:
            if len(header) != 32:
                raise AssertionError("Expected an eight-integer LSG Service header")
            code, level, date, hour, nlon, nlat, _, _ = struct.unpack("=8i", header)
            if (nlon, nlat, hour) != (72, 76, 0):
                raise AssertionError(f"Unexpected LSG grid or time: {header!r}")
            data = _record(stream)
            if data is None or len(data) != nlon * nlat * 4:
                raise AssertionError("Missing or truncated LSG Service field")
            key = (code, level, date)
            if key in result:
                raise AssertionError(f"Duplicate LSG Service record: {key}")
            result[key] = data
    return result


class LSGTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = tempfile.TemporaryDirectory(prefix="plasim-lsg-tests-")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.work = Path(cls.temp.name)
        cls.executable = build_model(cls.work / "build", lsg=True)
        cls.continuous = cls.prepare_coupled_run("continuous", days=2)
        run_model(cls.executable, cls.continuous)
        cls.ocean = lsg_output_records(cls.continuous / "lsg_output")

    @classmethod
    def prepare_coupled_run(cls, name: str, *, days: int) -> Path:
        run = prepare_run(cls.work, name, days=days)
        # Match MoSt: LSG's data also supply the coupled atmosphere's land mask.
        for source in (ROOT / "lsg" / "dat").iterdir():
            shutil.copy2(source, run / source.name)
        namelist = run / "plasim_namelist"
        namelist.write_text(
            namelist.read_text(encoding="ascii").replace(
                "&plasim_nl\n", "&plasim_nl\n n_days_per_year=360,\n"
            ), encoding="ascii",
        )
        # T21 has 32 atmosphere steps/day. Daily coupling makes this short run
        # advance LSG twice, rather than waiting for the default ten-day interval.
        (run / "oceanmod_namelist").write_text(
            "&oceanmod_nl\n nlsg=1, naomod=32, nocean=1, nhdiff=0\n/\n",
            encoding="ascii",
        )
        (run / "input").write_text(
            "&param\n kiterm=8, ntback=360, ntout=1, ntsurf=1\n/\n",
            encoding="ascii",
        )
        return run

    def test_coupled_t21_two_day_regression(self) -> None:
        self.assertEqual({key[2] for key in self.ocean}, {10101, 10102})
        for key, data in self.ocean.items():
            with self.subTest(record=key):
                self.assertTrue(all(map(math.isfinite, floats(data))))

        for date in (10101, 10102):
            for code in (-40, -2, -5):  # Wet mask, temperature, and salinity.
                self.assertEqual(
                    {level for c, level, d in self.ocean if c == code and d == date},
                    set(range(1, 23)),
                )
            mask = floats(self.ocean[-40, 1, date])
            self.assertEqual(set(mask), {0.0, 1.0})
            self.assertEqual(sum(mask), 3447)

        # Surface wet-point means from master d2eef95, gfortran 15.2, -O0.
        # Check both the ocean state and the atmospheric forcing received by LSG.
        mask = floats(self.ocean[-40, 1, 10102])
        for code, expected, tolerance in (
            (-2, 286.678575, 0.05),     # Potential temperature (K).
            (-5, 34.271895, 0.005),     # Salinity (per mille).
            (-52, -0.0236787, 0.001),   # Zonal stress from PlaSim (Pa).
            (-53, 0.00502879, 0.001),   # Meridional stress from PlaSim (Pa).
            (-18, -47.37544, 2.0),      # LSG heat flux to the mixed layer (W/m2).
        ):
            with self.subTest(code=code):
                wet = [v for v, m in zip(floats(self.ocean[code, 1, 10102]), mask)
                       if m == 1.0]
                self.assertAlmostEqual(math.fsum(wet) / len(wet), expected,
                                       delta=tolerance)
        for code in (-2, -5):
            self.assertNotEqual(self.ocean[code, 1, 10101],
                                self.ocean[code, 1, 10102])

        atmosphere = records(self.continuous / "plasim_status")
        self.assertEqual(struct.unpack("=i", atmosphere["nstep"])[0], 11584)
        # yfldo checks the return path: LSG heat flux interpolated onto PlaSim.
        for field, expected, tolerance in (
            ("dt", 277.594045, 0.3), ("yfldo", -30.81046, 2.0),
        ):
            values = doubles(atmosphere[field])
            self.assertTrue(all(map(math.isfinite, values)), field)
            self.assertAlmostEqual(math.fsum(values) / len(values), expected,
                                   delta=tolerance, msg=field)
        self.assertEqual((self.continuous / "kleiswi").read_text().split(),
                         ["84", "0"])

    def test_coupled_restart_matches_continuous_run(self) -> None:
        split = self.prepare_coupled_run("split", days=1)
        run_model(self.executable, split)
        (split / "plasim_status").replace(split / "plasim_restart")
        # Keep LSG's kleiin1/kleiswi and generated matrix in the same run directory.
        run_model(self.executable, split)
        for filename in ("plasim_status", "kleiin1"):
            with self.subTest(file=filename):
                self.assertEqual((split / filename).read_bytes(),
                                 (self.continuous / filename).read_bytes())
        self.assertEqual(
            lsg_output_records(split / "lsg_output"),
            {key: data for key, data in self.ocean.items() if key[2] == 10102},
        )


if __name__ == "__main__":
    unittest.main()
