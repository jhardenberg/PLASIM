# Parallel runs and the LSG ocean

## Running in parallel with MPI

PlaSim-LSG TNG includes MPI optimizations (batched multi-level collective
exchanges and streamlined spectral reductions) that reduce parallel overhead
automatically. To measure scaling on your hardware, see
{doc}`../development/benchmarking`.

### Configuring and compiling an MPI build in MoSt

1. Install compatible MPI C and Fortran compiler wrappers (such as `mpicc`,
   `mpif90`, and `mpiexec`), then run `./configure.sh` from the repository root
   so it creates `most_compiler_mpi`.
2. In MoSt (`./most.x` or your `.cfg` file), set **Cores** to the desired
   number of MPI ranks before compiling.
3. The atmospheric grid is decomposed by latitude, so `NLAT` (32 at T21, 48 at
   T31, 64 at T42) **must be divisible by `Cores`** (powers of two are
   recommended). If you enter an incompatible core count, MoSt resets `Cores`
   to `1`.
4. **Compiled vs. launch core count:** The processor count (`NPRO_ATM`) is
   compiled into `resmod.f90` and encoded in the executable name (for example,
   `most_plasim_t21_l10_p4.x`). In `most_plasim_run`, MoSt automatically writes
   the matching launch command:
   ```bash
   mpiexec -np 4 ./most_plasim_t21_l10_p4.x
   ```
   You cannot change the number of MPI ranks simply by editing `-np` in
   `most_plasim_run`—you must recompile the executable for the new core count
   using MoSt.

MoSt links `mpimod.f90` when `Cores > 1` and `mpimod_stub.f90` when `Cores = 1`
(the old User's Guide instruction to comment out `use mpi` manually is obsolete).
Automated CI tests verify 2-rank MPI builds at T21/L10 for both the mixed-layer
and coupled LSG configurations; see the {download}`test guide <../../tests/README.md>`
for numerical tolerances.

## Coupling with the LSG deep-ocean model

To couple PlaSim with the 3D **LSG (Large Scale Geostrophic)** deep-ocean
model, enable **LSG Ocean** (`LSG Ocean = 1`) in MoSt and compile the
experiment.

### What MoSt prepares for LSG runs

Selecting **LSG Ocean** changes both the compiled executable and the prepared
`plasim/run` directory:

- **Compiled modules:** MoSt links `lsg/src/lsgmod.f90` and `plasim/src/cpl.f90`
  instead of `lsgmod_stub.f90` and `cpl_stub.f90` (setting `NLSG=1` in a stub
  executable does not provide a deep ocean).
- **Runtime data (`lsg/dat/*`):** MoSt copies the LSG grid/bathymetry, the
  coupled land–sea mask, the LSG namelist file `input`, and initial ocean
  restart files (`kleiin1`, `kleiswi`, `mat77`) into `plasim/run/`. The
  supplied LSG grid has 72 × 76 horizontal points and 22 vertical levels.
- **Namelist settings:** MoSt sets `NLSG=1` and `NHDIFF=0` in
  `oceanmod_namelist`, and sets `N_DAYS_PER_YEAR=360` in `plasim_namelist`
  (coupled PlaSim–LSG runs use the 360-day calendar).

| Input | Group / file | Purpose |
| --- | --- | --- |
| `nlsg` | `oceanmod_nl` / `oceanmod_namelist` | Coupling mode (`1` uses atmospheric SST forcing and ocean heat-flux feedback). |
| `naomod` | `oceanmod_nl` / `oceanmod_namelist` | Atmospheric timesteps between LSG coupling exchanges (default `320`, which equals 10 days at 32 steps/day). |
| Coupling controls | `cplpar` / `cpl_namelist` | Grid interpolation and flux-correction switches. |
| Ocean parameters | `param` / `input` | LSG integration, output controls, and vertical-diffusion parameters. |
| `astar`, `zstar`, `arange`, `lambda` | `param` / `input` | Optional LSG vertical-diffusion profile parameters (negative sentinel values retain default settings). |

At the standard T21 timestep of 45 minutes (32 steps per day), `NAOMOD=320`
couples the atmosphere and LSG every 10 atmospheric days. During LSG
initialization, the ocean timestep `DT` is derived automatically from PlaSim's
coupling interval after reading `input`.

```{note}
Because the default coupling interval is 10 atmospheric days, a test run shorter
than 10 days with default settings will exit before taking a single LSG step.
(The 2-day regression test in `tests/test_lsg.py` explicitly sets daily coupling
so LSG advances twice.) Always verify that `lsg_output` and ocean state evolve.
```

## How `most_plasim_run` handles LSG output and restarts

In a coupled PlaSim–LSG run, `most_plasim_run` automatically converts and
archives both atmospheric and deep-ocean files at the end of each 1-year
segment:

- **NetCDF output (`output/`):** In addition to `MOST_PLA.XXXX.nc`,
  `MOST_OCE.XXXX.nc`, and `MOST_ICE.XXXX.nc`, the script converts `lsg_output`
  via `$srv2nc lsg_output output/$LSGNAME` to produce `output/MOST_LSG.XXXX.nc`.
- **Coupled restart state (`restart/`):** Along with the atmospheric restart
  (`plasim_status` $\rightarrow$ `plasim_restart` and `restart/MOST_REST.XXXX`),
  the script copies the LSG matrix (`mat77`), switch file (`kleiswi`), and
  ocean state (`kleiin1` $\rightarrow$ `restart/MOST_LSGREST.XXXX`).

When continuing or backing up a coupled experiment, you must keep the matching
atmospheric (`plasim_restart`) and ocean (`kleiin1`, `kleiswi`, `mat77`) files
together; see {doc}`restarts`.

## Sources checked

User's Guide chapter 3 compared with MoSt `Build`/`CheckPlasimNamelist`,
{repo}`plasim/src/mpimod.f90`, {repo}`plasim/src/plasimmod.f90`,
{repo}`plasim/src/oceanmod.f90`, {repo}`plasim/src/cpl.f90`,
{repo}`lsg/src/lsgmod.f90`, and `tests/test_mpi.py`/`tests/test_lsg.py`.
