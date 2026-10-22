# Frequently asked questions

These answers update the older `FAQ` for the current PlaSim-focused repository. For current workflows, start with the [README](README.md) and the [Sphinx user manual](docs/index.md). The original [User's Guide](plasim/doc/PS_UsersGuide.pdf) is retained for historical context.

The developing Sphinx manual starts with the recommended [MoSt workflow](docs/user/most.md), including headless preparation, followed by [experiment directories and long simulations](docs/user/experiments.md). An [alternative direct-Make build](docs/development/direct-build.md) is in its separate developer part. Contributor [documentation build instructions](contributing/documentation.md) are kept separately from the published manual.

## `configure.sh` cannot find `make`, Fortran, or another compiler. What do I need?

Install a C compiler, a C++ compiler, a Fortran 90 compiler such as `gfortran`, and `make` (or `gmake`). The graphical MoSt build also needs X11 development headers and libraries. Some Linux distributions do not install development packages by default. MPI compiler wrappers and a launcher are optional for parallel runs. The serial test suite only needs Python 3, `gfortran`, `cc`, and `make`.

## The C compiler reports that an X11 header is missing. How can I build MoSt?

Install your distribution's X11 development package, such as `libx11-dev` on Ubuntu, then rerun `./configure.sh`. X11 application libraries alone may not include the headers needed to compile the GUI.

## MoSt reports `command not found` after **Save & Run**. What should I check?

Run MoSt from the repository root as `./most.x` after `./configure.sh`, and check that the generated run script and executable exist in `plasim/run` or `plasim/bin`. If launching a script manually, invoke it with its path, for example `./script-name` from its directory. The old FAQ suggested putting the current directory in `PATH`; an explicit path is clearer and avoids that global shell setting.

## The model rejects a namelist variable. What does that mean?

The variable is not recognized by the version of the model being run. Check the spelling, the namelist group, and whether the file was written for another PlaSim version. The old FAQ specifically mentions `NRESTART` in older namelists; remove or update unsupported options before retrying. Use the [detailed namelist tables](docs/reference/parameters/index.md) and [legacy-input crosswalk](docs/reference/parameters/legacy.md) to check current names, units, defaults, and migration guidance. The [legacy namelist regression tests](tests/README.md) cover selected classic inputs, but not every historical option.

## I edited Fortran source, but the model behaves as before. Why?

Make permanent edits in `plasim/src`, not the copied sources under `plasim/bld`. MoSt can reuse binaries from `plasim/bin`. After saving any outputs you need, run `./cleanplasim` from the repository root and rebuild. This command removes the generated contents of `plasim/bld`, `plasim/bin`, and `plasim/run`.

## Why do orbital parameters depend on how I split a run?

Earth runs now default to `N_START_YEAR=2000` and `NFIXORB=1`, including
direct executable runs. Existing namelists that omit these fields inherit
the new defaults; explicitly specify older values when reproducing an old
experiment.

With `NFIXORB=0`, Berger orbital elements are calculated at radiation
initialization from the current model year, including the restored year
when restarting. They remain unchanged during that executable invocation.
A continuous multiyear run and annual restart chunks therefore use different
orbital forcing. For annual evolution, restart at each year boundary and
omit an explicit `IYRBP` override. For a prescribed fixed orbit, use
`NFIXORB=1` with explicit `ECCEN`, `OBLIQ`, and `MVELP`. This is a known
limitation, not a guarantee of restart-independent transient forcing; see
the [orbital configuration notes](docs/user/planets.md#prescribed-and-calculated-orbits).

## Can I edit orography with MoSt?

The old FAQ described an experimental PUMA orography editor for a 32-latitude setup: select a rectangular region, enter an anomaly in geopotential metres, and preprocess it. The GUI did not immediately redraw the result; the next PUMA run used the new orography. PUMA is not included in this PlaSim-focused checkout, so those steps are historical and cannot be followed here as written. For PlaSim input data, consult the [User's Guide](plasim/doc/PS_UsersGuide.pdf).

## How do I compile the postprocessor?

For the `burn7` postprocessor included here, run `make -C postprocessor`. You need the NetCDF C++ library and headers; the makefile may need include or library path adjustments for your installation. The old FAQ referred to `Most15`, `make_suse`, and `burn5.x`, which are not the build files or postprocessor in this repository. See the [postprocessing guide](docs/user/postprocessing.md) and the [burn7 quick reference](postprocessor/burn7qr.pdf).
