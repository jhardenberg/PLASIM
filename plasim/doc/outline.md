# Manual outline and migration plan

The manual separates **Part I: User guide** from **Part II: Developer guide**.
The sections below track the intended full manual; entries marked **planned**
are a content backlog, not instructions ready to follow. MoSt is the
recommended user build workflow; direct Make is an additional developer option.

## Part I: User guide

### 1. Getting started and running experiments

- **Available:** {doc}`user/most`: configure and compile with MoSt, select a
  graphical or headless preparation workflow, and launch the generated script.
- **Available:** {doc}`user/experiments`: a direct adaptation of User's Guide
  sections 1.2–1.5, covering directory roles, build/run preparation, and long
  simulations with current script and output conventions.
- **Planned:** platform-specific setup; further resolutions, parallelism,
  boundary conditions, and worked restart/recovery procedures.
- **Planned:** practical troubleshooting adapted from the root FAQ,
  distinguishing supported PlaSim workflows from historical PUMA recipes.

Primary material: User's Guide chapter 1, current README/FAQ, `configure.sh`,
`most.c`, and the regression setup.

### 2. Model components and experiment choices

- **Planned:** a practical overview of the atmosphere, land/vegetation, sea
  ice, mixed-layer ocean, and optional LSG ocean, linked to configuration.
- **Planned:** Earth, Mars, and Exo setups; calendar and planetary day
  conventions; start dates and prescribed versus calculated orbital elements.
- **Planned:** classic versus stellar-spectrum radiation, two-band albedos,
  tidally locked illumination, tuning choices, and compatibility notes.
- **Deferred:** migration of the scientific Reference Manual, including its
  dynamics, parameterization derivations, and full equation set. This section
  will initially explain how to select experiments without reproducing those
  derivations.

Primary material: User's Guide module overview, current README/changelog,
and the corresponding model sources. Tuning descriptions need verified
publication details and the actual settings used in this repository.

### 3. Configuration and output reference

- **Available:** a first MoSt configuration in {doc}`user/most`. The direct
  executable's runtime table in {ref}`headless-parameters` is currently in
  Part II's CI example; it explicitly distinguishes source defaults from
  MoSt-generated settings.
- **Planned:** namelist files and groups, accepted parameters, types, units,
  defaults, valid combinations, and migration notes for removed or moved inputs.
- **Planned:** boundary-data grids, Service and restart formats, and output
  frequency and averaging conventions.
- **Planned:** an atmospheric, ocean, and ice variable catalogue, starting
  from `variable_list.txt` and `codes_in_ice_output.pdf`, checked against output
  routines and the postprocessors. Record dimensions, codes, units, signs, and
  whether a field is instantaneous, accumulated, averaged, or derived.
- **Planned:** `srv2nc`, `burn7`, and `burn.sh`, including their different
  dependencies, transformations, and example conversions.

Primary material: User's Guide appendices and postprocessor chapter, output
lists, script help, `outmod.f90`, and specialized postprocessor documentation.
Do not silently equate raw model output with renamed or converted variables.

## Part II: Developer guide

- **Available:** {doc}`development/direct-build`: the optional direct-Make
  T21/L10 build and two-day run used by documentation CI, with a runtime
  parameter table and operational timestep/run-length equations.
- **Planned:** permanent sources, generated build/run directories, module
  selection, and serial/MPI and mixed-layer/LSG build variants.
- **Planned:** regression tests, numerical references, reproducibility,
  compatibility policy, and the limits of short-run validation.
- **Available:** {doc}`development/documentation`: build and review this
  manual, add chapters, and maintain the worked example.

Primary material: User's Guide module and parallelization chapters,
`AGENTS.md`, `tests/README.md`, and the current Makefile.

### How chapters will be migrated

1. Record the original section or repository file and the code that defines
   current behavior. Preserve attribution when adapting the User's Guide.
2. Rewrite the chapter around a user task. Check commands, parameter names,
   defaults, units, and compatibility against the current sources.
3. Check extracted tables and figures against the PDF. Mark unresolved
   points explicitly rather than guessing. The historical guide's namelists
   are not an authoritative list for today's executable.
4. Build with warnings treated as errors, follow the internal links, and run
   examples with the stated inputs. Document validation scope.
5. Add the completed page to the navigation and update this coverage plan.

The original PDFs and text files remain available while migration proceeds.
The {doc}`sources` page tracks the initial material and current exclusions.
