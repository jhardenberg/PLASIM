"""Sphinx configuration for the evolving PlaSim user documentation."""

project = "PlaSim"
author = "PlaSim contributors"
extensions = ["myst_parser", "sphinx.ext.mathjax", "sphinx.ext.extlinks"]
source_suffix = {".md": "markdown", ".rst": "restructuredtext"}
root_doc = "index"
exclude_patterns = ["_build", ".venv", "__pycache__"]
nitpicky = True

html_theme = "alabaster"
html_title = "PlaSim user and developer manual"
html_static_path = ["_static"]
html_css_files = ["custom.css"]
html_theme_options = {"description": "Planet Simulator", "fixed_sidebar": True}
html_sidebars = {"**": ["about.html", "navigation.html", "searchfield.html"]}
extlinks = {"repo": ("https://github.com/jhardenberg/PLASIM/blob/master/%s", "%s")}

latex_documents = [("index", "plasim-user-guide.tex", "PlaSim User and Developer Manual",
                    author, "manual")]
latex_elements = {"papersize": "a4paper", "pointsize": "11pt"}
