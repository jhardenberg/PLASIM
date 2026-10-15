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


class MPITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        for program in ("mpif90", "mpiexec"):
            if shutil.which(program) is None:
                raise unittest.SkipTest(f"{program} is required for MPI tests")
        cls.temp = tempfile.TemporaryDirectory(prefix="plasim-mpi-tests-")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.work = Path(cls.temp.name)

    def assert_values_close(self, actual, expected, *, atol, rtol, label) -> None:
        self.assertEqual(len(actual), len(expected), label)
        self.assertTrue(all(map(math.isfinite, actual)), label)
        self.assertTrue(all(map(math.isfinite, expected)), label)
        differences = [abs(a - b) for a, b in zip(actual, expected)]
        limits = [atol + rtol * abs(b) for b in expected]
        worst = max(range(len(actual)), key=lambda i: differences[i] / limits[i])
        self.assertLessEqual(
            differences[worst], limits[worst],
            f"{label}[{worst}]: MPI {actual[worst]} vs serial {expected[worst]}",
        )

    def compare_configuration(self, *, lsg: bool, spectral: bool = False) -> None:
        name = "lsg" if lsg else "mixed-layer"
        if spectral:
            name += "-spectral"
        prepare = prepare_coupled_run if lsg else prepare_run
        serial = prepare(self.work, f"{name}-serial", days=2)
        parallel = prepare(self.work, f"{name}-mpi", days=2)
        if spectral:
            for run in (serial, parallel):
                (run / "radmod_namelist").write_text(
                    "&radmod_nl\n nstartemp=1\n/\n", encoding="ascii"
                )
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
                             ("nstep", 11584)):
            self.assertEqual(struct.unpack("=i", actual[field])[0], value, field)
        self.assertEqual(actual["dls"], expected["dls"])
        # These two replicated values must not be gathered as a grid field.
        for label, state in (("serial", expected), ("MPI", actual)):
            self.assertEqual(len(state["zsolars"]), 16, f"{label} zsolars size")
        self.assert_values_close(
            doubles(actual["zsolars"]), doubles(expected["zsolars"]),
            atol=1e-14, rtol=1e-12, label="zsolars",
        )
        if spectral:
            fractions = doubles(actual["zsolars"])
            self.assertTrue(all(0.0 < value < 1.0 for value in fractions))
            self.assertAlmostEqual(math.fsum(fractions), 1.0, delta=1e-12)
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
                    atol=1e-10, rtol=1e-8, label=field,
                )

        if lsg:
            ocean = lsg_output_records(parallel / "lsg_output")
            reference = lsg_output_records(serial / "lsg_output")
            self.assertEqual({key[2] for key in ocean}, {10101, 10102})
            self.assertEqual(ocean.keys(), reference.keys())
            for key in ocean:
                with self.subTest(ocean_record=key):
                    # LSG Service fields are stored as 32-bit floats.
                    self.assert_values_close(
                        floats(ocean[key]), floats(reference[key]),
                        atol=1e-5, rtol=1e-6, label=str(key),
                    )
        else:
            split = prepare(self.work, f"{name}-mpi-split", days=1)
            if spectral:
                shutil.copy2(parallel / "radmod_namelist", split)
            run_model(mpi_exe, split, launcher=["mpiexec", "-n", "2"])
            (split / "plasim_status").replace(split / "plasim_restart")
            run_model(mpi_exe, split, launcher=["mpiexec", "-n", "2"])
            continued = records(split / "plasim_status")
            self.assertEqual(continued.keys(), actual.keys())
            for field in actual:
                with self.subTest(configuration=name, restart_field=field):
                    self.assertTrue(
                        continued[field] == actual[field],
                        f"{field} differs between continuous and restarted MPI runs",
                    )

    def test_mpi_mixed_layer_matches_serial(self) -> None:
        self.compare_configuration(lsg=False)

    def test_mpi_lsg_matches_serial(self) -> None:
        self.compare_configuration(lsg=True)

    def test_mpi_spectral_matches_serial(self) -> None:
        self.compare_configuration(lsg=False, spectral=True)


if __name__ == "__main__":
    unittest.main()
