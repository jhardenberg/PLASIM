# Getting started

Preparing and running an experiment in PlaSim-LSG TNG uses **MoSt** (`most.x`),
the model starter. MoSt selects the planet, resolution, processor count, and
physical modules, compiles the Fortran model executable, and populates a run
directory containing the namelists, boundary data, and the `most_plasim_run`
driver script.

```{toctree}
:hidden:

most
experiments
```

- **{doc}`most`:** Install prerequisites, run `./configure.sh`, compile the
  model via the MoSt GUI or headless config file (`./most.x -c`), and understand
  and run the generated `most_plasim_run` script.
- **{doc}`experiments`:** Understand the directory layout (`plasim/src`,
  `plasim/bld`, `plasim/bin`, `plasim/run`), move prepared setups into dedicated
  experiment directories for long simulations, and resume interrupted runs.

```{note}
MoSt also includes an optional real-time X11 **simulation GUI** (**Run with
GUI** / `NGUI=1`; see {doc}`gui`), which is separate from the MoSt
configuration window. That live display is mainly for interactive
demonstrations and teaching—keep **Run with GUI** disabled (`NGUI=0`) for all
normal and production runs.
```

Once you have run a basic experiment, see {doc}`configuration` to customize
planetary settings, boundary data, MPI/LSG coupling, and restarts.
