# Surface exchange and diffusion: `fluxmod_nl`

File: `fluxmod_namelist`. Read by `fluxini` in
{repo}`plasim/src/fluxmod.f90`; calculations are in `surflx` and `vdiff`.

```{table}
:class: parameter-table
:widths: 15 20 18 47

| Parameter | Type; input units | Default | Meaning and interactions |
| --- | --- | --- | --- |
| `nvdiff` | integer; switch | 1 | Enables vertical diffusion of temperature, humidity, and momentum in `fluxstep`. |
| `nshfl` | integer; switch | 1 | Enables surface sensible heat exchange. |
| `nevap` | integer; switch | 1 | Enables evaporation and its latent-heat contribution. |
| `nstress` | integer; switch | 1 | Enables surface wind stress. |
| `ntsa` | integer; selector | 2 | Surface-air-temperature calculation: 1 uses the dry potential-temperature extrapolation; 2 includes the humidity/virtual-temperature factor. Other values stop `surflx`. |
| `zumin` | real; wind floor, see below | 1 | Surface exchange uses `max(zumin,u²+v²)` before taking the speed; vertical diffusion uses `max(zumin,abs(speed(level)-speed(next)))` before dividing by layer separation. These are the actual two numerical uses. |
| `vdiff_lamm` | real; m | 160 | Asymptotic mixing-length parameter in `vdiff_lamm*k*z/(vdiff_lamm+k*z)`, also used to define the heat mixing scale. |
| `vdiff_b` | real; 1 | 5 | Stability-function coefficient appearing in both heat and momentum transfer factors. |
| `vdiff_c` | real; 1 | 5 | Unstable-regime stability-function coefficient. |
| `vdiff_d` | real; 1 | 5 | Stable-regime stability-function coefficient; also enters the heat mixing scale. |
```

The two `ZUMIN` expressions compare against a squared speed and a speed,
respectively. Thus the declaration's label “minimum wind speed (m/s)”
does not provide a single consistent unit convention for nondefault values.
The table records current behavior; the implementation finding is tracked
separately in the verification ledger.

`ZUMIN_D` from the old descriptive text is not the accepted spelling.
The main model's `NFLUX` is separate from these component switches; check
the actual `fluxstep` calls when selectively disabling physical tendencies.
