# Radiation: `radmod_nl`

File: `radmod_namelist`. Read by `radini` in
{repo}`plasim/src/radmod.f90`. The table includes current declaration
defaults and notes initialization overrides. `GSOL0` and prescribed orbital
elements belong to {doc}`planet`, not this group.

## Insolation, orbit, and absorbers

```{table}
:class: parameter-table
:widths: 15 20 18 47

| Parameter | Type; input units | Default | Meaning and interactions |
| --- | --- | --- | --- |
| `ndcycle` | integer; switch | 0 | 0 selects daily-mean shortwave treatment; 1 enables the diurnal cycle. Tidally locked illumination sets it to 1 in `solang`. |
| `ncstsol` | integer; switch | 0 | Nonzero uses constant prescribed latitude/declination cosines across the globe instead of geographic latitude and orbital declination in the zenith-angle calculation. |
| `solclat` | real; cosine | 1 | Cosine of the imposed insolation latitude when `ncstsol` is active. Used with `sqrt(1-solclat²)`; supply values within the cosine domain. |
| `solcdec` | real; cosine | 1 | Cosine of the imposed declination for `ncstsol`, with the analogous domain requirement. It is not an angle in degrees. |
| `iyrbp` | integer; years before 1950 | `1950-current_year` | Set from the actual model date before this namelist is read; an explicit value overrides that epoch. Used for Berger orbit initialization with `nfixorb=0`; has no effect on prescribed fixed elements. |
| `nsol` | integer; debug switch | 1 | Enables the solar-angle/insolation calculation; disabling it is a component-debug setting, not an orbital-epoch selector. |
| `nswr` | integer; switch | 1 | Enables shortwave radiation. |
| `nlwr` | integer; switch | 1 | Enables longwave radiation. |
| `nrscat` | integer; switch | 1 | Enables Rayleigh scattering in shortwave radiation. |
| `co2` | real; ppmv | 360 | Positive values initialize the three-dimensional CO₂ field uniformly. Nonpositive input does not itself supply a spatial CO₂ dataset. Also enters vegetation calculations. |
| `no3` | integer; selector | Earth/Exo 1; Mars 0 | 0 disables ozone treatment; 1 computes the analytic profile; 2 loads/interpolates `dqo3cl` climatology through the surface-data interface. |
| `a0o3` | real; cm at STP | 0.25 | Constant total-column term of the analytic ozone profile for `no3=1`. |
| `a1o3` | real; cm at STP | 0.11 | Absolute-sine-latitude coefficient in the analytic column. |
| `aco3` | real; cm at STP | 0.08 | Seasonal sine-latitude coefficient of that column. |
| `bo3` | real; m | 20000 | Height-location parameter in the analytic vertical ozone profile. |
| `co3` | real; m | 5000 | Vertical width in `exp((height-bo3)/co3)`; not a CO₂ concentration. |
| `toffo3` | real; calendar days | 90 | Phase offset in the analytic ozone seasonal cosine. |
| `o3scale` | real; multiplier | 1 | Multiplies computed/interpolated ozone after profile construction. |
| `dawn` | real; degrees | 0 | Dawn/dusk threshold converted to `sin(dawn*pi/180)` and compared with cosine of zenith angle. It is an angle threshold, not a time of day. |
```

## Clouds and radiation tuning

```{table}
:class: parameter-table
:widths: 15 20 18 47

| Parameter | Type; input units | Declaration default | Meaning and interactions |
| --- | --- | --- | --- |
| `nswrcl` | integer; selector | 1 | 1 computes shortwave cloud optical properties; 0 uses prescribed cloud-type coefficients below. |
| `rcl1` | real array(3); fractions | 0.15, 0.30, 0.60 | Prescribed cloud albedos for shortwave band 1 and the three cloud classes. |
| `rcl2` | real array(3); fractions | 0.15, 0.30, 0.60 | Corresponding prescribed cloud albedos in band 2. |
| `acl2` | real array(3); fractions | 0.05, 0.10, 0.20 | Prescribed band-2 cloud absorptivities. |
| `clgray` | real; fraction/selector | −1 | Positive values prescribe cloud grayness in longwave transmission; nonpositive values use cloud liquid water and `acllwr` to calculate it. |
| `acllwr` | real; m²/g | 0.100 | Longwave cloud mass-absorption coefficient. The exponent uses `-1.66*acllwr*1000*dql*dp*dsigma/ga`, including conversion of liquid-water mass to grams. |
| `tpofmt` | real; factor | 1 | Layer mean-transmissivity tuning factor in the longwave effective-radiation calculation. |
| `th2oc` | real; cm²/g in absorber convention | 0.024 | Water-vapour continuum coefficient in `1-exp(-th2oc*zsumwv)`; the longwave calculation uses a pressure-modified water amount in g/cm². Initialization tuning below can change it. |
| `tswr1` | real; coefficient | 0.077 | Cloud-albedo coefficient for shortwave band 1; modified per level by `tswr1mod`. Initialization tuning below can change it. |
| `tswr2` | real; coefficient | 0.065 | Cloud back-scattering coefficient for shortwave band 2; initialization tuning can change it. |
| `tswr3` | real; coefficient | 0.0055 | Band-2 cloud single-scattering-albedo coefficient; initialization tuning can change it. |
| `tswr1mod` | real array(NLEV); factors | 1 | Per-level modulation of `tswr1`, set to one before the namelist read. |
```

`radini` chooses tuning **before** reading `radmod_nl`, so explicit entries
override it. With dissipative heating enabled, the pre-read daily-mean,
nonuniform-level setup selects:

| Grid/levels | `tswr1` | `tswr2` | `tswr3` | `th2oc` |
| --- | --- | --- | --- | --- |
| T1/T21, 5 levels | 0.020 | 0.065 | 0.0040 | 0.0240 |
| T1/T21, ≥10 levels | 0.077 | 0.065 | 0.0055 | 0.0240 |
| T31, ≥10 levels | 0.077 | 0.067 | 0.0055 | 0.0240 |
| T42, ≥10 levels | 0.089 | 0.060 | 0.0048 | 0.0285 |

Other setups retain declarations and print the absence of a tuned setup.
Because branch selection precedes the radiation namelist read, a newly
supplied `ndcycle` is not retroactively used to choose these coefficients.

## Stellar spectrum

```{table}
:class: parameter-table
:widths: 15 20 18 47

| Parameter | Type; input units | Default | Meaning and interactions |
| --- | --- | --- | --- |
| `nstartemp` | integer; switch | 0 | Positive selects stellar-temperature-dependent shortwave treatment and invokes `solarini`; zero retains the classic path unless a spectrum file activates it. |
| `starbbtemp` | real; K | 5772 | Blackbody temperature used when spectrum initialization does not select input files. |
| `nsimplealbedo` | integer; selector | 1 | 1 uses a spectrum-weighted broadband albedo in both shortwave bands; the alternate path retains band-specific values. |
| `nstarfile` | integer; switch | 0 | Positive reads the two spectrum files, invokes `solarini`, and sets `nstartemp=1`. |
| `starfile` | character(80); path | blank | Lower-resolution two-column spectrum with 965 rows expected by `readdat`. |
| `starfilehr` | character(80); path | blank | High-resolution two-column spectrum with 2048 rows; used for spectral weighting. |
| `minwavel` | real; nm | 316.036116751 | Minimum wavelength used in stellar-spectrum integration. File wavelengths and flux conventions must match `solarini`/`readdat`, not just their two-column shape. |
```

Spectrum initialization precedes land/sea initialization and can supply
their shared spectral albedo arrays. Subsequent land/sea namelist entries
can override accepted arrays. Detailed source checks include `solarini`,
`solang`, `mko3`, `swr`, and `lwr`. See {doc}`../../user/restarts` before
continuing older states with spectral radiation.
