# Code structure and extension points

This chapter migrates the developer-facing module and parallelization
material from User's Guide chapters 2–3. User choices belong in
{doc}`../user/components`; the scientific Reference Manual is excluded.

## Permanent sources and build variants

`plasim/src` contains permanent sources and `make_plasim`. MoSt copies them
into a generated build directory, writes `resmod.f90`, and selects module
variants. Do not edit generated copies as a permanent change.

| Build selection | Implementation |
| --- | --- |
| Communication | `mpimod.f90` for MPI, `mpimod_stub.f90` for serial. |
| Simulation GUI | `guimod.f90`/`pumax.c`, or matching stubs. |
| Planet | `p_earth.f90`, `p_mars.f90`, or `p_exo.f90`. |
| Deep ocean | Real `lsg/src/lsgmod.f90` with `cpl.f90`, or `lsgmod_stub.f90` with `cpl_stub.f90`. |
| Vegetation | Default `simba.f90`, implementing module `vegmod`. |
| FFT | Default `fftmod.f90`; selectable `fft991mod.f90` for other supported factorization paths. |
| Rain | Default `rainmod.f90`; alternative rain implementations need their own interface/behavior validation. |

MoSt's selectors and Makefile variables decide which implementation is
compiled. An unreferenced alternative or stub is not automatically dead
code. Retain shared entry points and dummy arguments when changing one
variant.

## Execution and module lifecycle

The actual top-level sequence in `plasim_main` is:

```text
mpstart → setfilenames → opendiag → allocate_arrays
        → prolog → master → epilog → mpstop
```

`prolog` initializes the planet, reads inputs/restored state, establishes
time control, and initializes physical modules. `master` performs the
initial shortened steps and the integration loop. `gridpointd` applies
miscellaneous corrections, surface exchange, radiation, moist processes,
and the surface interface. `epilog` writes saved state and finalizes modules.

| Module | Lifecycle and related routines |
| --- | --- |
| Flux | `fluxini`, `fluxstep`, `fluxstop`; `surflx`, stress/sensible/evaporation helpers, `vdiff`. |
| Miscellaneous | `miscini`, `miscstep`, `miscstop`; humidity fixer and nudging/flux-correction helpers. |
| Surface | `surfini`, `surfstep`, `surfstop`; surface-code registry, land/sea interfaces. |
| Land/vegetation | `landini`, `landstep`, `landstop`; SIMBA routines in `simba.f90`. |
| Radiation | `radini`, `radstep`, `radstop`; shortwave/longwave and stellar-spectrum routines. |
| Rain | `rainini`, `rainstep`, `rainstop` in the selected implementation. |
| Sea/ice/ocean | `seaini`, `seastep`, `seastop`; ice and ocean initialization/step/output routines and optional LSG calls. |
| Transforms | `gp2fc`/`fc2gp` and Legendre transforms between grid, Fourier, and spectral forms. |
| Output/restarts | `outini`, `outsp`, `outgp`, `outdiag`, accumulation/reset, named restart helpers. |

File names and Fortran module names need not match: `plasimmod.f90` defines
the shared `pumamod`, and `simba.f90` defines `vegmod`. Preserve this
distinction when following `use` dependencies or searching for declarations.

## Data layout and MPI

Gridpoint work is partitioned in latitude. `NLPP=NLAT/NPRO` and
`NHOR=NLON*NLPP` describe rank-local arrays; `NUGP` describes the global
grid. Many routines flatten longitude/latitude into `NHOR`, which does not
turn a local field into a replicated global field.

The spectral decomposition uses `NSPP=(NRSP+NPRO-1)/NPRO` and padded
`NESP=NSPP*NPRO`. Padding and the transform reduction order matter when
comparing serial and MPI results. Follow actual gather/scatter/broadcast
interfaces rather than inferring layout solely from array size.

I/O usually runs on `NROOT`; distribute initialized state to other ranks
using the matching scalar/array/grid operation. **Replicated small arrays**
must not be passed through a grid gather simply because their element type
matches a grid field.

When adding a namelist parameter, check declaration, initialization,
root-process reading, MPI broadcast, all selected planet paths, restart
semantics, and output metadata if relevant. The current `soilcap` and
illumination regression cases demonstrate why a read on rank zero alone
does not establish a correct parallel implementation.

## Documentation-facing changes

Preserve scientific defaults and units unless a behavior change is intended.
Changes to a conversion, calendar, physical constant, interpolation, or
precision are functional changes. Record compatibility implications and
use meaningful state/flux comparisons; broad global means can miss a local
or layout error.

Update user instructions and source inventories in the same PR. Regenerate
the reference inventories with `generate_reference.py` and check their
semantic descriptions against initialization/output paths. Bugs found
while doing documentation belong in separate issues, without a code fix
or workaround tutorial in the manual migration.

Source comparison: User's Guide chapter 2 lifecycle descriptions and
chapter 3 decomposition rules checked against `plasim_main`, `prolog`,
`master`, `gridpointd`, `epilog`, `make_plasim`, `mpimod`, and shared
dimension definitions. Detailed code-verification records are in
{doc}`verification`.
