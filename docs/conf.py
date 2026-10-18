"""Sphinx configuration for the evolving PlaSim user documentation."""

project = "PlaSim-LSG TNG"
author = "PlaSim contributors"
extensions = ["myst_parser", "sphinx.ext.mathjax", "sphinx.ext.extlinks"]
source_suffix = {".md": "markdown", ".rst": "restructuredtext"}
root_doc = "index"
exclude_patterns = ["_build", ".venv", "__pycache__"]
nitpicky = True

html_theme = "sphinx_rtd_theme"
html_title = "PlaSim-LSG TNG user and developer manual"
html_static_path = ["_static"]
html_css_files = ["custom.css"]
html_theme_options = {
    "collapse_navigation": False,
    "navigation_depth": 4,
    "titles_only": True,
}
extlinks = {"repo": ("https://github.com/jhardenberg/PLASIM/blob/master/%s", "%s")}

latex_documents = [("index", "plasim-user-guide.tex", "PlaSim-LSG TNG User and Developer Manual",
                    author, "manual")]
latex_elements = {"papersize": "a4paper", "pointsize": "11pt"}
