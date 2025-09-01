
import sys
import os
import solve2eqclosure

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

img_path = "/home/isaac_paten/Documents/openFOAM_projects/testing_solve2eqclosure_package/two_squares/geom_files/two_squares.tif"
label_map_path = "/home/isaac_paten/Documents/openFOAM_projects/testing_solve2eqclosure_package/two_squares/geom_files/two_squares_label_map.tif"

case_dir = "/home/isaac_paten/Documents/openFOAM_projects/testing_solve2eqclosure_package/two_squares/"

load_of_cmd = "source /usr/lib/openfoam/openfoam2412/etc/bashrc"

voxel = 1e-7

cbd_surface_porosity = 0.5

D_s = 4e-14


solve2eqclosure.solve_closure_multiparticle(case_dir, img_path, label_map_path, load_of_cmd, voxel, cbd_surface_porosity, D_s, allow_flux=True, parallelise=False, n_procs=2, run_solver=True, T_offset=1e5)

