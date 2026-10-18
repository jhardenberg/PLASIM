# Introduction

**PlaSIm-LSG TNG (The Next Generation)** is an independently maintained
development of the original Planet Simulator (PlaSim). The original model
was created at the University of Hamburg; PlaSIm-LSG TNG is developed separately
and builds on and improves that model for climate and planetary experiments.

This guide applies specifically to the version in the
**[jhardenberg/PLASIM repository](https://github.com/jhardenberg/PLASIM)**.
Several PlaSim versions exist; their features and settings can differ.
The shorter name “PlaSim” elsewhere in this guide refers to this version
unless a historical source is explicitly identified.

## What is new in PlaSIm-LSG TNG?

- **More flexibility beyond Earth:** expanded planetary settings, radiation
  for different kinds of stars, and illumination for worlds that always
  face their star with the same side.
- **Refined model physics:** updates to radiation and land-surface processes,
  and vegetation treatment.
- **Tuned, working LSG coupling:** coupling with the LSG deep-ocean model
  for simulations in which the atmosphere and deep ocean evolve together.
- **Easier experiment preparation and analysis:** graphical or headless
  setup through MoSt, plus tools to convert results directly to NetCDF for
  analysis.
- **Stronger checks on model behavior:** fixes to calendars, restart handling,
  and parallel execution, supported by automated tests that help catch
  regressions.
- **Updated documentation:** a searchable user and developer manual, with
  current workflows and detailed descriptions of model inputs.

These highlights summarize developments recorded in the
{download}`changelog <../../CHANGELOG.md>`, which gives the full history
and compatibility notes.

## Explore the model

The atmosphere exchanges heat, water, and momentum with land, vegetation,
sea ice, and an ocean. The model can use a mixed-layer ocean or the coupled
LSG deep ocean.

Start with the component overview to understand the available choices.
Then follow {doc}`getting-started` to prepare a first experiment through
MoSt, the recommended model starter.

```{toctree}
:maxdepth: 1

components
```

The user guide progresses from preparation to {doc}`configuration`,
{doc}`analysis`, and the {doc}`configuration and output reference
<../reference/index>`. Developer instructions have their own part of the
manual, including alternative compilation and documentation maintenance.

Practical material from the legacy User's Guide is updated against the
current code. The original sources and attribution are retained in
{doc}`../sources`; the scientific Reference Manual remains separate.
