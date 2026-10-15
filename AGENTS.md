# Repository instructions

## Project and layout

PlaSim is a Fortran climate model with a mixed-layer ocean and optional LSG
coupling. Read `README.md` and `tests/README.md` before changing a workflow.

- `plasim/src`: permanent model sources and the `make_plasim` build rules.
- `plasim/dat`: atmospheric boundary data and configuration files.
- `lsg/src` and `lsg/dat`: LSG sources, runtime inputs, and initial restarts.
- `most.c` and `configure.sh`: model configuration and build setup.
- `postprocessor` and `scripts`: output conversion and experiment helpers.
- `tests`: Python `unittest` regression tests and reference data.

Edit permanent sources, not generated copies in `plasim/bld`, `plasim/bin`, or
`plasim/run`. Build and run tests in temporary directories. Do not commit
executables, module/object files, model output, or generated ocean matrices.
The checked-in runtime data and restart fixtures are intentional inputs.

## Scientific and compatibility changes

- Preserve classic Earth defaults unless the requested change explicitly
  modifies them. Treat changes to units, timescale conversions, calendars,
  physical constants, and numerical precision as functional changes.
- Keep changes focused and preserve the surrounding Fortran conventions and
  file line endings. Avoid unrelated formatting or build-system migrations.
- For optimizations, explain why the calculation remains equivalent and
  compare numerical results. Do not assume compiler or MPI changes preserve
  results without relevant checks.
- Check namelist, restart, and output compatibility when changing interfaces
  or stored state. Document input migrations and intentional incompatibilities.
- Do not weaken tolerances or regenerate fixtures merely to make a failing
  test pass. For an intentional baseline change, record its reason, source
  commit, compiler/flags, configuration, and comparison with the old baseline.

## Tests and CI

Run the suite from the repository root:

```sh
python3 -m unittest discover -s tests -v
```

It requires Python 3, `gfortran`, `cc`, and `make`. Use the existing build
rules and standard-library test harness. Run the full suite for model,
coupling, build, or test-harness changes. Add a focused regression for a bug
or new behavior when practical.

Preserve coverage for both the mixed-layer configuration without LSG and
the real coupled PlaSim–LSG model. Additional LSG tests must actually advance
the ocean: the default coupling interval is ten atmospheric days. Check
ocean state and exchanged fluxes, not just successful process exit. When
changing restart logic, check continuation of both coupled components and
relevant legacy inputs. Short serial tests do not cover MPI or long climate
statistics; report the scope of any additional validation.

GitHub Actions runs tests on pushes to `master` or `main`, by manual dispatch,
and on pull requests carrying the exact `run tests` label. Use that label for
code and test PRs and inspect the CI result before claiming CI passed.
For documentation-only changes, check links and `git diff --check`; model
runs are unnecessary unless a documented command or behavior also changed.
Report any checks that could not be completed and why.

## Documentation and changelog

- Include a `CHANGELOG.md` update in every PR that changes model behavior,
  fixes, tests, build/tooling, or significant documentation or workflows.
  Before opening or updating a PR, explicitly check that its changes are
  represented in the changelog.
- Add entries under the current planned or unreleased version identified in
  `CHANGELOG.md`. Preserve released history except to correct factual errors.
  Describe the user-visible result and any compatibility implications, and
  link the PR when its number is available.
- Verify exact tag names and release boundaries before editing version labels
  or comparison links. Do not create a release, tag, or version bump unless
  requested. For a purely editorial correction, fix the existing text rather
  than adding a redundant release note.
- Keep `README.md`, `FAQ.md`, and specialized documentation consistent with
  changed commands or behavior. Retain `scripts/README_burn.txt`,
  `postprocessor/README_POSTPROCESSOR`, and `tests/README.md`.

## Branches and review

Start new work from the current remote default branch, using a focused
`ai/` branch unless directed otherwise. Keep unrelated work separate and
preserve existing local changes. PR descriptions should explain the change,
scientific or compatibility implications, and validation. Leave merging to
the maintainer unless explicitly asked to merge.
