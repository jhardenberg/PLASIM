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
    status = report.get("status")
    if report.get("schema_version") != 1 or status not in ("complete", "partial", "failed"):
        raise ValueError(f"Only schema-1 benchmark results can be compared: {path}")
    if not report.get("cases"):
        raise ValueError("No benchmark cases")
    complete_cases = 0
    for case in report["cases"]:
        times = measured(case)
        if not all(t > 0 and math.isfinite(t) for t in times):
            raise ValueError(f"Missing/invalid measured samples: {case['name']}")
        if times:
            complete_cases += 1
        elif status == "complete" and case.get("status", "complete") == "complete":
            raise ValueError(f"Missing/invalid measured samples: {case['name']}")
    if not complete_cases:
        raise ValueError(f"No completed measured samples in {path}")
    return report


def measured(case: dict) -> list[float]:
    return [sample["wall_seconds"] for sample in case["samples"] if not sample["warmup"]]


def median(case: dict) -> float:
    return statistics.median(measured(case))


def report_incomplete(report: dict, label: str):
    status = report.get("status", "complete")
    skipped = [case["name"] for case in report["cases"] if not measured(case)]
    expected = report.get("settings", {}).get("repeats")
    partial = [f"{case['name']} ({len(measured(case))}/{expected})"
               for case in report["cases"]
               if measured(case) and (
                   (expected is not None and len(measured(case)) < expected) or
                   case.get("status") == "failed")]
    if status != "complete" or skipped or partial:
        detail = f" ({report['error']})" if report.get("error") else ""
        print(f"{label} status is {status}{detail}.")
        if skipped:
            print(f"  Skipping cases without measured samples: {', '.join(skipped)}")
        if partial:
            print(f"  Cases with partial measured samples: {', '.join(partial)}")

def format_compiler_info(report: dict) -> list[str]:
    """Format compiler paths and options recorded in a benchmark report."""
    tools = report.get("environment", {}).get("tools", {})
    settings = report.get("settings", {})
    cases = report.get("cases", [])
    has_serial = any(case.get("ranks", 1) == 1 for case in cases) if cases else True
    has_mpi = any(case.get("ranks", 1) > 1 for case in cases) if cases else False

    lines = []
    fc_info = tools.get("fc", {})
    fc_cmd = fc_info.get("path") or fc_info.get("version")
    fflags = settings.get("fflags")
    prec = settings.get("precision_flags")

    mpifc_info = tools.get("mpifc", {})
    mpifc_cmd = mpifc_info.get("path") or mpifc_info.get("version")
    mpifflags = settings.get("mpifflags") or fflags

    cc_info = tools.get("cc", {})
    cc_cmd = cc_info.get("path") or cc_info.get("version")
    cflags = settings.get("cflags")

    def combine_opts(flags: str | None, precision: str | None) -> str:
        parts = []
        if flags:
            parts.append(flags)
        if precision and precision not in (flags or ""):
            parts.append(precision)
        return " ".join(parts)

    # Serial Fortran
    if (fc_cmd or fflags) and (has_serial or not has_mpi or "fc" in tools):
        opts = combine_opts(fflags, prec)
        opts_str = f" ({opts})" if opts else ""
        if fc_cmd:
            lines.append(f"Fortran: {fc_cmd}{opts_str}")
        elif opts:
            lines.append(f"Fortran options: {opts}")

    # MPI Fortran
    if (mpifc_cmd or settings.get("mpifflags")) and (has_mpi or "mpifc" in tools):
        opts = combine_opts(mpifflags, prec)
        opts_str = f" ({opts})" if opts else ""
        if mpifc_cmd:
            lines.append(f"MPI Fortran: {mpifc_cmd}{opts_str}")
        elif opts:
            lines.append(f"MPI Fortran options: {opts}")

    # C compiler
    if cc_cmd or cflags:
        opts_str = f" ({cflags})" if cflags else ""
        if cc_cmd:
            lines.append(f"C compiler: {cc_cmd}{opts_str}")
        elif cflags:
            lines.append(f"C options: {cflags}")

    return lines


def summary_conditions(reference: dict, candidate: dict) -> list[str]:
    """Conditions shared by serial/MPI reports, allowing their different tools."""
    differences = []
    if reference["suite_sha256"] != candidate["suite_sha256"]:
        differences.append("benchmark runner SHA-256")
    if reference["source"]["model_sha256"] != candidate["source"]["model_sha256"]:
        differences.append("model-source SHA-256")
    for setting in ("days", "warmups", "coupling_days", "io", "timers",
                    "fflags", "cflags", "precision_flags"):
        if reference["settings"][setting] != candidate["settings"][setting]:
            differences.append(f"setting {setting}")
    if "mpifflags" in reference["settings"] or "mpifflags" in candidate["settings"]:
        ref_mpifflags = reference["settings"].get("mpifflags", reference["settings"].get("fflags"))
        cand_mpifflags = candidate["settings"].get("mpifflags", candidate["settings"].get("fflags"))
        if ref_mpifflags != cand_mpifflags:
            differences.append("setting mpifflags")
    before, after = reference["environment"], candidate["environment"]
    for setting in ("machine", "thread_environment", "runtime_environment", "workspace_storage"):
        if before.get(setting) != after.get(setting):
            differences.append(f"environment {setting}")
    for tool in ("make", "cc"):
        if before["tools"][tool] != after["tools"][tool]:
            differences.append(f"tool {tool}")
    # A serial report records fc; an MPI-only report records mpifc instead.
    # Wrappers have different paths, but must expose the same Fortran version.
    def versions(env):
        return {value["version"] for key, value in env["tools"].items()
                if key in ("fc", "mpifc")}
    if versions(before) != versions(after):
        differences.append("Fortran compiler version")
    if "mpifc" in before["tools"] and "mpifc" in after["tools"]:
        if (before["tools"]["mpifc"] != after["tools"]["mpifc"] or
                before["tools"]["launcher"] != after["tools"]["launcher"] or
                before["launcher"] != after["launcher"]):
            differences.append("MPI compiler/launcher")
    return differences


def summarize(reports: list[dict], allow_mismatch: bool = False) -> list[dict]:
    cases, origins, inputs = {}, {}, {}
    differences = []
    for index, report in enumerate(reports):
        report_incomplete(report, f"Report {index+1}")
    if len(reports) == 1:
        for line in format_compiler_info(reports[0]):
            print(line)
    else:
        for index, report in enumerate(reports, 1):
            info_lines = format_compiler_info(report)
            if info_lines:
                print(f"Report {index} compiler:")
                for line in info_lines:
                    print(f"  {line}")
    for index, report in enumerate(reports):
        if index:
            differences.extend(f"report {index+1}: {item}"
                               for item in summary_conditions(reports[0], report))
        for case in report["cases"]:
            if not measured(case):
                continue
            key = (case["resolution"], case["case"], case["ranks"])
            if key in cases:
                raise ValueError(f"Duplicate resolution/configuration/rank case: {case['name']}. "
                                 "Choose one report per case; samples are not pooled.")
            group = key[:2]
            if group in inputs and inputs[group] != case["input_sha256"]:
                differences.append(f"runtime inputs for {group[0]}-{group[1]}")
            inputs[group] = case["input_sha256"]
            cases[key], origins[key] = case, index
    if not cases:
        raise ValueError("No completed measured benchmark cases")
    mpi_reports = [(index, report) for index, report in enumerate(reports)
                   if "mpifc" in report["environment"].get("tools", {})]
    if mpi_reports:
        for index, report in mpi_reports[1:]:
            differences.extend(f"report {index+1}: {item}"
                               for item in summary_conditions(mpi_reports[0][1], report))
    differences = list(dict.fromkeys(differences))
    if differences:
        details = "\n".join("- " + difference for difference in differences)
        if not allow_mismatch:
            raise ValueError("Incompatible summary conditions:\n" + details +
                             "\nUse --allow-mismatch for an intentional descriptive comparison.")
        print("WARNING: configuration differences explicitly allowed; scaling ratios are descriptive:\n" + details)
    if any(report["settings"].get("parallel", False) for report in reports):
        print("WARNING: concurrent benchmark cases may affect timings through shared CPU/memory/I/O. "
              "Reported speedup and efficiency include these effects and are not isolated MPI scaling measurements.")
    print("Case                         n   Median(s)    Min–max(s)         Speedup/p1  Efficiency")
    rows = []
    for key in sorted(cases):
        case, index = cases[key], origins[key]
        values = measured(case)
        serial_key = (*key[:2], 1)
        serial = cases.get(serial_key)
        serial_report = reports[origins[serial_key]] if serial else None
        speedup = median(serial)/median(case) if serial is not None else None
        efficiency = 100*speedup/key[2] if speedup is not None else None
        scaling = f"{speedup:10.3f}x  {efficiency:8.1f}%" if speedup is not None else "        n/a        n/a"
        print(f"{case['name']:28} {len(values):2} {median(case):10.3f} "
              f"{min(values):8.3f}–{max(values):8.3f} {scaling}")
        rows.append({"name": case["name"], "resolution": key[0], "case": key[1], "ranks": key[2],
                     "source_report": index+1, "measured_samples": len(values),
                     "median_wall_seconds": median(case), "min_wall_seconds": min(values),
                     "max_wall_seconds": max(values), "speedup": speedup,
                     "efficiency_percent": efficiency, "configuration_differences": differences,
                     "concurrent_run": bool(reports[index]["settings"].get("parallel", False)),
                     "concurrent_serial_baseline": bool(serial_report and
                                                        serial_report["settings"].get("parallel", False))})
    print("Scaling includes launch and initialization costs; independently collected runs can differ in machine load.")
    return rows


def summary(report: dict):
    return summarize([report])


def compare(baseline: dict, candidate: dict, allow_mismatch: bool) -> list[dict]:
    report_incomplete(baseline, "Baseline report")
    report_incomplete(candidate, "Candidate report")
    base_info = format_compiler_info(baseline)
    cand_info = format_compiler_info(candidate)
    if base_info and base_info == cand_info:
        print("Compiler:")
        for line in base_info:
            print(f"  {line}")
    else:
        if base_info:
            print("Baseline compiler:")
            for line in base_info:
                print(f"  {line}")
        if cand_info:
            print("Candidate compiler:")
            for line in cand_info:
                print(f"  {line}")
    differences = []
    if baseline["suite_sha256"] != candidate["suite_sha256"]:
        differences.append("benchmark runner SHA-256")
    if baseline["environment"] != candidate["environment"]:
        differences.append("machine/toolchain/launcher/thread environment")
    for setting in ("days", "warmups", "coupling_days", "io", "timers",
                    "fflags", "cflags", "precision_flags"):
        if baseline["settings"][setting] != candidate["settings"][setting]:
            differences.append(f"setting {setting}: {baseline['settings'][setting]!r} vs {candidate['settings'][setting]!r}")
    if "mpifflags" in baseline["settings"] or "mpifflags" in candidate["settings"]:
        base_mpifflags = baseline["settings"].get("mpifflags", baseline["settings"].get("fflags"))
        cand_mpifflags = candidate["settings"].get("mpifflags", candidate["settings"].get("fflags"))
        if base_mpifflags != cand_mpifflags:
            differences.append(f"setting mpifflags: {base_mpifflags!r} vs {cand_mpifflags!r}")
    for setting, default in (("parallel", False), ("max_cores", None)):
        if baseline["settings"].get(setting, default) != candidate["settings"].get(setting, default):
            differences.append(f"scheduling setting {setting}")
    if baseline["settings"].get("parallel") or candidate["settings"].get("parallel"):
        # Other workloads/repetitions determine contention even for matched cases.
        if ([case["name"] for case in baseline["cases"]] !=
                [case["name"] for case in candidate["cases"]] or
                baseline["settings"]["repeats"] != candidate["settings"]["repeats"]):
            differences.append("parallel workload matrix/order or repetition count")
        print("Concurrent timings include shared-resource contention; ratios do not isolate code speedups.")
    reference = {case["name"]: case for case in baseline["cases"] if measured(case)}
    proposed = {case["name"]: case for case in candidate["cases"] if measured(case)}
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
    parser.add_argument("inputs", nargs="+", type=Path, help="Result files or directories")
    parser.add_argument("--summary", action="store_true",
                        help="Summarize cases across one or more files, including serial/MPI scaling")
    parser.add_argument("--allow-mismatch", action="store_true")
    parser.add_argument("--output", type=Path, help="Write a new JSON summary or comparison file")
    args = parser.parse_args()
    if not args.summary and len(args.inputs) > 2:
        parser.error("use --summary to combine more than two result files")
    reports = [load(path) for path in args.inputs]
    measured_names = [{case["name"] for case in report["cases"] if measured(case)}
                      for report in reports]
    measured_ranks = [{case["ranks"] for case in report["cases"] if measured(case)}
                      for report in reports]
    split_ranks = (len(reports) == 2 and not (measured_names[0] & measured_names[1]) and
                   measured_ranks[0].isdisjoint(measured_ranks[1]))
    if args.summary or len(reports) == 1 or split_ranks:
        for index, path in enumerate(args.inputs, 1):
            print(f"Report {index}: {path}")
        rows = summarize(reports, args.allow_mismatch)
        output = {"kind": "benchmark_summary", "reports": [str(path) for path in args.inputs],
                  "cases": rows}
    else:
        output = compare(reports[0], reports[1], args.allow_mismatch)
    if args.output:
        with args.output.open("x") as stream:
            json.dump(output, stream, indent=2, allow_nan=False)
            stream.write("\n")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError) as error:
        sys.exit(str(error))
