# Output fields, formats, and units

Use the {doc}`raw-output` catalogue for the complete inventory of model output
fields, source array assignments, writer routines, and `srv2nc` converted NetCDF
variable names and units. The historical `variable_list.txt` is a useful starting
index, not an independent guarantee of current dimensions, units, signs, or enabled
fields.

## Three kinds of model product

| Product | Representation | Reader/use |
| --- | --- | --- |
| `plasim_output.nc` | Direct NetCDF-4 output (`nnetcdf > 0`) | Standard NetCDF tools (CDO, Python netCDF4/xarray, Panoply). |
| `plasim_output`, `ice_output`, `ocean_output`, `lsg_output` | Binary Service-style output records (`nnetcdf = 0`) | Selected postprocessor; not a text editor. |
| `Nnnn_surf_cccc.sra` | Formatted surface-data headers/arrays | Boundary-data loader; see {doc}`../user/boundary-data`. |
| `plasim_status` / `plasim_restart` | Named binary restart records | Compatible model restart loader; not a Service converter. |

The raw atmospheric output currently writes **32-bit** real data and
32-bit integer headers, even when the model uses double-precision internal
arithmetic. The old guide's general statement about packed 16-bit output
does not describe these current `writegp`/`writesp` implementations.

## Direct NetCDF-4 output

When configured with `nnetcdf = 1` in `plasim_namelist`, PlaSim writes directly
to a compressed NetCDF-4 file (`plasim_output.nc`) instead of binary Service format.
The file contains coordinate variables `lon`, `lat`, `lev`, and unlimited `time`,
with 50 primary physical 3D and 2D variables.

- **Compression**: NetCDF-4 deflation (zlib) is enabled on all variables with level
  controlled by `ndeflate` (default `4`, range `0`–`9`). Chunking is structured per
  horizontal Gaussian slab (`NLON` × `NLAT`).
- **Averaging & cadence**: Controlled by `noutput_avg`:
  - `noutput_avg = 1` (default): True 24-hour daily averages across all model timesteps
    in each day (`ntspd` steps), integrating the diurnal cycle without midnight sampling
    bias. In this mode, `nwpd` is ignored.
  - `noutput_avg = 2`: Calendar monthly averages across all model timesteps in the month.
    In this mode, `nwpd` is ignored.
  - `noutput_avg = 0`: Instantaneous snapshots written at the interval governed by `nwpd`
    (`ntspd / nwpd` steps, e.g. 6-hourly with `nwpd = 4`).
- **Spectral synthesis**: Spectral variables (temperature, divergence, vorticity, orography)
  are synthesized to the Gaussian grid on hybrid levels, and horizontal winds `ua` and `va`
  are derived from vorticity and divergence.

## Atmospheric Service records

A record pair consists of an eight-integer header and its data array.
Fortran sequential-unformatted record markers and byte order are part of
the actual file layout; the integer header alone is not the whole binary
format.

| Header slot | Current atmospheric writer meaning |
| --- | --- |
| 1 | Numeric field code. |
| 2 | Level argument: zero for a surface field, model-level index for a level field. |
| 3 | Date `YYYYMMDD`. |
| 4 | Time `HHMM`. |
| 5, 6 | Gaussian `NLON, NLAT`, or `NRSP, 1` for spectral records. |
| 7 | Elapsed full steps since this invocation began (`nstep-nstep1`). |
| 8 | Configured `n_days_per_year`. |

This is the raw model header. The old guide's postprocessor `HEAD7` and
experiment-number descriptions refer to a different output path. Ice/ocean
writers set slots 7/8 to zero; do not impose the atmosphere's meanings on
every component. Afterburner pressure-level output also has its own level
and header conventions.

The initial atmospheric code **333** is metadata: half-level sigma values,
calendar selector, radius, gravity, dry gas constant, and lapse rate. Its
header includes model levels and truncation. It is not a diagnostic climate
variable and is not read as the ordinary eight-slot interpretation above.

## Representation and dimensions

Temperature (130), log surface pressure (152), divergence (155), and
vorticity (138) are written spectrally in the normal atmospheric path;
orography (129) is spectral as well. Humidity (133) is spectral when
`NQSPEC=1`, and written on the grid in the alternate moisture path.

Cloud liquid water (161) and cloud cover (162) are emitted for each model
level (`jlev`), rather than being intrinsically single surface-level fields
as the old text table can suggest. Surface diagnostics are on the Gaussian
grid. A NetCDF converter can introduce dimensions and coordinate variables
that are not themselves raw code records.

Additional diagnostic families use conditional and dynamic code ranges.
`NDIAGCF` enables clear-sky flux codes 101–107. User diagnostic arrays and
energy/entropy diagnostics depend on their switches and code selection;
the generated literal-call inventory does not enumerate every dynamic value.

## Time meaning and sign conventions

Not every field in the same output file is an instantaneous sample:

- Atmospheric precipitation (142–144), evaporation, heat/radiation fluxes,
  stress, runoff, and several other diagnostics are accumulated across
  model steps and divided by `naccuout` before writing. They are interval
  means of the corresponding quantities, not totals solely because an
  internal array name begins with `a`.
- `TASMAX`/`TASMIN` codes 201/202 use interval extrema; their interpretation
  as daily extrema depends on the output interval.
- Surface state variables such as ice thickness and temperatures are written
  from state arrays; inspect the writer when combining them with flux means.
- Ice flux accumulators are averaged over their own output interval.
  `srv2nc -m` adds another monthly aggregation; it does not make the original
  output instantaneous or reconstruct missing subinterval extremes.

The model and CMOR-style extraction use different sign conventions for
several fluxes. For example, `burn.sh` negates evaporation and selected
upward heat/radiation terms and scales water fluxes by 1000 for mass-flux
units. Do not apply those conversions a second time to an already converted
product. A variable's familiar name is insufficient to identify its sign.

Selected model-side physical units checked against declarations/writers:

| Quantity | Model-side interpretation |
| --- | --- |
| Surface geopotential | m²/s²; divide by the experiment's gravity for height. |
| Temperature | K in raw model fields; some GUI displays use Celsius. |
| Specific humidity/cloud liquid water | kg/kg in raw fields. |
| Precipitation/evaporation/runoff rates | Water-depth rate in m/s before mass-flux conversion. |
| Soil water and field capacity (`dwatc`, `dwmax`) | Metres of water. |
| Radiation and sensible/latent heat terms | W/m², with direction defined by the implementation. |
| Mixed-layer diffusion-budget outputs 904/905 | Heat-flux contributions from vertical/horizontal diffusion; distinguish these from the diffusivity parameters `VDIFFKL`/`HDIFFK` in m²/s. |

The {doc}`raw-output` catalogue deliberately labels its unit column **declared
units**, because it records the actual conversion table rather than
silently treating every label as a verified physical definition.

## Ice output and budget diagnostics

The current writer retains the principal code families listed in
`codes_in_ice_output.pdf`: 701–714 for heat-budget terms, 739 skin
temperature, 741 snow, 769 SST, 772 mask, 790/791 climatological ice,
794/795 freshwater/runoff, 796 snow-to-ice conversion, and optional 797
entropy output. It also writes **792**, the prognostic compactness,
which is absent from that old sheet. Extra arrays use a dynamic 750+ range.

The heat-budget terms below are interval means in W/m², retaining the
model's signs. Distinguish the conductive contribution used within the ice
calculation from the flux ultimately passed to the ocean.

| Code | Array written | Meaning in the current ice calculation |
| --- | --- | --- |
| 701 | `xheata` | Atmospheric heat-flux contribution. |
| 702 | `xofluxa` | Ocean heat-flux contribution. |
| 703 | `xtsfluxa` | Heating/cooling of ice and snow. |
| 704 | `xsmelta` | Snow-melt heat term. |
| 705 | `ximelta` | Ice melt/freeze heat term. |
| 706 | `xcfluxa` | Heat flux passed to the ocean after ice adjustments. |
| 707 | `xfluxca` | Conductive heat flux through ice. |
| 708 | `xqmelta` | Residual heat flux for ice. |
| 709 | `xflxicea` | Applied ice flux correction. |
| 712 | `xscflxa` | Snow-to-ice conversion heat term. |
| 713 | `xcfluxra` | Residual associated with the maximum ice-thickness limit. |
| 714 | `xcfluxna` | Residual associated with negative-ice correction. |

Codes 710 and 711 are the selected ice compactness (fraction) and thickness
(m), respectively; they are state fields rather than heat fluxes.

`iceout` writes code 741 from the calculated `zsnow` array; do not infer
its units from an unrelated atmospheric snow field. Code 710 is the ice
compactness field actually selected/limited by the active ice path; it
need not equal diagnostic code 792.

The heat-budget check in `icestep` constructs the residual

```{math}
R = c_{701}+c_{702}+c_{713}-c_{703}-c_{704}-c_{705}-c_{706}.
```

Its flux-corrected diagnostic additionally includes code 709. This describes
the diagnostic expression present in the code; it is **not** a promise of
zero residual for every switch combination, mask, correction, or aggregation.
The historical sheet's equalities should not be used as universal numerical
acceptance tests. Inspect the component masks and exact accumulation interval
when investigating a budget.

## LSG ocean output and grid conventions

Coupled simulations with the Large Scale Geostrophic ocean write output to
two primary binary Service-style files:

- `lsg_output`: created on Fortran unit 93 by `outpostsrv` in
  {repo}`lsg/src/lsgmod.f90` at the end of each coupling interval.
- `LSG_srf`: created on unit `nopost` by `outsurf` in {repo}`lsg/src/lsgmod.f90`
  to store surface fields and upper subsurface layers (layers 1, 2, 4) for
  high-frequency diagnostics.
- `bck...`: written by `outback` on sequential unformatted units for coupled
  restarts.

### Negative code convention

In its raw Service records, LSG marks variables with **negative integer codes**
(`jcode < 0`) in the first header slot: for example, `jcode = -2` for potential
temperature, `-5` for salinity, `-3` for zonal velocity, `-4` for meridional velocity,
`-7` for vertical velocity, and `-1` for surface elevation. Historically, this
prevented collision with positive WMO/GRIB atmospheric table codes.

When converting `lsg_output` via `scripts/srv2nc`, CDO maps negative Service codes
to their positive counterparts (1–99) and looks up descriptive names and units from
the `paramlsg.tab` dictionary.

### Staggered horizontal Arakawa E-grid

LSG operates on a semi-staggered Arakawa E-grid ($72 \times 76$ horizontal points
at 2.5° resolution) with two offset subgrids:

- **Scalar grid points** (`gpgridt`): variables including elevation `zeta` (code 1),
  potential temperature `t` (2), salinity `s` (5), freshwater flux `fluwat` (65),
  heat flux `fluxhea` (18), scalar land–sea mask `wet` (40), and bottom depth
  `depp` (98).
- **Vector grid points** (`gpgridu`): variables offset by half a grid cell,
  including zonal/meridional velocities `utot`/`vtot` (3, 4), barotropic velocities
  `ub`/`vb` (37, 38), wind stresses `taux`/`tauy` (52, 53), vector land–sea mask
  `wetvec` (41), and vector bottom depth `depv` (99).

`srv2nc` automatically separates vector variables (`uvars`) and assigns the appropriate
curvilinear grid description before merging them into CF-compliant NetCDF files.

### Vertical depth coordinate

The LSG ocean uses 22 vertical depth layers:

- **Layer midpoints** (`zaxislsgu` / `zaxislsgc`): 25, 75, 125, 175, 225, 275, 350,
  450, 550, 650, 750, 850, 950, 1100, 1300, 1500, 1800, 2250, 2750, 3500, 4500, and
  5500 m. Used for 3D state fields ($T$, $S$, $u$, $v$).
- **Layer interfaces** (`zaxislsgw`): 50, 100, 150, 200, 250, 312.5, 400, 500, 600,
  700, 800, 900, 1025, 1200, 1400, 1650, 2025, 2500, 3125, 4000, 5000, and 6000 m.
  Used for vertical velocity `w` (code 7).

Internal ocean potential temperature is stored in Celsius (`t(:,:,:)`), but the output
routines `outpostsrv` and `outsurf` add `tkelvin` (273.15 K) upon writing, so raw
code 2 is in Kelvin. Converted diagnostic code 62 (`tc`) retains Celsius.

## Sources checked

User's Guide chapter 5 and appendix B, `variable_list.txt`, and the ice
output sheet compared with {repo}`plasim/src/outmod.f90` (`outini`,
`writegp`, `writesp`, `outgp`, `outaccu`, `outreset`), `iceout`/`icestep`,
`oceanout`, `mpwritegph`, {repo}`lsg/src/lsgmod.f90` (`outpostsrv`, `outsurf`,
`outback`), and the actual converter tables/expressions in {repo}`scripts/srv2nc`.
