# Tests for the case directory: creating it, and not replacing an existing case by accident.

import os

import pytest

import solveclosure

DEMO_PATH = os.path.join(os.path.dirname(__file__), "..", "examples", "two_squares")
IMG = os.path.join(DEMO_PATH, "two_squares.tif")
LABEL_MAP = os.path.join(DEMO_PATH, "two_squares_label_map.tif")


# ---------- quick check (no OpenFOAM needed)

def test_existing_case_is_not_replaced_without_overwrite(tmp_path):
    os.makedirs(tmp_path / "case" / "openfoam_case")
    # raised before OpenFOAM is looked for, so no OpenFOAM needed
    with pytest.raises(FileExistsError, match="Delete it, or pass overwrite=True"):
        solveclosure.solve_closure(str(tmp_path / "case"), IMG, LABEL_MAP, 1e-7, load_of_cmd="false")


def test_no_error_with_overwrite_or_without_a_case(tmp_path):
    from solveclosure.utility import check_for_existing_solutions
    check_for_existing_solutions(str(tmp_path))                      # nothing there yet
    os.makedirs(tmp_path / "openfoam_case")
    check_for_existing_solutions(str(tmp_path), overwrite=True)


# ---------- with OpenFOAM

def test_case_dir_is_created_and_can_be_overwritten(tmp_path):
    case_dir = str(tmp_path / "new" / "case")   # does not exist yet
    solveclosure.solve_closure(case_dir, IMG, LABEL_MAP, 1e-7, run_solver=False)
    assert os.path.isfile(os.path.join(case_dir, "closure_data.pickle"))

    with pytest.raises(FileExistsError):
        solveclosure.solve_closure(case_dir, IMG, LABEL_MAP, 1e-7, run_solver=False)
    solveclosure.solve_closure(case_dir, IMG, LABEL_MAP, 1e-7, run_solver=False, overwrite=True)
    assert os.path.isfile(os.path.join(case_dir, "closure_data.pickle"))
