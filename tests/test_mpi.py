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

    def test_mpi_nondefault_parameters_match_serial(self) -> None:
        serial_exe = build_model(self.work / "parameters-serial-build")
        mpi_exe = build_model(self.work / "parameters-mpi-build", ranks=2)
        control = prepare_run(self.work, "parameters-control", days=2)
        run_model(serial_exe, control)
        control_state = records(control / "plasim_status")
        tidal_settings = (
            "nfixorb=1, eccen=0., obliq=0., ltidally_locked=.true., "
        )
        cases = (
            ("soilcap", "landmod", "soilcap=1.2e6"),
            ("tidal-lock", "planet", tidal_settings + "tl_substellar=180."),
            ("substellar-longitude", "planet", tidal_settings + "tl_substellar=90."),
        )
        serial_temperatures = {}
        for name, module, settings in cases:
            with self.subTest(parameter=name):
                serial = prepare_run(self.work, f"{name}-serial", days=2)
                parallel = prepare_run(self.work, f"{name}-mpi", days=2)
                for run in (serial, parallel):
                    (run / f"{module}_namelist").write_text(
                        f"&{module}_nl\n {settings}\n/\n", encoding="ascii"
                    )
                run_model(serial_exe, serial)
                run_model(mpi_exe, parallel, launcher=["mpiexec", "-n", "2"])
                expected = records(serial / "plasim_status")
                actual = records(parallel / "plasim_status")
                self.assertEqual(struct.unpack("=i", actual["nstep"])[0], 11584)
                # Verify that each input changes the serial solution, so an
                # ignored namelist setting cannot make the comparison pass.
                self.assertNotEqual(expected["dt"], control_state["dt"])
                serial_temperatures[name] = expected["dt"]
                for field in ("dt", "dq", "dalb", "dsalb1", "dsalb2", "dsoilt",
                              "ysst", "dicec", "diced", "sz", "sd", "st", "sq", "sp"):
                    self.assert_values_close(
                        doubles(actual[field]), doubles(expected[field]),
                        atol=1e-10, rtol=1e-8, label=f"{name}: {field}",
                    )
        self.assertNotEqual(serial_temperatures["tidal-lock"],
                            serial_temperatures["substellar-longitude"])

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
                             ("nstep", 11584)):
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

    def test_mpi_mixed_layer_matches_serial(self) -> None:
        self.compare_configuration(lsg=False)

    def test_mpi_lsg_matches_serial(self) -> None:
        self.compare_configuration(lsg=True)


if __name__ == "__main__":
    unittest.main()
