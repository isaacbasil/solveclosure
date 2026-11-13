# Example: the two squares case, solved as a dimensional problem.
#
# Run it from any folder: the case is built in "two_squares_case", in the folder it is run from.
# The expected result (global s surface average steady) is -170.9 mol s C-1 m-1.
import os
import solveclosure

# the folder where the OpenFOAM case is built (created if it does not exist)
case_dir = "two_squares_case"

# the example images, next to this script
demo_path = os.path.dirname(os.path.abspath(__file__))
img_path = os.path.join(demo_path, "two_squares.tif")
label_map_path = os.path.join(demo_path, "two_squares_label_map.tif")

# parameters
voxel = 1e-7
D_s = 4e-14

# solve. overwrite=True replaces the case from a previous run of this example.
# If OpenFOAM is not found automatically, add load_of_cmd="source /path/to/openfoam/etc/bashrc".
solveclosure.solve_closure(case_dir, img_path, label_map_path, voxel, D_s=D_s, dimensionless=False, overwrite=True)
