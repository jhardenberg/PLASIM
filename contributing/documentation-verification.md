# Documentation verification ledger

Contributor record retained outside the published Sphinx manual. Documentation
maintenance, this ledger, and migration coverage are kept in `contributing/`;
clean HTML/search/LaTeX builds omit their former manual pages.

The historical User's Guide is source material, not the current interface
specification. This migration compares its practical claims with the actual
code. The initial migration reviewed model sources at `9c47096`; subsequent
updates check the merged developments identified below, including mainline
`f924ab9` for the MPI and benchmark updates. This documentation PR does not
change model sources. Source checks and runtime checks below are deliberately
distinguished.

## Historical chapter coverage

| Original material | Current Sphinx destination | Code comparison and resulting update |
| --- | --- | --- |
| Chapter 1: installation/build/run | User: MoSt and experiment directories | `configure.sh`, `cleanplasim`, MoSt `main`, `ReadSettings`, `Build`, `WriteNamelistFile`, `SaveExit`, `SaveRun`, `WriteRunScript`: headless mode prepares only; model GUI remains a separate setting; `most_plasim_run` structure (`EXP`, `YEAR1`/`YEAR2`, `average="-m"`, `srv2nc`, `output/` and `restart/` archiving, `plasim_status` $\rightarrow$ `plasim_restart` handoff, and initial `rm -f plasim_restart`) documented step by step against `WriteRunScript`. |
| Chapter 2: module overview | User: components; developer: architecture | Actual default `make_plasim` variants and lifecycle calls replace obsolete PUMA/module/group references; SIMBA has `vegmod_nl`; sea exchange declaration default is one step. |
| Chapter 3: parallel execution | User: parallel/LSG; developer: architecture/testing | `resmod`, shared dimensions, `mpimod`, and MoSt core checks: compiled rank count, latitude divisibility, padded spectral layout; no manual `use mpi` editing recipe. |
| Chapter 4: GUI | User: GUI | `pumax.c:ReadConfig`, plot/palette registries, `guimod`, and sent arrays: file precedence, actual names/scaling, and separate X11 dependencies; old PUMA editors are not promoted as PlaSim workflows. |
| Chapter 5: postprocessor | User: postprocessing; reference: output | `burn7.cpp:Usage`, `parini`, option parser, `InitAll`, writers; `srv2nc` branches: direct CDO conversion now exists, current horizontal/vertical defaults are G/P, `-g` is GrADS, wind codes are 131/132. |
| Chapter 6: graphics | User: visualization | Retained CDO inspection and replaced the GrADS/Vis5D recipes with an xarray/Matplotlib map. Checked `srv2nc` code 167, kelvin units, and Gaussian `lon`/`lat` coordinates; the literal-included Python script uses the first output sample without further averaging or conversion. |
| Chapter 7: columns/soundings | Excluded from manual | Obsolete `COLUMN`/`YMODE` macro and single-column experiment recipe omitted from the manual as unsupported in PlaSim-LSG TNG. |
| Appendix A: symbols/constants | Reference: units; user: planets | Shared dimension formulas and current planet presets replace rounded old constants. Derivation-only notation stays with the excluded scientific Reference Manual. |
| Appendix B: output codes | Reference: output and output variables inventory | Literal current `writegp`/`writesp`/`mpwritegph` and `outpostsrv`/`outsurf` calls cross-referenced with Appendix B, `variable_list.txt`, and `srv2nc`: documented variable short names, full descriptive names, declared units, source arrays, levels, and writers across atmosphere, ice, mixed-layer ocean, LSG deep ocean, and derived diagnostics. |
| Appendix C and chapter 2 parameter tables | Reference: overview, detailed tables, legacy crosswalk, and accepted-name inventory | Every active default/planet/coupler/LSG member has a descriptive row: type/dimensions, units, pre-read default, active use, overrides, and retained/inactive controls. Old entries absent from current interfaces have explicit migration dispositions. |
| Ice-output sheet | Reference: output and writer inventory | `icestep`/`iceout`: current arrays and extra code 792 included; diagnostic residual expression retained without asserting universal closure of old budget equalities. |
| `variable_list.txt` and `srv2nc` parameter tables | Reference: output and output variables inventory | Variable names, descriptive labels, and declared units unified into `docs/reference/raw-output.md` with Fortran source arrays and writers, eliminating the redundant separate conversion metadata table. Documented LSG negative Service code convention, staggered Arakawa E-grid, and vertical depth levels. |
| README and FAQ | User chapters and troubleshooting | Current workflow, orbital/default/restart migrations, postprocessors, test policy, and supported versus historical recipes integrated. |
| Surface-data recipes in chapter 2/7 and Reference Manual chapter 8 | User: boundary data | Reference Manual chapter 8, `surface_ini`/`surfini`, and `get_surf_array`: documented all 15 standard Earth `.sra` files and 14 optional/diagnostic files, code module usage (`landmod`, `oceanmod`, `icemod`, `simba`, `radmod`, `miscmod`), original data sources (USGS GTOPO30, USGS LSP / Hagemann, MODIS / Rechid, AMIP-II / Taylor), land-to-sea flood-fill modifications, and mask clipping to 0–1. |

## Recent development coverage

The opening pages identify PlaSim-LSG TNG and its `jhardenberg/PLASIM`
repository. Their brief improvement summary follows the changelog's
planetary, physics/ocean-coupling, workflow, and testing developments;
historical authorship remains attributed to the original model.
The Sphinx sources and examples now live in the root `docs/` directory;
historical PDFs and reference files remain in `plasim/doc`. Build commands,
Read the Docs dependencies, source-inventory paths, and download links use
this layout.
The LSG highlight reflects the tuned vertical-diffusion settings in
`lsg/src/lsgmod.f90`, the exchanges in `plasim/src/cpl.f90`, and the real
coupled-model regression coverage in `tests/test_lsg.py`.

The benchmarking chapter adapts `benchmarks/README.md`. Source checks cover
`run.py`'s `arguments`, `build`, `prepare`, `execute`, `schedule`,
`state_summary`, `continuation_differences`, and result-writing paths, plus
`compare.py`'s loading, comparison, summary-compatibility, and scaling paths.
Timer descriptions also check `mksecond` in `plasim/src/plasim.f90` and the
root-rank timer calls in `radmod.f90`. These checks establish the documented
protocol and reporting behavior; timings are not new performance claims.

The brief MPI-performance note follows merged PR #57, checking the current
multi-level exchanges in `mpimod.f90`, river-routing calls in `landmod.f90`,
global-mean helpers in `legmod.f90`/`plasim.f90`, and coupled exchanges in
`oceanmod.f90`. It makes no fixed speedup claim. The PR #60 benchmark update
checks `CASES`, `prepare`, and `arguments` in `run.py`, and `summarize` in
`compare.py`: classic-only runnable cases, zero default warm-ups, retained
legacy-result reading, and descriptive scaling with concurrency flags and
warnings. The current `benchmarks/README.md` is the companion guide.

The planet/radiation chapter checks the selected `p_*` modules, `readnl`,
`radini` and stellar-spectrum code against recent README/changelog entries:
year-2000/fixed-orbit defaults; initialization-time orbital epoch and IYRBP;
Earth-day versus calendar conventions; stellar temperature/file inputs;
two-band albedos; tidal locking; moved namelist fields; and spectral restart
compatibility. LSG coverage checks the real coupler, `param` reader, derived
ocean timestep, and tests rather than treating a stub build as coupled.

This is a practical source-checked migration, not an independent scientific
review of the physical parameterizations. The complete mathematical
Reference Manual remains excluded. The detailed namelist tables explain all
302 input entries across 14 interfaces (348 memberships including the three
planet variants); the extracted list and coverage check establish membership,
not independent verification of scientific meaning or valid combinations.

## Detailed parameter checks

- `plasim_nl`: shared declarations, `readnl`, `initpm`/`dayseccheck`, `master`,
  `noise`, `setzt`, spectral tendencies, output and GUI calls. Recorded
  resolution-dependent presets, duration interaction, array-wide day/second
  detection, and accepted flags without active calculation branches.
- `planet_nl`: all three `planet_ini` variants plus rotation/calendar and
  radiation initialization; one explanatory table includes all preset differences.
- `landmod_nl`/`vegmod_nl`: declarations, `landini`, `tands`, `mktsoil`,
  `wandr`, `soilini`/`soilstep`, `vegini`/`vegstep`, surface loads, and restart
  restoration. Checked thermal depths, water thresholds, spectral arrays,
  carbon coefficients, acceleration, and initialization precedence.
- Flux/misc/surface: `fluxini`, `surflx`, `vdiff`, `miscini`/`mknudge`, and
  `surfini`. Recorded the actual wind-floor expressions, rotation-based
  nudging conversion, orography truncation, and retained surface flag.
- Radiation/rain: declarations and pre-read tuning in `radini`/`rainini`,
  `solarini`, `solang`, `mko3`, `swr`, `lwr`, `kuo`, `mkclouds`, and
  precipitation evaporation. Distinguished coefficients, fractions, angles,
  absorber conventions, spectrum shapes, and level-dependent defaults.
- Sea/ice/ocean: initialization and stepping, actual step counters,
  output/modulo intervals, climatology interpolation, flux corrections,
  horizontal/vertical diffusion, and LSG exchange. Local timing defaults
  are inherited before the corresponding namelist reads.
- Coupler/LSG: `clsgini`, getters/setters, `cinter`/`cinter2`, `conserve`,
  `croffc`, correction/blend routines, `inipar`, `inigr`, BBL, `set_quick`,
  `readbou`, and step/output calls. Recorded inactive standalone-era controls,
  required output interval, shipped-file overrides, and diffusion presets.

These are source checks; documenting all accepted controls does not mean
each nondefault parameter combination has been exercised at runtime.

## Runtime evidence and limits

| Check | Evidence/scope |
| --- | --- |
| Direct-Make example | Exact CI script built and ran T21/L10 for two days; checked final step, dimensions, and finite selected temperature state. |
| MoSt preparation | `configure.sh` built MoSt; supplied headless configuration prepared the expected executable, Gregorian/year-2000 inputs, and run script without starting a simulation. Local compiler setup was affected by separately tracked issue #51. |
| MoSt annual run | Twelve months of 2000 completed; atmospheric/ocean/ice NetCDF output and restart were nonempty; CDO confirmed twelve monthly atmospheric records and final state was finite. Script status is separately tracked in issue #52. |
| Converter checks | CDO inspection on real annual output plus synthetic grid/time/code cases. Discrepancies are filed in separate issues, without implementation changes here. |
| Benchmarking | Exact optional T21 smoke script built and ran serial mixed-layer and real LSG cases for ten days each. Checked finite selected state, atmospheric step count, one LSG step, summary/comparison commands, and continuation without repeating completed samples. The updated script uses the zero-warmup default and both classic cases; summary JSON flags and all 22 existing runner tests passed. T42, MPI, and concurrent model benchmarks were reviewed from source rather than newly run for this chapter; legacy spectral-result handling is covered by the runner tests. No speedup or scaling claim is made. |
| Python map | Exact `plot-temperature.py` rendered converted T21 Earth `tas` output (12 times, 32 Gaussian latitudes, 64 longitudes, K). PNG labels, orientation, color scale, and layout inspected. A derived single-time fixture using a CF 360-day calendar in year 1 also rendered successfully. Optional packages tested in an isolated environment: xarray 2026.9.0, Matplotlib 3.11.2, netCDF4 1.7.5, cftime 1.6.6.1. |
| GUI | Reader/field/plot behavior checked from source; interactive X11 operation not exercised. |
| burn7 | Source/interface review; legacy NetCDF C++ dependency unavailable for runtime validation. |
| Other planets | Relevant inputs and paths checked from source; no claim of new climate validation. |
| Parameter coverage | All 348 memberships across the 16 reviewed source variants have descriptive rows. Isolated checker trials reject missing, extra, duplicate, and incomplete rows. Types/units/defaults/semantics were reviewed separately against code, not inferred by the checker. |
| Sphinx | Strict HTML and LaTeX-source builds, reference-inventory consistency, and 3071 local link targets (including anchors/downloads) plus 284 asset references across 47 HTML pages passed after moving contributor notes outside the published manual. Read the Docs theme, PlaSim-LSG TNG opening pages, grouped sidebar navigation, breadcrumbs, and detailed table layouts reviewed in HTML; each chapter has exactly one toctree parent. External checking reached valid pages but GitHub throttled some requests with HTTP 429; a complete external-link pass was not obtained. Compiled PDF layout not validated. |

## Issue-only follow-up

Implementation findings are tracked outside this manual; no fixes or
workaround instructions are part of the migration:

- [#51](https://github.com/jhardenberg/PLASIM/issues/51): GNU Fortran version/precision-file detection.
- [#52](https://github.com/jhardenberg/PLASIM/issues/52): generated run-script status handling.
- [#53](https://github.com/jhardenberg/PLASIM/issues/53): NetCDF-to-SRA grid selection.
- [#54](https://github.com/jhardenberg/PLASIM/issues/54): SRA-to-NetCDF timestamps.
- [#55](https://github.com/jhardenberg/PLASIM/issues/55): converter code/unit metadata.
- [#56](https://github.com/jhardenberg/PLASIM/issues/56): inconsistent wind-speed dimensions in the two `ZUMIN` uses.

When extending this ledger, identify the source routine and the behavior
actually checked. Update descriptions to match code when old information
is stale. If the code reveals a suspected bug, reproduce it where practical
and report it separately instead of silently correcting the implementation
or documenting intended behavior as if it were current.
