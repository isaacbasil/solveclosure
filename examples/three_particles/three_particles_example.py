# Example: three overlapping particles, from an image without a label map.
#
# The label map is generated with generate_label_map, which separates the
# particles with a watershed, and the dimensionless closure problem is then
# solved.
#
# Run it from any folder: everything is written to "three_particles_case", in
# the folder it is run from. The expected result (global s surface average
# steady) is -0.1046.
import os
import solveclosure

# the folder where the label map and the OpenFOAM case are written
case_dir = "three_particles_case"
os.makedirs(case_dir, exist_ok=True)

# the example image, installed with solveclosure
img_path = solveclosure.example_path("three_particles.tif")

# generate the label map. This also saves three_particles_label_map_slices.png
# and three_particles_label_map_stats.png, to check that the three particles
# were found.
label_map_path = os.path.join(case_dir, "three_particles_label_map.tif")
solveclosure.generate_label_map(img_path, label_map_path)

# parameters
voxel = 1e-7

# solve. overwrite=True replaces the case from a previous run of this example.
# If OpenFOAM is not found automatically, add
# load_of_cmd="source /path/to/openfoam/etc/bashrc".
solveclosure.solve_closure(
    case_dir, img_path, label_map_path, voxel, overwrite=True,
)
