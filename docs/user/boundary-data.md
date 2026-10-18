# Surface and boundary data

MoSt selects boundary data matching the compiled resolution and planet.
Keep the selected dataset with the experiment and record any changes;
copying unrelated files with the same extension is not a grid conversion.

## Current file names and layout

`surfmod` registers a mapping from numeric field codes to model arrays.
The split-file name is `Nnnn_surf_cccc.sra`, with the atmospheric latitude
count and four-digit code. For T21, examples are:

| File | Model use |
| --- | --- |
| `N032_surf_0129.sra` | Surface geopotential/orography, code 129. |
| `N032_surf_0172.sra` | Land–sea mask, code 172. |
| `N032_surf_0169.sra` | Surface/SST climatology used by the sea modules. |

The `N032` label denotes 32 latitudes, not 32 longitudes or truncation T32.
T42 uses `N064` and 128 × 64 points. The current loader supports named split
files and legacy surface input paths; use the split files prepared by MoSt
for a new experiment. The old guide's blanket instruction to put all data
in `surface.txt` does not describe the normal current setup.

Each formatted Service record has an eight-integer header followed by its
numeric field. The split-file reader uses free-format numeric reads. The
longitude dimension varies fastest in the model's array ordering. Preserve
the Gaussian latitude grid and its orientation, not an equally spaced
latitude approximation.

For climatologies, `get_surf_array` accepts twelve months and creates
December/January padding when fourteen slots are needed. A single field can
also be repeated over the climatological slots. Other incomplete lengths
are rejected. Do not append arbitrary time records and assume they become
a dated transient forcing.

## Land mask and orography

The atmospheric `surface_ini`/`surfini` path reads and prepares the surface
fields, including the land mask and spectral orography initialization.
Orography in the input is geopotential in m²/s²; a terrain height in metres
requires multiplication by the intended gravity. Preserve the coupled land
mask supplied with LSG when using that configuration.

The current surface initialization clips land-mask values to the interval
0–1; it does not apply the old guide's threshold at 0.5. Preserve fractional
values deliberately and inspect how the active land/sea routines use them.

`NOROMAX` belongs to `surfmod_nl`. The old guide's `OROSCALE` listing does
not make that name an accepted current `surfmod_nl` input: use the
{doc}`../reference/namelist-inventory` when adding overrides. Inspect the
current `nspinit` path before altering spectral initialization.

## Prepare and inspect data

The repository supplies `nc2sra`, `sra2nc`, `makesra`, `earth.sh`, and
`aqua.sh`, as well as topography helpers. They have different assumptions
about grid, field count, and working directory. Start with a copy of the
existing matching dataset, run a small conversion, and verify dimensions,
coordinates, units, and codes before replacing experiment inputs.

For a checked-in T21 mask, from the repository root:

```sh
bash scripts/sra2nc plasim/dat/T21/N032_surf_0172.sra mask.nc
cdo -s griddes mask.nc
cdo -s infon mask.nc
```

Run conversions in a scratch directory if you want to keep products outside
the checkout, using absolute paths to the script and input. `sra2nc` expects
the supported formatted record sizes (T21/T42, single or climatological
sets); it is not a general reader for every possible Service text file.
For NetCDF-to-SRA, `nc2sra` takes `input.nc output.sra code` with optional
`-d YYYYMMDD` and `-t HHMM`; verify the produced header and field length.

Keep postprocessor Service output, model boundary SRA text, and binary
restart files distinct. Their filenames can look similar while their
layouts and purposes differ.

## Sources checked

User's Guide §§2.2–2.3, 2.5, 2.14–2.16 and chapter 7 compared with
`surface_ini`, `code_surf_file`, `get_surf_array`, and `surfini` in
{repo}`plasim/src/surfmod.f90`, the selected module readers, MoSt `Build`,
and {repo}`scripts/sra2nc`/{repo}`scripts/nc2sra`.
