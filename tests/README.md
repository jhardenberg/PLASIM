# PlaSim tests

Run from the repository root:

```sh
python3 -m unittest discover -s tests -v
```

GitHub Actions runs this command on pushes to `master` or `main`. It can also
be started manually from the Actions tab once the workflow is on the default
branch. On pull requests targeting either branch, add the exact `run tests`
label to start a run; later commits rerun the tests while the label remains.

The tests need Python 3, `gfortran`, `cc`, and `make`. MPI tests additionally
need `mpif90` and `mpiexec` from Open MPI or a compatible MPI installation;
those tests are skipped locally if either tool is absent. CI installs and
checks Open MPI. The suite builds headless serial and two-rank MPI T21/L10
binaries with and without LSG in temporary directories using the repository's
existing `make_plasim` build rules. No generated files are written into the
checkout.

The suite checks the Gregorian and 360 day calendar, a deterministic two day
T21 run with broad numerical baselines, and byte equality between continuous
two day runs and runs restarted after one day in broadband and spectral modes.
It also checks every value in selected Earth state fields against a one-day
reference for the year-2000, fixed-orbit defaults, resumes the older year-1
Berger-orbit restart, and checks non-default `albsmin` and `zumin` namelist options.
The default reference test omits both `N_START_YEAR` and `NFIXORB` to verify
the Fortran defaults independently of MoSt.
Orbital tests cross December–January in both the 360-day and Gregorian
calendars with `NFIXORB=0`. They check that a restart uses the restored year
even when `N_START_YEAR` is unchanged, matches a fresh run's orbital elements
for that year, and still respects an explicit `IYRBP` override. They also
record the current initialization-only limitation in a continuous run and
check prescribed `NFIXORB=1` elements at different start years.
The year-boundary test runs only six timesteps per calendar. It creates a
temporary restart from a one-step January run, shifts only its `nstep` clock
to one timestep before January 1, and compares a continuous two-step crossing
with two one-step invocations. This checks date selection and orbital
initialization, not the physical evolution of the artificial checkpoint;
ordinary restart-state equality is covered separately above. No saved
reference fixture is modified.
The fixed random seed is needed for the restart comparisons. These tests
exercise the serial model; additional MPI coverage is described below. T42
tests remain separate follow-up work.

Two additional two-day serial runs enable cloud radiative diagnostics
(`ndiagcf=1`), one with classic radiation and one with spectral radiation.
Every restart record must match the corresponding diagnostic-off run byte
for byte within the same build. The tests also read the seven clear-sky
flux diagnostics (Service codes 101–107) and require finite values and
nonzero output for each code, so disabling diagnostic output cannot satisfy
the state-invariance check.

Conversion tests verify parameter table uniqueness and code mappings in
`scripts/srv2nc` (including meridional pressure gradient `dpdy` under code 274
and mixed-layer vertical/horizontal diffusion heat-flux codes 904/905 in W/m²),
and perform synthetic NetCDF conversion checks when CDO is installed.

The current numerical baselines come from source commit `d4802a1`, built
with `gfortran -O0 -fdefault-real-8` and the new default date and orbit mode.
They are intentionally tolerant of small compiler and platform differences.
A passing test supports short-run regression checking, not scientific
validation of a long climate simulation.

## Earth reference data

[`earth_t21_l10_day1_2000_fixed.restart.gz`](fixtures/earth_t21_l10_day1_2000_fixed.restart.gz)
is the current one-day T21/L10 Earth reference, generated from source commit
`d4802a1d1dfcac38cd8773bdf3723c94d50f968f` with Homebrew GNU Fortran 15.2.0,
`-O0 -fdefault-real-8`, the 360-day calendar, `kick=0`, `ngui=0`, and `seed=1`.
`N_START_YEAR` and `NFIXORB` are omitted, selecting the new defaults 2000 and
1. It was generated using `build_model`, `prepare_run(..., days=1)`, and
`run_model` from `test_model.py`; the compressed payload is `plasim_status`.
Its uncompressed SHA-256 is
`dbc5d5203168b0a9952de7984cd63c605cb8b74ceaf3b2be79054b2afa9c9345`.

This reference was intentionally updated because changing the default orbit
changes the forcing, while changing the default year changes output dates
and timestep values. The saved
[metadata](fixtures/earth_t21_l10_day1_2000_fixed.metadata.json) records the
old and new means and maximum absolute differences for all nine compared
fields, plus the updated two-day atmosphere and LSG baseline means. For
example, the one-day stored `dt` mean changes from 278.6540404 to
278.6623857 K, with a largest elementwise change of 1.1260302 K; these are
short-run state comparisons, not climate statistics. The strict state test
keeps its original absolute and relative tolerances of `1e-6`; broad
regression tolerances are also unchanged.

[`earth_t21_l10_day1_360.restart.gz`](fixtures/earth_t21_l10_day1_360.restart.gz)
is retained as an older restart input, from unmodified source commit
`88e68db5302d1db3c0ad636444eadda833738d52`, using the same T21/L10 headless
build, 360-day calendar, fixed seed, and compiler/flags described above. Its
uncompressed SHA-256 remains
`6b851dcb07544493620992e82ce6af4fab573fdccaa6af94f102788665dac42c`.
The legacy-restart test explicitly sets `N_START_YEAR=1` and `NFIXORB=0`,
loads this older file, and compares continuation with a cold-start run using
those same older settings. This checks restart compatibility without
requiring the new defaults to reproduce a differently configured experiment.

The MoSt-generated 365-day setup is not covered by the strict state
comparison. Legacy restarts without spectral albedo records can be continued
in broadband radiation mode; spectral radiation requires those records.
The planet branch reads `psurf` from `planet_namelist`
and no longer accepts `sidereal_year` or `tropical_year`; those older input
locations and options are not covered by these tests.

## Coupled PlaSim and LSG tests

[`test_lsg.py`](test_lsg.py) builds the actual `lsg/src/lsgmod.f90` and
`plasim/src/cpl.f90`, rather than the stubs used by the atmosphere tests.
It uses the checked-in `lsg/dat` inputs and restart, including the coupled
land mask, on LSG's 72 × 76 grid with 22 ocean levels. The atmosphere uses
T21/L10, the 360-day calendar, the year-2000 fixed-orbit defaults, and
`nlsg=1` (atmospheric SST forcing and ocean heat-flux feedback).

The coupling interval is one day (`naomod=32`), instead of the production
default of ten days, so a two-day test advances the ocean twice. LSG output
is written at each step. The tests check output dates, grid and level counts,
finite values, changing ocean temperature and salinity, and numerical means
for surface temperature, salinity, atmospheric wind stress, and ocean heat
flux. The `yfldo` atmospheric restart field checks the returned LSG heat flux
after interpolation to PlaSim's grid.

The numerical means were updated from commit `d4802a1` with GNU Fortran
15.2.0 using `-O0 -fdefault-real-8`. Their tolerances allow small compiler
differences. A separate restart test compares a continuous two-day run with
two one-day runs, retaining `kleiin1`, `kleiswi`, and the generated LSG matrix
between runs. It requires byte equality for both the atmospheric and LSG
restart files and for the final day's ocean output within the same build.
This covers short coupled execution and restart consistency; ocean spin-up,
long climate statistics, and other coupling modes need separate tests.

These tests are included in the normal discovery command and the existing
GitHub Actions workflow. To run only the LSG tests:

```sh
python3 -m unittest discover -s tests -p 'test_lsg.py' -v
```

## MPI tests

[`test_mpi.py`](test_mpi.py) builds the real `mpimod.f90` with `mpif90` and
`NPRO_ATM=2`, then launches two ranks with `mpiexec -n 2`. It checks that the
diagnostic lists ranks 0 and 1 and that both two-day runs reach the expected
final step. The mixed-layer and coupled LSG configurations each have a
separate serial reference run with identical input files.

An additional mixed-layer run enables spectral radiation (`nstartemp=1`).
All configurations check that the replicated `zsolars` restart record stores
exactly two double-precision values and agrees with serial; the spectral
fractions must also be positive and sum to one. Both classic and spectral
mixed-layer runs compare every restart record byte for byte between a
continuous two-day MPI run and two one-day MPI runs.

An additional mixed-layer MPI test uses nondefault soil heat capacity
(`soilcap=1.2e6`), tidally locked illumination, and a substellar longitude
of 90 degrees instead of the default 180 degrees. The three cases share
one serial build and one MPI build. Each case is compared with its matching
serial reference after one timestep and after two days, including soil
temperature, surface albedos, ocean state, and atmospheric spectral fields.
The startup comparison uses the existing strict limits (`atol=1e-10`,
`rtol=1e-8`) and catches all three omissions in the unfixed code.

For these new nondefault cases only, the two-day comparison uses
`atol=1e-8`, `rtol=1e-6`. Ubuntu/GNU Fortran 13 passes the strict startup
checks but develops differences around `1.5e-5 K` in surface temperature,
`2.3e-9` in humidity, and `9e-9` in albedo by day two. This is consistent
with growth of reduction roundoff in nonlinear calculations. The longer-run
limits allow small drift (about `0.0003 K` at 300 K), while the strict
startup checks independently protect parameter distribution. Serial controls
also check that each input changes the solution, including the longitude
shift. These tests exercise the shared initialization through Earth; Mars
and Exo setups are not run.

Every value in selected gridpoint and global spectral fields is compared
with the serial reference. The mixed-layer case uses pointwise absolute
tolerance `1e-10` and relative tolerance `1e-8` for double-precision restart
data. The coupled LSG atmosphere, including the returned `yfldo` heat flux,
uses both a maximum-error bound and an RMS-error bound:

```text
max(abs(MPI - serial)) <= 1e-10 + 1e-8 * max(abs(serial))
RMS(MPI - serial)      <= 1e-10 + 1e-8 * RMS(serial)
```

For albedo and ice concentration, the maximum-error scale is their physical
unit range (1), rather than the largest value in a snapshot. Both serial
and MPI values must also remain in `[0, 1]`. Their RMS bound is still based
on the actual reference RMS. This avoids making the maximum-error allowance
depend on whether this particular run reaches full snow albedo or ice cover.

The serial Legendre transform pairs opposite latitudes, while the parallel
transform sums rank-local contributions. These different summation orders
introduce roundoff, which the coupled heat-flux calculation can amplify.
With the new fixed-orbit defaults, Linux CI exceeded the former pointwise
limits in albedo, two spectral fields, and returned heat flux, although
the serial regression, restart equality, and ocean-output comparisons
passed. Relative errors at individual small coefficients are a poor measure
of the error in the whole field. The coupled criterion therefore scales the
maximum error by the field maximum, while the additional RMS bound prevents
a large maximum from hiding a distributed bias. This changes the coupled
MPI acceptance criterion; it does not change the physical model or saved
reference tolerances. Small comparison tests check fraction normalization
and rejection of invalid fractions, localized corruption, and distributed
bias.

Diagnostic one-, two-, and four-rank runs on macOS/GNU Fortran 15.2.0
confirmed growth of coupled roundoff over two ocean steps. For two ranks,
the largest returned-heat-flux difference after two days was about
`7.6e-10 W/m2`, with a serial field maximum near `2646 W/m2`; Linux CI had
reported a `1.5e-7 W/m2` difference at a point near `-6.76 W/m2`.
The dated LSG Service fields retain their pointwise absolute tolerance
`1e-5` and relative tolerance `1e-6` for 32-bit output. Coupled LSG restart
consistency under MPI and scaling performance are not covered; CI exercises
two ranks, while the four-rank run was a local diagnostic.

To run only the MPI tests:

```sh
python3 -m unittest discover -s tests -p 'test_mpi.py' -v
```

## Calendar tests

[`calendar_test.f90`](calendar_test.f90) is compiled in both single and double
precision with runtime bounds checking. Separate cases check calendar origins,
month/year boundaries, Gregorian century rules, subdaily conversion, every
perpetual date in 360-, 365-, and 660-day calendars, and monthly climatology
interpolation (including December/January padding). Invalid perpetual days
must stop with a clear range diagnostic.

For simplified calendars, `cal2step` converts hours/minutes using the configured
`solar_day` in seconds. Non-aligned positive times truncate to the preceding
timestep. The inverse interface has only minute resolution, so exact round
trips are tested where the timestep is representable in whole minutes,
including a 48-hour solar day. Arbitrary planetary day lengths can lose
subminute time in `step2cal30`.

Gregorian perpetual dates deliberately use a fixed 365-day climatology:
day 60 is March 1, independently of any earlier dated conversion. Ordinary
Gregorian dates still include February 29 in leap years. Simplified perpetual
dates use the configured equal-length months. These conventions also apply
to the separate perpetual ocean and ice settings when they request monthly
interpolation. Valid day numbers range from 1 to `n_days_per_year`.

To run only the calendar tests:

```sh
python3 -m unittest discover -s tests -p test_model.py -k CalendarTests -v
```
