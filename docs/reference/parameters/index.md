# Detailed namelist reference

These tables complement the {doc}`../namelists` overview. Every accepted
input in the default model, the three planet modules, the real coupler,
and LSG has a row. The inventory checker verifies membership; descriptions
and initialization behavior are reviewed against the cited code.

Each chapter gives the filename and Fortran group. **Default** means the
value before reading that group's input, with exceptions and subsequent
changes stated explicitly. MoSt writes overrides, surface datasets can
replace spatial initial values, and restarts restore state. A declaration
default alone is therefore not the complete configuration of an experiment.
Use the namelist echo and diagnostics to retain the effective setup.

`integer`, `real`, `real(kind=8)`, `logical`, and `character(n)` denote Fortran
types; `real` follows the build's selected precision. Scalars are the default;
array dimensions are explicit. `1` in a units column means dimensionless.
Array defaults stated as a scalar apply to all elements. `NLEV` is the
compiled atmospheric level count, ordered from model top to bottom.

Do not interpret an accepted integer as an unrestricted enumeration. Use
the documented branches; diagnostic counts/intervals and physical arrays
also need values consistent with compiled dimensions and the experiment.
Alternative rain implementations are outside these default-module tables.

```{toctree}
:maxdepth: 1

plasim
planet
fluxmod
miscmod
surfmod
landmod
vegmod
radmod
rainmod
seamod
icemod
oceanmod
cpl
lsg
legacy
```

Historical User's Guide module tables and appendix C are the starting
material; {doc}`legacy` records moved, renamed, and removed entries. The
scientific Reference Manual remains separate. The tables describe accepted
inputs; they do not establish that every parameter combination has been
tested at runtime.
