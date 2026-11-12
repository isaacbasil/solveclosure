# Tests for the CBD and separator surface porosity checks. These do not need OpenFOAM and run in seconds.

import os
import warnings

import numpy as np
import pytest
import tifffile

import solveclosure
from solveclosure.utility import check_surface_porosities

DEMO_PATH = os.path.join(os.path.dirname(__file__), "..", "examples", "two_squares")


def image_with(*labels):
    img = np.zeros((4, 3, 3), dtype=np.uint8)
    img[1:3, 1, 1] = 1
    for k, label in enumerate(labels):
        img[0, 0, k] = label
    return img


@pytest.mark.parametrize("label, arg", [(2, "cbd_surf_por"), (3, "sep_surf_por")])
def test_missing_porosity_for_a_phase_in_the_image_is_an_error(label, arg):
    with pytest.raises(ValueError, match=f"{arg} must be given"):
        check_surface_porosities(image_with(label), None, None)


@pytest.mark.parametrize("label, arg, kwargs", [(3, "cbd_surf_por", dict(cbd_surf_por=0.5, sep_surf_por=0.4)),
                                                (2, "sep_surf_por", dict(cbd_surf_por=0.5, sep_surf_por=0.4))])
def test_porosity_for_a_phase_not_in_the_image_warns(label, arg, kwargs):
    with pytest.warns(UserWarning, match=f"{arg} was given, but the image contains no"):
        assert check_surface_porosities(image_with(label), **kwargs) == (0.5, 0.4)  # the given values are kept


def test_phases_not_in_the_image_get_none_without_warning():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert check_surface_porosities(image_with(), None, None) == (None, None)
        assert check_surface_porosities(image_with(2, 3), 0.5, 0.0) == (0.5, 0.0)   # 0 is a valid porosity
        assert check_surface_porosities(image_with(2), 0.5, None) == (0.5, None)


def test_solve_closure_checks_porosities_before_looking_for_openfoam(tmp_path):
    # the check runs straight after the image is read, so no OpenFOAM is needed to get the error
    img = tifffile.imread(os.path.join(DEMO_PATH, "two_squares.tif")).copy()
    img[:30][img[:30] == 0] = 2
    img_path = str(tmp_path / "img.tif")
    tifffile.imwrite(img_path, img)
    with pytest.raises(ValueError, match="cbd_surf_por must be given"):
        solveclosure.solve_closure(str(tmp_path / "case"), img_path, os.path.join(DEMO_PATH, "two_squares_label_map.tif"),
                                   1e-7, load_of_cmd="false")


def test_porosities_are_keyword_only():
    with pytest.raises(TypeError, match="positional"):
        solveclosure.solve_closure("case", "img.tif", "label_map.tif", 1e-7, 0.5)
