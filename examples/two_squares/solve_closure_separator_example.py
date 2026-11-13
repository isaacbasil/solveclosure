# Example: the two squares case with a separator.
#
# The image is cropped so that particle 1 sits on the first face of axis 0,
# and a one-voxel separator layer (label 3) is added in front of it with
# add_separator_layer. Particle 1 then reacts with the separator (scaled by
# sep_surf_por) instead of the electrolyte on that face.
#
# Run it from any folder: the case is built in "two_squares_separator_case",
# in the folder it is run from. The expected result (global s surface average
# steady) is -171.4 mol s C-1 m-1.
import os
import tifffile
import solveclosure

# the folder where the OpenFOAM case is built
case_dir = "two_squares_separator_case"

# the example images, installed with solveclosure
img = tifffile.imread(solveclosure.example_path("two_squares.tif"))
label_map = tifffile.imread(
    solveclosure.example_path("two_squares_label_map.tif"))

# crop so particle 1 touches the face, then add the separator layer
img, label_map = img[30:], label_map[30:]
img, label_map = solveclosure.add_separator_layer(
    img, label_map, axis=0, side="start", thickness=1)

os.makedirs(case_dir, exist_ok=True)
img_path = os.path.join(case_dir, "two_squares_separator.tif")
label_map_path = os.path.join(case_dir, "two_squares_separator_label_map.tif")
tifffile.imwrite(img_path, img)
tifffile.imwrite(label_map_path, label_map)

# parameters
voxel = 1e-7
separator_surface_porosity = 0.4
D_s = 4e-14

# solve. overwrite=True replaces the case from a previous run of this example.
# If OpenFOAM is not found automatically, add
# load_of_cmd="source /path/to/openfoam/etc/bashrc".
solveclosure.solve_closure(
    case_dir, img_path, label_map_path, voxel,
    sep_surf_por=separator_surface_porosity,
    D_s=D_s, dimensionless=False, overwrite=True,
)
