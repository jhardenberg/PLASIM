# PlaSim user and developer manual

PlaSim (Planet Simulator) is a general circulation model for meteorology,
climatology, and planetary experiments. This manual is being developed for
the current repository. The first part explains how to configure, build,
and run experiments with MoSt. The second part covers development, the
alternative direct-Make example used by CI, and documentation maintenance.

```{note}
This is an initial installment of the manual. It includes a MoSt getting-started
chapter and an adaptation of the User's Guide's experiment-directory and
long-simulation sections, plus developer material. It does not yet replace
the whole User's Guide. The scientific Reference Manual is outside this phase.
```

Start with {doc}`user/most`. **MoSt (`most.x`) is the recommended way to
compile PlaSim**, using either its graphical interface or its headless
configuration-file option.

```{toctree}
:maxdepth: 2
:caption: Part I — User guide

user/most
user/experiments
```

```{toctree}
:maxdepth: 2
:caption: Part II — Developer guide

development/direct-build
development/documentation
outline
sources
```

For workflows not yet migrated, consult the {download}`repository README
<../../README.md>`, {download}`FAQ <../../FAQ.md>`, and
{download}`original User's Guide <PS_UsersGuide.pdf>`. The
{download}`changelog <../../CHANGELOG.md>` records changes to behavior and
input compatibility.
