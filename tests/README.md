# PlaSim tests

Run from the repository root:

```sh
python3 -m unittest discover -s tests -v
```

GitHub Actions runs this command on pushes to `master` or `main`. It can also
be started manually from the Actions tab once the workflow is on the default
branch. On pull requests targeting either branch, add the exact `run tests`
label to start a run; later commits rerun the tests while the label remains.

The tests need Python 3, `gfortran`, `cc`, and `make`. They build a headless,
serial T21/L10 PlaSim in a temporary directory using the repository's existing
`make_plasim` build rules. No generated files are written into the checkout.

The suite checks the Gregorian and 360 day calendar, a deterministic two day
T21 run with broad numerical baselines, and byte equality between a continuous
two day run and a run restarted after one day. It also checks every value in
selected Earth state fields against a one day `master` restart fixture, resumes
that legacy restart, and runs one step with a non-default `albsmin` value.
The fixed random seed is needed for the restart comparisons. These tests
exercise the serial model; MPI and T42 tests remain separate follow-up work.

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
compatibility gates. The planet branch reads `psurf` from `planet_namelist`
and no longer accepts `sidereal_year` or `tropical_year`; those older input
locations and options are not covered by these tests.

Known gap: `cal2step` currently ignores hour and minute for the simplified
360 day calendar, so the calendar test checks that path at midnight. This is
a preexisting model issue to address separately.
