# Restarts and reproducible experiments

## Model state and segment handoff

The atmosphere writes its final state to `plasim_status`. At initialization,
the model checks for `plasim_restart` and restores state when that file is
present. Restart files are named binary records, not Service fields or
NetCDF output; do not pass them to `srv2nc`.

Within a running generated script, MoSt hands state from one annual segment
to the next by copying `plasim_status` to `plasim_restart`, then archiving
the status file. This is distinct from launching the entire script again:
its startup removes `plasim_restart`. Save the complete experiment before
changing the segment range or restoring state.

For a deliberately managed direct executable continuation, the essential
state handoff in the run directory is:

```sh
cp plasim_status plasim_restart
```

Archive outputs from the preceding segment before invoking the same compatible
executable again. Set the intended next segment duration in the namelists.
Do not insert this command in front of an unmodified `most_plasim_run` and
expect it to survive that script's initialization.

## Compatibility checks

Keep the compiled grid, level count, processor configuration, numerical
precision, model revision, and parameter settings with the saved state.
Named records allow the loader to check/recover fields, but do not make
arbitrary binaries interchangeable across compilers, architectures, or
model versions. Preserve an original copy before a compatibility trial.

Current restarts include band-specific albedo records. A broadband run can
continue an older restart without these by initializing from the saved
broadband fields; a spectral-radiation restart requires the appropriate
band records. Incomplete record pairs are rejected. Changing radiation mode
while loading an old state is therefore not equivalent to changing a scalar
forcing parameter.

For LSG, retain the ocean restart and switch state (`kleiin1`, `kleiswi`)
and required matrix products along with the atmospheric state. Use the
coupled setup's matching mask, ocean controls, and coupling interval.

## Dates, forcing, and initialization

A restored timestep determines the resumed date. `N_START_YEAR` is not a
way to relabel a restart's physical history. With `NFIXORB=0`, orbital
elements are recalculated at initialization using the restored year unless
`IYRBP` fixes an epoch. A continuous run and restart segments may therefore
have different transient orbital forcing; see {doc}`planets`.

Surface-module `NEWSURF` settings can request new boundary information on a
restart. Keep the original files and record such interventions: replacing
boundary conditions is an experiment change, not merely a file-management
operation.

## Reproducibility and validation

Archive at least the source commit, compiler/flags, MoSt configuration,
all runtime inputs, boundary data provenance, executable, diagnostic log,
and both components' saved state where applicable. A fixed nonzero `SEED`
supports deterministic initialization within a given build. It does not
guarantee identical results across compilers or MPI reductions.

The test suite compares continuous and restarted short runs, checks current
Earth reference values, and exercises selected legacy inputs. These are
compatibility/regression checks, not evidence that every historical namelist
is accepted or that a multidecadal climate is scientifically validated.

## Sources checked

User's Guide §§1.4–1.5 and current README/FAQ compared with `prolog`,
`read_atmos_restart`, and `epilog` in {repo}`plasim/src/plasim.f90`,
{repo}`plasim/src/restartmod.f90`, `landini`, MoSt `WriteRunScript`,
and the atmosphere/LSG restart tests. Selected legacy-input migrations are
listed in {doc}`../reference/namelists`.
