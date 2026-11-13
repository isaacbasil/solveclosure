# Tests for user-provided solver settings (solver_settings_dir).

import os
import pickle
import shutil

import pytest

import solveclosure

DEMO_PATH = os.path.join(os.path.dirname(__file__), "..", "examples", "two_squares")
IMG = os.path.join(DEMO_PATH, "two_squares.tif")
LABEL_MAP = os.path.join(DEMO_PATH, "two_squares_label_map.tif")
DEFAULTS = os.path.join(os.path.dirname(solveclosure.__file__), "templates", "solver_settings")


def custom_settings(tmp_path, tolerance="1e-10"):
    # the default files, with a different linear solver tolerance to recognise them
    folder = tmp_path / "my_settings"
    shutil.copytree(DEFAULTS, folder)
    path = folder / "fvSolution"
    text = path.read_text()
    assert "tolerance\t1e-8;" in text
    path.write_text(text.replace("tolerance\t1e-8;", f"tolerance\t{tolerance};"))
    return str(folder)


# ---------- quick check (no OpenFOAM needed)

def test_missing_file_is_an_error(tmp_path):
    folder = tmp_path / "my_settings"
    os.makedirs(folder)
    shutil.copy(os.path.join(DEFAULTS, "fvSchemes"), folder)   # no fvSolution
    with pytest.raises(FileNotFoundError, match="missing: fvSolution"):
        solveclosure.solve_closure(str(tmp_path / "case"), IMG, LABEL_MAP, 1e-7, solver_settings_dir=str(folder),
                                   load_of_cmd="false")
    assert not os.path.exists(tmp_path / "case")   # raised before anything was created


# ---------- with OpenFOAM

def test_custom_settings_are_used_for_every_particle(tmp_path):
    case_dir = str(tmp_path / "case")
    solveclosure.solve_closure(case_dir, IMG, LABEL_MAP, 1e-7, solver_settings_dir=custom_settings(tmp_path),
                               run_solver=False)
    paths = [os.path.join(case_dir, "solver_settings", "fvSolution")]
    paths += [os.path.join(case_dir, "openfoam_case", "system", f"particle_{i}", "fvSolution") for i in (1, 2)]
    for path in paths:
        with open(path) as f:
            assert "tolerance\t1e-10;" in f.read()


def test_solve_with_custom_settings(tmp_path):
    # a tighter linear solver tolerance must give the same result as the defaults
    case_dir = str(tmp_path / "case")
    solveclosure.solve_closure(case_dir, IMG, LABEL_MAP, 1e-7, solver_settings_dir=custom_settings(tmp_path),
                               save_plot=False)
    with open(os.path.join(case_dir, "closure_data.pickle"), "rb") as f:
        data = pickle.load(f)
    assert data["global s surface average steady"] == pytest.approx(-0.0659544, rel=1e-4)
