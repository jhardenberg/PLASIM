# Configure, compile, and run with MoSt

Use **MoSt**, the model starter (`most.x`), to build PlaSim and prepare an
experiment. MoSt selects the resolution and modules, compiles the executable,
and writes the namelists and run script. It supports both a graphical
interface and a configuration-file workflow for machines without a display.

This chapter follows the installation sequence in the original User's Guide,
section 1.1, and adds the current headless option. The next chapter,
{doc}`experiments`, adapts sections 1.2–1.5 on directories, building, and
running long simulations.

## Install the tools and configure MoSt

For the standard setup, provide a Fortran 90 compiler such as `gfortran`,
C and C++ compilers, Make, Bash, and X11 development headers and libraries.
MPI is optional for serial experiments. The generated run script uses
`scripts/srv2nc` to convert output, so install CDO as well when following
the output-producing example below.

From the repository root:

```sh
./configure.sh
./most.x -h
```

`configure.sh` detects the tools, creates compiler-option files and the
build/run directories, and builds `most.x`. Check its output and confirm
that the executable was produced. The current MoSt binary links to X11
even when invoked with `-c`; that option avoids opening a display, but does
not remove the build-time header or link-library requirements. A model
built with **Run with GUI** disabled uses GUI stubs.

## Choose an experiment in the graphical interface

Start MoSt from the repository root:

```sh
./most.x
```

For a first serial Earth setup, choose **Planet Simulator**, **Earth**, T21
(64 × 32), 10 levels, and one core. Enable **ML Ocean**, **Sea Ice**,
**Double Precision**, and **Write Output**; leave **LSG Ocean** disabled.
Set **Start year** to 2000 and **Years to run** to 1. Disable **Run with GUI**
for a simulation without the interactive model display.

Choose **Save & Exit** to compile and prepare the experiment for review before
launching it. **Save & Run** also starts the generated run script. The MoSt
window and the model's own simulation GUI are separate: disabling **Run with
GUI** affects the model executable, not the MoSt configuration window.

## Prepare the same setup without a display

The supplied {download}`most-earth.cfg <../examples/most-earth.cfg>` selects
a one-year T21/L10 Earth experiment with one core, a mixed-layer ocean and sea
ice, output enabled, and the model GUI disabled. It fixes the orbital elements
with `NFIXORB=1` and requests double precision.

From the repository root, after configuring MoSt:

```sh
cp plasim/doc/examples/most-earth.cfg earth.cfg
./most.x -c earth.cfg
```

```{literalinclude} ../examples/most-earth.cfg
:language: ini
:caption: MoSt configuration for the first Earth experiment.
```

This file uses MoSt's setting labels and a `[MoSt ...]` header. It is not a
Fortran namelist. For another setup, edit a copy or save a configuration from
the GUI. MoSt writes its settings to `most_last_used.cfg`; the command
`./most.x -c` reads that file when no explicit path is supplied. If a file
cannot be read or has an invalid header, MoSt reports that it is using
defaults, so inspect the messages and generated settings before proceeding.

**`-c` builds and prepares the experiment, then exits; it does not start
the simulation.** It follows the same preparation path as **Save & Exit**.
It also does not override **Run with GUI** in the saved configuration: keep
that setting at zero when preparing a fully headless model run.

## Review and start the simulation

For the supplied setup, check for
`plasim/run/most_plasim_t21_l10_p1.x`, `plasim/run/most_plasim_run`, and the
`*_namelist` files. The model should have `NGUI=0`, `N_START_YEAR=2000`,
`N_RUN_YEARS=1`, and `N_DAYS_PER_YEAR=365` in `plasim_namelist`, plus
`NFIXORB=1` in `planet_namelist`. MoSt selects the Gregorian calendar for
this Earth setup without LSG. The separate developer/CI example uses a
360-day calendar and different explicit runtime choices.

Before starting, review `most_plasim_run`: choose an experiment name through
`EXP`, confirm the loop length (`YEAR1`/`YEAR2`), and check its postprocessing
command. For this one-year example, `YEAR1=YEAR2=1`. With the model GUI off,
MoSt normally prepares annual invocations with restart handoff between them.

For an initial run in the generated directory:

```sh
cd plasim/run
./most_plasim_run
```

The script writes converted atmospheric/ocean/ice output and diagnostics
under `output/`, and stores restart products under `restart/`. For example,
the default experiment name produces `output/MOST_DIAG.0001.txt`. The suffix
`0001` is the script's segment counter, not the calendar year. Check the
diagnostics for the configured date, timestep, and any abort message, and
confirm that the expected converted files are nonempty.

For a long experiment, first move the prepared setup to a dedicated
directory as described in {doc}`experiments`. One year from an initial state
is a workflow example, not an equilibrated or validated climate.

## Further reading

The root {download}`README <../../../README.md>` and
{download}`FAQ <../../../FAQ.md>` cover platform notes, postprocessing,
namelist compatibility, and orbital configuration. In particular, the
`NFIXORB=0` orbital calculation occurs at initialization and can depend on
restart frequency. The fixed-orbit choice here avoids that particular issue.

For contributors interested in the compiler and runtime details, Part II
contains an {doc}`alternative direct-Make build <../development/direct-build>`.
It is also the short example executed by the documentation CI workflow.

## Sources and attribution

Adapted from section 1.1 of the University of Hamburg's *Planet Simulator
User's Guide*, version 16.0, with current behavior checked against the
repository README/FAQ, {repo}`configure.sh`, and {repo}`most.c` (`main`,
`ReadSettings`, `BuildScripts`, `SaveExit`, and `WriteRunScript`). The
configuration-file example describes this checkout and is an addition to the
historical guide. Full author attribution is in
{doc}`experiments` and the original guide on the {doc}`../sources` page.
