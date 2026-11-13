# Analytical slab cases.
#
# A slab of active material of thickness H, spanning the whole cross-section of the image, reacting
# on both faces with electrolyte: the steady closure variable is a parabola, and the corrected
# surface average is s = -H / (6 F D), or s_hat = -H / (6 L) in dimensionless form.
#
# Option 2 with two slabs of thicknesses H1 and H2 touching each other, each reacting only on its
# outer face (no flux between particles in Option 2): each slab has s = -H_i / (3 F D) with a zero
# volume average, so the corrected global surface average is -(H1 + H2) / (6 F D).
#
# The finite volume solution has a discretisation error of order (voxel / H)^2, so the tests check
# that the error is small and decreases about four times when the resolution is doubled.

import pickle

import numpy as np
import pytest
import tifffile

import solveclosure

F = 96485


def solve(tmp_path, name, img, label_map, **kwargs):
    img_path, label_map_path = str(tmp_path / f"{name}_img.tif"), str(tmp_path / f"{name}_lab.tif")
    tifffile.imwrite(img_path, img)
    tifffile.imwrite(label_map_path, label_map)
    case_dir = str(tmp_path / name)
    solveclosure.solve_closure(case_dir, img_path, label_map_path, 1e-7, save_plot=False, **kwargs)
    with open(case_dir + "/closure_data.pickle", "rb") as f:
        return pickle.load(f)


def one_slab(scale):
    # electrolyte, a slab of 20 * scale voxels, electrolyte; 40 * scale voxels long
    nx, H = 40 * scale, 20 * scale
    img = np.zeros((nx, 2, 2), dtype=np.uint8)
    img[10 * scale:30 * scale] = 1
    return img, img.astype(np.uint16), nx, H


def two_slabs(scale):
    # electrolyte, slab 1 (8 * scale voxels), slab 2 (16 * scale voxels), electrolyte; 44 * scale long
    nx, H1, H2 = 44 * scale, 8 * scale, 16 * scale
    img = np.zeros((nx, 2, 2), dtype=np.uint8)
    img[10 * scale:34 * scale] = 1
    label_map = np.zeros(img.shape, dtype=np.uint16)
    label_map[10 * scale:18 * scale] = 1
    label_map[18 * scale:34 * scale] = 2
    return img, label_map, nx, H1 + H2


@pytest.mark.openfoam
def test_slab_dimensionless(tmp_path):
    errors = []
    for scale in (1, 2):
        img, label_map, nx, H = one_slab(scale)
        data = solve(tmp_path, f"slab_{scale}", img, label_map)
        expected = -H / (6 * nx)    # L is the image length
        errors.append(abs(data["global s surface average steady"] / expected - 1))
        assert abs(data["global s volume average final"]) < 1e-6 * abs(expected)
    assert errors[0] < 0.01 and errors[1] < errors[0] / 3


@pytest.mark.openfoam
def test_slab_dimensional(tmp_path):
    img, label_map, nx, H = one_slab(2)
    D_s, voxel = 4e-14, 1e-7
    data = solve(tmp_path, "slab_dim", img, label_map, dimensionless=False, D_s=D_s)
    expected = -H * voxel / (6 * F * D_s)
    assert data["global s surface average steady"] == pytest.approx(expected, rel=0.003)


@pytest.mark.openfoam
def test_two_slabs_option_2(tmp_path):
    errors = []
    for scale in (1, 2):
        img, label_map, nx, H_total = two_slabs(scale)
        data = solve(tmp_path, f"two_slabs_{scale}", img, label_map, allow_flux=False)
        expected = -H_total / (6 * nx)
        errors.append(abs(data["global s surface average steady"] / expected - 1))
        assert abs(data["global s volume average final"]) < 1e-6 * abs(expected)
    assert errors[0] < 0.01 and errors[1] < errors[0] / 3
