import os

EXAMPLE_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "example_data")


def example_path(name):
    """
    Returns the path to an example image that is installed with solveclosure.

    The example images are:

    - ``two_squares.tif``: two touching active material particles with square cross-sections (40 x 40 and
      20 x 20 voxels) in electrolyte, in an image of 100 x 100 x 10 voxels.
    - ``two_squares_label_map.tif``: the label map of ``two_squares.tif``.
    - ``three_particles.tif``: three overlapping, irregular active material particles of different sizes
      (equivalent diameters of about 20 to 31 voxels) in electrolyte, in an image of 50 x 50 x 50 voxels. It
      has no label map, which can be made with :func:`solveclosure.generate_label_map`.

    Args:
        name (str): The file name of the example image.

    Returns:
        path (str): The absolute path to the example image.
    """

    path = os.path.join(EXAMPLE_DATA_DIR, name)
    if not os.path.isfile(path):
        available = ", ".join(sorted(f for f in os.listdir(EXAMPLE_DATA_DIR) if f.endswith(".tif")))
        raise FileNotFoundError(f"There is no example image called {name}. The example images are: {available}.")
    return path
