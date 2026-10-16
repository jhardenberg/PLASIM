# Changelog

Notable changes in the `master` branch are summarized here in a format inspired by [Keep a Changelog](https://keepachangelog.com/). This history starts with the [2014 source import](https://github.com/jhardenberg/PLASIM/commit/71bfcbf), covers the releases tagged [`1.0`](https://github.com/jhardenberg/PLASIM/releases/tag/1.0) and [`v1.0.1`](https://github.com/jhardenberg/PLASIM/releases/tag/v1.0.1), and describes the planetary developments as the planned v1.1 release. The bullets highlight changes relevant to users; the comparison links provide the full commit history.

## [v1.1](https://github.com/jhardenberg/PLASIM/compare/v1.0.1...master) — planned

Changes on `master` since the `v1.0.1` tag.

### Main changes

- Merged the planetary and exoplanet developments, including optional stellar-spectrum radiation, spectral surface albedos, and tidally locked illumination. See the feature and compatibility notes below ([#13](https://github.com/jhardenberg/PLASIM/pull/13)).
- Added repository instructions in `AGENTS.md` for scientific compatibility, testing both ocean configurations, documentation, changelog maintenance, and review ([#31](https://github.com/jhardenberg/PLASIM/pull/31)).

### Detailed changes

The `devel_planets` branch was merged on 2026-10-15 ([#13](https://github.com/jhardenberg/PLASIM/pull/13), [`bac0eb7`](https://github.com/jhardenberg/PLASIM/commit/bac0eb7)). Its changes relative to the preceding `master` include:

- **Planet setup and normalization:** Harmonized Earth, Mars, and Exo parameter handling and added planetary soil-water field capacity (`p_wsmax`). The new `normalization_day` option selects solar or sidereal day normalization for damping and dissipation coefficients. Earth defaults to `"solar"` for classic behavior; Mars and Exo default to `"sidereal"`.
- **Stellar radiation and albedos:** Added optional radiation based on a stellar blackbody temperature or supplied spectrum, two surface-albedo bands separated at 0.75 µm, and spectrum-dependent Rayleigh scattering scaled by surface pressure and gravity. The new spectral data module is included in the build. The default `nstartemp=0` retains the classic broadband radiation path; spectral behavior is enabled explicitly through the radiation namelist.
- **Illumination and orbits:** Added tidally locked illumination with a configurable substellar longitude (`ltidally_locked`, `tl_substellar`), made the diurnal-angle calculation use `solar_day`, and relaxed the former eccentricity limit of 0.1.
- **Physical timescales and ocean diffusion:** Expressed day-based physical parameter conversions in fixed 86,400-second Earth days and vegetation/soil turnover years in fixed 365-day Earth years. The latter changes their conversion in 360-day-calendar configurations. Horizontal diffusion in `oceanmod` now uses the configured planetary radius; for Earth this changes the radius from 6,371,000 to 6,371,220 m. These changes can affect enabled configurations even when the Earth planet is selected.
- **Namelist migration:** Moved `psurf` from `plasim_namelist` (`plasim_nl`) to `planet_namelist` (`planet_nl`) and removed `sidereal_year` and `tropical_year` from `planet_nl`. Exo's `planet_nl` also no longer accepts `alv`, `als`, or `tmelt`. In `landmod_nl`, the scalar controls `albsmax`, `albsminf`, `albsmaxf`, `albgmin`, and `albgmax` are no longer accepted; the spectral path uses two-band albedo arrays. The classic `albsmin` input remains supported.
- **Restart compatibility:** Added band-specific surface and land-climatology albedo records to new restarts. Broadband runs can continue older restarts without those records by initializing both bands from the broadband fields; spectral radiation requires the spectral records. Existing spectral records are read when present, and incomplete record pairs are rejected.
- **Output and postprocessing:** Added planetary radius, gravity, gas constant, and lapse rate to the Service metadata read by `burn7`, while retaining postprocessor namelist overrides. Added `nc2txt` and a meridional-profile analysis script, and changed `burn.sh` to derive surface albedo from shortwave fluxes.
- **Resolution and boundary data:** Corrected T42 dimensions in `makesra`, added T21/T42 selection to the Earth and aquaplanet boundary-data scripts, and extended the existing friction initialization and T42 convection defaults to models with at least ten vertical levels.
- **Regression tests:** Added continuous-versus-restarted equality checks in spectral radiation mode and numerical checks after continuing the legacy Earth restart. Retained the classic Earth state comparison and the `albsmin` namelist test; removed acceptance tests for the old `psurf` location and the deleted orbital-year options. These short T21 checks do not establish bitwise equality for every Earth configuration or long climate simulation.

### Subsequent changes

- **Defensive correctness:** Fixed missing diagnostic-unit imports in coupling helpers and restart equality checks, added explicit declarations and argument intents in those routines, and removed redundant interpolation assignments. Empty weighted sea masks now produce a zero diagnostic mean with a warning instead of leaving it undefined. Hardened MoSt settings/grid reads and failure cleanup. Postprocessing scripts now use repository-relative executable defaults with environment overrides, quote file paths, use private temporary directories, and propagate processing failures. Added focused model/tool regressions and X11 development headers to CI for display-free MoSt reader tests. Physical formulas, restart formats, and valid default Earth behavior are preserved; alternative rain schemes, stubs, and optional modules remain unchanged.
- **MPI tests:** Added two-rank T21/L10 runs with the real MPI module for both mixed-layer and LSG ocean configurations. Tests check rank diagnostics and compare atmospheric state, ocean state, and coupled fluxes against matching serial runs. CI now installs Open MPI and runs these tests through the existing discovery command ([#32](https://github.com/jhardenberg/PLASIM/pull/32)).
- **Coupled LSG tests:** Added a real PlaSim–LSG T21/L10 build and two-day regression run with daily coupling, checking ocean evolution and exchanged stress and heat fluxes. Added byte-equality checks between continuous and restarted runs for both components' restart files and the final day's ocean output. The existing mixed-layer tests remain in place, and unittest discovery includes both configurations in CI ([#30](https://github.com/jhardenberg/PLASIM/pull/30)).

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
