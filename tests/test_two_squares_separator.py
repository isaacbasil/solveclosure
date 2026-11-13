# Tests for separator voxels (label 3).
#
# The solver tests use exact equivalences instead of new reference values:
#   - a separator with surface porosity 1 must behave exactly like electrolyte,
#   - a separator with the same surface porosity as the CBD must behave exactly like CBD,
#   - cropping the image and adding a separator layer with add_separator_layer must give the
#     same result as relabelling the electrolyte in front of the particle as separator.
# The two squares occupy x >= 30, so relabelling x < 30 puts a separator against particle 1 only.

import os
import pickle

import numpy as np
import pytest
import tifffile

import solveclosure
from solveclosure.image_analysis import calculate_area_and_volume
from solveclosure.utility import check_image_labels

DEMO_PATH = os.path.dirname(solveclosure.example_path("two_squares.tif"))
VOXEL = 1e-7


def load_two_squares():
    img = tifffile.imread(os.path.join(DEMO_PATH, "two_squares.tif"))
    label_map = tifffile.imread(os.path.join(DEMO_PATH, "two_squares_label_map.tif"))
    return img, label_map


def with_front_region(img, label):
    # relabel the electrolyte in front of the squares (x < 30)
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
    solveclosure.solve_closure(case_dir, img_path, label_map_path, VOXEL, **kwargs)
    with open(os.path.join(case_dir, "closure_data.pickle"), "rb") as f:
        return pickle.load(f)


# ---------- quick checks (no OpenFOAM needed)

def test_area_counts_separator_faces():
    img = np.zeros((4, 3, 3), dtype=np.uint8)
    img[1:3, 1, 1] = 1   # two AM voxels in a line
    img[0, 1, 1] = 3     # separator on one end
    img[3, 1, 1] = 2     # CBD on the other end
    area_elec, area_cbd, area_sep, total, V = calculate_area_and_volume(img, 1.0, 0.5, 0.25)
    assert (area_elec, area_cbd, area_sep) == (8, 1, 1)
    assert total == 8 + 0.5 * 1 + 0.25 * 1
    assert V == 2


def test_add_separator_layer():
    img, label_map = load_two_squares()
    img2, lm2 = solveclosure.add_separator_layer(img, label_map, axis=0, side="start", thickness=2)
    assert img2.shape == (img.shape[0] + 2,) + img.shape[1:]
    assert np.all(img2[:2] == 3) and np.array_equal(img2[2:], img)
    assert np.all(lm2[:2] == 0) and np.array_equal(lm2[2:], label_map)

    img3, _ = solveclosure.add_separator_layer(img, label_map, axis=2, side="end")
    assert img3.shape == img.shape[:2] + (img.shape[2] + 1,)
    assert np.all(img3[:, :, -1] == 3)


def test_unsupported_label_is_rejected():
    img, label_map = load_two_squares()
    img = img.copy()
    img[0, 0, 0] = 7
    with pytest.raises(ValueError, match="unsupported label"):
        check_image_labels(img, label_map)
    check_image_labels(with_front_region(img * (img != 7), 3), label_map)  # 0-3 are fine


# ---------- full solves (need OpenFOAM)

@pytest.mark.openfoam
def test_separator_with_porosity_one_matches_electrolyte(tmp_path):
    img, label_map = load_two_squares()
    elec = solve(tmp_path, "elec", img, label_map, D_s=4e-14, dimensionless=False)
    sep = solve(tmp_path, "sep", with_front_region(img, 3), label_map,
                sep_surf_por=1.0, D_s=4e-14, dimensionless=False)

    assert sep["am-sep area (surface porosity omitted)"] > 0
    assert sep["total area (surface porosity included)"] == pytest.approx(elec["total area (surface porosity included)"], rel=1e-12)
    # OpenFOAM solves for s + T offset (1e5 here), so round-off is relative to the offset, not to s.
    # Splitting particle 1's boundary into an extra patch changes the summation order at that level.
    assert sep["global s surface average steady"] == pytest.approx(elec["global s surface average steady"], abs=1e-9 * sep["T offset"])
    assert np.round(sep["global s surface average steady"], 1) == -170.9  # validated two squares value


@pytest.mark.openfoam
def test_separator_matches_cbd_with_same_porosity(tmp_path):
    img, label_map = load_two_squares()
    cbd = solve(tmp_path, "cbd", with_front_region(img, 2), label_map, cbd_surf_por=0.3, dimensionless=True)
    sep = solve(tmp_path, "sep", with_front_region(img, 3), label_map,
                sep_surf_por=0.3, dimensionless=True)

    assert sep["am-sep area (surface porosity omitted)"] == pytest.approx(cbd["am-cbd area (surface porosity omitted)"])
    assert sep["global s surface average steady"] == pytest.approx(cbd["global s surface average steady"], rel=1e-9)


@pytest.mark.openfoam
def test_add_separator_layer_matches_relabelled_image(tmp_path):
    img, label_map = load_two_squares()
    L = img.shape[0] * VOXEL  # keep the same lengthscale for both cases

    relabelled = solve(tmp_path, "relabelled", with_front_region(img, 3), label_map,
                       sep_surf_por=0.4, dimensionless=True, L=L)

    cropped_img, cropped_lm = solveclosure.add_separator_layer(img[30:], label_map[30:], axis=0, side="start")
    padded = solve(tmp_path, "padded", cropped_img, cropped_lm,
                   sep_surf_por=0.4, dimensionless=True, L=L)

    assert padded["global s surface average steady"] == pytest.approx(relabelled["global s surface average steady"], rel=1e-9)
    # a separator with porosity 0.4 must change the result compared with plain electrolyte (porosity 1)
    elec = solve(tmp_path, "elec", img, label_map, dimensionless=True, L=L)
    assert relabelled["global s surface average steady"] != pytest.approx(elec["global s surface average steady"], rel=1e-3)


@pytest.mark.openfoam
def test_case_settings_are_saved_and_reused(tmp_path):
    img, label_map = load_two_squares()
    data = solve(tmp_path, "default_L", img, label_map, dimensionless=True)

    assert data["L"] == pytest.approx(img.shape[0] * VOXEL)  # default: length of axis 0
    assert data["voxel"] == VOXEL

    # the image has no CBD or separator, so neither surface porosity applies and both are saved as None
    assert data["cbd surface porosity"] is None and data["sep surface porosity"] is None

    # reprocessing reads the saved settings and must give the same result
    case_dir = os.path.join(str(tmp_path), "default_L") + "/"
    solveclosure.process_closure_results(case_dir)
    with open(os.path.join(case_dir, "closure_data.pickle"), "rb") as f:
        reprocessed = pickle.load(f)
    assert reprocessed["global s surface average steady"] == pytest.approx(data["global s surface average steady"], rel=1e-12)
