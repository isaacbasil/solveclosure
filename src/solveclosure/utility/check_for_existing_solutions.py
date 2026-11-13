import os


def check_for_existing_solutions(case_dir, overwrite=False):
    """
    Raises an error if the case directory already contains a closure problem case, unless overwrite is True.

    Args:
        case_dir (str): The path to the directory where the OpenFOAM case will be built.
        overwrite (bool): Set to True to replace an existing case. Default False.

    Returns:
    """

    if not overwrite and os.path.isdir(os.path.join(case_dir, "openfoam_case")):
        raise FileExistsError(f"{case_dir} already contains a closure problem case (the openfoam_case folder). "
                              "Delete it, or pass overwrite=True to replace it.")
