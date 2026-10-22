# Performance benchmarking

Use the standalone suite in `benchmarks` to measure the effect of a code
change or to explore serial/MPI performance. It records repeated timings
and the conditions under which they were collected. Benchmark workloads
run separately from regression tests and CI, with no pass/fail speed
threshold. For numerical correctness checks, see {doc}`testing`.

This chapter follows the {download}`benchmark guide
<../../benchmarks/README.md>`, checked against `benchmarks/run.py` and
`benchmarks/compare.py`. The guide retains the full protocol and additional
examples; both commands also provide `--help`.

## Requirements and workloads

Use Python 3.9 or newer, GNU Fortran (`gfortran`), a C compiler (`cc`), and
Make on Linux or macOS. MPI cases additionally need compatible `mpif90` and
`mpiexec`. The suite uses the Python standard library; no GUI, CDO, NetCDF,
or extra Python packages are required.

The default matrix has four serial cases: each configuration below runs
at both T21/L10 and T42/L10. Each additional MPI rank count runs the same
four configurations. T31/L10 (96 × 48 grid points) can also be selected with
`--resolutions T31`, or combined with the others using
`--resolutions T21 T31 T42`. The default remains T21/T42.

| Case | Radiation | Ocean |
| --- | --- | --- |
| `mixed` | Classic broadband | Mixed layer |
| `lsg` | Classic broadband | Real coupled LSG |

Only `mixed` and `lsg` are accepted by `--cases`; all new benchmarks use
classic broadband radiation (`nstartemp=0`). The model's spectral-radiation
capability remains available for ordinary experiments.

The benchmark protocol prescribes Earth, ten atmospheric levels, a 360-day
year starting on 1 January of year 1, `seed=1`, `kick=0`, and disabled
cloud-forcing diagnostics. T21 uses 32 atmospheric steps/day, T31 uses 48,
and T42 uses 72 (45/30/20 minutes, matching MoSt and the model defaults). The runner writes `NTSPD`
explicitly to keep these timings across source revisions. Historical
40-step T31 and 48-step T42 results are different workloads; use a new
results directory and retain source/input compatibility checks. Other physics settings inherit source defaults. Default
compilation uses `-O3 -fdefault-real-8` for Fortran and `-O3` for C, without adding
fast-math or native-architecture flags.

Each resolution uses its checked-in atmospheric boundary data. Coupled
cases use the real LSG implementation and coupling inputs. T21 takes the
LSG-supplied land mask; T31 and T42 retain their native atmospheric masks
because no replacement for them is supplied in `lsg/dat`. The LSG grid stays
at 72 × 76 points with 22 levels. These workloads do not establish a scientifically
validated coupled climate at any resolution.

## Start with a small run

The following optional smoke example builds serial T21 mixed-layer and
LSG cases, runs each for ten days once, and prints a summary. It retains
results in a fresh temporary directory and reports its location. It can
be launched from the repository root:

```sh
bash docs/examples/benchmark-smoke.sh
```

```{literalinclude} ../examples/benchmark-smoke.sh
:language: bash
```

To run the same smoke check at T31, including both ocean configurations:

```sh
bash docs/examples/benchmark-smoke.sh T31
```

This checks that the workflow executes, including one LSG step at the
default coupling interval. One short sample cannot establish a speed
improvement. Warm-ups, when enabled, start from fresh inputs just like
measured samples: they condition caches, not the simulated climate, and
their restart state is not reused.

For the full default benchmark and a summary, run from the repository root:

```sh
python3 benchmarks/run.py --output benchmarks/results/baseline
python3 benchmarks/compare.py benchmarks/results/baseline
```

The defaults are 120 simulated days, five measured repetitions, and zero
warm-ups **per case**. Request excluded preliminary runs with `--warmups N`;
each lasts the full `--days` duration and is recorded but excluded from
summary statistics. The full matrix can take hours, especially at T42.
Select a smaller matrix when investigating a particular component.

| Option | Default | Effect |
| --- | --- | --- |
| `--resolutions` | `T21 T42` | Select any combination of T21, T31, and T42. |
| `--cases` | `mixed lsg` | Select one or both ocean configurations; radiation is classic broadband. |
| `--ranks` | `1` | Serial for 1; real MPI for larger counts. Each count must be a power of two dividing every selected latitude count (32 for T21, 48 for T31, 64 for T42); T31 allows at most 16 ranks. |
| `--days` | `120` | Positive simulated days; LSG runs require an integer number of coupling intervals. |
| `--repeats`, `--warmups` | `5`, `0` | Positive measured count and nonnegative excluded count. |
| `--coupling-days` | `10` | LSG exchange interval; choices are 1 or 10 days. |
| `--io` | `minimal` | Suppress regular Service output, or select `daily` output. |
| `--fc`, `--mpifc`, `--cc` | `gfortran`, `mpif90`, `cc` | Compiler executables; precision is fixed separately by the runner. |
| `--fflags`, `--cflags` | `-O3`, `-O3` | Optimization flags; use, for example, `--fflags='-O2'`. |
| `--launcher` | `mpiexec` | Quoted MPI launch command/options, before the runner's `-n` argument. |
| `--no-timers` | Timers enabled | Disable model component timing consistently across compared runs. |
| `--parallel`, `--max-cores` | Sequential; available logical CPUs | Concurrent cases and their shared rank budget; see below. |
| `--timeout` | `3600` seconds | Limit each build/run and terminate its process group on timeout. |
| `--work-dir`, `--keep-work` | System temporary directory; remove work | Select workspace parent and optionally retain binaries and run directories. |

## Compare source revisions

Use the same runner to build two existing checkouts. `--source` reads their
files, including local edits, without switching branches or modifying either
checkout. From the checkout containing the benchmark scripts:

```sh
python3 benchmarks/run.py --source /path/to/baseline-checkout \
  --output benchmarks/results/baseline-revision
python3 benchmarks/run.py --source /path/to/candidate-checkout \
  --output benchmarks/results/candidate-revision
python3 benchmarks/compare.py benchmarks/results/baseline-revision \
  benchmarks/results/candidate-revision --output benchmarks/results/comparison.json
```

Choose output names appropriate to the experiment. An existing result
directory is continued only when its recorded settings, cases, source
digest, runtime inputs, and environment match. Repeating the same run
command skips completed cases and recorded samples. An incompatible
directory, or one without `results.json`, is rejected. Exported comparison
and summary JSON files must have new filenames.

Saved result files containing the former spectral benchmark cases can still
be summarized and compared. To continue an old eight-case run, use its
original runner; start a new output directory for the current reduced matrix.
Runner-version compatibility checks still apply when combining reports.
To continue any run that used warm-ups, explicitly pass its original
`--warmups N` count.

The comparison matches resolution/configuration/rank cases and reports
unmatched or incomplete cases. It checks runner versions, runtime inputs,
compiler flags, recorded environments, storage, and timing/output policies.
Sequential runs may have different measured repetition counts; concurrent
runs also require matching workload order and repetition counts. The
`--allow-mismatch` option permits an intentional descriptive comparison,
such as different compiler flags or hardware; it cannot isolate a code-only
effect.

Speedup is `baseline median / candidate median`; percent time saved is
`100 × (1 − candidate median / baseline median)`. Inspect the sample counts
and ranges alongside those ratios. For small effects, lengthen runs,
repeat independent experiments, and alternate baseline/candidate order on
a quiet machine to expose variation from load or temperature. Ratios are
descriptive statistics, not significance tests.

## Measure MPI scaling

Include matching serial and MPI cases in one run:

```sh
python3 benchmarks/run.py --output benchmarks/results/serial-and-mpi \
  --ranks 1 2
python3 benchmarks/compare.py benchmarks/results/serial-and-mpi
```

The summary gives speedup relative to the matching serial case and
efficiency as `100 × speedup / ranks`. Timings include launch and
initialization overhead. Use the same external CPU allocation/binding and
comparable machine load. For Open MPI, for example, pass
`--launcher 'mpiexec --bind-to core'` when appropriate to the allocation.
The runner sets common OpenMP/BLAS thread counts to one; it does not pin
CPUs, change power settings, or automatically enable oversubscription.

To reuse separately collected serial results, collect only additional MPI
sizes, with matching source, inputs, timing options, and environment:

```sh
python3 benchmarks/run.py --output benchmarks/results/mpi-only \
  --ranks 2 4 8 --max-cores 8
python3 benchmarks/compare.py --summary \
  benchmarks/results/baseline benchmarks/results/mpi-only \
  --output benchmarks/results/scaling-summary.json
```

Here `baseline` must be the matching serial benchmark, not the short smoke
example. `--summary` combines reports without repeating rank 1 or pooling
raw samples; duplicate cases are rejected. Serial and MPI Fortran versions
must agree, and separate MPI reports must agree on wrapper and launcher.
Sequential core budgets and repetition counts can differ. The exported
summary records source report paths and summarized rows; it is not a raw
`results.json` input for later comparisons. JSON rows also record
`concurrent_run` and `concurrent_serial_baseline` flags.

Speedup and efficiency are shown whenever a matching serial baseline has
measured samples. Concurrent runs retain these ratios with a warning that
they include shared-resource effects. `n/a` means there is no measured
matching serial baseline. Compatibility checks remain in place; explicitly
allowing differences with `--allow-mismatch` retains descriptive ratios and
warns about those differences.

## Run independent cases concurrently

```sh
python3 benchmarks/run.py --output benchmarks/results/parallel \
  --parallel --max-cores 8 --ranks 1 2 4
```

`--max-cores` bounds the sum of active MPI ranks, counting serial cases as
one. Two four-rank cases fill an eight-slot budget. Set the limit to the
actual job allocation; its default uses Linux process affinity where
available, otherwise the logical CPU count. It is a rank budget, not CPU
pinning or a count of physical cores. Even in sequential mode, each selected
rank count must fit within it.

Builds finish before measurements begin and use one compiler process at a
time. Concurrent cases have private inputs, ocean matrices, and outputs;
each case's warm-ups and measured repeats remain sequential. Arrange CPU
binding externally so separate MPI launchers do not bind to overlapping
cores; consult the benchmark guide for launcher considerations.

Concurrent timings include competition for CPU, memory, and storage. Use
this mode to finish a matrix sooner. Use isolated sequential cases to
measure model speedups or MPI efficiency. Summaries display scaling ratios
with a warning when a case or its serial baseline ran concurrently; those
ratios describe performance under concurrent load.
Matching scheduling settings alone do not guarantee identical overlap.

To check the runner's scheduling and report-handling tests without compiling
the model:

```sh
python3 -m unittest discover -s benchmarks -p 'test_runner.py' -v
```

## Coupling, output, and timing scope

The default ten-day LSG interval is converted to the appropriate atmospheric
step count at each resolution. `--coupling-days 1` exercises more frequent
coupling and changes the ocean timestep and numerical workload. Compare
daily and ten-day configurations separately, with the same cadence on both
sides of a revision comparison. LSG advancement is checked using its
completion diagnostic, ocean restart, and newly generated `mat77` matrix.

Minimal output retains diagnostics and final restarts while suppressing
regular atmospheric and ocean Service output. Each sample starts from
fresh inputs and generates its own LSG matrix, with subsequent matrix
refresh set beyond the run horizon. With `--io daily`, atmospheric output
is daily and LSG output occurs at every ocean step, which is daily only
when coupling is daily. Keep output policy and storage location fixed.

The primary metric is monotonic wall time around the executable or MPI
launcher. It includes process launch, initialization, LSG matrix generation,
integration, diagnostics, and final restart writing. Build time, input
copying, state checks, hashing, and result serialization are excluded.

Model radiation timers measure elapsed intervals on the root rank despite
their CPU labels; the final total CPU statistic measures root-process CPU
time. Neither is aggregate MPI CPU time. Component clocks have millisecond
granularity and can be unreliable across month boundaries. Timer overhead
is part of the workload; use `--no-timers` consistently if needed. Collect
profiles separately and record any profiling flags.

## Retain and interpret results

`results.json` retains the source commit and tracked changes, source/input
hashes, namelists, compiler/environment details, scheduling policy, sample
timestamps, warm-up and measured samples, wall-time statistics, throughput,
model timers, and selected final-state summaries/hashes. The suite also
retains `samples.csv`, build logs, stdout logs, and diagnostics. Results
under `benchmarks/results` are ignored by Git; share relevant measurements
with optimization PRs. `--keep-work` retains the potentially large temporary
build and run directories for inspection.

A failed or timed-out case is recorded while remaining cases continue.
Ctrl-C stops the batch. Partial or failed reports can still be summarized
or compared when they contain measured samples; inspect the reported
omissions and counts before interpreting them. To continue, rerun the
original command with matching settings.

The runner checks atmospheric dimensions and step count, finite selected
state fields, MPI-rank diagnostics, and actual LSG advancement. Changed
selected-state hashes are reported during revision comparison. These are
execution checks, not proof of scientific equivalence. Pair performance
results with {doc}`testing` and focused physical validation of the proposed
change; a short benchmark does not establish a spun-up climate.
