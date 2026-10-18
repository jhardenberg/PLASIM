# PlaSim user documentation

PlaSim (Planet Simulator) is a general circulation model for meteorology,
climatology, and planetary experiments. This manual is being developed for
the current repository, starting with a practical guide to running the model.

```{note}
This first installment contains a proposed manual outline and one complete
worked chapter. It does not replace the existing User's Guide yet. Migration
of the scientific Reference Manual and its equations is outside this phase.
```

Start with {doc}`running/headless` for a two-day Earth experiment using the
included boundary data. It needs a Fortran compiler, a C compiler, and Make;
no graphical interface or external data download is required.

```{toctree}
:maxdepth: 2
:caption: User documentation

outline
running/headless
sources
building
```

For workflows not yet migrated, consult the {download}`repository README
<../../README.md>`, {download}`FAQ <../../FAQ.md>`, and
{download}`original User's Guide <PS_UsersGuide.pdf>`. The
{download}`changelog <../../CHANGELOG.md>` records changes to behavior and
input compatibility.
