[![DOI](https://zenodo.org/badge/101884206.svg)](https://zenodo.org/badge/latestdoi/101884206)
[![Documentation Status](https://readthedocs.org/projects/plasim-lsg/badge/?version=latest)](https://plasim-lsg.readthedocs.io/en/latest/?badge=latest)
![Stand with Ukraine](https://badgen.net/badge/stand%20with/UKRAINE/?color=0057B8&labelColor=FFD700)

# PlaSim-LSG TNG (The Next Generation)

PlaSim-LSG TNG (The Next Generation) builds on and improves the original Planet Simulator (PlaSim), a general circulation model used in meteorology and Earth sciences. This version is maintained in [jhardenberg/PLASIM](https://github.com/jhardenberg/PLASIM). This repository was originally a streamlined fork of [Hartmut Borth's PLASIM repository](https://github.com/HartmutBorth/PLASIM) and is now maintained independently. It contains the components needed to build and run PlaSim-LSG TNG, its LSG ocean configuration, MoSt (the model starter), postprocessors, and tests.

Running and interpreting the model requires some knowledge of meteorology and climatology, as well as familiarity with Linux, C, and Fortran. Start with the [Sphinx user manual](docs/index.md). The original [User's Guide](plasim/doc/PS_UsersGuide.pdf) is retained for historical context; the scientific [Reference Manual](plasim/doc/PS_ReferenceManual.pdf) remains separate. See also the [FAQ](FAQ.md) and [changelog](CHANGELOG.md).

The [Sphinx manual](docs/index.md) provides a user guide and a separate developer guide, migrated from the practical User's Guide and checked against current code. Start with [MoSt compilation and preparation](docs/user/most.md); then consult chapters on experiments, components, planetary settings, MPI/LSG, boundary data, GUI, restarts, postprocessing, and output/configuration reference. Advanced users can consult the [detailed namelist tables](docs/reference/parameters/index.md), including types, units, defaults, and interactions for each current input. The developer part includes the [optional direct-Make/CI example](docs/development/direct-build.md), testing, and performance benchmarking. Contributor [documentation maintenance notes](contributing/documentation.md) are kept separately from the published manual. The scientific Reference Manual is outside this migration.

## Features in this repository

- Model tuning described in Angeloni et al. (submitted to GMD).
- [`scripts/srv2nc`](scripts/srv2nc), which uses CDO to convert PlaSim and LSG Service output directly to compressed NetCDF4 without the afterburner.
- Headless MoSt: `most.x -c` reads `most_last_used.cfg` by default, or a configuration file supplied as an additional argument.
- Planetary and exoplanet developments, including optional stellar-spectrum radiation, spectral surface albedos, and tidally locked illumination.

## Requirements

For the standard build, install a C compiler, a C++ compiler, a Fortran 90 compiler such as `gfortran`, and `make`. The graphical MoSt interface also needs X11 headers and libraries. `configure.sh` searches for these tools and reports what it finds. For parallel execution, install MPI with Fortran and C compiler wrappers (for example, `mpif90`, `mpicc`, and `mpiexec`). MPI is optional for serial runs.

The `burn7` postprocessor needs the legacy NetCDF C++ library and its `netcdfcpp.h` header. The `srv2nc` and `burn.sh` scripts use CDO; `burn.sh` also invokes `burn7`. The Python map example uses optional xarray and Matplotlib packages, with netCDF4 and cftime for reading NetCDF files and model calendars.

## Configure, compile, and run

Running an experiment in PlaSim-LSG TNG uses **MoSt** (`most.x`), the model starter, from the repository root:

```sh
./configure.sh
./most.x
```

1. **Build MoSt (`./configure.sh`):** Detects your Fortran/C/C++/MPI compilers and X11 libraries, creates `plasim/bld`, `plasim/bin`, and `plasim/run`, and builds `most.x`.
2. **Configure and compile PlaSim (`./most.x` or `./most.x -c`):**
   - **Interactive GUI (`./most.x`):** Select **Planet Simulator**, choose your planet (`Earth`, `Mars`, or `Exo`), resolution (`T21` at 64 × 32, `T31` at 96 × 48, or `T42` at 128 × 64), levels, cores, and ocean modules (`ML Ocean`, `Sea Ice`, or `LSG Ocean`). Click **Save & Exit** to compile the model and prepare `plasim/run/` (or **Save & Run** to also launch the simulation immediately).
   - **Headless config file (`./most.x -c`):** Run `./most.x -c docs/examples/most-earth.cfg` (or `./most.x -c` to use `most_last_used.cfg`) to compile and prepare `plasim/run/` without opening an X11 display.
3. **Run the simulation (`most_plasim_run`):** MoSt places the compiled executable (`most_plasim_t21_l10_p1.x`), boundary data (`*.sra`), runtime namelists (`*_namelist`), and the driver script `most_plasim_run` inside `plasim/run/`:
   ```sh
   cd plasim/run
   ./most_plasim_run
   ```
   With the simulation GUI disabled (`NGUI=0`), `most_plasim_run` loops from `YEAR1` to `YEAR2` (one model year per segment), converts raw Service output to compressed NetCDF4 in `output/` (`MOST_PLA.0001.nc`, `MOST_OCE.0001.nc`, `MOST_ICE.0001.nc`, `MOST_DIAG.0001.txt`, plus `MOST_LSG.0001.nc` when LSG is enabled) using `scripts/srv2nc`, and copies `plasim_status` to `plasim_restart` (and `restart/MOST_REST.0001`) to hand off state between years.

For multi-year experiments, copy `plasim/run/` to a dedicated experiment directory before editing namelists or `most_plasim_run`; see [Configure, compile, and run with MoSt](docs/user/most.md) and [Experiment directories and long simulations](docs/user/experiments.md). Edit permanent model sources in [`plasim/src`](plasim/src). Running `./cleanplasim` removes all generated files in `plasim/bld`, `plasim/bin`, and `plasim/run`; save any outputs you need first.

### Orbital parameters and experiment dates

New Earth experiments default to start year **2000** and `NFIXORB=1`, both
when launched directly and through MoSt. `N_START_YEAR` is set in
`plasim_namelist` (`plasim_nl`); `NFIXORB` is set in
`planet_namelist` (`planet_nl`). This holds the prescribed eccentricity
(`ECCEN`), obliquity (`OBLIQ`), and longitude of perihelion (`MVELP`) fixed.
The seasonal and diurnal cycles still follow the model calendar. Saved MoSt
configurations and existing namelists retain their explicit settings.

With `NFIXORB=0`, the model computes Berger orbital elements **once at
radiation initialization**, using the current model year. A cold start uses
`N_START_YEAR`; a restart uses the year of the restored model timestep,
even if `N_START_YEAR` is unchanged. An explicit `IYRBP` in
`radmod_namelist` overrides this epoch: the orbital year is `1950 - IYRBP`.
`IYRBP` has no effect when `NFIXORB=1`.

**There is currently no automatic orbital update at a year boundary within
one executable invocation.** For example, a continuous 2000–2009 run with
`NFIXORB=0` retains the elements calculated for 2000 throughout. Running the
same experiment as one-year chunks, each continued from `plasim_restart`,
recalculates the elements for 2000, 2001, and so on, unless `IYRBP` explicitly
fixes the orbital epoch. MoSt normally creates annual chunks without the
simulation GUI; selecting that GUI instead runs all requested years in one
invocation. Check the generated run script and `N_RUN_YEARS` rather than
assuming an update interval. The computed epoch and elements are printed in
`plasim_diag` at each initialization.

This initialization-only behavior is a known limitation for transient
orbital experiments: changing restart frequency can change the forcing and
trajectory. Use annual restarts for yearly orbital updates, or prescribe a
fixed orbit for time-independent forcing. Automatic annual updates remain
an open design question in [issue #9](https://github.com/jhardenberg/PLASIM/issues/9).

Existing inputs that omit either setting now inherit its new default.
To retain the previous Earth setup, explicitly set `N_START_YEAR=1` in
`plasim_namelist` and `NFIXORB=0` in `planet_namelist`.
Restart-file formats are unchanged, but continuing an existing
`NFIXORB=0` experiment now uses its restart year instead of its original
start year. To reproduce its previous orbital forcing, set `IYRBP` to
`1950 - original_start_year` (for example, `IYRBP=-50` for an original start
year of 2000), or retain any existing explicit `IYRBP` value.

## Platform notes

### Ubuntu and other Linux distributions

The older Ubuntu instructions install `gfortran` and `libx11-dev` for a graphical build. For MPI they also install `libopenmpi-dev` and `openmpi-bin`. Install a C/C++ toolchain and `make` as well. Package names may differ by distribution and release. A serial, headless T21 build is exercised by the [test suite](#tests).

### macOS

The original macOS notes report successful builds on Mac OS X 10.5 and 10.6 with `gfortran`. They use MacPorts to install a GNU compiler, CDO, GrADS, ImageMagick, a PostScript viewer, and OpenMPI. Those version-specific commands (`gcc45`, for example) are historical; use packages appropriate for your current macOS installation. An X11 installation is needed for the GUI.

### Windows

The legacy Windows notes say that PlaSim and the postprocessor can be compiled with suitable Fortran and C++ compilers, while the MoSt GUI requires X11 and does not run as a native Windows GUI. They suggest an X11 environment or running Linux in a virtual machine or on the computer itself. These are historical options, not a currently tested Windows setup.

## Historical PlaSim–PUMA coupling notes

The old coupling README describes a two-instance experiment. It requires a separate PUMA tree and executables, which are absent from this checkout. In MoSt, the PUMA instance used one CPU, two instances, orography, an annual cycle, `NSYNC=1`, and `SYNCSTR=0.1`; PlaSim used one CPU, two instances, `NSYNC=1`, and `SYNCSTR=0.1`.

The recipe copied PUMA run files ending in `_01` and PlaSim's executable, `*.sra` files, and files ending in `_00` into one run directory. It set `NEQSIG=1` and `N_DAYS_PER_YEAR=360` in `puma_namelist_00`, optionally copied `GUI_01.cfg` and `GUI_00.cfg`, and required a run script that kept `_01` PUMA and `_00` PlaSim output separate. The original example launched both executables with MPMD MPI syntax: `openmpiexec -np 1 most_plasim_t21_l10_p1.x : -np 1 most_puma.x 32 10`. Treat this as an archived recipe for the former model suite; it is not a runnable command for the current repository.

## Postprocessing

### `burn7`

`burn7` is the C++ afterburner for PUMA and PlaSim Service data. It uses the NetCDF C++ library, processes version 16 data, and is backward compatible with older files. Compared with `burn6`, the original notes describe lower memory use, faster processing, and improved CF/NetCDF compatibility.

Build it with `make -C postprocessor`. The makefile expects `netcdfcpp.h` and `libnetcdf_c++` to be available to the compiler and linker. The macOS-specific `postprocessor/makefile_MAC` uses `/opt/local/include` and `/opt/local/lib`; adjust include and library paths for your installation if needed. The resulting `postprocessor/burn7.x` can be placed on your `PATH`. For usage, see the postprocessor chapter of the [PlaSim User's Guide](plasim/doc/PS_UsersGuide.pdf) and the [quick reference card](postprocessor/burn7qr.pdf).

### `burn.sh` CMOR-style extraction

[`scripts/burn.sh`](scripts/burn.sh) extracts variables from PlaSim output using CMOR-style names. It adjusts names, signs, and units and computes some derived variables. Its historical version 1.0 usage is:

```text
burn.sh [options] infile outfile var
  -h                Show help and the variable list
  -s                Extract 3D variables on sigma levels
  -a                Extract an afterburner variable without CMOR conversion
  -p lev1,lev2,...  Pressure levels in hPa
```

The default pressure levels are `20,30,50,70,100,150,200,250,300,400,500,600,700,850,925,1000` hPa. `uas` and `vas` are derived from `ua` and `va` at sigma level 1. Sea-level pressure (`psl`) is derived from surface humidity, temperature, and pressure using the hypsometric formula. Variables outside the named list are passed directly to the afterburner. `burn.sh` uses this checkout's `postprocessor/burn7.x` by default; set `BURNER=/path/to/burn7.x` to use another executable. `PLEVS` can override the default pressure levels, or use `-p`. Both executable and data paths may contain spaces. The following variable reference preserves the original script README's categories and uses the current script's source-variable names; `burn.sh -h` generates its current list.

#### 2D CMOR2 variables

| Name | Long name | Units | Source variables |
| --- | --- | --- | --- |
| `ps` | Surface Air Pressure | Pa | `ps` |
| `psl` | Sea Level Pressure | Pa | `psl` |
| `tas` | Near-Surface Air Temperature | K | `tas` |
| `tasmin` | Daily Minimum Near-Surface Air Temperature | K | `tasmin` |
| `tasmax` | Daily Maximum Near-Surface Air Temperature | K | `tasmax` |
| `ts` | Surface Temperature | K | `ts` |
| `uas` | Eastward Near-Surface Wind | m s-1 | `ua` |
| `vas` | Northward Near-Surface Wind | m s-1 | `va` |
| `evspsbl` | Evaporation | kg m-2 s-1 | `evap` |
| `pr` | Precipitation | kg m-2 s-1 | `pr` |
| `prc` | Convective Precipitation | kg m-2 s-1 | `prc` |
| `prl` | Large Scale Precipitation | kg m-2 s-1 | `prl` |
| `prsn` | Snowfall Flux | kg m-2 s-1 | `prsn` |
| `mrros` | Surface Runoff | kg m-2 s-1 | `mrro` |
| `mrso` | Total Soil Moisture Content | kg m-2 s-1 | `mrso` |
| `tsl` | Temperature of Soil | K | `tso` |
| `rsdt` | TOA Incident Shortwave Radiation | W m-2 | `rsut rst` |
| `rsut` | TOA Outgoing Shortwave Radiation | W m-2 | `rsut` |
| `rlut` | TOA Outgoing Longwave Radiation | W m-2 | `rlut` |
| `rsds` | Surface Downwelling Shortwave Radiation | W m-2 | `ssru rss` |
| `rsus` | Surface Upwelling Shortwave Radiation | W m-2 | `ssru` |
| `rlds` | Surface Downwelling Longwave Radiation | W m-2 | `stru rls` |
| `rlus` | Surface Upwelling Longwave Radiation | W m-2 | `stru` |
| `hfls` | Surface Upward Latent Heat Flux | W m-2 | `hfls` |
| `hfss` | Surface Upward Sensible Heat Flux | W m-2 | `hfss` |
| `clt` | Total Cloud Fraction | % | `clt` |
| `prw` | Water Vapor Path | kg m-2 | `prw` |
| `huss` | Near-Surface Specific Humidity | 1 | `hus` |
| `hurs` | Near-Surface Specific Humidity | 1 | `tas td2m` |
| `orog` | Surface Altitude | m | `sg` |
| `snd` | Snow Depth | m | `snd` |
| `snm` | Surface Snow Melt | kg m-2 s-1 | `snm` |
| `tauu` | Surface Downward Eastward Wind Stress | Pa | `tauu` |
| `tauv` | Surface Downward Northward Wind Stress | Pa | `tauv` |
| `sit` | Sea Ice Thickness | m | `sit` |
| `sic` | Sea Ice Cover | % | `sic` |

#### 3D CMOR2 variables

| Name | Long name | Units | Source variables |
| --- | --- | --- | --- |
| `hus` | Specific Humidity | 1 | `hus` |
| `hur` | Relative Humidity | % | `hur` |
| `zg` | Geopotential Height | 1 | `zg` |
| `ta` | Air Temperature | K | `ta` |
| `ua` | Eastward Wind | m s-1 | `ua` |
| `va` | Northward Wind | m s-1 | `va` |
| `wa` | Upward Wind | m s-1 | `wa` |
| `wap` | omega (=dp/dt) | Pa s-1 | `wap` |
| `cl` | Cloud Area Fraction | % | `cl` |
| `clw` | Mass Fraction of Cloud Liquid Water | 1 | `clw` |

#### Not standard variables

| Name | Long name | Units | Source variables |
| --- | --- | --- | --- |
| `td2m` | Near-Surface Dewpoint Temperature | K | `td2m` |
| `rst` | TOA Net Shortwave Radiation | W m-2 | `rst` |
| `rls` | Surface Net Longwave Radiation | W m-2 | `rls` |
| `alb` | Surface Albedo | 1 | `alb` |
| `prl` | Large Scale Precipitation | kg m-2 s-1 | `prl` |
| `sndc` | Surface Snow Depth Change | m s-1 | `sndc` |
| `stf` | Stream Function | m | `stf` |
| `lsm` | Land Sea Mask | 1 | `lsm` |
| `mld` | Ocean Mixed Layer Thickness | m | `mld` |

### Monthly extraction

[`scripts/postmon.sh`](scripts/postmon.sh) processes `MOST.NNN` files for an
inclusive year range and writes fixed fields and monthly means:

```sh
INDIR=/path/to/run POSTDIR=/path/to/post scripts/postmon.sh experiment 1 10
```

It uses the adjacent `burn.sh`; set `BURNSH` to another executable script if
needed. Set `BURNER` for that script's afterburner. If `INDIR` and `POSTDIR` are
omitted, the historical defaults use `$WORK/plasim/plasim/exps/experiment`
and `$SCRATCH/plasim/exps/experiment/post`. `PLEVS` is passed to `burn.sh`.

Both extraction scripts require Bash, CDO, and `mktemp`. They use private
temporary directories under `TMPDIR` (or `/tmp`), clean up on exit or signals,
and return a nonzero status on processing failures. `burn.log` in the current
directory records the most recent `burn.sh` invocation, including all component
variables and command errors. Numerical conversion formulas and output naming
are unchanged.

### Other conversion tools

[`scripts/srv2nc`](scripts/srv2nc) converts PlaSim and LSG Service output to NetCDF4 with CDO. [`scripts/nc2sra`](scripts/nc2sra) and [`scripts/sra2nc`](scripts/sra2nc) convert between NetCDF and Service-format boundary data. The [`scripts` directory](scripts) also contains monthly postprocessing and boundary-data helpers.

## Atmospheric timestep and LSG timing defaults

MoSt and the model select 45/30/20-minute atmospheric timesteps for
T21/T31/T42. With LSG enabled, omitted or zero `NAOMOD` selects ten
atmospheric days: 320/480/720 steps at those Earth defaults. Positive
explicit intervals must span whole days. Earlier direct T31/T42 defaults
were 36/30 minutes, and a fixed 320-step coupling interval did not preserve
ten days at higher resolutions. These timing changes affect existing
experiments; preserve original valid timing settings explicitly for
continuation. See [coupling defaults and migration](docs/user/parallel-ocean.md).

## Performance benchmarks

A separate [benchmark suite](benchmarks/README.md) measures repeated optimized
T21/T42 runs with mixed-layer and real LSG oceans, classic broadband radiation,
and selectable MPI rank counts. Use `--parallel --max-cores N` to run independent
benchmark cases within a shared rank budget; `compare.py --summary` combines
separately collected serial and MPI results. It records timings and build/input metadata
and compares source revisions. Benchmarks are run manually, outside regression
tests and test CI; their state summaries do not replace correctness checks.
See the manual's [benchmarking chapter](docs/development/benchmarking.md)
for a small runnable example, timing scope, and revision/MPI comparisons.

## Tests

Run the regression suite from the repository root:

```sh
python3 -m unittest discover -s tests -v
```

The tests require Python 3, `gfortran`, `cc`, and `make`. MPI tests additionally require `mpif90` and `mpiexec`; they are skipped locally if those tools are absent. The MoSt input-reader tests also need X11 headers and libraries (no running X server); CI installs `libx11-dev` alongside Open MPI. Tests build headless T21/L10 PlaSim binaries in temporary directories using `make_plasim`; generated files are not written into the checkout. The suite checks Gregorian and 360-day calendars, a deterministic two-day run with broad numerical baselines, byte equality between continuous and restarted two-day runs, selected Earth state values against a saved one-day reference for the new defaults, legacy restart loading, and classic namelist inputs. A fixed random seed is required for restart comparisons.

The suite also builds and runs the real PlaSim–LSG coupled model. Its two-day test uses daily coupling to exercise two ocean steps, checks ocean state and fluxes in both directions, and verifies that restarting both components reproduces a continuous run. See the [coupled test setup](tests/README.md#coupled-plasim-and-lsg-tests) for inputs, baselines, and scope.

Separate [MPI tests](tests/README.md#mpi-tests) run both ocean configurations on two ranks and compare their atmospheric state, ocean state, and coupled fluxes with matching serial runs.

The current broad baselines come from source commit `d4802a1`, using the year-2000 fixed-orbit defaults and `gfortran -O0 -fdefault-real-8` and tolerate small compiler and platform differences. Passing these short-run regression tests does not establish long-term scientific validity. T42 and other MPI rank counts remain future work.

The current one-day Earth reference is [`earth_t21_l10_day1_2000_fixed.restart.gz`](tests/fixtures/earth_t21_l10_day1_2000_fixed.restart.gz), generated from commit `d4802a1` with the intentional year-2000, fixed-orbit defaults. The older [`earth_t21_l10_day1_360.restart.gz`](tests/fixtures/earth_t21_l10_day1_360.restart.gz) remains an input for legacy-restart continuation, with its original year-1, Berger-orbit settings made explicit in that test. The elementwise state comparison retains absolute and relative tolerance `1e-6`. Both references use the 360-day calendar; the MoSt-generated 365-day setup is not covered by the strict state comparison. See [reference provenance and comparisons](tests/README.md#earth-reference-data) for source commits, compiler settings, checksums, and the recorded changes.

GitHub Actions runs the suite on pushes to `master` or `main`, by manual dispatch, and on pull requests targeting those branches when the exact `run tests` label is present. Later commits rerun a labeled PR.

[Calendar tests](tests/README.md#calendar-tests) also cover subdaily times with configured planetary day lengths, perpetual dates, and monthly climatology interpolation. Gregorian perpetual dates use a fixed 365-day climatology (day 60 is March 1); ordinary dated runs retain leap years.
