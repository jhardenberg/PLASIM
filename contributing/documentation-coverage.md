# Manual structure and migration coverage

The practical content of the User's Guide is organized into a user part and
an implementation/maintenance part. This is a migration to the current
interfaces, not a verbatim transcription of obsolete examples. The scientific
Reference Manual is excluded.

## Part I: User guide

Chapters are grouped under [Introduction](../docs/user/introduction.md),
[Getting started](../docs/user/getting-started.md), [Configuring experiments](../docs/user/configuration.md), and
[Postprocessing and visualization](../docs/user/analysis.md), followed by the configuration/output reference and
troubleshooting. Each chapter retains its existing URL.

| Topic | Chapter |
| --- | --- |
| Recommended compilation/preparation | [Configure, compile, and run with MoSt](../docs/user/most.md): MoSt GUI and configuration-file workflows. |
| Experiment management | [Experiment directories and long simulations](../docs/user/experiments.md): original guide §§1.2–1.5 adapted to current paths and scripts. |
| Components and configuration choices | [Model components and experiment choices](../docs/user/components.md): practical current module overview. |
| Recent planetary development | [Planets, calendars, and radiation settings](../docs/user/planets.md): effective presets, calendars, orbits, spectrum, albedos, and illumination. |
| Parallel and coupled runs | [Parallel runs and the LSG ocean](../docs/user/parallel-ocean.md): MoSt MPI selection and actual LSG setup. |
| Input data | [Surface and boundary data](../docs/user/boundary-data.md): current surface-file names, grids, climatologies, and conversion interfaces. |
| Interactive model display | [The simulation GUI](../docs/user/gui.md): current configuration precedence, arrays, plot types, and display scaling. |
| Continuation and provenance | [Restarts and reproducible experiments](../docs/user/restarts.md): segment handoff, compatibility, and reproducibility. |
| Output conversion | [Convert and analyse model output](../docs/user/postprocessing.md): srv2nc, current burn7, and extraction conventions. |
| Inspection and graphics | [Inspect and visualize results](../docs/user/visualization.md): tested CDO inspection and current versus historical graphics paths. |
| Columns and soundings | [Column-oriented experiments and soundings](../docs/user/column.md): individual current controls, absent historical macro, and sounding interface. |
| Practical FAQ | [Troubleshooting and compatibility](../docs/user/troubleshooting.md): current workflow and compatibility checks. |
| Configuration reference | [Runtime configuration reference](../docs/reference/namelists.md) overview, [Detailed namelist reference](../docs/reference/parameters/index.md) with individual inputs, and the complete accepted-name inventory. |
| Output reference | [Output fields, formats, and units](../docs/reference/output.md), literal writer inventory, and separate conversion metadata vocabulary. |
| Definitions | [Dimensions, constants, and terminology](../docs/reference/units.md): current dimensions, selected constants, and unit/representation distinctions. |

## Part II: Developer guide

- [Code structure and extension points](../docs/development/architecture.md): lifecycle, module variants, array layout,
  and MPI extension rules migrated from User's Guide chapters 2–3.
- [Tests and scientific validation](../docs/development/testing.md): existing regression coverage, provenance, and
  the limits of short numerical checks.
- [Performance benchmarking](../docs/development/benchmarking.md): classic-radiation workloads, current
  defaults, timing scope, revision/MPI
  comparisons, concurrent scheduling, continuation, and result interpretation.
- [Alternative direct-Make build and CI example](../docs/development/direct-build.md): optional direct-Make/CI example, runtime
  parameter table, and operational timestep equations. MoSt remains the
  recommended user build method.
- [Source material and attribution](../docs/sources.md): original material and authorship.

## Contributor notes

Documentation maintenance, verification records, and this coverage outline
are kept in `contributing/` and are not published as manual chapters. See
[documentation maintenance](documentation.md) and the
[verification notes](documentation-verification.md).

## Scope and remaining validation

All seven practical User's Guide chapters and appendices A–C have current
counterparts or an explicit historical disposition in the verification
ledger. This does not mean every old paragraph, screenshot, symbol from a
derivation, platform recipe, optional rain implementation, or code switch
has been independently tested.

The generated namelist inventory covers active declarations for default
modules, all three planet variants, the real coupler, and LSG. Detailed tables
cover all 302 parameter entries across 14 interfaces, with 348 memberships
when the three planet variants are counted separately. Coverage checks catch
missing, extra, duplicate, and incomplete table rows; semantic verification
still requires human review of the cited code paths. The output inventory enumerates literal writers, not
all dynamic diagnostic code values. Converter labels are recorded as labels,
not silently certified as physical units.

Additional runtime validation remains useful for interactive GUI operation,
other planet/column configurations, burn7 with its legacy dependency, and
compiled PDF layout. These limits are recorded explicitly rather than being
filled with unverified claims. The Reference Manual's full scientific
formulation remains a separate future project.
