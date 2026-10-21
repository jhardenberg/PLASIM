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
| `zumin` | real; m/s | 1 | Minimum wind speed for surface exchange (`max(zumin², u²+v²)`) and vertical diffusion shear (`max(zumin, |Δv|)`). |
| `vdiff_lamm` | real; m | 160 | Asymptotic mixing-length parameter in `vdiff_lamm*k*z/(vdiff_lamm+k*z)`, also used to define the heat mixing scale. |
| `vdiff_b` | real; 1 | 5 | Stability-function coefficient appearing in both heat and momentum transfer factors. |
| `vdiff_c` | real; 1 | 5 | Unstable-regime stability-function coefficient. |
| `vdiff_d` | real; 1 | 5 | Stable-regime stability-function coefficient; also enters the heat mixing scale. |
```

Both `ZUMIN` expressions apply a wind-speed floor in m/s: surface exchange
floors squared lowermost-level speed by `zumin²` before computing transfer
coefficients and bulk Richardson numbers, and vertical diffusion floors the
vertical shear speed difference by `zumin`.

`ZUMIN_D` from the old descriptive text is not the accepted spelling.
The main model's `NFLUX` is separate from these component switches; check
the actual `fluxstep` calls when selectively disabling physical tendencies.
