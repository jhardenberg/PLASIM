# Planets, calendars, and radiation settings

These features extend the older User's Guide. Select **Earth**, **Mars**,
or **Exo** through MoSt so it selects the matching compiled planet module
and boundary datasets. Copying an Earth namelist into a different compiled
planet setup is not a complete planetary conversion.

## Planet inputs and effective defaults

`planet_ini` applies presets before reading `planet_nl`. The main model
then reads its own namelist and computes derived quantities. Distinguish
module declarations, planet presets, MoSt-generated values, surface input,
and restored restart fields when identifying an effective setting.

Selected **direct Earth** presets, before MoSt/user overrides:

| Input | Meaning | Preset | Units |
| --- | --- | --- | --- |
| `psurf` | Reference mean surface pressure | 101100 | Pa |
| `ga` | Gravity | 9.80665 | m/s² |
| `plarad` | Planet radius | 6371220 | m |
| `gascon` | Dry-air gas constant | 287 | J/(kg K) |
| `solar_day` | Solar day | 86400 | s |
| `sidereal_day` | Sidereal day | 86164.0916 | s |
| `normalization_day` | Reference day for normalization | `"solar"` | selector |
| `nfixorb` | Prescribed orbital elements | 1 | switch |
| `eccen` | Eccentricity | 0.016715 | 1 |
| `obliq` | Obliquity | 23.441 | degrees |
| `mvelp` | Longitude of perihelion | 102.7 | degrees |
| `gsol0` | Solar constant | 1365 | W/m² |

For example, MoSt's generated Earth configuration writes its own `GSOL0`
and rounded orbital values; these can differ from direct presets. Read the
namelist echo and the final configuration summary in `plasim_diag`.

`PSURF` now belongs to `planet_nl`, rather than `plasim_nl`.
`SIDEREAL_YEAR` and `TROPICAL_YEAR` are no longer accepted planet parameters.
The Exo list also omits the old `ALV`, `ALS`, and `TMELT` inputs. The current
per-planet accepted names are in {doc}`../reference/namelist-inventory`.

## Dates and calendars

`N_START_YEAR` and `N_START_MONTH` in `plasim_nl` choose the cold-start date;
new Earth runs default to year 2000. A restart restores its saved timestep.

- `N_DAYS_PER_YEAR=365` selects Gregorian date handling, including leap years.
  The number 365 is a selector, not a promise that every year has 365 days.
- Other configured year lengths use the simplified equal-month calendar;
  the usual setup is 360 days with `N_DAYS_PER_MONTH=30`.
- MoSt selects the Gregorian calendar for its Earth mixed-layer setup and a
  360-day calendar when LSG is enabled. A directly launched Earth model
  otherwise starts with the 360-day preset.
- Perpetual-date controls (`NPERPETUAL` and separate ocean/ice controls)
  select a climatological day. Gregorian perpetual dates use a fixed 365-day
  climatology: day 60 is March 1. Ordinary dated runs retain leap years.

The atmospheric timestep is derived from the solar-day length and the
requested step count or minutes. Do not assume a model day is always an
86,400-second Earth day when changing planet/rotation settings. Earth-day
damping inputs and fixed-Earth-year vegetation turnover are distinct from
the model calendar. Check the parameter's actual conversion before changing it.

## Prescribed and calculated orbits

`NFIXORB=1` holds `ECCEN`, `OBLIQ`, and `MVELP` fixed. It does not disable the
seasonal or diurnal cycle. With `NFIXORB=0`, the radiation initialization
computes Berger elements for the current model year; on restart that is the
restored year. An explicit `IYRBP` in `radmod_nl` selects year `1950-IYRBP`
instead. It has no effect on the prescribed elements with `NFIXORB=1`.

The calculation occurs at initialization, not automatically at each year
boundary within one invocation. Consequently, a continuous multiyear run
and annual restart segments need not receive the same transient orbital
forcing. Record the orbital settings, initialization epoch, and restart
schedule as part of the experiment.

To reproduce the former year-1/Berger setup, explicitly select
`N_START_YEAR=1` and `NFIXORB=0`. Continuing an older transient experiment
requires preserving its intended orbital epoch as well as its restart data.

## Classic and stellar-spectrum radiation

The classic path is selected by `NSTARTEMP=0` in `radmod_nl`.
`NSTARTEMP=1` activates stellar-temperature-dependent shortwave treatment;
`STARBBTEMP` supplies a blackbody temperature in kelvin (declaration default
5772). The model uses two albedo bands separated at 0.75 µm and changes the
shortwave scattering calculation for the selected spectrum and planetary
properties.

`NSTARFILE>0` activates file-based stellar spectra and also enables
`NSTARTEMP`. `STARFILE` and `STARFILEHR` are paths to the two input spectra.
The current reader expects two-column arrays with 965 and 2048 rows,
respectively; inspect `solarini`/`readdat` and the supplied data format before
preparing a custom spectrum. `MINWAVEL` is given in nanometres. Arbitrary
spectral files are not interchangeable merely because they contain two columns.

`NSIMPLEALBEDO=1` uses the spectrum-weighted broadband albedo in both bands;
the band-specific alternative retains separate values. Snow, glacier,
ground, ocean, and sea-ice albedo arrays are not interchangeable. The
accepted albedo arrays live in the relevant land/sea groups. Several old
scalar inputs (`ALBSMAX`, `ALBSMINF`, `ALBSMAXF`, `ALBGMIN`, `ALBGMAX`) are
not accepted by today's `landmod_nl`; `ALBSMIN` remains accepted.

Broadband runs can initialize missing spectral restart fields from the
broadband state. Spectral radiation needs the appropriate saved band
records; see {doc}`restarts` before continuing an old experiment.

## Illumination and tuning

`LTIDALLY_LOCKED` in `planet_nl` enables tidally locked illumination;
`TL_SUBSTELLAR` specifies the substellar longitude in degrees. Record these
with radiation and rotation controls rather than assuming a change of
planet name implies a tidally locked setup.

Radiation initialization also applies resolution/level-dependent tuning
before reading user overrides. Values quoted in the 2011 guide are not a
complete description of the current tuned configuration. Preserve the
effective namelists, diagnostics, source revision, and reference publication
for a published experiment. The repository README's Angeloni et al. citation
is retained as supplied; no unverified final publication details are invented
here.

## Sources checked

{repo}`plasim/src/p_earth.f90`, {repo}`plasim/src/p_mars.f90`,
{repo}`plasim/src/p_exo.f90`, `readnl` in {repo}`plasim/src/plasim.f90`,
{repo}`plasim/src/calmod.f90`, `radini`/`solarini` in
{repo}`plasim/src/radmod.f90`, and current restart handling in `landmod`.
The verification ledger distinguishes source review from runtime coverage.
