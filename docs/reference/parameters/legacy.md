# Legacy parameter migration

This crosswalk preserves useful guidance from the User's Guide module
tables and appendix C while using current file/group names and behavior.
The detailed tables cover every accepted name in the reviewed current
implementations; this page accounts for old entries that cannot simply
be copied into those files.

## Files and groups

| Historical file/group | Current file/group |
| --- | --- |
| `puma_namelist` / `INP` | `plasim_namelist` / `plasim_nl` |
| `puma_namelist` / `PLANET` | `planet_namelist` / `planet_nl` |
| `puma_namelist` / `MISCPAR` | `miscmod_namelist` / `miscmod_nl` |
| `puma_namelist` / `FLUXPAR` | `fluxmod_namelist` / `fluxmod_nl` |
| `puma_namelist` / `RADPAR` | `radmod_namelist` / `radmod_nl` |
| `puma_namelist` / `RAINPAR` | `rainmod_namelist` / `rainmod_nl` |
| `puma_namelist` / `SURFPAR` | `surfmod_namelist` / `surfmod_nl` |
| `land_namelist` / `LANDPAR` | `landmod_namelist` / `landmod_nl`, with vegetation initialization moved to `vegmod_namelist` / `vegmod_nl` |
| `sea_namelist` / `SEAPAR` | `seamod_namelist` / `seamod_nl` |
| `ocean_namelist` / `OCEANPAR` | `oceanmod_namelist` / `oceanmod_nl` |
| `ice_namelist` / `ICEPAR` | `icemod_namelist` / `icemod_nl` |

## Moved, renamed, or removed inputs

| Historical input | Current disposition |
| --- | --- |
| `COLUMN`, `YMODE` | Not accepted in modern `plasim_nl`. |
| `MARS` in `INP` | Not accepted. Select the compiled planet through MoSt; its presets and data are separate from the planet label. |
| `PSURF` in `INP` | In `planet_nl`, with pressure in Pa. |
| `TIME0` in `INP` | Not accepted; runtime timing is controlled by the actual instrumented `NTIME` path. |
| `WW` in `PLANET` | Not accepted; derived as `2*pi/sidereal_day`. |
| `SIDEREAL_YEAR`, `TROPICAL_YEAR` | Not accepted in current planet lists. The model calendar has its own year/month controls. |
| `TNUDGE` | `TNUDGET` in `miscmod_nl`; converted using the configured sidereal day. |
| `ZUMIN_D` in descriptive flux text | Accepted name is `ZUMIN`; see {doc}`fluxmod`. |
| `GSOL0` in radiation group | In `planet_nl`, W/m². |
| `KBETTA` in appendix C | Accepted spelling is `KBETA`, with modes 0, 1, and 2. |
| `OROSCALE` in surface group | Not accepted by `surfmod_nl`; `NOROMAX` controls spectral orography truncation. |
| `NBIOME` in land group | Not accepted; vegetation execution is `NVEG` in `plasim_nl`. This does not make every old biome setting equivalent to SIMBA's current configuration. |
| `ALBSMAX`, `ALBSMINF`, `ALBSMAXF`, `ALBGMIN`, `ALBGMAX` in land group | Not accepted. Current snow/glacier band limits use `DSNOWALBMN`, `DSNOWALBMX`, and `DGLACALBMN`, including derived forest/glacier values. `ALBSMIN` remains accepted for broadband calculations. |
| `FORGROW`, `NCVEG`, `RINISOIL`, `RINIVEG` in land group | Accepted in `vegmod_nl` now. `NCVEG` multiplies carbon increments; it is not the general vegetation execution switch. |
| `GS`, `Z0_MAX`, `RLAIGROW` | Not accepted names. Current growth/conductance/roughness initialization uses `RINIDAGG`, `RINIDSC`, `RINIDMR`, and `FORGROW` in `vegmod_nl`; there is no automatic old-input translation. |
| `VDIFFK` in ocean group | Accepted input is `VDIFFKL`; the code derives interface `vdiffk` from layer values. |
| `NRESTART` in old examples | Not a current `plasim_nl` parameter; the presence of `plasim_restart` selects model-state restoration. |

## Same name, changed or incomplete historical description

- `N_START_YEAR` and `NFIXORB` now default to 2000 and prescribed orbit.
  With calculated orbits, initialization uses the restored year or explicit
  `IYRBP`; continuous and annually segmented forcing can differ.
- `NEQSIG` defaults to nonuniform levels (0), not the appendix's 1.
  `SELLON` is an integer longitude index, not a real angle in degrees.
- `TDISSQ` has a current default of
  0.1 Earth days. `TFRC` is a real array and its ≥10-level preset damps the
  first two levels. See {doc}`plasim` for array-wide legacy day detection.
- `N_RUN_YEARS`, `N_RUN_DAYS`, `MPSTEP`, and `NDIAG` have current
  initialization/default rules in {doc}`plasim`; old literal values are not
  today's defaults. Specify duration explicitly.
- `NPACKGP`/`NPACKSP` do not activate the old packed 16-bit raw writer.
  `NFLUX`, `NSURF`, and ocean `NDIAG` are accepted but lack an active
  controlling calculation branch in the reviewed default sources.
- Land `RLUE`/`CO2CONV` use current SIMBA coefficients, not the old appendix
  values. Field capacity starts from the planet, then can be spatially
  overridden. Snow depth is water equivalent; soil thermal depths are metres.
- Atmosphere–ice exchange defaults to one step, not 32. Ice/ocean `NOUT`
  defaults are derived from the caller before reading their local inputs;
  their `TAUNC` values use fixed Earth days.
- Precipitation and radiation tuning depends on compiled grid/levels.
  Current `NSHALLOW`, `GAMMA`, `TSWR*`, and `TH2OC` rules are documented in
  {doc}`rainmod` and {doc}`radmod`.

The superseded tables remain in the retained original guide for historical
context. These updates cover practical configuration information without
migrating the scientific Reference Manual's derivations.
