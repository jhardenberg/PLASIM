# Experiment directories and long simulations

This chapter explains how MoSt organizes source, build, binary, and run
directories, how to move a prepared setup out of `plasim/run` into a dedicated
experiment directory, and how to manage or extend multi-year simulations with
`most_plasim_run`. It adapts sections **1.2–1.5** of the original *Planet
Simulator User's Guide* to the current repository layout.

## Repository directory layout

MoSt uses relative paths between its source, data, build, binary, and run
directories. Always run `./configure.sh` and `./most.x` from the repository
root.

| Directory | Purpose | How to use it |
| --- | --- | --- |
| `plasim/src` | Permanent Fortran/C sources and `make_plasim` rules | Make permanent code changes here. |
| `plasim/dat` | Atmospheric boundary data (`T21`, `T31`, `T42`, `T21_mars`, `T21_exo`, etc.) and GUI layouts | MoSt copies the files matching your selected planet and resolution into `plasim/run`. |
| `lsg/src`, `lsg/dat` | LSG deep-ocean sources, grid/mask data, and initial ocean restarts | Used when **LSG Ocean** is enabled in MoSt. |
| `plasim/bld` | Generated build script (`most_plasim_build`), `resmod.f90`, copied sources, and `.o`/`.mod` files | Treat as a temporary compilation scratch area; never edit sources here permanently. |
| `plasim/bin` | Compiled model executables (such as `most_plasim_t21_l10_p1.x`) | Cached by resolution, levels, and core count. |
| `plasim/run` | Staging directory where MoSt places the executable, boundary data, `*_namelist` files, and `most_plasim_run` | Use for quick tests, or copy to a dedicated directory for production runs. |
| `scripts` | Postprocessing and data-conversion tools (`srv2nc`, `sra2nc`, `nc2sra`, `burn.sh`) | Invoked by `most_plasim_run` or manually for data preparation and analysis. |
| `docs` | Sphinx user and developer manual | Current documentation and runnable examples. |

## What happens during the build and preparation phases

### 1. The build phase (`plasim/bld` and `plasim/bin`)

When you select **Save & Exit**, **Save & Run**, or `./most.x -c`, MoSt writes
and executes `plasim/bld/most_plasim_build`. That script:

1. Writes `plasim/bld/resmod.f90` with the compiled dimensions (`NLAT_ATM`,
   `NLEV_ATM`, and `NPRO_ATM`).
2. Copies all source files from `plasim/src/` (and `lsg/src/lsgmod.f90` if LSG
   is enabled) into `plasim/bld/`.
3. Concatenates the compiler configuration (`most_compiler` or
   `most_compiler_mpi`, plus optional `most_debug_options` and
   `most_precision_options`) with `make_plasim` to create `plasim/bld/makefile`.
4. Runs `make -e` with environment variables selecting the planet module
   (`PLAMOD`), ocean/coupler (`OCEAN`, `OCEANCOUP`), MPI (`MPIMOD`), and GUI
   (`GUIMOD`, `PUMAX`) implementations.
5. Copies the resulting binary to `plasim/bin/most_plasim_t<trunc>_l<levels>_p<cores>.x`
   and into `plasim/run/`.

Because `make` reuses existing `.o` files in `plasim/bld/` when timestamps
permit, and because the executable name only encodes resolution, levels, and
cores, run `./cleanplasim` from the repository root whenever you want to force
a completely clean rebuild:

```sh
./cleanplasim
```

```{warning}
`./cleanplasim` deletes all generated files in `plasim/bld`, `plasim/bin`,
**and** `plasim/run` (including any outputs left in `plasim/run`). Copy any
experiment files or outputs you want to keep before running `./cleanplasim` or
re-running MoSt.
```

### 2. The run-preparation phase (`plasim/run`)

After compiling, MoSt populates `plasim/run/` with:

- The compiled executable (`most_plasim_t21_l10_p1.x`).
- Boundary data files (`N032_surf_*.sra`, plus `lsg/dat/*` if LSG is enabled)
  and `GUI.cfg`.
- All 12 Fortran namelist files (`plasim_namelist`, `planet_namelist`,
  `radmod_namelist`, `landmod_namelist`, `vegmod_namelist`, `oceanmod_namelist`,
  `icemod_namelist`, `seamod_namelist`, `surfmod_namelist`, `fluxmod_namelist`,
  `rainmod_namelist`, `miscmod_namelist`).
- The driver script `most_plasim_run`.

```{note}
MoSt's generated namelists can differ from the internal Fortran defaults of a
directly launched executable. For example, MoSt sets `N_DAYS_PER_YEAR=365`
(Gregorian calendar) for uncoupled Earth runs and `N_DAYS_PER_YEAR=360` when
LSG is enabled, whereas a raw executable with an empty `plasim_namelist`
defaults to `360`. Always inspect the generated `*_namelist` files in your run
directory.
```

## Setting up a dedicated directory for a long experiment

Because re-running MoSt overwrites `plasim/run/`, you should copy the prepared
directory to a separate folder before editing namelists or launching a long
simulation:

1. **Prepare the baseline setup in MoSt:** Choose your planet, resolution, core
   count, and ocean modules, disable **Run with GUI**, and select **Save & Exit**
   (or run `./most.x -c your_config.cfg`).
2. **Copy `plasim/run` to a new experiment directory:** Choose a filesystem
   with enough disk space for multi-year NetCDF outputs and restarts. For
   example:

   ```sh
   mkdir -p experiments
   mkdir experiments/earth-control
   cp -R plasim/run/. experiments/earth-control/
   cd experiments/earth-control
   ```

   (Using `mkdir experiments/earth-control` without `-p` on the target folder
   prevents accidentally overwriting an existing experiment.)

3. **Customize the namelists and `most_plasim_run`:** Inside
   `experiments/earth-control/`:
   - Edit `*_namelist` to adjust physical parameters (for example, `CO2` in
     `radmod_namelist`). Keep `N_RUN_YEARS=1` in `plasim_namelist` so each loop
     iteration of `most_plasim_run` integrates one model year.
   - Edit `most_plasim_run` to set a descriptive experiment prefix (such as
     `EXP=EARTH_CTRL`) and your desired total number of years (`YEAR1=1`,
     `YEAR2=30`).
   - Choose whether to apply monthly averaging: by default, `most_plasim_run` sets
     `average="-m"`, which instructs `srv2nc` to compute monthly means when
     converting raw output to NetCDF. Comment this out (`#average="-m"` or set
     `average=""`) if you need daily or timestep-frequency outputs (set by `NWPD`
     in `plasim_namelist`).
   - Verify the `srv2nc=/abs/path/to/scripts/srv2nc` line in `most_plasim_run`
     if you moved the checkout or copied the directory to another machine.
   - Save a copy of your `.cfg` file, git commit hash, and compiler flags
     alongside the experiment for provenance.

4. **Launch the simulation:** On a workstation, redirect stdout and stderr to a
   log file:

   ```sh
   ./most_plasim_run > run.log 2>&1
   ```

   On an HPC cluster, invoke `./most_plasim_run` inside your batch scheduler
   script (SLURM, PBS, etc.). For long unattended runs on a workstation, use
   `nohup`, `tmux`, or `screen` so the job survives terminal disconnects.

## How `most_plasim_run` manages multi-year segments and restarts

When `NGUI=0`, `most_plasim_run` integrates a multi-year experiment as a
sequence of 1-year segments (`for ((YEAR=$YEAR1; YEAR<=$YEAR2; YEAR++))`):

- **End of segment `YEAR`:** The model writes its final atmospheric/land/ocean/ice
  state to `plasim_status`.
- **Handoff to segment `YEAR+1`:** `most_plasim_run` executes:
  ```bash
  if [ -e plasim_status ]; then
     cp plasim_status plasim_restart
     mv plasim_status restart/$RESTNAME
  fi
  ```
  When the model starts segment `YEAR+1`, it detects `plasim_restart` in the
  working directory, restores the saved state and model clock, and integrates
  the next year.
- **Continuing an interrupted or completed run:** Remember that line 12 of
  `most_plasim_run` is `rm -f plasim_restart`. If a 30-year run stops after
  segment 10 (or if you want to extend a finished 10-year run to year 20),
  **do not** simply run `./most_plasim_run` again unmodified. That would delete
  `plasim_restart` and start over from year 1. Instead:
  1. Copy the last good restart file into place as `plasim_restart` (for
     example, `cp restart/EARTH_CTRL_REST.0010 plasim_restart`, plus the matching
     LSG restart files if using LSG; see {doc}`restarts`).
  2. In `most_plasim_run`, comment out `#rm -f plasim_restart` and set
     `YEAR1=11` and `YEAR2=20` before launching the script.

## Sources and attribution

Adapted and paraphrased from chapter 1, sections 1.2–1.5 (printed pages 5–7),
of the University of Hamburg's *Planet Simulator User's Guide*, version 16.0,
by Frank Lunkeit, Simon Blessing, Klaus Fraedrich, Heiko Jansen, Edilbert Kirk,
Ute Luksch, and Frank Sielmann. The original is available on {doc}`../sources`.

Current directory roles, build scripts, and run-script behavior were checked
against {repo}`configure.sh`, {repo}`cleanplasim`, {repo}`most.c` (`Build`,
`WriteNamelistFile`, and `WriteRunScript`), and the repository README/FAQ.
