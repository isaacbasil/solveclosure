# Fast unit tests of the image analysis, case setup and results processing. No OpenFOAM needed.

import os
import pickle
import re

import numpy as np
import pytest
import tifffile

import solveclosure
from solveclosure.image_analysis import (calculate_area_and_volume, calculate_source_terms_dimensional,
                                         calculate_source_terms_dimensionless, subdivide_image_using_label_map)
from solveclosure.openfoam_case_setup import make_topoSetDict

F = 96485


# ---------- areas and source terms

def cube_image():
    img = np.zeros((4, 4, 4), dtype=np.uint8)
    img[1:3, 1:3, 1:3] = 1    # a 2 x 2 x 2 cube of AM in electrolyte
    return img


def test_area_and_volume_of_a_cube():
    voxel = 1e-7
    area_elec, area_cbd, area_sep, total, V = calculate_area_and_volume(cube_image(), voxel, 0.5, 0.5)
    assert area_elec == pytest.approx(24 * voxel ** 2)    # 6 sides of 2 x 2 faces
    assert area_cbd == area_sep == 0
    assert total == pytest.approx(area_elec)
    assert V == pytest.approx(8 * voxel ** 3)


def test_faces_on_the_image_boundary_do_not_count():
    img = np.zeros((3, 3, 3), dtype=np.uint8)
    img[0, :, :] = 1    # a layer of AM on the face of the image
    area_elec, _, _, total, V = calculate_area_and_volume(img, 1.0, 1.0, 1.0)
    assert area_elec == 9 and total == 9 and V == 9    # only the 3 x 3 faces against electrolyte


def test_surface_porosities_weight_the_area():
    img = np.zeros((4, 3, 3), dtype=np.uint8)
    img[1:3, 1, 1] = 1
    img[0, 1, 1] = 2      # CBD on one end
    img[3, 1, 1] = 3      # separator on the other
    area_elec, area_cbd, area_sep, total, V = calculate_area_and_volume(img, 1.0, 0.25, 0.5)
    assert (area_elec, area_cbd, area_sep) == (8, 1, 1)
    assert total == 8 + 0.25 + 0.5


def test_source_terms_dimensionless():
    voxel, L = 1e-7, 1e-6
    img = cube_image()
    img[0, 1:3, 1:3] = 2    # CBD against one side of the cube
    S, bc_elec, bc_cbd, bc_sep, area, V = calculate_source_terms_dimensionless(img, voxel, 0.4, 1.0, L)
    expected_area = (20 + 0.4 * 4) * voxel ** 2
    assert area == pytest.approx(expected_area) and V == pytest.approx(8 * voxel ** 3)
    assert S == pytest.approx(L * expected_area / V)
    assert bc_elec == -1 and bc_cbd == pytest.approx(-0.4)
    assert bc_sep is False    # no AM-separator boundary


def test_source_terms_dimensional():
    voxel, D_s = 1e-7, 4e-14
    S, bc_elec, bc_cbd, bc_sep, area, V = calculate_source_terms_dimensional(cube_image(), voxel, 0.5, 0.5, D_s)
    assert S == pytest.approx(area / (F * V))
    assert bc_elec == pytest.approx(-1 / (D_s * F))
    assert bc_cbd is False and bc_sep is False


# ---------- topoSetDict cell numbering

def read_topo_cell_sets(path):
    text = open(path).read()
    sets = {}
    for name, values in re.findall(r"name\s+(\w+);\s*type\s+cellSet;.*?value\s*\((.*?)\);", text, re.S):
        sets[name] = [int(v) for v in values.split()]
    return sets


def test_topoSetDict_cell_numbering_matches_blockMesh(tmp_path):
    # blockMesh numbers the cells of the block with x (image axis 0) fastest, then y, then z
    nx, ny, nz = 3, 4, 5
    rng = np.random.default_rng(1)
    img = rng.choice([0, 1, 2, 3, 51], size=(nx, ny, nz)).astype(np.uint8)
    label_map = np.where(img == 1, 1, 0).astype(np.uint16)
    label_map[(img == 1) & (np.indices(img.shape)[0] == 2)] = 2    # a second "particle"
    path = str(tmp_path / "topoSetDict")
    make_topoSetDict(path, img, label_map)
    sets = read_topo_cell_sets(path)

    expected = {"c_am_1": (img == 1) & (label_map == 1), "c_am_2": (img == 1) & (label_map == 2),
                "c_elec": img == 0, "c_cbd": img == 2, "c_sep": img == 3, "c_inactive": img == 51}
    all_cells = []
    for name, mask in expected.items():
        cell_ids = sorted(sets[name])
        i, j, k = np.nonzero(mask)
        assert cell_ids == sorted((i + nx * j + nx * ny * k).tolist()), name
        all_cells += cell_ids
    assert sorted(all_cells) == list(range(nx * ny * nz))    # every cell in exactly one set


# ---------- neighbour detection

def test_neighbours_of_particles_touching_the_image_edges(tmp_path):
    # two particles that fill the whole cross-section of the image, so they touch every image face
    img = np.ones((6, 3, 3), dtype=np.uint8)
    label_map = np.ones((6, 3, 3), dtype=np.uint16)
    label_map[3:] = 2
    path = str(tmp_path / "label_map.tif")
    tifffile.imwrite(path, label_map)
    _, _, neighbours = subdivide_image_using_label_map(path, img)
    assert neighbours == {1: [2], 2: [1]}    # each other, and no electrolyte from the image edges


def test_neighbours_include_phases_and_only_touching_particles(tmp_path):
    img = np.zeros((9, 3, 3), dtype=np.uint8)
    img[0:2] = 1; img[2] = 2; img[3:5] = 1; img[5] = 3; img[6:8] = 1; img[8] = 51
    img[:, 0, 0] = 0    # a line of electrolyte along the image edge
    label_map = np.zeros(img.shape, dtype=np.uint16)
    label_map[0:2][img[0:2] == 1] = 1
    label_map[3:5][img[3:5] == 1] = 2
    label_map[6:8][img[6:8] == 1] = 3
    path = str(tmp_path / "label_map.tif")
    tifffile.imwrite(path, label_map)
    _, _, neighbours = subdivide_image_using_label_map(path, img)
    assert sorted(map(str, neighbours[1])) == ["cbd", "elec"]                 # particle 2 is not touching
    assert sorted(map(str, neighbours[2])) == ["cbd", "elec", "sep"]
    assert sorted(map(str, neighbours[3])) == ["elec", "inactive", "sep"]


# ---------- process_closure_results on synthetic data

def write_dat(path, header, times, values):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(f"# {header}\n# Time\tvalue\n")
        for t, v in zip(times, values):
            f.write(f"{t}\t{v}\n")


def test_process_closure_results_on_synthetic_data(tmp_path):
    case_dir = str(tmp_path) + "/"
    offset, cbd_por = 100.0, 0.5
    A_elec = {1: 3.0, 2: 2.0}          # m2 (dimensional case)
    A_cbd = {1: 2.0, 2: 0.0}
    V = {1: 4.0, 2: 1.0}               # m3
    total_A = sum(A_elec.values()) + cbd_por * sum(A_cbd.values())
    closure_data = {"T offset": offset, "dimensionless": False, "L": None, "cbd surface porosity": cbd_por,
                    "sep surface porosity": None, "total area (surface porosity included)": total_A,
                    "total particle volume": sum(V.values()),
                    "particle data": {k: {"particle surface area": A_elec[k] + cbd_por * A_cbd[k],
                                          "particle volume": V[k]} for k in (1, 2)}}
    with open(case_dir + "closure_data.pickle", "wb") as f:
        pickle.dump(closure_data, f)

    # the solver field is T = s + offset; surface integrals over each surface type, volume integrals
    times = [0.1, 0.2, 0.3]
    s_elec = {1: [-1.0, -2.0, -2.0], 2: [-3.0, -4.0, -4.0]}
    s_cbd = {1: [-0.5, -1.0, -1.0]}
    s_vol = {1: [0.1, 0.2, 0.2], 2: [-0.1, 0.0, 0.0]}
    pp = case_dir + "openfoam_case/postProcessing/"
    for k in (1, 2):
        write_dat(f"{pp}particle_{k}/particle_{k}_surfaceIntegral_elec/0/surfaceFieldValue.dat", "surface", times,
                  [(s + offset) * A_elec[k] for s in s_elec[k]])
        write_dat(f"{pp}particle_{k}/particle_{k}_volumeIntegral/0/volFieldValue.dat", "volume", times,
                  [(s + offset) * V[k] for s in s_vol[k]])
    write_dat(f"{pp}particle_1/particle_1_surfaceIntegral_cbd/0/surfaceFieldValue.dat", "surface", times,
              [(s + offset) * A_cbd[1] for s in s_cbd[1]])

    with pytest.warns(UserWarning):    # the synthetic transient is too short to count as steady
        data = solveclosure.process_closure_results(case_dir)

    surf = [(sum(s_elec[k][n] * A_elec[k] for k in (1, 2)) + cbd_por * s_cbd[1][n] * A_cbd[1]) / total_A for n in range(3)]
    vol = [sum(s_vol[k][n] * V[k] for k in (1, 2)) / sum(V.values()) for n in range(3)]
    expected = np.array(surf) - np.array(vol)
    assert np.allclose(data["global s surface average transient"], expected)
    assert data["global s surface average steady"] == pytest.approx(expected[-1])
    assert data["global s volume average final"] == pytest.approx(vol[-1])
    assert list(data["times for transient data"]) == times
    with open(case_dir + "closure_data.pickle", "rb") as f:    # written to the results file too
        assert pickle.load(f)["global s surface average steady"] == pytest.approx(expected[-1])
