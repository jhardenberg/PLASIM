# Changelog

Notable changes in the `master` branch are summarized here in a format inspired by [Keep a Changelog](https://keepachangelog.com/). This history starts with the [2014 source import](https://github.com/jhardenberg/PLASIM/commit/71bfcbf), covers the releases tagged [`1.0`](https://github.com/jhardenberg/PLASIM/releases/tag/1.0) and [`v1.0.1`](https://github.com/jhardenberg/PLASIM/releases/tag/v1.0.1), and describes the planetary developments as the planned v1.1 release. The bullets highlight changes relevant to users; the comparison links provide the full commit history.

## [v1.1](https://github.com/jhardenberg/PLASIM/compare/v1.0.1...master)

Changes on `master` since the `v1.0.1` tag.

### Main changes

- Merged planetary and exoplanet features, including stellar-spectrum radiation, spectral albedos, and tidal locking ([#13](https://github.com/jhardenberg/PLASIM/pull/13)).
- Added repository guidance for scientific compatibility, testing, documentation, and review ([#31](https://github.com/jhardenberg/PLASIM/pull/31)).

### Detailed changes

The `devel_planets` branch was merged on 2026-10-15 ([#13](https://github.com/jhardenberg/PLASIM/pull/13), [`bac0eb7`](https://github.com/jhardenberg/PLASIM/commit/bac0eb7)). Highlights:

- **Planet setup:** Harmonized Earth, Mars, and Exo parameters and added soil-water field capacity (`p_wsmax`). Added solar/sidereal damping normalization (`normalization_day`), defaulting to solar for Earth and sidereal for Mars/Exo.
- **Stellar radiation:** Added optional blackbody or supplied stellar spectra, two-band surface albedos split at 0.75 µm, and spectrum-dependent Rayleigh scattering. The default `nstartemp=0` retains classic broadband radiation.
- **Illumination and orbits:** Added tidal locking and configurable substellar longitude (`ltidally_locked`, `tl_substellar`), used `solar_day` for diurnal angles, and relaxed the former 0.1 eccentricity limit.
- **Timescales and diffusion:** Standardized physical timescales to 86,400-second Earth days and 365-day Earth years, changing vegetation/soil conversions under 360-day calendars. Ocean diffusion now uses planetary radius, including the Earth change from 6,371,000 to 6,371,220 m.
- **Namelist migration:** Moved `psurf` to `planet_namelist`; removed `sidereal_year`, `tropical_year`, and Exo inputs `alv`, `als`, `tmelt`. Removed land albedo scalars `albsmax`, `albsminf`, `albsmaxf`, `albgmin`, `albgmax` in favor of two-band arrays; classic `albsmin` remains supported.
- **Restart compatibility:** Added spectral surface and land-climatology albedo records. Broadband runs can continue older restarts using broadband fields; spectral runs require spectral records. Incomplete record pairs are rejected.
- **Output and postprocessing:** Added planetary metadata for `burn7`, retaining namelist overrides; added `nc2txt` and meridional-profile analysis; changed `burn.sh` to derive surface albedo from shortwave fluxes.
- **Resolution and boundary data:** Fixed T42 dimensions in `makesra`, added T21/T42 boundary-data script selection, and extended friction initialization and T42 convection defaults to models with at least ten vertical levels.
- **Regression tests:** Added spectral restart equality and legacy Earth restart continuation checks. Retained classic Earth and `albsmin` tests; removed tests accepting migrated or deleted inputs. Coverage remains short T21 runs.

### Subsequent changes

- **Atmosphere/LSG timing:** Aligned automatic timesteps with MoSt (T15/T21/T31/T42/T63: 60/45/30/20/15 minutes) and added automatic ten-day coupling (`NAOMOD=0`) with interval/clock validation. Older T31/T42 direct runs, T63 runs, and higher-resolution 320-step coupling inputs need timing migration; historical T31/T42 benchmarks use different workloads ([#72](https://github.com/jhardenberg/PLASIM-LSG/issues/72), [#73](https://github.com/jhardenberg/PLASIM-LSG/pull/73)).
- **T31 benchmarks:** Added optional T31/L10 mixed-layer and LSG workloads (`--resolutions T31`) with serial/MPI support. Benchmarks explicitly use MoSt timesteps: 32/48/72 steps/day at T21/T31/T42; the default resolution selection remains T21/T42 ([#71](https://github.com/jhardenberg/PLASIM-LSG/pull/71)).
- **Parallel tests and builds:** Added `tests/run_tests.py` with up to four parallel test workers by default, retained standard unittest discovery, and switched CI to four workers. Enabled parallel Make with a missing module dependency fixed; build concurrency is configurable through `PLASIM_BUILD_JOBS`.
- **Stubs and optional components:** Fixed stub diagnostics and coupling interfaces, documented optional components, and added build/run regressions for `fft991mod`, semi-Lagrangian tracer transport, and stub interfaces ([#45](https://github.com/jhardenberg/PLASIM-LSG/issues/45)).
- **Root cleanup:** Removed unused legacy files `index.html`, `make_most`, `makedebug`, and `csub.c` ([#79](https://github.com/jhardenberg/PLASIM-LSG/pull/79)).
- **Convection schemes:** Unified convection in `rainmod.f90` under `nconvection`: standard Kuo (0, unchanged default), Betts–Miller (1), MCA (2), and historical Kuo (3). Added MCA controls `rsoft`/`tadjust`, retained the `kbetta` alias, and removed duplicate scheme sources ([#45](https://github.com/jhardenberg/PLASIM-LSG/issues/45)).
- **LSG surface masks:** Added T31/T42 LSG-adapted atmospheric masks and `scripts/derive_lsg_sra.py`, resolving uncoupled ocean cells and missing velocity vectors. Added T31 support to `sra2nc` and mask regressions at T21/T31/T42 ([#20](https://github.com/jhardenberg/PLASIM-LSG/issues/20)).
- **Tools cleanup:** Removed the unused legacy `tools/` directory and its documentation CI triggers; historical utilities remain available in Git history ([#76](https://github.com/jhardenberg/PLASIM-LSG/pull/76)).
- **Repository guides:** Shortened the README around model features and quickstart instructions, linked detailed manual and benchmark guidance, and migrated `postmon.sh` documentation into the manual ([#74](https://github.com/jhardenberg/PLASIM-LSG/issues/74)).
- **MoSt run scripts:** Made generated scripts stop on model, conversion, or required-restart failures while tolerating absent optional outputs and LSG restart files. Added script regressions ([#52](https://github.com/jhardenberg/PLASIM-LSG/issues/52)).
- **Boundary timestamps:** Fixed `sra2nc` losing non-midnight timestamps; missing timestamps still map to midnight. Added conversion and round-trip regressions ([#69](https://github.com/jhardenberg/PLASIM-LSG/pull/69), [#54](https://github.com/jhardenberg/PLASIM-LSG/issues/54)).
- **Output metadata:** Corrected `srv2nc` pressure-gradient code `dpdy` to 274 and mixed-layer diagnostics 904/905 to heat-flux names and units (`W/m²`), with converter regressions ([#66](https://github.com/jhardenberg/PLASIM-LSG/pull/66), [#55](https://github.com/jhardenberg/PLASIM-LSG/issues/55)).
- **Single precision:** Fixed a radiation-reader type mismatch preventing single-precision builds and added a build/run regression. Benchmarks now support `--single-precision` and check precision compatibility in comparisons ([#64](https://github.com/jhardenberg/PLASIM-LSG/pull/64)).
- **Boundary grid detection:** Fixed `nc2sra` always selecting T21. T31/T42 inputs now retain their dimensions, and unsupported grids are rejected; added converter regressions ([#67](https://github.com/jhardenberg/PLASIM-LSG/pull/67), [#53](https://github.com/jhardenberg/PLASIM-LSG/issues/53)).
- **Compiler precision setup:** Fixed GNU Fortran version parsing, including major-only and legacy versions, and ensured precision options are generated for GNU, NAG, and fallback compilers. Added configuration regressions ([#68](https://github.com/jhardenberg/PLASIM-LSG/pull/68), [#51](https://github.com/jhardenberg/PLASIM-LSG/issues/51)).
- **Surface wind floor:** Corrected surface exchange to interpret `zumin` consistently as a wind speed in m/s. The default `zumin=1.0` is unchanged; added a nondefault regression ([#65](https://github.com/jhardenberg/PLASIM-LSG/pull/65), [#56](https://github.com/jhardenberg/PLASIM-LSG/issues/56)).
- **Testing guidance:** Expanded repository guidance for deterministic tests, MPI roundoff, tolerance selection, diagnostic-state invariance, and long-run statistical validation ([#39](https://github.com/jhardenberg/PLASIM/pull/39)).
- **Compilers and optimization:** Added Intel `ifx` support, tuned GNU/Intel production flags and native architecture selection (`MOST_ARCH_OPTS` override), fixed FFT/river-routing argument aliasing, and validated MPI compiler wrappers. Benchmarks now probe configured toolchains, record compiler flags, and check serial/MPI compatibility ([#62](https://github.com/jhardenberg/PLASIM-LSG/pull/62), [#61](https://github.com/jhardenberg/PLASIM-LSG/issues/61)).
- **User documentation:** Added a Sphinx/MyST user and developer manual with MoSt workflows, complete namelist/output references, boundary-data provenance, benchmarking, and runnable examples. Added strict builds, inventory checks, and contributor verification records; the scientific Reference Manual remains separate ([#50](https://github.com/jhardenberg/PLASIM/pull/50)).
- **Benchmark matrix:** Reduced runnable cases to classic broadband radiation with zero warmups by default; older spectral results remain readable. Added descriptive scaling reports with concurrency flags. Existing eight-case runs need their original runner or a new output directory ([#60](https://github.com/jhardenberg/PLASIM-LSG/pull/60)).
- **MPI performance:** Batched collectives and LSG coupling gathers, used neighbor exchanges for river routing, and removed redundant transforms and unused diagnostic communication. Numerical regression results remain identical; added runoff checks across MPI rank boundaries ([#57](https://github.com/jhardenberg/PLASIM-LSG/pull/57)).
- **Performance benchmarks:** Added standalone serial/MPI timing and comparison tools for mixed-layer and LSG workloads, recording variability, toolchains, inputs, and model state. Supports bounded concurrent execution, failed-case reporting, continuation, partial results, and combined summaries ([#49](https://github.com/jhardenberg/PLASIM/pull/49)).
- **MPI restarts:** Fixed an out-of-bounds solar-fraction gather and restored the serial two-value `zsolars` record layout. Added record checks and classic/spectral MPI restart comparisons ([#33](https://github.com/jhardenberg/PLASIM/pull/33)).
- **Coupled MPI comparisons:** Added maximum/RMS field-error checks to account for coupled roundoff, with physical-range checks for albedo/ice fractions. Retained mixed-layer/ocean pointwise checks, restart equality, and saved references ([#48](https://github.com/jhardenberg/PLASIM/pull/48)).
- **Orbital configuration:** Changed Earth defaults to year 2000 and `NFIXORB=1`, updating numerical baselines. With `NFIXORB=0`, initialization uses the current restart year unless `IYRBP` overrides it; `IYRBP=1950-original_start_year` preserves the previous epoch. Automatic annual orbital updates remain unsupported ([#48](https://github.com/jhardenberg/PLASIM/pull/48); [#9](https://github.com/jhardenberg/PLASIM/issues/9)).
- **Calendar fixes:** Fixed subdaily simplified-calendar conversion, perpetual-date month numbering, and Gregorian perpetual climatology (365 days; day 60 is March 1). Invalid perpetual days now stop with a diagnostic; added single/double-precision regressions ([#42](https://github.com/jhardenberg/PLASIM/pull/42)).
- **Defensive fixes:** Fixed diagnostic imports and undefined empty-mask means, hardened MoSt input/error handling, and made postprocessing paths, temporary files, and failure propagation more robust. Physical formulas and restart formats are unchanged ([#44](https://github.com/jhardenberg/PLASIM/pull/44)).
- **MPI tests:** Added two-rank T21/L10 regressions for mixed-layer and real LSG oceans, comparing atmospheric/ocean state and exchanged fluxes with serial runs. CI now installs Open MPI ([#32](https://github.com/jhardenberg/PLASIM/pull/32)).
- **MPI namelists:** Fixed broadcasts of `soilcap`, `ltidally_locked`, and `tl_substellar` for nondefault configurations. Added strict startup and two-day serial/MPI comparisons; default settings and existing default-run tolerances are unchanged ([#37](https://github.com/jhardenberg/PLASIM/issues/37), [#38](https://github.com/jhardenberg/PLASIM/pull/38)).
- **Coupled LSG tests:** Added real T21/L10 coupled regressions with daily ocean advancement, state/flux checks, and byte-equal continuous/restarted atmospheric and ocean results ([#30](https://github.com/jhardenberg/PLASIM/pull/30)).
- **Cloud diagnostics:** Restored broadband albedo after clear-sky calculations so `ndiagcf` no longer changes classic radiation. Added classic/spectral state-invariance and diagnostic-output checks ([#34](https://github.com/jhardenberg/PLASIM/issues/34), [#35](https://github.com/jhardenberg/PLASIM/pull/35)).

## [v1.0.1](https://github.com/jhardenberg/PLASIM/releases/tag/v1.0.1) — 2026-10-15

Changes from the `1.0` tag to the `v1.0.1` tag (`b093af1`), before the planetary developments were merged.

### Main changes

- Added short, reproducible T21/L10 PlaSim tests and a GitHub Actions workflow for manual runs, labeled pull requests, and pushes to `master` ([#23](https://github.com/jhardenberg/PLASIM/pull/23)).
- Added classic Earth numerical, legacy restart, and namelist compatibility checks ([#24](https://github.com/jhardenberg/PLASIM/pull/24)).
- Expanded LSG ocean setup and vertical diffusion controls, and added scripts for boundary data preparation and conversion ([2021 changes](https://github.com/jhardenberg/PLASIM/compare/1.0...6514261)).
- Added NetCDF/Service-format conversion tools and corrected latitude and grid handling ([#17](https://github.com/jhardenberg/PLASIM/pull/17), [#18](https://github.com/jhardenberg/PLASIM/pull/18), [#19](https://github.com/jhardenberg/PLASIM/pull/19)).

### Detailed changes

- **Model and coupling:** Added configurable LSG vertical diffusion parameters (`astar`, `zstar`, `arange`, `lambda`), improved initialization when `inorm=1`, added fixed bathymetry and topography helpers, and initialized sea ice from climatology ([`25cb792`](https://github.com/jhardenberg/PLASIM/commit/25cb792), [`fa6d9a5`](https://github.com/jhardenberg/PLASIM/commit/fa6d9a5), [`117c772`](https://github.com/jhardenberg/PLASIM/commit/117c772), [`ffed5aa`](https://github.com/jhardenberg/PLASIM/commit/ffed5aa), [`df6ff48`](https://github.com/jhardenberg/PLASIM/commit/df6ff48)).
- **Model and coupling:** Added an initial-surface-condition script, Service-format boundary data scripts, and configuration-file support for LSG; preserved an additional `mat77` field ([`30f73a7`](https://github.com/jhardenberg/PLASIM/commit/30f73a7), [`7451769`](https://github.com/jhardenberg/PLASIM/commit/7451769), [`ef2b170`](https://github.com/jhardenberg/PLASIM/commit/ef2b170), [`66fdcce`](https://github.com/jhardenberg/PLASIM/commit/66fdcce)).
- **Postprocessing:** Added sea-level-pressure computation and later added wind and spectral-to-grid conversion to `srv2nc` ([`6514261`](https://github.com/jhardenberg/PLASIM/commit/6514261), [`bf8f230`](https://github.com/jhardenberg/PLASIM/commit/bf8f230)).
- **Data conversion:** Added `nc2sra` and `sra2nc`, fixed the Gaussian output grid and latitude orientation, and improved their documentation and command behavior ([#17](https://github.com/jhardenberg/PLASIM/pull/17), [#18](https://github.com/jhardenberg/PLASIM/pull/18), [#19](https://github.com/jhardenberg/PLASIM/pull/19)).
- **Tests and CI:** Added calendar, deterministic two-day, and restart-consistency tests; then added a saved master Earth state fixture and checks for legacy restart and namelist inputs. CI runs on pushes, by manual dispatch, or on pull requests carrying the `run tests` label ([#23](https://github.com/jhardenberg/PLASIM/pull/23), [#24](https://github.com/jhardenberg/PLASIM/pull/24)).
- **Maintenance:** Updated README guidance for this standalone repository and made configuration more robust to locale-specific numeric formats ([`8e7e672`](https://github.com/jhardenberg/PLASIM/commit/8e7e672), [`27ab3a9`](https://github.com/jhardenberg/PLASIM/commit/27ab3a9)).

## [v1.0](https://github.com/jhardenberg/PLASIM/releases/tag/1.0) — 2020-09-18

Changes from the [original source import](https://github.com/jhardenberg/PLASIM/commit/71bfcbf) to the `1.0` tag. The original import included the version 16 model suite; the tag contains the streamlined PlaSim-focused repository and version 17 features.

### Main changes

- Introduced the version 17 model-starter and postprocessor changes listed below.
- Developed PlaSim physics and diagnostics, including a separate SIMBA vegetation module, radiation and surface-parameter fixes, and additional energy and entropy diagnostics.
- Streamlined the repository around PlaSim in 2017, while retaining its coupled LSG ocean and postprocessing workflows ([`2d1008e`](https://github.com/jhardenberg/PLASIM/commit/2d1008e)).
- Improved coupled-ocean physics, MPI portability, and data processing through the `1.0` release.

### Version 17 release notes

The original `NEW_IN_VERSION_17` file highlighted these changes to the model suite:

- Configurable planet setup in `planetmod.f90`.
- Consistent names for namelists and their files.
- Bash run scripts generated by MoSt.
- A redesigned MoSt GUI with more options.
- The new `burn7` postprocessor.

### Detailed changes

- **Planet and surface setup:** Added the Exo planet option to MoSt/PlaSim and moved vegetation initialization, namelist, and restart handling into SIMBA ([`1e29731`](https://github.com/jhardenberg/PLASIM/commit/1e29731), [`1e86243`](https://github.com/jhardenberg/PLASIM/commit/1e86243)).
- **Physics:** Corrected ozone absorption and CO₂/water-vapour band overlap, tuned radiation and land parameters, and fixed land, ice heat-flux, and artificial snow-melt behavior ([`4e4d4bf`](https://github.com/jhardenberg/PLASIM/commit/4e4d4bf), [`03cc392`](https://github.com/jhardenberg/PLASIM/commit/03cc392), [`893455c`](https://github.com/jhardenberg/PLASIM/commit/893455c), [`471f838`](https://github.com/jhardenberg/PLASIM/commit/471f838), [`dfb3411`](https://github.com/jhardenberg/PLASIM/commit/dfb3411)).
- **Physics and diagnostics:** Added automatic PlaSim timestep selection and three-dimensional energy and entropy diagnostics; fixed an entropy diagnostic initialization case ([`8992d36`](https://github.com/jhardenberg/PLASIM/commit/8992d36), [`23cf675`](https://github.com/jhardenberg/PLASIM/commit/23cf675), [`ea4d2d8`](https://github.com/jhardenberg/PLASIM/commit/ea4d2d8)).
- **Ocean coupling:** Adjusted LSG vertical diffusivity, fixed MPI gather/scatter buffer overlap, retained LSG restart files, and updated vertical diffusion and ocean/ice output defaults ([`7923ad2`](https://github.com/jhardenberg/PLASIM/commit/7923ad2), [`a475905`](https://github.com/jhardenberg/PLASIM/commit/a475905), [`0ac258e`](https://github.com/jhardenberg/PLASIM/commit/0ac258e), [`74a1602`](https://github.com/jhardenberg/PLASIM/commit/74a1602), [`4838702`](https://github.com/jhardenberg/PLASIM/commit/4838702)).
- **Restart and calendar:** Fixed PlaSim restart data used by the postprocessor and corrected the days-per-year handling in the NetCDF afterburner ([`9b7eaf5`](https://github.com/jhardenberg/PLASIM/commit/9b7eaf5), [`7efce03`](https://github.com/jhardenberg/PLASIM/commit/7efce03), [`b807308`](https://github.com/jhardenberg/PLASIM/commit/b807308)).
- **Postprocessing:** Added monthly-mean and CMORization scripts, the `burn.sh` workflow, and `srv2nc` for direct compressed NetCDF conversion of PlaSim and LSG Service output ([`9f950d8`](https://github.com/jhardenberg/PLASIM/commit/9f950d8), [`6534b44`](https://github.com/jhardenberg/PLASIM/commit/6534b44), [`f3fef0a`](https://github.com/jhardenberg/PLASIM/commit/f3fef0a)).
- **Build and interface:** Added compiler and MPI compatibility fixes, a console-only MoSt mode, resolution-switching fixes, and setup documentation ([`b149568`](https://github.com/jhardenberg/PLASIM/commit/b149568), [`a475905`](https://github.com/jhardenberg/PLASIM/commit/a475905), [`43eeeed`](https://github.com/jhardenberg/PLASIM/commit/43eeeed), [`35e3634`](https://github.com/jhardenberg/PLASIM/commit/35e3634)).

## Original source import — 2014-04-02

The repository began with an import of the version 16 MoSt/PlaSim source tree from SVN revision 46 ([`71bfcbf`](https://github.com/jhardenberg/PLASIM/commit/71bfcbf)). It already included PlaSim, PUMA, SAM, the LSG ocean, MoSt, and their documentation. See the [version 16 notes](https://github.com/jhardenberg/PLASIM/blob/71bfcbf/NEW_IN_VERSION_16) for features present at the starting point.

[Full history from the import to v1.0](https://github.com/jhardenberg/PLASIM/compare/71bfcbf...1.0) · [Full history from v1.0 to v1.0.1](https://github.com/jhardenberg/PLASIM/compare/1.0...v1.0.1) · [Full history from v1.0.1 to the v1.1 draft](https://github.com/jhardenberg/PLASIM/compare/v1.0.1...master)
