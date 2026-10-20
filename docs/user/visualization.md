# Inspect and visualize results

Start from a NetCDF dataset produced by {doc}`postprocessing` and inspect
its coordinates and physical units before plotting. NetCDF conversion does
not by itself prove that a field is on a regular latitude grid or on
pressure levels.

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

## Plot a temperature map with Python

This example uses xarray to read near-surface air temperature (`tas`) and
Matplotlib to draw a longitude–latitude map of the first output time.
Install these optional analysis packages in your Python virtual environment:

```sh
python -m pip install xarray matplotlib netCDF4 cftime
```

`netCDF4` supplies the NetCDF reader; `cftime` supports model calendars such
as a 360-day year. From the repository root, run the supplied script on your
converted atmospheric output:

```sh
python docs/examples/plot-temperature.py atmosphere.nc temperature-map.png
```

In a notebook, replace `sys.argv[1:]` with the two filenames:

```{literalinclude} ../examples/plot-temperature.py
:language: python
```

Open `temperature-map.png` to see the map. The colors use the variable's
recorded units; the script applies no unit conversion or additional time
averaging. The plot uses the dataset's latitude coordinates directly, including
Gaussian latitudes, and needs no regridding for this display.

Check `print(ds)` when adapting the example: it expects `tas`, `time`,
`lat`, and `lon` as produced by the atmospheric `srv2nc` path. `squeeze`
removes singleton dimensions such as a near-surface height axis. For a
three-dimensional field, select a level explicitly before plotting. Label
any alternative variable with its own units and sign convention.

For other plot types, see the [xarray plotting guide](https://docs.xarray.dev/en/stable/user-guide/plotting.html)
and [Matplotlib figure guide](https://matplotlib.org/stable/users/explain/figure/figure_intro.html).

## Sources checked

Variable code 167 (`tas`, kelvin) and the horizontal grid branches in
{repo}`scripts/srv2nc`. CDO inspection and the Python map example were
exercised on converted Earth output.
