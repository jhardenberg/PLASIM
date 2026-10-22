"""Parallel test runner for PlaSim test suites using the standard library."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from pathlib import Path
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = ROOT / "tests"

# Known suites ordered by descending execution time to maximize parallel throughput.
DEFAULT_SUITE_ORDER = [
    "test_timing.py",
    "test_mpi.py",
    "test_model.py",
    "test_lsg.py",
    "test_defensive.py",
    "test_scripts.py",
]


class SuiteResult:
    def __init__(self, name: str, returncode: int, duration: float, stdout: str, stderr: str):
        self.name = name
        self.returncode = returncode
        self.duration = duration
        self.stdout = stdout
        self.stderr = stderr

    @property
    def passed(self) -> bool:
        return self.returncode == 0


def discover_test_files(tests_dir: Path, patterns: list[str] | None = None) -> list[str]:
    """Discover test_*.py files, matching optional filter patterns or specific files."""
    all_files = sorted([f.name for f in tests_dir.glob("test_*.py")])
    ordered: list[str] = []
    # Place known suites first according to DEFAULT_SUITE_ORDER
    for name in DEFAULT_SUITE_ORDER:
        if name in all_files:
            ordered.append(name)
    for name in all_files:
        if name not in ordered:
            ordered.append(name)

    if not patterns:
        return ordered

    filtered: list[str] = []
    for target in patterns:
        target_name = Path(target).name
        if not target_name.endswith(".py"):
            target_name += ".py"
        matched = False
        for name in ordered:
            if target_name == name or Path(target).stem == Path(name).stem:
                if name not in filtered:
                    filtered.append(name)
                matched = True
        if not matched:
            # Try substring match
            for name in ordered:
                if target in name and name not in filtered:
                    filtered.append(name)
                    matched = True
        if not matched:
            print(f"Warning: pattern or file '{target}' matched no test files.", file=sys.stderr)
    return filtered


def run_single_suite(test_file: str, *, verbose: bool, failfast: bool) -> SuiteResult:
    """Run a single test suite in an isolated subprocess."""
    cmd = [
        sys.executable, "-m", "unittest", "discover",
        "-s", str(TESTS_DIR), "-p", test_file,
    ]
    if verbose:
        cmd.append("-v")
    if failfast:
        cmd.append("-f")

    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{TESTS_DIR}{os.pathsep}{ROOT}" + (
        f"{os.pathsep}{existing_pythonpath}" if existing_pythonpath else ""
    )

    t0 = time.perf_counter()
    result = subprocess.run(
        cmd,
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    duration = time.perf_counter() - t0
    return SuiteResult(test_file, result.returncode, duration, result.stdout, "")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Parallel test runner for PlaSim using standard-library unittest.",
    )
    parser.add_argument(
        "targets",
        nargs="*",
        help="Optional test files or pattern filters (e.g. test_mpi.py or mpi)",
    )
    parser.add_argument(
        "-j", "--jobs",
        type=int,
        default=max(1, min(4, os.cpu_count() or 1)),
        help="Number of concurrent test suites to run (default: min(4, CPU count))",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose test execution output",
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Quiet output; only report summaries and failures",
    )
    parser.add_argument(
        "-f", "--failfast",
        action="store_true",
        help="Stop on first test failure",
    )
    parser.add_argument(
        "-k", "--pattern",
        action="append",
        dest="patterns",
        help="Only run tests whose module matches the pattern",
    )

    args = parser.parse_args(argv)

    patterns = (args.targets or []) + (args.patterns or [])
    test_files = discover_test_files(TESTS_DIR, patterns=patterns if patterns else None)

    if not test_files:
        print("No test files found to run.", file=sys.stderr)
        return 1

    jobs = max(1, args.jobs)
    print(f"Running {len(test_files)} test suite(s) with {jobs} worker(s)...")

    results: list[SuiteResult] = []
    overall_start = time.perf_counter()

    if jobs == 1 or len(test_files) == 1:
        # Run sequentially
        for test_file in test_files:
            if not args.quiet:
                print(f"Starting {test_file}...")
            res = run_single_suite(test_file, verbose=args.verbose, failfast=args.failfast)
            results.append(res)
            status = "PASS" if res.passed else "FAIL"
            print(f"[{status}] {test_file} ({res.duration:.2f}s)")
            if not res.passed or (args.verbose and not args.quiet):
                print(res.stdout)
            if args.failfast and not res.passed:
                break
    else:
        # Run in parallel using thread pool dispatching subprocesses
        with ThreadPoolExecutor(max_workers=jobs) as executor:
            future_to_file = {
                executor.submit(run_single_suite, f, verbose=args.verbose, failfast=args.failfast): f
                for f in test_files
            }
            for future in as_completed(future_to_file):
                res = future.result()
                results.append(res)
                status = "PASS" if res.passed else "FAIL"
                print(f"[{status}] {res.name} ({res.duration:.2f}s)")
                if not res.passed:
                    print(res.stdout)
                elif args.verbose and not args.quiet:
                    # In verbose mode, print full output when suite completes
                    print(res.stdout)
                if args.failfast and not res.passed:
                    executor.shutdown(wait=False, cancel_futures=True)
                    break

    overall_duration = time.perf_counter() - overall_start

    # Summary table
    results.sort(key=lambda r: r.duration, reverse=True)
    passed_count = sum(1 for r in results if r.passed)
    failed_suites = [r.name for r in results if not r.passed]

    print("\n" + "=" * 70)
    print("Test Suite Summary:")
    print("-" * 70)
    for r in results:
        status_str = "OK" if r.passed else "FAILED"
        print(f"  {r.name:25s} {status_str:8s} {r.duration:7.2f}s")
    print("-" * 70)
    print(
        f"Total: {len(results)} suite(s), {passed_count} passed, "
        f"{len(failed_suites)} failed in {overall_duration:.2f}s "
        f"(using {jobs} worker(s))"
    )
    print("=" * 70)

    if failed_suites:
        print(f"FAILED (suites: {', '.join(failed_suites)})", file=sys.stderr)
        return 1

    print("ALL TEST SUITES PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
