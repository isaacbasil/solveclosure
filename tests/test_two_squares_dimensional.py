# Tests the solve_closure function in dimensional form by ensuring that it can solve and reproduce validated results for the steady state solution.

import os
import pickle

import numpy as np
import pytest

import solveclosure


@pytest.mark.openfoam
def test_two_squares_dimensional(tmp_path):
    case_dir = str(tmp_path / "case")
    img_path = solveclosure.example_path("two_squares.tif")
    label_map_path = solveclosure.example_path("two_squares_label_map.tif")
    voxel = 1e-7
    D_s = 4e-14

    solveclosure.solve_closure(case_dir, img_path, label_map_path, voxel, D_s=D_s, dimensionless=False)

    with open(os.path.join(case_dir, "closure_data.pickle"), "rb") as f:
        closure_data = pickle.load(f)

    # check that value calculated agrees with validated results
    assert np.round(closure_data["global s surface average steady"], 1) == -170.9
