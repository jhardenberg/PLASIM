# Vegetation: `vegmod_nl`

File: `vegmod_namelist`. Read by `vegini` in
{repo}`plasim/src/simba.f90` (module `vegmod`). These settings operate
when `NVEG>0` in {doc}`plasim`; the carbon-production/turnover coefficients
remain in {doc}`landmod`.

```{table}
:class: parameter-table
:widths: 15 20 18 47

| Parameter | Type; input units | Default | Meaning and interactions |
| --- | --- | --- | --- |
| `ncveg` | integer; multiplier | 1 | Time accelerator multiplying vegetation and soil carbon increments. Zero holds those carbon pools fixed, but does not disable all vegetation calculations or surface feedbacks. |
| `forgrow` | real; fraction | 1 | Initial biomass growth-allocation field `dgrow`; net primary production uses `dgrow*0.5*zgpp`. Surface `dgrow` can replace it. |
| `rinidagg` | real; factor | 0.5 | Initial above-ground growth factor `dagg`, used with biomass to determine maximum leaf area. Surface data can replace it. |
| `rinidsc` | real; factor | 1 | Initial stomatal/wetness multiplier `dsc` in the vegetation surface-conductance expression. It is not an independently specified aerodynamic velocity. Surface data can replace it. |
| `rinidmr` | real; m | 2 | Initial maximum vegetation roughness `dmr`; roughness blends this with the bare-soil value using forest fraction. Surface data can replace it. |
| `rinisoil` | real; kg C/m² | 0 | Cold-start soil organic carbon pool `dcsoil`; restored carbon replaces this initialization on restart. |
| `riniveg` | real; kg C/m² | 0 | Cold-start vegetation biomass carbon pool `dcveg`; restored carbon replaces this initialization on restart. |
```

The legacy `NCVEG` description as a simple compute/hold switch misses its
time-acceleration role. The old land table's `FORGROW`, `RINISOIL`, and
`RINIVEG` belong here now; `RLAIGROW`, `GS`, and `Z0_MAX` are not accepted
names in this group. Surface inputs `dagg`, `dsc`, `dmr`, and `dgrow` are
spatial fields, not additional namelist variables. Source checks cover
allocation, surface loading, restart restoration, and `vegstep` equations.
