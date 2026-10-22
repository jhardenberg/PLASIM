# Troubleshooting and compatibility

These answers adapt the repository FAQ and the User's Guide's practical
advice. Implementation bugs discovered while checking the manual are filed
as separate issues; this chapter does not prescribe patches or workarounds
for them.

## A compiler, Make, or X11 header is missing

Read the `configure.sh` output and install the missing development tools,
not only runtime libraries. MoSt needs a C compiler, Fortran compiler,
Make, and its X11 headers/libraries; the standard configuration also checks
a C++ compiler. A simulation GUI additionally needs a working display.
MPI wrappers are optional for serial operation. See {doc}`most` for the
distinction between headless operation and build dependencies.

Platform and package names differ across operating systems and distributions.
The headless regression build is exercised on Linux CI, with additional local
macOS validation. Windows users typically build and run inside WSL2 or a Linux
virtual machine.

## Save & Run cannot find a command

Start MoSt from the repository root using `./most.x`. Check that the prepared
run script and matching executable exist, that the compiler build actually
completed, and that postprocessing dependencies such as CDO are available.
For a manually launched script, use its explicit path from the appropriate
working directory. The old FAQ's suggestion to add `.` globally to `PATH`
is not needed.

## A namelist parameter is rejected

Check spelling, the group name, and the **current** accepted parameter list.
A variable declared somewhere in Fortran is not necessarily a namelist
parameter. The old `puma_namelist`/`INP` examples are not the current PlaSim
interface. See {doc}`../reference/namelists` for moved and removed inputs,
including `PSURF`, the orbital-year fields, old scalar albedo settings,
and the column macro.

## A permanent source edit appears to have no effect

Edit `plasim/src`, not the generated copy in `plasim/bld`. Preserve your
experiment and outputs, then clear generated build/run files with
`./cleanplasim` and prepare again through MoSt. Read {doc}`experiments`
first: that command also removes contents under `plasim/run`.

## A run produces output but the interpretation is unclear

Check dates, representation, vertical coordinates, source units, averaging
intervals, and the selected postprocessor. A pressure-level output name is
not evidence that pressure interpolation was performed; a GUI temperature
display can have different scaling from raw model temperature. Consult
{doc}`../reference/output` and preserve conversion commands with the result.

## Restarted and continuous runs differ

Check binary/input compatibility, random seed handling, and any changed
boundary conditions. For `NFIXORB=0`, initialization can select a different
orbital epoch at restart; a new segment is not always the same forcing as
continuing the old invocation. LSG needs its ocean state as well as the
atmospheric restart. See {doc}`restarts` and the test guide for the exact
short-run comparisons the repository performs.

## The model creates Abort_Message

Keep the file and diagnostic log with the failed input. Check the first
reported problem, effective namelists, selected data, and compiled setup.
Do not treat a success process status as evidence that the model continued
normally. Reproduce a problem in a short, isolated experiment before
changing scientific inputs or numerical tolerances.

## Report a reproducible problem

Provide the source commit, platform/compiler, build flags, MoSt
configuration, relevant namelists, boundary-data provenance, launch command,
and the shortest diagnostic log that shows the problem. State whether it
occurs in serial, MPI, mixed-layer, or LSG configurations. Preserve original
restart files and avoid regenerating numerical references just to make a
comparison pass.

Source comparison: root `FAQ.md`, current MoSt/configuration paths, model
namelist/restart readers, output writers, and `tests/README.md`.
