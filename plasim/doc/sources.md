# Source material and coverage

This manual combines the historical User's Guide with current repository
instructions and implementation checks. Original authorship is retained;
new descriptions should identify the source sections and distinguish
historical behavior from the present model.

| Material | Intended use | Coverage in this installment |
| --- | --- | --- |
| {download}`User's Guide <PS_UsersGuide.pdf>` (version 16.0, 70 pages) | Installation, running, module overview, GUI, postprocessing, and appendices | Section 1.1 informs {doc}`user/most`; sections 1.2–1.5 are adapted in {doc}`user/experiments`. Remaining chapters are planned. |
| {download}`README <../../README.md>` | Current build/run workflows, planets, orbital settings, postprocessing, and tests | MoSt workflow, current context, and the outline; remains an entry point for workflows not yet migrated. |
| {download}`FAQ <../../FAQ.md>` | Dependencies, namelist errors, source/build separation, and troubleshooting | Selected troubleshooting in the user and developer chapters; full integration is planned. |
| {download}`Changelog <../../CHANGELOG.md>` | New features and behavior/input migrations | Used to identify work beyond the historical manual. |
| {download}`Ice output codes <codes_in_ice_output.pdf>` | Ice variables and budget identities | Planned; not transcribed or verified in this installment. |
| {download}`Variable list <variable_list.txt>` | Variable names, dimensions, units, and codes | Planned; reconcile with current output and conversion code before publishing a catalogue. |
| {download}`Test guide <../../tests/README.md>` and {repo}`tests/test_model.py` | Headless compilation, runtime setup, and validation scope | Basis for the standalone direct-Make example in Part II. |
| {download}`burn.sh guide <../../scripts/README_burn.txt>` and {download}`postprocessor notes <../../postprocessor/README_POSTPROCESSOR>` | Specialized postprocessing instructions | Planned; keep these sources available during migration. |

The scientific Reference Manual is intentionally excluded from this phase:
none of its chapters or equation set is being migrated. The few equations
in the developer example explain operational timestep and run-length choices
directly from the current run-control code.

The User's Guide was produced with LaTeX, but editable LaTeX sources are not
present in this checkout. If recovered, use them to improve future migration
of tables, figures, and citations rather than relying on PDF text extraction.
