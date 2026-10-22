# Tests and scientific validation

Run the regression suite from the repository root:

```sh
python3 tests/run_tests.py -v
```

or with the standard single-process discovery command:

```sh
python3 -m unittest discover -s tests -v
```

It requires Python 3, `gfortran`, `cc`, and Make. MPI cases additionally
need matching `mpif90` and `mpiexec`; locally they are skipped if those
programs are absent. The suite builds in temporary directories using the
existing Makefile and checked-in runtime inputs.

## What is covered

| Area | Current checks |
| --- | --- |
| Calendars | Gregorian/simplified dates, leap-century rules, subdaily conversion, perpetual days, and monthly interpolation; single/double precision with bounds checks. |
| Serial Earth | T21/L10 short-run numerical baselines, finite selected state fields, current fixed-orbit reference values, and selected input compatibility. |
| Restarts | Continuous versus split short runs, classic/spectral modes, selected older restart continuation, and orbital-epoch selection across a year boundary. |
| Cloud diagnostics | State invariance when diagnostics are enabled and nonempty finite clear-sky flux output. |
| Real LSG | Actual ocean advancement with daily coupling, ocean state, bidirectional exchange, and atmosphere/ocean restart consistency. |
| MPI | Two-rank mixed-layer/LSG comparisons including runoff, restart layout, spectral fractions, and selected nondefault broadcasts. |

See {download}`tests/README.md <../../tests/README.md>` for precise
configurations, tolerances, limitations, and commands to select subsets.
That file remains the detailed testing reference, not a second independent
set of numerical expectations.

For repeated performance measurements and serial/MPI comparisons, use
{doc}`benchmarking`. The standalone benchmark suite records timings and
execution checks separately from these regression tests.

The current Earth fixture uses year 2000, a fixed orbit, and a 360-day
calendar; its metadata records the source commit, compiler, flags, and
checksum. The older year-1/Berger fixture remains a legacy input. Do not
compare differently forced experiments and interpret the difference as a
restart-format failure.

## Interpret results appropriately

Byte equality is meaningful for certain continuous/restarted cases within
the same build. Serial/MPI or cross-platform comparisons can need bounded
numerical error because reductions have different summation order. Keep
physical bounds as well as magnitude/RMS checks for bounded fractions.
Do not weaken tolerances or regenerate fixtures to accommodate an
unexplained change.

A two-day run does not establish climate equilibrium, ocean spin-up,
long-term statistics, scaling, or correctness at every resolution/core count.
The coupled tests shorten the exchange interval so the ocean actually
advances; merely completing two atmospheric days at a ten-day coupling
interval would not cover the same behavior.

## CI and documentation checks

The model workflow runs on default-branch pushes, manual dispatch, and PRs
carrying the exact `run tests` label. Inspect the actual result before
reporting that CI passed. The documentation workflow separately checks
source-inventory drift, strict HTML/LaTeX-source builds, and the unchanged
direct-Make example. It does not run the scientific Reference Manual or
publish a site.

Documentation-only edits need the applicable build/link/example checks;
model/coupling/build/test-harness changes require the broader suite under
`AGENTS.md`. Keep bug fixes discovered during documentation in separately
scoped issues and later PRs.

Sources checked: current `tests/test_model.py`, `tests/test_lsg.py`,
`tests/test_mpi.py`, `tests/calendar_test.f90`, fixture metadata, and the
two GitHub Actions workflows.
