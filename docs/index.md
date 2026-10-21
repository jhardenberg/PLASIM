# PlaSim-LSG TNG user and developer manual

**PlaSim-LSG TNG (The Next Generation)** is a global 3D atmospheric general
circulation model (GCM) coupled to land, vegetation, sea-ice, and ocean
modules. Originally developed at the University of Hamburg as the Planet
Simulator (PlaSim), this independently maintained version in the
**[jhardenberg/PLASIM repository](https://github.com/jhardenberg/PLASIM)**
adds expanded planetary and exoplanet capabilities, refined physics, tuned
coupling with the **LSG (Large Scale Geostrophic)** deep-ocean model, faster
MPI parallelization, direct NetCDF postprocessing, and automated regression
testing.

```{note}
This manual provides practical instructions for configuring, compiling,
running, and modifying the model, verified against the current source code.
The mathematical derivations in the historical {download}`Reference Manual <../plasim/doc/PS_ReferenceManual.pdf>` remain separate.
```

## Quick workflow overview

Running an experiment in PlaSim-LSG TNG follows four steps using **MoSt**
(`most.x`), the recommended model starter:

1. **Configure and build MoSt** once from the repository root (`./configure.sh`).
2. **Select your experiment and compile the model** interactively (`./most.x`)
   or headlessly (`./most.x -c earth.cfg`), which prepares `plasim/run/`.
3. **Run the generated script** (`./most_plasim_run` inside `plasim/run/` or a
   copied experiment directory) to integrate the model year by year, archive
   restarts, and convert output to NetCDF.
4. **Inspect and plot** the resulting NetCDF files in `output/` using CDO or
   Python.

Start with {doc}`user/introduction` to learn what is inside the model, or jump
straight to {doc}`user/most` to build and run your first simulation.

```{toctree}
:maxdepth: 2
:titlesonly:
:caption: Part I — User guide

user/introduction
user/getting-started
user/configuration
user/analysis
reference/index
user/troubleshooting
```

```{toctree}
:maxdepth: 1
:titlesonly:
:caption: Part II — Developer guide

development/architecture
development/testing
development/benchmarking
development/direct-build
sources
```

## Additional repository resources

- {download}`Repository README <../README.md>` and {download}`FAQ <../FAQ.md>`:
  quick repository overview, orbital date handling, and common questions.
- {download}`Changelog <../CHANGELOG.md>`: release history, new features, and
  input compatibility notes.
- {download}`Original User's Guide <../plasim/doc/PS_UsersGuide.pdf>` and
  {download}`Reference Manual <../plasim/doc/PS_ReferenceManual.pdf>`:
  historical manuals retained for context and scientific equations.
