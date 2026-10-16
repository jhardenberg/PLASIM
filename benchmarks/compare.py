#!/usr/bin/env python3
"""Summarize benchmark samples/scaling, or compare two matched benchmark runs."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import statistics
import sys


def load(path: Path) -> dict:
    report = json.loads((path / "results.json" if path.is_dir() else path).read_text())
    if report.get("schema_version") != 1 or report.get("status") != "complete":
        raise ValueError(f"Only complete schema-1 results can be compared: {path}")
    for case in report["cases"]:
        times = measured(case)
        if not times or not all(t > 0 and math.isfinite(t) for t in times):
            raise ValueError(f"Missing/invalid measured samples: {case['name']}")
    if not report["cases"]:
        raise ValueError("No benchmark cases")
    return report


def measured(case: dict) -> list[float]:
    return [sample["wall_seconds"] for sample in case["samples"] if not sample["warmup"]]


def median(case: dict) -> float:
    return statistics.median(measured(case))


def summary(report: dict):
    cases = {(case["resolution"], case["case"], case["ranks"]): case for case in report["cases"]}
    print("Case                         n   Median(s)    Min–max(s)         Speedup/p1  Efficiency")
    for key, case in cases.items():
        values = measured(case)
        serial = cases.get((*key[:2], 1))
        speedup = median(serial)/median(case) if serial else None
        scaling = f"{speedup:10.3f}x  {100*speedup/key[2]:8.1f}%" if speedup else "        n/a        n/a"
        print(f"{case['name']:28} {len(values):2} {median(case):10.3f} "
              f"{min(values):8.3f}–{max(values):8.3f} {scaling}")
    print("Scaling compares separately built serial/MPI binaries; it includes launch and initialization costs.")


def compare(baseline: dict, candidate: dict, allow_mismatch: bool) -> list[dict]:
    differences = []
    if baseline["suite_sha256"] != candidate["suite_sha256"]:
        differences.append("benchmark runner SHA-256")
    if baseline["environment"] != candidate["environment"]:
        differences.append("machine/toolchain/launcher/thread environment")
    for setting in ("days", "warmups", "coupling_days", "io", "timers",
                    "fflags", "cflags", "precision_flags"):
        if baseline["settings"][setting] != candidate["settings"][setting]:
            differences.append(f"setting {setting}: {baseline['settings'][setting]!r} vs {candidate['settings'][setting]!r}")
    reference = {case["name"]: case for case in baseline["cases"]}
    proposed = {case["name"]: case for case in candidate["cases"]}
    common = reference.keys() & proposed.keys()
    if not common:
        raise ValueError("No matching resolution/configuration/rank cases")
    for name in sorted(common):
        if reference[name]["input_sha256"] != proposed[name]["input_sha256"]:
            differences.append(f"runtime input SHA-256 for {name}")
    if differences:
        details = "\n".join("- " + difference for difference in differences)
        if not allow_mismatch:
            raise ValueError("Incompatible benchmark conditions:\n" + details +
                             "\nUse --allow-mismatch only for an intentional descriptive comparison.")
        print("Configuration differences explicitly allowed:\n" + details)
    omitted = reference.keys() ^ proposed.keys()
    if omitted:
        print("Unmatched cases omitted: " + ", ".join(sorted(omitted)))
    print("Case                         Base(s)    New(s)    Speedup   Time saved   n(base/new)  Changed fields")
    rows = []
    for name in sorted(common):
        before, after = reference[name], proposed[name]
        base, new = median(before), median(after)
        first_base = next(s["state"] for s in before["samples"] if not s["warmup"])
        first_new = next(s["state"] for s in after["samples"] if not s["warmup"])
        fields = first_base["fields"].keys() & first_new["fields"].keys()
        changed = sum(first_base["fields"][f]["sha256"] != first_new["fields"][f]["sha256"] for f in fields)
        row = {"case": name, "baseline_median_seconds": base, "candidate_median_seconds": new,
               "speedup": base/new, "time_saved_percent": 100*(1-new/base),
               "baseline_range_seconds": [min(measured(before)), max(measured(before))],
               "candidate_range_seconds": [min(measured(after)), max(measured(after))],
               "baseline_samples": len(measured(before)), "candidate_samples": len(measured(after)),
               "changed_selected_state_fields": changed, "configuration_differences": differences,
               "root_timer_speedups": {}}
        for timer in ("total_cpu_root_seconds", "radiation_elapsed_root_seconds",
                      "shortwave_elapsed_root_seconds", "longwave_elapsed_root_seconds"):
            base_times = [s["timers"][timer] for s in before["samples"] if not s["warmup"] and timer in s["timers"]]
            new_times = [s["timers"][timer] for s in after["samples"] if not s["warmup"] and timer in s["timers"]]
            if base_times and new_times and min(statistics.median(base_times), statistics.median(new_times)) > 0:
                row["root_timer_speedups"][timer] = statistics.median(base_times)/statistics.median(new_times)
        rows.append(row)
        print(f"{name:28} {base:8.3f} {new:9.3f} {base/new:9.3f}x {100*(1-new/base):9.2f}% "
              f"{len(measured(before)):5}/{len(measured(after)):<5} {changed:7}/{len(fields)}")
        print(f"  ranges: base {min(measured(before)):.3f}–{max(measured(before)):.3f}s; "
              f"new {min(measured(after)):.3f}–{max(measured(after)):.3f}s")
    print("Ratios/ranges are descriptive, not significance tests. State hashes are sanity information, not scientific validation.")
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", nargs="?", type=Path, help="Omit to summarize one run and its MPI scaling")
    parser.add_argument("--allow-mismatch", action="store_true")
    parser.add_argument("--output", type=Path, help="Write a new JSON comparison file")
    args = parser.parse_args()
    baseline = load(args.baseline)
    if args.candidate is None:
        if args.output:
            parser.error("--output requires two runs")
        summary(baseline)
    else:
        rows = compare(baseline, load(args.candidate), args.allow_mismatch)
        if args.output:
            with args.output.open("x") as stream:
                json.dump(rows, stream, indent=2, allow_nan=False)
                stream.write("\n")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError) as error:
        sys.exit(str(error))
