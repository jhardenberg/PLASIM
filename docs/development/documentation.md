# Build and maintain the documentation

This chapter belongs to Part II, for contributors maintaining the manual.
For compiling and running PlaSim as a user, start with {doc}`../user/most`.

The Sphinx documentation sources live in `docs` at the repository root.
The original PDFs and historical reference files remain in `plasim/doc`.
Chapters use MyST Markdown with Sphinx roles and directives for navigation,
equations, references, downloads, and source-code inclusion. HTML uses the
Read the Docs Sphinx theme, installed through `requirements.txt`.

## Build HTML locally

Use Python 3.11 or newer. From the repository root:

```sh
python3 -m venv docs/.venv
docs/.venv/bin/python -m pip install -r docs/requirements.txt
docs/.venv/bin/python -m sphinx -W --keep-going -n -b html docs docs/_build/html
```

Open `docs/_build/html/index.html` in a browser. For a local web preview:

```sh
python3 -m http.server --bind 127.0.0.1 --directory docs/_build/html 8000
```

Visit `http://127.0.0.1:8000` and stop the server with Ctrl-C. MathJax renders
HTML equations; the default renderer loads from a CDN, so equations need
network access on first viewing. Building the HTML itself does not execute
the model or need a compiler.

The virtual environment and generated documentation are ignored by Git.
The root README/FAQ and other source downloads are copied automatically by
Sphinx's `download` role; no duplicate editable copies are maintained.

## Check links and the worked example

The strict HTML command above checks cross-references and local download
targets. Check external links separately when network access is available:

```sh
docs/.venv/bin/python -m sphinx -W --keep-going -b linkcheck docs docs/_build/linkcheck
bash -n docs/examples/headless-earth.sh
bash docs/examples/headless-earth.sh
git diff --check
```

Accepted namelist names, literal raw writer calls, and converter metadata
have checked-in generated inventories. The same checker verifies that each
accepted namelist member has exactly one complete row in its detailed table,
including each compiled planet variant. Refresh and check them with:

```sh
python3 docs/generate_reference.py
python3 docs/generate_reference.py --check
```

Edit the descriptive tables in `reference/parameters/` by hand. Add a row
when introducing an accepted input; remove or migrate it when an interface
changes. The coverage check does not infer types, defaults, units, or meaning
from the row, so passing it alone is not semantic validation.

The generator extracts interfaces; it does not infer effective defaults or
physical semantics. Review initialization, units, conditions, and conversions
against the code and update {doc}`verification` as part of the same change.

The example requires `gfortran`, `cc`, and `make`. It creates and retains a
fresh temporary workspace rather than writing build/run files into the
checkout. Inspect it before removing that workspace when finished.

The documentation workflow builds HTML and LaTeX sources with warnings
treated as errors, runs this exact example, and uploads the HTML as a CI
artifact. It does not publish a public site. The model's broader regression
suite remains a separate workflow; see the {download}`test guide
<../../tests/README.md>` for its scope and invocation.

Read the Docs uses the root `.readthedocs.yaml`, which selects
`docs/conf.py` and installs `docs/requirements.txt`. It builds the manual
separately from the GitHub Actions workflow.

## LaTeX and future PDF builds

Generate LaTeX sources without a TeX installation:

```sh
docs/.venv/bin/python -m sphinx -W --keep-going -n -b latex docs docs/_build/latex
```

A complete PDF build additionally needs a TeX toolchain and `latexmk`:

```sh
docs/.venv/bin/python -m sphinx -M latexpdf docs docs/_build -W --keep-going -n
```

LaTeX-source generation alone does not verify a compiled PDF's layout.
PDF publication and visual review are follow-up work for the larger manual.

## Add or update a chapter

1. Update the coverage status in {doc}`../outline` and add the page to the
   appropriate `index.md` toctree when it is ready for readers. User workflows
   belong in Part I (`user/`); implementation, testing, alternative builds,
   and documentation maintenance belong in Part II (`development/`). Keep
   MoSt as the recommended user build/preparation method.
   Group related user chapters beneath the introduction, getting-started,
   configuration, or postprocessing landing pages. Keep each chapter in one
   toctree so its navigation and breadcrumbs have a clear parent.
2. Give parameters their file/group, type, units, current default, and
   configuration scope. Identify input migrations and distinguish compiled
   settings from runtime controls. Maintain the detailed row and the legacy
   crosswalk as well as any summary; explain initialization/restart precedence
   and inputs that are accepted but inactive in the selected implementation.
3. Add provenance in the chapter and update {doc}`../sources` when needed.
   Compare every described interface/default/unit/workflow with the current
   code rather than copying old defaults. Record routines and runtime/source
   verification scope in {doc}`verification`. Update stale descriptions to
   current behavior. File implementation bugs separately as issues; do not
   fix them or add workaround instructions in the documentation migration.
4. Keep executable examples in `examples/` and include them with
   `literalinclude`, so the displayed procedure and the executed file agree.
5. Run the strict build and affected examples. Review navigation, equations,
   tables, and code blocks in a browser. Add a changelog entry for significant
   documentation changes.

Sphinx configuration is in `conf.py`; Python dependencies are bounded to
compatible major versions in `requirements.txt`. The authoring references
are the [Sphinx guide](https://www.sphinx-doc.org/en/master/usage/quickstart.html)
and [MyST syntax guide](https://myst-parser.readthedocs.io/en/stable/syntax/roles-and-directives.html).
Theme navigation options follow the [Read the Docs theme configuration guide](https://sphinx-rtd-theme.readthedocs.io/en/stable/configuring.html).
