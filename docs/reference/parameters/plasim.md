# Atmosphere and run control: `plasim_nl`

File: `plasim_namelist`. Read by `readnl` in
{repo}`plasim/src/plasim.f90`; declarations are in
{repo}`plasim/src/plasimmod.f90`. Defaults below are direct-build defaults,
before MoSt/user overrides. The selected planet initializes the calendar
and mean ground temperature first.

## Clock, run duration, and initialization

```{table}
:class: parameter-table
:widths: 15 20 18 47

| Parameter | Type; input units | Default | Meaning and interactions |
| --- | --- | --- | --- |
| `n_start_year` | integer; calendar year | 2000 | Cold-start year; restart state restores its own timestep/date. |
| `n_start_month` | integer; month | 1 | Cold-start month, starting at day 1 at midnight. |
| `n_days_per_year` | integer; selector/day count | Earth/Exo 360; Mars 660 | 365 selects Gregorian dates with leap years; other lengths use the simplified calendar. MoSt normally writes 365 for Earth without LSG and 360 with LSG. Rotation scaling can change this before calendar initialization. |
| `n_days_per_month` | integer; days | Earth/Exo 30; Mars 55 | Month length for the simplified calendar and climatological interpolation. Keep the year/month settings consistent. |
| `n_run_years` | integer; years | 0 | Added to `n_run_months` as `12*n_run_years`; specifies duration of this invocation, including on restart. |
| `n_run_months` | integer; months | 0 | Calendar-month countdown. Prefer this or the day/step countdown, not both: a positive day/step countdown returns immediately when exhausted, even if requested months remain; the durations are not added together. |
| `n_run_days` | integer; model solar days | 0 | Converted to `n_run_days*ntspd+n_run_steps` for the short-run countdown. |
| `n_run_steps` | integer; full steps | 0 | Extra steps in the short-run countdown. Supply a positive duration explicitly. |
| `mpstep` | integer; minutes | 0, automatic | Positive values determine `ntspd` using the configured solar day and round the count to an even integer. Automatic presets match MoSt: T15 60 min, T21 45, T31 30, T42 20, T63 15. Other grids retain 45 min below T21, 30 up to 48 latitudes, otherwise `(30*64)/NLAT`. Actual step seconds are `solar_day/ntspd`. |
| `ntspd` | integer; steps/solar day | 0, automatic | Used directly when positive and `mpstep<=0`. Positive `mpstep` takes precedence. Do not supply inconsistent values assuming both remain effective. |
| `nperpetual` | integer; climatological day | 0 | Zero follows the dated annual cycle; positive values fix the day used by radiation and relevant climatological interpolation. Gregorian perpetual dates use a 365-day climatology. Ocean and ice have separate controls. |
| `kick` | integer; selector | 1 | Cold-start log-pressure perturbation: 0 none; 1 white noise; 2 equator-symmetric white noise; 3 a prescribed spectral perturbation. At T1, values above 2 are reset to zero. |
| `seed` | integer array(8); seed values | 0 | If the first element is nonzero, supplies explicit random initialization; zero selects automatic seeding. Keep all eight entries with reproducible experiments. |
| `nkits` | integer; count | 3 | Number of shortened startup steps before ordinary leapfrog stepping; not additional requested full run days. |
| `naqua` | integer; mode | 0 | Nonzero selects aquaplanet surface initialization; `naqua=1` also sets `nveg=0` in `readnl`. Requires appropriate boundary/forcing choices. |
| `nveg` | integer; switch | 1 | Positive enables SIMBA initialization and stepping; MoSt writes its own vegetation selection. See {doc}`vegmod`. |
```

## Dynamics and vertical structure

```{table}
:class: parameter-table
:widths: 15 20 18 47

| Parameter | Type; input units | Default | Meaning and interactions |
| --- | --- | --- | --- |
| `nadv` | integer; switch | 1 | Controls advective/dynamical tendency branches in `spectrala`/`spectrald`. |
| `nhordif` | integer; switch | 1 | Zero clears restoration, Rayleigh friction, and all four diffusion timescale arrays during `readnl`, in addition to disabling horizontal diffusion coefficients. |
| `nhdiff` | integer; wavenumber | 15; T42 16 | Critical total wavenumber above which the spectral diffusion weighting grows; keep below `NTRU` for the denominator used in initialization. This is not ocean `nhdiff`. |
| `ndel` | integer array(NLEV); exponent | 2; T42 4 | Power of the wavenumber-distance weighting for spectral diffusion at each level. |
| `tdissd` | real array(NLEV); seconds or legacy days | 0.20 days; T42 0.06 days | Divergence diffusion timescale; see conversion convention below. Positive values enable damping. |
| `tdissz` | real array(NLEV); seconds or legacy days | 1.10 days; T42 0.30 days | Vorticity diffusion timescale. |
| `tdisst` | real array(NLEV); seconds or legacy days | 5.60 days; T42 0.76 days | Temperature diffusion timescale. |
| `tdissq` | real array(NLEV); seconds or legacy days | 0.10 days | Specific-humidity diffusion timescale; the historical appendix's 5.6 is stale. |
| `restim` | real array(NLEV); seconds or legacy days | 0 | Temperature-restoration timescale toward the prescribed reference state; nonpositive values disable it at that level. |
| `tfrc` | real array(NLEV); seconds or legacy days | 0; for NLEV≥10: first two 20, 100 Earth days | Rayleigh-friction timescale. Remaining levels are zero; the current setup differs from the old bottom-layer example. |
| `neqsig` | integer; selector | 0 | 0 uses the built-in nonuniform half-level profile; 1 uses `jlev/NLEV`; −1 uses user `sigh`. |
| `sigh` | real array(NLEV); sigma fraction | 0 | Half-level coordinates when `neqsig=-1`; provide a complete consistent vertical grid ending at the surface. Other modes compute their own grid. |
| `t0` | real array(NLEV); K | 250 | Reference temperature profile used by the semi-implicit dynamics; converted internally to nondimensional temperature. |
| `tgr` | real; K | Earth/Exo 288; Mars 210 | Mean ground temperature defining the reference vertical profile and orographic pressure initialization. |
| `dtrop` | real; m | 12000 | Tropopause height in the reference-temperature construction. |
| `dttrp` | real; K | 2 | Smooths the reference-temperature transition near the tropopause. |
| `dtep` | real; K | 0 | Equator-to-pole reference-temperature contrast coefficient in `setzt`; affects imposed restoration state rather than directly fixing prognostic temperatures. |
| `dtns` | real; K | 0 | North–south asymmetry coefficient of the reference/restoration temperature. |
| `ndheat` | integer; selector | 1 | Positive adds momentum-dissipation heating; values above 1 also enable additional efficiency diagnostics. Affects the radiation tuning branch chosen before its namelist is read. |
| `nsponge` | integer; switch | 0 | Positive relaxes top-level temperature toward the second level, using `dampsp`; requires at least two levels. |
| `dampsp` | real; seconds or legacy days | 0 | Positive sponge timescale; values below one model timestep are interpreted as Earth days and converted before normalization. Only acts with `nsponge>0`. |
| `nsela` | integer; switch | 0 | Positive initializes the semi-Lagrangian tracer path and enables its transport calls. |
| `nqspec` | integer; representation | 1 | 1 transports humidity spectrally; 0 uses the alternate gridpoint humidity path. Coordinate this with transport options rather than changing output interpretation alone. |
| `nrad` | integer; switch | 1 | Positive calls `radstep`; zero skips it. Radiation component switches remain in {doc}`radmod`. |
| `nflux` | integer; legacy control | 1 | Accepted and broadcast, but has no active calculation branch in the current default sources. Control exchange/diffusion with the actual {doc}`fluxmod` switches. |
```

`initpm:dayseccheck` examines each whole timescale array: if its maximum
is positive and below `solar_day/ntspd`, it multiplies the **entire array**
by 86400, interpreting the values as fixed Earth days. Larger values are
treated as seconds. Avoid mixing seconds and day-valued entries in one
array. T42 presets are already set in seconds before the namelist read.
The conversion to nondimensional damping then uses the selected
`normalization_day`, solar for classic Earth and sidereal for Mars/Exo.

## Output, diagnostics, and GUI

```{table}
:class: parameter-table
:widths: 15 20 18 47

| Parameter | Type; input units | Default | Meaning and interactions |
| --- | --- | --- | --- |
| `noutput` | integer; switch | 1 | Enables atmospheric output and is passed to the sea modules as their master output switch. |
| `nnetcdf` | integer; switch | 0 | Output format switch. `0` writes classic binary Service format (`plasim_output`). `1` writes direct compressed NetCDF-4 (`plasim_output.nc`). |
| `noutput_avg` | integer; code | 1 | Time-averaging mode for NetCDF output when `nnetcdf = 1`. `1` computes true 24-hour daily averages across all timesteps in each calendar day (`ntspd` steps, integrating the diurnal cycle; `nwpd` is ignored). `2` computes monthly averages across all timesteps in the calendar month (`nwpd` is ignored). `0` writes instantaneous snapshots at interval `ntspd / nwpd` governed by `nwpd`. |
| `ndeflate` | integer; level (0–9) | 4 | NetCDF-4 deflate (zlib compression) level for direct NetCDF output (`0` = no compression, `9` = maximum compression). |
| `nwpd` | integer; writes/day | 1 | Writes per model day. Sets output interval to `ntspd / nwpd` steps for classic Service format (`nnetcdf = 0`) and for instantaneous NetCDF output (`nnetcdf = 1, noutput_avg = 0`). Ignored when NetCDF daily (`noutput_avg = 1`) or monthly (`noutput_avg = 2`) averaging is active. |
| `ndiag` | integer; steps | 0 → `10*ntspd` | Diagnostic interval; nonpositive input becomes ten model days. |
| `ndiagcf` | integer; switch | 0 | Enables clear-sky radiation/cloud-forcing diagnostic fluxes; adds output fields. |
| `ndiaggp` | integer; switch | 0 | 1 enables the built-in gridpoint tendency diagnostics and adds 21 to `ndiaggp3d`. |
| `ndiaggp2d` | integer; count | 0 | Additional two-dimensional gridpoint diagnostic arrays. Must agree with their producing code. |
| `ndiaggp3d` | integer; count | 0 | Additional three-dimensional gridpoint diagnostic arrays, before the built-in increment. |
| `ndiagsp` | integer; switch | 0 | 1 enables built-in spectral diagnostics and adds 3 to `ndiagsp3d`. |
| `ndiagsp2d` | integer; count | 0 | Additional two-dimensional spectral diagnostic arrays. |
| `ndiagsp3d` | integer; count | 0 | Additional three-dimensional spectral diagnostic arrays, before the built-in increment. |
| `nenergy` | integer; switch | 0 | Positive enables energy-budget diagnostics. |
| `nener3d` | integer; switch | 0 | Positive allocates/stores level-resolved energy diagnostics; use with the associated energy calculations. |
| `nentropy` | integer; switch | 0 | Positive enables entropy-budget diagnostics. |
| `nentro3d` | integer; switch | 0 | Positive allocates/stores level-resolved entropy diagnostics; use with the associated entropy calculations. |
| `nprint` | integer; debug selector | 0 | Additional model/module diagnostic printing; not an output sampling interval. |
| `nprhor` | integer; grid index | 0 | Selects a horizontal point for debugging routines; meaningful range depends on the routine's local/global layout. |
| `ncoeff` | integer; count | 0 | Number of spectral coefficients printed by `prisp`. |
| `ndl` | integer array(NLEV); switches | 0 | Nonzero selects a level for spectral diagnostic printouts in `wrspam`. |
| `ntime` | integer; switch | 0 | 1 collects timing diagnostics in the instrumented routines. |
| `npackgp` | integer; retained flag | 0 | Accepted historical gridpoint packing flag. Current raw writers use 32-bit records; this does not activate the old 16-bit packed output. |
| `npacksp` | integer; retained flag | 0 | Corresponding spectral packing flag; same current writer limitation. |
| `ngui` | integer; switch/steps | 0 | Positive enables the compiled simulation GUI; also used as an interval for GUI-related diagnostic calls. Zero disables it. Requires the matching GUI build. |
| `nguidbg` | integer(kind=4); switch | 0 | Enables GUI debugging printouts in the GUI implementation. |
| `sellon` | integer; one-based longitude index | 1 | Longitude selected for sounding/column display; the GUI presents a degree value and converts it to this index. |
| `nsync` | integer; synchronization mode | 0 | Controls the multi-instance synchronization path; the historical PlaSim–PUMA two-instance recipe also requires a separate PUMA executable absent here. |
| `syncstr` | real; nondimensional tendency coefficient | 0 | Strength multiplying synchronized state differences. Positive `synctime` replaces it with `1/(2*pi*synctime)`. |
| `synctime` | real; normalized day multiples | 0 | Positive values derive `syncstr`; this expression does not multiply by 86400. The integration uses `delt=2*pi/ntspd`, so the discrete relaxation uses model-day multiples. Zero leaves explicit strength effective. |
```

Sources checked beyond the reader: `initpm`, `master`, `noise`, `setzt`,
`gridpointd`, `spectrala`/`spectrald`, output writers, and GUI routines.
This is a reference for accepted controls, not validation of every possible
combination of diagnostic counts and experimental transport options.
