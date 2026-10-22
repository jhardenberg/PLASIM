# Runtime configuration reference

Use MoSt to prepare a consistent set of input files, then make deliberate
overrides in the copied experiment. Runtime inputs do not replace the
compiled resolution, processor count, or selected planet/ocean modules.

The tables here are a quick overview. Advanced users can consult the
{doc}`parameters/index` for a row for every accepted input, with types,
array dimensions, units, defaults, initialization precedence, and interactions.
In particular, see the complete {doc}`land parameter tables <parameters/landmod>`.

## Syntax and current group names

Each Fortran namelist file contains its matching group:

```text
&radmod_nl
 co2=360.0,
 ndcycle=0
/
```

Names are case-insensitive. Arrays may use Fortran list/repetition syntax,
for example `seed=8*1`. Character values should be quoted; logical values
use `.true.`/`.false.`. Keep array lengths within the compiled dimensions.
An unknown name or a name in the wrong group is an input error.

| File | Group | Defining source |
| --- | --- | --- |
| `plasim_namelist` | `plasim_nl` | `plasim.f90`, shared declarations in `plasimmod.f90` |
| `planet_namelist` | `planet_nl` | Selected `p_earth`, `p_mars`, or `p_exo` |
| `fluxmod_namelist` | `fluxmod_nl` | `fluxmod.f90` |
| `miscmod_namelist` | `miscmod_nl` | `miscmod.f90` |
| `surfmod_namelist` | `surfmod_nl` | `surfmod.f90` |
| `landmod_namelist` | `landmod_nl` | `landmod.f90` |
| `vegmod_namelist` | `vegmod_nl` | `simba.f90` |
| `radmod_namelist` | `radmod_nl` | `radmod.f90` |
| `rainmod_namelist` | `rainmod_nl` | Default `rainmod.f90` |
| `seamod_namelist` | `seamod_nl` | `seamod.f90` |
| `icemod_namelist` | `icemod_nl` | `icemod.f90` |
| `oceanmod_namelist` | `oceanmod_nl` | `oceanmod.f90` |
| `cpl_namelist` | `cplpar` | `cpl.f90`, real LSG build |
| `input` | `param` | `lsgmod.f90`, real LSG build |

The generated {doc}`namelist-inventory` lists every accepted name in these
implementations. It is intentionally separate from the explanatory tables:
membership is extracted automatically, while meaning and effective defaults
require initialization-path review. Alternative rain modules have separate
interfaces and are not implied by the default inventory.

## Timing and diagnostics

| Name in `plasim_nl` | Type/units | Direct source default | Use |
| --- | --- | --- | --- |
| `n_start_year` | integer year | 2000 | Cold-start date; restart clock is restored. |
| `n_start_month` | integer month | 1 | Cold-start month. |
| `n_days_per_year` | integer selector/day count | 360 for direct Earth | 365 selects Gregorian; usual simplified calendar is 360. |
| `n_run_years`, `n_run_months` | integer calendar intervals | 0 | Month/year countdown. MoSt writes a duration. |
| `n_run_days`, `n_run_steps` | integer model days/steps | 0 | Short-run step countdown; do not mix stopping conventions casually. |
| `mpstep` | integer minutes | 0, automatic | Requested step; T21 Earth automatic selection is 45 minutes. |
| `ntspd` | integer steps/day | 0 before initialization | Derived or supplied steps per solar day. |
| `noutput` | integer switch | 1 | Enable atmospheric output. MoSt can override it. |
| `nwpd` | integer writes/day | 1 | Used to derive the output interval in atmospheric steps. |
| `ndiag` | integer atmospheric steps | 0, automatic | Diagnostic interval; nonpositive values become ten model days. |
| `ndiagcf` | integer switch | 0 | Additional clear-sky cloud-radiation diagnostics. |
| `nenergy`, `nentropy` | integer switches | 0 | Additional budget diagnostics and code ranges. |
| `kick` | integer selector | 1 | Initial perturbation mode; zero disables noise. |
| `seed` | integer array(8) | all zero | Fixed nonzero first element selects explicit initialization. |
| `ngui` | integer switch/interval | 0 | Simulation GUI; build through MoSt for a matching implementation. |
| `neqsig` | integer selector | 0 | Vertical-coordinate choice; the old appendix's value 1 is not today's declaration default. |

The full direct-Make example provides {ref}`headless-parameters` and a
verified relation between step length and run duration. For production runs,
check the effective values in the diagnostic echo and generated run script.

## Surface, physics, and ocean controls

Selected controls below are declaration defaults unless a preset/override
is stated. They are not a replacement for the complete accepted-name inventory.

| Group | Controls | Meaning and source defaults |
| --- | --- | --- |
| `fluxmod_nl` | `nevap`, `nshfl`, `nstress`, `nvdiff` | Surface evaporation, sensible heat, stress, vertical diffusion: all 1. |
| `fluxmod_nl` | `ntsa`, `zumin`, `vdiff_lamm` | Near-surface temperature choice 2, minimum wind speed 1 m/s, mixing length 160 m. |
| `miscmod_nl` | `nfixer`, `nudge`, `tnudget` | Humidity correction 1; nudging 0; temperature-nudging timescale input 10 sidereal-day multiples, converted in `miscini`. |
| `surfmod_nl` | `nspinit`, `nsurf`, `noromax` | Surface/spectral initialization controls; `noromax` starts at compiled `NTRU`. |
| `landmod_nl` | `nlandt`, `nlandw` | Prognostic land temperature and soil water: both 1. |
| `landmod_nl` | `soilcap` | Soil volumetric heat capacity, 2.4e6 J/(m³ K). |
| `landmod_nl` | `wsmax`, `nwatcini`, `dwatcini` | Field capacity initialized from planet `p_wsmax`; optional explicit soil-water initialization defaults off. Water-depth inputs are metres. |
| `landmod_nl` | `tau_veg`, `tau_soil` | 10 and 42 fixed 365-day Earth years, converted to seconds. |
| `radmod_nl` | `co2`, `ndcycle`, `no3` | CO₂ 360 ppmv; diurnal cycle 0; ozone selection initialized in the planet/radiation path. |
| `radmod_nl` | `nstartemp`, `nsimplealbedo`, `starbbtemp` | Classic path 0; broadband-in-both-bands selection 1; blackbody temperature 5772 K. |
| `seamod_nl` | `ncpl_atmos_ice` | Atmosphere–ice exchange interval: one atmospheric step. |
| `seamod_nl` | `albsea`, `dz0sea`, `dz0ice` | Sea albedo 0.069; roughness lengths 1.5e-5 and 0.001 m. Spectral behavior also uses band arrays. |
| `icemod_nl` | `nice`, `nfluko`, `ncpl_ice_ocean` | Ice selection, flux correction, and ice–ocean coupling interval; keep these distinct from atmospheric/LSG intervals. |
| `oceanmod_nl` | `dlayer`, `vdiffkl`, `hdiffk` | Declared mixed-layer depth 50 m, vertical diffusivity 1e-4 m²/s, horizontal diffusivity 1e5 m²/s. Activation switches and layer count matter. |
| `oceanmod_nl` | `nlsg`, `naomod` | LSG mode 0; exchange interval 0 selects ten atmospheric days, resolved using the actual timestep. Requires the real coupled build when enabled. |

## Migrating old inputs

| Historical guide/input | Current behavior |
| --- | --- |
| `puma_namelist` containing `INP`, `PLANET`, `RADPAR`, `FLUXPAR`, etc. | Use the separate file/group pairs above. |
| `PSURF` in `plasim_nl` | Accepted in `planet_nl`. |
| `TNUDGE` in a miscellaneous group | Current name is `TNUDGET` in `miscmod_nl`. |
| `ZUMIN_D` | Current flux-group name is `ZUMIN`. |
| `VDIFFK` in the ocean appendix | Current input is `VDIFFKL`; inspect its layer dimension. |
| Scalar `ALBSMAX`, `ALBSMINF`, `ALBSMAXF`, `ALBGMIN`, `ALBGMAX` in `landmod_nl` | Not accepted; use the current band-array interface where appropriate. `ALBSMIN` remains accepted. |
| `SIDEREAL_YEAR`, `TROPICAL_YEAR` in `planet_nl` | Removed from current lists. |
| `COLUMN`, `YMODE` macro setup | Not accepted in modern `plasim_nl`. |
| `NRESTART` copied from an old example | Restart selection comes from the input restart file; it is not a current `plasim_nl` parameter. |
| Old `gsol0` location/default | Accepted in `planet_nl`; direct presets and MoSt values can differ. |

## Sources checked

User's Guide module tables and appendix C compared with every active
namelist declaration in the inventory, the corresponding initialization
routines, planet presets, and MoSt `WriteNamelistFile`. Important effective
settings depend on the selected path; inspect their initialization code when
using combinations beyond the examples.
