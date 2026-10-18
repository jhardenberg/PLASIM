# Inspect and visualize results

User's Guide chapter 6 describes GrADS and Vis5D workflows. Start from a
correctly converted dataset and inspect its coordinates and physical units
before choosing a plotting tool. NetCDF conversion does not by itself prove
that a field is on a regular latitude grid or on pressure levels.

## Inspect NetCDF with the tools used by this repository

For an output file already produced by `srv2nc`:

```sh
cdo -s sinfo atmosphere.nc
cdo -s showname atmosphere.nc
cdo -s showtimestamp atmosphere.nc
cdo -s griddes atmosphere.nc
cdo -s zaxisdes atmosphere.nc
```

These commands check available fields, dates, horizontal representation,
and vertical coordinates without requiring a graphical display. A file can
contain both Gaussian and spectral fields; use the appropriate transformation
before a grid-based operation. Scalar and vector LSG fields also use different
grid descriptions.

For a gridpoint near-surface temperature field named `tas`, a quick spatial
mean series can be inspected with:

```sh
cdo -s outputtab,date,value -fldmean -selname,tas atmosphere.nc
```

This illustrates data inspection, not a climate-equilibrium or validation
criterion. Check the available name in your particular conversion first.
When plotting precipitation or heat flux, state the units and sign convention
from the selected output path; see {doc}`../reference/output`.

## GrADS paths retained in the code

Current burn7 has a `-g` option that writes a GrADS control file for Service
plotting. With explicit gridpoint controls in `fields.nl`, a typical form is:

```sh
./postprocessor/burn7.x -g plasim_output fields.srv < fields.nl > burn7.log
```

Do not also request NetCDF for this GrADS path: the current program disables
GrADS output when NetCDF is selected. The repository additionally contains
`tools/srvctl.f90` for a binary Service descriptor and `tools/sractl.f90` for
formatted Service input. Their input records must maintain consistent field
and level ordering. They do not turn arbitrary model files or restart files
into plotting-ready datasets.

## Historical Vis5D recipes

The old manual describes conversion through external `puma2srv`/`puma2v5d`
and Vis5D tools. Those converters are not provided as a maintained workflow
in this checkout. Preserve that material in the original guide rather than
presenting its old executable names or workstation setup as current commands.
Use a viewer compatible with the verified NetCDF output, or validate an
external conversion separately.

## Sources checked

User's Guide chapter 6 compared with burn7 `WriteGradsCtl` and its option
parser, {repo}`tools/srvctl.f90`, {repo}`tools/sractl.f90`, and the srv2nc
grid branches. The CDO inspection commands were exercised on the generated
Earth NetCDF output; external graphical applications were not exercised.
