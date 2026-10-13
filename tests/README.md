# PlaSim tests

Run from the repository root:

```sh
python3 -m unittest discover -s tests -v
```

The tests need Python 3, `gfortran`, `cc`, and `make`. They build a headless,
serial T21/L10 PlaSim in a temporary directory using the repository's existing
`make_plasim` build rules. No generated files are written into the checkout.

The suite checks the Gregorian and 360 day calendar, a deterministic two day
T21 run with broad numerical baselines, and byte equality between a continuous
two day run and a run restarted after one day. The fixed random seed is needed
for the restart comparison. These tests exercise the serial model; MPI tests
can be added separately when its execution path is addressed.

The numerical baselines come from the current `master` model, built with
`gfortran -O0 -fdefault-real-8`. They are intentionally tolerant of small
compiler and platform differences. A passing test supports short run
regression checking, not scientific validation of a long climate simulation.

Known gap: `cal2step` currently ignores hour and minute for the simplified
360 day calendar, so the calendar test checks that path at midnight. This is
a preexisting model issue to address separately.
