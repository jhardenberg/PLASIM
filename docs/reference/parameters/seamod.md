# Sea-surface interface: `seamod_nl`

File: `seamod_namelist`. Read by `seaini` in
{repo}`plasim/src/seamod.f90`. This interface accumulates atmospheric
fluxes and calls the ice/ocean components; their prognostic switches are
in their own groups.

```{table}
:class: parameter-table
:widths: 15 20 18 47

| Parameter | Type; input units | Default | Meaning and interactions |
| --- | --- | --- | --- |
| `ncpl_atmos_ice` | integer; atmospheric step interval | 1 | Calls the ice interface when `mod(nstep,ncpl_atmos_ice)=0` after startup; accumulated fluxes are averaged over the intervening calls. Use a positive interval. The old appendix's 32 is stale. |
| `albsea` | real; fraction | 0.069 | Broadband albedo for open water. Spectral bands use `doceanalb`. |
| `albice` | real; fraction | 0.7 | Maximum broadband sea-ice albedo; the temperature-dependent value is limited by this maximum and mixed with open-water albedo. |
| `dz0sea` | real; m | 1.5e−5 | Minimum open-water roughness length; `seastep` takes the maximum of this and the Charnock value. |
| `dz0ice` | real; m | 0.001 | Roughness over sea ice; blended with open water using ice compactness. |
| `drhssea` | real; fraction | 1 | Wetness factor for open water. |
| `drhsice` | real; fraction | 1 | Wetness factor for ice, blended with the ocean value. |
| `charnock` | real; 1 | 0.018 | Coefficient of stress-dependent ocean roughness in `seastep`; the declaration comment calling it an albedo is stale. |
| `doceanalb` | real array(2); fractions | 0.069 | Open-water band albedos, below/above 0.75 µm. Spectrum initialization can replace declarations before this group is read. |
| `dicealbmn` | real array(2); fractions | 0.5 | Minimum-temperature-law band ice albedo values; used with the temperature slope and upper limits. |
| `dicealbmx` | real array(2); fractions | 0.7 | Maximum band ice albedo values. |
```

The effective sea albedo is a blend of ice and open-water contributions,
not simply a constant input. Source checks cover `seaini`, `seastep`,
roughness, albedo construction, and the atmosphere–ice call/averaging path.
