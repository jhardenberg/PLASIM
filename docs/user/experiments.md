# Experiment directories and long simulations

This chapter adapts sections **1.2–1.5** of the original *Planet Simulator
User's Guide*: the MoSt directory, model build phase, model run phase, and
running long simulations. The original guide's build/run separation remains
useful today. The paths and commands below describe this PlaSim-focused
checkout, rather than the former `Most16` package containing PUMA as well.

## Where MoSt puts your files

Keep the repository layout intact: MoSt uses relative paths between its
source, data, build, binary, and run directories. Run `configure.sh` and
`most.x` from the repository root.

| Directory | Purpose | How to use it |
| --- | --- | --- |
| `plasim/src` | Permanent Fortran sources and build rules | Make lasting code changes here. |
| `plasim/dat` | Initial/boundary data and configuration resources | MoSt selects the data matching the chosen resolution and planet. |
| `docs` | Sphinx user and developer manual | Consult it for supported workflows and input conventions. |
| `plasim/doc` | Historical manuals and reference material | Retained source material for the current manual. |
| `plasim/bld` | Copied sources, generated resolution module, build script, and compilation products | Treat as a generated working area. |
| `plasim/bin` | Built model executables | MoSt names executables according to the selected configuration. |
| `plasim/run` | Prepared executable, input data, namelists, and run script | Use for an initial check; copy the setup elsewhere for a lasting experiment. |

`configure.sh` creates the generated directories when needed. Preserve any
experiment edits and outputs outside them before reconfiguring or cleaning.

## What happens during the build

MoSt writes `plasim/bld/most_plasim_build` and executes it. The script copies
the permanent sources from `plasim/src`, assembles a Makefile using the
detected compiler settings, and invokes Make. MoSt writes `resmod.f90` for
the selected latitudes, vertical levels, and processor count, and selects
the planet, GUI, MPI, and ocean modules for that setup.

For T21, 10 levels, and one core, the executable is named
`most_plasim_t21_l10_p1.x`. MoSt places it in `plasim/bin` and copies it into
`plasim/run`, along with boundary data and configuration files. The filename
encodes resolution and processor count; it is not a complete record of the
source revision, physical settings, or compiler flags. Retain those with
your experiment as well.

Make can reuse compiled objects in the generated build directory. Editing a
copied source there does not make a lasting change: the next preparation
copies `plasim/src` again. To force a fresh build after preserving any files
you need, run from the repository root:

```sh
./cleanplasim
```

This removes the generated contents of **all three** directories
`plasim/bld`, `plasim/bin`, and `plasim/run`, including any run output stored
there. Then prepare the experiment again with MoSt. This updates the old
guide's advice about cached executables to the current build procedure.

## What happens during run preparation

MoSt writes namelists such as `plasim_namelist` and `planet_namelist` and the
script `most_plasim_run`. **Save & Exit** prepares these files without
starting the run. **Save & Run** prepares them and launches the script.
The current `most.x -c` option performs the preparation step without opening
the MoSt window; see {doc}`most` for a configuration-file example.

Inspect the prepared namelists rather than assuming they match the defaults
of a directly launched executable. For example, MoSt selects a Gregorian
calendar for the Earth mixed-layer setup in the previous chapter, while
the direct model defaults to a 360-day calendar. Re-running MoSt can replace
your edited namelists and run script, so preserve customized setups in their
own directories.

## Set up a directory for a long experiment

The original guide recommends keeping long simulations on a filesystem
with sufficient free space and checking disk quotas. Estimate space for
output, diagnostics, and restart files before starting. Local storage may
avoid network-filesystem overhead; choose storage appropriate to your
machine or cluster and its backup policy.

First prepare an experiment with MoSt. Choose the model, resolution, output
settings, and number of years. Keep **Run with GUI** disabled for normal and
production runs. Select **Save & Exit**, or use the headless equivalent.
Copy the contents of the freshly prepared `plasim/run` to a new experiment directory.
For example, from the repository root:

```sh
mkdir -p experiments
mkdir experiments/earth-control
cp -R plasim/run/. experiments/earth-control/
cd experiments/earth-control
```

Use a different location if the repository filesystem is unsuitable for
long output. Keep experiment directories and model products out of commits.
The second `mkdir` deliberately requires a new directory so an existing
experiment is not silently reused.

Before running, edit `most_plasim_run` to set `EXP` to a meaningful name,
review the segment loop and namelists, and check the `srv2nc` path. The
current generated script records an absolute path to the checkout's
`scripts/srv2nc`; update it if the experiment is transferred to another
machine or the checkout moves. Retain a copy of the MoSt configuration,
namelists, run script, executable, source revision, and compiler options.

On a workstation, you can start the script in the foreground:

```sh
./most_plasim_run > run.log 2>&1
```

Use the local scheduler's submission procedure on a cluster. For a long
unattended workstation run, arrange process/session management appropriate
to your system; appending `&` alone does not make a job survive logout.

## Output segments and restart handoff

With the simulation GUI disabled, the generated script normally runs one
model year per invocation, copies `plasim_status` to `plasim_restart` for
the next segment, and archives segment products. It creates `output/` for
converted output and diagnostics and `restart/` for saved state. Its default
`average="-m"` setting requests monthly means from `srv2nc`.

Check output and postprocessing for a short trial before committing to a
long integration. The generated script removes `plasim_restart` at startup:
**launching the whole script again is not a resume command**. Continuing an
interrupted experiment requires deliberately restoring a compatible saved
restart, setting the remaining segment range, and adapting the initialization
line so the restored state is retained. LSG runs also need their ocean
restart products. A complete recovery recipe is planned separately.

## Sources and attribution

Adapted and paraphrased from chapter 1, sections 1.2–1.5 (printed pages 5–7),
of the University of Hamburg's *Planet Simulator User's Guide*, version
16.0, by Frank Lunkeit, Simon Blessing, Klaus Fraedrich, Heiko Jansen,
Edilbert Kirk, Ute Luksch, and Frank Sielmann. The original is available on
{doc}`../sources`.

The directory roles and long-run workflow come from that guide. Current
details were checked against {repo}`configure.sh`, {repo}`cleanplasim`,
{repo}`most.c` (`Build`, `WriteNamelistFile`, and `WriteRunScript`), and the
README/FAQ. Headless preparation, automatic NetCDF conversion, current
calendar selection, and the restart-startup caveat are updates for this
repository. No scientific Reference Manual material is included.
