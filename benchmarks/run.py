#!/usr/bin/env python3
"""Build and benchmark PlaSim independently of the regression-test harness."""
from __future__ import annotations

import argparse
import csv
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, TimeoutError as FutureTimeout, wait
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import shutil
import shlex
import signal
import statistics
import struct
import subprocess
import sys
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
RESOLUTIONS = {"T21": (32, 32), "T42": (64, 48)}  # latitudes, steps per Earth day
CASES = ("mixed", "mixed-spectral", "lsg", "lsg-spectral")
NAMELISTS = ("fluxmod", "icemod", "landmod", "miscmod", "oceanmod", "planet",
             "radmod", "rainmod", "seamod", "surfmod", "vegmod")
FIELDS = ("dt", "dq", "dalb", "ysst", "dicec", "yfldo", "sz", "sd", "st", "sq", "sp")


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def tree_digest(paths: list[Path], root: Path) -> str:
    result = hashlib.sha256()
    for path in sorted(paths):
        result.update(str(path.relative_to(root)).encode() + b"\0")
        result.update(digest(path).encode() + b"\0")
    return result.hexdigest()


def capture(command: list[str], cwd: Path | None = None) -> str:
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True,
                            errors="replace", timeout=30)
    if result.returncode:
        raise RuntimeError(f"Command failed: {command}\n{result.stderr}")
    return result.stdout.strip()


class ExecutionControl:
    """Track child process groups so a failed/interrupted batch can stop them all."""

    def __init__(self):
        self.lock = threading.Lock()
        self.processes = set()
        self.cancelled = False

    def start(self, command, **kwargs):
        with self.lock:
            if self.cancelled:
                raise RuntimeError("Benchmark batch cancelled")
            process = subprocess.Popen(command, **kwargs)
            self.processes.add(process)
            return process

    def discard(self, process):
        with self.lock:
            self.processes.discard(process)

    @staticmethod
    def signal_group(process, sig):
        try:
            os.killpg(process.pid, sig)
        except ProcessLookupError:
            pass

    def cancel(self):
        with self.lock:
            self.cancelled = True
            processes = list(self.processes)
        for process in processes:
            self.signal_group(process, signal.SIGTERM)
        # A single grace period for the whole batch, including MPI children.
        deadline = time.monotonic() + 5
        for process in processes:
            try:
                process.wait(timeout=max(0, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                pass
        for process in processes:
            self.signal_group(process, signal.SIGKILL)


def execute(command: list[str], cwd: Path, log: Path, env: dict, timeout: int,
            control: ExecutionControl | None = None) -> float:
    """Time the process/launcher only; stop its process group on timeout."""
    control = control if control is not None else ExecutionControl()
    with log.open("wb") as output:
        start = time.perf_counter()
        process = control.start(command, cwd=cwd, stdout=output, stderr=output,
                                env=env, start_new_session=True)
        try:
            # A blocking wait in a worker avoids Popen.wait(timeout)'s polling
            # delay, which can visibly bias timings of short model runs.
            with ThreadPoolExecutor(max_workers=1) as worker:
                finished = worker.submit(process.wait)
                try:
                    code = finished.result(timeout=timeout)
                except BaseException as error:
                    control.signal_group(process, signal.SIGTERM)
                    try:
                        finished.result(timeout=5)
                    except FutureTimeout:
                        control.signal_group(process, signal.SIGKILL)
                        finished.result()
                    # The launcher can exit before descendants do. Kill any
                    # remaining group members even when its wait succeeded.
                    control.signal_group(process, signal.SIGKILL)
                    if isinstance(error, FutureTimeout):
                        raise RuntimeError(f"Command timed out after {timeout}s; see {log}") from error
                    raise
            elapsed = time.perf_counter() - start
        finally:
            control.discard(process)
    if code:
        raise RuntimeError(f"Command exited {code}; see {log}")
    return elapsed


def schedule(jobs, max_cores: int, parallel: bool, control: ExecutionControl):
    """Run (core cost, callable) jobs without exceeding the shared rank budget."""
    pending = list(jobs)
    if any(cost < 1 or cost > max_cores for cost, _ in pending):
        raise ValueError("Every job must fit within the core budget")
    workers = min(len(pending), max_cores) if parallel else 1
    with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
        active = {}
        used = 0
        try:
            while pending or active:
                # First fitting job: independent small cases can fill free slots
                # while a larger MPI case waits for enough capacity.
                for job in pending[:]:
                    cost, function = job
                    if used + cost <= max_cores and (parallel or not active):
                        active[executor.submit(function)] = cost
                        used += cost
                        pending.remove(job)
                done, _ = wait(active, return_when=FIRST_COMPLETED)
                for future in done:
                    used -= active.pop(future)
                    future.result()
        except BaseException:
            control.cancel()
            for future in active:
                future.cancel()
            raise


def read_records(path: Path) -> dict[str, bytes]:
    """Read native gfortran sequential records, validating record boundaries."""
    def record(stream):
        marker = stream.read(4)
        if not marker:
            return None
        if len(marker) != 4:
            raise RuntimeError(f"Truncated record in {path}")
        size, = struct.unpack("=i", marker)
        if size < 0 or size > path.stat().st_size:
            raise RuntimeError(f"Unsupported record in {path}")
        data, closing = stream.read(size), stream.read(4)
        if len(data) != size or closing != marker:
            raise RuntimeError(f"Truncated record in {path}")
        return data

    result = {}
    with path.open("rb") as stream:
        while (name := record(stream)) is not None:
            data = record(stream)
            if data is None:
                raise RuntimeError(f"Missing restart payload in {path}")
            result[name.decode("ascii").strip()] = data
    return result


def state_summary(run: Path, resolution: str, days: int, lsg: bool,
                  coupling_days: int, diag: str) -> dict:
    if (run / "Abort_Message").exists():
        raise RuntimeError((run / "Abort_Message").read_text(errors="replace"))
    records = read_records(run / "plasim_status")
    nlat, steps = RESOLUTIONS[resolution]
    for name, expected in (("nlat", nlat), ("nlon", 2*nlat), ("nlev", 10),
                           ("nstep", (360 + days)*steps)):
        actual, = struct.unpack("=i", records[name])
        if actual != expected:
            raise RuntimeError(f"{name}: expected {expected}, got {actual}")
    result = {"nstep": (360 + days)*steps, "fields": {}}
    for field in FIELDS:
        if field not in records:
            raise RuntimeError(f"Missing state field: {field}")
        payload = records[field]
        if len(payload) % 8:
            raise RuntimeError(f"Expected 64-bit restart field: {field}")
        values = struct.unpack(f"={len(payload)//8}d", payload)
        if not values or not all(map(math.isfinite, values)):
            raise RuntimeError(f"Non-finite/empty state field: {field}")
        result["fields"][field] = {
            "count": len(values), "min": min(values), "max": max(values),
            "mean": math.fsum(values)/len(values),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
    if lsg:
        match = re.search(r"Normal end of LSG run.*?last timestep\s*=\s*(\d+)", diag)
        if match is None:
            raise RuntimeError("Missing normal LSG completion diagnostic")
        ocean_step = int(match.group(1))
        # This protocol fixes the initial atmosphere date to 1-Jan-0001;
        # LSG computes nt0=0 from that date, independently of kleiswi's unit.
        expected = days // coupling_days
        if ocean_step != expected:
            raise RuntimeError(f"LSG did not advance as expected: {ocean_step} != {expected}")
        if not (run / "mat77").is_file():
            raise RuntimeError("LSG did not create mat77")
        result["ocean_step"] = ocean_step
        result["ocean_restart_sha256"] = digest(run / "kleiin1")
    return result


def timers(diag: str) -> dict:
    number = r"([0-9.+\-EeDd]+)"
    expressions = {
        "total_cpu_root_seconds": r"Total CPU time\s*:\s*" + number,
        "radiation_elapsed_root_seconds": r"CPU usage in RADSTEP.*?All routines\s*:\s*" + number,
        "shortwave_elapsed_root_seconds": r"CPU usage in RADSTEP.*?Short wave\s*:\s*" + number,
        "longwave_elapsed_root_seconds": r"CPU usage in RADSTEP.*?Long\s+wave\s*:\s*" + number,
    }
    return {key: float(match.group(1).replace("D", "E").replace("d", "e"))
            for key, pattern in expressions.items()
            if (match := re.search(pattern, diag, re.S))}


def build(args, work: Path, output: Path, resolution: str, lsg: bool, ranks: int,
          env: dict) -> tuple[Path, dict]:
    name = f"{resolution}-{'lsg' if lsg else 'mixed'}-p{ranks}"
    directory = work / ("build-" + name)
    directory.mkdir()
    for path in (args.source / "plasim/src").iterdir():
        if path.suffix in (".f90", ".f", ".c") or path.name == "make_plasim":
            shutil.copy2(path, directory / path.name)
    if lsg:
        shutil.copy2(args.source / "lsg/src/lsgmod.f90", directory / "lsgmod.f90")
    source = (directory / "resmod_def.f90").read_text()
    for key, value in (("NLAT_ATM", RESOLUTIONS[resolution][0]),
                       ("NLEV_ATM", 10), ("NPRO_ATM", ranks)):
        source, count = re.subn(rf"({key}\s*=\s*)\d+", rf"\g<1>{value}", source)
        if count != 1:
            raise RuntimeError(f"Cannot configure {key} in resmod_def.f90")
    (directory / "resmod.f90").write_text(source)
    shutil.copy2(directory / "make_plasim", directory / "makefile")
    build_env = env.copy()
    build_env.pop("MAKEFLAGS", None)
    build_env.pop("MFLAGS", None)
    build_env.update(
        MOST_CC=args.cc, MOST_CC_OPTS=args.cflags,
        MOST_F90=args.mpifc if ranks > 1 else args.fc, MOST_F90_OPTS=args.fflags,
        MOST_PREC="-fdefault-real-8", MPIMOD="mpimod" if ranks > 1 else "mpimod_stub",
        GUIMOD="guimod_stub", PUMAX="pumax_stub", GUILIB="", FFTMOD="fftmod",
        RAINMOD="rainmod", VEGMOD="simba", PLAMOD="p_earth", LANDMOD="landmod",
        OCEAN="lsgmod" if lsg else "lsgmod_stub", OCEANCOUP="cpl" if lsg else "cpl_stub",
    )
    elapsed = execute(["make", "-e", "-j1", "plasim.x"], directory,
                      output / f"build-{name}.log", build_env, args.timeout)
    executable = directory / "plasim.x"
    return executable, {"seconds": elapsed, "sha256": digest(executable), "name": name}


def prepare(args, directory: Path, resolution: str, case: str) -> dict:
    directory.mkdir()
    lsg = case.startswith("lsg")
    for path in (args.source / f"plasim/dat/{resolution}").iterdir():
        if path.is_file():
            shutil.copy2(path, directory / path.name)
    if lsg:
        for path in (args.source / "lsg/dat").iterdir():
            if path.is_file():
                shutil.copy2(path, directory / path.name)
    configs = {f"{module}_namelist": f"&{module}_nl\n/\n" for module in NAMELISTS}
    configs["plasim_namelist"] = (
        "&plasim_nl\n n_run_years=0, n_run_months=0, "
        f"n_run_days={args.days}, n_run_steps=0, n_days_per_year=360, "
        "n_start_year=1, n_start_month=1, "
        f"kick=0, ngui=0, seed=1, noutput={int(args.io == 'daily')}, "
        f"nwpd=1, ndiagcf=0, ntime={int(not args.no_timers)}\n/\n")
    configs["radmod_namelist"] = (
        f"&radmod_nl\n nstartemp={int('spectral' in case)}, starbbtemp=5778.0\n/\n")
    if lsg:
        configs["oceanmod_namelist"] = (
            f"&oceanmod_nl\n nlsg=1, naomod={args.coupling_days*RESOLUTIONS[resolution][1]}, "
            "nocean=1, nhdiff=0\n/\n")
        cadence = 1 if args.io == "daily" else 100000000
        configs["input"] = (f"&param\n kiterm=8, ntback=100000000, "
                            f"ntout={cadence}, ntsurf={cadence}\n/\n")
    else:
        configs["oceanmod_namelist"] = "&oceanmod_nl\n nlsg=0, nocean=1\n/\n"
    for name, text in configs.items():
        (directory / name).write_text(text, encoding="ascii")
    if lsg:
        configs["cpl_namelist"] = (directory / "cpl_namelist").read_text()
    return configs


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT, help="Checkout to build (default: this repo)")
    parser.add_argument("--output", type=Path, required=True, help="New directory for results and logs")
    parser.add_argument("--resolutions", nargs="+", choices=RESOLUTIONS, default=list(RESOLUTIONS))
    parser.add_argument("--cases", nargs="+", choices=CASES, default=list(CASES))
    parser.add_argument("--ranks", nargs="+", type=int, default=[1], help="MPI sizes; 1 uses a serial build")
    parser.add_argument("--parallel", action="store_true",
                        help="Run independent cases concurrently (timings include contention)")
    available = len(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else (os.cpu_count() or 1)
    parser.add_argument("--max-cores", type=int, default=available,
                        help="Maximum simultaneous serial processes/MPI ranks (default: available logical CPUs)")
    parser.add_argument("--days", type=int, default=120)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--coupling-days", type=int, choices=(1, 10), default=10)
    parser.add_argument("--io", choices=("minimal", "daily"), default="minimal")
    parser.add_argument("--fc", default="gfortran")
    parser.add_argument("--mpifc", default="mpif90")
    parser.add_argument("--cc", default="cc")
    parser.add_argument("--fflags", default="-O3", help="Fortran optimization flags; precision is fixed separately")
    parser.add_argument("--cflags", default="-O3")
    parser.add_argument("--launcher", default="mpiexec", help="Quoted MPI launcher command/flags, before -n")
    parser.add_argument("--timeout", type=int, default=3600, help="Seconds per build/run")
    parser.add_argument("--work-dir", type=Path, help="Parent for temporary builds/runs (default: system temp)")
    parser.add_argument("--keep-work", action="store_true", help="Retain binaries and run directories for inspection")
    parser.add_argument("--no-timers", action="store_true", help="Disable model component timing instrumentation")
    args = parser.parse_args()
    args.launcher = shlex.split(args.launcher)
    if not args.launcher:
        parser.error("launcher must not be empty")
    args.source, args.output = args.source.resolve(), args.output.resolve()
    if args.work_dir:
        args.work_dir = args.work_dir.resolve()
    if args.days < 1 or args.repeats < 1 or args.warmups < 0 or args.timeout < 1:
        parser.error("days/repeats/timeout must be positive; warmups must be nonnegative")
    if args.max_cores < 1:
        parser.error("max-cores must be positive")
    if max(args.ranks) > args.max_cores:
        parser.error("each selected MPI rank count must fit within --max-cores")
    for resolution in args.resolutions:
        for ranks in args.ranks:
            if ranks < 1 or ranks & (ranks-1) or RESOLUTIONS[resolution][0] % ranks:
                parser.error("ranks must be powers of two dividing each selected latitude count")
    if any(case.startswith("lsg") for case in args.cases) and args.days % args.coupling_days:
        parser.error("LSG days must be a positive multiple of --coupling-days")
    for name in ("resolutions", "cases", "ranks"):
        setattr(args, name, list(dict.fromkeys(getattr(args, name))))
    return args


def main():
    args = arguments()
    tools = {"make": "make", "cc": args.cc}
    if 1 in args.ranks:
        tools["fc"] = args.fc
    if any(rank > 1 for rank in args.ranks):
        tools.update(mpifc=args.mpifc, launcher=args.launcher[0])
    for name, command in tools.items():
        if shutil.which(command) is None:
            raise RuntimeError(f"Required {name} executable not found: {command}")
    env = os.environ.copy()
    thread_env = {name: "1" for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                                        "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")}
    env.update(thread_env)
    versions = {name: {"path": shutil.which(command),
                       "version": capture([command, "--version"]).splitlines()[0]}
                for name, command in tools.items()}
    model_files = [p for d in ("plasim/src", "lsg/src")
                   for p in (args.source / d).iterdir() if p.is_file()]
    processor = platform.processor()
    if sys.platform == "darwin":
        try:
            processor = capture(["sysctl", "-n", "machdep.cpu.brand_string"])
        except RuntimeError:
            pass  # Sandboxed hosts can deny this optional hardware query.
    elif Path("/proc/cpuinfo").is_file():
        processor = next((line.split(":", 1)[1].strip()
                          for line in Path("/proc/cpuinfo").read_text().splitlines()
                          if line.startswith("model name")), processor)
    relevant_env = {key: value for key, value in env.items()
                    if key.startswith(("OMP_", "OPENBLAS_", "MKL_", "VECLIB_", "KMP_",
                                       "OMPI_MCA_", "MPICH_", "I_MPI_"))
                    and not re.search(r"TOKEN|SECRET|PASSWORD|CREDENTIAL|KEY", key, re.I)}
    machine = {"hostname": platform.node(), "platform": platform.platform(),
               "machine": platform.machine(), "processor": processor,
               "logical_cpus": os.cpu_count(),
               "affinity": sorted(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else None}
    report = {"schema_version": 1, "status": "running", "created_utc": datetime.now(timezone.utc).isoformat(),
              "suite_sha256": digest(Path(__file__)), "source": {
                  "path": str(args.source), "commit": capture(["git", "rev-parse", "HEAD"], args.source),
                  "tracked_changes": capture(["git", "status", "--porcelain", "--untracked-files=no"], args.source),
                  "model_sha256": tree_digest(model_files, args.source)},
              "environment": {"machine": machine, "tools": versions, "thread_environment": thread_env, "runtime_environment": relevant_env,
                              "launcher": args.launcher if any(r > 1 for r in args.ranks) else []},
              "settings": {"days": args.days, "repeats": args.repeats, "warmups": args.warmups,
                           "coupling_days": args.coupling_days, "io": args.io,
                           "timers": not args.no_timers, "fflags": args.fflags,
                           "cflags": args.cflags, "precision_flags": "-fdefault-real-8",
                           "parallel": args.parallel, "max_cores": args.max_cores},
              "work_directory": None, "kept_work": args.keep_work, "cases": []}
    args.output.mkdir(parents=True, exist_ok=False)
    if args.work_dir:
        args.work_dir.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="plasim-benchmark-", dir=args.work_dir))
    report["work_directory"] = str(work)
    report["environment"]["workspace_storage"] = {
        "parent": str(work.parent.resolve()), "filesystem_device": work.stat().st_dev}
    result_path = args.output / "results.json"

    report_lock = threading.RLock()

    def save():
        with report_lock:
            result_path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")

    control = ExecutionControl()

    def run_case(entry, executable, template, case_output):
        name, resolution, ranks = entry["name"], entry["resolution"], entry["ranks"]
        lsg = entry["case"].startswith("lsg")
        for index in range(args.warmups + args.repeats):
            warmup = index < args.warmups
            label = f"{'warmup' if warmup else 'sample'}-{index+1:02d}"
            run = work / f"{name}-{label}"
            shutil.copytree(template, run)
            command = ([*args.launcher, "-n", str(ranks)] if ranks > 1 else []) + [str(executable)]
            print(f"Running {name}: {label}, {args.days} simulated days", flush=True)
            started_utc = datetime.now(timezone.utc).isoformat()
            try:
                wall = execute(command, run, case_output / (label + ".stdout.log"), env, args.timeout, control)
            finally:
                if (run / "plasim_diag").exists():
                    shutil.copy2(run / "plasim_diag", case_output / (label + ".diag.log"))
            finished_utc = datetime.now(timezone.utc).isoformat()
            diag = (run / "plasim_diag").read_text(errors="replace")
            if ranks > 1:
                seen = {int(r) for r in re.findall(r"^\* CPU\s+(\d+)", diag, re.M)}
                if seen != set(range(ranks)):
                    raise RuntimeError(f"Unexpected MPI rank diagnostics: {seen}")
            state = state_summary(run, resolution, args.days, lsg, args.coupling_days, diag)
            sample = {"warmup": warmup, "wall_seconds": wall,
                      "started_utc": started_utc, "finished_utc": finished_utc,
                      "simulated_years_per_wall_day": (args.days/360)*86400/wall,
                      "command": command, "timers": timers(diag), "state": state}
            with report_lock:
                entry["samples"].append(sample)
                save()
            if not args.keep_work:
                shutil.rmtree(run)
        measured = [s["wall_seconds"] for s in entry["samples"] if not s["warmup"]]
        median = statistics.median(measured)
        summary = {"median_wall_seconds": median, "min_wall_seconds": min(measured),
                   "max_wall_seconds": max(measured),
                   "stdev_wall_seconds": statistics.stdev(measured) if len(measured) > 1 else None,
                   "median_absolute_deviation_seconds": statistics.median(abs(t-median) for t in measured),
                   "simulated_years_per_wall_day": (args.days/360)*86400/median}
        print(f"  {name}: median {median:.3f} s, range {min(measured):.3f}–{max(measured):.3f} s", flush=True)
        with report_lock:
            entry["summary"] = summary
            save()

    try:
        save()
        builds = {}
        jobs = []
        for resolution in args.resolutions:
            for ranks in args.ranks:
                for case in args.cases:
                    lsg = case.startswith("lsg")
                    key = (resolution, lsg, ranks)
                    if key not in builds:
                        print(f"Building {resolution}, {'LSG' if lsg else 'mixed'}, {ranks} rank(s)", flush=True)
                        builds[key] = build(args, work, args.output, resolution, lsg, ranks, env)
                    executable, build_info = builds[key]
                    name = f"{resolution}-{case}-p{ranks}"
                    case_output = args.output / name
                    case_output.mkdir()
                    template = work / (name + "-inputs")
                    configs = prepare(args, template, resolution, case)
                    for filename, text in configs.items():
                        (case_output / filename).write_text(text)
                    entry = {"name": name, "resolution": resolution, "case": case, "ranks": ranks,
                             "input_sha256": tree_digest(list(template.iterdir()), template),
                             "namelists": configs, "build": build_info, "samples": []}
                    report["cases"].append(entry)
                    jobs.append((ranks, lambda e=entry, x=executable, t=template, o=case_output:
                                 run_case(e, x, t, o)))
        save()
        # Complete all builds and template preparation before timed runs.
        schedule(jobs, args.max_cores, args.parallel, control)
        report["status"] = "complete"
        save()
        with (args.output / "samples.csv").open("w", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["case", "warmup", "wall_seconds", "simulated_years_per_wall_day"])
            for entry in report["cases"]:
                for sample in entry["samples"]:
                    writer.writerow([entry["name"], sample["warmup"], sample["wall_seconds"],
                                     sample["simulated_years_per_wall_day"]])
    except BaseException as error:
        report.update(status="failed", error=f"{type(error).__name__}: {error}")
        save()
        raise
    finally:
        if not args.keep_work:
            shutil.rmtree(work)
    print(f"Results: {result_path}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, subprocess.SubprocessError) as error:
        sys.exit(str(error))
