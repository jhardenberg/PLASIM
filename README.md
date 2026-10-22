[![DOI](https://zenodo.org/badge/101884206.svg)](https://zenodo.org/badge/latestdoi/101884206)
[![Documentation Status](https://readthedocs.org/projects/plasim-lsg/badge/?version=latest)](https://plasim-lsg.readthedocs.io/en/latest/?badge=latest)
![Stand with Ukraine](https://badgen.net/badge/stand%20with/UKRAINE/?color=0057B8&labelColor=FFD700)

# PlaSim-LSG TNG (The Next Generation)

PlaSim-LSG TNG (The Next Generation) is an intermediate-complexity atmosphere–ocean general circulation model (AOGCM) designed for climate research, paleoclimate studies, climate dynamics, and educational use.
This repository was originally a streamlined fork of [the original PLASIM repository](https://github.com/HartmutBorth/PLASIM) developed at University of Hamburg and is now maintained independently.

The model couples:
- **Planet Simulator (PlaSim):** A 3D spectral primitive-equation atmospheric model with parameterizations for radiation, clouds, moist and dry convection, large-scale condensation, boundary-layer fluxes, and land-surface processes.
- **Ocean options:** A mixed-layer (slab) ocean with thermodynamic sea ice, or fully coupled 3D circulation via the **Large-Scale Geostrophic (LSG)** ocean general circulation model.
- **Planetary flexibility:** Configurable planetary parameters for Earth, Mars, and hypothetical or exoplanetary climates.

Complete user and developer documentation is available on [Read the Docs](https://plasim-lsg.readthedocs.io/) (sources in [`docs/`](docs/index.md)).

## What is new in this version

PlaSim-LSG TNG modernizes and extends the original model suite:

- **Modern compiler and architecture support:** Updated Fortran 90 and C source trees compatible with modern compilers (GCC/`gfortran` 10+, Intel `ifx`/`ifort`), native architecture vectorization flags, robust precision handling, and parallel MPI execution.
- **Model tuning:** Atmospheric and surface tuning described in Angeloni et al. (submitted to GMD).
- **Headless MoSt configuration (`most.x -c`):** The model starter (MoSt) supports fully automated, display-free configuration and compilation via configuration files (`.cfg`), suitable for remote clusters, automated scripts, and CI pipelines without requiring an X11 display.
- **Direct NetCDF4 output:** Modernized output processing using [`scripts/srv2nc`](scripts/srv2nc) and CDO to convert raw model Service-format files directly into compressed NetCDF4, integrated into standard run scripts.
- **Planetary and exoplanet physics:** Support for stellar-spectrum shortwave radiation, spectral surface albedos, tidally locked illumination, and user-specified orbital configurations.
- **Comprehensive testing:** Automated regression test suite covering serial and MPI execution, mixed-layer and LSG coupled dynamics, calendars, and restart bit-reproducibility.
- **Performance benchmarking:** Standalone benchmark suite (`benchmarks/`) for reproducible execution, multi-core scaling analysis, and compiler comparison.
- **Sphinx documentation:** Complete user and developer documentation hosted on [Read the Docs](https://plasim-lsg.readthedocs.io/).

## Quickstart: configure, compile, and run

### Prerequisites

- **Build tools:** C and C++ compilers (`gcc`, `g++`), Fortran 90 compiler (`gfortran`), `make`, and `bash`.
- **X11 development headers:** `libx11-dev` (Ubuntu/Debian) or XQuartz (macOS) to build MoSt.
- **Optional:** MPI (`mpif90`, `mpicc`, `mpiexec`) for multi-core parallel runs; CDO (Climate Data Operators) for NetCDF4 conversion.

### 1. Build MoSt

From the repository root, detect compilers and compile the model starter:

```sh
./configure.sh
```

### 2. Configure and compile PlaSim

Configure your experiment interactively using the GUI:

```sh
./most.x
```

Select the planet (Earth, Mars, Exo), resolution (T21, T31, T42), vertical levels, ocean model (Mixed Layer or LSG), and CPU cores. Click **Save & Exit** to compile the executable and populate `plasim/run/`.

Alternatively, configure headlessly without a GUI display:

```sh
./most.x -c docs/examples/most-earth.cfg
```

### 3. Run the simulation

```sh
cd plasim/run
./most_plasim_run
```

The run script integrates the model, converts raw output to compressed NetCDF4 in `plasim/run/output/` using CDO, and archives annual restarts in `plasim/run/restart/`.

For details on directory layout, multi-year runs, and experiment management, consult:
- [Configure, compile, and run with MoSt](https://plasim-lsg.readthedocs.io/en/latest/user/most.html) ([docs/user/most.md](docs/user/most.md))
- [Experiment directories and long simulations](https://plasim-lsg.readthedocs.io/en/latest/user/experiments.html) ([docs/user/experiments.md](docs/user/experiments.md))
- [Planetary and orbital settings](https://plasim-lsg.readthedocs.io/en/latest/user/planets.html) ([docs/user/planets.md](docs/user/planets.md))
- [Parallel execution and coupled LSG ocean](https://plasim-lsg.readthedocs.io/en/latest/user/parallel-ocean.html) ([docs/user/parallel-ocean.md](docs/user/parallel-ocean.md))
- [Output conversion and postprocessing](https://plasim-lsg.readthedocs.io/en/latest/user/postprocessing.html) ([docs/user/postprocessing.md](docs/user/postprocessing.md))
- [Namelist parameter reference](https://plasim-lsg.readthedocs.io/en/latest/reference/index.html) ([docs/reference/index.md](docs/reference/index.md))

## Performance benchmarks

A standalone performance benchmark suite is provided in [`benchmarks/`](benchmarks/README.md) to measure model throughput, evaluate multi-core scaling, and compare compiler flags or git revisions across standardized T21 and T42 workloads (or optional T31 via `--resolutions T31`):

```sh
python3 benchmarks/run.py --benchmark smoke --cores 1,2
python3 benchmarks/compare.py benchmarks/results/
```

See the [benchmarking guide](benchmarks/README.md) and the manual's [benchmarking chapter](https://plasim-lsg.readthedocs.io/en/latest/development/benchmarking.html) ([docs/development/benchmarking.md](docs/development/benchmarking.md)) for details.

## Testing

Run the automated regression test suite from the repository root:

```sh
python3 tests/run_tests.py -v
```

or with the standard single-process discovery command:

```sh
python3 -m unittest discover -s tests -v
```

The test suite builds and executes headless T21 simulations in temporary directories, verifying continuous versus restarted runs, calendar calculations, legacy inputs, and coupled PlaSim–LSG ocean evolution. See [`tests/README.md`](tests/README.md) and the [testing guide](https://plasim-lsg.readthedocs.io/en/latest/development/testing.html) ([docs/development/testing.md](docs/development/testing.md)) for details.

## Documentation and resources

- **User Manual:** Complete guide and namelist reference on [Read the Docs](https://plasim-lsg.readthedocs.io/) (sources in [`docs/`](docs/index.md)).
- **FAQ:** Common questions and troubleshooting in [FAQ.md](FAQ.md) and [Troubleshooting Guide](https://plasim-lsg.readthedocs.io/en/latest/user/troubleshooting.html).
- **Changelog:** Detailed history of changes in [CHANGELOG.md](CHANGELOG.md).
- **Historical manuals:** Original PDF documentation is retained in [`plasim/doc/`](plasim/doc/) for reference.
