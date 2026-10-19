# Introduction

## What is PlaSim-LSG TNG?

**PlaSim-LSG TNG (The Next Generation)** is a global 3D climate model of
intermediate complexity designed for meteorology, paleoclimate, Earth-system,
and planetary climate experiments. It builds on the original Planet Simulator
(PlaSim) created at the University of Hamburg and is maintained independently
in the **[jhardenberg/PLASIM repository](https://github.com/jhardenberg/PLASIM)**.
Because several PlaSim forks exist with different features and input conventions,
this manual documents the specific interfaces of this repository (referred to
simply as "PlaSim" where unambiguous).

At its core, PlaSim couples a **spectral primitive-equation atmosphere** with
parameterizations for physical processes on a Gaussian longitude–latitude grid:

- **Atmosphere and radiation:** 3D spectral dynamics (vorticity, divergence,
  temperature, surface pressure, and specific humidity), shortwave and
  longwave radiation (with classic broadband or optional stellar-spectrum
  modes), interactive clouds, moist convection, large-scale precipitation,
  and boundary-layer vertical diffusion.
- **Land and vegetation:** Soil heat transfer, soil hydrology and river
  runoff, snow cover, and the optional **SIMBA** dynamic vegetation and carbon
  module.
- **Ocean and sea ice:** Thermodynamic sea ice coupled either to a slab
  **mixed-layer ocean** (default, with optional horizontal diffusion and heat-flux
  correction) or to the 3D **LSG (Large Scale Geostrophic) deep-ocean model**
  (72 × 76 horizontal grid, 22 vertical levels).
- **Planets:** Built-in presets and boundary datasets for **Earth**, **Mars**,
  and generalized **Exo** (exoplanet) setups, including configurable orbits,
  calendars, and tidally locked illumination.

## How PlaSim is configured and compiled

PlaSim separates **compile-time build choices** from **runtime namelist
parameters**:

1. **Compile-time settings (selected via MoSt):** Horizontal resolution
   (standard truncations **T21** at 64 × 32, **T31** at 96 × 48, or **T42** at
   128 × 64 grid points), vertical levels (typically 10), number of MPI
   processor cores, planet preset (`Earth`, `Mars`, or `Exo`), deep-ocean
   coupling (`LSG Ocean`), numerical precision, and whether to link the X11
   simulation GUI. These are compiled into the Fortran executable (`resmod.f90`
   and selected module variants).
2. **Runtime settings (namelists and run script):** Integration length, start
   year, calendar type, $\mathrm{CO_2}$ concentration, solar constant, orbital
   elements, output frequency, and physical tuning parameters. These are read
   from plain-text `*_namelist` files in the run directory when the executable
   starts, while multi-year looping and NetCDF postprocessing are controlled
   by the generated run script (`most_plasim_run`).

## What is new in PlaSim-LSG TNG?

- **Expanded planetary capabilities:** Harmonized presets for Earth, Mars, and
  exoplanets, optional stellar-spectrum radiation and two-band surface
  albedos, and tidally locked illumination.
- **Refined model physics:** Updated radiation, land-surface hydrology, and
  standalone SIMBA vegetation handling.
- **Tuned, working LSG deep-ocean coupling:** Ready-to-run coupling between
  PlaSim and the LSG ocean model with configurable vertical diffusion and
  conserved flux exchanges.
- **Improved MPI parallel performance:** Batched collective communications and
  streamlined spectral transforms reduce parallel overhead across multiple cores.
- **Easier experiment setup and NetCDF output:** Both graphical and headless
  (`most.x -c`) experiment preparation, plus direct Service-to-NetCDF4
  conversion via CDO (`scripts/srv2nc`) without needing the legacy afterburner.
- **Automated testing and verification:** Regression tests covering serial,
  MPI, restart continuation, calendar rules, and coupled PlaSim–LSG runs.

Full details and compatibility notes are recorded in the
{download}`changelog <../../CHANGELOG.md>`.

## Where to go next

```{toctree}
:hidden:

components
```

- **Understand the modules:** Read {doc}`components` for an overview of all
  atmospheric, land, ice, and ocean modules and their namelist files.
- **Compile and run your first simulation:** Follow {doc}`getting-started` and
  {doc}`most` to build MoSt, compile PlaSim, and run `most_plasim_run`.
- **Customize and analyze:** Continue to {doc}`configuration` (planets,
  boundary data, MPI/LSG, restarts), {doc}`analysis` (converting and plotting
  NetCDF output), and the {doc}`configuration and output reference <../reference/index>`.
- **Extend or test the code:** Part II covers {doc}`../development/architecture`,
  {doc}`../development/testing`, {doc}`../development/benchmarking`, and the
  {doc}`../development/direct-build`. Attribution to the original University of
  Hamburg manuals is in {doc}`../sources`.
