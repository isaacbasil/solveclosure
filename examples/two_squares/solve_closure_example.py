
import os
import solveclosure

# set the path to the directory where the openfoam case will be run
case_dir = "path/to/your/case/directory/"


# preparing image paths - don't change this
demo_path = os.path.join(os.getcwd(), "examples/two_squares/")
img_path = os.path.join(demo_path, "two_squares.tif")
label_map_path = os.path.join(demo_path, "two_squares_label_map.tif")

# parameters 
voxel = 1e-7
D_s = 4e-14

# solve 
solveclosure.solve_closure(case_dir, img_path, label_map_path, voxel, D_s=D_s, dimensionless=False)



