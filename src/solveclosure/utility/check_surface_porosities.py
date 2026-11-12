import warnings

import numpy as np

CBD_LABEL = 2
SEPARATOR_LABEL = 3


def check_surface_porosities(img, cbd_surf_por, sep_surf_por):
    """
    Checks the CBD and separator surface porosities against the phases present in the image.

    A surface porosity must be given for each phase with a surface porosity (CBD, label 2, and
    separator, label 3) that the image contains. A surface porosity given for a phase that the image
    does not contain has no effect, and a warning is shown. A phase that is not in the image, and has
    no surface porosity given, keeps None (no surface porosity applies).

    Args:
        img (nd array): The electrode image.
        cbd_surf_por (float or None): The CBD surface porosity, or None if not given.
        sep_surf_por (float or None): The separator surface porosity, or None if not given.

    Returns:
        cbd_surf_por (float or None): The CBD surface porosity, or None if the image has no CBD and none was given.
        sep_surf_por (float or None): The separator surface porosity, or None if the image has no separator and none was given.
    """

    checked = []
    for arg, value, label, phase in (("cbd_surf_por", cbd_surf_por, CBD_LABEL, "CBD"),
                                     ("sep_surf_por", sep_surf_por, SEPARATOR_LABEL, "separator")):
        present = bool(np.any(img == label))
        if value is None and present:
            raise ValueError(f"The image contains {phase} (label {label}), so {arg} must be given.")
        if value is not None and not present:
            warnings.warn(f"{arg} was given, but the image contains no {phase} (label {label}), so it has no effect.",
                          UserWarning, stacklevel=3)
        checked.append(value)

    return tuple(checked)
