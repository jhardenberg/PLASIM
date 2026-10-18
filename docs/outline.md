# Manual structure and migration coverage

The practical content of the User's Guide is organized into a user part and
an implementation/maintenance part. This is a migration to the current
interfaces, not a verbatim transcription of obsolete examples. The scientific
Reference Manual is excluded.

## Part I: User guide

Chapters are grouped under {doc}`user/introduction`,
{doc}`user/getting-started`, {doc}`user/configuration`, and
{doc}`user/analysis`, followed by the configuration/output reference and
troubleshooting. Each chapter retains its existing URL.

| Topic | Chapter |
| --- | --- |
| Recommended compilation/preparation | {doc}`user/most`: MoSt GUI and configuration-file workflows. |
| Experiment management | {doc}`user/experiments`: original guide §§1.2–1.5 adapted to current paths and scripts. |
| Components and configuration choices | {doc}`user/components`: practical current module overview. |
| Recent planetary development | {doc}`user/planets`: effective presets, calendars, orbits, spectrum, albedos, and illumination. |
| Parallel and coupled runs | {doc}`user/parallel-ocean`: MoSt MPI selection and actual LSG setup. |
| Input data | {doc}`user/boundary-data`: current surface-file names, grids, climatologies, and conversion interfaces. |
| Interactive model display | {doc}`user/gui`: current configuration precedence, arrays, plot types, and display scaling. |
| Continuation and provenance | {doc}`user/restarts`: segment handoff, compatibility, and reproducibility. |
| Output conversion | {doc}`user/postprocessing`: srv2nc, current burn7, and extraction conventions. |
| Inspection and graphics | {doc}`user/visualization`: tested CDO inspection and current versus historical graphics paths. |
| Columns and soundings | {doc}`user/column`: individual current controls, absent historical macro, and sounding interface. |
| Practical FAQ | {doc}`user/troubleshooting`: current workflow and compatibility checks. |
| Configuration reference | {doc}`reference/namelists` overview, {doc}`reference/parameters/index` with individual inputs, and the complete accepted-name inventory. |
| Output reference | {doc}`reference/output`, literal writer inventory, and separate conversion metadata vocabulary. |
| Definitions | {doc}`reference/units`: current dimensions, selected constants, and unit/representation distinctions. |

## Part II: Developer guide

- {doc}`development/architecture`: lifecycle, module variants, array layout,
  and MPI extension rules migrated from User's Guide chapters 2–3.
- {doc}`development/testing`: existing regression coverage, provenance, and
  the limits of short numerical checks.
- {doc}`development/direct-build`: optional direct-Make/CI example, runtime
  parameter table, and operational timestep equations. MoSt remains the
  recommended user build method.
- {doc}`development/documentation`: build, verify, and extend this manual.
- {doc}`development/verification`: chapter-by-chapter code comparison,
  historical differences, runtime evidence, and issue-only follow-up.
- {doc}`sources`: original material and authorship.

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
