# Tests for inactive material (label 51), which blocks the active material surface it touches.
#
# The two squares occupy x >= 30, so relabelling the electrolyte at x < 30 puts the relabelled
# phase against one face of particle 1 only.

import os
import pickle

import numpy as np
import pytest
import tifffile

import solveclosure
from solveclosure.image_analysis import calculate_area_and_volume

DEMO_PATH = os.path.dirname(solveclosure.example_path("two_squares.tif"))
VOXEL = 1e-7


def load_two_squares():
    img = tifffile.imread(os.path.join(DEMO_PATH, "two_squares.tif"))
    label_map = tifffile.imread(os.path.join(DEMO_PATH, "two_squares_label_map.tif"))
    return img, label_map


def with_front_region(img, label):
    img = img.copy()
    img[:30][img[:30] == 0] = label
    return img


def solve(tmp_path, name, img, label_map, **kwargs):
    case_dir = os.path.join(str(tmp_path), name) + "/"
    os.makedirs(case_dir)
    img_path = os.path.join(case_dir, "img.tif")
    label_map_path = os.path.join(case_dir, "label_map.tif")
    tifffile.imwrite(img_path, img)
    tifffile.imwrite(label_map_path, label_map)
    solveclosure.solve_closure(case_dir, img_path, label_map_path, VOXEL, dimensionless=True, **kwargs)
    with open(os.path.join(case_dir, "closure_data.pickle"), "rb") as f:
        return case_dir, pickle.load(f)


# ---------- quick checks (no OpenFOAM needed)

def test_inactive_faces_are_not_reactive():
    img = np.zeros((4, 3, 3), dtype=np.uint8)
    img[1:3, 1, 1] = 1     # two AM voxels in a line
    img[0, 1, 1] = 51      # inactive material on one end
    img[3, 1, 1] = 2       # CBD on the other end
    area_elec, area_cbd, area_sep, total, V = calculate_area_and_volume(img, 1.0, 0.5, 1.0)
    assert (area_elec, area_cbd, area_sep) == (8, 1, 0)
    assert total == 8 + 0.5 * 1     # the inactive face contributes nothing


# ---------- with OpenFOAM

@pytest.mark.openfoam
def test_inactive_material_matches_separator_with_zero_porosity(tmp_path):
    img, label_map = load_two_squares()
    case_dir, inactive = solve(tmp_path, "inactive", with_front_region(img, 51), label_map)
    _, separator = solve(tmp_path, "separator", with_front_region(img, 3), label_map, sep_surf_por=0.0)

    assert inactive["total area (surface porosity included)"] == pytest.approx(separator["total area (surface porosity included)"], rel=1e-12)
    assert inactive["global s surface average steady"] == pytest.approx(separator["global s surface average steady"], rel=1e-9)

    # the inactive material is meshed as its own zone and gives particle 1 a zero-flux boundary
    with open(os.path.join(case_dir, "openfoam_case", "0", "particle_1", "T")) as f:
        bc = f.read()
    assert "particle_1_to_Inactive" in bc and "zeroGradient" in bc.split("particle_1_to_Inactive")[1].split("}")[0]
    # only the particle's own neighbours get a coupled patch (not itself)
    assert "particle_1_to_particle_2" in bc and "particle_1_to_particle_1" not in bc
    assert not os.path.exists(os.path.join(case_dir, "openfoam_case", "0", "Inactive"))


@pytest.mark.openfoam
def test_inactive_material_is_not_electrolyte(tmp_path):
    img, label_map = load_two_squares()
    _, electrolyte = solve(tmp_path, "electrolyte", img, label_map)
    _, inactive = solve(tmp_path, "inactive", with_front_region(img, 51), label_map)

    # the blocked face of particle 1 (40 x 10 voxel faces) no longer counts as reactive area
    blocked_area = 40 * 10 * VOXEL ** 2
    assert inactive["total area (surface porosity included)"] == pytest.approx(
        electrolyte["total area (surface porosity included)"] - blocked_area, rel=1e-12)
    assert inactive["global s surface average steady"] != pytest.approx(electrolyte["global s surface average steady"], rel=1e-3)
