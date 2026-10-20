# PlaSim–LSG coupler: `cplpar`

File: `cpl_namelist`. Read by `clsgini` in
{repo}`plasim/src/cpl.f90`; only the real LSG build uses this interface.
Atmosphere-to-ocean fields are accumulated/averaged before interpolation.
The atmosphere, ocean scalar, and ocean vector grids have different masks.

## Interpolation and conservation

An interpolation selector of 1 uses cell-overlap interpolation (`cinter`);
the alternate branch, normally 0, uses masked coordinate interpolation
(`cinter2`). Both can fill missing target cells and apply the selected
global correction. Conservation selectors mean: 0 none; 1 multiplicative
correction of the area-weighted integral; 2 multiplicative correction of
the weighted mean; 3 additive correction of the integral; 4 additive
correction of the mean. Masked areas enter those definitions.

```{table}
:class: parameter-table
:widths: 15 20 18 47

| Parameter | Type; input units | Default | Meaning and interactions |
| --- | --- | --- | --- |
| `nissta` | integer; interpolation selector | 0 | Atmosphere/mixed-layer SST to ocean scalar grid. |
| `niicea` | integer; interpolation selector | 0 | Atmospheric ice thickness to ocean scalar grid. |
| `nipmea` | integer; interpolation selector | 0 | Atmospheric freshwater flux to ocean scalar grid. |
| `nitaua` | integer; interpolation selector | 0 | Atmospheric wind-stress components to ocean vector grid. |
| `nihfla` | integer; interpolation selector | 0 | Atmospheric heat flux to ocean scalar grid in heat-flux coupling. |
| `nissto` | integer; interpolation selector | 1 | Ocean SST to atmospheric grid. |
| `nihflo` | integer; interpolation selector | 1 | Ocean heat feedback to atmospheric grid. |
| `ncssta` | integer; conservation selector | 3 | Global correction after atmosphere-to-ocean SST interpolation. |
| `ncicea` | integer; conservation selector | 1 | Correction after atmosphere-to-ocean ice interpolation. |
| `ncpmea` | integer; conservation selector | 3 | Correction after freshwater interpolation. |
| `nctaua` | integer; conservation selector | 3 | Correction applied to both wind-stress components. |
| `ncssto` | integer; conservation selector | 3 | Correction after ocean-to-atmosphere SST interpolation. |
| `nchflo` | integer; conservation selector | 3 | Correction after ocean-to-atmosphere heat-feedback interpolation. |
```

`NCHFLA` is declared internally for atmosphere-to-ocean heat correction
but is **not** accepted in `cplpar`; do not infer accepted names from
declarations or naming symmetry alone.

## Forcing blends, corrections, and diagnostics

```{table}
:class: parameter-table
:widths: 15 20 18 47

| Parameter | Type; input units | Default | Meaning and interactions |
| --- | --- | --- | --- |
| `cfacsst` | real; fraction | 1 | Blend of coupled SST with file boundary SST in LSG: `factor*coupled+(1-factor)*file`. One selects coupled forcing; zero selects file forcing. |
| `cfacice` | real; fraction | 1 | Same blend for ice thickness. |
| `cfactau` | real; fraction | 1 | Same blend for both wind-stress components. |
| `cfacfresh` | real; fraction | 1 | Same blend for freshwater forcing, including runoff treatment. |
| `nflsst` | integer; switch | 0 | 1 adds monthly SST correction from `flukofile` to the coupled SST before the boundary blend. |
| `nflice` | integer; switch | 0 | 1 adds monthly ice correction. |
| `nfltau` | integer; switch | 0 | 1 adds monthly corrections to both wind-stress components. |
| `nflfresh` | integer; switch | 0 | 1 adds monthly freshwater correction. |
| `nfloheat` | integer; switch | 0 | 1 adds monthly deep-ocean heat-flux correction in `cflukob`. |
| `flukofile` | character(80); path | `fluko_data.txt` | Formatted monthly correction records read when corrections are requested; retain matching field codes and grids. |
| `nroffc` | integer; selector | 0 | 0 keeps runoff; 1 redistributes as a global ocean mean; 2 replaces mapped regions with their area means; 3 redistributes between mapped input/output regions. |
| `runoffmap` | character(80); path | `runoffmap.txt` | Region-mask file for runoff modes 2/3; mode 3 needs both input and output maps. |
| `nprint` | integer; debug switch | 0 | Positive prints coupler grids, interpolation/conservation information, and selected fields. |
| `ndbox` | integer; ocean i index | 1 | Ocean diagnostic longitude index passed to LSG initialization. |
| `ndboy` | integer; ocean j index | 1 | Ocean diagnostic latitude index passed to LSG initialization. |
```

The coupling mode and interval come from `oceanmod_nl`, not additional
`cplpar` inputs. Corrections here are separate from mixed-layer/ice
`NFLUKO`. Source checks include `clsgini`, exchange getters/setters,
`cinter`, `cinter2`, `conserve`, `croffc`, `cflukoa`/`cflukob`, `cpfac`,
and LSG `readbou`.
