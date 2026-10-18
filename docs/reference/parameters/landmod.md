# Land: `landmod_nl`

File: `landmod_namelist`. Read by `landini` in
{repo}`plasim/src/landmod.f90`. This replaces the historical
`land_namelist`/`LANDPAR` interface. Soil has `NLSOIL=5` compiled layers.

## Temperature, water, and surface properties

```{table}
:class: parameter-table
:widths: 15 20 18 47

| Parameter | Type; input units | Default | Meaning and interactions |
| --- | --- | --- | --- |
| `nlandt` | integer; switch | 1 | 1 integrates soil/surface temperature; 0 uses climatological temperature. |
| `nlandw` | integer; switch | 1 | 1 integrates soil water; 0 supplies climatological soil wetness. |
| `albland` | real; fraction | 0.2 | Background broadband land albedo used to initialize `dalbcl`; surface climatology can replace it. Spectral background fields are initialized separately from `dgroundalb`. |
| `dz0land` | real; m | 2 | Fallback land roughness length, initializing `dz0clim`; surface data and vegetation can replace spatial values. |
| `drhsland` | real; fraction | 0.25 | Fallback land wetness factor. Missing soil-water climatology is initialized to `dwmax*drhsfull*drhsland`. |
| `wsmax` | real; m water | `p_wsmax` | Bucket field capacity; `landini` replaces the declaration 0.5 by the planet value before reading. Negative values are clipped to zero. Surface `dwmax` and vegetation can change the spatial capacity. |
| `drhsfull` | real; fraction of capacity | 0.4 | Soil-water threshold for unrestricted evaporation. For positive capacity, wetness is `min(1,dwatc/(drhsfull*dwmax))`. |
| `nwatcini` | integer; switch | 0 | Positive requests explicit cold-start soil water `dwatcini`; otherwise `soilini` initializes `drhsland*drhsfull*dwmax`. It does not relabel saved restart water. |
| `dwatcini` | real; m water | 0 | Explicit soil water when `nwatcini>0`; initialization assigns it directly, while the subsequent prognostic water budget limits water to the bucket capacity and diagnoses runoff. |
| `dzglac` | real; m terrain height | −1 | If positive, sets glacier cover where surface geopotential exceeds `dzglac*ga`; nonpositive values leave the supplied mask unchanged. |
| `dztop` | real; m | 0.20 | Thickness used for the mixed soil/snow surface layer in the thermal calculation; distinct from the deeper `dsoilz` array. |
| `dsoilz` | real array(5); m | 0.4, 0.8, 1.6, 3.2, 6.4 | Soil thermal-layer thicknesses. Preserve the compiled five-element shape. |
| `soilcap` | real; J/(m³ K) | 2.4e6 | Volumetric soil heat capacity used by the soil-temperature calculation. |
| `dsmax` | real; m water equivalent | 5 | Maximum snow depth; a negative value removes this limit. Snow removed at the limit contributes to runoff. |
| `newsurf` | integer; selector | 0 | 0 leaves the normal cold-start/restart surface setup; 1 rereads temperature/water climatology; 2 resets capacity, roughness, albedo, and soil-water climatology to fallback values. These overrides follow either initialization path; they do not make a restart a cold start. |
```

## Snow and glacier albedo

Two-element arrays follow the shortwave bands below and above 0.75 µm.
The stellar-spectrum initialization can set their values before `landini`;
the values below are the shared declarations for the classic path.

```{table}
:class: parameter-table
:widths: 15 20 18 47

| Parameter | Type; input units | Default | Meaning and interactions |
| --- | --- | --- | --- |
| `albsmin` | real; fraction | 0.4 | Minimum broadband snow albedo, used in the broadband land/vegetation calculations. It remains accepted although several companion historical scalars do not. |
| `dsnowalbmn` | real array(2); fraction | 0.4 | Minimum band snow albedos. `landini` uses these to set `albsmin1/2`. |
| `dsnowalbmx` | real array(2); fraction | 0.8 | Maximum band snow albedos; also sets maximum band glacier albedos. Forest maxima are initialized to half these values, with forest minima at 0.75 of those maxima. |
| `dglacalbmn` | real array(2); fraction | 0.6 | Minimum band glacier albedos. |
| `dsnowalb` | real array(2); fraction | 0.6 | Shared band snow-albedo values initialized by the radiation/spectrum path and accepted here; distinct from temperature-dependent minimum/maximum limits. |
```

`ALBSMAX`, `ALBSMINF`, `ALBSMAXF`, `ALBGMIN`, and `ALBGMAX` in the old
table are no longer accepted namelist inputs. Derived band scalars are not
additional namelist names. See {doc}`radmod` for spectrum weighting.

## Vegetation coefficients stored in the land group

```{table}
:class: parameter-table
:widths: 15 20 18 47

| Parameter | Type; input units | Default | Meaning and interactions |
| --- | --- | --- | --- |
| `rlue` | real; kg C/J | 3.4e−10 | Light-use efficiency in light-limited gross primary production: multiplies absorbed shortwave flux and vegetation/temperature/CO₂ factors in `vegstep`. The old appendix's 8e−10 is not today's default. |
| `co2conv` | real; carbon-conversion coefficient | 8.3e−4 | Water-limited carbon conversion in `co2conv*dp*zveg*(-devap)/zvpd*(0.3*co2)`. Here pressures are Pa, evaporation is m/s, CO₂ is ppmv, and the result is kg C/(m² s); the coefficient therefore includes kg C/(m³ ppmv) in this numerical convention. The old value 14 is stale. |
| `tau_veg` | real; fixed Earth years | 10 | Vegetation carbon turnover; multiplied by `365*86400` before use. Converted timescales below one second stop initialization. |
| `tau_soil` | real; fixed Earth years | 42 | Soil carbon turnover; same conversion and lower bound as `tau_veg`, independent of the planet calendar. |
| `rinifor` | real; fraction | 0.5 | Initial forest fraction on a cold start, before available surface forest data replace it. |
| `rnbiocats` | real; category control | 0 | Below 2, keeps continuous forest/soil cover. At 2 or above, discretizes cover using integer categories and denominator `rnbiocats-1`. |
```

The vegetation execution switch is `NVEG` in {doc}`plasim`, and its
initial carbon/growth controls are in {doc}`vegmod`. Boundary fields can
override fallback scalars; a restart restores state rather than repeating
every cold-start initialization. Relevant paths checked: `landini`,
`landstep`, `tands`, `mktsoil`, `wandr`, `soilini`/`soilstep`, and
`vegstep` in `simba.f90`.
