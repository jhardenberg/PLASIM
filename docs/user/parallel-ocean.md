# Parallel runs and the LSG ocean

## Select MPI through MoSt

Recent MPI optimizations improve the efficiency of parallel runs by reducing
overhead and unnecessary work. They are included automatically in current
builds and use the same MoSt setup described below. The benefit depends on
the experiment and hardware; see {doc}`../development/benchmarking` to
measure performance on your system.

Install compatible MPI C and Fortran wrappers and a launcher, then run
`configure.sh` so MoSt detects them. Select the desired core count in MoSt
before preparing the experiment. The executable's compiled processor count
must match its launch count; changing only `mpiexec -n` does not rebuild it.

MoSt generates `most_compiler_mpi` and uses the real `mpimod.f90` for a
parallel build. Serial builds use `mpimod_stub.f90`. The old User's Guide's
instruction to comment out `use mpi` by hand is not part of the current
user workflow.

The atmosphere is partitioned by latitude: `NLAT` must be divisible by the
process count. MoSt checks the count and can reset incompatible choices to
one; inspect the generated `resmod.f90`, executable suffix, and launch line.
The source contains comments recommending powers of two, while
`CheckPlasimNamelist` enforces the divisibility/range condition. This is not
a validation claim for every divisor or resolution.

The repository's automated MPI coverage is two ranks at T21/L10 for both
mixed-layer and LSG configurations, with additional spectral/nondefault
parameter cases. Roundoff can grow differently in serial and MPI runs;
the tests distinguish numerical bounds from restart byte equality. See
the {download}`test guide <../../tests/README.md>` for measured tolerances
and coverage. MPI availability does not establish scaling performance.

## Enable the deep-ocean configuration

Select **LSG Ocean** in MoSt and prepare the experiment again. This changes
both the compiled modules and runtime inputs. The real build uses
`lsg/src/lsgmod.f90` and `plasim/src/cpl.f90`; the mixed-layer-only build
uses the corresponding stubs. Setting `NLSG` in a stub executable does not
provide a deep ocean.

MoSt copies `lsg/dat` inputs into the run directory, including the coupled
land mask and ocean restart. Preserve the ocean data as part of the setup;
the atmospheric restart alone is not the coupled state. The included LSG
grid is 72 × 76 with 22 ocean levels.

| Input | Group/file | Purpose |
| --- | --- | --- |
| `nlsg` | `oceanmod_nl` / `oceanmod_namelist` | Coupling mode; the tested mode 1 uses atmospheric SST forcing and ocean heat-flux feedback. |
| `naomod` | `oceanmod_nl` | Atmospheric steps between LSG exchanges; declaration default 320. |
| Coupling/flux-correction settings | `cplpar` / `cpl_namelist` | Interpolation/exchange controls and selected flux corrections. |
| Ocean controls | `param` / `input` | LSG integration/output controls and vertical-diffusion parameters. |
| `astar`, `zstar`, `arange`, `lambda` | LSG `param` | Optional vertical-diffusion profile controls; the code's negative sentinels retain its default selection. |

At the usual 32 atmospheric steps per day, `NAOMOD=320` means ten days.
Do not describe that setting as ten days for an arbitrary timestep. In
LSG initialization, `DT` is derived from the PlaSim coupling interval after
reading `input`; an independently edited LSG `DT` is not authoritative in
this coupled path. The coupled calendar uses 360 days.

The regression setup deliberately exchanges daily so a two-day run actually
advances LSG twice. A short run at the ten-day interval can succeed without
exercising an ocean step; inspect ocean evolution and exchanged fluxes,
not only process exit.

## Retain coupled state

Keep compatible atmospheric and ocean restarts together, including
`plasim_status`/`plasim_restart`, `kleiin1`, `kleiswi`, and the generated LSG
matrix when required by the selected workflow. The standard run script
archives ocean products as well as atmospheric output. See {doc}`restarts`
for the distinction between a segment handoff and restarting the entire script.

Current coupled tests cover short advancement and restart consistency.
Ocean spin-up, other coupling modes, arbitrary grids, and long climate
statistics need experiment-specific validation.

## Sources checked

User's Guide chapter 3 compared with MoSt `Build`/`CheckPlasimNamelist`,
{repo}`plasim/src/mpimod.f90`, {repo}`plasim/src/plasimmod.f90`,
{repo}`plasim/src/oceanmod.f90`, {repo}`plasim/src/cpl.f90`,
{repo}`lsg/src/lsgmod.f90`, and `tests/test_mpi.py`/`tests/test_lsg.py`.
