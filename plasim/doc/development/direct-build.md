# Alternative direct-Make build and CI example

The recommended user workflow is {doc}`../user/most`. This optional
developer example shows how the CI build works by calling Make directly.

It compiles a serial Earth model at T21 horizontal resolution
(64 longitudes × 32 latitudes) with 10 atmospheric levels. It uses the
checked-in T21 boundary data and the mixed-layer ocean configuration without
LSG coupling. It is a short build/run check and a way to inspect runtime controls,
not a spun-up climate experiment.

The workflow adapts the build/run separation described in the original
User's Guide, chapter 1, to the headless build used by the current regression
suite. It invokes the model directly, so you do not need to build MoSt or
install X11. MoSt remains the standard way to select and build user experiments,
including when its configuration-file mode is used without a display.

## Requirements and working directories

Run the commands from the repository root on Linux or macOS with Bash, a
Fortran compiler named `gfortran`, a C compiler named `cc`, and `make` on
your `PATH`. The script uses the existing `make_plasim` rules, compiles with
`-O0 -fdefault-real-8`, and selects serial communication, GUI, and LSG stubs in a fresh
temporary directory. These flags match the short regression builds; a
production build and its numerical results need separate validation.

The checkout supplies all model inputs for this example. Build files and
outputs go into separate `build` and `run` directories under the reported
temporary workspace. The script retains that workspace for inspection and
creates a new one each time it runs.

## Choose the runtime controls

Fortran namelists are plain text. A file such as `plasim_namelist` contains a
group beginning with `&plasim_nl` and ending with `/`. Runtime namelists do
not change this executable's compiled resolution or processor count.

(headless-parameters)=
### Parameters used here

Defaults below are for a direct Earth executable built from the current
sources, before reading user input. MoSt-generated files or other planet
modules can prescribe different values. All rows belong to `plasim_nl` in
`plasim_namelist` except `nfixorb`, which belongs to `planet_nl` in
`planet_namelist`.

| Parameter | Type and units | Source default | Example value | Purpose |
| --- | --- | --- | --- | --- |
| `n_start_year` | integer, calendar year | `2000` | `2000` | Cold-start year; a restart restores its own model clock. |
| `n_days_per_year` | integer, model days | `360` | `360` | Equal 30-day months here; `365` selects the Gregorian calendar, including leap years. |
| `n_run_years` | integer, years | `0` | `0` | Leave the month/year countdown disabled in this short example. |
| `n_run_months` | integer, months | `0` | `0` | Additional calendar months to integrate. |
| `n_run_days` | integer, model days | `0` | `2` | Run for two model days. |
| `n_run_steps` | integer, timesteps | `0` | `0` | Additional steps in the day/step countdown. |
| `mpstep` | integer, minutes | `0` (automatic) | `45` | Requested timestep; automatic selection also gives 45 minutes at T21 Earth. |
| `kick` | integer switch | `1` | `0` | Disable the initial noise perturbation. |
| `ngui` | integer switch | `0` | `0` | Disable the simulation GUI. |
| `seed` | integer array, 8 elements | all `0` | all `1` | Supply a fixed random seed; all zeros select clock-based initialization. |
| `nfixorb` | integer switch | `1` | `1` | Keep prescribed Earth orbital elements fixed. |

The script writes these choices explicitly, including all eight seed
elements. Empty groups in the other namelist files retain their module
defaults. The source definitions are in {repo}`plasim/src/plasimmod.f90`,
the Earth presets in {repo}`plasim/src/p_earth.f90`, and timestep selection
and run control in {repo}`plasim/src/plasim.f90`.

### From a timestep to an integration length

For the Earth setup here, `solar_day` is 86,400 seconds and the requested
45-minute step divides the day exactly. The full timestep and steps per day
are related by

```{math}
:label: earth-timestep

\begin{aligned}
\Delta t &= 60\,\mathtt{mpstep} = 2700\ \mathrm{s}, \\
N_{\mathrm{day}} &= \frac{86400\ \mathrm{s}}{\Delta t} = 32.
\end{aligned}
```

With `n_run_years=n_run_months=0`, the day/step countdown is

```{math}
:label: short-run-length

\begin{aligned}
N_{\mathrm{run}} &= \mathtt{n\_run\_days}\,N_{\mathrm{day}} \\
&\quad + \mathtt{n\_run\_steps} \\
&= 2\times32+0=64.
\end{aligned}
```

Equation {eq}`short-run-length` counts full integration-loop steps; the
model also performs shorter initialization steps. These are operational
relations from the run-control code, not a migration of the scientific
Reference Manual. The general timestep selector uses integer arithmetic
and makes the steps-per-day count even; equation {eq}`earth-timestep` should
not be used to infer arbitrary planetary timestep behavior. Check the
effective timestep and calendar printed in `plasim_diag`.

Keep the year/month controls at zero when following this day/step example;
do not combine the two stopping conventions without checking the run logic.

## Build and run

From the repository root:

```sh
bash plasim/doc/examples/headless-earth.sh
```

The script prints its workspace path before compiling and reports success
only after checking for a model abort and nonempty output products. Compiler
and model messages remain visible. To inspect the exact procedure, download
{download}`headless-earth.sh <../examples/headless-earth.sh>` or read it below.

```{literalinclude} ../examples/headless-earth.sh
:language: bash
:caption: Complete build-and-run example (the same file exercised by CI).
```

## Inspect the results

In the printed workspace's `run` directory, expect:

| File | Meaning | First check |
| --- | --- | --- |
| `plasim_diag` | Text diagnostics, namelist echo, and configuration summary | Confirm a 45-minute step, 32 steps per day, the 360-day calendar, year 2000, and a two-day run. |
| `plasim_output` | Atmospheric output in binary Service format | Confirm it is nonempty; use a postprocessor to inspect fields. |
| `plasim_status` | Final atmospheric restart state | Retain it with the namelists if you plan a continuation. |

You can use `less /path/printed/by/the/script/run/plasim_diag` to review the
diagnostics; replace the example path with the actual workspace. A fixed
seed makes repeated runs within a given build reproducible, but does not
guarantee byte-identical results across compilers or platforms.

The root README describes `scripts/srv2nc` for conversion to NetCDF with CDO,
and `burn7`/`burn.sh` for other postprocessing workflows. Those tools are
not prerequisites for this example. Their full Sphinx chapters are
{doc}`planned <../outline>`.

## Continue or troubleshoot

- **Model abort or missing products:** inspect the compiler output,
  `run/plasim_diag`, and `run/Abort_Message` if present. A successful process
  exit alone is insufficient because some Fortran stops return success.
- **Namelist rejected:** check the group and spelling against the current
  source, not just the historical User's Guide. For example, `psurf` now
  belongs to `planet_nl`, and several old albedo controls were removed.
- **Source edits have no effect:** this example always copies
  `plasim/src` to a fresh build directory. In a MoSt workflow, cached binaries
  may be reused; the root FAQ explains how to rebuild after preserving outputs.
- **Restarting:** the input name is `plasim_restart`; the completed run writes
  `plasim_status`. Copying the latter to the former selects continuation on
  the next invocation in that run directory. Archive the first segment's
  outputs and keep the compatible namelists and executable before rerunning.
  This chapter's `nfixorb=1` avoids the initialization-only orbital recalculation
  behavior described in the README/FAQ for `nfixorb=0`.

Do not use this two-day run to infer equilibrium, long-term stability, or a
validated climate. The existing {download}`test guide <../../../tests/README.md>`
describes stronger short-run checks, restart comparisons, and the separate
MPI and LSG configurations.

## Sources and attribution

The workflow follows chapter 1 (installation and build/run directories) of
the University of Hamburg's *Planet Simulator User's Guide*, version 16.0,
by Frank Lunkeit, Simon Blessing, Klaus Fraedrich, Heiko Jansen, Edilbert
Kirk, Ute Luksch, and Frank Sielmann. Current commands and defaults are
checked against the repository README, FAQ, `tests/test_model.py`,
`resmod_def.f90`, `make_plasim`, and the model sources linked above. See
{doc}`../sources` for the original material and migration scope.
