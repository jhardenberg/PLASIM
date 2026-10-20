# Model components and experiment choices

This chapter provides a practical overview of the physical modules in
PlaSim-LSG TNG, their source files, and the runtime namelists that control
them. It adapts chapter 2 of the original *Planet Simulator User's Guide* to
the current codebase (mathematical derivations remain in the separate
{download}`Reference Manual <../../plasim/doc/PS_ReferenceManual.pdf>`).

## Overview of model modules

The atmosphere integrates its prognostic variables (vorticity, divergence,
temperature, log surface pressure, and specific humidity) in spectral space
using triangular truncation (**T21** corresponds to a 64 × 32 Gaussian grid,
**T31** to 96 × 48, and **T42** to 128 × 64) and $\sigma$ vertical levels.
At every timestep, the fields are transformed to the Gaussian grid to compute
diabatic tendencies and surface exchanges across the modules listed below.

Horizontal resolution, vertical levels, MPI core count, the planet preset, and
whether LSG is linked are **compile-time settings** selected through MoSt;
editing a runtime namelist alone does not change the compiled grid or link
additional modules.

| Component | Source file(s) | Namelist file / group | Responsibilities |
| --- | --- | --- | --- |
| **Dynamics and run control** | `plasim.f90`, `plasimmod.f90` | `plasim_namelist` / `plasim_nl` | Time integration, spectral dynamics, horizontal diffusion, calendar/duration control, diagnostics, and restarts. |
| **Planet properties** | `p_earth.f90`, `p_mars.f90`, or `p_exo.f90` | `planet_namelist` / `planet_nl` | Planetary radius, gravity, surface pressure, gas constants, rotation rate, solar constant, and orbital parameters. |
| **Surface fluxes** | `fluxmod.f90` | `fluxmod_namelist` / `fluxmod_nl` | Surface wind stress, sensible and latent heat fluxes, and boundary-layer vertical diffusion. |
| **Radiation** | `radmod.f90`, `specblock.f90` | `radmod_namelist` / `radmod_nl` | Shortwave and longwave radiative transfer, $\mathrm{CO_2}$, ozone, clouds, and optional stellar-spectrum radiation. |
| **Moist processes** | `rainmod.f90` | `rainmod_namelist` / `rainmod_nl` | Cumulus convection, large-scale condensation, cloud formation, snowfall, and dry convective adjustment. |
| **Humidity and nudging** | `miscmod.f90` | `miscmod_namelist` / `miscmod_nl` | Negative-humidity mass fixer (`NFIXER`) and optional temperature nudging (`NUDGE`). |
| **Surface interface** | `surfmod.f90` | `surfmod_namelist` / `surfmod_nl` | Reading surface boundary files (`*.sra`), spectral orography initialization, and land/sea dispatch. |
| **Land surface** | `landmod.f90` | `landmod_namelist` / `landmod_nl` | Multilayer soil temperature, soil hydrology (bucket model), snow pack, river routing/runoff, and land albedos. |
| **Vegetation** | `simba.f90` (module `vegmod`) | `vegmod_namelist` / `vegmod_nl` | SIMBA dynamic vegetation, biomass/soil carbon pools, and land-surface property feedbacks. |
| **Sea interface** | `seamod.f90` | `seamod_namelist` / `seamod_nl` | Atmosphere–ice–ocean coupling frequency, open-ocean albedo, and sea-surface roughness. |
| **Sea ice** | `icemod.f90` | `icemod_namelist` / `icemod_nl` | Thermodynamic sea-ice thickness and concentration, snow on ice, and basal heat flux. |
| **Mixed-layer ocean** | `oceanmod.f90` | `oceanmod_namelist` / `oceanmod_nl` | Slab mixed-layer temperature, Q-flux heat-budget correction, horizontal diffusion, and LSG coupling switch (`NLSG`). |
| **LSG coupler & ocean** | `cpl.f90`, `lsg/src/lsgmod.f90` | `cpl_namelist` / `cplpar`, `input` / `param` | Grid interpolation, flux conservation, and 3D Large Scale Geostrophic deep-ocean integration (when compiled with LSG). |

```{note}
In historical manuals, several module groups (`FLUXPAR`, `RADPAR`, etc.) were
placed inside a single `puma_namelist` file. In PlaSim-LSG TNG, each module
reads its own `*_namelist` file listed in the table above. See
{doc}`../reference/namelist-inventory` for the complete list of accepted
parameters in each file.
```

## Ocean and sea-ice configurations

MoSt's **ML Ocean**, **Sea Ice**, and **LSG Ocean** checkboxes configure how
the ocean and sea ice evolve:

- **Prescribed vs. interactive mixed-layer ocean (`NOCEAN` in `oceanmod_nl`):**
  `NOCEAN=1` computes mixed-layer sea-surface temperature prognostically in a
  slab of depth `DLAYER` (default 50 m; note that `NLEV_OCE=1` is compiled into
  `oceanmod.f90`). `NOCEAN=0` prescribes climatological sea-surface temperatures
  from the boundary dataset.
- **Prescribed vs. interactive sea ice (`NICE` in `icemod_nl`):** `NICE=1`
  computes thermodynamic sea ice prognostically; `NICE=0` prescribes
  climatological sea ice.
- **Flux correction (`NFLUKO` and `TAUNC`):** Controls heat-flux correction
  and relaxation in the mixed-layer and sea-ice modules independently of
  whether the ocean is prognostic.
- **Coupled 3D deep ocean (`NLSG` in `oceanmod_nl`):** Selecting **LSG Ocean**
  in MoSt links the real `lsgmod.f90` and `cpl.f90` modules and sets `NLSG=1`
  (putting `NLSG=1` into a stub build has no effect). See
  {doc}`parallel-ocean` for details on LSG coupling intervals (`NAOMOD`),
  whereas `NCPL_ATMOS_ICE` in `seamod_nl` defaults to 1 atmospheric step.

## Land surface and SIMBA vegetation

- **Soil temperature and hydrology (`landmod_nl`):** `NLANDT=1` and `NLANDW=1`
  enable prognostic soil temperatures and bucket soil moisture (`NWATCINI` and
  `DWATCINI` optionally prescribe initial soil water). The planet module sets
  the default field capacity (`P_WSMAX`) before `landmod_nl` is read.
- **Dynamic vegetation (`NVEG` in `plasim_nl` and `vegmod_nl`):** SIMBA lives
  in `simba.f90` with its own `vegmod_namelist`. Although `simba.f90` is always
  compiled, interactive vegetation feedbacks are controlled at runtime by
  `NVEG` in `plasim_namelist` (MoSt sets `NVEG=0` by default; set `NVEG=1` to
  enable dynamic vegetation). Note that the turnover timescales `TAU_VEG` and
  `TAU_SOIL` in `landini` are converted using fixed 365-day Earth years.
- For complete parameter descriptions, see {doc}`../reference/parameters/landmod`
  and {doc}`../reference/parameters/vegmod`.

## Surface fluxes, moisture correction, and nudging

- **Surface exchange switches (`fluxmod_nl`):** `NEVAP` (evaporation), `NSHFL`
  (sensible heat flux), `NSTRESS` (wind stress), and `NVDIFF` (vertical
  diffusion) all default to `1`. The minimum surface wind speed parameter is
  `ZUMIN` (formerly `zumin_d` in older manuals); see
  {doc}`../reference/parameters/fluxmod` for how it enters the surface flux and
  vertical diffusion formulas.
- **Humidity correction and temperature nudging (`miscmod_nl`):** `NFIXER=1`
  enables the spectral negative-humidity mass fixer. `NUDGE=0` leaves
  atmospheric temperature nudging off (`NUDGE=1` reads `dtnudge` climatology;
  `NUDGE=2` reads `dfnudge` flux-correction data), with relaxation timescale
  `TNUDGET` (formerly `TNUDGE`).

## Sources checked

User's Guide §§2.1–2.16 compared with the modules in the table,
{repo}`plasim/src/make_plasim`, `prolog`/`gridpointd`/`epilog` in
{repo}`plasim/src/plasim.f90`, and MoSt's `WriteNamelistFile`.
Developer details on routine lifecycles and MPI array decomposition are in
{doc}`../development/architecture`.
