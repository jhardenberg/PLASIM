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
It also checks every value in selected Earth state fields against a one day
`master` restart fixture, resumes that legacy restart, and runs one step with
a non-default `albsmin` value.
The fixed random seed is needed for the restart comparisons. These tests
exercise the serial model; additional MPI coverage is described below. T42
tests remain separate follow-up work.

The numerical baselines come from the current `master` model, built with
`gfortran -O0 -fdefault-real-8`. They are intentionally tolerant of small
compiler and platform differences. A passing test supports short run
regression checking, not scientific validation of a long climate simulation.

`fixtures/earth_t21_l10_day1_360.restart.gz` is a T21/L10 Earth restart after
one day of the unmodified `master` commit `88e68db5302d1db3c0ad636444eadda833738d52`,
using the same headless build and namelists as `test_model.py` with Homebrew
GNU Fortran 15.2.0. Its uncompressed SHA-256 is
`6b851dcb07544493620992e82ce6af4fab573fdccaa6af94f102788665dac42c`.
The elementwise comparison uses an absolute and relative tolerance of `1e-6`
to catch changes that broad global means miss. The fixture uses the source
model's default 360 day calendar; the MoSt-generated 365 day setup is not yet
covered by this strict comparison. The legacy restart and `albsmin` checks are
compatibility gates. Legacy restarts without spectral albedo records can be
continued in broadband radiation mode; spectral radiation requires those
records. The planet branch reads `psurf` from `planet_namelist`
and no longer accepts `sidereal_year` or `tropical_year`; those older input
locations and options are not covered by these tests.

## Coupled PlaSim and LSG tests

[`test_lsg.py`](test_lsg.py) builds the actual `lsg/src/lsgmod.f90` and
`plasim/src/cpl.f90`, rather than the stubs used by the atmosphere tests.
It uses the checked-in `lsg/dat` inputs and restart, including the coupled
land mask, on LSG's 72 × 76 grid with 22 ocean levels. The atmosphere uses
T21/L10, the 360-day calendar, and `nlsg=1` (atmospheric SST forcing and
ocean heat-flux feedback).

The coupling interval is one day (`naomod=32`), instead of the production
default of ten days, so a two-day test advances the ocean twice. LSG output
is written at each step. The tests check output dates, grid and level counts,
finite values, changing ocean temperature and salinity, and numerical means
for surface temperature, salinity, atmospheric wind stress, and ocean heat
flux. The `yfldo` atmospheric restart field checks the returned LSG heat flux
after interpolation to PlaSim's grid.

The numerical means were recorded from commit `d2eef95` with GNU Fortran
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

An additional mixed-layer MPI test uses nondefault soil heat capacity
(`soilcap=1.2e6`), tidally locked illumination, and a substellar longitude
of 90 degrees instead of the default 180 degrees. The three cases share
one serial build and one MPI build. Each two-day run is compared with its
matching serial reference, including soil temperature, surface albedos,
ocean state, and atmospheric spectral fields, using the same tolerances
as the default cases below. Serial comparisons also check that the input
settings change the solution, including the longitude shift. These tests
exercise the shared planetary initialization through Earth; Mars and Exo
setups are not run.

Every value in selected gridpoint and global spectral fields is compared
with the serial reference, with absolute tolerance `1e-10` and relative
tolerance `1e-8` for double-precision restart data. For LSG this includes the
heat flux returned to PlaSim and all dated ocean Service fields, using
absolute tolerance `1e-5` and relative tolerance `1e-6` for the latter's
32-bit output. This allows roundoff from MPI reductions while checking data
distribution and flux exchange. MPI restart consistency, other rank counts,
and scaling performance are not covered by these tests.

To run only the MPI tests:

```sh
python3 -m unittest discover -s tests -p 'test_mpi.py' -v
```

Known gap: `cal2step` currently ignores hour and minute for the simplified
360 day calendar, so the calendar test checks that path at midnight. This is
a preexisting model issue to address separately.
