# PlaSim-LSG TNG user and developer manual

**PlaSim-LSG TNG (The Next Generation)** builds on and improves the original
Planet Simulator (PlaSim), a general circulation model for meteorology,
climatology, and planetary experiments. This manual documents the version
maintained in the **[jhardenberg/PLASIM repository](https://github.com/jhardenberg/PLASIM)**.
It brings together expanded planetary capabilities, refinements to model
physics and ocean coupling, easier workflows, and stronger automated checks.

See the {doc}`introduction <user/introduction>` for a brief overview of what
is new. The first part explains how to configure, build, and run experiments
with MoSt. The second part covers development, testing, performance
benchmarking, and the alternative direct-Make example used by CI.

```{note}
The scientific Reference Manual remains separate; its derivations and
equation set are not included here.
```

Start with {doc}`user/most`. **MoSt (`most.x`) is the recommended way to
compile PlaSim-LSG TNG**, using either its graphical interface or its headless
configuration-file option.

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

The {download}`repository README <../README.md>`,
{download}`FAQ <../FAQ.md>`, and {download}`original User's Guide
<../plasim/doc/PS_UsersGuide.pdf>` remain available, including historical material and
figures. Use the current manual for present-day interfaces. The
{download}`changelog <../CHANGELOG.md>` records changes to behavior and
input compatibility.
