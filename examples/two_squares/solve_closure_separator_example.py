# Example: the two squares case with a separator.
#
# The image is cropped so that particle 1 sits on the first face of axis 0, and a
# one-voxel separator layer (label 3) is added in front of it with add_separator_layer.
# Particle 1 then reacts with the separator (scaled by sep_surf_por) instead of the
# electrolyte on that face.
import os
import tifffile
import solveclosure

# set the path to the directory where the openfoam case will be run
case_dir = "path/to/your/case/directory/"

# preparing image paths - don't change this
demo_path = os.path.join(os.getcwd(), "examples/two_squares/")
img = tifffile.imread(os.path.join(demo_path, "two_squares.tif"))
label_map = tifffile.imread(os.path.join(demo_path, "two_squares_label_map.tif"))

# crop so particle 1 touches the face, then add the separator layer
img, label_map = img[30:], label_map[30:]
img, label_map = solveclosure.add_separator_layer(img, label_map, axis=0, side="start", thickness=1)

os.makedirs(case_dir, exist_ok=True)
img_path = os.path.join(case_dir, "two_squares_separator.tif")
label_map_path = os.path.join(case_dir, "two_squares_separator_label_map.tif")
tifffile.imwrite(img_path, img)
tifffile.imwrite(label_map_path, label_map)

# parameters
voxel = 1e-7
cbd_surface_porosity = 0.5
separator_surface_porosity = 0.4
D_s = 4e-14

# solve
solveclosure.solve_closure(case_dir, img_path, label_map_path, voxel, cbd_surface_porosity,
                           sep_surf_por=separator_surface_porosity, D_s=D_s, dimensionless=False)
