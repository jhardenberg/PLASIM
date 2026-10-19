# Configuring experiments

Once you have prepared a baseline setup with MoSt ({doc}`most`) and copied
`plasim/run/` to a dedicated experiment directory ({doc}`experiments`), you
can customize your simulation.

Remember the distinction between **compile-time** and **runtime** settings:

- **Compile-time choices (require rebuilding with MoSt):** Horizontal
  resolution (`T21`, `T31`, `T42`), vertical levels, MPI core count, planet
  module (`Earth`, `Mars`, `Exo`), deep-ocean coupling (`LSG Ocean`), numerical
  precision, and the interactive X11 GUI.
- **Runtime choices (edit `*_namelist` files and `most_plasim_run`):**
  Integration length, calendar, orbital forcing, $\mathrm{CO_2}$ and radiation
  spectra, surface boundary datasets, and physical parameterization constants.

```{toctree}
:hidden:

planets
boundary-data
parallel-ocean
restarts
```

- **{doc}`planets`:** Planet presets, Gregorian vs. 360-day calendars, fixed
  vs. transient Berger orbits (`NFIXORB`), stellar-spectrum radiation, two-band
  albedos, and tidally locked illumination.
- **{doc}`boundary-data`:** Surface boundary files (`Nnnn_surf_cccc.sra`),
  land–sea masks, geopotential orography, and converting between NetCDF and
  Service formats (`sra2nc`, `nc2sra`).
- **{doc}`parallel-ocean`:** Compiling and launching multi-core MPI runs and
  coupling PlaSim to the 3D LSG deep-ocean model.
- **{doc}`restarts`:** Managing `plasim_status` and `plasim_restart`,
  continuing runs across segments in `most_plasim_run`, and preserving
  reproducibility.

For a quick lookup of namelist groups and common parameters, see the
{doc}`namelist overview <../reference/namelists>`, or consult the
{doc}`detailed parameter tables <../reference/parameters/index>` for every
accepted variable's type, units, default, and code interactions.
