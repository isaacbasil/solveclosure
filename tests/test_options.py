# Tests of closure Option 2 (allow_flux=False) and of parallel solves.

import os
import pickle

import numpy as np
import pytest
import tifffile

import solveclosure


def two_squares():
    img = tifffile.imread(solveclosure.example_path("two_squares.tif"))
    label_map = tifffile.imread(solveclosure.example_path("two_squares_label_map.tif"))
    return img, label_map


def solve(tmp_path, name, img, label_map, **kwargs):
    img_path, label_map_path = str(tmp_path / f"{name}_img.tif"), str(tmp_path / f"{name}_lab.tif")
    tifffile.imwrite(img_path, img)
    tifffile.imwrite(label_map_path, label_map)
    case_dir = str(tmp_path / name)
    solveclosure.solve_closure(case_dir, img_path, label_map_path, 1e-7, save_plot=False, **kwargs)
    with open(case_dir + "/closure_data.pickle", "rb") as f:
        return pickle.load(f)


# ---------- Option 2

@pytest.mark.openfoam
def test_option_2_equals_independent_particles(tmp_path):
    # With Option 2 there is no flux between particles, so each particle is independent. Solving each
    # particle alone, with the other particle replaced by inactive material (no flux, no reaction),
    # and combining the results must give the same corrected global surface average.
    img, label_map = two_squares()
    both = solve(tmp_path, "option_2", img, label_map, allow_flux=False)

    areas, volumes, surface_averages, volume_averages = [], [], [], []
    for particle, other in ((1, 2), (2, 1)):
        alone_img = img.copy()
        alone_img[label_map == other] = 51
        alone = solve(tmp_path, f"particle_{particle}", alone_img, (label_map == particle).astype(np.uint16))
        areas.append(alone["total area (surface porosity included)"])
        volumes.append(alone["total particle volume"])
        volume_averages.append(alone["global s volume average final"])
        surface_averages.append(alone["global s surface average steady"] + alone["global s volume average final"])
    combined = (np.dot(areas, surface_averages) / sum(areas) - np.dot(volumes, volume_averages) / sum(volumes))

    assert both["total area (surface porosity included)"] == pytest.approx(sum(areas), rel=1e-12)
    assert both["global s surface average steady"] == pytest.approx(combined, rel=1e-9)


@pytest.mark.openfoam
def test_option_2_differs_from_option_1(tmp_path):
    img, label_map = two_squares()
    option_1 = solve(tmp_path, "option_1", img, label_map)
    option_2 = solve(tmp_path, "option_2", img, label_map, allow_flux=False)
    assert option_1["global s surface average steady"] == pytest.approx(-0.065954, abs=1e-6)
    assert option_2["global s surface average steady"] == pytest.approx(-0.067842, abs=1e-6)


# ---------- serial and parallel

@pytest.mark.openfoam
@pytest.mark.parallel
def test_serial_and_parallel_agree(tmp_path):
    # a short end time, so that the solver is continued (and the results reconstructed) several times
    img, label_map = two_squares()
    load_of_cmd = os.environ.get("SOLVECLOSURE_PARALLEL_LOAD_OF_CMD")
    serial = solve(tmp_path, "serial", img, label_map, end_time=0.02)
    parallel = solve(tmp_path, "parallel", img, label_map, end_time=0.02, parallelise=True, n_procs=2,
                     load_of_cmd=load_of_cmd)
    assert parallel["continuations"] == serial["continuations"] > 0
    assert parallel["global s surface average steady"] == pytest.approx(serial["global s surface average steady"],
                                                                        rel=1e-6)
    assert len(parallel["times for transient data"]) == len(serial["times for transient data"])
