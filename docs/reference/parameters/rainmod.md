# Clouds and precipitation: `rainmod_nl`

File: `rainmod_namelist`. These are the unified precipitation implementation's
inputs, read by `rainini` in {repo}`plasim/src/rainmod.f90`. The convection
scheme is selected at runtime via `nconvection`.

```{table}
:class: parameter-table
:widths: 15 20 18 47

| Parameter | Type; input units | Default before input | Meaning and interactions |
| --- | --- | --- | --- |
| `kbeta` | integer; selector | 1 | Kuo moisture partition: 0 omits beta; 1 computes it from mean humidity; 2 uses explicit `rbeta`. Historical `KBETTA` is not the accepted spelling. |
| `nbeta` | integer; exponent | 3 | Power in `((1-RH)/(1-rhbeta))**nbeta` for the diagnosed beta branch. |
| `rhbeta` | real; RH fraction | 0 | Critical relative humidity for the beta expression; below it beta remains one. The expression's denominator requires a value different from one. |
| `rbeta` | real; fraction | 0 | Explicit beta for `kbeta=2`, useful in controlled sensitivity experiments. |
| `nprl` | integer; switch | 1 | 1 enables large-scale precipitation. |
| `nprc` | integer; switch | 1 | 1 enables Kuo convective precipitation and its humidity-tendency preparation. |
| `ndca` | integer; switch | 1 | 1 enables dry convective adjustment. |
| `ncsurf` | integer; switch | 1 | Allows convection to originate at the surface in the Kuo calculation. |
| `nmoment` | integer; switch | 0 | Enables convective momentum mixing in the relevant convection branch. |
| `nshallow` | integer; switch | 1; T21/L5 0 | Enables shallow convection; `rainini` disables it for T21 with five levels before reading overrides. |
| `nstorain` | integer; switch | 0 | Positive enables the stochastic large-scale rain branch, consuming random numbers; preserve seeds for reproducible comparisons. |
| `nclouds` | integer; switch | 1 | 1 calls diagnostic cloud generation in `rainstep`. |
| `nevapprec` | integer; switch | 1 | 1 enables evaporation of falling precipitation. |
| `rcrit` | real array(NLEV); RH fractions | `max(0.85,sigma,1-sigma)` | Critical RH profile for nonconvective clouds, initialized from the actual sigma grid before reading. Supply a complete intended profile if overriding it. |
| `clwcrit1` | real; Pa/s | −0.1 | First pressure-velocity threshold for low-level nonconvective-cloud suppression. |
| `clwcrit2` | real; Pa/s | 0 | Second threshold. With the default first threshold below the second, suppression is inactive; ordered thresholds construct the transition factor in `rainini`/`mkclouds`. |
| `pdeep` | real; Pa | 999999 | Convection with cloud-top pressure above this threshold is identified as shallow in the Kuo path. |
| `pdeepth` | real; Pa | 70000 | Additional pressure threshold used to modify the top of the shallow-convection layer. |
| `rkshallow` | real; m²/s | 10 | Diffusivity used by shallow convection. |
| `gamma` | real; 1 | 0.01; T42/≥10 levels 0.007 | Precipitation-evaporation coefficient multiplying the local saturation deficit and layer sigma thickness, divided by `deltsec2` in the humidity-tendency limit. |
| `nconvection` | integer; selector | 0 | Convection scheme selector: 0 for default Kuo; 1 for Betts–Miller (`mkbm`); 2 for Moist Convective Adjustment (`mca`); 3 for historical Kuo (`kuo_old`). |
| `kbetta` | integer; selector | −1 | Legacy namelist alias for `kbeta` from older documentation; if non-negative, overrides `kbeta`. |
| `rsoft` | real; fraction | 1.0 | Relative humidity threshold factor for soft convection in Moist Convective Adjustment (`nconvection=2`). |
| `tadjust` | real; timesteps | 1.0 | Convective relaxation time scale in timesteps for Moist Convective Adjustment (`nconvection=2`; must be ≥ 1.0). |
```

The runtime switch `nconvection` selects among the unified convection schemes.
Several settings interact: a shallow scheme needs its branch enabled, cloud
thresholds affect diagnostic cloud construction, and `rbeta` only overrides
the computed partition with `kbeta=2`. Source checks cover `rainini`,
`rainstep`, `kuo`, `mkbm`, `mca`, `kuo_old`, shallow convection, `mkclouds`,
and precipitation evaporation. The old defaults for shallow convection and
some tuning are not current.
