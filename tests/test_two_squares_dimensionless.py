# Tests the solve_closure function in dimensionless form by ensuring that it can solve and reproduce validated results for the steady state solution.

import os
import pickle

import numpy as np
import pytest

import solveclosure


@pytest.mark.openfoam
def test_two_squares_dimensionless(tmp_path):
    case_dir = str(tmp_path / "case")
    img_path = solveclosure.example_path("two_squares.tif")
    label_map_path = solveclosure.example_path("two_squares_label_map.tif")
    voxel = 1e-7

    solveclosure.solve_closure(case_dir, img_path, label_map_path, voxel, dimensionless=True)

    with open(os.path.join(case_dir, "closure_data.pickle"), "rb") as f:
        closure_data = pickle.load(f)

    # check that value calculated agrees with validated results
    # steady state value; -0.055516 in solveclosure 0.1.0 came from a run that stopped before steady state
    assert np.round(closure_data["global s surface average steady"], 6) == -0.065954
