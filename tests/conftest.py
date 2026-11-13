# Shared test setup.
#
# Tests marked "openfoam" need an OpenFOAM installation. They use the command in the environment
# variable SOLVECLOSURE_LOAD_OF_CMD to load OpenFOAM if it is set (for example on GitHub Actions),
# and otherwise solveclosure's automatic search. They are skipped if no OpenFOAM is found.
# Tests marked "parallel" also need MPI; SOLVECLOSURE_PARALLEL_LOAD_OF_CMD can give a separate
# command to load OpenFOAM for them.
#
#   pytest -m "not openfoam"     runs only the fast tests, which need no OpenFOAM

import os
import sys

import pytest

LOAD_OF_CMD = os.environ.get("SOLVECLOSURE_LOAD_OF_CMD")


def openfoam_available():
    if LOAD_OF_CMD:
        return True
    from solveclosure.utility import find_latest_openfoam_installation
    try:
        find_latest_openfoam_installation()
        return True
    except FileNotFoundError:
        return False


def pytest_collection_modifyitems(config, items):
    if any("openfoam" in item.keywords for item in items) and not openfoam_available():
        skip = pytest.mark.skip(reason="no OpenFOAM found (set SOLVECLOSURE_LOAD_OF_CMD)")
        for item in items:
            if "openfoam" in item.keywords:
                item.add_marker(skip)


@pytest.fixture(autouse=True)
def _load_openfoam_from_environment(monkeypatch):
    # when SOLVECLOSURE_LOAD_OF_CMD is set, it replaces the automatic search for OpenFOAM
    if LOAD_OF_CMD:
        import solveclosure  # noqa: F401  (makes sure the module is loaded)
        monkeypatch.setattr(sys.modules["solveclosure.solve_closure"], "find_latest_openfoam_installation",
                            lambda: LOAD_OF_CMD)


@pytest.fixture(autouse=True)
def _do_not_write_into_the_package():
    # tests must never write into the installed package (for example next to the example images)
    yield
    import solveclosure
    folder = os.path.dirname(solveclosure.example_path("two_squares.tif"))
    contents = sorted(os.listdir(folder))
    assert contents == ["three_particles.tif", "two_squares.tif", "two_squares_label_map.tif"], \
        f"A test wrote into the installed package: {folder} contains {contents}"
