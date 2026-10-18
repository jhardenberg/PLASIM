# Convert and analyse model output

The original User's Guide chapter 5 describes Pumaburner. This repository
has two principal conversion paths: CDO-based `srv2nc`, used by the generated
run script, and the C++ `burn7` afterburner. The claim that Pumaburner is the
only interface to raw output is no longer current.

## Direct NetCDF conversion with srv2nc

`scripts/srv2nc` uses CDO to convert atmosphere, sea-ice, mixed-layer-ocean,
and LSG Service data to compressed NetCDF4 by default. It adjusts the
horizontal/vertical grid description and applies its parameter tables.
Use a separate scratch directory for manual conversions and preserve raw
inputs until the converted products have been checked.

From the repository root, for an existing atmospheric output file:

```sh
bash scripts/srv2nc plasim_output atmosphere.nc
bash scripts/srv2nc -m plasim_output atmosphere-monthly.nc
```

| Option | Current action |
| --- | --- |
| `-m` | Apply monthly averaging. |
| `-y` | Apply yearly averaging. |
| `-s` | Transform spectral fields to grid points in the atmospheric path. |
| `-u` | Derive horizontal wind components from divergence/vorticity in the spectral atmospheric path. |
| `-p` | Request sea-level pressure through the script's atmospheric spectral branch. |
| `-d code1,code2,...` | Remove listed field codes from the result. |
| `-f format` | Select an output format; default `nc4 -z zip`. |
| `-h` | Print the script's help. |

Not every option applies to every input type. The LSG branch builds separate
scalar/vector grids and depth axes; it is not the same operation as an
atmospheric spectral transform. Inspect the output grid, variable names,
vertical coordinates, and dates after conversion.

For example:

```sh
cdo -s sinfo atmosphere-monthly.nc
cdo -s showname atmosphere-monthly.nc
cdo -s showtimestamp atmosphere-monthly.nc
```

CDO names/units are converter metadata; see {doc}`../reference/output` and
the separate writer/converter inventories before interpreting them as raw
physical definitions. Raw output does not contain every derived quantity
listed in a postprocessor table.

## Build burn7

The current `postprocessor/makefile` builds `burn7.x` with a C++ compiler
and the **legacy NetCDF C++ interface** (`netcdfcpp.h`, `libnetcdf_c++`).
The NetCDF C library alone, or a newer incompatible C++ interface, is not
a substitute for that header/API.

```sh
make -C postprocessor
```

Adjust include/library search paths for the installed dependencies as
needed. `postprocessor/makefile_MAC` is a platform-specific example; its
`/opt/local` paths are not universal defaults. Keep compilation and analysis
products out of commits. Consult the {download}`burn7 quick reference
<../../../postprocessor/burn7qr.pdf>` alongside the current code.

## Select fields and levels

The afterburner's input is its own case-insensitive control text, read on
standard input. It is not a Fortran `&group ... /` namelist. For example,
save the following as `temperature.nl`:

```text
CODE = 130
HTYPE = G
VTYPE = P
hPa = 500
MEAN = 0
NETCDF = 1
```

Then, from the repository root with the required files present:

```sh
./postprocessor/burn7.x plasim_output temperature-500.nc < temperature.nl > burn7.log
```

The repository's `postprocessor/example.nl` demonstrates a similar setup
using a variable name. The historical three-field example should use
temperature code **130**, zonal wind **131**, and meridional wind **132**;
the explanatory sentence in the old guide misnumbers the winds.

| Control | Meaning in current burn7 |
| --- | --- |
| `HTYPE` | `G` Gaussian grid, `S` spherical harmonics, `F` Fourier coefficients, `Z` zonal means. Current parser default is `G`. |
| `VTYPE` | `P` pressure levels or `S` sigma/model levels. Current parser default is `P`. |
| `MODLEV` | Select model levels when using sigma output; levels run from model top to bottom. |
| `hPa` | Requested pressure levels in hectopascals, not pascals. |
| `CODE` | Field selection, subject to available inputs and derived-field dependencies. |
| `MEAN` | `0` preserves time samples; `1` requests monthly means. Other deviation modes have representation/output restrictions. |
| `NETCDF` | NetCDF output when compiled with that support; otherwise Service output. |
| `HEAD7` | Override the corresponding user slot in afterburner Service output. |
| `MULTI` | Process a sequence of input files using the supported naming convention. |

Choose `HTYPE`, `VTYPE`, averaging, and levels explicitly in a reproducible
recipe. NetCDF output and some derived fields restrict valid representations.
The current command line supports `-c` for its code list, `-d` for debug,
`-m`, `-n`, and `-s` for reduced-memory operation. **`-g` now requests GrADS
control output, not the GRIB output described by the old manual.**
Do not carry the old `GRIB`/`HHMM` control table over as current behavior.

The current output metadata can carry planetary constants from model code
333; `radius`, `gravity`, `gascon`, and `lapse` overrides in burn7 control
text remain available. Use constants matching the experiment.

## CMOR-style extraction

`scripts/burn.sh` wraps burn7 and CDO to rename fields, change signs/units,
and compute selected derived quantities. Its interface is
`burn.sh [options] infile outfile variable`; `-s` requests sigma levels,
`-a` bypasses its CMOR-style conversion, and `-p` supplies pressure levels
in hPa. Default pressure levels are
`20,30,50,70,100,150,200,250,300,400,500,600,700,850,925,1000`.

This is a separate transformation from `srv2nc`. For example, the extraction
expressions multiply precipitation by 1000, reverse some upward-flux signs,
convert cloud fractions to percent, and derive albedo from shortwave fluxes.
Use the actual expression for the requested field; a familiar variable name
is not evidence of identical units or sign conventions across both paths.
The retained {download}`script guide <../../../scripts/README_burn.txt>`
provides its historical field categories. Current script configuration and
open supporting-tool issues are tracked separately from this manual.

## Sources checked

User's Guide chapter 5 and script/postprocessor notes compared with
{repo}`scripts/srv2nc`, {repo}`scripts/burn.sh`, current Makefiles,
`Usage`, `parini`, `InitAll`, `ServiceGrid`, and the option parser in
{repo}`postprocessor/burn7.cpp`. Runtime checks cover srv2nc on real model
output; burn7 was reviewed from source because its legacy C++ dependency
was not available in the validation environment.
