
def write_decomposeParDict_file(file_path, n_procs):
    """
    Writes the OpenFOAM decomposeParDict file for a parallelised case.  
    
    Args:
        file_path (str): The absolute path to the decomposeParDict file. 
        n_procs (int): The number of processors used for parallelisation.

    Returns:
    """

    content = f"""
FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      decomposeParDict;
}}

numberOfSubdomains {n_procs};

method          scotch;

"""
    
    with open(file_path, 'w') as f:
        f.write(content)