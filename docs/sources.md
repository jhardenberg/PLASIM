# Source material and attribution

The manual adapts the University of Hamburg's *Planet Simulator User's
Guide*, version 16.0, by Frank Lunkeit, Simon Blessing, Klaus Fraedrich,
Heiko Jansen, Edilbert Kirk, Ute Luksch, and Frank Sielmann. The original
PDF is retained, including its figures and historical context. Descriptions
of current behavior are checked against the model code.

The original module parameter tables and appendix C are carried into
{doc}`reference/parameters/index`, with current inputs explained individually
and removed/moved entries accounted for in the legacy crosswalk. Their old
defaults and descriptions are compared with initialization and calculation
paths rather than copied unchanged.

| Material | Current use |
| --- | --- |
| {download}`User's Guide <../plasim/doc/PS_UsersGuide.pdf>` (70 pages) | Practical user, developer, and reference material from chapters 1–7 and appendices A–C; obsolete instructions are replaced or identified as historical. |
| {download}`README <../README.md>` | Current MoSt, planetary/orbital, postprocessor, and test context. |
| {download}`FAQ <../FAQ.md>` | Dependencies, file paths, rejected inputs, source/build separation, and compatibility advice. |
| {download}`Changelog <../CHANGELOG.md>` | Recent features and intentional input/behavior migrations, checked against implementation before adoption. |
| {download}`Ice-output sheet <../plasim/doc/codes_in_ice_output.pdf>` | Code families compared with current `iceout`/`icestep`; added fields and diagnostic scope reflected in the output reference. |
| {download}`Variable list <../plasim/doc/variable_list.txt>` | Historical names/dimensions/units compared with actual writers and converters; current inventories keep those sources distinct. |
| {download}`Test guide <../tests/README.md>` and source tests | Actual temporary builds, fixtures, restart/MPI/LSG checks, and validation limits. |
| {download}`Benchmark guide <../benchmarks/README.md>` and benchmark scripts | Workloads, defaults, optional T31 selection, timing boundaries, revision/scaling comparisons, concurrent scheduling, continuation, and result interpretation checked against `run.py` and `compare.py`. |
| {download}`burn.sh guide <../scripts/README_burn.txt>` | Historical extraction categories compared with current script expressions. |
| {download}`Postprocessor notes <../postprocessor/README_POSTPROCESSOR>` and {download}`burn7 quick reference <../postprocessor/burn7qr.pdf>` | Compared with today's `burn7.cpp` options, parser, metadata, and Makefiles. |

The scientific Reference Manual is intentionally excluded: its chapters,
derivations, and equation set have not been migrated. Operational equations
for timestep/run length and code-defined diagnostics do not change that scope.

The original User's Guide was produced with LaTeX, but editable sources are
not in this checkout. The migration paraphrases practical text, preserves
authorship, and checks extracted information against code. No historical
screenshot is presented as proof of the current GUI. If original editable
sources become available, they can improve future figure/citation handling.

Implementation bugs found during documentation work are reported in separate
GitHub issues and left for separate fixes. The manual describes current
interfaces and tested scope; it does not contain workaround tutorials for
those findings.
