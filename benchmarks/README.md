# PlaSim performance benchmarks

These standalone Python scripts measure performance changes. Benchmark workloads
are outside model regression discovery and test CI, use no pass/fail speed
thresholds, and do not import the regression harness. No model source is modified.

Use Python 3.9+, GNU Fortran (`gfortran`), a C compiler (`cc`), and `make`.
MPI runs also need `mpif90` and `mpiexec`. Linux and macOS are the initial
supported hosts. No GUI, CDO, NetCDF, or Python packages are required.

## Workloads

The default matrix includes **all eight serial T21/L10 and T42/L10 cases**:

| Case | Atmosphere radiation | Ocean |
| --- | --- | --- |
| `mixed` | Classic broadband | Mixed layer, without LSG |
| `mixed-spectral` | Spectral, stellar temperature 5778 K | Mixed layer, without LSG |
| `lsg` | Classic broadband | Real coupled LSG |
| `lsg-spectral` | Spectral, stellar temperature 5778 K | Real coupled LSG |

Both resolutions use their checked-in atmospheric boundary data. Coupled runs
also use the real `lsg/src/lsgmod.f90`, `plasim/src/cpl.f90`, and `lsg/dat`
inputs. T21 therefore uses the LSG-supplied T21 land mask, as MoSt does;
T42 uses its native T42 land mask because no T42 replacement exists in
`lsg/dat`. The LSG ocean grid remains 72 × 76 with 22 levels. These are
performance workloads, not a claim that a T42 coupled climate is scientifically
validated or that different resolutions/ocean configurations have identical
initial states.

The protocol fixes Earth, ten atmosphere levels, a 360-day year, start date
1-Jan-0001, `seed=1`, `kick=0`, and disabled cloud-forcing diagnostics. T21 has
32 atmosphere steps/day; T42 has 48. Other physics settings retain source
defaults. The LSG case uses `nlsg=1`, `nocean=1`, `nhdiff=0`, and `kiterm=8`.
Each selected MPI rank count gets its own build; `1` selects serial stubs,
while `2`, `4`, etc. select the real MPI module. Rank counts must be powers
of two dividing both selected latitude counts.

Default optimization is `-O3 -fdefault-real-8`, with `-O3` for C. No fast-math
or native-architecture flag is added. Set compiler executables and flags
explicitly to investigate those choices; they are recorded in the results.

## Run a benchmark

From the repository root:

```sh
python3 benchmarks/run.py --output benchmarks/results/baseline
```

The defaults are 120 simulated days, five measured repetitions, and one
excluded warm-up **per case**. The full matrix can take hours on a workstation,
especially at T42. Each sample starts from a fresh copy of the same inputs.
Warm-ups condition filesystem/CPU caches; they are not climate spin-up and
do not supply restart state to measured samples.

For a short functional check of the complete matrix:

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

The one-file summary prints wall-time medians, ranges, and MPI speedup and
efficiency relative to a matching serial case when present. It includes
launcher overhead and is not a pure communication or strong-scaling kernel
measurement. Use a quiet machine and document CPU allocation and binding.
For example, Open MPI launcher options can be passed as a quoted command:

```sh
python3 benchmarks/run.py --output benchmarks/results/bound-mpi \
  --ranks 2 --launcher 'mpiexec --bind-to core'
```

The script sets common OpenMP/BLAS thread counts to one. It does not select
CPU affinity, change power settings, or enable oversubscription automatically.
Use the same external allocation/binding for comparisons. Relevant OpenMP/BLAS
and MPI environment settings are recorded, alongside the workspace parent and
filesystem device. Record additional OS settings and job-scheduler allocations
with the experiment.

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
launcher/helper processes and the Python coordinator add some overhead.
Concurrent MPI launchers may bind to overlapping CPUs: use an external
allocation/launcher that partitions CPUs if disjoint binding is required.

Without `--parallel`, cases run one at a time; `--max-cores` still bounds the
selected MPI rank count. Builds use one compiler process at a time and all
finish before model runs begin, so compilation does not overlap measurements.
Each concurrent case has private inputs, outputs, and ocean matrices. Its
warmups finish before its measured repeats, and repeats remain sequential.
A failure, timeout, or Ctrl-C stops the batch and terminates active process
groups. Completed samples remain in the failed result report.

Parallel mode is useful for completing the workload matrix sooner. Its per-case
timings include CPU, memory, and I/O contention and are unsuitable for claiming
isolated model or MPI speedups. The one-file summary suppresses MPI scaling
ratios in this mode. Use sequential mode on a quiet allocated machine for
performance comparisons. Scheduling mode and core budget are recorded;
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
  --cases lsg lsg-spectral --coupling-days 1 --days 120
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
this protocol. Output directories must be new, preventing accidental overwrite.

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
  Failed/partial result files are marked and rejected by the comparison script.
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
