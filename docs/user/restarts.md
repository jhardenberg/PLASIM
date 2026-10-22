# Restarts and reproducible experiments

## Timing defaults and continuation

Atmospheric automatic timesteps now match MoSt (T21/T31/T42: 45/30/20
minutes), and omitted or zero ocean `NAOMOD` selects ten atmospheric days.
Older direct T31/T42 runs used 36/30 minutes. Keep their original timestep
explicit when continuing: the saved step counter does not encode its own
timestep duration. Keep a valid original coupling interval explicit and
retain the corresponding LSG restart and matrix. Legacy fractional-day
LSG intervals are now rejected because they silently truncated the ocean
timestep. Changing those intervals is a new numerical setup, not an exact
continuation. See {doc}`parallel-ocean` for the timing table and migration.

## How `plasim_status` and `plasim_restart` work

At the end of every executable run (`epilog`), PlaSim writes its complete
final state (atmosphere, land, vegetation, sea ice, and mixed-layer ocean) to
the binary file `plasim_status`. At startup (`prolog`), the model checks
whether `plasim_restart` exists in the working directory:

- **If `plasim_restart` is absent (cold start):** The model initializes from a
  resting isothermal atmosphere (plus random noise if `KICK > 0`) and surface
  boundary climatologies at `N_START_YEAR` / `N_START_MONTH`.
- **If `plasim_restart` is present (restart continuation):** The model reads
  the saved state and resumes the model clock from the stored timestep.

Restart files use named binary records (`restartmod.f90`), not Service records
or NetCDF; do not pass them to `srv2nc`.

### Segment handoff inside `most_plasim_run` vs. resuming a stopped script

When you run `most_plasim_run` with the simulation GUI off (`NGUI=0`), the
script runs one model year per loop iteration and hands the state to the next
iteration:

```bash
if [ -e plasim_status ]; then
   cp plasim_status plasim_restart
   mv plasim_status restart/$RESTNAME
fi
```

However, before entering the `for ((YEAR=$YEAR1; YEAR<=$YEAR2; YEAR++))` loop,
`most_plasim_run` executes:

```bash
rm -f plasim_restart
```

Consequently, **re-running `./most_plasim_run` unmodified does not resume a
previous run**—it deletes `plasim_restart` and starts a cold run from segment 1.

To resume or extend an experiment from saved segment `N` (for example, continuing
after segment `0010` for segments `11` through `20`):

1. Restore the saved atmospheric restart into the working directory:
   ```sh
   cp restart/MOST_REST.0010 plasim_restart
   ```
   If **LSG Ocean** is enabled, also restore the matching ocean restart files
   (`cp restart/MOST_LSGREST.0010 kleiin1`, plus `restart/kleiswi` and
   `restart/mat77` if they are not already in the working directory).
2. Edit `most_plasim_run`:
   - Comment out `#rm -f plasim_restart` so the restored file is kept.
   - Set `YEAR1=11` and `YEAR2=20`.
3. Launch `./most_plasim_run`.

For a direct executable run without `most_plasim_run`, simply copy
`cp plasim_status plasim_restart` after archiving the previous segment's output
files, then invoke `./plasim.x` again.

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
and required matrix products (`mat77`) along with the atmospheric state. Use
the coupled setup's matching mask, ocean controls, and coupling interval.

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
