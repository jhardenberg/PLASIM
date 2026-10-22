# PlaSim performance benchmarks

These standalone Python scripts measure performance changes. Benchmark workloads
are outside model regression discovery and test CI, use no pass/fail speed
thresholds, and do not import the regression harness. No model source is modified.

Use Python 3.9+, GNU Fortran (`gfortran`), a C compiler (`cc`), and `make`.
MPI runs also need `mpif90` and `mpiexec`. Linux and macOS are the initial
supported hosts. No GUI, CDO, NetCDF, or Python packages are required.

## Workloads

The default matrix includes **all four serial T21/L10 and T42/L10 cases**:

| Case | Atmosphere radiation | Ocean |
| --- | --- | --- |
| `mixed` | Classic broadband | Mixed layer, without LSG |
| `lsg` | Classic broadband | Real coupled LSG |

T31/L10 (96 × 48 grid points) is also available through `--resolutions T31`.
Select any combination with `--resolutions T21 T31 T42`; omitting the option
keeps the T21/T42 default matrix. T31 supports power-of-two rank counts up
to 16 because each rank count must divide its 48 latitudes.

Each selected rank count runs the selected configurations with classic broadband
radiation (`nstartemp=0`). Only `mixed` and `lsg` are accepted by `--cases`.
Existing JSON files containing spectral results can still be summarized and
compared. Use a new output directory for the reduced matrix: continuation
requires the original case selection and runtime settings to match. The
comparison tool retains its checks of runner versions when combining old
and new result files.

All three resolutions use their checked-in atmospheric boundary data. Coupled
runs also use the real `lsg/src/lsgmod.f90`, `plasim/src/cpl.f90`, and `lsg/dat`
inputs. T21 therefore uses the LSG-supplied T21 land mask, as MoSt does;
T31 and T42 use their native atmospheric land masks because no replacement
exists for them in `lsg/dat`. The LSG ocean grid remains 72 × 76 with 22 levels. These are
performance workloads, not a claim that a T31 or T42 coupled climate is
scientifically validated or that different resolutions/ocean configurations have identical
initial states.

The protocol fixes Earth, ten atmosphere levels, a 360-day year, start date
1-Jan-0001, `seed=1`, `kick=0`, and disabled cloud-forcing diagnostics. T21 has
32 atmosphere steps/day; T31 has 48; T42 has 72 (45/30/20 minutes). Other physics settings retain
source defaults. The runner writes `NTSPD` explicitly to retain the MoSt
timesteps across source revisions, including older automatic defaults.
Historical runs at 40 T31 or 48 T42 steps/day represent different workloads;
start a new results directory. The LSG case uses `nlsg=1`, `nocean=1`, `nhdiff=0`, and `kiterm=8`.
Each selected MPI rank count gets its own build; `1` selects serial stubs,
while `2`, `4`, etc. select the real MPI module. Rank counts must be powers
of two dividing every selected latitude count.

### Compilers and optimization flags

By default, `benchmarks/run.py` probes compilers and optimization flags by
running `configure.sh` from the target `--source` in an isolated temporary
directory. This automatically adopts the compiler executables (`most_compiler`,
`most_compiler_mpi`) and production optimization flags configured for that
checkout (such as `-O3 -funroll-loops` and host architecture tuning on GNU Fortran,
or `-O3 -fp-model precise -xHost` on Intel Fortran). Model precision is fixed
to double precision (`-fdefault-real-8` for GNU Fortran, `-r8` for Intel Fortran).

Use `--no-configure` (or `--reuse-configure`) to inhibit running `configure.sh`
and reuse existing `most_compiler` and `most_compiler_mpi` files in `--source`,
falling back to default tool names (`gfortran`, `mpif90`, `cc`, `-O3`) if none
exist.

Compiler executables and optimization flags can also be overridden explicitly:
- `--fc <compiler>`: Fortran compiler for serial runs
- `--mpifc <wrapper>`: MPI Fortran wrapper for parallel runs
- `--cc <compiler>`: C compiler
- `--fflags "<flags>"`: Fortran optimization flags for serial builds
- `--mpifflags "<flags>"`: Fortran optimization flags for MPI builds (defaults to configured MPI flags or `--fflags`)
- `--cflags "<flags>"`: C optimization flags (defaults to configured C flags or `-O3`)
- `--precision-flags "<flags>"`: Fortran precision flags (defaults to auto-detected `-r8` or `-fdefault-real-8`, or pass `none` for single precision)
- `--single-precision`: Build and benchmark in single precision (`MOST_PREC=""`, default 32-bit `real`)
- `--allow-mixed-compilers`: Bypass the consistency check if serial and MPI Fortran compilers belong to different toolchains

`benchmarks/run.py` verifies that the serial Fortran compiler and MPI Fortran wrapper belong to the same compiler family (e.g. both Intel or both GNU) when parallel ranks are executed, stopping with an error if an inconsistent toolchain is detected. All compiler settings and flags are recorded in `results.json` and verified for
compatibility during comparison.

The aligned defaults change the T42 workload from 48 to 72 atmospheric
steps/day. Use a new results directory after updating; continuation and
comparison must retain their source/input compatibility checks. Historical
T42 results used a different timestep and are not matching workloads.

## Run a benchmark

From the repository root:

```sh
python3 benchmarks/run.py --output benchmarks/results/baseline
```

The defaults are 120 simulated days, five measured repetitions, and **zero
warmups** per case. The full matrix can take hours on a workstation, especially
at T42. Each sample starts from a fresh copy of the same inputs.

Use `--warmups N` to request excluded preliminary runs, for example
`--warmups 1` for one extra run before the five measured repetitions. Each
warmup lasts the full `--days` duration; its timing is recorded but excluded
from summary statistics. Warmups may condition filesystem/CPU caches; they
do not supply restart state to measured samples. To continue a result directory
created with warmups, explicitly pass its original `--warmups N` setting.

To benchmark T31 with both ocean configurations:

```sh
python3 benchmarks/run.py --output benchmarks/results/t31 --resolutions T31
```

For a short functional check of the default matrix:

```sh
python3 benchmarks/run.py --output benchmarks/results/smoke \
  --days 10 --repeats 1 --warmups 0
```

Short smoke samples verify execution; they are insufficient evidence for a
small speed improvement. Increase the simulation duration until startup
costs and timing variation are small relative to the effect being measured.

To include serial and two-rank MPI runs of both resolutions and both oceans:

```sh
python3 benchmarks/run.py --output benchmarks/results/serial-and-mpi \
  --ranks 1 2
python3 benchmarks/compare.py benchmarks/results/serial-and-mpi
```

The summary prints the recorded compiler executables and optimization/precision
flags at the top, followed by wall-time medians, ranges, and MPI speedup and
efficiency relative to a matching serial case when present. It includes
launcher overhead and is not a pure communication or strong-scaling kernel
measurement. Use a quiet machine and document CPU allocation and binding.
The default MPI launcher is `mpiexec --bind-to none`, avoiding core-binding
crashes and contention on shared nodes, SLURM allocations, or concurrent runs.
Custom launcher options or specific binding policies can be passed via `--launcher`:

```sh
python3 benchmarks/run.py --output benchmarks/results/bound-mpi \
  --ranks 2 --launcher 'mpiexec --bind-to core'
```

To deactivate `--bind-to none` and use standard `mpiexec` defaults, specify `--launcher mpiexec`.

The script sets common OpenMP/BLAS thread counts to one. It does not select
CPU affinity, change power settings, or enable oversubscription automatically.
Use the same external allocation/binding for comparisons. Relevant OpenMP/BLAS
and MPI environment settings are recorded, alongside the workspace parent and
filesystem device. Record additional OS settings and job-scheduler allocations
with the experiment.

## Combine separately collected serial and MPI results

To reuse an existing serial run, collect only the MPI sizes you need:

```sh
python3 benchmarks/run.py --output benchmarks/results/mpi-only \
  --ranks 2 4 8 --max-cores 8
python3 benchmarks/compare.py --summary \
  benchmarks/results/serial benchmarks/results/mpi-only
```

Use the same source checkout, machine, compiler, input settings (including
`--days`, coupling and output policy), warmups, and timing options as the
serial run. Omit `--parallel` for isolated MPI efficiency measurements.
The new run does not repeat rank 1. `--summary` accepts two or more result
files/directories and matches each MPI case to its serial resolution/ocean
baseline. It prints all timings and reports speedup and efficiency whenever
a matching serial baseline has measured samples. You can also collect ranks
2, 4, and 8 in separate runs and supply all their files to the same command.

The tool checks model/runner digests, runtime inputs, shared environment and
compiler settings. Serial and MPI compiler/launcher entries may differ as
expected; Fortran versions must agree, and separate MPI reports must agree
on their MPI wrapper and launcher. Different sequential core budgets and
repetition counts are allowed. Duplicate cases are rejected; samples from
repeated experiments are never silently pooled. Collect runs under the same
external CPU allocation/binding and comparable machine load.

Speedup is the serial median wall time divided by the MPI median wall time;
efficiency is speedup divided by the rank count, expressed as a percentage.
These values are displayed for concurrent cases (`--parallel`) as well. A
warning identifies possible shared-resource effects when either a case or
its serial baseline used concurrency. Ratios from those runs describe scaling
under concurrent load. `n/a` means there is no measured matching serial baseline.
For other incompatible conditions, `--allow-mismatch` explicitly permits a
descriptive summary, including scaling ratios, and warns about the differences.

To retain the combined table as a new JSON file:

```sh
python3 benchmarks/compare.py --summary \
  benchmarks/results/serial benchmarks/results/mpi-only \
  --output benchmarks/results/scaling-summary.json
```

This exports summary rows, their originating report paths, and per-row
`concurrent_run`/`concurrent_serial_baseline` flags; original raw
samples and metadata remain in their existing result files. The exported
summary is not a raw `results.json` input. Two inputs **without** `--summary`
perform the before/after source-revision comparison when they share rank
counts, or automatically summarize when their rank sets are disjoint (such as
a serial report and an MPI-only report).

## Parallel execution and core limit

Run independent benchmark cases concurrently with a maximum of eight CPU slots:

```sh
python3 benchmarks/run.py --output benchmarks/results/parallel \
  --parallel --max-cores 8 --ranks 1 2 4
```

`--max-cores N` limits the **sum of MPI ranks in active runs**, counting a
serial run as one. For example, two four-rank cases fill an eight-slot budget.
A selected rank count larger than the limit is rejected before building.
The default limit is the number of logical CPUs available through Linux
process affinity, or the machine's logical CPU count on other hosts.
Set it explicitly to match your job allocation, particularly in containers
or schedulers where CPU quotas are not reflected in process affinity.
This is a process/rank budget, not CPU pinning or a limit on physical cores;
Concurrent MPI launchers may bind to overlapping CPUs: by default,
`benchmarks/run.py` invokes `mpiexec --bind-to none` to prevent core-binding
conflicts and aborts when multiple MPI jobs or restricted affinity masks are present.
If dedicated core binding is desired on an isolated machine, specify
`--launcher 'mpiexec --bind-to core'`.

Without `--parallel`, cases run one at a time; `--max-cores` still bounds the
selected MPI rank count. Builds use one compiler process at a time and all
finish before model runs begin, so compilation does not overlap measurements.
Each concurrent case has private inputs, outputs, and ocean matrices. Its
warmups finish before its measured repeats, and repeats remain sequential.
If a build or case fails or times out, its process group is terminated, the
failure is recorded on that case, and the remaining cases continue to
completion; Ctrl-C stops the entire batch immediately. Completed samples and
`samples.csv` remain in the partial/failed result report.

Parallel mode is useful for completing the workload matrix sooner. Its per-case
timings include CPU, memory, and I/O contention and are unsuitable for claiming
isolated model or MPI speedups. Summaries display scaling ratios with a
concurrency warning in this mode. Use sequential mode on a quiet allocated
machine for isolated performance comparisons. Scheduling mode and core budget
are recorded;
comparisons reject different policies/budgets and, in parallel mode, different
workload matrices/order or repetition counts unless `--allow-mismatch` is set.
Even matching parallel settings do not guarantee identical overlap between runs.

To check the scheduler itself without compiling the model:

```sh
python3 -m unittest discover -s benchmarks -p 'test_runner.py' -v
```

## Coupling frequency and output

The default LSG coupling interval is **ten days**, expressed with the correct
atmosphere timestep count for each resolution. A run must contain a positive
integer number of coupling intervals. The runner verifies actual LSG advance
from its completion diagnostic and requires an ocean restart and new `mat77`.
`kleiswi` contains a restart unit and mode, not a timestep counter.

For a coupling-heavy investigation:

```sh
python3 benchmarks/run.py --output benchmarks/results/daily-coupling \
  --cases lsg --coupling-days 1 --days 120
```

Daily coupling changes the numerical workload and ocean timestep. Compare
baseline and candidate at the same cadence; report ten-day and daily results
separately. Daily coupling is useful for exposing overhead, and does not
represent a speedup of the production ten-day configuration.

`--io minimal` (default) suppresses regular atmosphere/ocean Service output;
diagnostics and final restarts remain. LSG matrix refresh is set beyond the
run horizon. Each sample builds its own matrix from fresh inputs: matrices
and restarts are never borrowed from another sample or revision. This avoids
accidental reuse of a stale `mat77` (see issue [#40](https://github.com/jhardenberg/PLASIM/issues/40)).
`--io daily` enables daily atmosphere output and output at every LSG step
(daily only with daily coupling). Keep the output policy and storage location
identical between comparisons.

## Compare source revisions

Use the same benchmark scripts to build two existing source checkouts:

```sh
python3 benchmarks/run.py --source /path/to/baseline-checkout \
  --output benchmarks/results/baseline
python3 benchmarks/run.py --source /path/to/candidate-checkout \
  --output benchmarks/results/candidate
python3 benchmarks/compare.py benchmarks/results/baseline \
  benchmarks/results/candidate --output benchmarks/results/comparison.json
```

`--source` builds that checkout's files, including local edits. It does not
switch Git branches or change either checkout. Commit identifiers, tracked
status, model-source digests, and actual runtime-input digests are recorded.
The two checkouts need the same input layout and namelist options used by
this protocol. An existing output directory is continued only if it contains a
compatible `results.json` with identical settings, case selection, source,
inputs, and environment; otherwise it is rejected to prevent accidental overwrite.

The comparison requires compatible runner versions, recorded environments,
compiler flags, workspace storage, timing/output settings, and runtime inputs. It compares only
matching resolution/configuration/rank cases and identifies omitted cases.
Different repetition counts are allowed and reported for sequential runs. `--allow-mismatch`
explicitly permits a descriptive comparison when changing build flags or
hardware intentionally; such a result cannot isolate a code-only effect.

Speedup is `baseline median / candidate median`; time saved is
`100 * (1 - candidate median / baseline median)`. Sample ranges and counts
are reported. These are descriptive statistics, not significance tests.
For small effects, run longer, repeat independent experiments, and alternate
baseline/candidate execution order to expose thermal/load drift. A faster
component may have negligible whole-model impact.

## What is timed and retained

- **Wall time:** monotonic elapsed time around the executable or MPI launcher,
  including process launch, initialization, LSG matrix generation, integration,
  diagnostics, and final restart writing. Build time, input copying, state
  checks, hashing, and result serialization are excluded.
- **Model timers:** `ntime=1` is enabled by default. Radiation timers call
  `mksecond`/`date_and_time`: despite the model's CPU label they measure elapsed
  intervals on the root rank. The separate final total CPU statistic is root
  process CPU time. Neither is aggregate MPI CPU time. Timer instrumentation
  adds overhead; use `--no-timers` consistently if that overhead matters.
  Calendar-clock component timers have millisecond granularity and can be
  unreliable across a month boundary; the external monotonic wall timer is
  the primary metric.
- **Results:** `results.json` records metadata, namelists, input/source hashes,
  scheduling policy/core budget, sample start/end timestamps,
  all warm-up/measured samples, wall-time median/min/max/standard deviation/MAD,
  throughput, component timers, and selected final-state summaries/hashes.
  `samples.csv`, build logs, stdout logs, and model diagnostic logs are retained.
  Re-running `benchmarks/run.py` on an output directory with an existing
  `results.json` continues the run if all settings match, skipping completed
  cases and already recorded samples. Partial or failed result files are marked
  and can still be summarized or compared for any cases that completed measured
  samples, while reporting skipped or partial cases.
- **Sanity checks:** expected grid dimensions and atmosphere step count,
  finite selected state fields, actual MPI rank diagnostics, and LSG completion
  are required. Changed selected-state hashes are shown during comparison.
  These checks and summaries do **not** establish scientific equivalence;
  use the regression suite and focused physical validation for code changes.

Builds/runs use a temporary workspace outside the checkout by default. `--work-dir /path/to/scratch` selects its parent. `--keep-work`
retains binaries, templates, and every run for inspection/profiling; the path
is in `results.json`. Profiles should be collected separately from the
uninstrumented performance comparison, and any added profiling flags reported.
Run directories can be large. `--timeout` bounds each build/run and terminates
its process group on timeout or interruption. Results under `benchmarks/results`
are ignored by Git; retain/share relevant measurements with optimization PRs.

The default workloads deliberately include initialization costs. For future
steady-integration-only or kernel measurements, add a separately named
protocol with explicit state/geometry setup rather than silently changing
these measurements.

## Related investigations

- [Radiation performance (#46)](https://github.com/jhardenberg/PLASIM/issues/46)
- [Coupler interpolation geometry (#47)](https://github.com/jhardenberg/PLASIM/issues/47)
