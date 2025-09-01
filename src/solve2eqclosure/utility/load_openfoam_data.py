import warnings
def load_openfoam_data(path):
    """
    Loads OpenFOAM postProcessing data. 
    
    Args:
        path (str): The absolute path to postProcessing file.

    Returns:
        t (list): The time entries for surface or volume integral results. 
        y (list): The surface or volume integral results. 
    """

    t = []
    y = []

    with open(path, 'r') as file:
        for line in file:
            if line.startswith('%'):
                continue
            elif line.startswith('#'):
                continue
            parts = line.split()
            if len(parts) == 2:
                t.append(float(parts[0]))
                y.append(float(parts[1]))
            else:
                warnings.warn(
                    "Beware, more than 2 columns were found in the file being read", UserWarning)

    return t, y