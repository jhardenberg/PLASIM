# Configure, compile, and run with MoSt

**MoSt** (`most.x`, the Model Starter) is the standard tool for compiling
PlaSim-LSG TNG and preparing an experiment. When you configure an experiment
with MoSt, it:

1. Generates the resolution module (`resmod.f90`) and compiles the Fortran
   executable (`most_plasim_t<trunc>_l<levels>_p<cores>.x`) in `plasim/bld/`.
2. Copies the compiled executable and matching boundary datasets (`*.sra`,
   plus LSG inputs when enabled) into `plasim/run/`.
3. Writes the runtime Fortran namelist files (`*_namelist`) and the shell run
   script (`most_plasim_run`) into `plasim/run/`.

MoSt supports both an interactive X11 graphical window (`./most.x`) and a
headless configuration-file mode (`./most.x -c`) for remote servers without a
display.

## Step 1: Install prerequisites and build MoSt

To configure and build PlaSim through MoSt, install:

- **Compilers and build tools:** A Fortran 90 compiler (such as `gfortran`), C
  and C++ compilers (`gcc`/`cc`, `g++`/`c++`), `make`, and `bash`.
- **X11 development headers and libraries:** Required to compile `most.x`
  (for example, `libx11-dev` on Ubuntu/Debian or XQuartz on macOS), even if you
  plan to run `most.x -c` headlessly.
- **MPI (optional):** MPI Fortran/C wrappers (`mpif90`, `mpicc`) and launcher
  (`mpiexec`) for multi-core parallel runs.
- **CDO (Climate Data Operators):** Used by the generated `most_plasim_run`
  script (`scripts/srv2nc`) to convert raw Service output to NetCDF4.

From the repository root, run `configure.sh` to detect your compilers, create
the compiler-option files (`most_compiler`, `most_precision_options`, and
optional `most_compiler_mpi`), create the `plasim/bld`, `plasim/bin`, and
`plasim/run` directories, and compile `most.x`:

```sh
./configure.sh
./most.x -h
```

Check the terminal output to confirm that your Fortran and C compilers were
found and that `most.x` was built.

## Step 2: Configure and compile the model

You can configure and compile your experiment either interactively with the
MoSt GUI (Option A) or from the command line using a configuration file
(Option B).

```{note}
**Two distinct GUIs:** The **MoSt window** (`./most.x`) is used before the run
to choose settings and compile the model. The **simulation GUI**
(**Run with GUI** / `NGUI=1`) opens live X11 plots while the model integrates. Because the
simulation GUI is mainly for visual demonstration and teaching rather than
scientific production runs, always disable **Run with GUI** (`Run with GUI = 0`)
for standard and production experiments.
```

### Option A: Interactive GUI setup

Launch MoSt from the repository root:

```sh
./most.x
```

For a first serial Earth experiment:

1. Under **Model**, select **Planet Simulator** and **Earth**.
2. Under **Modules**, enable **ML Ocean** and **Sea Ice**; leave **LSG Ocean**
   off.
3. Under **Parallelism** and **Resolution**, set **Cores** to `1`, select
   **T21 [64x32]**, and set **Levels** to `10`.
4. Under **Options**, enable **Double Precision** and **Write Output**, and
   disable **Run with GUI** (recommended for all normal and production runs).
5. Under **Simulation**, set **Start year** to `2000` and **Years to run** to
   `1`.
6. Click **Save & Exit** to compile the model and populate `plasim/run/`
   without launching the simulation immediately (or click **Save & Run** to
   compile and launch `plasim/run/most_plasim_run` in the background).

### Option B: Headless setup with a `.cfg` file

On machines without an X11 display, or for reproducible scripted builds, pass
`-c` and a MoSt configuration file. The supplied
{download}`most-earth.cfg <../examples/most-earth.cfg>` configures the same
1-year serial T21/L10 Earth experiment with a mixed-layer ocean, sea ice,
double precision, output enabled, fixed orbit (`NFIXORB=1`), and the simulation
GUI disabled:

```sh
cp docs/examples/most-earth.cfg earth.cfg
./most.x -c earth.cfg
```

```{literalinclude} ../examples/most-earth.cfg
:language: ini
:caption: MoSt configuration file (docs/examples/most-earth.cfg).
```

Key points for `-c` mode:

- **Prepare only:** `./most.x -c` compiles the executable and writes the files
  in `plasim/run/`, then exits (equivalent to **Save & Exit**). It does **not**
  start the simulation.
- **Configuration format:** The `.cfg` file uses MoSt's `[MoSt ...]` header and
  option labels, not Fortran namelist syntax. Whenever MoSt exits, it saves the
  active settings to `most_last_used.cfg`. Running `./most.x -c` with no
  filename argument reads `most_last_used.cfg`.
- **Fallback warning:** If the specified `.cfg` file cannot be opened or lacks
  the `[MoSt` header, MoSt prints `Using default configuration` and falls back
  to internal defaults (which have `Run with GUI = 1` and `Write Output = 0`).
  Always check the terminal output and keep `Run with GUI = 0` in your `.cfg`
  file for headless runs.

## Step 3: Understand the prepared `plasim/run` directory

After Step 2 completes, inspect `plasim/run/`:

| Prepared file | Purpose |
| --- | --- |
| `most_plasim_t21_l10_p1.x` | Compiled PlaSim executable for T21, 10 levels, and 1 core. |
| `most_plasim_run` | Bash driver script that runs the model, manages restarts, and converts output to NetCDF (sometimes referred to informally as `most_plasim_run.sh`, though the generated file has no `.sh` extension). |
| `plasim_namelist`, `planet_namelist`, etc. | Runtime Fortran namelist files (`*_namelist`) read by the executable. |
| `N032_surf_*.sra` | Surface boundary-condition files for the T21 (32-latitude) Gaussian grid. |

For this Earth mixed-layer setup without LSG, MoSt writes `NGUI=0`,
`N_START_YEAR=2000`, `N_RUN_YEARS=1`, and `N_DAYS_PER_YEAR=365` (Gregorian
calendar) in `plasim_namelist`, and `NFIXORB=1` in `planet_namelist`.

```{important}
When **Run with GUI** is disabled (`NGUI=0`), MoSt always sets `N_RUN_YEARS=1`
inside `plasim_namelist` and sets `YEAR2` in `most_plasim_run` to your
requested **Years to run**. Multi-year integrations are carried out by
`most_plasim_run` looping over 1-year model invocations and handing off the
restart file between years.
```

## Step 4: How the `most_plasim_run` script works

Before launching a simulation, open `plasim/run/most_plasim_run` in a text
editor. For the 1-year serial setup above, MoSt generates a script with the
following structure:

```bash
#!/bin/bash
# run-script generated by Most ...
EXP=MOST    # Name your experiment here
YEAR1=1
YEAR2=1
average="-m"  # Comment this line if you do not want monthly averaging
srv2nc=/abs/path/to/PLASIM/scripts/srv2nc
[ $# == 1 ] && cd $1
rm -f plasim_restart
rm -f Abort_Message
mkdir -p output
mkdir -p restart
for ((YEAR=$YEAR1; YEAR<=$YEAR2; YEAR++)); do
   DATANAME=`printf '%s_PLA.%04d.nc' $EXP $YEAR`
   OCENAME=`printf '%s_OCE.%04d.nc' $EXP $YEAR`
   ICENAME=`printf '%s_ICE.%04d.nc' $EXP $YEAR`
   LSGNAME=`printf '%s_LSG.%04d.nc' $EXP $YEAR`
   DIAGNAME=`printf '%s_DIAG.%04d.txt' $EXP $YEAR`
   RESTNAME=`printf '%s_REST.%04d' $EXP $YEAR`
   LSGRESTNAME=`printf '%s_LSGREST.%04d' $EXP $YEAR`
   ./most_plasim_t21_l10_p1.x
   [ -e Abort_Message ] && exit 1
   [ -e plasim_diag ] && mv plasim_diag output/$DIAGNAME
   [ -e plasim_output ] && $srv2nc $average plasim_output output/$DATANAME
   [ -e ocean_output ] && $srv2nc $average ocean_output output/$OCENAME
   [ -e ice_output ] && $srv2nc $average ice_output output/$ICENAME
   [ -e lsg_output ] && $srv2nc lsg_output output/$LSGNAME
   [ -e plasim_status ] && cp plasim_status plasim_restart
   [ -e plasim_status ] && mv plasim_status restart/$RESTNAME
   [ -e mat77 ] && cp mat77 restart/mat77
   [ -e kleiswi ] && cp kleiswi restart/kleiswi
   [ -e kleiin1 ] && cp kleiin1 restart/$LSGRESTNAME
done
```

### Configurable variables at the top of `most_plasim_run`

- **`EXP=MOST`:** Filename prefix for all archived outputs and restarts. Change
  this (for example, `EXP=EARTH_CTRL`) to give your experiment a descriptive
  label.
- **`YEAR1` and `YEAR2`:** Start and end values of the script's segment counter
  (`0001`, `0002`, ...). Note that `YEAR` in the script is the **run segment
  number**, not the model's calendar year (`N_START_YEAR`, which starts at 2000
  and increments automatically across restarts).
- **`average="-m"`:** Passed to `scripts/srv2nc` so CDO computes monthly means
  when converting atmospheric, mixed-layer ocean, and sea-ice output to NetCDF.
  Comment out `#average="-m"` (or set `average=""`) to keep every written output
  timestep (set by `NWPD` in `plasim_namelist`, default 1 write per day) in the
  NetCDF files.
- **`srv2nc=...`:** Absolute path to the repository's `scripts/srv2nc`
  converter. Update this path if you move the repository or copy the experiment
  to another machine.

### What happens during each loop iteration

1. **Initialization:** Before entering the `for` loop, the script deletes any
   existing `plasim_restart` and `Abort_Message` in the run directory and
   creates `output/` and `restart/`. Because `plasim_restart` is removed, the
   first segment (`YEAR=$YEAR1`) starts from initial conditions.
2. **Model execution:** The script runs `./most_plasim_t21_l10_p1.x` (or
   `mpiexec -np <N> ./most_plasim_t21_l10_p<N>.x` for parallel builds). If the
   model aborts and writes `Abort_Message`, the script exits immediately with
   status `1`.
3. **Output conversion (`output/`):** Raw Service files (`plasim_output`,
   `ocean_output`, `ice_output`, and `lsg_output` if present) are converted to
   compressed NetCDF4 via `srv2nc` and saved under `output/`, alongside the
   diagnostic log `output/${EXP}_DIAG.XXXX.txt`.
4. **Restart handoff (`restart/`):** The model writes its end-of-year state to
   `plasim_status`. The script copies `plasim_status` to `plasim_restart` so the
   **next** loop iteration automatically continues from the end of the previous
   year, and moves `plasim_status` to `restart/${EXP}_REST.XXXX`. (For coupled
   LSG runs, it also archives `mat77`, `kleiswi`, and `kleiin1`.)

```{warning}
Because `most_plasim_run` executes `rm -f plasim_restart` before the loop,
re-running `./most_plasim_run` unmodified starts a **fresh cold run** from year
1 and overwrites matching segment files. To continue or extend an existing run,
follow the continuation procedure in {doc}`experiments`.
```

## Step 5: Run the simulation and inspect output

For a quick trial directly in `plasim/run/`:

```sh
cd plasim/run
./most_plasim_run
```

(You can also invoke it from the repository root by passing the run directory
as its argument: `./plasim/run/most_plasim_run plasim/run`.)

When the 1-year Earth run finishes, check the generated directories:

```text
plasim/run/
├── output/
│   ├── MOST_DIAG.0001.txt   # Text diagnostics, namelist echo, and timestep logs
│   ├── MOST_PLA.0001.nc     # Atmospheric NetCDF4 output (12 monthly means)
│   ├── MOST_OCE.0001.nc     # Mixed-layer ocean NetCDF4 output
│   └── MOST_ICE.0001.nc     # Sea-ice NetCDF4 output
└── restart/
    └── MOST_REST.0001       # Saved atmospheric restart state after year 1
```

Verify that `output/MOST_DIAG.0001.txt` shows the expected calendar and
completion summary with no abort messages, and that the `.nc` files are
nonempty.

```{tip}
Before starting a multi-year production experiment or editing namelists, copy
the contents of `plasim/run/` to a dedicated experiment directory so future
MoSt builds or `./cleanplasim` do not overwrite your work. See
{doc}`experiments` for step-by-step instructions.
```

## Optional demonstration feature: the simulation GUI

If **Run with GUI** is enabled in MoSt (`NGUI=1`), the compiled executable
opens an interactive X11 window showing live atmospheric and ocean plots while
the model runs. This feature is mainly for visual demonstrations and teaching.
It is not used for scientific production runs (which should always use
`Run with GUI = 0` for speed, annual restart segmentation, and reproducibility).
Details on `GUI.cfg` and its display arrays are kept in the subsection below:

```{toctree}
:maxdepth: 1

gui
```

## Further reading

- **Managing experiment directories and resuming runs:** {doc}`experiments`.
- **Customizing namelists, planets, MPI, and LSG coupling:**
  {doc}`configuration` and {doc}`../reference/namelists`.
- **Inspecting and plotting NetCDF output:** {doc}`postprocessing` and
  {doc}`visualization`.
- **Alternative direct-Make build (without MoSt or X11):**
  {doc}`../development/direct-build` in Part II shows how CI compiles and runs
  `plasim.x` directly with `make`.

## Sources and attribution

Adapted from section 1.1 of the University of Hamburg's *Planet Simulator
User's Guide*, version 16.0, with current behavior checked against the
repository {download}`README <../../README.md>`, {download}`FAQ <../../FAQ.md>`,
{repo}`configure.sh`, and {repo}`most.c` (`main`, `ReadSettings`,
`BuildScripts`, `SaveExit`, and `WriteRunScript`). Full author attribution is
in {doc}`experiments` and {doc}`../sources`.
