# Model components and experiment choices

This is the practical module overview from User's Guide chapter 2, updated
against the current default build. It describes responsibilities and controls;
the mathematical derivations in the separate Reference Manual are excluded.

## Atmosphere and surface

The atmosphere uses a spectral representation for its prognostic state and
a Gaussian longitude/latitude grid for physical processes. T21 has 64 × 32
grid points; T31 has 96 × 48; T42 has 128 × 64. Vertical levels and the MPI
process count are compiled settings selected through MoSt. Increasing a
number in a runtime namelist does not change the compiled resolution.

| Component | Current implementation | Main runtime file/group | Role |
| --- | --- | --- | --- |
| Dynamics and run control | `plasim.f90`, `plasimmod.f90` | `plasim_namelist` / `plasim_nl` | Initialization, time integration, dynamics, diagnostics, and restart orchestration. |
| Planet properties | `p_earth.f90`, `p_mars.f90`, or `p_exo.f90` | `planet_namelist` / `planet_nl` | Planet-specific presets and physical/orbital inputs. |
| Surface fluxes | `fluxmod.f90` | `fluxmod_namelist` / `fluxmod_nl` | Wind stress, sensible and latent heat exchange, and vertical diffusion. |
| Moist processes | `rainmod.f90` | `rainmod_namelist` / `rainmod_nl` | Large-scale/convective precipitation, cloud processes, and dry adjustment. |
| Radiation | `radmod.f90`, `specblock.f90` | `radmod_namelist` / `radmod_nl` | Shortwave/longwave radiation and optional stellar-spectrum treatment. |
| Humidity correction and nudging | `miscmod.f90` | `miscmod_namelist` / `miscmod_nl` | Negative-humidity correction and optional upper-level temperature nudging. |
| Surface input/interface | `surfmod.f90` | `surfmod_namelist` / `surfmod_nl` | Surface-field lookup and land/sea interfaces. |
| Land | `landmod.f90` | `landmod_namelist` / `landmod_nl` | Soil heat/water, snow, surface properties, and runoff. |
| Vegetation | `simba.f90` (module `vegmod`) | `vegmod_namelist` / `vegmod_nl` | SIMBA vegetation and land-surface feedbacks. |
| Sea interface | `seamod.f90` | `seamod_namelist` / `seamod_nl` | Atmosphere–ice–ocean exchange and surface properties. |
| Sea ice | `icemod.f90` | `icemod_namelist` / `icemod_nl` | Prognostic or prescribed ice and snow; exchanges with the ocean. |
| Mixed-layer ocean | `oceanmod.f90` | `oceanmod_namelist` / `oceanmod_nl` | Mixed-layer temperature, heat budgets, optional horizontal diffusion, and LSG coupling selection. |

The old guide puts several groups in `puma_namelist` under names such as
`FLUXPAR` and `RADPAR`. Those are historical: use the separate current files
above. The {doc}`../reference/namelist-inventory` is extracted from code.

## Choosing ocean and ice behavior

MoSt's **ML Ocean**, **Sea Ice**, and **LSG Ocean** choices select model
options, not just output displays. Inspect the generated inputs:

- `NOCEAN` in `oceanmod_nl` selects computed mixed-layer behavior versus
  prescribed conditions. `NICE` in `icemod_nl` selects prognostic sea ice
  versus climatological ice.
- `DLAYER` controls the mixed-layer depth in metres. The current
  `oceanmod.f90` has `NLEV_OCE=1` compiled in; an arbitrarily long namelist
  array does not turn it into a multilayer ocean.
- `NFLUKO`, `TAUNC`, and prescribed fields determine flux correction and
  relaxation. They are separate from the decision to enable an ocean model.
- `NLSG` and the compiled ocean/coupler implementations select the deep-ocean
  configuration described in {doc}`parallel-ocean`.

Sea-interface `NCPL_ATMOS_ICE` defaults to one atmospheric step in today's
code, rather than the 32 stated in the old appendix. Keep the distinct
atmosphere–ice, ice–ocean, and atmosphere–LSG intervals separate when designing
an experiment.

## Land and vegetation

Land temperature and water use `NLANDT` and `NLANDW`; optional initial soil
water uses `NWATCINI` and `DWATCINI`. The planet preset supplies `P_WSMAX`,
which initializes the soil field capacity before `landmod_nl` is read.
Surface datasets and restart state can determine spatial fields in addition
to these scalar controls.

For every land input's meaning, units, defaults, and interactions, see the
{doc}`detailed land tables <../reference/parameters/landmod>` and
{doc}`vegetation tables <../reference/parameters/vegmod>`.

SIMBA is now in `simba.f90` with its own `vegmod_nl`. The `NVEG` switch in
`plasim_nl` controls vegetation execution; a compiled SIMBA module does not
mean that vegetation feedbacks are active. In particular, MoSt writes its
own `NVEG` selection. The turnover parameters `TAU_VEG` and `TAU_SOIL` are
converted using fixed 365-day Earth years in the current land initialization.

## Fluxes, moisture, and nudging

The main flux switches `NEVAP`, `NSHFL`, `NSTRESS`, and `NVDIFF` default to
1 in `fluxmod`. The wind-floor input is named `ZUMIN`, not the old guide's
`zumin_d` spelling. Its current surface and vertical-diffusion expressions
use different speed conventions; see {doc}`../reference/parameters/fluxmod`.

In `miscmod_nl`, `NFIXER=1` enables the negative-humidity correction.
`NUDGE=0` leaves temperature nudging off; `NUDGE=1` reads the `dtnudge`
climatology, and `NUDGE=2` uses `dfnudge` flux-correction data. The accepted
timescale name is `TNUDGET`, not the historical `TNUDGE`. See the actual
conversion in `miscini` when choosing a non-Earth experiment; not every
time parameter in this model has the same normalization convention.

## Sources checked

User's Guide §§2.1–2.16 compared with the modules in the table,
{repo}`plasim/src/make_plasim`, `prolog`/`gridpointd`/`epilog` in
{repo}`plasim/src/plasim.f90`, and MoSt's `WriteNamelistFile`.
Developer details are in {doc}`../development/architecture`.
