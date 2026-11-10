# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------
import os
import sys
from importlib.metadata import PackageNotFoundError, version as _pkg_version

# Add src/ to sys.path so autodoc can find the package even if it is not installed.
sys.path.insert(0, os.path.abspath("../src"))

# -- Project information -----------------------------------------------------
project = "solveclosure"
copyright = "2025, Isaac Paten"
author = "Isaac Paten"

# Take the version from the installed package (pyproject.toml), so it never
# needs updating here.
try:
    release = _pkg_version("solveclosure")
except PackageNotFoundError:
    release = "unknown"
version = ".".join(release.split(".")[:2])

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",  # generates the API pages automatically
    "sphinx.ext.napoleon",     # Google/NumPy-style docstrings
    "sphinx.ext.viewcode",     # "[source]" links next to each function
    "sphinx.ext.mathjax",      # LaTeX-style maths
    "sphinx.ext.intersphinx",  # links to Python/NumPy/SciPy docs
]

# Regenerate the API pages from the package on every build, so new or renamed
# modules are picked up without editing any .rst files.
autosummary_generate = True
autodoc_default_options = {
    "members": True,
    "show-inheritance": True,
}
autodoc_member_order = "bysource"

napoleon_google_docstring = True
napoleon_numpy_docstring = True

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "scipy": ("https://docs.scipy.org/doc/scipy/", None),
    "skimage": ("https://scikit-image.org/docs/stable/", None),
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------
html_theme = "sphinx_rtd_theme"
html_title = f"solveclosure {release}"
html_theme_options = {
    "navigation_depth": 3,
}
html_context = {
    "display_github": True,
    "github_user": "isaacbasil",
    "github_repo": "solveclosure",
    "github_version": "main",
    "conf_py_path": "/docs/",
}
