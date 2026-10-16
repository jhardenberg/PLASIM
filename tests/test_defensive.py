"""Focused checks of model diagnostics and supporting-tool failure paths."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from test_model import ROOT, SOURCE, command


class DiagnosticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if shutil.which("gfortran") is None:
            raise unittest.SkipTest("gfortran is required")
        temporary = tempfile.TemporaryDirectory(prefix="plasim-diagnostics-")
        cls.addClassCleanup(temporary.cleanup)
        cls.work = Path(temporary.name)
        cls.executable = cls.work / "diagnostics"
        # Discard unused model entry points, linking the real helper routines.
        linker = "-Wl,-dead_strip" if sys.platform == "darwin" else "-Wl,--gc-sections"
        command([
            "gfortran", "-O0", "-fdefault-real-8", "-fcheck=all",
            "-ffpe-trap=invalid,zero,overflow", "-finit-integer=-999",
            "-ffunction-sections", "-fdata-sections", linker,
            str(SOURCE / "resmod_def.f90"), str(SOURCE / "cpl.f90"),
            str(SOURCE / "restartmod.f90"), str(ROOT / "tests" / "defensive_test.f90"),
            "-o", str(cls.executable),
        ], cwd=cls.work)

    def test_coupling_diagnostics_and_results(self):
        command([str(self.executable), "coupling"], cwd=self.work)
        text = (self.work / "diagnostics.txt").read_text()
        for diagnostic in ("In CINTER:", "In CINTER2:", "In CFILL:", "In CONSERVE:",
                           "No Conservation", "no sea points"):
            self.assertIn(diagnostic, text)
        self.assertFalse(list(self.work.glob("fort.*")))

    def test_restart_equality_diagnostics(self):
        command([str(self.executable), "restart"], cwd=self.work)
        text = (self.work / "diagnostics.txt").read_text()
        self.assertIn("Array {same} is OK", text)
        self.assertIn("No Equality on different", text)
        self.assertFalse(list(self.work.glob("fort.*")))


class MostInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if shutil.which("cc") is None:
            raise unittest.SkipTest("cc is required")
        temporary = tempfile.TemporaryDirectory(prefix="plasim-most-input-")
        cls.addClassCleanup(temporary.cleanup)
        cls.work = Path(temporary.name)
        cls.executable = cls.work / "most_input"
        x11 = []
        if sys.platform == "darwin":
            if not Path("/opt/X11/include/X11/Xlib.h").is_file():
                raise unittest.SkipTest("X11 development files are required")
            x11 = ["-I/opt/X11/include", "-L/opt/X11/lib"]
        command([
            "cc", "-O0", "-I", str(ROOT), *x11,
            str(ROOT / "tests" / "most_input_test.c"), "-lm", "-lX11",
            "-o", str(cls.executable),
        ], cwd=cls.work)

    def run_reader(self, mode, path):
        return subprocess.run([str(self.executable), mode, str(path)], cwd=self.work,
                              capture_output=True, text=True, timeout=10)

    def test_settings_empty_and_final_line(self):
        settings = self.work / "settings.cfg"
        settings.write_text("")
        result = self.run_reader("settings", settings)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("READ=0", result.stdout)
        settings.write_text("[MoSt test]\nTEST = 7")  # No final newline.
        result = self.run_reader("settings", settings)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("READ=1", result.stdout)
        self.assertIn("VALUE=7", result.stdout)

    def test_grid_valid_and_malformed(self):
        path = self.work / "grid.sra"
        header = "".join(f"{n:10d}" for n in (129, 0, 0, 0, 8, 4, 0, 0)) + "\n"
        rows = ["".join(f"{i + j*8 + 1:12.5E}" for i in range(8)) + "\n"
                for j in range(4)]
        path.write_text(header + "".join(rows))
        result = self.run_reader("grid", path)
        self.assertEqual(result.returncode, 0, result.stderr)
        for invalid in ("", header, header + rows[0], header + "not numbers\n" * 4,
                        header.replace("         8", "        16"),
                        header + "1" * 240 + "\n"):
            with self.subTest(input=invalid[:85]):
                path.write_text(invalid)
                result = self.run_reader("grid", path)
                self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
                self.assertIn("grid", result.stderr.lower())
        result = self.run_reader("grid", self.work / "missing.sra")
        self.assertEqual(result.returncode, 3)

    def test_checked_in_orography_formats(self):
        for resolution, latitudes in (("T21", 32), ("T42", 64)):
            with self.subTest(resolution=resolution):
                path = ROOT / "plasim" / "dat" / resolution / f"N{latitudes:03d}_surf_0129.sra"
                result = self.run_reader(f"reference{latitudes}", path)
                self.assertEqual(result.returncode, 0, result.stderr)


class ScriptTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="plasim-scripts-")
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name)
        self.tools = self.work / "tools with spaces"
        self.tools.mkdir()
        self.scratch = self.work / "temporary files"
        self.scratch.mkdir()
        self.env = os.environ.copy()
        self.env.update(PATH=str(self.tools) + os.pathsep + self.env["PATH"],
                        TMPDIR=str(self.scratch), BURNER=str(self.tools / "burn7.x"))
        self.make_tool("burn7.x", '#!/bin/bash\ncat >/dev/null\nprintf "data" > "$2"\n')
        self.make_tool("cdo", '#!/bin/bash\nprintf "data" > "${!#}"\n')
        self.input = self.work / "input file"
        self.input.write_text("model output")
        self.output = self.work / "output file.nc"

    def make_tool(self, name, body):
        path = self.tools / name
        path.write_text(body)
        path.chmod(0o755)
        return path

    def run_script(self, script, *args):
        return subprocess.run(["bash", str(ROOT / "scripts" / script), *map(str, args)],
                              cwd=self.work, env=self.env, capture_output=True,
                              text=True, timeout=10)

    def assert_clean(self):
        self.assertEqual(list(self.scratch.iterdir()), [])
        self.assertFalse(list(self.work.glob("temp*.*.nc")))
        self.assertFalse(list(self.work.glob("burn*.nl")))

    def test_burn_success_and_paths_with_spaces(self):
        for variable in ("tas", "alb"):
            with self.subTest(variable=variable):
                result = self.run_script("burn.sh", self.input, self.output, variable)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(self.output.read_text(), "data")
                self.assert_clean()

    def test_burn_command_failures_and_cleanup(self):
        for tool in ("burn7.x", "cdo"):
            with self.subTest(tool=tool):
                self.setUp_tools_for_failure(tool)
                result = self.run_script("burn.sh", self.input, self.output, "tas")
                self.assertEqual(result.returncode, 23, result.stderr)
                self.assertFalse(self.output.exists())
                self.assert_clean()

    def test_burn_missing_executable(self):
        self.env["BURNER"] = str(self.tools / "missing")
        result = self.run_script("burn.sh", self.input, self.output, "tas")
        self.assertEqual(result.returncode, 127, result.stderr)
        self.assertIn("Required command not found", result.stderr)
        self.assert_clean()

    def test_repository_relative_defaults(self):
        repository = self.work / "repository with spaces"
        scripts = repository / "scripts"
        scripts.mkdir(parents=True)
        for name in ("burn.sh", "postmon.sh"):
            shutil.copy2(ROOT / "scripts" / name, scripts / name)
        (repository / "postprocessor").mkdir()
        shutil.copy2(self.tools / "burn7.x", repository / "postprocessor" / "burn7.x")
        self.env.pop("BURNER")
        self.env.pop("BURNSH", None)
        self.env.update(INDIR=str(self.work / "input directory"),
                        POSTDIR=str(self.work / "post directory"))
        Path(self.env["INDIR"]).mkdir()
        (Path(self.env["INDIR"]) / "MOST.001").write_text("model output")
        result = subprocess.run(["bash", str(scripts / "postmon.sh"), "example", "1", "1"],
                                cwd=self.work, env=self.env, capture_output=True,
                                text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((Path(self.env["POSTDIR"]) / "001/example_001_tas.nc").is_file())
        self.assert_clean()

    def setUp_tools_for_failure(self, tool):
        self.make_tool("burn7.x", '#!/bin/bash\ncat >/dev/null\nprintf "data" > "$2"\n')
        self.make_tool("cdo", '#!/bin/bash\nprintf "data" > "${!#}"\n')
        self.make_tool(tool, '#!/bin/bash\nexit 23\n')

    def test_postmon_paths_and_failure(self):
        self.env.update(INDIR=str(self.work / "input directory"),
                        POSTDIR=str(self.work / "post directory"),
                        BURNSH=str(self.tools / "extract"))
        Path(self.env["INDIR"]).mkdir()
        (Path(self.env["INDIR"]) / "MOST.001").write_text("model output")
        self.make_tool("extract", '#!/bin/bash\nprintf "data" > "$2"\n')
        result = self.run_script("postmon.sh", "example", "1", "1")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((Path(self.env["POSTDIR"]) / "001/example_001_tas.nc").is_file())
        self.assert_clean()
        self.make_tool("extract", '#!/bin/bash\nexit 23\n')
        result = self.run_script("postmon.sh", "example", "1", "1")
        self.assertEqual(result.returncode, 23)
        self.assert_clean()
        self.make_tool("extract", '#!/bin/bash\nprintf "data" > "$2"\n')
        self.make_tool("cdo", '#!/bin/bash\nexit 24\n')
        result = self.run_script("postmon.sh", "example", "1", "1")
        self.assertEqual(result.returncode, 24)
        self.assert_clean()
