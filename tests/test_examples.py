# Tests for the example images installed with solveclosure, and the example scripts.

import os
import pickle
import runpy

import numpy as np
import pytest
import tifffile

import solveclosure

EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "examples")


# ---------- quick checks (no OpenFOAM needed)

def test_example_images_are_installed():
    img = tifffile.imread(solveclosure.example_path("two_squares.tif"))
    label_map = tifffile.imread(solveclosure.example_path("two_squares_label_map.tif"))
    three = tifffile.imread(solveclosure.example_path("three_particles.tif"))
    assert img.shape == label_map.shape == (100, 100, 10) and set(np.unique(img)) == {0, 1}
    assert label_map.max() == 2
    assert three.shape == (50, 50, 50) and set(np.unique(three)) == {0, 1}


def test_unknown_example_image():
    with pytest.raises(FileNotFoundError, match="three_particles.tif"):
        solveclosure.example_path("nope.tif")


def test_three_particles_are_found_by_generate_label_map(tmp_path):
    label_map = solveclosure.generate_label_map(solveclosure.example_path("three_particles.tif"),
                                                str(tmp_path / "lab.tif"), save_image=False, save_stats=False)
    assert label_map.max() == 3


# ---------- with OpenFOAM: the example scripts, run as a user would

@pytest.mark.parametrize("script, case_dir, expected", [
    ("two_squares/solve_closure_example.py", "two_squares_case", -170.9),
    ("two_squares/solve_closure_separator_example.py", "two_squares_separator_case", -171.4),
    ("three_particles/three_particles_example.py", "three_particles_case", -0.1046),
])
@pytest.mark.openfoam
def test_example_scripts(tmp_path, monkeypatch, script, case_dir, expected):
    monkeypatch.chdir(tmp_path)   # the scripts build their case in the folder they are run from
    runpy.run_path(os.path.join(EXAMPLES_DIR, script), run_name="__main__")
    with open(os.path.join(case_dir, "closure_data.pickle"), "rb") as f:
        result = pickle.load(f)["global s surface average steady"]
    assert result == pytest.approx(expected, abs=0.05 if expected < -1 else 5e-5)
