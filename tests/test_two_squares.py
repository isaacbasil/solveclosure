# Tests the solve_closure_multiparticle script by ensuring that it can solve and reproduce validated results for the steady state solution. 

import os
import solveclosure
import subprocess
import pickle
import numpy as np


def test_two_squares():
    # preparing paths 
    demo_path = os.path.join(os.getcwd(), "examples/two_squares/")
    case_dir = os.path.join(demo_path, "results/")
    img_path = os.path.join(demo_path, "two_squares.tif")
    label_map_path = os.path.join(demo_path, "two_squares_label_map.tif")


    # parameters 
    voxel = 1e-7
    cbd_surface_porosity = 0.5
    D_s = 4e-14

    # create a temporary directory to test
    cmd = f"mkdir {case_dir}"
    subprocess.run(["bash", "-c", cmd], check=False)

    # solve 
    solveclosure.solve_closure_multiparticle(case_dir, img_path, label_map_path, voxel, cbd_surface_porosity, D_s=D_s, dimensionless=False)

    # read steady state closure value
    closure_data_path = os.path.join(case_dir, "closure_data.pickle")

    with open(closure_data_path, 'rb') as f:
        closure_data = pickle.load(f)

    s_surf_ave_steady_state = closure_data["global s surface average steady"]

    # delete the directory afterwards
    cmd = f"rm -r {case_dir}"
    subprocess.run(["bash", "-c", cmd], check=True)

    # check that value calculated agrees with validated results
    assert np.round(s_surf_ave_steady_state, 1) == -170.9