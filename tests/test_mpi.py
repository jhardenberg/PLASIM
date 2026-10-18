"""Two-rank MPI runs compared with serial runs of both ocean configurations."""

from __future__ import annotations

import math
from pathlib import Path
import re
import shutil
import struct
import tempfile
import unittest

from test_lsg import floats, lsg_output_records, prepare_coupled_run
from test_model import build_model, doubles, prepare_run, records, run_model


class FieldComparison:
    def assert_values_close(self, actual, expected, *, atol, rtol, label,
                            field_norm=False) -> None:
        self.assertEqual(len(actual), len(expected), label)
        self.assertTrue(all(map(math.isfinite, actual)), label)
        self.assertTrue(all(map(math.isfinite, expected)), label)
        differences = [abs(a - b) for a, b in zip(actual, expected)]
        if field_norm:
            # Serial transforms pair opposite latitudes; MPI transforms sum
            # rank-local contributions. Coupling amplifies their roundoff.
            # Scale relative error by the physical field, including its zeros.
            peak = max(map(abs, expected))
            reference_rms = math.sqrt(math.fsum(b*b for b in expected)
                                      / len(expected))
            error_rms = math.sqrt(math.fsum(d*d for d in differences)
                                  / len(differences))
            worst = max(range(len(differences)), key=differences.__getitem__)
            self.assertLessEqual(
                differences[worst], atol + rtol * peak,
                f"{label}[{worst}]: max error {differences[worst]}, "
                f"reference max {peak}, error RMS {error_rms}, "
                f"reference RMS {reference_rms}",
            )
            # A large field maximum must not hide a distributed bias.
            self.assertLessEqual(
                error_rms, atol + rtol * reference_rms,
                f"{label}: error RMS {error_rms}, reference RMS {reference_rms}",
            )
            return
        limits = [atol + rtol * abs(b) for b in expected]
        worst = max(range(len(actual)), key=lambda i: differences[i] / limits[i])
        self.assertLessEqual(
            differences[worst], limits[worst],
            f"{label}[{worst}]: MPI {actual[worst]} vs serial {expected[worst]}",
        )


class MPIComparisonTests(FieldComparison, unittest.TestCase):
    def test_coupled_comparison_handles_small_values(self) -> None:
        self.assert_values_close([2e-9, 0.8], [0.0, 0.8],
                                 atol=1e-10, rtol=1e-8, label="albedo",
                                 field_norm=True)

    def test_coupled_comparison_rejects_local_error(self) -> None:
        with self.assertRaises(AssertionError):
            self.assert_values_close([1e-4, 0.8], [0.0, 0.8],
                                     atol=1e-10, rtol=1e-8, label="albedo",
                                     field_norm=True)

    def test_coupled_comparison_rejects_distributed_bias(self) -> None:
        with self.assertRaisesRegex(AssertionError, "error RMS"):
            self.assert_values_close([1.0 + 8e-9, 8e-9, 8e-9, 8e-9],
                                     [1.0, 0.0, 0.0, 0.0],
                                     atol=1e-10, rtol=1e-8, label="field",
                                     field_norm=True)


class MPITests(FieldComparison, unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        for program in ("mpif90", "mpiexec"):
            if shutil.which(program) is None:
                raise unittest.SkipTest(f"{program} is required for MPI tests")
        cls.temp = tempfile.TemporaryDirectory(prefix="plasim-mpi-tests-")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.work = Path(cls.temp.name)

    def compare_configuration(self, *, lsg: bool) -> None:
        name = "lsg" if lsg else "mixed-layer"
        prepare = prepare_coupled_run if lsg else prepare_run
        serial = prepare(self.work, f"{name}-serial", days=2)
        parallel = prepare(self.work, f"{name}-mpi", days=2)
        serial_exe = build_model(self.work / f"{name}-serial-build", lsg=lsg)
        mpi_exe = build_model(self.work / f"{name}-mpi-build", lsg=lsg, ranks=2)
        run_model(serial_exe, serial)
        run_model(mpi_exe, parallel, launcher=["mpiexec", "-n", "2"])

        diagnostic = (parallel / "plasim_diag").read_text()
        self.assertEqual(
            {int(rank) for rank in re.findall(r"^\* CPU\s+(\d+)", diagnostic, re.M)},
            {0, 1},
        )
        expected = records(serial / "plasim_status")
        actual = records(parallel / "plasim_status")
        for field, value in (("nlat", 32), ("nlon", 64), ("nlev", 10),
                             ("nstep", 23040064)):
            self.assertEqual(struct.unpack("=i", actual[field])[0], value, field)
        self.assertEqual(actual["dls"], expected["dls"])
        # Parallel reductions can change roundoff; compare every value in both
        # gridpoint fields and global spectral fields rather than file bytes.
        fields = ["dt", "dq", "dalb", "ysst", "dicec", "diced",
                  "sz", "sd", "st", "sq", "sp"]
        if lsg:
            fields.append("yfldo")  # Returned LSG heat flux after MPI scatter.
        for field in fields:
            with self.subTest(configuration=name, field=field):
                self.assert_values_close(
                    doubles(actual[field]), doubles(expected[field]),
                    atol=1e-10, rtol=1e-8, label=field, field_norm=lsg,
                )

        if lsg:
            ocean = lsg_output_records(parallel / "lsg_output")
            reference = lsg_output_records(serial / "lsg_output")
            self.assertEqual({key[2] for key in ocean}, {20000101, 20000102})
            self.assertEqual(ocean.keys(), reference.keys())
            for key in ocean:
                with self.subTest(ocean_record=key):
                    # LSG Service fields are stored as 32-bit floats.
                    self.assert_values_close(
                        floats(ocean[key]), floats(reference[key]),
                        atol=1e-5, rtol=1e-6, label=str(key),
                    )

    def test_mpi_mixed_layer_matches_serial(self) -> None:
        self.compare_configuration(lsg=False)

    def test_mpi_lsg_matches_serial(self) -> None:
        self.compare_configuration(lsg=True)


if __name__ == "__main__":
    unittest.main()
