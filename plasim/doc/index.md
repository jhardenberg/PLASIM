# PlaSim user and developer manual

PlaSim (Planet Simulator) is a general circulation model for meteorology,
climatology, and planetary experiments. This manual is being developed for
the current repository. The first part explains how to configure, build,
and run experiments with MoSt. The second part covers development, the
alternative direct-Make example used by CI, and documentation maintenance.

```{note}
This manual migrates the practical User's Guide and repository instructions,
checking descriptions against current source code. Runtime validation is
identified separately from source review in the verification ledger. The
scientific Reference Manual and its equation set are outside this phase.
```

Start with {doc}`user/most`. **MoSt (`most.x`) is the recommended way to
compile PlaSim**, using either its graphical interface or its headless
configuration-file option.

```{toctree}
:maxdepth: 1
:caption: Part I — User guide

user/most
user/experiments
user/components
user/planets
user/parallel-ocean
user/boundary-data
user/gui
user/restarts
user/postprocessing
user/visualization
user/column
user/troubleshooting
reference/index
```

```{toctree}
:maxdepth: 1
:caption: Part II — Developer guide

development/architecture
development/testing
development/direct-build
development/documentation
development/verification
outline
sources
```

The {download}`repository README <../../README.md>`,
{download}`FAQ <../../FAQ.md>`, and {download}`original User's Guide
<PS_UsersGuide.pdf>` remain available, including historical material and
figures. Use the current manual for present-day interfaces. The
{download}`changelog <../../CHANGELOG.md>` records changes to behavior and
input compatibility.
