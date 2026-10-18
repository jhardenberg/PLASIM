# Planet properties: `planet_nl`

File: `planet_namelist`. MoSt selects one compiled `planet_ini` from
{repo}`plasim/src/p_earth.f90`, {repo}`plasim/src/p_mars.f90`, or
{repo}`plasim/src/p_exo.f90`. Each currently accepts the same 23 names.
The defaults here are presets **before** reading this file; MoSt's generated
values can override them. Selecting `yplanet` alone does not replace the
compiled planet module or its boundary data.

```{table}
:class: parameter-table
:widths: 15 20 18 47

| Parameter | Type; input units | Default: Earth/Exo; Mars | Meaning and interactions |
| --- | --- | --- | --- |
| `yplanet` | character(80); label | `Earth` / `Exo`; `Mars` | Planet label in diagnostics; the compiled module supplies presets. |
| `nfixorb` | integer; selector | 1 | 1 uses prescribed orbital elements; 0 calculates Berger elements at radiation initialization using the current year or explicit radiation `iyrbp`. |
| `eccen` | real; 1 | 0.016715; Mars 0.09341233 | Prescribed orbital eccentricity for `nfixorb=1`. |
| `mvelp` | real; degrees | 102.7; Mars 336.04084 | Prescribed longitude of perihelion, not a longitude of vernal equinox as the old appendix labels it. |
| `obliq` | real; degrees | 23.441; Mars 25.19 | Prescribed axial obliquity. |
| `rotspd` | real; factor | 1 | If different from 1, `readnl` divides the solar day by this factor, rescales the year/month counts, and derives a new sidereal day. A Gregorian selector is first changed to 360. Record resulting values rather than treating this as a display-only factor. |
| `solar_day` | real; s | 86400; Mars 88775.24409 | Solar-day length; determines step seconds and calendar subdaily conversion, after any `rotspd` scaling. |
| `sidereal_day` | real; s | 86164.0916; Mars 88642.663 | Rotation period defining `ww=2*pi/sidereal_day`; can be recomputed by the `rotspd` branch. |
| `normalization_day` | character(8); selector | `solar` / `sidereal`; Mars `sidereal` | `solar` selects the solar day for damping normalization; the alternate branch uses the sidereal day. Use the documented spellings. |
| `akap` | real; 1 | 0.286; Mars 0.2273 | Dry gas constant/specific heat ratio; `acpd=gascon/akap` is derived afterward. |
| `alr` | real; K/m | 0.0065; Mars 0.0025 | Reference atmospheric lapse rate, also carried in output metadata for postprocessing. |
| `gascon` | real; J/(kg K) | 287; Mars 188.9 | Dry-air gas constant. |
| `psurf` | real; Pa | 101100; Mars 636 | Reference mean surface pressure used to scale spectral log pressure. Actual local pressure also depends on model state/orography. |
| `ga` | real; m/s² | 9.80665; Mars 3.728 | Gravity used in hydrostatics, flux conversions, and geopotential/height relationships. |
| `plarad` | real; m | 6371220; Mars 3396200 | Planet radius used in atmospheric geometry and normalization. Separate compiled coupler constants are not changed by renaming the planet. |
| `ra1` | real; Pa | 610.78; Mars 610.66 | Saturation-vapor-pressure prefactor in `ra1*exp(ra2*(T-TMELT)/(T-ra4))`. |
| `ra2` | real; 1 | 17.2693882; Mars 21.875 | Exponential coefficient in the same Magnus–Teten expression. |
| `ra4` | real; K | 35.86; Mars 7.65 | Temperature offset in that expression's denominator. |
| `pnu` | real; 1 | 0.1; Mars 0.15 | Leapfrog time-filter coefficient; derives `pnu21=1-2*pnu`. |
| `gsol0` | real; W/m² | 1365; Mars 595 | Stellar flux at the reference orbital distance; actual insolation also uses orbital distance and zenith angle. MoSt's Earth example writes its own value. |
| `p_wsmax` | real; m water | 0.5; Mars 0 | Initializes land `wsmax` before `landmod_nl` is read. |
| `ltidally_locked` | logical | `.false.` | Enables fixed-longitude illumination in `solang`; that branch sets `ndcycle=1`. Does not independently change rotation or orbit. |
| `tl_substellar` | real; degrees longitude | 180 | Substellar longitude used by the tidally locked illumination branch. |
```

Orbital elements with `nfixorb=0` are calculated once per initialization,
including restart initialization, rather than at every subsequent New Year.
See {doc}`../../user/planets` for experiment consequences.

The old `SIDEREAL_YEAR`/`TROPICAL_YEAR` inputs are absent. `WW` is derived,
not accepted in this group. Planet presets also set calendar, ozone, and
mean-profile defaults whose overrides belong in their respective groups.
